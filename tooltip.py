"""
翻译结果面板 —— Google Translate 风格。

特性：
  - 白色背景、圆角、柔和阴影
  - 原文 + 译文分区显示，长文本可滚动
  - 自适应宽度（最窄 720px，最宽 1100px）
  - 不会自动消失，点击外部或 ESC 关闭
  - 可拖动位置
"""

import os
import sys
import webbrowser

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QApplication, QPushButton,
    QSizePolicy, QScrollArea, QFrame, QMenu,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor


# ── 样式表 ──────────────────────────────────────────────

LIGHT_STYLE = """
QWidget#panel {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 22px;
}
QPushButton#langBadge {
    background: #e8f0fe;
    color: #1a73e8;
    border: none;
    border-radius: 14px;
    padding: 6px 20px;
    font-size: 16px;
    font-weight: 600;
}
QPushButton#langBadge:hover {
    background: #d2e3fc;
}
QLabel#sourceText {
    color: #5f6368;
    font-size: 22px;
    line-height: 1.8;
}
QLabel#translatedText {
    color: #202124;
    font-family: "HarmonyOS Sans SC";
    font-size: 23px;
    font-weight: 500;
    line-height: 1.8;
}
QLabel#statusOk {
    color: #34a853;
    font-size: 14px;
}
QLabel#statusErr {
    color: #ea4335;
    font-size: 14px;
}
QPushButton#copyBtn {
    background: #f1f3f4;
    color: #5f6368;
    border: none;
    border-radius: 10px;
    padding: 6px 18px;
    font-size: 14px;
}
QPushButton#copyBtn:hover {
    background: #e8f0fe;
    color: #1a73e8;
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
QLabel#divider {
    background: #e8eaed;
    max-height: 1px;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    width: 12px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #dadce0;
    border-radius: 6px;
    min-height: 36px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QMenu {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    padding: 4px;
    color: #202124;
}
QMenu::item {
    background: #ffffff;
    padding: 8px 32px 8px 20px;
    color: #202124;
    font-size: 14px;
}
QMenu::item:selected {
    background: #e8f0fe;
    color: #1a73e8;
}
"""


# ── 卡片内语言选择弹窗 ────────────────────────────────

_LANG_OPTIONS = [
    ("zh-CN", "🇨🇳 中文"),
    ("en",    "🇬🇧 English"),
    ("ja",    "🇯🇵 日本語"),
    ("ko",    "🇰🇷 한국어"),
    ("fr",    "🇫🇷 Français"),
    ("ru",    "🇷🇺 Русский"),
    ("es",    "🇪🇸 Español"),
]


class _LanguagePopup(QWidget):
    """卡片内语言选择弹窗，点击外部自动关闭。"""

    language_selected = pyqtSignal(str)

    def __init__(self, current_code, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Popup
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        from font_manager import get_font
        self.setFont(get_font(15))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)

        container = QWidget()
        container.setStyleSheet("""
            background: #ffffff;
            border: 1px solid #dadce0;
            border-radius: 14px;
        """)
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(2)

        for code, label in _LANG_OPTIONS:
            btn = QPushButton(label)
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {'#e8f0fe' if code == current_code else 'transparent'};
                    color: {'#1a73e8' if code == current_code else '#202124'};
                    border: none;
                    border-radius: 8px;
                    padding: 0px 16px;
                    text-align: left;
                    font-weight: {'600' if code == current_code else '400'};
                }}
                QPushButton:hover {{
                    background: #f1f3f4;
                }}
            """)
            btn.clicked.connect(lambda checked, c=code: self._select(c))
            layout.addWidget(btn)

        self.adjustSize()

    def _select(self, code):
        self.language_selected.emit(code)
        self.close()


class TranslationPanel(QWidget):
    """Google 风格翻译结果面板。"""

    closed = pyqtSignal()
    language_selected = pyqtSignal(str)  # 目标语言 code

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._result = ""
        self._drag_pos = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(LIGHT_STYLE)
        self.setMinimumWidth(720)
        self.setMaximumWidth(1100)

        # 任务栏图标
        if getattr(sys, 'frozen', False):
            res_dir = sys._MEIPASS
        else:
            res_dir = os.path.dirname(os.path.abspath(__file__))
        icon_ico = os.path.join(res_dir, "resources", "icon.ico")
        if os.path.exists(icon_ico):
            self.setWindowIcon(QIcon(icon_ico))

        # 字体
        from font_manager import get_font
        self.setFont(get_font(12))

        # 外层容器（负责阴影）
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        self._panel = QWidget()
        self._panel.setObjectName("panel")
        self._panel.setMinimumHeight(850)
        shadow = QGraphicsDropShadowEffect(self._panel)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 45))
        shadow.setOffset(0, 5)
        self._panel.setGraphicsEffect(shadow)
        outer.addWidget(self._panel)

        # 主布局
        main = QVBoxLayout(self._panel)
        main.setContentsMargins(44, 40, 44, 40)
        main.setSpacing(28)

        # ── 顶栏：语言标签 + 关闭按钮
        top = QHBoxLayout()
        top.setSpacing(8)

        self._lang_label = QPushButton("EN → ZH")
        self._lang_label.setObjectName("langBadge")
        self._lang_label.setFixedHeight(32)
        self._lang_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lang_label.clicked.connect(self._show_lang_popup)
        top.addWidget(self._lang_label)

        self._status_label = QLabel("●")
        self._status_label.setObjectName("statusOk")
        top.addWidget(self._status_label)

        top.addStretch()

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("closeBtn")
        self._close_btn.setFixedSize(40, 40)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.close_panel)
        top.addWidget(self._close_btn)

        main.addLayout(top)

        # ── 原文区域（可滚动）
        self._source_scroll = QScrollArea()
        self._source_scroll.setWidgetResizable(True)
        self._source_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._source_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        source_content = QWidget()
        source_content.setStyleSheet("background: transparent;")
        source_layout = QVBoxLayout(source_content)
        source_layout.setContentsMargins(0, 0, 4, 0)

        self._source_label = QLabel("")
        self._source_label.setObjectName("sourceText")
        self._source_label.setWordWrap(True)
        self._source_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._source_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        source_layout.addWidget(self._source_label)
        source_layout.addStretch()

        self._source_scroll.setWidget(source_content)
        self._source_scroll.setMinimumHeight(150)
        self._source_scroll.setMaximumHeight(380)
        main.addWidget(self._source_scroll)

        # ── 分割线
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        main.addWidget(divider)

        # ── 译文区域（可滚动）
        self._result_scroll = QScrollArea()
        self._result_scroll.setWidgetResizable(True)
        self._result_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._result_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 4, 0)

        self._result_label = QLabel("")
        self._result_label.setObjectName("translatedText")
        from font_manager import get_translated_font
        self._result_label.setFont(get_translated_font(14))
        self._result_label.setWordWrap(True)
        self._result_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._result_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        scroll_layout.addWidget(self._result_label)
        scroll_layout.addStretch()

        self._result_scroll.setWidget(scroll_content)
        self._result_scroll.setMinimumHeight(350)
        self._result_scroll.setMaximumHeight(1000)
        main.addWidget(self._result_scroll, stretch=1)

        # ── 同步滚动
        self._syncing = False
        self._source_scroll.verticalScrollBar().valueChanged.connect(
            self._sync_from_source
        )
        self._result_scroll.verticalScrollBar().valueChanged.connect(
            self._sync_from_result
        )

        # ── 自定义右键菜单（在 label 上装事件过滤器）
        self._source_label.installEventFilter(self)
        self._result_label.installEventFilter(self)

        # ── 加载状态
        self._loading_label = QLabel("翻译中...")
        self._loading_label.setObjectName("statusOk")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.hide()
        main.addWidget(self._loading_label)

        # ── 底栏
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._copy_btn = QPushButton("📋 复制译文")
        self._copy_btn.setObjectName("copyBtn")
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.clicked.connect(self._copy_result)
        bottom.addWidget(self._copy_btn)

        bottom.addStretch()

        self._hint_label = QLabel("ESC 关闭")
        self._hint_label.setObjectName("statusOk")
        self._hint_label.setStyleSheet("color: #9aa0a6; font-size: 15px;")
        bottom.addWidget(self._hint_label)

        main.addLayout(bottom)

        self.hide()

    # ── 公开方法 ──────────────────────────────────────────

    def show_loading(self, source_text=""):
        """显示加载状态。"""
        self._source_label.setText(source_text[:500])
        self._source_label.show()
        self._result_label.hide()
        self._loading_label.show()
        self._copy_btn.hide()
        self._lang_label.setText("翻译中...")
        self._status_label.setObjectName("statusOk")
        self._status_label.setStyleSheet("color: #fbbc04; font-size: 13px;")
        self._status_label.setText("●")
        self._show_at_cursor()

    def show_result(self, original, translated, lang="", resolved_src="", resolved_target=""):
        """显示翻译结果。"""
        self._result = translated
        self._loading_label.hide()
        self._source_label.setText(original[:500])
        self._source_label.show()
        self._result_label.setText(translated)
        self._result_label.show()
        self._copy_btn.show()

        if lang == "error":
            self._lang_label.setText("翻译失败")
            self._status_label.setObjectName("statusErr")
            self._status_label.setStyleSheet("color: #ea4335; font-size: 13px;")
        else:
            from languages import get_display_name
            src_code = resolved_src or lang
            tgt_code = resolved_target or self.config.get("target_lang", "zh-CN")
            src = "自动" if src_code == "auto" else get_display_name(src_code)
            dst = get_display_name(tgt_code)
            self._lang_label.setText(f"{src} → {dst}")
            self._status_label.setObjectName("statusOk")
            self._status_label.setStyleSheet("color: #34a853; font-size: 13px;")
        self._status_label.setText("●")
        self._show_at_cursor()

    def close_panel(self):
        self.hide()
        self.closed.emit()

    def _show_lang_popup(self):
        current = self.config.get("target_lang", "zh-CN")
        popup = _LanguagePopup(current, self)
        popup.language_selected.connect(self._on_lang_picked)
        # 定位到语言按钮下方
        btn_pos = self._lang_label.mapToGlobal(self._lang_label.rect().bottomLeft())
        popup.adjustSize()
        pw, ph = popup.width(), popup.height()
        screen = QApplication.screenAt(btn_pos) or QApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = btn_pos.x()
        y = btn_pos.y() + 4
        if x + pw > geo.right() - 10:
            x = geo.right() - pw - 10
        if y + ph > geo.bottom() - 10:
            y = btn_pos.y() - ph - self._lang_label.height() - 4
        popup.move(x, y)
        popup.show()

    def _on_lang_picked(self, code):
        self.config["target_lang"] = code
        self.language_selected.emit(code)

    # ── 内部方法 ──────────────────────────────────────────

    def _show_at_cursor(self):
        """定位到鼠标附近并显示。"""
        hint = self.sizeHint()
        w = max(hint.width(), self.minimumWidth())
        h = max(hint.height(), self._panel.minimumHeight() + 40)

        mouse = QCursor.pos()
        screen = QApplication.screenAt(mouse) or QApplication.primaryScreen()
        geo = screen.availableGeometry()

        x = mouse.x() + 20
        y = mouse.y() + 20

        if x + w > geo.right() - 10:
            x = mouse.x() - w - 20
        if y + h > geo.bottom() - 10:
            y = mouse.y() - h - 20
        if y < geo.top() + 10:
            y = geo.top() + 10
        if x < geo.left() + 10:
            x = geo.left() + 10

        self.move(x, y)
        self.show()
        self.raise_()

    def _copy_result(self):
        if self._result:
            QApplication.clipboard().setText(self._result)
            self._copy_btn.setText("✓ 已复制")
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("📋 复制译文"))

    def _sync_from_source(self, value):
        if self._syncing:
            return
        self._syncing = True
        self._result_scroll.verticalScrollBar().setValue(value)
        self._syncing = False

    def _sync_from_result(self, value):
        if self._syncing:
            return
        self._syncing = True
        self._source_scroll.verticalScrollBar().setValue(value)
        self._syncing = False

    # ── 事件 ──────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_panel()
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.ContextMenu and obj in (self._source_label, self._result_label):
            self._show_custom_menu(event)
            return True
        return super().eventFilter(obj, event)

    def _show_custom_menu(self, event):
        selected = self._get_selected_text()
        menu = QMenu(self)

        copy_action = menu.addAction("📋 复制")
        copy_action.setEnabled(bool(selected))
        copy_action.triggered.connect(lambda: self._copy_text(selected))

        search_action = menu.addAction("🔍 DeepSeek 搜索")
        search_action.setEnabled(bool(selected))
        search_action.triggered.connect(lambda: self._search_deepseek(selected))

        menu.exec(event.globalPos())

    def _get_selected_text(self):
        """从原文或译文 label 获取选中的文字。"""
        for label in (self._result_label, self._source_label):
            try:
                text = label.selectedText()
                if text:
                    return text
            except Exception:
                pass
        return ""

    def _copy_text(self, text):
        if text:
            QApplication.clipboard().setText(text)

    def _search_deepseek(self, text):
        if text and text.strip():
            # 复制到剪贴板，打开 DeepSeek 后用户 Ctrl+V 即可粘贴
            QApplication.clipboard().setText(text.strip())
            webbrowser.open("https://chat.deepseek.com/")

    def _is_interactive_child(self, pos):
        """检查点击位置是否在可交互的子控件上（按钮、滚动区）。"""
        child = self.childAt(pos)
        while child and child != self:
            if isinstance(child, (QPushButton, QScrollArea)):
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
