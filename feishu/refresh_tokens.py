"""Refresh Feishu tokens and optionally sync FEISHU_REFRESH_TOKEN to GitHub Secrets.

Intended for twice-weekly automation so refresh_token (~7d TTL) never expires.

Examples:
  python -m feishu.refresh_tokens
  python -m feishu.refresh_tokens --update-github-secret
  python -m feishu.refresh_tokens --tenant-only
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from .auth import FeishuAuth


def update_github_secret(name: str, value: str, repo: str | None = None) -> None:
    env = os.environ.copy()
    # Prefer an explicit secrets-admin token; fall back to GH_TOKEN/GITHUB_TOKEN.
    token = (
        os.getenv("FEISHU_SECRETS_PAT")
        or os.getenv("SECRETS_ADMIN_TOKEN")
        or os.getenv("GH_TOKEN")
        or os.getenv("GITHUB_TOKEN")
    )
    if not token:
        raise RuntimeError(
            "更新 GitHub Secret 需要 FEISHU_SECRETS_PAT（fine-grained PAT，"
            "具备 Secrets: Read and write）"
        )
    env["GH_TOKEN"] = token
    cmd = ["gh", "secret", "set", name, "--body", value]
    if repo:
        cmd.extend(["--repo", repo])
    subprocess.run(cmd, check=True, env=env)


def write_github_job_summary(payload: dict) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [
        "## Feishu token refresh",
        "",
        f"- ok: `{payload.get('ok')}`",
        f"- mode: `{payload.get('mode')}`",
        "",
        "```json",
        json.dumps(payload.get("token_meta", {}), indent=2, ensure_ascii=False),
        "```",
        "",
    ]
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh Feishu API tokens")
    parser.add_argument(
        "--tenant-only",
        action="store_true",
        help="Only refresh tenant_access_token (app identity)",
    )
    parser.add_argument(
        "--update-github-secret",
        action="store_true",
        help="Write rotated FEISHU_REFRESH_TOKEN back to GitHub Secrets",
    )
    parser.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPOSITORY"),
        help="owner/name for gh secret set",
    )
    parser.add_argument(
        "--fail-without-refresh-token",
        action="store_true",
        help="Exit non-zero if user refresh_token path is unavailable",
    )
    args = parser.parse_args(argv)

    auth = FeishuAuth()
    report: dict = {"ok": False, "mode": "tenant-only" if args.tenant_only else "full"}

    try:
        auth.get_tenant_access_token(force=True)
        report["tenant"] = "ok"
    except Exception as exc:  # noqa: BLE001
        report["tenant"] = f"error: {exc}"
        report["token_meta"] = auth.bundle.to_public_dict()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        write_github_job_summary(report)
        return 1

    if not args.tenant_only:
        try:
            before = auth.bundle.refresh_token
            auth.refresh_user_access_token(force=True)
            report["user"] = "ok"
            after = auth.bundle.refresh_token
            report["refresh_token_rotated"] = bool(after and after != before)
            if args.update_github_secret and after:
                try:
                    update_github_secret(
                        "FEISHU_REFRESH_TOKEN", after, repo=args.repo
                    )
                    report["github_secret_updated"] = True
                except Exception as secret_exc:  # noqa: BLE001
                    # Rotation succeeded locally; secret sync is best-effort.
                    report["github_secret_updated"] = False
                    report["github_secret_error"] = str(secret_exc)
        except Exception as exc:  # noqa: BLE001
            report["user"] = f"error: {exc}"
            if args.fail_without_refresh_token:
                report["token_meta"] = auth.bundle.to_public_dict()
                print(json.dumps(report, indent=2, ensure_ascii=False))
                write_github_job_summary(report)
                return 1

    report["ok"] = report.get("tenant") == "ok" and (
        args.tenant_only or report.get("user") == "ok"
    )
    report["token_meta"] = auth.bundle.to_public_dict()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    write_github_job_summary(report)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
