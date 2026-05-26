import os
import sys
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QLinearGradient
from PyQt6.QtCore import Qt, pyqtSignal
from languages import get_grouped_languages


def _base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _resource_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _create_icon():
    px = QPixmap(64, 64)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, 64, 64)
    grad.setColorAt(0.0, QColor(26, 115, 232))
    grad.setColorAt(1.0, QColor(66, 133, 244))
    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(2, 2, 60, 60, 14, 14)
    p.setPen(QColor(255, 255, 255))
    p.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    p.end()
    return QIcon(px)


class TrayIcon(QSystemTrayIcon):
    translate_clipboard = pyqtSignal()
    screenshot_translate = pyqtSignal()
    language_changed = pyqtSignal(str)
    open_settings = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        icon_ico = os.path.join(_resource_dir(), "resources", "icon.ico")
        self.setIcon(QIcon(icon_ico) if os.path.exists(icon_ico) else _create_icon())

        self._build_menu()
        self.activated.connect(self._on_activated)
        self.setToolTip("HoverTranslator — Ctrl+T 截图翻译 · 右键设置")

    def _build_menu(self):
        menu = QMenu()

        menu.addAction("✂️ 截图选区翻译 (Ctrl+T)").triggered.connect(
            self.screenshot_translate.emit
        )
        menu.addAction("📋 翻译剪贴板").triggered.connect(
            self.translate_clipboard.emit
        )
        menu.addSeparator()

        self._lang_menu = menu.addMenu("🌐 目标语言")
        self._build_language_menu()
        menu.addSeparator()

        theme_menu = menu.addMenu("🎨 主题")
        theme_menu.addAction("☀️ 浅色").triggered.connect(lambda: self._set_theme("light"))
        theme_menu.addAction("🌙 深色").triggered.connect(lambda: self._set_theme("dark"))
        menu.addSeparator()

        menu.addAction("⚙️ 设置").triggered.connect(self.open_settings.emit)
        menu.addAction("ℹ️ 关于").triggered.connect(self._show_about)
        menu.addAction("❌ 退出").triggered.connect(QApplication.quit)

        self.setContextMenu(menu)

    def _build_language_menu(self):
        current_target = self.config["target_lang"]
        for group_name, langs in get_grouped_languages().items():
            group_menu = self._lang_menu.addMenu(group_name)
            for lang in langs:
                action = group_menu.addAction(f'{lang["flag"]}  {lang["name"]}')
                action.setCheckable(True)
                action.setChecked(lang["code"] == current_target)
                action.triggered.connect(
                    lambda checked, code=lang["code"]: self._on_lang(code)
                )

    def _on_lang(self, code):
        self.config["target_lang"] = code
        self.language_changed.emit(code)
        self._lang_menu.clear()
        self._build_language_menu()

    def _set_theme(self, theme):
        self.config["theme"] = theme

    def _show_about(self):
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("关于 HoverTranslator")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(
            "<h3>HoverTranslator v0.12.2</h3>"
            "<p>Windows 桌面翻译工具</p>"
            "<hr>"
            "<p><b>快捷键</b></p>"
            "<p>Ctrl+T — 截图选区翻译</p>"
            "<p>Ctrl+Q — 快捷翻译选中文字</p>"
            "<p>ESC — 关闭翻译面板</p>"
            "<hr>"
            "<p><b>翻译引擎</b>：Google / MyMemory / DeepL / 百度 / Microsoft</p>"
            "<p><b>OCR 引擎</b>：RapidOCR（ONNX Runtime，离线）</p>"
            "<p><b>字体</b>：Noto Sans SC + HarmonyOS Sans SC</p>"
            "<hr>"
            "<p>MIT License</p>"
        )
        msg.exec()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.screenshot_translate.emit()

    def rebuild_language_menu(self):
        """外部（设置窗口）切换语言后，重建语言子菜单以更新勾选状态。"""
        self._lang_menu.clear()
        self._build_language_menu()

    def update_proxy_status(self, text):
        self.setToolTip(f"HoverTranslator — {text}\nCtrl+T 截图翻译 · 右键设置")
