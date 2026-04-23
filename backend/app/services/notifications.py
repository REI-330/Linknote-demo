from __future__ import annotations

import subprocess
import textwrap

from ..config.settings import AppConfig


def daily_report_url(config: AppConfig, report_date: str) -> str:
    host = config.server.host.strip() or "127.0.0.1"
    if host == "0.0.0.0":
        host = "127.0.0.1"
    return f"http://{host}:{config.server.port}/?report_date={report_date}"


def notify_daily_report_ready(config: AppConfig, report_date: str, total_items: int, completed_items: int, failed_items: int) -> None:
    if not config.notification.enabled or not config.schedule.notify_on_complete:
        return
    url = daily_report_url(config, report_date)
    title = "LinkNote 日报整理完成"
    body = f"{report_date} 共 {total_items} 条，完成 {completed_items} 条，失败 {failed_items} 条。点击打开日报。"
    _show_windows_balloon(title, body, url)


def _show_windows_balloon(title: str, body: str, url: str) -> None:
    safe_url = url.replace("'", "''")
    script = textwrap.dedent(
        f"""
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $script:opened = $false
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.BalloonTipTitle = {title!r}
        $notify.BalloonTipText = {body!r}
        $notify.Visible = $true

        $openAction = {{
            if ($script:opened) {{
                return
            }}
            $script:opened = $true
            Start-Process '{safe_url}' | Out-Null
        }}

        $notify.add_BalloonTipClicked($openAction)
        $notify.add_Click($openAction)
        $notify.add_DoubleClick($openAction)
        $notify.ShowBalloonTip(5000)

        $end = (Get-Date).AddSeconds(12)
        while (-not $script:opened -and (Get-Date) -lt $end) {{
            [System.Windows.Forms.Application]::DoEvents()
            Start-Sleep -Milliseconds 200
        }}

        $notify.Dispose()
        """
    ).strip()
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
