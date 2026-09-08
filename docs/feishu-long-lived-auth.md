# Feishu / Lark long-lived access setup

科学问题层与分析角扩增（写入多维表格）见 `docs/science-question-expansion.md`。
#
# Goal: keep Cloud Agent / scripts able to call Feishu OpenAPI without relying on
# the short-lived personal remote-MCP URL (≈7 days).

## Why not only the official remote MCP link?

Personal Feishu MCP server URLs expire and need manual re-auth. For stable access:

1. Create an **企业自建应用** (custom app) — `APP_ID` / `APP_SECRET` never expire.
2. Fetch `tenant_access_token` on demand (~2h).
3. Once complete user OAuth with `offline_access`, rotate `refresh_token` twice weekly.

## One-time setup (you must do this in Feishu console)

1. Open [飞书开放平台](https://open.feishu.cn/app) → 创建企业自建应用.
2. **凭证与基础信息**：复制 App ID / App Secret.
3. **权限管理**：批量开通读写权限（脚本会打印完整列表）:

```bash
pip install -r requirements-feishu.txt
python -m feishu.oauth_bootstrap --print-scopes
```

至少包含：`offline_access`、`docx:document`、`drive:drive`、`wiki:wiki`、`bitable:app`、`sheets:spreadsheet` 及其 readonly 对应项。

4. **安全设置**：
   - 添加重定向 URL，例如 `http://localhost:8787/callback`
   - 打开「刷新 user_access_token」开关
5. **版本管理与发布**：创建版本 → 申请线上发布 → 管理员审批通过。
6. 把应用加入目标知识库/文档的**协作者**（例如「转录组文献库」），否则 tenant 身份读不到用户文档。

## Configure repository secrets

In GitHub → Settings → Secrets and variables → Actions, add:

| Secret | Required | Purpose |
| --- | --- | --- |
| `FEISHU_APP_ID` | yes | App ID |
| `FEISHU_APP_SECRET` | yes | App Secret |
| `FEISHU_REFRESH_TOKEN` | recommended | User offline refresh token |
| `FEISHU_SECRETS_PAT` | recommended | PAT that can update repo secrets (rotate refresh_token) |

`FEISHU_SECRETS_PAT` needs permission to set Actions secrets on this repo.

## Bootstrap the first refresh_token

```bash
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=xxx
export FEISHU_REDIRECT_URI=http://localhost:8787/callback

python -m feishu.oauth_bootstrap --auth-url
# open URL, authorize, copy ?code=...

python -m feishu.oauth_bootstrap --exchange --code <CODE>
# then store printed FEISHU_REFRESH_TOKEN into GitHub Secrets
```

## Twice-weekly automation

Workflow: `.github/workflows/feishu-token-refresh.yml`

- Cron: `0 2 * * 1,4` (Monday & Thursday 02:00 UTC)
- Also runnable via **Actions → Feishu Token Refresh → Run workflow**
- Rotates `refresh_token` and writes it back to `FEISHU_REFRESH_TOKEN` when `FEISHU_SECRETS_PAT` is set

Manual local refresh:

```bash
python -m feishu.refresh_tokens
python -m feishu.refresh_tokens --update-github-secret --repo owner/name
```

## Cursor Cloud Agent MCP

Prefer HTTP MCP configured at https://cursor.com/agents (MCP dropdown), **or** local stdio:

```json
{
  "mcpServers": {
    "lark-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@larksuiteoapi/lark-mcp",
        "mcp",
        "-a",
        "${FEISHU_APP_ID}",
        "-s",
        "${FEISHU_APP_SECRET}",
        "--oauth"
      ]
    }
  }
}
```

See also `docs/feishu-mcp.example.json`.

## Important limits

- Agents **cannot** grant Feishu open-platform permissions for you; console approval is required.
- After ~365 days, Feishu requires the user to re-consent for a new refresh_token.
- Personal remote MCP links remain short-lived; keep this app-credential path as the source of truth.
