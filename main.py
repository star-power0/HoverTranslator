"""
HoverTranslator 主程序。

两种翻译方式：
  1. Ctrl+T → 截图选区 → OCR → 翻译（主要方式）
  2. Ctrl+Q → 复制选中文字 → 翻译（备选方式）
"""

import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, QRect

from config import Config
from translator import Translator
from tooltip import TranslationPanel
from hotkey_manager import HotkeyManager
from tray_icon import TrayIcon
from proxy_detector import detect_proxy
from selector import ScreenSelector
from ocr_engine import OcrWorker
from font_manager import get_font
from settings_window import SettingsWindow


def is_already_running():
    try:
        ctypes.windll.kernel32.CreateMutexW(None, False, "HoverTranslatorMutex")
        return ctypes.windll.kernel32.GetLastError() == 183
    except Exception:
        return False


class ProxyDetectThread(QThread):
    result = pyqtSignal(str)

    def __init__(self, user_proxy=""):
        super().__init__()
        self.user_proxy = user_proxy

    def run(self):
        proxy = detect_proxy(self.user_proxy)
        self.result.emit(proxy)


class HoverTranslatorApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("HoverTranslator")

        # 全局字体
        self.app.setFont(get_font(11))

        self.config = Config()
        self.translator = Translator(self.config)
        self.panel = TranslationPanel(self.config)
        self.selector = ScreenSelector()
        self.hotkey = HotkeyManager()
        self.tray = TrayIcon(self.config)
        self.settings_window = SettingsWindow(self.config)

        self._clipboard_text = ""
        self._ocr_worker = None
        self._request_id = 0
        self._translator_request_id = 0

        self._setup()

    def _setup(self):
        # 注册快捷键
        self.hotkey.register("ctrl+t")
        self.hotkey.register("ctrl+q")

        # 快捷键信号
        self.hotkey.triggered.connect(self._on_hotkey)
        # 选区完成 → OCR
        self.selector.region_selected.connect(self._on_region_selected)
        # 翻译结果
        self.translator.translated.connect(self._on_translated)
        # 卡片内语言切换
        self.panel.language_selected.connect(self._on_card_lang_changed)
        # 托盘
        self.tray.translate_clipboard.connect(self._on_translate_clipboard)
        self.tray.screenshot_translate.connect(self._start_screenshot)
        self.tray.language_changed.connect(lambda code: setattr(self, '_clipboard_text', ''))
        # 设置窗口
        self.tray.open_settings.connect(self._open_settings)
        self.settings_window.provider_changed.connect(self._on_provider_changed)
        self.settings_window.language_changed.connect(self._on_settings_lang_changed)
        self.settings_window.credentials_changed.connect(
            lambda: self.translator._cache.clear()
        )

    # ── 快捷键分发 ────────────────────────────────────────

    def _on_hotkey(self, name):
        if name == "ctrl+t":
            self._start_screenshot()
        elif name == "ctrl+q":
            self._quick_translate()

    # ── 截图选区翻译 ──────────────────────────────────────

    def _start_screenshot(self):
        self.selector.start_selection()

    def _on_region_selected(self, rect: QRect):
        self._request_id += 1
        rid = self._request_id
        bbox = (rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
        self._ocr_worker = OcrWorker(bbox)
        self._ocr_worker.finished.connect(lambda text: self._on_ocr_done(text, rid))
        self._ocr_worker.start()

    def _on_ocr_done(self, text, rid):
        if rid != self._request_id:
            return
        if text and len(text.strip()) >= 2:
            self._translator_request_id = rid
            self.panel.show_loading(text.strip())
            self.translator.translate(text.strip())

    # ── 快捷翻译（Ctrl+Q）─────────────────────────────────

    def _quick_translate(self):
        self._clipboard_before = QApplication.clipboard().text()
        user32 = ctypes.windll.user32
        VK_C, KEYUP = 0x43, 0x0002
        user32.keybd_event(0x11, 0, 0, 0)
        user32.keybd_event(VK_C, 0, 0, 0)
        user32.keybd_event(VK_C, 0, KEYUP, 0)
        user32.keybd_event(0x11, 0, KEYUP, 0)
        QTimer.singleShot(200, self._read_clipboard)

    def _read_clipboard(self):
        text = QApplication.clipboard().text()
        if text and text.strip() and text.strip() != self._clipboard_text:
            self._clipboard_text = text.strip()
            self._request_id += 1
            self._translator_request_id = self._request_id
            self.panel.show_loading(self._clipboard_text)
            self.translator.translate(self._clipboard_text)

    def _on_translate_clipboard(self):
        text = QApplication.clipboard().text()
        if text and text.strip():
            self._clipboard_text = text.strip()
            self._request_id += 1
            self._translator_request_id = self._request_id
            self.panel.show_loading(self._clipboard_text)
            self.translator.translate(self._clipboard_text)

    def _on_translated(self, original, result, lang):
        if self._request_id != self._translator_request_id:
            return
        src = getattr(self.translator, '_last_src', '')
        tgt = getattr(self.translator, '_last_target', '')
        self.panel.show_result(original, result, lang, src, tgt)

    def _on_card_lang_changed(self, code):
        """卡片内语言选择器切换语言后，用当前原文重新翻译。"""
        text = self.panel._source_label.text()
        if text and text.strip():
            self._request_id += 1
            self._translator_request_id = self._request_id
            self.panel.show_loading(text.strip())
            self.translator.translate(text.strip())

    # ── 设置窗口 ──────────────────────────────────────────

    def _open_settings(self):
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _on_provider_changed(self, provider):
        self.translator.set_provider(provider)

    def _on_settings_lang_changed(self, code):
        """设置窗口切换语言后，同步更新托盘菜单勾选。"""
        self.tray.rebuild_language_menu()

    # ── 代理检测 ──────────────────────────────────────────

    def _start_proxy_detection(self):
        self._proxy_thread = ProxyDetectThread(self.config.get("proxy", ""))
        self._proxy_thread.result.connect(self._on_proxy_detected)
        self._proxy_thread.start()

    def _on_proxy_detected(self, proxy):
        self.translator.set_proxy(proxy)
        names = {
            7890: "Clash", 10809: "V2Ray", 1080: "Shadowsocks",
            10871: "Trojan", 2080: "Surge",
        }
        if proxy:
            try:
                port = int(proxy.split(":")[-1].strip("/"))
                msg = f"已连接: {names.get(port, proxy)}"
            except (ValueError, IndexError):
                msg = f"已连接: {proxy}"
        else:
            msg = "直连模式"
        self.tray.update_proxy_status(msg)
        self.tray.showMessage("网络就绪", msg, QSystemTrayIcon.MessageIcon.Information, 3000)

    # ── 启动 ──────────────────────────────────────────────

    def run(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("系统不支持托盘图标")
            sys.exit(1)

        self.tray.show()
        self.hotkey.start()

        self.tray.showMessage(
            "HoverTranslator 已启动",
            "Ctrl+T 截图选区翻译\nCtrl+Q 快捷翻译选中文字",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )
        QTimer.singleShot(500, self._start_proxy_detection)

        return self.app.exec()


def main():
    if is_already_running():
        print("HoverTranslator 已经在运行中")
        sys.exit(0)
    app = HoverTranslatorApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
