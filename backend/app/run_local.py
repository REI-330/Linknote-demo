from __future__ import annotations

"""供 Windows 启动脚本调用的本地后端启动入口。"""

import os
import threading
import webbrowser

import uvicorn

from .services.config_manager import load_app_config


def _server_binding() -> tuple[str, int, bool]:
    config = load_app_config()
    host = config.server.host.strip()
    if not host:
        host = "0.0.0.0" if config.server.lan_enabled else "127.0.0.1"
    return host, config.server.port, config.server.open_browser


def main() -> None:
    host, port, open_browser = _server_binding()
    browser_host = "127.0.0.1" if host == "0.0.0.0" else host
    suppress_browser = os.getenv("LINKNOTE_SUPPRESS_BROWSER", "").strip().lower() in {"1", "true", "yes", "on"}
    # 自动打开浏览器对终端用户更友好，但开发脚本会关闭这一行为，
    # 这样前后端窗口可以独立启动。
    if open_browser and not suppress_browser:
        threading.Timer(1.5, lambda: webbrowser.open(f"http://{browser_host}:{port}/")).start()
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
