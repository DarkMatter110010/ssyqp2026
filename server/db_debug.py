# -*- coding: utf-8 -*-
"""
db_debug.py - 数据库调试工具（PyQt6）

直接在服务器端运行，通过 db_tool.py 中的函数进行数据库的查看、插入、删除、更新等操作。
界面包含两个选项卡：
  - 数据写入：使用 QLineEdit 和 QPushButton 输入班级代号和里程，直接向数据库写入数据；
  - 数据查看：使用 QListWidget 显示数据库中的所有数据。
"""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QCheckBox
)

import db_tool

# 读取配置并初始化数据库
CONFIG = db_tool.load_config()
db_tool.init_db(CONFIG)

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
    font-size: 26px;
    font-weight: bold;
    letter-spacing: 3px;
}
QLabel#subtitle {
    color: #3a7ca5;
    font-size: 13px;
}
QLabel#fieldLabel {
    color: #3d5a73;
    font-size: 15px;
    font-weight: bold;
}
QTabWidget::pane {
    border: 2px solid #b9d0e2;
    border-radius: 12px;
    background: #fff;
    top: -1px;
}
QTabBar::tab {
    background: #d5e3f0;
    color: #3d5a73;
    padding: 10px 26px;
    margin-right: 6px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-size: 15px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #1f5d8f;
    color: #fff;
}
QLineEdit {
    border: 2px solid #a9c6de;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 18px;
    color: #33475c;
    background: #f4f9fd;
    selection-background-color: #3a7ca5;
}
QLineEdit:focus {
    border-color: #3a7ca5;
}
QPushButton {
    border: none;
    border-radius: 10px;
    padding: 12px 22px;
    font-size: 16px;
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
QListWidget {
    border: 2px solid #b9d0e2;
    border-radius: 10px;
    background: #fff;
    font-size: 13px;
    color: #33475c;
    padding: 4px;
    alternate-background-color: #eef5fb;
}
QListWidget::item {
    padding: 3px 6px;
    border-bottom: 1px dashed #dbe7f2;
}
QListWidget::item:selected {
    background: #cfe3f2;
    color: #24567a;
}
QLabel#statusOk {
    color: #1e7d34;
    font-size: 14px;
    font-weight: bold;
    background: #e3f6e7;
    border: 1px solid #b5e3c1;
    border-radius: 8px;
    padding: 8px;
}
QLabel#statusErr {
    color: #c0392b;
    font-size: 14px;
    font-weight: bold;
    background: #fdeceb;
    border: 1px solid #f3c0bc;
    border-radius: 8px;
    padding: 8px;
}
QLabel#sumLabel {
    color: #1f6f9f;
    font-size: 13px;
    font-weight: bold;
    background: #e8f2fa;
    border: 1px solid #c4dcef;
    border-radius: 6px;
    padding: 3px 10px;
}
QPushButton#btnRefresh {
    background: #5a7186;
    padding: 6px 14px;
    font-size: 13px;
}
QPushButton#btnRefresh:hover { background: #6d869e; }
QCheckBox#checkTop {
    color: #3d5a73;
    font-size: 14px;
    font-weight: bold;
    spacing: 6px;
}
QCheckBox#checkTop::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #a9c6de;
    border-radius: 5px;
    background: #f4f9fd;
}
QCheckBox#checkTop::indicator:checked {
    background: #1f5d8f;
    border-color: #1f5d8f;
}
"""


class DebugWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('数据库调试')
        self.setFixedSize(660, 600)  # 固定窗口大小，不可调整
        self.setStyleSheet(QSS)

        central = QWidget()
        central.setObjectName('central')
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 24)
        root.setSpacing(12)

        # 标题
        title = QLabel('数据库调试')
        title.setObjectName('title')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel('数据库文件：' + CONFIG['database']['path'] + '　　表：' + CONFIG['database']['table'])
        sub.setObjectName('subtitle')
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        root.addWidget(sub)

        # 选项卡
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)
        self.tabs.addTab(self._build_write_tab(), '数据写入')
        self.tabs.addTab(self._build_view_tab(), '数据查看')

        # 右下角置顶复选框（放在标签页之外）
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 4, 0)
        bottom_row.addStretch(1)
        self.check_top = QCheckBox('置顶')
        self.check_top.setObjectName('checkTop')
        self.check_top.toggled.connect(self.on_top_toggle)
        bottom_row.addWidget(self.check_top)
        root.addLayout(bottom_row)

    # ------------------------------------------------------------------
    def _build_write_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        layout.addWidget(self._field('班级代号：', 'class'))

        layout.addWidget(self._field('里程（米）：', 'distance'))

        # 按钮区
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
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
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(8)

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
        """读取班级代号与里程；里程允许为负数或 0（负数用于冲减多记的里程）。"""
        class_code = self.class_edit.text().strip()
        distance_text = self.distance_edit.text().strip()
        if not db_tool.valid_class_code(class_code):
            raise ValueError('班级代号不合法')
        try:
            distance = int(distance_text) if distance_text else 0
        except ValueError:
            raise ValueError('里程必须为整数')
        return class_code, distance

    def _show_ok(self, msg):
        self.write_status.setStyleSheet(
            "color:#1e7d34; background:#e3f6e7; border:1px solid #b5e3c1;"
            "border-radius:8px; padding:8px; font-size:14px; font-weight:bold;")
        self.write_status.setText(msg)

    def _show_err(self, msg):
        self.write_status.setStyleSheet(
            "color:#c0392b; background:#fdeceb; border:1px solid #f3c0bc;"
            "border-radius:8px; padding:8px; font-size:14px; font-weight:bold;")
        self.write_status.setText(msg)

    def _guard(self, fn):
        """统一执行并捕获异常。"""
        try:
            fn()
        except ValueError as e:
            self._show_err(str(e))
        except Exception as e:  # noqa: BLE001
            self._show_err('操作失败：' + str(e))

    def _refresh_view(self):
        self.list_widget.clear()
        for item in db_tool.query_all(CONFIG):
            row = QListWidgetItem(f"{item['class_code']} 　　　　　　 {item['distance']} 米")
            row.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.list_widget.addItem(row)
        total = db_tool.sum_distance(CONFIG)
        self.sum_label.setText(f'总里程：{total:,} 米')

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def on_insert(self):
        def run():
            class_code, distance = self._read_inputs()
            db_tool.insert_class(CONFIG, class_code, distance)
            self._show_ok(f'已写入：班级 {class_code}，里程 {distance} 米')
            self._refresh_view()
        self._guard(run)

    def on_add(self):
        def run():
            class_code, distance = self._read_inputs()
            db_tool.add_distance(CONFIG, class_code, distance)
            new_val = db_tool.query_class(CONFIG, class_code)
            self._show_ok(f'已累加：班级 {class_code} 累加 {distance} 米，现总里程 {new_val} 米')
            self._refresh_view()
        self._guard(run)

    def on_delete(self):
        def run():
            class_code = self.class_edit.text().strip()
            if not db_tool.valid_class_code(class_code):
                raise ValueError('班级代号不合法')
            if db_tool.delete_class(CONFIG, class_code) == 0:
                raise ValueError('该班级暂无数据')
            self._show_ok(f'已删除：班级 {class_code}')
            self._refresh_view()
        self._guard(run)

    def on_refresh(self):
        self._refresh_view()

    def on_top_toggle(self, checked):
        """点击右下角"置顶"复选框，开启/关闭窗口置顶。"""
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Microsoft YaHei', 10))
    window = DebugWindow()
    window.on_refresh()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
