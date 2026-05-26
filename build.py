"""
HoverTranslator 打包脚本。
运行: python build.py
输出: dist/HoverTranslator/HoverTranslator.exe
"""

import PyInstaller.__main__
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(_HERE, "main.py"),
    "--name=HoverTranslator",
    "--noconfirm",
    "--windowed",                     # 无控制台窗口
    f"--icon={_HERE}/resources/icon.ico",
    # 资源文件打包进去
    f"--add-data={_HERE}/resources;resources",
    # 隐藏导入
    "--hidden-import=PyQt6.sip",
    "--hidden-import=deep_translator",
    "--hidden-import=deep_translator.constants",
    "--hidden-import=deep_translator.google",
    "--hidden-import=deep_translator.deepl",
    "--hidden-import=deep_translator.baidu",
    "--hidden-import=deep_translator.microsoft",
    "--hidden-import=deep_translator.mymemory",
    "--hidden-import=rapidocr_onnxruntime",
    "--hidden-import=pynput.keyboard._win32",
    "--hidden-import=pynput.mouse._win32",
    # rapidocr 的 config.yaml + models/ 需要作为数据文件收集
    "--collect-data=rapidocr_onnxruntime",
    # 输出到 dist/
    f"--distpath={_HERE}/dist",
    f"--workpath={_HERE}/build",
    f"--specpath={_HERE}",
])
