"""Bootstrap Feishu user OAuth to obtain the first refresh_token.

Examples:
  python -m feishu.oauth_bootstrap --auth-url
  python -m feishu.oauth_bootstrap --exchange --code <AUTH_CODE>
  python -m feishu.oauth_bootstrap --print-scopes
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .auth import FeishuAuth
from .client import build_authorization_url, exchange_code_for_tokens
from .scopes import OAUTH_SCOPES, PERMISSION_CHECKLIST


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Feishu OAuth bootstrap")
    parser.add_argument(
        "--redirect-uri",
        default=os.getenv("FEISHU_REDIRECT_URI", "http://localhost:8787/callback"),
        help="Must match an authorized redirect URL in the Feishu app console",
    )
    parser.add_argument("--auth-url", action="store_true", help="Print consent URL")
    parser.add_argument("--exchange", action="store_true", help="Exchange auth code")
    parser.add_argument("--code", default=None, help="Authorization code from redirect")
    parser.add_argument("--print-scopes", action="store_true")
    args = parser.parse_args(argv)

    if args.print_scopes:
        print("OAuth scope string:\n")
        print(OAUTH_SCOPES)
        print("\nConsole checklist:")
        for scope, desc in PERMISSION_CHECKLIST:
            print(f"  - {scope}: {desc}")
        return 0

    auth = FeishuAuth()
    auth.require_app_credentials()

    if args.auth_url:
        url = build_authorization_url(auth.app_id, args.redirect_uri)
        print("在浏览器打开以下链接并授权（需包含 offline_access）：\n")
        print(url)
        print(
            "\n授权完成后，从回调 URL 的 ?code= 参数复制授权码，然后执行：\n"
            f"  FEISHU_APP_ID=... FEISHU_APP_SECRET=... "
            f"python -m feishu.oauth_bootstrap --exchange --code <CODE> "
            f"--redirect-uri {args.redirect_uri}"
        )
        return 0

    if args.exchange:
        if not args.code:
            print("--exchange 需要 --code", file=sys.stderr)
            return 2
        data = exchange_code_for_tokens(auth, args.code, args.redirect_uri)
        public = {
            "ok": True,
            "scope": data.get("scope"),
            "expires_in": data.get("expires_in"),
            "refresh_token_expires_in": data.get("refresh_token_expires_in"),
            "has_refresh_token": bool(data.get("refresh_token")),
            "cache": str(auth.cache_path),
            "token_meta": auth.bundle.to_public_dict(),
        }
        print(json.dumps(public, indent=2, ensure_ascii=False))
        if data.get("refresh_token"):
            print(
                "\n请将 refresh_token 写入 GitHub Secret `FEISHU_REFRESH_TOKEN`"
                "（或本机环境变量）。原始 token 已写入本地 cache，勿提交到 git。",
                file=sys.stderr,
            )
            # Print once to stdout for secret piping; marked clearly.
            print("\nFEISHU_REFRESH_TOKEN=" + data["refresh_token"])
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
