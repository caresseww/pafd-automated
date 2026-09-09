#!/usr/bin/env python3
"""Cross-walk workbench grants/ideas onto the proof layer (2026-09-09).

Idempotent: new records are created only if 主题编号 / 课题 / 原则 / slug is missing.
Workbench notes are appended to 假证明 / 分析设计 only when the marker is absent.
Requires FEISHU_APP_ID / FEISHU_APP_SECRET (tenant token is enough).
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
NEAR6 = "recvu4KfhdtXzf"

T_DOMAIN = "tbl6gGWIjJK4EHuC"
T_CAT = "tblehZt4QnwGydED"
T_NEAR = "tblu7FDd4xUFDfZo"
T_IMPL = "tblYfIYilivpVxPL"
T_PRIN = "tblbJyzy6pXRgBf6"
T_METH = "tblpkQr9jGh5ZnC1"

DATE = "2026-09-09"
MARK = "工作台补白 · 2026-09-09"


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


NEW_DOMAIN = [
    {
        "主题编号": "8.10",
        "问题名称": "本队列是第三引擎，标书名词不得覆盖证明层",
        "问题层": "8 模型与转化",
        "科学层": "模型与转化",
        "命题类型": "方向说明",
        "分析方向": "模型转化",
        "近季动作": "进入分析",
        "公共数据进入": "视角本身",
        "原编号": "工作台；82502089；双结对",
        "排序": 810,
        "优先序": 810,
        "证明角色": "证明条件",
        "所属问题": ["全题条件"],
        "科学问题": "课题组工作台的课题和 Idea，是第二份题库，还是本队列已经测到的句子？",
        "主句": "工作台课题与已发表队列是第三引擎。它写下本队列已经测到的句子，不抬高公共发现条数，也不许用标书细胞名词覆盖证明层已锁句子。",
        "假证明": "把 82502089 的 MDSC 写进 6.1 图题；把 EOS、LOS、NEC 聚成一个重症感染内型；用公开单细胞复述标书机制图。",
        "图上分栏": "公共句一栏，本队列句一栏，标书机制图一栏。后两栏不得改写第一栏图题。",
        "分析设计": (
            "第三引擎只写本队列对象：粪蛋白与代谢、血 CyTOF、胃液前哨、逐日喂养/抗菌/导管字段。\n"
            "82502089 可写梭菌–丁酸–粪 S100 中介，以及 HLA-DR-low 髓系随日龄与 LOS±48h 的位移。"
            "图题用位移，不用髓系来源抑制细胞。\n"
            "Idea 表租户令牌无读权限。对账只用项目与文章上的链接文本。"
        ),
        "数据与口径": "工作台 10 个项目；Idea 名来自链接文本。不消耗新的公共队列。",
        "证据边界": "标书创新点不是证明层主句。本队列不关闭 9.x 对公共数据的指控。",
        "现在可进入的数据": "2023 队列粪多组学、CyTOF、胃液预试验、已发表 NPJ / Front Immunol / Gut Microbes / Mucosal Immunol。",
        "若做成会改变什么": "近季不再用 MDSC 或重症感染内型覆盖已锁句子。",
    },
    {
        "主题编号": "6.7",
        "问题名称": "S100A8/A9 必须按舱室分句",
        "问题层": "6 免疫语言",
        "科学层": "免疫语言",
        "命题类型": "具体问题",
        "分析方向": "免疫语言",
        "近季动作": "进入分析",
        "公共数据进入": "可进入发现",
        "原编号": "82502089；胃液；NPJ2026",
        "排序": 670,
        "优先序": 670,
        "证明角色": "证明语言",
        "所属问题": ["尺子", "A 分母", "B 肠终末", "C 两种感染"],
        "科学问题": "同一份 S100A8/A9，在粪、胃液、循环血和切除肠里，是不是同一个发现？",
        "主句": "S100A8/A9 按舱室分句：粪蛋白、胃液宿主标志、循环髓系程序、切除肠组织，不是同一个发现。",
        "假证明": "用粪钙卫蛋白证明血 MDSC；用胃液 S100 证明肠坏死；用组成性新生儿髓系高表达证明抑制细胞。",
        "图上分栏": "粪、胃液、循环 CyTOF、公共血 sc、鼠肠 sc 五栏。NEC 升高、喂养不耐受降低、LOS 降低不得平均。",
        "分析设计": (
            "粪：NEC 急性期升高（Hong CTG 2023）；喂养不耐受更低（Hong Nutrients 2023）；"
            "LOS 标书图 2 写下降；NICU 暴露调制钙卫蛋白（Huang NPJ 2026）。三套相反句子是时钟加情境。\n"
            "胃液：EOS 候选宿主标志之一，停在前哨舱室。\n"
            "血：CyTOF 只报 HLA-DR-low 髓系随日龄与 LOS±48h；公共 sc 只报组成性高表达与发生残留。\n"
            "禁用：Meng Yao 2024 重分析写成早产 M-MDSC；粪蛋白写成 MDSC 功能。"
        ),
        "数据与口径": "本队列粪 ELISA / 蛋白组；胃液预试验；CyTOF N=42；公共尺子仍是 6.1。",
        "证据边界": "跨舱室不可互换，直到同窗配对出现。血极只描述图谱，不证明 LOS。",
        "现在可进入的数据": "本队列粪与 CyTOF；公共出生窗与分选极。LOS 未分选单细胞仍空。",
        "若做成会改变什么": "82502089 与胃液标书不再共用一个 S100 图题。",
    },
    {
        "主题编号": "3.7",
        "问题名称": "AhR 必须先选细胞与疾病",
        "问题层": "3 少死于肠坏死",
        "科学层": "保护肠",
        "命题类型": "具体问题",
        "分析方向": "肠",
        "近季动作": "进入分析",
        "公共数据进入": "可进入发现",
        "原编号": "黄国青；双结对 Idea；蒋 LTi",
        "排序": 370,
        "优先序": 370,
        "证明角色": "证明角度",
        "所属问题": ["B 肠终末", "C 两种感染"],
        "科学问题": "ILA/IAA–AhR 在坏死成纤维里致病，能不能和 LOS 屏障保护、LTi 签名基因写成同一句？",
        "主句": "AhR 不是疾病名词。坏死成纤维里它可以是致病输出；LOS 屏障里它仍是另一句；LTi 签名里它只是基因名。",
        "假证明": "写成 AhR 通路参与早产儿肠道疾病；用鼠上皮铁死亡证明成纤维 AhR；把 ILA/IAA 保护叙事与致病叙事平均。",
        "图上分栏": "成纤维致病一栏，屏障保护一栏，LTi 基因名一栏。人 Egozi 谱系方向单独一栏。",
        "分析设计": (
            "人角：3.3 仍写髓系促炎、成纤维同向、上皮少动。公开 GSE297483 / zenodo 只换队列、不换外科对照宇宙。\n"
            "本队列粪角：发病前肠杆菌–ILA/IAA–钙卫蛋白耦联（黄标书图 1），与 NPJ 2026 同一矩阵的上游句。\n"
            "模型角：Pdgfra-Cre; Ahr^fl/fl 只证鼠必需性。8.7 / GSE288751 上皮代谢是正交句，不进本题主图。\n"
            "Idea「HbF参与NEC氧化应激」是第三句，不并进 AhR。"
        ),
        "数据与口径": "黄标书图 1–6；Egozi 非耗竭；GSE288751 禁用为本题因果。",
        "证据边界": "鼠遗传学不是人验证。外科对照方向不是 Ptgs2+ 成纤维已立住。",
        "现在可进入的数据": "人谱系方向已在 3.3。AhR 因果只在鼠。",
        "若做成会改变什么": "黄标书与双结对 Idea 不再共用一个 AhR 图题。",
    },
]


NOTE = {
    "V4": (
        f"{MARK}\n"
        "82502089 仍用髓系来源抑制细胞作创新点。本队列 CyTOF 与 Huang Front Immunol 2026 "
        "已经把 NEC 血写成 HLA-DR-low 单核位移。图题跟位移，不跟标书名词。"
    ),
    "6.1": (
        f"{MARK}\n"
        "人尺子未锁前，禁止把标书图 4 鼠低 MHC 簇或 Meng Yao 重分析写成人尺。"
        "本队列只许问模块差是否与 S100 / 丁酸应答重叠。见 6.7。"
    ),
    "2.4": (
        f"{MARK}\n"
        "82502089 图 7：出生最高、随日龄下降、LOS 后 48h 再降。"
        "这句先按发生残留与出生窗翻转写。不得写成保护性 MDSC 在 LOS 里衰竭。"
    ),
    "2.2": (
        f"{MARK}\n"
        "胃液联合基金的 0–72 小时窗是本题的前哨对象，不是日龄轴，也不是循环血饼。"
    ),
    "3.3": (
        f"{MARK}\n"
        "黄国青是成纤维为什么与髓系同向的机制假说。人角仍是 Egozi 方向。"
        "AhR-Ptgs2 因果只在鼠。见 3.7。不得用 8.7 上皮铁死亡证明成纤维 AhR。"
    ),
    "4.1": (
        f"{MARK}\n"
        "精细分型队列不得把 EOS、LOS、NEC 聚成一个重症感染内型。"
        "胃液课题只进早发前哨，不进晚发未分选血。82502089 的鼠脾/肠不得与人 bulk 画一张败血症图。"
    ),
    "4.2": (
        f"{MARK}\n"
        "胃液宿主转录不是本题的全血组成。S100A8/A9 在胃液出现必须另起舱室句。见 6.7。"
    ),
    "7.2": (
        f"{MARK}\n"
        "蒋 82402017 的 LTi 句只在新生鼠。人已发表句是抗生素–厌氧菌、早期抗生素–BPD/NEC、嗜酸/II 型。"
        "NeoVanc 仍是治疗日 bulk，不是 LTi。Chen Mucosal Immunol 2026 不关闭 LOS 未分选血。"
    ),
    "7.3": (
        f"{MARK}\n"
        "十五五母乳与张樱彦开题只与肠受体时间对齐。"
        "Huang NPJ 2026 已经是 186 人发育图谱；全球图谱 Idea 不得再发同一张图。"
        "禁止乳汁直接对比坏死肠。Hong MNFR 2022 是 I 期 NEC 试点，不是健康受体。"
    ),
    "8.0": (
        f"{MARK}\n"
        "第三引擎见 8.10。本队列动物伦理已批的是肠源性 LOS 与 S100 干预，不是把 109 行公开鼠集加总成人论文。"
    ),
    "8.4": (
        f"{MARK}\n"
        "能改管理的标志：粪 S100 / 丁酸、胃液核酸-蛋白联检、血 HLA-DR。"
        "切除回肠上的 AhR-Ptgs2 只生成假说。手术标本不能当筛查。"
    ),
    "8.7": (
        f"{MARK}\n"
        "本题保持上皮代谢正交。黄国青的成纤维 AhR 不进本题主图。HbF–氧化应激 Idea 也不并入。"
    ),
    "V3": (
        f"{MARK}\n"
        "胃液是前哨，粪是监测，切除肠是病灶，循环血是床旁。"
        "四个器官不得互相冒充。见 6.7。"
    ),
    "5.3": (
        f"{MARK}\n"
        "工作台 Idea「LOS相关脑损伤」与预警模型项目，公共人转录组仍支撑不住。"
        "CHNN 只写率。禁止用模型脑损伤写人类结局。"
    ),
    "8.8": (
        f"{MARK}\n"
        "82502089 的鼠 LOS 脾/肠单细胞只问模型里极能不能被拧或 S100 能不能被补。"
        "不问人的晚发窗口。不得与精细分型 CyTOF 画一张图。"
    ),
}


IMPL_ROW = {
    "课题": "本队列与标书",
    "对应大块": "Ⅴ 重症监护作为发育环境",
    "对应科学问题": "8.10；6.7；3.7；V4；2.4；4.1；7.2；7.3",
    "进入等级": "现在可进入发现",
    "库内研究数": 10,
    "纳入分析数": 6,
    "排序": 11,
    "1. 现在有什么数据": (
        "工作台 10 个项目。第三引擎已落地的人句：\n"
        "Huang NPJ 2026：186 人、1153 份粪，NICU 暴露重编程菌群-代谢-钙卫蛋白。\n"
        "Huang Front Immunol 2026：40 人、45 份血 CyTOF，NEC 位移进入 HLA-DR-low 单核态。\n"
        "Hong Gut Microbes 2024：UTI 前病原特异菌群。Hong CTG / Nutrients 2023：粪钙卫蛋白时钟。\n"
        "Chen Mucosal Immunol 2026：嗜酸/II 型与丁酸。胃液预试验 41 份三组学。\n"
        "82502089 图 7 CyTOF N=42；图 9 丁酸中介 N=719。黄标书图 1 与 NPJ 同一粪矩阵。\n"
        "Idea 表无读权限。对账只用链接文本。"
    ),
    "2. 数据规模": (
        "在研/投稿项目 9，未中 1。国青两支在研（82502089、82402017），NEC 国青与胃液联合基金在审。"
        "双结对 300+ 例；精细分型目标 250+100；胃液拟千人级 EOS 高危。"
        "这些数字是本队列规模，不得加进公共纳排。"
    ),
    "3. 能否联合分析": (
        "不能与公共单细胞合池，不能跨物种 joint UMAP，不能把粪/血/胃液/切除肠平均。\n"
        "EOS、LOS、NEC 必须分章。AhR 必须先选细胞与疾病。S100 必须按舱室分句。\n"
        "UTI 粪句不得关闭 LOS 感染前血。乳汁不得直接对比坏死肠。"
    ),
    "4. 下载状态": (
        "本行不靠 GEO。立刻动作是改名词与分句，不是再下一张公开集。\n"
        "公开层该下的仍走各块课题落实：NeoVanc、GeoMx、GSE297483。"
    ),
    "5. 个人还需补充": (
        "给 Idea 表读权限，或把 Idea 正文镜像进可读表。\n"
        "82502089 正文图题把 MDSC 换成 HLA-DR-low / S100 模块。\n"
        "双结对免疫臂与国青对齐时不要回写成 MDSC。"
    ),
    "立刻动作": (
        "写粪 S100 三结局分句；写血 HLA-DR-low 位移，不用 MDSC；"
        "AhR 分栏；胃液只当早发前哨；用 7.6 缺失图对照本队列逐日字段。"
    ),
}


PRINCIPLES = [
    {
        "原则": "标书细胞名词不得覆盖证明层已锁句子",
        "说明": (
            "国青、联合基金、院内项目的创新点名词（MDSC、重症感染内型、AhR 通路、LTi）"
            "不得写进证明层图题。本队列句子按对象重写：位移、模块差、舱室蛋白、前哨。"
            "工作台是第三引擎，不抬高公共发现条数。见 8.10。"
        ),
        "次序": 31,
    },
    {
        "原则": "同一分子跨舱室必须分句",
        "说明": (
            "S100A8/A9 与 AhR、丁酸、ILA/IAA 在粪、血、胃液、切除肠、鼠里可以同时存在，"
            "但必须按舱室、细胞和疾病分句。禁止平均成一条「通路参与早产儿疾病」。见 6.7、3.7。"
        ),
        "次序": 32,
    },
]


NEAR7 = {
    "次序": 7,
    "课题": "本队列与标书名词对账",
    "对应编号": "8.10；6.7；3.7",
    "数据广度": "中",
    "科学价值": "高",
    "完成难度": "低",
    "文献对标": "有方法学范例",
    "为何先做": (
        "82502089、黄国青、精细分型、胃液、双结对正在用证明层已经禁止的名词。"
        "先改句子，再跑下一张公共矩阵。"
    ),
    "主要限制": "Idea 表无读权限；标书图未进本工作区。",
    "对标文献": (
        "Huang 2026 NPJ Biofilms Microbiomes；Huang 2026 Front Immunol；"
        "Hong 2024 Gut Microbes；Chen 2026 Mucosal Immunol"
    ),
    "现在有什么数据": IMPL_ROW["1. 现在有什么数据"],
    "数据规模": IMPL_ROW["2. 数据规模"],
    "能否联合分析": IMPL_ROW["3. 能否联合分析"],
    "下载状态": "不靠新下载。对账用工作台与已发表论文。",
    "个人还需补充": IMPL_ROW["5. 个人还需补充"],
}


METH_ROW = {
    "方法": "禁止：用标书细胞名词作图题，或把同一分子跨舱室平均",
    "次序": 106,
    "slug": "tx-forbid-grant-noun",
    "步骤板块": "禁止事项",
    "状态": "禁止",
    "适用对象": ["全库"],
    "工具与版本": "不启用工具。写作与出图纪律。",
    "关键参数": "禁止名词：MDSC 作图题；重症感染内型混病；AhR 通路作疾病名。",
    "步骤骨架": (
        "出图前核三问：这张图的对象是粪、血、胃液还是切除肠？"
        "疾病是 NEC、EOS 还是 LOS？名词是位移/模块/蛋白，还是标书细胞类型？"
    ),
    "失败模式": "用 82502089 创新点直接当 6.1 图题；把胃液 S100 画进血饼。",
    "本库落点": "领域 8.10 / 6.7 / 3.7；原则 31 / 32。",
    "精读锚点": "证明层 V4、2.4、V3、4.1。",
    "更新日期": DATE,
}


CAT_APPEND = {
    "Ⅱ": (
        f"{MARK}\n"
        "工作台接口：黄国青只解释成纤维为何与髓系同向；人对照宇宙仍是外科对照。"
        "粪侧 ILA/IAA 与钙卫蛋白是本队列句，不是 Egozi 谱系句。"
    ),
    "Ⅲ": (
        f"{MARK}\n"
        "工作台接口：82502089 与精细分型必须分章。"
        "血句用 HLA-DR-low 位移。胃液只进早发前哨。UTI 粪句不关闭感染前血。"
    ),
    "Ⅴ": (
        f"{MARK}\n"
        "工作台接口：第三引擎见 8.10。"
        "本队列逐日字段是 7.6 缺失指控的正面对照。母乳只与肠受体对齐。"
    ),
}


def upsert_by_key(
    s: requests.Session,
    table: str,
    rows: list[dict],
    key: str,
    payloads: list[dict],
) -> dict[str, str]:
    have = {field_text(r.get("fields", {}).get(key)): r["record_id"] for r in rows}
    created_ids: dict[str, str] = {}
    to_create = []
    for rec in payloads:
        name = rec[key]
        if name in have and have[name]:
            batch_update(s, table, [{"record_id": have[name], "fields": rec}])
            created_ids[name] = have[name]
            print(f"updated {table} {key}={name} {have[name]}")
        else:
            to_create.append({"fields": rec})
    if to_create:
        for rec in batch_create(s, table, to_create):
            name = field_text(rec.get("fields", {}).get(key))
            created_ids[name] = rec["record_id"]
            print(f"created {table} {key}={name} {rec['record_id']}")
    return created_ids


def main() -> None:
    s = session()
    log: dict = {"date": DATE, "created": {}, "updated": {}}

    domain_rows = list_all(s, T_DOMAIN)
    have = {field_text(r.get("fields", {}).get("主题编号")): r for r in domain_rows}

    new_ids = upsert_by_key(s, T_DOMAIN, domain_rows, "主题编号", NEW_DOMAIN)
    log["created"].update(new_ids)

    # re-list so appends see new rows if needed
    domain_rows = list_all(s, T_DOMAIN)
    have = {field_text(r.get("fields", {}).get("主题编号")): r for r in domain_rows}

    domain_patch = []
    for key, note in NOTE.items():
        rec = have.get(key)
        if not rec:
            print("WARN missing domain", key)
            continue
        fields = rec.get("fields") or {}
        new_fake = append_note(fields.get("假证明"), note)
        new_design = append_note(fields.get("分析设计"), note)
        if new_fake == field_text(fields.get("假证明")) and new_design == field_text(
            fields.get("分析设计")
        ):
            print("skip already patched", key)
            continue
        domain_patch.append(
            {
                "record_id": rec["record_id"],
                "fields": {"假证明": new_fake, "分析设计": new_design},
            }
        )
    if domain_patch:
        batch_update(s, T_DOMAIN, domain_patch)
        log["updated"]["domain_notes"] = [x["record_id"] for x in domain_patch]
        print("updated domain notes", len(domain_patch))

    impl_rows = list_all(s, T_IMPL)
    log["impl"] = upsert_by_key(s, T_IMPL, impl_rows, "课题", [IMPL_ROW])

    prin_rows = list_all(s, T_PRIN)
    log["prin"] = upsert_by_key(s, T_PRIN, prin_rows, "原则", PRINCIPLES)

    near_rows = list_all(s, T_NEAR)
    log["near"] = upsert_by_key(s, T_NEAR, near_rows, "课题", [NEAR7])

    meth_rows = list_all(s, T_METH)
    log["meth"] = upsert_by_key(s, T_METH, meth_rows, "slug", [METH_ROW])

    cat_rows = list_all(s, T_CAT)
    cat_patch = []
    for rec in cat_rows:
        num = field_text((rec.get("fields") or {}).get("大块编号"))
        note = CAT_APPEND.get(num)
        if not note:
            continue
        fields = rec.get("fields") or {}
        new_prog = append_note(fields.get("现行进展"), note)
        new_iface = append_note(fields.get("与其他块的接口"), note)
        if MARK in field_text(fields.get("现行进展")):
            print("skip cat", num)
            continue
        cat_patch.append(
            {
                "record_id": rec["record_id"],
                "fields": {"现行进展": new_prog, "与其他块的接口": new_iface},
            }
        )
    if cat_patch:
        batch_update(s, T_CAT, cat_patch)
        log["updated"]["catalog"] = [x["record_id"] for x in cat_patch]
        print("updated catalog", len(cat_patch))

    out = ROOT / ".feishu/exports/tx/20260909_workbench_proof.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2))
    print("log", out)
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
