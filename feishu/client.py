from __future__ import annotations

import os
from typing import Any, Optional
from urllib.parse import quote, urlencode

from .auth import FeishuAuth, OPEN_API_BASE
from .scopes import OAUTH_SCOPES


class FeishuClient:
    def __init__(self, auth: Optional[FeishuAuth] = None, prefer_user: bool = True) -> None:
        self.auth = auth or FeishuAuth()
        self.prefer_user = prefer_user

    def _headers(self) -> dict[str, str]:
        token = self.auth.ensure_tokens(prefer_user=self.prefer_user)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = path if path.startswith("http") else f"{OPEN_API_BASE}{path}"
        resp = self.auth.session.request(
            method, url, headers=self._headers(), timeout=60, **kwargs
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("code") not in (0, None):
            raise RuntimeError(f"Feishu API error on {method} {path}: {data}")
        return data

    def get_bot_info(self) -> dict[str, Any]:
        """Lightweight identity check using tenant token."""
        token = self.auth.get_tenant_access_token()
        resp = self.auth.session.get(
            f"{OPEN_API_BASE}/bot/v3/info",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def search_docs(self, query: str, count: int = 20) -> dict[str, Any]:
        return self.request(
            "POST",
            "/suite/docs-api/search/object",
            json={"search_key": query, "count": count, "offset": 0},
        )

    def get_docx_raw(self, document_id: str) -> dict[str, Any]:
        return self.request("GET", f"/docx/v1/documents/{document_id}/raw_content")

    def get_wiki_node(self, token: str) -> dict[str, Any]:
        return self.request("GET", f"/wiki/v2/spaces/get_node?token={quote(token)}")


def build_authorization_url(
    app_id: str,
    redirect_uri: str,
    scopes: str = OAUTH_SCOPES,
    state: str = "feishu-long-lived",
) -> str:
    """Build the user-consent URL (include offline_access for refresh_token)."""
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": state,
    }
    return "https://accounts.feishu.cn/open-apis/authen/v1/authorize?" + urlencode(
        params, quote_via=quote
    )


def exchange_code_for_tokens(
    auth: FeishuAuth,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    auth.require_app_credentials()
    resp = auth.session.post(
        f"{OPEN_API_BASE}/authen/v2/oauth/token",
        json={
            "grant_type": "authorization_code",
            "client_id": auth.app_id,
            "client_secret": auth.app_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") not in (0, None) and "access_token" not in data:
        raise RuntimeError(f"换取 user_access_token 失败: {data}")

    import time

    now = time.time()
    auth.bundle.user_access_token = data["access_token"]
    auth.bundle.user_expire_at = now + int(data.get("expires_in", 7200))
    if data.get("refresh_token"):
        auth.bundle.refresh_token = data["refresh_token"]
        auth.bundle.refresh_expire_at = now + int(
            data.get("refresh_token_expires_in", 604800)
        )
    auth.bundle.scope = data.get("scope")
    auth.bundle.updated_at = now
    auth._save_cache()
    return data
