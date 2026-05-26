"""
设置窗口 — 翻译提供商选择 + API Key 管理 + 快捷键提示。

Google 风格白色圆角卡片，与 TranslationPanel 视觉一致。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QGraphicsDropShadowEffect,
    QApplication, QCheckBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QCursor

from translator import PROVIDERS
from languages import LANGUAGES
from font_manager import get_font


# ── 样式表 ──────────────────────────────────────────────

_STYLE = """
QWidget#panel {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 22px;
}
QLabel#title {
    color: #202124;
    font-size: 22px;
    font-weight: 600;
}
QLabel#sectionTitle {
    color: #202124;
    font-size: 16px;
    font-weight: 600;
}
QLabel#desc {
    color: #5f6368;
    font-size: 14px;
}
QPushButton#closeBtn {
    background: transparent;
    color: #9aa0a6;
    border: none;
    font-size: 28px;
    font-weight: bold;
}
QPushButton#closeBtn:hover {
    color: #ea4335;
}
QPushButton#testBtn {
    background: #f1f3f4;
    color: #5f6368;
    border: none;
    border-radius: 10px;
    padding: 8px 20px;
    font-size: 14px;
}
QPushButton#testBtn:hover {
    background: #e8f0fe;
    color: #1a73e8;
}
QLabel#divider {
    background: #e8eaed;
    max-height: 1px;
}
QLineEdit {
    background: #f8f9fa;
    border: 1px solid #dadce0;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    color: #202124;
}
QLineEdit:focus {
    border-color: #1a73e8;
}
QComboBox {
    background: #f8f9fa;
    border: 1px solid #dadce0;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    color: #202124;
    min-width: 200px;
}
QComboBox:focus {
    border-color: #1a73e8;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #dadce0;
    selection-background-color: #e8f0fe;
    selection-color: #1a73e8;
    font-size: 14px;
}
QCheckBox {
    color: #5f6368;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""


def _provider_card_style(selected=False):
    if selected:
        return """
        QPushButton {
            background: #e8f0fe;
            border: 2px solid #1a73e8;
            border-radius: 12px;
            padding: 12px 16px;
            color: #1a73e8;
            font-size: 14px;
            font-weight: 600;
        }
        """
    return """
    QPushButton {
        background: #ffffff;
        border: 1px solid #dadce0;
        border-radius: 12px;
        padding: 12px 16px;
        color: #202124;
        font-size: 14px;
    }
    QPushButton:hover {
        background: #f8f9fa;
        border-color: #bdc1c6;
    }
    """


def _hotkey_badge_style():
    return """
    QLabel {
        background: #e8f0fe;
        color: #1a73e8;
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 13px;
        font-weight: 600;
    }
    """


class SettingsWindow(QWidget):
    """设置窗口：翻译提供商选择、API Key、语言、快捷键。"""

    provider_changed = pyqtSignal(str)
    language_changed = pyqtSignal(str)
    credentials_changed = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._drag_pos = None
        self._provider_cards = {}
        self._key_inputs = {}
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._save_credentials)
        self._init_ui()
        self._select_provider(self.config.get("provider", "google"), emit=False)

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(_STYLE)
        self.setFont(get_font(12))
        self.setMinimumWidth(560)
        self.setMaximumWidth(640)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        panel = QWidget()
        panel.setObjectName("panel")
        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 45))
        shadow.setOffset(0, 5)
        panel.setGraphicsEffect(shadow)
        outer.addWidget(panel)

        main = QVBoxLayout(panel)
        main.setContentsMargins(40, 36, 40, 36)
        main.setSpacing(20)

        # ── 顶栏
        top = QHBoxLayout()
        title = QLabel("⚙️ 设置")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(40, 40)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._close)
        top.addWidget(close_btn)
        main.addLayout(top)

        # ── 翻译提供商
        sec1 = QLabel("翻译提供商")
        sec1.setObjectName("sectionTitle")
        main.addWidget(sec1)

        provider_grid = QVBoxLayout()
        provider_grid.setSpacing(10)
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        for i, (key, info) in enumerate(PROVIDERS.items()):
            label = f"{info['emoji']}  {info['name']}"
            if info["requires_key"]:
                label += " 🔑"
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, k=key: self._select_provider(k))
            self._provider_cards[key] = btn
            if i < 3:
                row1.addWidget(btn)
            else:
                row2.addWidget(btn)

        provider_grid.addLayout(row1)
        provider_grid.addLayout(row2)
        main.addLayout(provider_grid)

        # 描述文字
        self._desc_label = QLabel("")
        self._desc_label.setObjectName("desc")
        self._desc_label.setWordWrap(True)
        main.addWidget(self._desc_label)

        # ── API Key 输入区
        self._key_container = QWidget()
        key_layout = QVBoxLayout(self._key_container)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(10)

        # DeepL
        self._deepl_frame = self._build_key_section("DeepL API Key", "deepl_api_key")
        self._deepl_free_cb = QCheckBox("使用 DeepL 免费 API（api-free.deepl.com）")
        self._deepl_free_cb.setChecked(self.config.get("deepl_use_free_api", True))
        self._deepl_free_cb.toggled.connect(self._on_deepl_free_toggled)
        key_layout.addWidget(self._deepl_frame)
        key_layout.addWidget(self._deepl_free_cb)

        # Baidu
        self._baidu_appid_frame = self._build_key_section("百度 AppID", "baidu_appid")
        self._baidu_appkey_frame = self._build_key_section("百度 AppKey", "baidu_appkey")
        key_layout.addWidget(self._baidu_appid_frame)
        key_layout.addWidget(self._baidu_appkey_frame)

        # Microsoft
        self._ms_key_frame = self._build_key_section("Microsoft API Key", "microsoft_api_key")
        self._ms_region_frame = self._build_key_section("Region（可选）", "microsoft_region")
        key_layout.addWidget(self._ms_key_frame)
        key_layout.addWidget(self._ms_region_frame)

        main.addWidget(self._key_container)

        # ── 连接测试
        test_row = QHBoxLayout()
        test_row.setSpacing(12)
        test_btn = QPushButton("🔗 测试连接")
        test_btn.setObjectName("testBtn")
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._run_test)
        test_row.addWidget(test_btn)

        self._test_status = QLabel("● 未测试")
        self._test_status.setStyleSheet("color: #9aa0a6; font-size: 14px;")
        test_row.addWidget(self._test_status)
        test_row.addStretch()
        main.addLayout(test_row)

        # ── 分割线
        main.addWidget(self._make_divider())

        # ── 目标语言
        sec2 = QLabel("目标语言")
        sec2.setObjectName("sectionTitle")
        main.addWidget(sec2)

        self._lang_combo = QComboBox()
        current_target = self.config.get("target_lang", "zh-CN")
        for lang in LANGUAGES:
            display = f'{lang["flag"]}  {lang["name"]}'
            self._lang_combo.addItem(display, lang["code"])
            if lang["code"] == current_target:
                self._lang_combo.setCurrentIndex(self._lang_combo.count() - 1)
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        main.addWidget(self._lang_combo)

        # ── 分割线
        main.addWidget(self._make_divider())

        # ── 快捷键提示
        sec3 = QLabel("快捷键")
        sec3.setObjectName("sectionTitle")
        main.addWidget(sec3)

        hotkeys_container = QWidget()
        hotkeys_container.setStyleSheet("background: #f8f9fa; border-radius: 12px;")
        hk_layout = QVBoxLayout(hotkeys_container)
        hk_layout.setContentsMargins(20, 16, 20, 16)
        hk_layout.setSpacing(10)

        for key_text, desc_text in [
            ("Ctrl+T", "截图选区翻译"),
            ("Ctrl+Q", "快捷翻译选中文字"),
            ("ESC", "关闭翻译面板"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(12)
            badge = QLabel(key_text)
            badge.setStyleSheet(_hotkey_badge_style())
            badge.setFixedHeight(28)
            row.addWidget(badge)
            desc = QLabel(desc_text)
            desc.setStyleSheet("color: #5f6368; font-size: 14px;")
            row.addWidget(desc)
            row.addStretch()
            hk_layout.addLayout(row)

        main.addWidget(hotkeys_container)

        # ── 分割线
        main.addWidget(self._make_divider())

        # ── 关于
        about = QLabel(
            "HoverTranslator v0.12.2\n"
            "翻译引擎: deep_translator  ·  OCR: RapidOCR (ONNX Runtime)\n"
            "字体: Noto Sans SC + HarmonyOS Sans SC"
        )
        about.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        about.setWordWrap(True)
        main.addWidget(about)

        main.addStretch()
        self.hide()

    # ── 提供商选择 ────────────────────────────────────────

    def _select_provider(self, provider_key, emit=True):
        # 更新卡片样式
        for key, btn in self._provider_cards.items():
            btn.setStyleSheet(_provider_card_style(selected=(key == provider_key)))

        info = PROVIDERS.get(provider_key, {})
        self._desc_label.setText(info.get("description", ""))

        # 显示/隐藏 API Key 输入
        self._hide_all_key_fields()
        if provider_key == "deepl":
            self._deepl_frame.show()
            self._deepl_free_cb.show()
        elif provider_key == "baidu":
            self._baidu_appid_frame.show()
            self._baidu_appkey_frame.show()
        elif provider_key == "microsoft":
            self._ms_key_frame.show()
            self._ms_region_frame.show()

        self._key_container.setVisible(info.get("requires_key", False))

        # 重置测试状态
        self._test_status.setText("● 未测试")
        self._test_status.setStyleSheet("color: #9aa0a6; font-size: 14px;")

        if emit:
            self.config["provider"] = provider_key
            self.provider_changed.emit(provider_key)

    def _hide_all_key_fields(self):
        for frame in [
            self._deepl_frame, self._deepl_free_cb,
            self._baidu_appid_frame, self._baidu_appkey_frame,
            self._ms_key_frame, self._ms_region_frame,
        ]:
            frame.hide()

    # ── API Key 输入 ──────────────────────────────────────

    def _build_key_section(self, placeholder, config_key):
        frame = QWidget()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setText(self.config.get(config_key, ""))
        inp.textChanged.connect(self._on_key_changed)

        toggle = QPushButton("👁")
        toggle.setFixedSize(36, 36)
        toggle.setStyleSheet("""
            QPushButton { background: transparent; border: none; font-size: 16px; }
            QPushButton:hover { background: #f1f3f4; border-radius: 6px; }
        """)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.clicked.connect(lambda checked, e=inp: self._toggle_echo(e))

        layout.addWidget(inp)
        layout.addWidget(toggle)

        self._key_inputs[config_key] = inp
        return frame

    def _toggle_echo(self, inp):
        if inp.echoMode() == QLineEdit.EchoMode.Password:
            inp.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            inp.setEchoMode(QLineEdit.EchoMode.Password)

    def _on_key_changed(self):
        self._save_timer.start()

    def _save_credentials(self):
        for config_key, inp in self._key_inputs.items():
            self.config[config_key] = inp.text().strip()
        self.credentials_changed.emit()

    def _on_deepl_free_toggled(self, checked):
        self.config["deepl_use_free_api"] = checked
        self.credentials_changed.emit()

    # ── 连接测试 ──────────────────────────────────────────

    def _run_test(self):
        self._test_status.setText("● 测试中...")
        self._test_status.setStyleSheet("color: #fbbc04; font-size: 14px;")
        self._save_credentials()  # 先保存当前输入

        from translator import Translator
        self._test_translator = Translator(self.config)
        self._test_translator.test_connection(self._on_test_done)

    def _on_test_done(self, success, message):
        if success:
            self._test_status.setText(f"● {message}")
            self._test_status.setStyleSheet("color: #34a853; font-size: 14px;")
        else:
            self._test_status.setText(f"● {message}")
            self._test_status.setStyleSheet("color: #ea4335; font-size: 14px;")

    # ── 语言切换 ──────────────────────────────────────────

    def _on_lang_changed(self, index):
        code = self._lang_combo.itemData(index)
        if code:
            self.config["target_lang"] = code
            self.language_changed.emit(code)

    # ── 工具方法 ──────────────────────────────────────────

    def _make_divider(self):
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        return divider

    def _close(self):
        self.hide()
        self.closed.emit()

    def showEvent(self, event):
        super().showEvent(event)
        # 居中显示
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    # ── 拖动 ──────────────────────────────────────────────

    def _is_interactive_child(self, pos):
        child = self.childAt(pos)
        while child and child != self:
            if isinstance(child, (QPushButton, QLineEdit, QComboBox, QCheckBox)):
                return True
            child = child.parentWidget()
        return False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_interactive_child(event.pos()):
                self._drag_pos = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._close()
        super().keyPressEvent(event)
