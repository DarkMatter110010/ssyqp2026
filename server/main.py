# -*- coding: utf-8 -*-
import os
import threading
from flask import Flask, request, jsonify, render_template, redirect, url_for

import db_tool

app = Flask(__name__)
app.json.ensure_ascii = False

config = db_tool.load_config()
db_tool.init_db(config)

HOST: str = config['server']['host']
PORT: int = config['server']['port']


@app.route('/')
@app.route('/index')
def redirect_index():
    return redirect(url_for('index_page'))
@app.route('/index.html', methods=['GET'])
def index_page():
    return render_template('index.html')


@app.route('/config')
def redirect_config():
    return redirect(url_for('config_page'))
@app.route('/config.html', methods=['GET'])
def config_page():
    return render_template('config.html')





def _respond(ok, **extra):
    """成功 status=ok，失败 status=error。"""
    if ok:
        body = {'status': 'ok'}
    else:
        body = {'status': 'error'}
    body.update(extra)
    return jsonify(body)


def _get_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@app.route('/api/add', methods=['POST'])
def api_add():
    """
    请求体：{"class_code": int, "distance": int, "password": str}
    """
    data = _get_json()
    class_code = data.get('class_code')
    distance = data.get('distance')
    password = data.get('password')

    if not db_tool.valid_class_code(class_code):
        return _respond(False, message='班级代号不合法')
    if not password:
        return _respond(False, message='密码不能为空')
    if not db_tool.verify_password(config, password):
        return _respond(False, message='密码错误')

    # 里程为空按 0 处理；必须为 0~9999999 的整数（不超过 7 位）
    try:
        distance = int(distance) if distance not in (None, '') else 0
        if distance < 0:
            return _respond(False, message='里程不能为负数')
        if distance > 9999999:
            return _respond(False, message='里程不能超过 7 位数字')
    except (ValueError, TypeError):
        return _respond(False, message='里程格式不正确')

    db_tool.add_distance(config, class_code, distance)
    return _respond(True)


@app.route('/api/write', methods=['POST'])
def api_write():
    """
    覆盖写入（设置）某班级里程：
    请求体：{"class_code": int, "distance": int, "password": str}
    响应体：{"status": ..., "message": ...}
    """
    data = _get_json()
    class_code = data.get('class_code')
    distance = data.get('distance')
    password = data.get('password')

    if not db_tool.valid_class_code(class_code):
        return _respond(False, message='班级代号不合法')
    if not password:
        return _respond(False, message='密码不能为空')
    if not db_tool.verify_password(config, password):
        return _respond(False, message='密码错误')

    # 里程为空按 0 处理；必须为 0~9999999 的整数（不超过 7 位）
    try:
        distance = int(distance) if distance not in (None, '') else 0
        if distance < 0:
            return _respond(False, message='里程不能为负数')
        if distance > 9999999:
            return _respond(False, message='里程不能超过 7 位数字')
    except (ValueError, TypeError):
        return _respond(False, message='里程格式不正确')

    db_tool.insert_class(config, class_code, distance)
    return _respond(True)


@app.route('/api/query', methods=['POST'])
def api_query():
    """
    请求体：{"class_code": "..."}
    响应体：{"status": ..., "distance": ...}
    """
    data = _get_json()
    class_code = data.get('class_code')

    if not db_tool.valid_class_code(class_code):
        return _respond(False, message='班级代号不合法')

    distance = db_tool.query_class(config, class_code)
    if distance is None:
        return _respond(False, message='该班级暂无数据')

    return _respond(True, distance=distance)


@app.route('/api/delete', methods=['POST'])
def api_delete():
    """
    请求体：{"class_code": "...", "password": "..."}
    """
    data = _get_json()
    class_code = data.get('class_code')
    password = data.get('password')

    if not db_tool.valid_class_code(class_code):
        return _respond(False, message='班级代号不合法')
    if not password:
        return _respond(False, message='密码不能为空')
    if not db_tool.verify_password(config, password):
        return _respond(False, message='密码错误')

    if db_tool.delete_class(config, class_code) == 0:
        return _respond(False, message='该班级暂无数据')

    return _respond(True)


@app.route('/api/sum', methods=['POST'])
def api_sum():
    """
    请求体：{}
    响应体：{"status": ..., "sum_distance": ...}
    """
    return _respond(True, sum_distance=db_tool.sum_distance(config))


@app.route('/api/list', methods=['POST'])
def api_list():
    """
    响应体：{"status": ..., "data": [{"class_code": ..., "distance": ...}, ...]}
    """
    return _respond(True, data=db_tool.query_all(config))


if __name__ == '__main__':
    # 通过 config.json 的 ssl 配置启用 HTTPS（证书缺失时自动回退 HTTP）
    ssl_ctx = None
    ssl_cfg = config.get('ssl') or {}
    if ssl_cfg.get('enabled'):
        cert, key = ssl_cfg.get('cert'), ssl_cfg.get('key')
        if cert and key and os.path.exists(cert) and os.path.exists(key):
            ssl_ctx = (cert, key)
        else:
            print('[警告] ssl.enabled=true 但证书文件不存在，将以 HTTP 启动')

    access_url = config.get('server', {}).get('access_url')
    if not access_url:
        scheme = 'https' if ssl_ctx else 'http'
        nginx_port = config.get('server', {}).get('nginx_port', 7443)
        access_url = f'{scheme}://{HOST}:{nginx_port}/'

    # app.run 会阻塞主线程，用 Timer 在独立线程延迟打印，确保服务已就绪
    threading.Timer(1.5, lambda: print(f'\n>>> 益起跑已启动，浏览器访问：{access_url}\n')).start()
    app.run(host=HOST, port=PORT, debug=False, ssl_context=ssl_ctx)
