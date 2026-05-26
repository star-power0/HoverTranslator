# HoverTranslator

Windows 桌面翻译工具。Ctrl+T 截图选区，框住文字自动识别翻译。图片、按钮、菜单、网页里不能复制的文字都能翻。

**[📥 下载最新版 Release](https://github.com/star-power0/HoverTranslator/releases)** — 下载 zip 解压即用，无需安装 Python。

## 功能

### 截图选区翻译（Ctrl+T）
按 Ctrl+T，屏幕变暗出现十字光标，拖拽画框选住要翻译的文字区域。松开后自动 OCR 识别文字 → 调用 Google Translate 翻译 → 弹出翻译卡片。

适用场景：游戏内文字、图片上的文字、PDF 不能复制的段落、菜单/按钮文字。

### 快捷翻译（Ctrl+Q）
选中任意文字，按 Ctrl+Q，自动复制并翻译。适用于可选中的文本场景。

### 翻译卡片
- Google 风格白色卡片，圆角 + 阴影
- 原文 + 译文分区显示，长文本可滚动
- 原文和译文同步滚动
- 可拖动卡片位置
- 一键复制译文
- 点击语言标签可直接切换目标语言，选后自动重新翻译
- 点击卡片外或按 ESC 关闭

### 右键搜索
在翻译卡片的文字区域右键选中文字，可选择：
- 复制选中文字
- 跳转 DeepSeek 搜索（自动带入选中文字作为提问）

### OCR 智能分段
截图区域包含多段文字时，OCR 自动根据行间距检测段落边界，保留原文结构。翻译引擎按段落并行翻译，保持段落分隔。

### 自动代理检测
启动时自动检测网络环境，支持：
- 直连（Warp / 系统 VPN）
- Clash（端口 7890）
- V2Ray（端口 10809）
- Shadowsocks（端口 1080）
- Trojan、Surge 等常见代理
- Windows 系统代理设置
- 手动配置代理（config.json）

### 系统托盘
程序运行后在系统托盘显示图标，右键可：
- 触发截图翻译
- 翻译剪贴板内容
- 切换目标语言（19 种）
- 切换主题（浅色/深色）
- 打开设置窗口
- 退出程序

## 翻译引擎

支持 5 个翻译提供商（通过 deep_translator 库），可在设置窗口中一键切换：

| 提供商 | 免费 | 说明 |
|--------|------|------|
| Google 翻译 | ✅ | 免费，无需 API Key，支持 130+ 语言 |
| MyMemory | ✅ | 免费，无需 API Key，单次最多 500 字符 |
| DeepL | ❌ | 高质量翻译，需 API Key（有免费额度） |
| 百度翻译 | ❌ | 中文翻译优秀，需 AppID + AppKey |
| Microsoft | ❌ | 需 Azure 认知服务 API Key |

支持自动检测源语言，智能切换翻译方向。翻译结果带缓存，重复内容秒出。

## OCR 引擎

使用 RapidOCR（ONNX Runtime），完全离线运行，无需联网。支持中英文混合识别，对截图中的印刷体文字识别效果好。

## 设置窗口

右键托盘图标 → "⚙️ 设置" 打开可视化设置界面：

- **翻译提供商**：点击卡片切换，蓝色高亮当前选中
- **API Key**：密码模式输入，带 👁 显示/隐藏切换，自动保存
- **连接测试**：点击"🔗 测试连接"验证 API Key 是否有效
- **目标语言**：下拉选择，19 种语言带国旗标识
- **快捷键提示**：Ctrl+T / Ctrl+Q / ESC 用法说明

也可以直接编辑程序目录下的 `config.json`。

## 字体

- **原文**：Noto Sans SC（思源黑体，Google + Adobe 联合开发，开源）
- **译文**：HarmonyOS Sans SC（鸿蒙黑体，华为开发，开源免费商用）

两套字体打包在程序内，无需系统额外安装。

## 支持语言

| 分组 | 语言 |
|------|------|
| 东亚 | 简体中文、繁體中文、英语、日语、韩语 |
| 欧洲 | 法语、德语、西班牙语、葡萄牙语、意大利语、俄语、荷兰语、波兰语、瑞典语 |
| 其他 | 阿拉伯语、印地语、泰语、越南语、土耳其语 |

翻译卡片内点击语言标签可快速切换，托盘菜单也可切换。

## 安装运行

### 方式一：直接运行 exe（推荐）

下载 `dist/HoverTranslator/` 文件夹，双击 `HoverTranslator.exe` 即可。无需安装 Python。

> 首次运行会自动检测代理，约 1-5 秒后托盘提示"网络就绪"。

### 方式二：源码运行

需要 Python 3.10+ 环境：

```bash
cd HoverTranslator
pip install -r requirements.txt
python main.py
```

### 依赖

| 库 | 用途 |
|---|---|
| PyQt6 | 界面框架 |
| deep-translator | 翻译接口（Google / DeepL / 百度 / Microsoft / MyMemory） |
| rapidocr-onnxruntime | 离线 OCR 引擎 |
| pynput | 全局快捷键监听 |
| Pillow | 截图处理 |

## 配置

程序目录下的 `config.json`：

```json
{
  "hotkey": "ctrl+q",
  "source_lang": "auto",
  "target_lang": "zh-CN",
  "theme": "dark",
  "auto_hide_seconds": 5,
  "font_size": 14,
  "max_text_length": 500,
  "proxy": "",
  "provider": "google",
  "deepl_api_key": "",
  "deepl_use_free_api": true,
  "baidu_appid": "",
  "baidu_appkey": "",
  "microsoft_api_key": "",
  "microsoft_region": ""
}
```

- `target_lang`：默认翻译目标语言
- `provider`：翻译提供商（google / mymemory / deepl / baidu / microsoft）
- `proxy`：留空自动检测，或填写如 `http://127.0.0.1:7890`
- `max_text_length`：超过此长度的文本会截断
- DeepL / 百度 / Microsoft 的 API Key 可在设置窗口中填写，也可手动编辑

## 打包 exe

```bash
python build.py
```

输出到 `dist/HoverTranslator/HoverTranslator.exe`。需要 PyInstaller：

```bash
pip install pyinstaller
```

## 项目结构

```
HoverTranslator/
├── main.py              # 程序入口，信号连接与流程控制
├── selector.py          # 全屏半透明蒙层，拖拽选区
├── ocr_engine.py        # RapidOCR 离线识别 + 智能分段
├── translator.py        # 多提供商翻译引擎 + 缓存
├── tooltip.py           # 翻译卡片 UI + 语言选择弹窗
├── settings_window.py   # 设置窗口（提供商选择、API Key、语言）
├── hotkey_manager.py    # pynput 全局快捷键
├── tray_icon.py         # 系统托盘图标与菜单
├── languages.py         # 语言注册表（19 种语言定义）
├── proxy_detector.py    # 代理自动检测（端口扫描 + 注册表）
├── font_manager.py      # 双字体加载器
├── config.py            # 配置文件读写
├── build.py             # PyInstaller 打包脚本
├── config.json          # 用户配置文件
├── requirements.txt     # Python 依赖
├── resources/
│   ├── icon.ico         # 程序图标
│   └── fonts/           # Noto Sans SC + HarmonyOS Sans SC
├── CHANGELOG.md         # 版本更新记录
└── README.md
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+T | 截图选区翻译 |
| Ctrl+Q | 快捷翻译选中文字 |
| ESC | 关闭翻译面板 |

## 故障排除

| 问题 | 解决方法 |
|------|---------|
| Ctrl+T 无反应 | 确认程序在后台运行（检查系统托盘图标） |
| OCR 选区要框住文字区域，不要选太多空白 |
| 翻译失败 | 确认网络可用或代理已开启；也可在 config.json 手动填写 proxy |
| 面板挡住了内容 | 拖动面板到其他位置 |
| 多次运行无响应 | 检查任务管理器，结束已有的 HoverTranslator 进程 |

## 许可证

MIT License

字体许可：
- Noto Sans SC — [OFL 1.1](https://scripts.sil.org/OFL)
- HarmonyOS Sans SC — [华为开源许可](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides-V5/font-resource-0000001492275641-V5)
