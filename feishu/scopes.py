"""Recommended Feishu app scopes for full cloud-doc read/write access.

Enable these in 飞书开放平台 → 应用 → 权限管理, then publish a new version.
Also enable 「刷新 user_access_token」 in 安全设置, and grant offline_access.
"""

# Space-separated OAuth scope string used by oauth_bootstrap.py
OAUTH_SCOPES = " ".join(
    [
        "offline_access",
        # Docs (new + legacy)
        "docx:document",
        "docx:document:readonly",
        "docs:doc",
        "docs:doc:readonly",
        "docs:permission.member",
        "docs:permission.member:readonly",
        # Drive / files
        "drive:drive",
        "drive:drive:readonly",
        "drive:file",
        "drive:file:readonly",
        "drive:export:readonly",
        # Wiki
        "wiki:wiki",
        "wiki:wiki:readonly",
        "wiki:node:read",
        # Bitable
        "bitable:app",
        "bitable:app:readonly",
        # Sheets
        "sheets:spreadsheet",
        "sheets:spreadsheet:readonly",
        # Contact (minimal, for identity checks)
        "contact:user.base:readonly",
        "auth:user.id:read",
    ]
)

# Human-readable checklist for the developer console (batch-apply where possible)
PERMISSION_CHECKLIST = [
    ("offline_access", "离线访问 — 获取 refresh_token，长期续期必需"),
    ("docx:document", "创建及编辑新版文档"),
    ("docx:document:readonly", "查看新版文档"),
    ("docs:doc", "查看、评论、编辑和管理文档（旧版）"),
    ("docs:permission.member", "添加云文档协作者"),
    ("drive:drive", "查看、评论、编辑和管理云空间中所有文件"),
    ("drive:file", "上传、下载云空间文件"),
    ("wiki:wiki", "查看、编辑和管理知识库"),
    ("bitable:app", "查看、评论、编辑和管理多维表格"),
    ("sheets:spreadsheet", "查看、评论、编辑和管理电子表格"),
    ("contact:user.base:readonly", "获取用户基本信息"),
]
