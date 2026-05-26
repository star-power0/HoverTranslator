"""
屏幕截图选区工具。

触发后覆盖全屏半透明蒙层，用户拖拽画框选择 OCR 区域。
选区完成后发出 region_selected 信号，包含选区坐标。
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor, QGuiApplication


class ScreenSelector(QWidget):
    """全屏半透明蒙层，支持拖拽选区。"""

    region_selected = pyqtSignal(QRect)   # 选区完成（屏幕坐标）
    cancelled = pyqtSignal()              # 用户取消

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._start = None
        self._end = None
        self._selecting = False

    def start_selection(self):
        """显示蒙层，开始选区。"""
        screen = QGuiApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 半透明蒙层
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))

        if self._start and self._end:
            rect = QRect(self._start, self._end).normalized()

            # 选区内透明（挖洞效果）
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # 选区边框
            pen = QPen(QColor(26, 115, 232), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

            # 选区尺寸提示
            size_text = f"{rect.width()} × {rect.height()}"
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(self.font())
            tx = rect.left()
            ty = rect.top() - 8 if rect.top() > 20 else rect.bottom() + 18
            painter.drawText(tx, ty, size_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._end = event.pos()
            self._selecting = True

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            self._end = event.pos()
            rect = QRect(self._start, self._end).normalized()

            self.hide()

            if rect.width() > 10 and rect.height() > 10:
                # 转换为屏幕坐标（逻辑像素），OcrWorker 内部会乘以 DPI 缩放比
                screen_rect = QRect(
                    self.x() + rect.x(),
                    self.y() + rect.y(),
                    rect.width(),
                    rect.height(),
                )
                self.region_selected.emit(screen_rect)
            else:
                self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
