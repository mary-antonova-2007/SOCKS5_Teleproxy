from __future__ import annotations

import argparse
import json
import sys

from .service import TelegramSocks5Service
from .settings import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telegram_socks5_api")
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser("bootstrap", help="Create initial admin and materialize runtime config")
    bootstrap.add_argument("--admin-username", required=True)
    bootstrap.add_argument("--admin-password", required=True)
    bootstrap.add_argument("--force", action="store_true")
    bootstrap.add_argument("--skip-reload", action="store_true")

    sub.add_parser("render-config", help="Write current 3proxy config to the shared data path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = TelegramSocks5Service(get_settings())

    if args.command == "bootstrap":
        record = service.bootstrap_admin(
            args.admin_username,
            args.admin_password,
            force=args.force,
        )
        service.ensure_runtime()
        if not args.skip_reload:
            service.reloader.reload()
        print(json.dumps({"status": "ok", "admin": record.username}, ensure_ascii=False))
        return 0

    if args.command == "render-config":
        path = service.save_config_only()
        print(json.dumps({"status": "ok", "config": str(path)}, ensure_ascii=False))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
