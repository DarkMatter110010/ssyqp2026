# -*- coding: utf-8 -*-
"""
db_client.py - 数据管理客户端（PyQt6）

通过 HTTP/HTTPS 请求后端 API 完成数据的查看、写入、累加、删除，不直接接触数据库。
连接地址与后缀盐在 settings.ini 中配置（需与 server/config.json 一致）；密码由用户在界面输入。
"""

import configparser
import hashlib
import http.client
import json
import os
import ssl
import sys
import threading
import urllib.parse

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QCheckBox
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, 'settings.ini')

# HTTPS 自签名证书：客户端不做证书校验
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def load_settings(path=SETTINGS_PATH):
    cp = configparser.ConfigParser()
    cp.read(path, encoding='utf-8')
    return cp


SETTINGS = load_settings()
BACKUP_HOST = "127.100.10.1"
BACKUP_PORT = "7443"


def api_base():
    url = SETTINGS.get('server', 'url', fallback='').strip().rstrip('/')
    if url:
        return url
    host = SETTINGS.get('server', 'host', fallback=BACKUP_HOST)
    port = SETTINGS.get('server', 'port', fallback=BACKUP_PORT)
    return f'http://{host}:{port}'


def password_hash(raw_password):
    """计算 SHA256(用户密码 + 后缀盐)，用于后端密码校验。"""
    salt = SETTINGS.get('security', 'salt', fallback='')
    return hashlib.sha256((raw_password + salt).encode('utf-8')).hexdigest()


_REQ_LOCK = threading.Lock()
_HTTP_CONN = None


def save_setting(section, key, value):
    """把界面设置写回 settings.ini（失败时静默忽略，不阻塞界面）。"""
    if not SETTINGS.has_section(section):
        SETTINGS.add_section(section)
    SETTINGS.set(section, key, 'true' if value else 'false')
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            SETTINGS.write(f)
    except OSError:
        pass


def _reset_conn():
    global _HTTP_CONN
    _HTTP_CONN = None


def _get_conn():
    global _HTTP_CONN
    if _HTTP_CONN is None:
        parsed = urllib.parse.urlparse(api_base())
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        if parsed.scheme == 'https':
            _HTTP_CONN = http.client.HTTPSConnection(host, port, context=_SSL_CTX, timeout=8)
        else:
            _HTTP_CONN = http.client.HTTPConnection(host, port, timeout=8)
    return _HTTP_CONN


def _send(path, payload):
    conn = _get_conn()
    data = json.dumps(payload or {}).encode('utf-8')
    conn.request('POST', path, body=data,
                 headers={'Content-Type': 'application/json'})
    resp = conn.getresponse()
    return json.loads(resp.read().decode('utf-8'))


def api_request(path, payload=None, retry=False, fresh=False):
    """向后端发送 POST JSON 请求（连接复用），返回解析后的字典。

    retry=True 时连接失效会自动重连一次；仅用于幂等请求（列表/汇总），
    写操作（写入/累加/删除）不得传 True，避免重复执行。
    fresh=True 时强制使用全新连接（写操作），避免复用已空闲失效的连接。
    """
    with _REQ_LOCK:
        if fresh:
            _reset_conn()
        try:
            return _send(path, payload)
        except (http.client.HTTPException, OSError):
            _reset_conn()
            if not retry:
                raise
            return _send(path, payload)


def valid_class_code(code):
    """班级代号校验：101-699，百位 1-6，后两位 1-99。"""
    if code is None:
        return False
    s = str(code).strip()
    if not s.isdigit():
        return False
    n = int(s)
    if n < 100 or n > 699:
        return False
    if n // 100 not in (1, 2, 3, 4, 5, 6):
        return False
    if n % 100 < 1 or n % 100 > 99:
        return False
    return True


QSS = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #eaf2f8, stop:0.5 #dbe8f2, stop:1 #ccdcea);
}
QWidget#central {
    background: transparent;
}
QLabel#title {
    color: #1f5d8f;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 2px;
}
QLabel#subtitle {
    color: #3a7ca5;
    font-size: 11px;
}
QLabel#fieldLabel {
    color: #3d5a73;
    font-size: 12px;
    font-weight: bold;
}
QTabWidget::pane {
    border: 2px solid #b9d0e2;
    border-radius: 8px;
    background: #fff;
    top: -1px;
}
QTabBar::tab {
    background: #d5e3f0;
    color: #3d5a73;
    padding: 5px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 12px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #1f5d8f;
    color: #fff;
}
QLineEdit {
    border: 2px solid #a9c6de;
    border-radius: 7px;
    padding: 5px 9px;
    font-size: 13px;
    color: #33475c;
    background: #f4f9fd;
    selection-background-color: #3a7ca5;
}
QLineEdit:focus {
    border-color: #3a7ca5;
}
QPushButton {
    border: none;
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: bold;
    color: #fff;
}
QPushButton#btnInsert {
    background: #1f5d8f;
}
QPushButton#btnInsert:hover { background: #2a6fa8; }
QPushButton#btnAdd {
    background: #2e7d78;
}
QPushButton#btnAdd:hover { background: #3a948e; }
QPushButton#btnDelete {
    background: #b03a48;
}
QPushButton#btnDelete:hover { background: #c74a58; }
QPushButton:disabled {
    background: #9fb3c4;
}
QListWidget {
    border: 2px solid #b9d0e2;
    border-radius: 8px;
    background: #fff;
    font-size: 11px;
    color: #33475c;
    padding: 3px;
    alternate-background-color: #eef5fb;
}
QListWidget::item {
    padding: 2px 5px;
    border-bottom: 1px dashed #dbe7f2;
}
QListWidget::item:selected {
    background: #cfe3f2;
    color: #24567a;
}
QLabel#statusOk {
    color: #1e7d34;
    font-size: 11px;
    font-weight: bold;
    background: #e3f6e7;
    border: 1px solid #b5e3c1;
    border-radius: 6px;
    padding: 4px;
}
QLabel#statusErr {
    color: #c0392b;
    font-size: 11px;
    font-weight: bold;
    background: #fdeceb;
    border: 1px solid #f3c0bc;
    border-radius: 6px;
    padding: 4px;
}
QLabel#sumLabel {
    color: #1f6f9f;
    font-size: 11px;
    font-weight: bold;
    background: #e8f2fa;
    border: 1px solid #c4dcef;
    border-radius: 5px;
    padding: 3px 8px;
}
QPushButton#btnRefresh {
    background: #5a7186;
    padding: 4px 10px;
    font-size: 11px;
}
QPushButton#btnRefresh:hover { background: #6d869e; }
QCheckBox#checkTop {
    color: #3d5a73;
    font-size: 11px;
    font-weight: bold;
    spacing: 4px;
}
QCheckBox#checkTop::indicator {
    width: 14px;
    height: 14px;
    border: 2px solid #a9c6de;
    border-radius: 4px;
    background: #f4f9fd;
}
QCheckBox#checkTop::indicator:checked {
    background: #1f5d8f;
    border-color: #1f5d8f;
}
"""


class ApiSignals(QObject):
    """后台任务完成信号（跨线程自动排队回主线程）。"""
    ok = pyqtSignal(list)   # 依次为各请求的响应 dict
    err = pyqtSignal(str)   # 错误消息


class ApiTask(QRunnable):
    """在后台线程串行执行一串请求，避免阻塞 UI。"""

    def __init__(self, requests, safe_retry=False, fresh_main=False):
        super().__init__()
        self.requests = requests            # [(path, payload), ...]
        self.safe_retry = safe_retry        # 允许连接失效后重试（仅限幂等请求）
        self.fresh_main = fresh_main        # 主请求强制新连接（写操作）
        self.sig = ApiSignals()

    def run(self):
        try:
            results = []
            for i, (path, payload) in enumerate(self.requests):
                resp = api_request(path, payload, retry=self.safe_retry,
                                   fresh=(self.fresh_main and i == 0))
                # 主请求业务失败（如密码错误）必须如实报错，不能显示成功
                if i == 0 and resp.get('status') != 'ok':
                    raise RuntimeError(resp.get('message') or '操作失败')
                results.append(resp)
            self.sig.ok.emit(results)
        except Exception as e:  # noqa: BLE001
            self.sig.err.emit(str(e))


class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('数据管理')
        self.setFixedSize(300, 400)  # 固定窗口大小，不可调整
        self.setStyleSheet(QSS)
        self._pending_task = None  # 当前进行中的后台任务

        central = QWidget()
        central.setObjectName('central')
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 10, 16, 12)
        root.setSpacing(8)

        # 标题
        title = QLabel('数据管理')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel('后端地址：' + api_base())
        sub.setObjectName('subtitle')
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        root.addWidget(sub)

        # 选项卡
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)
        self.tabs.addTab(self._build_write_tab(), '数据写入')
        self.tabs.addTab(self._build_view_tab(), '数据查看')

        # 底部复选框（放在标签页之外），状态变更即时写回 settings.ini
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 4, 0)
        self.check_clear = QCheckBox('自动清空班级代号和里程')
        self.check_clear.setObjectName('checkTop')
        self.check_clear.setChecked(SETTINGS.getboolean('setting', 'selfclean', fallback=True))
        self.check_clear.toggled.connect(lambda v: save_setting('setting', 'selfclean', v))
        bottom_row.addWidget(self.check_clear)
        bottom_row.addStretch(1)
        self.check_top = QCheckBox('置顶')
        self.check_top.setObjectName('checkTop')
        self.check_top.setChecked(SETTINGS.getboolean('setting', 'topmost', fallback=True))
        self.check_top.toggled.connect(lambda v: save_setting('setting', 'topmost', v))
        self.check_top.toggled.connect(self.on_top_toggle)
        bottom_row.addWidget(self.check_top)
        root.addLayout(bottom_row)

        # 启动时应用配置的置顶状态
        self.on_top_toggle(self.check_top.isChecked())

    # ------------------------------------------------------------------
    def _build_write_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(7)

        layout.addWidget(self._field('班级代号：', 'class'))

        layout.addWidget(self._field('里程（米）：', 'distance'))

        # 密码（用户输入，提交后不清空）
        layout.addWidget(self._field('密　码：', 'password'))
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        # 按钮区
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_insert = QPushButton('写入')
        self.btn_insert.setObjectName('btnInsert')
        self.btn_add = QPushButton('累加')
        self.btn_add.setObjectName('btnAdd')
        self.btn_delete = QPushButton('删除')
        self.btn_delete.setObjectName('btnDelete')
        for b in (self.btn_insert, self.btn_add, self.btn_delete):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self.write_status = QLabel('')
        layout.addWidget(self.write_status)
        layout.addStretch(1)

        self.btn_insert.clicked.connect(self.on_insert)
        self.btn_add.clicked.connect(self.on_add)
        self.btn_delete.clicked.connect(self.on_delete)

        return page

    def _field(self, text, obj_name):
        """构造一个带标签的输入行（无占位文字）。"""
        frame = QFrame()
        box = QHBoxLayout(frame)
        box.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        label.setObjectName('fieldLabel')
        edit = QLineEdit()
        edit.setObjectName(obj_name)
        box.addWidget(label)
        box.addWidget(edit)
        setattr(self, obj_name + '_edit', edit)
        return frame

    # ------------------------------------------------------------------
    def _build_view_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(5)

        top = QHBoxLayout()
        self.sum_label = QLabel('总里程：0 米')
        self.sum_label.setObjectName('sumLabel')
        self.btn_refresh = QPushButton('刷新')
        self.btn_refresh.setObjectName('btnRefresh')
        top.addWidget(self.sum_label)
        top.addStretch(1)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)

        self.btn_refresh.clicked.connect(self.on_refresh)
        return page

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    def _read_inputs(self):
        """读取班级代号与里程；里程须为 0~9999999 的整数。"""
        class_code = self.class_edit.text().strip()
        distance_text = self.distance_edit.text().strip()
        if not valid_class_code(class_code):
            raise ValueError('班级代号不合法')
        try:
            distance = int(distance_text) if distance_text else 0
        except ValueError:
            raise ValueError('里程必须为整数')
        if distance < 0 or distance > 9999999:
            raise ValueError('里程需为 0~9999999 的整数')
        return class_code, distance

    def _read_password(self):
        """读取界面输入的密码并计算密文；密码提交后始终保留。"""
        pwd = self.password_edit.text()
        if not pwd:
            raise ValueError('密码不能为空')
        return password_hash(pwd)

    def _maybe_clear_inputs(self):
        """按底部复选框决定是否清空班级代号与里程（密码框始终不清空）。"""
        if self.check_clear.isChecked():
            self.class_edit.clear()
            self.distance_edit.clear()

    def _show_ok(self, msg):
        self.write_status.setStyleSheet(
            "color:#1e7d34; background:#e3f6e7; border:1px solid #b5e3c1;"
            "border-radius:6px; padding:4px; font-size:11px; font-weight:bold;")
        self.write_status.setText(msg)

    def _show_err(self, msg):
        self.write_status.setStyleSheet(
            "color:#c0392b; background:#fdeceb; border:1px solid #f3c0bc;"
            "border-radius:6px; padding:4px; font-size:11px; font-weight:bold;")
        self.write_status.setText(msg)

    def _set_busy(self, busy):
        """请求期间禁用按钮并提示，防止重复提交。"""
        self.btn_insert.setEnabled(not busy)
        self.btn_add.setEnabled(not busy)
        self.btn_delete.setEnabled(not busy)
        self.btn_refresh.setEnabled(not busy)
        if busy:
            self.write_status.setStyleSheet(
                "color:#5a7186; background:#eef2f5; border:1px solid #c9d6e0;"
                "border-radius:6px; padding:4px; font-size:11px; font-weight:bold;")
            self.write_status.setText('请求中…')

    def _run_api(self, requests, on_ok=None, safe_retry=False, fresh_main=False):
        """后台执行请求列表，完成后在主线程回调 on_ok(results)。"""
        task = ApiTask(requests, safe_retry=safe_retry, fresh_main=fresh_main)
        task.on_ok = on_ok
        self._pending_task = task
        # 连接窗口实例方法：信号在后台线程发射，自动排队回主线程执行
        task.sig.ok.connect(self._handle_api_ok)
        task.sig.err.connect(self._handle_api_err)
        self._set_busy(True)
        QThreadPool.globalInstance().start(task)

    def _handle_api_ok(self, results):
        """请求成功（在主线程执行）。"""
        task, self._pending_task = self._pending_task, None
        self._set_busy(False)
        if task is not None and task.on_ok:
            task.on_ok(results)

    def _handle_api_err(self, msg):
        """请求失败（在主线程执行）。"""
        self._pending_task = None
        self._set_busy(False)
        self._show_err('请求失败：' + msg)

    def _apply_list(self, data):
        self.list_widget.clear()
        for item in data.get('data', []):
            row = QListWidgetItem(f"{item['class_code']} 　　　　　　 {item['distance']} 米")
            row.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.list_widget.addItem(row)

    def _apply_sum(self, data):
        self.sum_label.setText(f"总里程：{data.get('sum_distance', 0):,} 米")

    def _apply_view(self, results):
        """results 为 [list 响应, sum 响应]，更新查看页。"""
        if results and results[0].get('status') == 'ok':
            self._apply_list(results[0])
        if len(results) >= 2:
            self._apply_sum(results[1])

    def _after_mutate(self, msg, results):
        """写操作成功后的统一收尾：提示、按需清空、刷新查看页。"""
        self._show_ok(msg)
        self._maybe_clear_inputs()
        self._apply_view(results[1:])

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def on_insert(self):
        try:
            class_code, distance = self._read_inputs()
            password = self._read_password()
        except ValueError as e:
            self._show_err(str(e))
            return
        payload = {'class_code': class_code, 'password': password, 'distance': distance}
        self._run_api(
            [('/api/write', payload), ('/api/list', None), ('/api/sum', None)],
            on_ok=lambda r, c=class_code, d=distance: self._after_mutate(
                f'已写入：班级 {c}，里程 {d} 米', r),
            fresh_main=True)

    def on_add(self):
        try:
            class_code, distance = self._read_inputs()
            password = self._read_password()
        except ValueError as e:
            self._show_err(str(e))
            return
        payload = {'class_code': class_code, 'password': password, 'distance': distance}
        self._run_api(
            [('/api/add', payload), ('/api/list', None), ('/api/sum', None)],
            on_ok=lambda r, c=class_code, d=distance: self._after_mutate(
                f'已累加：班级 {c}，累加 {d} 米', r),
            fresh_main=True)

    def on_delete(self):
        try:
            class_code = self.class_edit.text().strip()
            if not valid_class_code(class_code):
                raise ValueError('班级代号不合法')
            password = self._read_password()
        except ValueError as e:
            self._show_err(str(e))
            return
        payload = {'class_code': class_code, 'password': password}
        self._run_api(
            [('/api/delete', payload), ('/api/list', None), ('/api/sum', None)],
            on_ok=lambda r, c=class_code: self._after_mutate(f'已删除：班级 {c}', r),
            fresh_main=True)

    def _on_refreshed(self, results):
        self._apply_view(results)
        self._show_ok('已刷新')

    def on_refresh(self):
        self._run_api([('/api/list', None), ('/api/sum', None)],
                      on_ok=self._on_refreshed, safe_retry=True)

    def on_top_toggle(self, checked):
        """点击右下角"置顶"复选框，开启/关闭窗口置顶。"""
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Microsoft YaHei', 9))
    window = ClientWindow()
    window.on_refresh()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
