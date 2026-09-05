# -*- coding: utf-8 -*-
"""
db_tool.py - 数据库操作工具文件

负责与 sqlite3 数据库进行交互，执行 SQL 语句、处理查询结果等。
包含数据库初始化（创建数据库、检查表是否存在、创建表）、查询、插入、
删除、更新等数据库操作函数，所有函数均向外暴露接口。

用法：所有函数第一个参数为 config（配置字典，通常由 load_config() 返回）。
"""

import json
import os
import sqlite3
import hmac

# 配置文件默认路径（与本文件同目录）
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


def load_config(path=CONFIG_PATH):
    """读取并返回 config.json 配置字典。"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _db_path(config):
    """将数据库路径解析为绝对路径。

    相对路径基于本文件（db_tool.py）所在目录解析，保证从任意工作目录
    运行（如直接双击 db_debug.py）都能定位到 server/ 下的数据库文件，
    不会因工作目录不同而找不到数据库或误建空库。
    """
    db_path = config['database']['path']
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(CONFIG_PATH), db_path)
    return db_path


def connect(config):
    """建立数据库连接并返回连接对象（返回的行可按列名访问）。"""
    conn = sqlite3.connect(_db_path(config))
    conn.row_factory = sqlite3.Row
    return conn


def get_table(config):
    """返回数据库表名。"""
    return config['database']['table']


def init_db(config):
    """
    数据库初始化：
      1. 创建数据库文件（sqlite3.connect 会自动创建）；
      2. 检查表是否存在，不存在则创建表。
    """
    db_path = _db_path(config)
    table = get_table(config)
    # 确保数据库文件所在目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = connect(config)
    try:
        # 检查表是否存在
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if cursor.fetchone() is None:
            # 创建表：class_code 班级 URI（主键），distance 班级里程（米）
            conn.execute(
                f"CREATE TABLE {table} ("
                "class_code TEXT PRIMARY KEY NOT NULL, "
                "distance INTEGER NOT NULL DEFAULT 0)"
            )
            conn.commit()
            return True  # 新建了表
        return False  # 表已存在
    finally:
        conn.close()


def valid_class_code(class_code):
    """
    校验班级代号是否符合规则：
      - 101-199 高一、201-299 高二、301-399 高三、
        401-499 高一国际部、501-599 高二国际部、601-699 高三国际部。
    返回 True / False。
    """
    if class_code is None:
        return False
    if not isinstance(class_code, str):
        class_code = str(class_code)
    if not class_code.isdigit():
        return False
    code = int(class_code)
    first = code // 100
    last_two = code % 100
    if code < 100 or code > 699:
        return False
    if first < 1 or first > 6:
        return False
    if last_two < 1 or last_two > 99:
        return False
    return True


def verify_password(config, password_hash):
    """
    校验密码密文（前端加密后的 SHA256 十六进制串）是否与配置中的密文一致。
    使用常数时间比较，避免时序攻击。返回 True / False。
    """
    stored = config['password']['hash']
    if not isinstance(password_hash, str):
        return False
    return hmac.compare_digest(stored.lower(), password_hash.lower())


def query_class(config, class_code):
    """
    查询某班级的里程。
    参数：class_code - 班级代号（字符串或数字）。
    返回：该班级的里程（整数）；若班级不存在返回 None。
    """
    conn = connect(config)
    try:
        cursor = conn.execute(
            f"SELECT distance FROM {get_table(config)} WHERE class_code=?",
            (str(class_code),)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return row['distance']
    finally:
        conn.close()


def insert_class(config, class_code, distance):
    """
    写入班级里程数据：若班级不存在则插入新纪录，若班级已存在则用新数据覆写旧数据。
    参数：class_code - 班级代号；distance - 里程（米，整数）。
    返回：受影响行数。
    """
    conn = connect(config)
    try:
        cur = conn.execute(
            f"INSERT INTO {get_table(config)} (class_code, distance) VALUES (?, ?) "
            f"ON CONFLICT(class_code) DO UPDATE SET distance = excluded.distance",
            (str(class_code), int(distance))
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def add_distance(config, class_code, distance):
    """
    为某班级累加里程：
      - 班级不存在时，插入新纪录（里程 = distance）；
      - 班级已存在时，在原有总里程基础上累加 distance。
    返回：受影响行数（恒为 1）。
    """
    conn = connect(config)
    try:
        cur = conn.execute(
            f"INSERT INTO {get_table(config)} (class_code, distance) VALUES (?, ?) "
            f"ON CONFLICT(class_code) DO UPDATE SET distance = distance + excluded.distance",
            (str(class_code), int(distance))
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def delete_class(config, class_code):
    """
    删除某班级的数据。返回：受影响行数（0 表示班级不存在）。
    """
    conn = connect(config)
    try:
        cur = conn.execute(
            f"DELETE FROM {get_table(config)} WHERE class_code=?",
            (str(class_code),)
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def query_all(config):
    """
    查询所有班级数据，按里程降序排列（里程相同时按班级代号升序）。
    返回：列表，元素为 {"class_code": ..., "distance": ...}。
    """
    conn = connect(config)
    try:
        rows = conn.execute(
            f"SELECT class_code, distance FROM {get_table(config)} "
            "ORDER BY distance DESC, class_code ASC"
        ).fetchall()
        return [{"class_code": r['class_code'], "distance": r['distance']} for r in rows]
    finally:
        conn.close()


def sum_distance(config):
    """
    查询所有班级里程之和（单个数据）。若没有任何数据返回 0。
    """
    conn = connect(config)
    try:
        row = conn.execute(
            f"SELECT COALESCE(SUM(distance), 0) AS total FROM {get_table(config)}"
        ).fetchone()
        return int(row['total'])
    finally:
        conn.close()
