#!/usr/bin/env python3
"""Write person×grant×public-data empowerment notes into Feishu (2026-09-10).

Idempotent: appends only when marker is absent; upserts 近季第 8 项 by 课题 name.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

for line in (
    (ROOT / ".feishu/credentials.env").read_text().splitlines()
    if (ROOT / ".feishu/credentials.env").exists()
    else []
):
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from feishu.auth import FeishuAuth  # noqa: E402

APP = "UOJMb64IDajJDXsjrarcVIS4nub"
OPEN = "https://open.feishu.cn/open-apis"
T_DOMAIN = "tbl6gGWIjJK4EHuC"
T_IMPL = "tblYfIYilivpVxPL"
T_NEAR = "tblu7FDd4xUFDfZo"
T_CAT = "tblehZt4QnwGydED"
DATE = "2026-09-10"
MARK = "工作台赋能 · 2026-09-10"


def session() -> requests.Session:
    tok = FeishuAuth().get_tenant_access_token()
    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/json; charset=utf-8",
        }
    )
    return s


def api(s: requests.Session, method: str, path: str, **kwargs) -> dict:
    r = s.request(method, f"{OPEN}{path}", timeout=60, **kwargs)
    data = r.json()
    if data.get("code") not in (0, None):
        raise RuntimeError(f"{method} {path}: {data}")
    return data


def list_all(s: requests.Session, table: str) -> list[dict]:
    out: list[dict] = []
    page_token = None
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        data = api(s, "GET", f"/bitable/v1/apps/{APP}/tables/{table}/records", params=params)
        out.extend(data["data"].get("items") or [])
        if not data["data"].get("has_more"):
            break
        page_token = data["data"].get("page_token")
    return out


def batch_update(s: requests.Session, table: str, records: list[dict]) -> None:
    for i in range(0, len(records), 500):
        api(
            s,
            "POST",
            f"/bitable/v1/apps/{APP}/tables/{table}/records/batch_update",
            json={"records": records[i : i + 500]},
        )


def batch_create(s: requests.Session, table: str, records: list[dict]) -> list[dict]:
    created: list[dict] = []
    for i in range(0, len(records), 500):
        data = api(
            s,
            "POST",
            f"/bitable/v1/apps/{APP}/tables/{table}/records/batch_create",
            json={"records": records[i : i + 500]},
        )
        created.extend(data["data"].get("records") or [])
    return created


def field_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and "text" in item:
                parts.append(item.get("text") or "")
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    if isinstance(value, dict):
        if "text" in value:
            return value.get("text") or ""
        if "text_arr" in value:
            return ",".join(value.get("text_arr") or [])
    return str(value)


def append_note(old, note: str) -> str:
    text = field_text(old).rstrip()
    if MARK in text:
        return text
    if not text:
        return note
    return text + "\n\n" + note


IMPL_NOTES = {
    "本队列与标书": {
        "立刻动作": (
            f"{MARK}\n"
            "四种用法对号：A 借尺子 / B 借对照宇宙 / C 借扰动 / D 借空格。\n"
            "洪 82502089：GSE326288+GSE253963+GSE164120 投影 CyTOF，去掉 MDSC 图题。\n"
            "黄：下 GSE297483/178088/268423，与 Egozi 分研究并列；GSE288751 不进成纤维主图。\n"
            "蒋胃液：宿主模块对读 EOS 三套与 GSE222204 羊水，不合并。\n"
            "蒋分型：写入分章纪律。曹/洪：7.6 缺失图对 2023 队列字段。\n"
            "P0 下载：NeoVanc、GSE138712、GSE297483、GSE178088、GSE158702。"
        ),
        "5. 个人还需补充": (
            f"{MARK}\n"
            "人员名册仍无权限。赋能按项目关联人员写：洪/蒋/黄/曹/严卫丽/陈海威/"
            "陈绘宇/张樱彦/骆凝馨/李淑涓/余微寅/郭欣惠/韩俊彦/张澜。\n"
            "全文见仓库 docs/workbench-tx-empowerment.md。"
        ),
    },
    "肠坏死": {
        "立刻动作": (
            f"{MARK} 黄国青：Egozi 已是人角方向。下 GSE297483 换队列不换对照。"
            "GSE154617 只对读吲哚 AhR。禁止鼠上皮证明成纤维。"
        ),
    },
    "早发感染": {
        "立刻动作": (
            f"{MARK} 蒋胃液：三套 bulk 是血组成，胃液只模块对读。"
            "羊水 GSE222204 与出生窗 GSE326288 分栏。不关闭 4.2。"
        ),
    },
    "晚发感染": {
        "立刻动作": (
            f"{MARK} 双结对/预警：先下 NeoVanc 与 GSE138712 写治疗日轴。"
            "空格 4.3/4.5 当设计页。不问人的 LOS 未分选极。"
        ),
    },
    "免疫度量": {
        "立刻动作": (
            f"{MARK} 洪 82502089：尺子投影替换 Meng Yao=M-MDSC。"
            "分选极不进饼。模型极不进人本尺。"
        ),
    },
    "监护环境": {
        "立刻动作": (
            f"{MARK} 曹/十五五：猪换档只比方向。乳汁待下载只作词典，时间对齐。"
            "蒋抗菌：NeoVanc 是暴露轴，不是 LTi。7.6 对 2023 队列字段。"
        ),
    },
    "动物模型": {
        "立刻动作": (
            f"{MARK} 工作台只用已纳入四问：猪换档、鼠上皮、脾 BCG、高氧外群。"
            "GSE154617 对读黄标书。GSE246144/200931 先写禁用。"
        ),
    },
}


DOMAIN_8_10 = (
    f"{MARK}\n"
    "四种用法：A 借尺子，B 借对照宇宙，C 借扰动，D 借空格。"
    "公开组合七句（不靠本队列）：分母三时钟、尺子极、Egozi 谱系、EOS 三套、"
    "早发/晚发分章、缺失指控、模型一段。其余空格仍是本队列理由。"
)

NEAR8 = {
    "次序": 8,
    "课题": "公开组合七句与标书赋能",
    "对应编号": "8.10；6.7；3.7；4.1",
    "数据广度": "中",
    "科学价值": "高",
    "完成难度": "低",
    "文献对标": "有方法学范例",
    "为何先做": "公开数据自己组合就能交分母、尺子、Egozi 方向、EOS 组成和缺失指控。各标书先对上这七句，再谈本队列。",
    "主要限制": "人员名册无权限；Idea 正文仍锁。",
    "对标文献": "Egozi 2023；Smith 出生窗；Cunnington EOS bulk；NeoVanc 待下载",
    "现在有什么数据": "纳入分析 28。人发现主集：Egozi、三套 EOS bulk、出生窗/日龄轴/分选极、羊水。",
    "数据规模": "可进入发现 19 + 可进入坐标 18。待下载不进本页。",
    "能否联合分析": "四种用法分列。禁止一张新生儿败血症图、禁止 MDSC 图题、禁止乳汁对坏死肠。",
    "下载状态": "P0：NeoVanc、GSE138712、GSE297483、GSE178088、GSE158702。",
    "个人还需补充": "见 docs/workbench-tx-empowerment.md。洪先改图题，黄先下 Lee bulk，蒋先写分章。",
}


def main() -> None:
    s = session()
    log: dict = {"date": DATE, "updated": {}, "created": {}}

    impl_rows = list_all(s, T_IMPL)
    impl_patch = []
    for rec in impl_rows:
        name = field_text((rec.get("fields") or {}).get("课题"))
        notes = IMPL_NOTES.get(name)
        if not notes:
            continue
        fields = rec.get("fields") or {}
        new_fields = {}
        for key, note in notes.items():
            merged = append_note(fields.get(key), note)
            if merged != field_text(fields.get(key)):
                new_fields[key] = merged
        if new_fields:
            impl_patch.append({"record_id": rec["record_id"], "fields": new_fields})
            print("impl", name, list(new_fields))
        else:
            print("skip impl", name)
    if impl_patch:
        batch_update(s, T_IMPL, impl_patch)
        log["updated"]["impl"] = [x["record_id"] for x in impl_patch]

    domain_rows = list_all(s, T_DOMAIN)
    for rec in domain_rows:
        if field_text((rec.get("fields") or {}).get("主题编号")) != "8.10":
            continue
        fields = rec.get("fields") or {}
        new_design = append_note(fields.get("分析设计"), DOMAIN_8_10)
        if new_design != field_text(fields.get("分析设计")):
            batch_update(
                s,
                T_DOMAIN,
                [{"record_id": rec["record_id"], "fields": {"分析设计": new_design}}],
            )
            log["updated"]["8.10"] = rec["record_id"]
            print("updated 8.10")
        else:
            print("skip 8.10")
        break

    near_rows = list_all(s, T_NEAR)
    have = {field_text((r.get("fields") or {}).get("课题")): r["record_id"] for r in near_rows}
    if NEAR8["课题"] in have:
        batch_update(s, T_NEAR, [{"record_id": have[NEAR8["课题"]], "fields": NEAR8}])
        log["updated"]["near8"] = have[NEAR8["课题"]]
        print("updated near8")
    else:
        created = batch_create(s, T_NEAR, [{"fields": NEAR8}])
        log["created"]["near8"] = created[0]["record_id"] if created else None
        print("created near8", log["created"]["near8"])

    cat_rows = list_all(s, T_CAT)
    cat_patch = []
    note = (
        f"{MARK}\n"
        "工作台赋能：公开组合七句先交卷。用法 A/B/C/D 对号。"
        "详见课题落实「本队列与标书」与近季第 8 项。"
    )
    for rec in cat_rows:
        num = field_text((rec.get("fields") or {}).get("大块编号"))
        if num not in {"Ⅰ", "Ⅱ", "Ⅲ", "Ⅴ"}:
            continue
        fields = rec.get("fields") or {}
        if MARK in field_text(fields.get("现行进展")):
            print("skip cat", num)
            continue
        cat_patch.append(
            {
                "record_id": rec["record_id"],
                "fields": {"现行进展": append_note(fields.get("现行进展"), note)},
            }
        )
    if cat_patch:
        batch_update(s, T_CAT, cat_patch)
        log["updated"]["catalog"] = [x["record_id"] for x in cat_patch]
        print("updated catalog", len(cat_patch))

    out = ROOT / ".feishu/exports/tx/20260910_workbench_empowerment.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
