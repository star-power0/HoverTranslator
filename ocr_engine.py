"""
OCR 引擎：截取选区 → 识别文字。

使用 RapidOCR (ONNX Runtime)：
  - 完全离线，无需网络
  - 支持中英文混合识别
  - pip install rapidocr-onnxruntime 即可，无外部依赖
"""

import os
import numpy as np
from PIL import ImageGrab, Image
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication
from rapidocr_onnxruntime import RapidOCR

import sys as _sys

if getattr(_sys, 'frozen', False):
    _DEBUG_DIR = os.path.join(os.path.dirname(_sys.executable), "debug_ocr")
else:
    _DEBUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_ocr")


# 鼠标周围截取区域（像素）
CAPTURE_PAD_X = 220   # 左右各扩展
CAPTURE_PAD_Y = 80    # 上下各扩展
CAPTURE_W = CAPTURE_PAD_X * 2
CAPTURE_H = CAPTURE_PAD_Y * 2


# 全局引擎实例（避免每次重建）
_ocr_engine = None

def _get_engine():
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    return _ocr_engine


def _join_ocr_lines(result):
    """根据行间距智能分段：段内用空格，段间用换行。"""
    entries = []
    for line in result:
        bbox = line[0]
        text = line[1].strip()
        if not text:
            continue
        y_top = min(p[1] for p in bbox)
        y_bot = max(p[1] for p in bbox)
        entries.append((y_top, y_bot, text))

    if not entries:
        return ""

    entries.sort(key=lambda e: e[0])

    # 计算中位行高，作为段落间距阈值
    heights = [e[1] - e[0] for e in entries]
    median_h = sorted(heights)[len(heights) // 2] if heights else 20
    gap_threshold = median_h * 0.8

    paragraphs = []
    current = [entries[0][2]]
    for i in range(1, len(entries)):
        gap = entries[i][0] - entries[i - 1][1]
        if gap > gap_threshold:
            paragraphs.append(" ".join(current))
            current = [entries[i][2]]
        else:
            current.append(entries[i][2])
    paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs)


class OcrWorker(QThread):
    """后台线程：截图 + OCR 识别。"""
    finished = pyqtSignal(str)   # 识别出的文字

    def __init__(self, rect):
        super().__init__()
        self.rect = rect   # (x1, y1, x2, y2)

    def run(self):
        try:
            # Qt6 报告逻辑像素，ImageGrab 需要物理像素 → 乘以 DPI 缩放比
            dpr = 1.0
            try:
                screen = QApplication.primaryScreen()
                if screen:
                    dpr = screen.devicePixelRatio()
            except Exception:
                pass

            physical = tuple(int(c * dpr) for c in self.rect)
            screenshot = ImageGrab.grab(bbox=physical)

            # 小区域 2x 放大提高识别率，不做二值化（RapidOCR 自带更优预处理）
            w, h = screenshot.size
            if w < 600 or h < 150:
                screenshot = screenshot.resize(
                    (w * 2, h * 2), Image.Resampling.LANCZOS
                )

            # 调试：保存截图以便排查
            try:
                os.makedirs(_DEBUG_DIR, exist_ok=True)
                screenshot.save(os.path.join(_DEBUG_DIR, "last_capture.png"))
            except Exception:
                pass

            img_array = np.array(screenshot)
            engine = _get_engine()
            result, _ = engine(img_array)
            if result:
                combined = _join_ocr_lines(result)
                self.finished.emit(combined)
            else:
                self.finished.emit("")
        except Exception:
            self.finished.emit("")


class HoverOcr(QObject):
    """鼠标悬停 OCR 管理器：监听鼠标静止 → 截图 → OCR。"""

    text_detected = pyqtSignal(str)   # 识别到文字后发出

    def __init__(self):
        super().__init__()
        self._worker = None
        self._running = False

    def capture_at_cursor(self):
        """在当前鼠标位置截图并 OCR。"""
        if self._running:
            return

        cursor = QCursor.pos()
        screen = QApplication.screenAt(cursor) or QApplication.primaryScreen()
        geo = screen.availableGeometry()

        x1 = max(cursor.x() - CAPTURE_PAD_X, geo.left())
        y1 = max(cursor.y() - CAPTURE_PAD_Y, geo.top())
        x2 = min(cursor.x() + CAPTURE_PAD_X, geo.right())
        y2 = min(cursor.y() + CAPTURE_PAD_Y, geo.bottom())

        self._running = True
        self._worker = OcrWorker((x1, y1, x2, y2))
        self._worker.finished.connect(self._on_ocr_done)
        self._worker.start()

    def _on_ocr_done(self, text):
        self._running = False
        if text:
            self.text_detected.emit(text)
