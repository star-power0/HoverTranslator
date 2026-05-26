"""
字体加载器：加载项目自带的两套字体。
  - Noto Sans SC：原文用，清秀克制
  - HarmonyOS Sans SC：译文用，圆润现代
"""

import os
import sys
from PyQt6.QtGui import QFont, QFontDatabase


if getattr(sys, 'frozen', False):
    _PROJECT_DIR = sys._MEIPASS
else:
    _PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_FONT_DIR = os.path.join(_PROJECT_DIR, "resources", "fonts")

# 字体族名 → 文件列表
_FONT_MAP = {
    "Noto Sans SC": [
        os.path.join(_FONT_DIR, "NotoSansSC-Regular.ttf"),
        os.path.join(_FONT_DIR, "NotoSansSC-Bold.ttf"),
    ],
    "HarmonyOS Sans SC": [
        os.path.join(_FONT_DIR, "HarmonyOS_Sans_SC_Regular.ttf"),
        os.path.join(_FONT_DIR, "HarmonyOS_Sans_SC_Bold.ttf"),
    ],
}

_families = {}   # {"Noto Sans SC": "Noto Sans SC", ...}
_loaded = False


def _load():
    global _loaded
    if _loaded:
        return
    _loaded = True

    for name, files in _FONT_MAP.items():
        last_fid = -1
        for p in files:
            if os.path.isfile(p):
                fid = QFontDatabase.addApplicationFont(p)
                if fid >= 0:
                    last_fid = fid
        if last_fid >= 0:
            fams = QFontDatabase.applicationFontFamilies(last_fid)
            _families[name] = fams[0] if fams else name
        else:
            _families[name] = "DengXian"


def get_font(size=11, bold=False):
    """获取原文字体（Noto Sans SC）。"""
    _load()
    family = _families.get("Noto Sans SC", "DengXian")
    f = QFont(family, size)
    if bold:
        f.setWeight(QFont.Weight.DemiBold)
    f.setStyleHint(QFont.StyleHint.SansSerif)
    return f


def get_translated_font(size=11, bold=False):
    """获取译文字体（HarmonyOS Sans SC）。"""
    _load()
    family = _families.get("HarmonyOS Sans SC", "DengXian")
    f = QFont(family, size)
    if bold:
        f.setWeight(QFont.Weight.DemiBold)
    f.setStyleHint(QFont.StyleHint.SansSerif)
    return f
