#!/usr/bin/env python3
"""Organically fold public work packages into 课题落实; clear 近季.

Does not create 20 new 近季 rows. Cross questions stay inside the
课题 that already asks them. Analyses stay split (no hard merge).
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
T_NEAR = "tblu7FDd4xUFDfZo"
T_IMPL = "tblYfIYilivpVxPL"
T_CAT = "tblehZt4QnwGydED"
T_PRIN = "tblbJyzy6pXRgBf6"
T_DOMAIN = "tbl6gGWIjJK4EHuC"
DATE = "2026-09-10"
MARK = "有机整合 · 2026-09-10"
SPLIT = "分计划 · 2026-09-10"


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


def batch_delete(s: requests.Session, table: str, record_ids: list[str]) -> None:
    for i in range(0, len(record_ids), 500):
        api(
            s,
            "POST",
            f"/bitable/v1/apps/{APP}/tables/{table}/records/batch_delete",
            json={"records": record_ids[i : i + 500]},
        )


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


# 立刻动作整段重写：一个课题一份开工单，交叉问法写在本课题里。
IMPL_ACTION = {
    "发育坐标": (
        f"{MARK}\n"
        "本课题就是对照宇宙，三时钟和「脐血≠DOL1」在这里做，不另开近季。\n"
        "步骤：①发生层与循环三对象继续分列 ②GSE271413 / GSE326288 / GSE233321 / "
        "E-MTAB-7407 / Jardine 整倍体分别建时钟 ③证明孕龄、日龄、寿命箱不可并轴 "
        "④GSE212309 只写清脐血不是出生 48h ⑤仍补 Goh 文献行；GSE158702 只与 Ⅰ-5 并列。\n"
        "产出：全组对照坐标图。人员：跨数据集整合 1 人，3–4 月。\n"
        "禁令：禁止跨对象合图。禁止临床成熟度量表。尺子在「免疫度量」出，本课题不重画饼。"
    ),
    "免疫度量": (
        f"{MARK}\n"
        "本课题就是髓系尺子和四态证伪。与「发育坐标」同环境、分对象跑，不合池。\n"
        "步骤：①GSE253963 建嗜酸 vs 未成熟粒判别 ②GSE164120 验 NRBC ③出生窗未分选验证 "
        "④GSE236099 只看感染中轨迹，句子不交给「晚发感染」当 LOS。\n"
        "产出：注释参考 + 四态证伪。人员：注释 1 人，2–3 月。洪 82502089 的 CyTOF 投到这把尺子。\n"
        "禁令：禁止 MDSC 图题。分选极不进饼。"
    ),
    "标准与度量": (
        f"{MARK}\n"
        "各课题质控在这里收口，不另立项。\n"
        "步骤：①三对象分列 ②先踢 NRBC 再谈髓系 ③空值率成图 ④池化只作反例 "
        "⑤发育坐标 / 免疫度量的共享脚本放这里。\n"
        "禁令：全血、PBMC、分选禁止混饼。空值不插补。"
    ),
    "肠坏死": (
        f"{MARK}\n"
        "成熟度偏移和共享髓系是本课题的子问，不另开课题、不另开近季。\n"
        "步骤：①Egozi 非耗竭按谱系报方向，CD45 分区验内分泌耗竭 ②申请核验 OMIX012413"
        "（现场不是第二单细胞队列，另有一行种属=小鼠）；未核验不当第二发现 "
        "③子问-成熟度：供者投到「发育坐标」的时钟上，只报偏移方向 "
        "④子问-共享髓系：本课题只出肠侧模块；血尺子找「免疫度量」，公开 LOS 空格找「晚发感染」 "
        "⑤仍下 GeoMx / Lee bulk / GSE178088，先核与 Egozi 重叠。\n"
        "产出：外科对照谱系图 + 模块方向表。人员：对接黄一璜 / 曹芯诚，3–4 月。\n"
        "禁令：禁止与 OMIX 或 GSE178088 硬合并。Pan-GI 不是健康早产。方向表不是肠源性 LOS 证明。"
    ),
    "早发感染": (
        f"{MARK}\n"
        "早发败血症独立计划。垂直感染、出生转换窗。不与晚发共用分析设计、排期或图题。\n"
        "数据：GSE69686、E-MTAB-4785、SDY1538。胃液只在本计划做宿主模块对读。"
        "羊水在「监护环境」，本计划不搬矩阵。\n"
        "步骤：①三套各自质控、分研究解卷积 ②组成一栏、校正后状态一栏 "
        "③参照只用新生儿全血 ④等「免疫度量」交出参考后，只在本计划重跑 "
        "⑤胃液 LCN2/MMP8/S100/IL-6 与三套对读，不合矩阵 ⑥写早发组成文。\n"
        "产出：早发全血组成图 + 胃液对读表。人员：蒋胃液主持；陈绘宇只参与本计划。"
        "工期：现在开工，2–3 月。不等 HRA、不等 NeoVanc。\n"
        "本计划不含：HRA019867、NeoVanc、GSE138712、GSE236099、感染前血、LOS 预警模型。\n"
        "禁令：禁止与晚发写进同一份计划或同一张「败血症」图。禁止三套 meta。"
    ),
    "晚发感染": (
        f"{MARK}\n"
        "晚发败血症独立计划。医院获得、住院期防御真空。不与早发共用分析设计、排期或图题。\n"
        "数据：申请 HRA019867；下载 E-MTAB-15687 NeoVanc、GSE138712。"
        "GSE236099 只当「不是 LOS 主集」的反例，不进主分析。\n"
        "步骤：①本周申请 HRA，未获批不画结果 ②先下两套治疗日全血 "
        "③确诊与可能感染分臂 ④只问治疗后宿主程序随治疗日怎么变 "
        "⑤易感窗子问：在「发育坐标」上标住院时点，发病前点不是健康点 "
        "⑥HRA 元数据有病原分层再做分类器，没有就停 ⑦空格 4.3/4.5 当本计划设计页。\n"
        "产出：晚发治疗日轴 + 公开 LOS 空格页。人员：陈绘宇主做晚发；双结对/预警只引用本计划。"
        "工期：申请 4–8 周与下载并行；分析约 3 月。与早发同时开工，但是另一份计划。\n"
        "本计划不含：EOS 三套主分析、胃液矩阵、早发解卷积主文。\n"
        "禁令：禁止与早发共用计划或「新生儿败血症」标题。公开未分选 LOS 单细胞仍空。"
        "借「免疫度量」尺子只投影，不把出生窗写成 LOS 基线。"
    ),
    "肺与共病": (
        f"{MARK}\n"
        "BPD 第三维和远隔模块是同一课题的两层问法，不是两个清单。\n"
        "步骤：①核修 E-MTAB-14507，信主句不信「可进入发现」标签 ②指定专人申请 "
        "phs003427 与 EGA 肺（约 700GB）③肺–血–羊水分栏 ④远隔子问只写模块相似 "
        "⑤脑小胶质对读「动物模型」，不写同体肠-脑。\n"
        "人员：肺 + 受控大数据 1 人，3–4 月。\n"
        "禁令：模块相似 ≠ 同体共病。羊水坐标在「监护环境」，不并进循环年龄轴。"
    ),
    "监护环境": (
        f"{MARK}\n"
        "营养换档、治疗暴露、宫内印记、医院生态都是「监护当环境」的子问。\n"
        "步骤：①7.6 缺失图先做，对人 2023 队列字段 ②人侧喂养空格是主句；"
        "猪换档方向引用「动物模型」，不把猪当人肠时钟 "
        "③治疗暴露引用「晚发感染」的 NeoVanc，本课题只问坐标偏了没有，不是 LTi "
        "④羊水 GSE222204 单独成坐标 ⑤菌群另库，不对单细胞合图。\n"
        "人员：对接张樱彦 / 郭欣惠、曹。营养子问约 2 月，待发育坐标时钟可用。\n"
        "禁令：禁止乳汁对坏死肠。禁止人-猪对齐标尺。"
    ),
    "动物模型": (
        f"{MARK}\n"
        "本课题交一张外推边界表，供「肠坏死」和「监护环境」引用，不按物种加总。\n"
        "步骤：①四问对账：猪换档 / 鼠上皮 / 脾 BCG / 高氧外群 ②同源映射 "
        "③上皮主类能否对上 ④免疫亚群、Paneth、α-防御素、MDSC 写入不可外推 "
        "⑤鼠上皮代谢动与人上皮少动写成两句，交给肠坏死引用。\n"
        "产出：边界表。人员：对接刘璨，2–3 月。\n"
        "禁令：禁止跨物种 joint UMAP。猪无肠 α-防御素。模型极不写成人发现。"
    ),
    "外群与方法": (
        f"{MARK}\n"
        "年龄外推和成人/儿科脓毒症着色都在本课题，不另开包。\n"
        "步骤：①GSE279452 只外推着色 ②与出生窗、分选极分年龄并列 "
        "③交「成人文献不得代替新生儿」边界 ④UC 外群只校准肠坏死的通用炎症。\n"
        "禁令：不画新生儿败血症整合图。不与 GSE236099 合并。"
        "本课题不是早发或晚发的第三份计划，只给两份独立计划提供外推着色。"
    ),
    "本队列与标书": (
        f"{MARK}\n"
        "第三引擎。不新建公开课题，只引用上面课题已经在做的产出。\n"
        "洪 →「免疫度量」去 MDSC 图题 +「肠坏死」方向表（讨论用，不当肠源性证明）。\n"
        "黄 →「肠坏死」图谱；AhR 先选成纤维、先选 NEC。\n"
        "蒋胃液 → 只进「早发感染」独立计划。蒋分型 / LOS 预警 → 只进「晚发感染」独立计划。\n"
        "蒋抗菌 →「监护环境」治疗暴露（不是 LTi）。两份败血症计划不合并。\n"
        "曹 →「监护环境」缺失图 + 营养子问。\n"
        "近季表已清空。组会按本表 11 个课题开工。"
    ),
}

IMPL_EXTRA = {
    "发育坐标": f"{MARK} 人员：跨数据集整合 1 人。产出被免疫度量、肠坏死成熟度子问、晚发易感窗子问引用。",
    "免疫度量": f"{MARK} 人员：注释 1 人，与发育坐标同环境。产出被 82502089 与肠坏死共享髓系子问引用。",
    "肠坏死": f"{MARK} 人员：黄一璜 / 曹芯诚。成熟度借发育坐标，血侧空格借晚发，边界借动物模型。",
    "早发感染": f"{MARK} 独立计划。蒋胃液 + 陈绘宇（早发侧）。现在开工。不含晚发任何数据集。",
    "晚发感染": f"{MARK} 独立计划。陈绘宇主做晚发。HRA 专人跟申请。不含 EOS 三套主分析。",
    "肺与共病": f"{MARK} 人员：指定一人跑 dbGaP/EGA，不宜分散。",
    "监护环境": f"{MARK} 人员：张樱彦 / 郭欣惠、曹。猪矩阵不搬进本课题主对象。",
    "动物模型": f"{MARK} 人员：刘璨。边界表是给别人引用的公共品。",
    "本队列与标书": f"{MARK} 全文 docs/public-workpackage-tree.md。公开产出全组共享，按贡献署名。",
}

JOINT_LINE = (
    f"{MARK} 交叉子问留在本课题里对读，不另开近季，不与其它课题合池。"
)


def main() -> None:
    s = session()
    log: dict = {"date": DATE, "deleted_near": [], "updated": {}, "created": {}}

    near_rows = list_all(s, T_NEAR)
    to_delete = [r["record_id"] for r in near_rows]
    if to_delete:
        batch_delete(s, T_NEAR, to_delete)
        log["deleted_near"] = to_delete
        print("deleted 近季", len(to_delete), to_delete)
    else:
        print("近季 already empty")

    impl_rows = list_all(s, T_IMPL)
    impl_patch = []
    for rec in impl_rows:
        name = field_text((rec.get("fields") or {}).get("课题"))
        action = IMPL_ACTION.get(name)
        if not action:
            print("skip impl", name)
            continue
        fields = rec.get("fields") or {}
        new_fields = {"立刻动作": action}
        extra = IMPL_EXTRA.get(name)
        if extra:
            if name in {"早发感染", "晚发感染", "本队列与标书"}:
                merged_extra = append_note(fields.get("5. 个人还需补充"), extra)
                if SPLIT not in field_text(fields.get("5. 个人还需补充")):
                    merged_extra = append_note(
                        merged_extra,
                        f"{SPLIT} 早发与晚发两份独立计划，不共用开工单。",
                    )
                new_fields["5. 个人还需补充"] = merged_extra
            else:
                new_fields["5. 个人还需补充"] = append_note(
                    fields.get("5. 个人还需补充"), extra
                )
        new_joint = append_note(fields.get("3. 能否联合分析"), JOINT_LINE)
        if name in {"早发感染", "晚发感染"} and SPLIT not in field_text(
            fields.get("3. 能否联合分析")
        ):
            other = "晚发感染" if name == "早发感染" else "早发感染"
            new_joint = (
                new_joint.rstrip()
                + "\n\n"
                + f"{SPLIT} 本课题与「{other}」不能联合分析，不能共用设计、参照或图题。"
            )
        if new_joint != field_text(fields.get("3. 能否联合分析")):
            new_fields["3. 能否联合分析"] = new_joint
        impl_patch.append({"record_id": rec["record_id"], "fields": new_fields})
        print("impl", name)
    if impl_patch:
        batch_update(s, T_IMPL, impl_patch)
        log["updated"]["impl"] = [x["record_id"] for x in impl_patch]

    prin_rows = list_all(s, T_PRIN)
    prin33 = next(
        (
            r
            for r in prin_rows
            if r["fields"].get("次序") == 33 or str(r["fields"].get("次序")) == "33"
        ),
        None,
    )
    prin33_text = (
        "执行单位是课题落实。近季优先课题整表删除。"
        "汇报中的 P0/P1/交叉是课题内部的开工包和子问，不是新课题。"
        "有机整合：成熟度、共享髓系、易感窗、远隔、治疗暴露留在已经在问的课题里，"
        "借用其它课题锁住的尺子或空格，分栏对读。"
        "早发感染与晚发感染必须两份独立计划：数据、步骤、产出、人员、工期各写各的。"
        "硬合并：不同对象、对照宇宙、物种或早发/晚发画进同一张图或同一份开工单，或把交叉立成第六条主线。"
        "不新增第 10 层或第 35 张科学问题卡。"
    )
    if prin33:
        if "两份独立计划" not in field_text((prin33.get("fields") or {}).get("说明")):
            batch_update(
                s,
                T_PRIN,
                [
                    {
                        "record_id": prin33["record_id"],
                        "fields": {
                            "原则": "交叉问法挂在已有课题里；早发与晚发分开计划",
                            "说明": prin33_text,
                        },
                    }
                ],
            )
            log["updated"]["原则33"] = prin33["record_id"]
            print("updated 原则 33")
        else:
            print("原则 33 exists")
    else:
        created = batch_create(
            s,
            T_PRIN,
            [
                {
                    "fields": {
                        "次序": 33,
                        "原则": "交叉问法挂在已有课题里；早发与晚发分开计划",
                        "说明": prin33_text,
                    }
                }
            ],
        )
        log["created"]["原则33"] = created[0]["record_id"] if created else None
        print("created 原则 33", log["created"]["原则33"])

    for rec in list_all(s, T_DOMAIN):
        if field_text((rec.get("fields") or {}).get("主题编号")) != "8.10":
            continue
        fields = rec.get("fields") or {}
        note = (
            f"{MARK}\n"
            "近季已清空。组会按课题落实 11 个课题开工。"
            "公开组合七句仍是各课题步骤里的锁句，不再单独占一条近季。"
        )
        new_design = append_note(fields.get("分析设计"), note)
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

    cat_patch = []
    note = (
        f"{MARK}\n"
        "近季已删除。开工看课题落实：发育坐标 / 免疫度量 / 肠坏死 / 动物模型先并行。"
        "交叉子问挂在各课题内，不合池。"
    )
    for rec in list_all(s, T_CAT):
        num = field_text((rec.get("fields") or {}).get("大块编号"))
        if num not in {"Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ"}:
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

    for rec in list_all(s, T_CAT):
        if field_text((rec.get("fields") or {}).get("大块编号")) != "Ⅲ":
            continue
        fields = rec.get("fields") or {}
        if SPLIT in field_text(fields.get("现行进展")):
            print("skip cat Ⅲ split")
            break
        batch_update(
            s,
            T_CAT,
            [
                {
                    "record_id": rec["record_id"],
                    "fields": {
                        "现行进展": append_note(
                            fields.get("现行进展"),
                            f"{SPLIT} 早发感染与晚发感染两份独立计划，不共用开工单、排期或图题。",
                        )
                    },
                }
            ],
        )
        log["updated"]["catalog_III"] = rec["record_id"]
        print("updated catalog Ⅲ split")
        break

    leftover = list_all(s, T_NEAR)
    log["near_remaining"] = [
        field_text((r.get("fields") or {}).get("课题")) for r in leftover
    ]
    print("near remaining", log["near_remaining"])

    out = ROOT / ".feishu/exports/tx/20260910_public_workpackages.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
