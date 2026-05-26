import json
import sys
import os

DEFAULT_CONFIG = {
    "hotkey": "ctrl+q",
    "source_lang": "auto",
    "target_lang": "zh-CN",
    "theme": "dark",
    "auto_hide_seconds": 5,
    "font_size": 14,
    "max_text_length": 500,
    "proxy": "",
    # 翻译提供商
    "provider": "google",
    "deepl_api_key": "",
    "deepl_use_free_api": True,
    "baidu_appid": "",
    "baidu_appkey": "",
    "microsoft_api_key": "",
    "microsoft_region": "",
}

# exe 模式：config.json 在 exe 旁边；脚本模式：在脚本旁边
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")


class Config:
    def __init__(self):
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        self.save()

    def get_provider_credentials(self):
        """返回当前提供商的凭证字典。"""
        provider = self.get("provider", "google")
        if provider == "deepl":
            return {
                "api_key": self.get("deepl_api_key", ""),
                "use_free_api": self.get("deepl_use_free_api", True),
            }
        elif provider == "baidu":
            return {
                "appid": self.get("baidu_appid", ""),
                "appkey": self.get("baidu_appkey", ""),
            }
        elif provider == "microsoft":
            creds = {"api_key": self.get("microsoft_api_key", "")}
            region = self.get("microsoft_region", "")
            if region:
                creds["region"] = region
            return creds
        return {}
