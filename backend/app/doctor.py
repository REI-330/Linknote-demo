from __future__ import annotations

import sys

from .services.config_manager import load_app_config
from .services.diagnostics import collect_health_bootstrap


def main() -> int:
    payload = collect_health_bootstrap(load_app_config())
    print(f"[LinkNote] Startup checks: {payload['status']}")
    for check in payload["checks"]:
        badge = "OK" if check["status"] == "ok" else "WARN"
        print(f"  [{badge}] {check['label']}: {check['detail']}")
        if check.get("followup"):
            print(f"         -> {check['followup']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
