"""
语言注册表 —— 所有支持的语言定义在此文件中。
添加新语言只需在 LANGUAGES 列表中追加一项即可，无需修改其他文件。

字段说明：
  code  : deep-translator / Google Translate 使用的语言代码
  name  : 界面显示名称（中文）
  flag  : 可选的旗帜 emoji
  group : 分组标签，用于 UI 菜单归类（"东亚"/"欧洲"/"其他"）
"""

LANGUAGES = [
    # ── 东亚 ──────────────────────────────────────────────
    {"code": "zh-CN",  "name": "简体中文",  "flag": "🇨🇳", "group": "东亚"},
    {"code": "zh-TW",  "name": "繁體中文",  "flag": "🇹🇼", "group": "东亚"},
    {"code": "en",     "name": "英语",      "flag": "🇬🇧", "group": "东亚"},
    {"code": "ja",     "name": "日语",      "flag": "🇯🇵", "group": "东亚"},
    {"code": "ko",     "name": "韩语",      "flag": "🇰🇷", "group": "东亚"},

    # ── 欧洲 ──────────────────────────────────────────────
    {"code": "fr",     "name": "法语",      "flag": "🇫🇷", "group": "欧洲"},
    {"code": "de",     "name": "德语",      "flag": "🇩🇪", "group": "欧洲"},
    {"code": "es",     "name": "西班牙语",  "flag": "🇪🇸", "group": "欧洲"},
    {"code": "pt",     "name": "葡萄牙语",  "flag": "🇵🇹", "group": "欧洲"},
    {"code": "it",     "name": "意大利语",  "flag": "🇮🇹", "group": "欧洲"},
    {"code": "ru",     "name": "俄语",      "flag": "🇷🇺", "group": "欧洲"},
    {"code": "nl",     "name": "荷兰语",    "flag": "🇳🇱", "group": "欧洲"},
    {"code": "pl",     "name": "波兰语",    "flag": "🇵🇱", "group": "欧洲"},
    {"code": "sv",     "name": "瑞典语",    "flag": "🇸🇪", "group": "欧洲"},

    # ── 其他 ──────────────────────────────────────────────
    {"code": "ar",     "name": "阿拉伯语",  "flag": "🇸🇦", "group": "其他"},
    {"code": "hi",     "name": "印地语",    "flag": "🇮🇳", "group": "其他"},
    {"code": "th",     "name": "泰语",      "flag": "🇹🇭", "group": "其他"},
    {"code": "vi",     "name": "越南语",    "flag": "🇻🇳", "group": "其他"},
    {"code": "tr",     "name": "土耳其语",  "flag": "🇹🇷", "group": "其他"},
]


def get_language_map():
    """返回 {code: lang_dict} 字典，方便按 code 查找。"""
    return {lang["code"]: lang for lang in LANGUAGES}


def get_display_name(code):
    """根据语言 code 返回带旗帜的显示名，找不到时返回 code 本身。"""
    lang_map = get_language_map()
    if code in lang_map:
        l = lang_map[code]
        return f'{l["flag"]} {l["name"]}'
    return code


def get_grouped_languages():
    """按 group 分组返回，用于构建层级菜单。
    返回格式: {group_name: [lang_dict, ...], ...}
    """
    groups = {}
    for lang in LANGUAGES:
        groups.setdefault(lang["group"], []).append(lang)
    return groups


def detect_language(text):
    """简易语言检测：含 CJK 字符 → 中文，否则 → 英文。
    返回 deep-translator 的 source 参数值。
    """
    cjk_range = ("一", "鿿")
    for ch in text:
        if cjk_range[0] <= ch <= cjk_range[1]:
            return "zh-CN"
    return "en"
