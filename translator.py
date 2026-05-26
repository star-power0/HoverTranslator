import os
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from deep_translator import (
    GoogleTranslator,
    MyMemoryTranslator,
    DeeplTranslator,
    BaiduTranslator,
    MicrosoftTranslator,
)
from languages import detect_language


CACHE_MAX = 300

# ── 翻译提供商注册表 ──────────────────────────────────────

PROVIDERS = {
    "google": {
        "class": GoogleTranslator,
        "name": "Google 翻译",
        "emoji": "🌐",
        "description": "免费，无需 API Key，支持 130+ 语言",
        "requires_key": False,
    },
    "mymemory": {
        "class": MyMemoryTranslator,
        "name": "MyMemory",
        "emoji": "💾",
        "description": "免费，无需 API Key，单次最多 500 字符",
        "requires_key": False,
    },
    "deepl": {
        "class": DeeplTranslator,
        "name": "DeepL",
        "emoji": "🔷",
        "description": "高质量翻译，需 API Key（有免费额度）",
        "requires_key": True,
        "key_fields": ["api_key"],
    },
    "baidu": {
        "class": BaiduTranslator,
        "name": "百度翻译",
        "emoji": "🐻",
        "description": "中文翻译优秀，需 AppID + AppKey",
        "requires_key": True,
        "key_fields": ["appid", "appkey"],
    },
    "microsoft": {
        "class": MicrosoftTranslator,
        "name": "Microsoft",
        "emoji": "🪟",
        "description": "微软翻译，需 API Key（Azure 认知服务）",
        "requires_key": True,
        "key_fields": ["api_key"],
    },
}


class TranslateWorker(QThread):
    """后台线程：调用翻译 API，不阻塞 UI。"""

    finished = pyqtSignal(str, str, str)

    def __init__(self, text, source, target, translator_cls, translator_kwargs, proxy=None):
        super().__init__()
        self.text = text
        self.source = source
        self.target = target
        self.translator_cls = translator_cls
        self.translator_kwargs = translator_kwargs
        self.proxy = proxy

    def run(self):
        try:
            if self.proxy:
                os.environ["HTTP_PROXY"] = self.proxy
                os.environ["HTTPS_PROXY"] = self.proxy
            else:
                os.environ.pop("HTTP_PROXY", None)
                os.environ.pop("HTTPS_PROXY", None)

            translator = self.translator_cls(
                source=self.source, target=self.target, **self.translator_kwargs
            )
            paragraphs = [p.strip() for p in self.text.split("\n\n") if p.strip()]
            if len(paragraphs) <= 1:
                result = translator.translate(self.text)
                self.finished.emit(self.text, result or "", self.source)
            else:
                from concurrent.futures import ThreadPoolExecutor, as_completed
                futures = {}
                with ThreadPoolExecutor(max_workers=len(paragraphs)) as pool:
                    for i, para in enumerate(paragraphs):
                        futures[pool.submit(translator.translate, para)] = i
                    results = [None] * len(paragraphs)
                    for f in as_completed(futures):
                        idx = futures[f]
                        try:
                            results[idx] = f.result() or paragraphs[idx]
                        except Exception:
                            results[idx] = paragraphs[idx]
                self.finished.emit(self.text, "\n\n".join(results), self.source)
        except Exception as e:
            self.finished.emit(self.text, self._friendly_error(e), "error")

    @staticmethod
    def _friendly_error(e):
        err = str(e).lower()
        if "timeout" in err or "connect" in err:
            return "网络连接失败\n请确认代理/VPN 已开启"
        if "429" in err:
            return "请求过于频繁，请稍后再试"
        if "api" in err and ("key" in err or "credential" in err):
            return "API Key 无效或未配置\n请在设置中填写正确的 Key"
        return f"翻译失败: {str(e)[:80]}"


class ConnectionTestWorker(QThread):
    """后台线程：测试翻译提供商连接。"""

    finished = pyqtSignal(bool, str)

    def __init__(self, translator_cls, translator_kwargs):
        super().__init__()
        self.translator_cls = translator_cls
        self.translator_kwargs = translator_kwargs

    def run(self):
        try:
            t = self.translator_cls(source="auto", target="zh-CN", **self.translator_kwargs)
            result = t.translate("Hello")
            if result:
                self.finished.emit(True, f"连接成功: {result}")
            else:
                self.finished.emit(False, "返回结果为空")
        except Exception as e:
            self.finished.emit(False, str(e)[:80])


class Translator(QObject):
    """翻译引擎：管理缓存、语言方向、后台 worker。"""

    translated = pyqtSignal(str, str, str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._cache = {}
        self._worker = None
        self._test_worker = None
        self._active_proxy = None

    def set_proxy(self, proxy):
        """设置检测到的可用代理（空字符串 = 直连）。"""
        self._active_proxy = proxy or None

    def set_provider(self, provider_name):
        """切换翻译提供商并清空缓存。"""
        self.config["provider"] = provider_name
        self._cache.clear()

    def get_current_provider_info(self):
        """获取当前提供商信息。"""
        name = self.config.get("provider", "google")
        return PROVIDERS.get(name, PROVIDERS["google"])

    def test_connection(self, callback):
        """测试当前提供商连接，结果通过 callback(success, message) 回调。"""
        provider_name = self.config.get("provider", "google")
        info = PROVIDERS.get(provider_name, PROVIDERS["google"])
        creds = self.config.get_provider_credentials()
        self._test_worker = ConnectionTestWorker(info["class"], creds)
        self._test_worker.finished.connect(callback)
        self._test_worker.start()

    def translate(self, text):
        text = text.strip()
        if not text:
            return
        max_len = self.config["max_text_length"]
        if len(text) > max_len:
            text = text[:max_len]

        source, target = self._resolve_languages(text)
        self._last_src = source
        self._last_target = target

        provider_name = self.config.get("provider", "google")
        cache_key = (text, source, target, provider_name)
        if cache_key in self._cache:
            self.translated.emit(*self._cache[cache_key])
            return

        info = PROVIDERS.get(provider_name, PROVIDERS["google"])
        creds = self.config.get_provider_credentials()
        self._worker = TranslateWorker(
            text, source, target, info["class"], creds, self._active_proxy
        )
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _resolve_languages(self, text):
        source = self.config["source_lang"]
        target = self.config["target_lang"]

        if source == "auto":
            detected = detect_language(text)
            if detected == "zh-CN":
                return "zh-CN", target if target != "zh-CN" else "en"
            else:
                return "auto", target

        return source, target

    def _on_finished(self, orig, result, lang):
        provider_name = self.config.get("provider", "google")
        cache_key = (orig, self._last_src, self._last_target, provider_name)
        self._cache[cache_key] = (orig, result, lang)
        if len(self._cache) > CACHE_MAX:
            self._cache.pop(next(iter(self._cache)))
        self.translated.emit(orig, result, lang)
