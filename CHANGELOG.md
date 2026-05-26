# CHANGELOG

## v0.12.2 — 2026-05-26

### 修复：翻译卡片在任务栏显示，方便切换回来
- **问题**：移除 `WindowStaysOnTopHint` 后，翻译卡片不再置顶，但打开其他窗口后在任务栏找不到卡片，无法切回来
- **修复**：移除 `WindowType.Tool` 标志，翻译卡片现在会在底部任务栏显示图标；关闭卡片后任务栏图标自动消失，后台程序继续运行（托盘图标常驻），下次翻译时重新出现

### 修复：翻译卡片任务栏图标为空白
- **问题**：翻译卡片没有设置窗口图标，任务栏显示默认空白图标
- **修复**：加载 `resources/icon.ico` 作为窗口图标，与托盘图标一致

---

## v0.12.1 — 2026-05-26

### 修复：DeepSeek 搜索跳转空白页
- **问题**：DeepSeek 前端更新，`chat.deepseek.com/a/chat?q=` 参数不再自动填入输入框，跳转后显示空白页面
- **修复**：改为先将选中文字复制到剪贴板，再打开 DeepSeek 首页，用户 Ctrl+V 即可粘贴搜索

### 修复：翻译卡片始终置顶遮挡其他窗口
- **问题**：翻译卡片设置了 `WindowStaysOnTopHint`，无论打开什么软件都挡在前面，搜索 DeepSeek 时被卡片遮住
- **修复**：移除 `WindowStaysOnTopHint`，翻译卡片不再强制置顶，其他窗口可以正常覆盖它；卡片仍可拖动和交互

---

## v0.12.0 — 2026-05-26

### 新增：可视化设置窗口 + 多翻译提供商支持
- **设置窗口 UI**：Google 风格白色圆角卡片，居中显示，与翻译卡片视觉一致
  - 5 个翻译提供商卡片按钮（Google / MyMemory / DeepL / 百度 / Microsoft），选中蓝色高亮
  - API Key 输入区：密码模式 + 👁 显示切换，按提供商条件显示/隐藏
  - DeepL 免费 API 开关（`api-free.deepl.com`）
  - 🔗 连接测试按钮：绿灯/黄灯/红灯/灰灯状态反馈
  - 目标语言下拉选择器（19 种语言，带国旗 emoji）
  - 快捷键提示区：Ctrl+T / Ctrl+Q / ESC 蓝色药丸标签
  - 关于信息：版本号 + 引擎说明
- **多翻译提供商**：通过 `deep_translator` 库支持 5 个翻译引擎
  - Google 翻译（免费，无需 Key）
  - MyMemory（免费，无需 Key，单次最多 500 字符）
  - DeepL（高质量，需 API Key，有免费额度）
  - 百度翻译（中文优秀，需 AppID + AppKey）
  - Microsoft（需 Azure 认知服务 API Key）
- **连接测试**：`ConnectionTestWorker(QThread)` 后台线程翻译 "Hello" 测试连通性
- **配置持久化**：API Key 输入自动保存到 `config.json`（500ms 防抖）
- **托盘菜单**：新增 `open_settings` 信号，点击"⚙️ 设置"弹出可视化窗口（替代原来的 notepad 打开 config.json）
- **信号架构**：
  - `provider_changed(str)` → 切换翻译引擎 + 清缓存
  - `language_changed(str)` → 更新 config + 同步托盘菜单勾选
  - `credentials_changed()` → 清翻译缓存
- **打包更新**：`build.py` 添加 `deep_translator.deepl/baidu/microsoft/mymemory` hidden imports，dist 315MB

---

## v0.11.1 — 2026-05-26

### 优化：使用干净虚拟环境打包，体积 969MB → 316MB
- **问题**：之前用 ESP-IDF 的 Python 环境（D:\Robomaster\esp32-idf\...）打包，PyInstaller 把 torch、scipy、pandas 等无关包全部卷入，dist 高达 969MB
- **修复**：创建独立虚拟环境 `.venv`（Python 3.11），只安装 HoverTranslator 实际需要的 6 个库
- **结果**：dist 从 969MB 缩小到 316MB，exe 本体 5.9MB
- 清理了错误环境中安装的 HoverTranslator 专属包（deep-translator、pynput、rapidocr-onnxruntime）

---

## v0.11.0 — 2026-05-26

### 新增：PyInstaller 打包成 .exe
- 创建 `build.py` 打包脚本，一键生成可执行文件
- 输出路径：`dist/HoverTranslator/HoverTranslator.exe`
- `--windowed` 模式，运行时无控制台黑窗口
- 资源文件（字体、图标）打包进 `_internal/` 目录
- 隐藏导入：PyQt6.sip、deep_translator、rapidocr_onnxruntime、pynput._win32
- `config.json` 需放在 exe 同目录，用户可自由编辑

### 适配：打包路径兼容
- `config.py`：frozen 模式下 config.json 路径指向 `sys.executable` 所在目录
- `font_manager.py`：frozen 模式下字体从 `sys._MEIPASS`（`_internal/`）加载
- `tray_icon.py`：新增 `_base_dir()` / `_resource_dir()` 辅助函数，区分 frozen / 脚本模式
- `ocr_engine.py`：调试截图目录适配 frozen 路径

### 修复：打包后 OCR 引擎无法启动
- **根因**：PyInstaller 只收集 `.py` 文件，不会自动打包 `rapidocr_onnxruntime` 的数据文件（`config.yaml` + `models/*.onnx`）
- **表现**：exe 启动正常，快捷键正常触发，但 OCR 阶段报 `FileNotFoundError: config.yaml`
- **修复**：`build.py` 添加 `--collect-data=rapidocr_onnxruntime`，自动收集包内所有非 Python 文件（config.yaml、3 个 ONNX 模型文件约 16MB）
- **排查过程**：逐步添加文件日志（hotkey → OCR → translator），定位到 OCR 初始化阶段崩溃；控制台版本确认错误信息

### 使用方式
1. 开发模式：`python main.py`（不变）
2. 打包：`python build.py` → 生成 `dist/HoverTranslator/`
3. 运行：双击 `dist/HoverTranslator/HoverTranslator.exe`
4. 修改配置：编辑 exe 同目录的 `config.json`

---

## v0.10.0 — 2026-05-26

### 新增：右键 DeepSeek 搜索
- 右键选中文字后出现自定义菜单：「📋 复制」+「🔍 DeepSeek 搜索」
- 通过 eventFilter 拦截 QLabel 的右键事件，替换默认菜单
- 搜索打开 `chat.deepseek.com/a/chat?q=选中文字`，国内无需 VPN
- 通过 `label.selectedText()` 获取选中内容，无选中时菜单项置灰

### 新增：卡片内语言选择器
- 语言标签从纯文本改为可点击按钮，弹出语言选择弹窗
- 7 种语言：中文、English、日本語、한국어、Français、Русский、Español
- 当前语言高亮，选后自动重新翻译

### 新增：OCR 智能分段
- `_join_ocr_lines()` 根据行间距自动检测段落边界，段内空格连接，段间 `\n\n` 分隔
- 翻译引擎按段落并行翻译（ThreadPoolExecutor），保留原文结构
- 单段落走快速路径，无额外开销

### 字体：原文/译文双字体
- **原文**：Noto Sans SC（清秀克制）
- **译文**：HarmonyOS Sans SC（鸿蒙黑体，圆润现代，华为开源免费商用）
- `font_manager.py` 扩展为双字体加载器

### 优化：原文可滚动 + 同步滚动
- 原文区域改为 QScrollArea 包裹，最大高度 380px
- 原文和译文同步滚动，`_syncing` 标志防递归

### 优化：UI 细节
- 译文字号 26→**23px**
- 面板最小高度 520→**850px**
- 复制按钮缩小：padding 6×18，字号 14px
- 右键菜单样式：白色背景 + 圆角 + 蓝色 hover，去掉黑边

---

## v0.9.1 — 2026-05-26

### 优化：OCR 智能分段
- **根本问题**：OCR 把多行文字全部拼成一条，丢失段落结构，译文也是一大坨
- **修复**：`_join_ocr_lines()` 根据行间距自动检测段落边界——间距超过中位行高 80% 视为段落分隔，段内空格连接，段间 `\n\n` 分隔
- 翻译引擎按段落分别翻译，保留原文结构
- 多段落时使用 `ThreadPoolExecutor` 并行翻译，总耗时 = 最慢单段而非所有段之和
- 单段落走快速路径（一次请求），与之前一样快

---

## v0.9.0 — 2026-05-26

### 新增：卡片内语言选择器
- 语言标签从纯文本 `QLabel` 改为可点击 `QPushButton`，带 hover 效果
- 点击后弹出 `_LanguagePopup` 弹窗，白色卡片风格，与主面板一致
- 7 种语言可选：中文、English、日本語、한국어、Français、Русский、Español
- 当前选中语言高亮显示（蓝色背景 + 粗体）
- 弹窗自动定位在语言按钮下方，clamp 到屏幕边界内
- 选择语言后自动重新翻译当前原文，无需手动操作
- 源语言保持 auto 检测，与目标冲突时自动切换（原有逻辑）

---

## v0.8.2 — 2026-05-26

### 修复：拖动卡片后无法滚动和复制
- **根本问题**：`mousePressEvent` 在外层 Widget 上拦截所有左键点击，子控件（滚动区、按钮）收不到鼠标事件
- **修复**：新增 `_is_interactive_child()` 检查，点击在 `QPushButton` 或 `QScrollArea` 上时跳过拖动，让子控件正常处理事件

### 优化：卡片定位
- `_show_at_cursor()` 使用 `sizeHint()` 计算尺寸，`move()` 后 `show()`，不用 `setFixedSize`（会锁死大小导致布局异常）

---

## v0.8.1 — 2026-05-26

### 修复：偶现显示上一轮翻译结果
- **根本问题**：快速连续截图时，前一次 OCR/翻译的信号回调未失效，旧结果仍在到达
- **修复**：引入请求 ID 机制，每次新请求递增 `_request_id`，回调时检查 ID 是否匹配，不匹配直接丢弃

### 修复：卡片定位跳动
- **根本问题**：`show()` 后立即调用 `_position_near_cursor()`，但 Qt 布局尚未完成计算，导致位置不准确或闪跳
- **修复**：`show_loading` 先移到屏幕外再 `show()`，通过 `QTimer.singleShot(0, ...)` 延迟到下一个事件循环再定位；`show_result` 不再重新定位，避免卡片跳动

---

## v0.8.0 — 2026-05-25

### 修复：语言标签显示不全 + 方向错误
- **根本问题**：语言标签 `setFixedHeight(24)` 对 emoji + 中文文字来说太矮，文字被截断；且标签显示的是 config 中固定的 `target_lang`，而非实际翻译使用的目标语言，导致中文→英文时仍显示"简体中文 → 简体中文"
- **修复**：标签高度 24→**32px**；Translator 暴露 `_last_src` / `_last_target`，面板使用实际翻译语言显示标签

### 修复：卡片顶部超出屏幕
- **根本问题**：`_position_near_cursor()` 在 `show()` 之前调用 `adjustSize()`，布局未计算完成，拿到的高度不准确，导致卡片放到了屏幕外面
- **修复**：先 `show()` + `ensurePolished()` 再定位；补全 `show_result` 中的重新定位逻辑

---

## 卡片定位迭代过程记录（v0.7.2 → v0.8.2）

卡片定位经历了多次失败尝试，以下记录完整过程和教训。

### 尝试 1：压缩源文本 + scroll stretch（v0.7.2）
- **做法**：源文本 `setMaximumHeight(120)` + 滚动区 `stretch=1`
- **结果**：源文本被过度压缩显示不全，译文区仍然拥挤
- **教训**：空间分配问题不是靠压缩局部解决的，应该拉高整个卡片

### 尝试 2：拉高卡片 + 减小译文字号（v0.7.2 修订）
- **做法**：面板 `setMinimumHeight(520)` + 滚动区 `setMinimumHeight(350)` + 源文本 `setMaximumHeight(200)` + 译文字号 30→26px
- **结果**：效果不错，但定位出问题——卡片顶部超出屏幕
- **教训**：卡片尺寸变了，定位逻辑也要跟着调

### 尝试 3：先 show() 再定位（v0.8.0）
- **做法**：`show()` → `ensurePolished()` → `adjustSize()` → `_position_near_cursor()`
- **结果**：定位有时生效有时不生效；卡片先出现在错误位置再跳到正确位置
- **教训**：`show()` 后立刻定位有竞态问题，Qt 布局还没算完就 move 了

### 尝试 4：QTimer.singleShot(0) 延时定位（v0.8.1）
- **做法**：`move(-5000, -5000)` → `show()` → `QTimer.singleShot(0, _position_near_cursor)`
- **结果**：定位更不稳定；翻译结果有时出不来（面板卡在 -5000,-5000）
- **教训**：`-5000,-5000` 技巧在 PyQt6 中不必要且有害——当翻译结果来自缓存时（同线程直接信号），`_on_translated` 在定时器回调之前同步触发，面板永远在屏幕外

### 尝试 5：adjustSize → move → show（v0.8.2 初版）
- **做法**：回到标准模式 `adjustSize()` → `clamp到屏幕` → `move()` → `show()`
- **结果**：定位基本正确，但有轻微闪烁——`adjustSize()` 在 `show()` 前只拿到最小高度，`show()` 后布局重新计算导致跳动
- **教训**：`adjustSize()` 隐藏状态下计算不准

### 尝试 6：setFixedSize 锁定尺寸（v0.8.2 中版）
- **做法**：`sizeHint()` 拿宽度 + `setFixedSize(w, h)` 锁定尺寸 → `move()` → `show()`
- **结果**：位置正确了，但 `setFixedSize` 锁死了卡片大小，后续布局变化时位置全乱；用户拖动后无法滚动和复制
- **教训**：`setFixedSize()` 会永久锁定尺寸，破坏后续布局计算和子控件交互

### 最终方案（v0.8.2 最终版）
- **做法**：`sizeHint()` 估算宽高 → `move()` → `show()`，不用 `setFixedSize`
- **同时修复**：拖动事件用 `_is_interactive_child()` 排除按钮和滚动区
- **关键认知**：
  - PyQt6 中 `adjustSize()` 在 `show()` 前不准，不能依赖
  - `setFixedSize()` 会锁死布局，不能用
  - `sizeHint()` 是 `show()` 前唯一可靠的尺寸来源
  - `-5000,-5000` + 定时器回调方案在有同步信号时会失败
  - 外层 Widget 的 mousePressEvent 会拦截子控件事件，需要手动排除

---

## v0.7.2 — 2026-05-25

### 优化：译文区域空间分配
- **根本问题**：原文区无高度限制，长原文把面板空间全占满，译文区被挤得很小需要频繁滚动
- **修复**：原文区最大高度限制 **200px**；滚动区设置 `stretch=1` 优先占据剩余空间
- 面板最小高度 **520px**，滚动区最小高度 **350px**，保证卡片整体够大
- 译文字号 30→**26px**，同屏显示更多译文内容

---

## v0.7.1 — 2026-05-25

### 修复：卡片垂直高度不足
- **根本问题**：滚动区最大高度 600px 配大字体（22px/30px），文字几行就溢出滚动，阅读体验极差
- **修复**：滚动区最大高度 600→**1000px**，卡片整体高度大幅增加
- 内边距上下 36→**40px**，元素间距 20→**28px**，更透气

---

## v0.7.0 — 2026-05-25

### 字体：引入 Google Noto Sans SC
- **下载 Noto Sans SC**（Regular + Bold），Google 出品的开源中文字体，专门为中国大陆简体设计
- 字体文件存放于 `resources/fonts/`，随项目分发
- 新增 `font_manager.py` 字体加载器：自动加载项目字体，失败时回退系统等线
- 全局字体从等线升级为 Noto Sans SC

### 卡片再次大幅放大
- 最小宽度 520→**720px**，最大宽度 900→**1100px**，大屏终于撑得开
- 原文字号 19→**22px**，译文字号 25→**30px**
- 内边距 36×28 → **44×36**，更透气
- 语言标签 15→**16px**，圆角 13→**14px**
- 关闭按钮 36→**40px**，28px 字号
- 复制按钮 16→**17px**，圆角 10→**12px**
- 滚动条宽度 10→**12px**，更易操作
- 面板圆角 18→**22px**

---

## v0.6.0 — 2026-05-25

### UI 全面放大 + 字体升级
- **字体**：全局从微软雅黑改为等线（DengXian），更清秀现代
- **原文区**：15px → 19px，和译文一样大，不再委屈原文
- **译文区**：19px → 25px，更醒目
- **卡片尺寸**：最小宽度 380→520px，最大宽度 640→900px，大屏终于不显小
- **内边距**：24×20 → 36×28，更宽敞呼吸感
- **滚动区**：最大高度 400→600px
- **语言标签**：13→15px，圆角 11→13px
- **关闭按钮**：28→36px，26px 字号
- **复制按钮**：14→16px，更大点击区
- **滚动条**：宽度 8→10px，更易抓取
- **圆角**：14→18px，更圆润

---

## v0.5.0 — 2026-05-25

### 修复：DPI 坐标偏差
- **根本问题**：Qt6 使用逻辑像素，`ImageGrab.grab()` 使用物理像素，高 DPI 屏幕下选区与截图不一致
- **修复**：`OcrWorker` 内部通过 `devicePixelRatio()` 将逻辑坐标转为物理坐标
- 移除 `SetProcessDpiAwarenessContext`（与 Qt6 自身 DPI 处理冲突）

### 修复：OCR 识别率极低
- **根本问题**：自定义二值化预处理（阈值 160）破坏了真实截图中的文字信息
- **修复**：移除自定义预处理（灰度 + 二值化），改用 RapidOCR 内置预处理流水线
- 小区域自动 2x LANCZOS 放大提高检测率
- RapidOCR 引擎改为全局单例，避免重复初始化
- 新增调试功能：自动保存截图到 `debug_ocr/last_capture.png`，方便排查

### 优化：UI 卡片和字体（大幅增大）
- 翻译卡片：最小宽度 320→380px，最大宽度 560→640px
- 内边距：20×16 → 24×20，更宽敞
- 原文字号 13→15px，译文字号 15→19px
- 语言标签 11→13px，按钮 12→14px，关闭按钮 16→20px
- 滚动区最大高度 300→400px
- 全局字体 Microsoft YaHei（微软雅黑）

---

## v0.4.0 — 2026-05-25

### 快捷键修复
- **根本问题**：pynput 在按住 Ctrl 时报告 `\x14`（控制字符）而非 `'t'`，导致 Ctrl+T/Ctrl+Q 永远检测不到
- **修复**：`_key_to_name()` 将控制字符 `\x01`~`\x1a` 还原为字母 `a`~`z`
- **重构**：合并为单个 `HotkeyManager` 实例，支持注册多个快捷键
- 新增 `selector.py` 全屏截图选区工具

### 核心变更：截图选区翻译（参考 Pot Desktop 设计）

**交互方式重做**（解决了 v0.3 悬停方案的所有问题）：
- **Ctrl+T → 全屏蒙层 → 拖拽画框 → OCR → 翻译**
  - 用户自己选区，精确控制识别范围
  - 选区有蓝色边框 + 尺寸提示（如 400×120）
  - 半透明蒙层 + 十字光标，专业截图体验
- **Ctrl+Q 保留**：选中文字 → 快捷翻译

**UI 全面重写**（Google Translate 风格）：
- 白色背景 + 柔和阴影，告别黑乎乎
- 原文灰色小字 + 译文黑色大字，层次分明
- 文本可选中复制
- 长文本自动滚动（最大 300px 高度）
- 自适应宽度（320px ~ 560px）
- **不会自动消失**，点击 ✕ 或 ESC 关闭
- **可拖动**面板位置
- 语言标签：Google 蓝色圆角 badge

### 新增文件
- `selector.py` — 全屏截图选区工具（蒙层 + 拖拽画框 + 坐标转换）

### 移除
- 移除鼠标悬停自动翻译（误触发太多）
- 移除 `MouseIdleTracker`
- 移除暗色 glass-morphism 样式

---

## v0.3.0 — 2026-05-25

### 核心变更：鼠标悬停翻译
- **新增 `ocr_engine.py`** — 截取鼠标周围区域 + RapidOCR 离线识别
  - 完全离线，中英文混合识别，无需外部安装
  - 截取鼠标周围 440×160 像素区域
- **新增鼠标悬停检测** — 鼠标静止 1 秒自动触发 OCR → 翻译
  - 纯鼠标操作，不需要键盘
  - 图片、按钮、嵌入文字等不可选中的内容也能翻译
  - 鼠标移动时自动取消，不会误触发
- **新增 `MouseIdleTracker`** — pynput 全局鼠标监听，独立线程
- Ctrl+Q 快捷键保留为备选方式
- 托盘菜单改为「悬停翻译」开关（原「自动翻译」）

### 依赖变更
- 新增 `Pillow`（截图）
- 新增 `rapidocr-onnxruntime`（离线 OCR，中英文）

### 核心变更：鼠标悬停翻译
- **新增 `ocr_engine.py`** — 截取鼠标周围区域 + RapidOCR 离线识别
  - 完全离线，中英文混合识别，无需外部安装
  - 截取鼠标周围 440×160 像素区域
- **新增鼠标悬停检测** — 鼠标静止 1 秒自动触发 OCR → 翻译
  - 纯鼠标操作，不需要键盘
  - 图片、按钮、嵌入文字等不可选中的内容也能翻译
  - 鼠标移动时自动取消，不会误触发
- **新增 `MouseIdleTracker`** — pynput 全局鼠标监听，独立线程
- Ctrl+Q 快捷键保留为备选方式
- 托盘菜单改为「悬停翻译」开关（原「自动翻译」）

### 依赖变更
- 新增 `Pillow`（截图）
- 新增 `rapidocr-onnxruntime`（离线 OCR，中英文）

---

## v0.2.0 — 2026-05-25

### 新增
- `languages.py` 语言注册表，支持 19 种语言，扩展只需追加一行
- `proxy_detector.py` 代理自动检测模块
  - 优先直连测试（Warp/1.1.1.1 秒过）
  - 自动读取系统环境变量和 Windows 注册表代理设置
  - 快速端口扫描（socket 0.3s）+ 仅对开放端口做 HTTP 验证
  - 覆盖 Clash/V2Ray/SS/Trojan/Surge 等 9 个常见端口
- `README.md` 完整项目文档（安装、使用、配置、扩展说明）
- 托盘菜单「目标语言」分组子菜单（东亚/欧洲/其他）
- 托盘 tooltip 实时显示代理连接状态
- 托盘菜单「设置」入口，一键打开 config.json

### 改进
- 代理检测不再需要手动填写端口，全自动
- 翻译引擎改用外部注入代理，与 config 解耦
- 启动通知时序修复：先显示托盘再发通知
- 翻译失败提示更友好（区分超时/限流/其他错误）
- 语言方向标签改用语言注册表动态显示（如「🇬🇧 英语 → 🇨🇳 简体中文」）

---

## v0.1.0 — 2026-05-25

### 初始版本
- `main.py` 程序入口，单实例运行
- `translator.py` Google Translate 翻译引擎 + 缓存
- `tooltip.py` Glass-morphism 悬浮翻译卡片（圆角、阴影、淡入淡出动画）
- `hotkey_manager.py` Ctrl+Q 全局快捷键监听
- `tray_icon.py` 系统托盘图标和右键菜单
- `config.py` JSON 配置文件管理
- 剪贴板保护（翻译后恢复原内容）
- 自动语言检测（中英文方向）
