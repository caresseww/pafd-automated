from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import requests

OPEN_API_BASE = os.getenv("FEISHU_OPEN_API_BASE", "https://open.feishu.cn/open-apis")
DEFAULT_CACHE_PATH = Path(os.getenv("FEISHU_TOKEN_CACHE", ".feishu/token_cache.json"))


@dataclass
class TokenBundle:
    tenant_access_token: Optional[str] = None
    tenant_expire_at: Optional[float] = None
    user_access_token: Optional[str] = None
    user_expire_at: Optional[float] = None
    refresh_token: Optional[str] = None
    refresh_expire_at: Optional[float] = None
    scope: Optional[str] = None
    updated_at: Optional[float] = None

    def to_public_dict(self) -> dict[str, Any]:
        """Metadata safe for logs (no raw secrets)."""
        now = time.time()

        def remaining(ts: Optional[float]) -> Optional[int]:
            if ts is None:
                return None
            return max(0, int(ts - now))

        return {
            "has_tenant_access_token": bool(self.tenant_access_token),
            "tenant_seconds_left": remaining(self.tenant_expire_at),
            "has_user_access_token": bool(self.user_access_token),
            "user_seconds_left": remaining(self.user_expire_at),
            "has_refresh_token": bool(self.refresh_token),
            "refresh_seconds_left": remaining(self.refresh_expire_at),
            "scope": self.scope,
            "updated_at": self.updated_at,
        }


class FeishuAuth:
    """Manage tenant + user tokens for long-lived Feishu API access.

    - App credentials (FEISHU_APP_ID / FEISHU_APP_SECRET) never expire.
    - tenant_access_token lasts ~2h and is fetched on demand.
    - user refresh_token lasts ~7d; refresh twice weekly to avoid expiry.
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        cache_path: Path = DEFAULT_CACHE_PATH,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.app_id = app_id or os.getenv("FEISHU_APP_ID") or os.getenv("APP_ID")
        self.app_secret = (
            app_secret or os.getenv("FEISHU_APP_SECRET") or os.getenv("APP_SECRET")
        )
        self.cache_path = Path(cache_path)
        self.session = session or requests.Session()
        self.bundle = self._load_cache()
        if refresh_token or os.getenv("FEISHU_REFRESH_TOKEN"):
            self.bundle.refresh_token = (
                refresh_token or os.getenv("FEISHU_REFRESH_TOKEN") or self.bundle.refresh_token
            )

    def require_app_credentials(self) -> None:
        if not self.app_id or not self.app_secret:
            raise RuntimeError(
                "缺少 FEISHU_APP_ID / FEISHU_APP_SECRET。"
                "请在飞书开放平台创建企业自建应用，并将凭证写入环境变量或 GitHub Secrets。"
            )

    def get_tenant_access_token(self, force: bool = False) -> str:
        self.require_app_credentials()
        now = time.time()
        if (
            not force
            and self.bundle.tenant_access_token
            and self.bundle.tenant_expire_at
            and self.bundle.tenant_expire_at - now > 300
        ):
            return self.bundle.tenant_access_token

        url = f"{OPEN_API_BASE}/auth/v3/tenant_access_token/internal"
        resp = self.session.post(
            url,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"获取 tenant_access_token 失败: {data}")

        token = data["tenant_access_token"]
        expire = int(data.get("expire", 7200))
        self.bundle.tenant_access_token = token
        self.bundle.tenant_expire_at = now + expire
        self.bundle.updated_at = now
        self._save_cache()
        return token

    def refresh_user_access_token(self, force: bool = True) -> TokenBundle:
        """Refresh user token using one-time refresh_token; persist the new one."""
        self.require_app_credentials()
        if not self.bundle.refresh_token:
            raise RuntimeError(
                "缺少 FEISHU_REFRESH_TOKEN。"
                "请先运行: python -m feishu.oauth_bootstrap --auth-url"
                " 完成用户授权后换取 refresh_token。"
            )

        now = time.time()
        if (
            not force
            and self.bundle.user_access_token
            and self.bundle.user_expire_at
            and self.bundle.user_expire_at - now > 300
        ):
            return self.bundle

        url = f"{OPEN_API_BASE}/authen/v2/oauth/token"
        resp = self.session.post(
            url,
            json={
                "grant_type": "refresh_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "refresh_token": self.bundle.refresh_token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") not in (0, None) and "access_token" not in data:
            raise RuntimeError(f"刷新 user_access_token 失败: {data}")

        access = data.get("access_token")
        if not access:
            raise RuntimeError(f"刷新 user_access_token 失败: {data}")

        self.bundle.user_access_token = access
        self.bundle.user_expire_at = now + int(data.get("expires_in", 7200))
        new_refresh = data.get("refresh_token")
        if new_refresh:
            self.bundle.refresh_token = new_refresh
            refresh_ttl = int(data.get("refresh_token_expires_in", 604800))
            self.bundle.refresh_expire_at = now + refresh_ttl
        self.bundle.scope = data.get("scope", self.bundle.scope)
        self.bundle.updated_at = now
        self._save_cache()
        return self.bundle

    def ensure_tokens(self, prefer_user: bool = True) -> str:
        """Return a usable bearer token (user preferred when available)."""
        if prefer_user and self.bundle.refresh_token:
            bundle = self.refresh_user_access_token(force=False)
            if bundle.user_access_token:
                return bundle.user_access_token
        return self.get_tenant_access_token(force=False)

    def healthcheck(self) -> dict[str, Any]:
        result: dict[str, Any] = {"ok": False, "checks": {}}
        try:
            tenant = self.get_tenant_access_token(force=True)
            result["checks"]["tenant_access_token"] = {
                "ok": True,
                "prefix": tenant[:8] + "...",
            }
        except Exception as exc:  # noqa: BLE001 — surface in health report
            result["checks"]["tenant_access_token"] = {"ok": False, "error": str(exc)}
            result["token_meta"] = self.bundle.to_public_dict()
            return result

        if self.bundle.refresh_token:
            try:
                self.refresh_user_access_token(force=True)
                result["checks"]["user_access_token"] = {"ok": True}
            except Exception as exc:  # noqa: BLE001
                result["checks"]["user_access_token"] = {"ok": False, "error": str(exc)}
        else:
            result["checks"]["user_access_token"] = {
                "ok": False,
                "error": "FEISHU_REFRESH_TOKEN not configured (tenant-only mode)",
            }

        result["token_meta"] = self.bundle.to_public_dict()
        result["ok"] = result["checks"]["tenant_access_token"]["ok"]
        return result

    def _load_cache(self) -> TokenBundle:
        if not self.cache_path.exists():
            return TokenBundle()
        try:
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return TokenBundle(**{k: raw.get(k) for k in TokenBundle.__dataclass_fields__})
        except Exception:  # noqa: BLE001
            return TokenBundle()

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(asdict(self.bundle), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            os.chmod(self.cache_path, 0o600)
        except OSError:
            pass
