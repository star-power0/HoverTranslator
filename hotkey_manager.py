"""
全局快捷键管理器。

使用 pynput 的 keyboard.Listener 监听键盘事件。
支持多个快捷键注册到同一个监听器上。
"""

import time
from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard


class HotkeyManager(QObject):
    """全局快捷键管理器，支持多个快捷键绑定。"""

    # 每个快捷键对应一个信号，由外部代码 connect
    triggered = pyqtSignal(str)   # 发出快捷键名称，如 "ctrl+t"

    def __init__(self):
        super().__init__()
        self._hotkeys = {}        # {frozenset: name}
        self._pressed = set()
        self._last_trigger = {}
        self._listener = None

    def register(self, hotkey_str):
        """注册一个快捷键，如 "ctrl+t"。"""
        keys = self._parse(hotkey_str)
        self._hotkeys[keys] = hotkey_str

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    # ── 内部 ──────────────────────────────────────────────

    @staticmethod
    def _parse(hotkey_str):
        parts = hotkey_str.lower().replace(" ", "").split("+")
        keys = set()
        for p in parts:
            if p in ("ctrl", "control"):
                keys.add("ctrl")
            elif p == "shift":
                keys.add("shift")
            elif p == "alt":
                keys.add("alt")
            else:
                keys.add(p)
        return frozenset(keys)

    @staticmethod
    def _key_to_name(key):
        """将 pynput key 对象转为小写名称。
        关键：Ctrl+T 时 pynput 报告 key.char = '\\x14'，需要还原为 't'。
        """
        # 修饰键
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return "ctrl"
        if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
            return "shift"
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            return "alt"

        # 普通键
        if hasattr(key, "char") and key.char:
            ch = key.char
            # 控制字符还原：\x01→a, \x11→q, \x14→t, ...
            if len(ch) == 1 and ord(ch) < 27:
                return chr(ord(ch) + 96)   # \x01→a, \x02→b, ...
            return ch.lower()
        return None

    def _on_press(self, key):
        name = self._key_to_name(key)
        if not name:
            return

        self._pressed.add(name)

        for combo, hotkey_name in self._hotkeys.items():
            if combo.issubset(self._pressed):
                now = time.time()
                last = self._last_trigger.get(hotkey_name, 0)
                if now - last > 0.5:
                    self._last_trigger[hotkey_name] = now
                    self.triggered.emit(hotkey_name)

    def _on_release(self, key):
        name = self._key_to_name(key)
        if name:
            self._pressed.discard(name)
