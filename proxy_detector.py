"""
代理自动检测模块。

检测顺序（快速路径优先）：
  1. 直连测试（Warp/1.1.1.1 等系统级 VPN 最先命中，1 秒内）
  2. config.json 中用户手动填写的 proxy
  3. 系统环境变量 HTTP_PROXY / HTTPS_PROXY
  4. Windows 注册表系统代理
  5. 快速扫描常见端口（socket 0.3s）→ 仅对开放端口做 HTTP 验证
"""

import os
import socket
import winreg
import requests

# 常见代理软件默认端口（按流行度排序）
COMMON_PORTS = {
    7890:  "Clash",
    10809: "V2Ray",
    1080:  "Shadowsocks",
    7891:  "Clash (备)",
    10808: "V2Ray (备)",
    1087:  "Shadowsocks (备)",
    10871: "Trojan",
    2080:  "Surge",
    8080:  "通用 HTTP",
}

TEST_URL = "https://www.google.com/generate_204"
HTTP_TIMEOUT = 4
SOCKET_TIMEOUT = 0.3


def detect_proxy(user_proxy=""):
    """返回可用的代理 URL，空字符串 = 直连。"""

    # 1. 直连测试（Warp / 1.1.1.1 等系统 VPN 最先）
    if _test_http(""):
        return ""

    # 2. 用户手动配置
    if user_proxy and _test_http(user_proxy):
        return user_proxy

    # 3. 环境变量
    env_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or ""
    if env_proxy and _test_http(env_proxy):
        return env_proxy

    # 4. Windows 注册表
    sys_proxy = _read_system_proxy()
    if sys_proxy and _test_http(sys_proxy):
        return sys_proxy

    # 5. 快速端口扫描 → 仅对开放端口做 HTTP 验证
    open_ports = _quick_port_scan()
    for port in open_ports:
        proxy_url = f"http://127.0.0.1:{port}"
        if _test_http(proxy_url):
            return proxy_url

    return ""


def _quick_port_scan():
    """用 socket 快速探测哪些端口有服务监听（每个 0.3s）。"""
    open_ports = []
    for port in COMMON_PORTS:
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=SOCKET_TIMEOUT)
            s.close()
            open_ports.append(port)
        except (OSError, socket.timeout):
            pass
    return open_ports


def _test_http(proxy_url):
    """测试通过代理（或直连）能否访问 Google。"""
    try:
        proxies = {"https": proxy_url, "http": proxy_url} if proxy_url else None
        resp = requests.get(TEST_URL, proxies=proxies, timeout=HTTP_TIMEOUT)
        return resp.status_code == 204
    except Exception:
        return False


def _read_system_proxy():
    """从 Windows 注册表读取系统代理。"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        )
        enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
        if enabled:
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
            winreg.CloseKey(key)
            if server:
                if "://" not in server:
                    server = "http://" + server
                return server
        winreg.CloseKey(key)
    except (OSError, FileNotFoundError):
        pass
    return ""
