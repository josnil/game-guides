#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从《暗渊崛起》的游戏数据生成四大类结构化数据：装备 / 技能 / 状态 / 宠物。

 ---------------------------------------------------------------------------
 用法：
   python tools/build-gamedata.py                # 用默认游戏路径
   python tools/build-gamedata.py --game "D:/其他/暗渊崛起"
   python tools/build-gamedata.py --no-icons      # 跳过图标解密

 依赖：Pillow（图标压缩）。没装也能跑，只是图标会直接复制解密后的原图。
       pip install Pillow

 读取（严格对应游戏目录结构）：
   data/Weapons.json / Armors.json / Skills.json / States.json / Actors.json
   data/Enemies.json          → 掉落来源
   data/Items.json            → 宠物进化道具
   data/Classes.json          → 宠物职业、职业限制
   data/System.json           → 类型名、加密密钥
   img/system/IconSet.png_    → 图标（RPGMV 格式加密，用密钥解密）
   js/plugins.js              → 套装定义、宠物配置（注意 parameters 是字典）

 写入：
   _data/gamedata/equipment.json   武器 / 防具 / 套装 / 万能散搭装
   _data/gamedata/skills.json
   _data/gamedata/states.json
   _data/gamedata/pets.json
   _data/gamedata/meta.json        类型表、统计、生成时间
   assets/gamedata/iconset.png     解密并压缩后的图标雪碧图
 ---------------------------------------------------------------------------
"""

import argparse
import json
import math
import os
import re
import sys

DEFAULT_GAME = r"D:\steam\steamapps\common\暗渊崛起"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 八维基础属性（RPG Maker 顺序）
PARAM_KEYS = ["mhp", "mmp", "atk", "def", "mat", "mdf", "agi", "luk"]
PARAM_CN = ["最大HP", "最大MP", "攻击", "防御", "魔法攻击", "魔法防御", "敏捷", "幸运"]

# 附加属性。顺序与 RPG Maker / VisuMZ 的索引一致，不能改顺序。
XPARAM_CN = ["命中率", "闪避率", "暴击率", "暴击回避", "魔法回避",
             "魔法反射", "反击率", "HP再生", "MP再生", "TP再生"]
SPARAM_CN = ["被狙率", "防御率", "恢复率", "药物效果", "魔法消耗率",
             "TP消耗率", "物理伤害率", "魔法伤害率", "地形伤害率", "经验获得率"]

# 属性浮动与强化（读自 BZ_RandomEnhanceEquipment 的实际配置，下面会被真实值覆盖）
FLOAT_PCT = 20.0
ENHANCE_PCT = 20.0
ENHANCE_MAX = 2

ICON_CELL = 32
ICON_COLS = 16


def log(msg=""):
    print(msg, flush=True)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def is_separator(name):
    """数据库里的分类分隔项，如「-----上衣-重甲」"""
    return bool(name) and name.startswith("-----")


def keep_entry(item, include_unnamed=False):
    """这条数据要不要收录。

    - 分类分隔条目（----- 开头）永远排除；
    - 名字为空的占位条目：RPG Maker 的数据库会预留大量空位，
      它们没有任何内容，收进来只会污染表格 —— 默认排除；
    - 加 --include-unnamed 可改为收录（技能里有 154 条无名但有公式的内部技能，
      想看全量时可以打开）。
    """
    nm = (item.get("name") or "").strip()
    if is_separator(nm):
        return False
    if not nm:
        return include_unnamed
    return True


def note_tags(note):
    """单行形式 <Tag: value> 与 <Tag> -> {tag: [values]}"""
    out = {}
    for m in re.finditer(r"<([^<>\n:]+?)\s*:\s*([^<>\n]*)>", note or ""):
        out.setdefault(m.group(1).strip(), []).append(m.group(2).strip())
    for m in re.finditer(r"<([^<>\n:]+?)>", note or ""):
        out.setdefault(m.group(1).strip(), [])
    return out


def note_blocks(note, tag):
    """多行块形式 <Tag> ... </Tag>"""
    out = []
    for m in re.finditer(r"<%s>([\s\S]*?)</%s>" % (re.escape(tag), re.escape(tag)), note or ""):
        out.append(m.group(1).strip())
    return out


def note_get(note, tag, default=None):
    """取第一个单行标签值"""
    m = re.search(r"<%s\s*:\s*([^<>\n]*)>" % re.escape(tag), note or "")
    return m.group(1).strip() if m else default


def note_has(note, tag):
    return re.search(r"<%s\s*[:>]" % re.escape(tag), note or "") is not None


def parse_id_list(s):
    return [int(x) for x in re.split(r"[|,，\s]+", s or "") if x.strip().isdigit()]


def clean_text(s):
    """去掉 RPG Maker 文本里的控制码。

    游戏描述里混着这类东西：
        \\C[20]所有伤害变为暗属性      ← 切换文字颜色
        \\c[18]自动继承宠物的专属技能
        前摇\\|后摇                   ← 停顿标记
    直接输出会在页面上看到「\\C[20]」这种乱码，必须先清掉。
    """
    if not s:
        return ""
    s = re.sub(r"\\[Cc]\[\d+\]", "", s)          # 颜色
    s = re.sub(r"\\[VNPI]\[\d+\]", "", s)        # 变量 / 角色名 / 头像等占位
    s = re.sub(r"\\[|.!><^{}]", "", s)           # 停顿、等待、行首尾控制
    s = re.sub(r"\\\$", "", s)                   # 显示金钱窗口
    return s.strip()


def load_plugins(js_dir):
    """plugins.js 是 `var $plugins = [...]`；parameters 是字典（不是数组）"""
    txt = open(os.path.join(js_dir, "plugins.js"), "r", encoding="utf-8").read()
    entries = json.loads(txt[txt.index("["):txt.rindex("]") + 1])
    return {e.get("name"): e for e in entries}


# ---------------------------------------------------------------------------
def decrypt_rpgmv(path, key_hex):
    """RPGMV 加密图片：16 字节签名（原样） + 接着 16 字节与密钥异或 + 其余原始数据"""
    raw = open(path, "rb").read()
    if raw[:5] != b"RPGMV":
        return None
    body = bytearray(raw[16:])
    key = bytes.fromhex(key_hex)
    for i in range(16):
        body[i] ^= key[i]
    return bytes(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=os.environ.get("AYJQ_GAME", DEFAULT_GAME))
    ap.add_argument("--no-icons", action="store_true")
    ap.add_argument("--include-unnamed", action="store_true",
                    help="连名字为空的条目也收进来（默认排除）")
    args = ap.parse_args()

    game = args.game
    data_dir = os.path.join(game, "data")
    js_dir = os.path.join(game, "js")

    log("=" * 74)
    log("《暗渊崛起》游戏数据生成")
    log("=" * 74)
    log("游戏目录：" + game)
    if not os.path.isdir(data_dir):
        log("✗ 找不到 data 目录：" + data_dir)
        return 1

    global FLOAT_PCT, ENHANCE_PCT, ENHANCE_MAX

    # ---------- 0. 基础表 ----------
    system = read_json(os.path.join(data_dir, "System.json"))
    types = {
        "weaponTypes": system.get("weaponTypes") or [],
        "armorTypes": system.get("armorTypes") or [],
        "skillTypes": system.get("skillTypes") or [],
        "elements": system.get("elements") or [],
        "equipTypes": system.get("equipTypes") or [],
    }

    def tn(kind, idx):
        arr = types.get(kind) or []
        return arr[idx] if isinstance(idx, int) and 0 <= idx < len(arr) else ""

    weapons_raw = read_json(os.path.join(data_dir, "Weapons.json"))
    armors_raw = read_json(os.path.join(data_dir, "Armors.json"))
    skills_raw = read_json(os.path.join(data_dir, "Skills.json"))
    states_raw = read_json(os.path.join(data_dir, "States.json"))
    actors_raw = read_json(os.path.join(data_dir, "Actors.json"))
    classes_raw = read_json(os.path.join(data_dir, "Classes.json"))
    enemies_raw = read_json(os.path.join(data_dir, "Enemies.json"))
    items_raw = read_json(os.path.join(data_dir, "Items.json"))

    classes = {c["id"]: c for c in classes_raw if c}
    # 套装效果里会引用状态 ID，这里先建好索引（要在解析套装之前）
    states_by_id = {s["id"]: s for s in states_raw if s}
    log(f"基础表：武器 {len([x for x in weapons_raw if x])} / 防具 {len([x for x in armors_raw if x])} / "
        f"技能 {len([x for x in skills_raw if x])} / 状态 {len([x for x in states_raw if x])} / "
        f"角色 {len([x for x in actors_raw if x])} / 敌人 {len([x for x in enemies_raw if x])}")

    # ---------- 1. 插件配置（真实取值）----------
    plugins = load_plugins(js_dir)
    par = (plugins.get("BZ_RandomEnhanceEquipment") or {}).get("parameters") or {}
    if par:
        try:
            FLOAT_PCT = float(par.get("statFloatPercentage") or FLOAT_PCT)
            ENHANCE_PCT = float(par.get("enhancePercentage") or ENHANCE_PCT)
            e2 = float(par.get("enhance2Probability") or 0)
            e1 = float(par.get("enhance1Probability") or 0)
            ENHANCE_MAX = 2 if e2 > 0 else (1 if e1 > 0 else 0)
            log(f"强化配置：属性浮动 ±{FLOAT_PCT:g}%  强化 +{ENHANCE_PCT:g}%/次  最多 {ENHANCE_MAX} 次")
        except (TypeError, ValueError):
            pass

    enhance_mult = (1 + ENHANCE_PCT / 100.0) ** ENHANCE_MAX
    log(f"⇒ 属性区间：下界 = 基础×{1 - FLOAT_PCT / 100:.2f}，"
        f"上界 = 基础×{1 + FLOAT_PCT / 100:.2f}×{enhance_mult:.2f} = 基础×{(1 + FLOAT_PCT / 100) * enhance_mult:.3f}")

    # ---------- 2. 掉落来源反查 ----------
    drop_index = {}
    for e in enemies_raw:
        if not e:
            continue
        for d in e.get("dropItems") or []:
            kind = d.get("kind")  # 1=item 2=weapon 3=armor
            iid = d.get("dataId")
            if not kind or not iid:
                continue
            den = float(d.get("denominator") or 0)
            key = ("weapon" if kind == 2 else "armor" if kind == 3 else "item", iid)
            drop_index.setdefault(key, []).append({
                "enemyId": e["id"],
                "enemy": e["name"],
                # RPG Maker 的 denominator 是「1/N」里的 N，不是百分比本身。
                # 早期版本直接当百分比输出，6 会变成 6%（实际是 1/6 ≈ 16.7%）。
                "rate": round(100.0 / den, 2) if den else None,
            })
    log(f"掉落反查：{len(drop_index)} 种物品有敌人掉落记录")

    # ---------- 3. 套装定义 ----------
    set_defs = []
    raw_sets = (plugins.get("VisuMZ_2_EquipSetBonuses") or {}).get("parameters", {}).get("EquipSets:arraystruct")
    if raw_sets:
        try:
            for s in json.loads(raw_sets):
                set_defs.append(json.loads(s))
        except Exception as ex:
            log(f"⚠ 套装定义解析失败：{ex}")
    log(f"套装定义：{len(set_defs)} 套")

    def parse_piece(struct_str):
        """把 VisuMZ 的 PieceN 结构转成可读加成"""
        if not struct_str:
            return None
        try:
            o = json.loads(struct_str)
        except Exception:
            return None
        if not o:
            return None
        out = {"text": None, "params": {}, "xparams": {}, "sparams": {},
               "states": [], "skills": [], "other": {}}
        t = o.get("Text:str")
        if t and t != "auto":
            out["text"] = t
        ps = o.get("PassiveStates:arraynum")
        if ps:
            try:
                for sid in json.loads(ps):
                    sid = int(sid)
                    st = states_by_id.get(sid)
                    out["states"].append({
                        "id": sid,
                        "name": (st or {}).get("name") or ("状态 #%d" % sid),
                        "iconIndex": (st or {}).get("iconIndex", 0),
                    })
            except Exception:
                pass
        # 八维属性
        pm = o.get("Param:struct")
        if pm:
            try:
                p = json.loads(pm)
            except Exception:
                p = {}
            for i, cn in enumerate(PARAM_CN):
                plus = p.get("Plus%d:num" % i)
                rate = p.get("Rate%d:num" % i)
                try:
                    pv = float(str(plus).replace("+", "") or 0)
                except ValueError:
                    pv = 0
                try:
                    rv = float(rate or 1)
                except ValueError:
                    rv = 1
                if pv or rv != 1:
                    out["params"][PARAM_KEYS[i]] = {"plus": pv, "rate": rv, "cn": PARAM_CN[i]}
        # XParam / SParam：结构是 {KEY: 说明, RateN:num, PlusN:num} 成对出现
        for skey, table, dst in (("XParam:struct", XPARAM_CN, out["xparams"]),
                                 ("SParam:struct", SPARAM_CN, out["sparams"])):
            sv = o.get(skey)
            if not sv:
                continue
            try:
                sp = json.loads(sv)
            except Exception:
                continue
            for i, cn in enumerate(table):
                plus = sp.get("Plus%d:num" % i)
                rate = sp.get("Rate%d:num" % i)
                try:
                    pv = float(str(plus).replace("+", "") or 0)
                except ValueError:
                    pv = 0
                try:
                    rv = float(rate or 1)
                except ValueError:
                    rv = 1
                if pv or rv != 1:
                    dst[str(i)] = {"plus": pv, "rate": rv, "cn": cn}
        # 其它非空字段（技能等）原样留着，页面如实呈现
        for k, v in o.items():
            if k in ("Text:str", "ShowText:eval", "Bonuses", "PassiveStates:arraynum",
                     "Param:struct", "XParam:struct", "SParam:struct"):
                continue
            if v and v not in ("[]", "{}", "''"):
                out["other"][k] = v
        if not (out["params"] or out["xparams"] or out["sparams"] or out["states"] or out["other"]):
            return None

        # 预先拼好可读文本。浮点格式化在 Liquid 里很别扭（附加属性的加成是 0.1 这种小数），
        # 放在 Python 这边算完，页面只负责展示。
        def fmt(v, fraction):
            """fraction=True 表示加成是比例（0.1 → +10%）"""
            s = v["cn"]
            if v["plus"]:
                if fraction:
                    s += " +%g%%" % (v["plus"] * 100)
                else:
                    s += " +%g" % v["plus"]
            if v["rate"] != 1:
                s += " ×%g" % v["rate"]
            return s

        labels = []
        for v in out["params"].values():
            labels.append(fmt(v, False))
        for v in out["xparams"].values():
            labels.append(fmt(v, True))
        for v in out["sparams"].values():
            labels.append(fmt(v, True))
        for st in out["states"]:
            labels.append("状态：" + st["name"])
        for k in out["other"]:
            # 键名形如 "AddSkill:struct"，去掉类型后缀再展示
            labels.append(re.sub(r":\w+$", "", k))
        out["labels"] = labels
        return out

    sets = []
    for sd in set_defs:
        name = sd.get("SetName:str")
        if not name:
            continue
        pieces = []
        for i in range(1, 21):
            pc = parse_piece(sd.get("Piece%d:struct" % i))
            if pc:
                pieces.append({"count": i, **pc})
        sets.append({
            "name": name,
            "iconIndex": int(sd.get("Icon:num") or 0),
            "pieces": pieces,
            "members": [],
        })
    set_by_name = {s["name"]: s for s in sets}

    # ---------- 4. 装备 ----------
    def build_equip(item, kind):
        if not item or not keep_entry(item, args.include_unnamed):
            return None
        note = item.get("note") or ""
        params = item.get("params") or [0] * 8
        rng = {}
        for i, k in enumerate(PARAM_KEYS):
            base = params[i] if i < len(params) else 0
            if base == 0:
                continue
            # 装备属性有两重浮动：
            #   1) 掉落时八维在 ±statFloatPercentage% 内随机（这一档只往下走，也可能往上）
            #   2) 强化每次 +enhancePercentage%，最多 ENHANCE_MAX 次
            # 取两个候选值的 min / max 作为「下界 / 上界」——
            # 注意负属性（如敏捷 -8）不能直接拿 base×0.8 当下界，那样会算反。
            a = base * (1 - FLOAT_PCT / 100.0)
            b = base * (1 + FLOAT_PCT / 100.0) * enhance_mult
            lo, hi = math.floor(min(a, b)), math.ceil(max(a, b))
            rng[k] = {"base": base, "low": lo, "high": hi, "cn": PARAM_CN[i]}

        out = {
            "id": item["id"],
            "kind": kind,
            "name": item["name"],
            "iconIndex": item.get("iconIndex", 0),
            "desc": clean_text(item.get("description")),
            "price": item.get("price", 0),
            "range": rng,
            "dropFrom": drop_index.get((kind, item["id"]), []),
            "set": note_get(note, "Equip Set"),
            "wildcard": note_has(note, "Equip Set Wildcard"),
            "wildcardSets": note_get(note, "Equip Set Wildcards"),
            "twoHanded": note_has(note, "双手持"),
            "reqRaw": (note_blocks(note, "Equip Requirements") or [None])[0],
            "classOnly": note_get(note, "Equip For Classes Only"),
            "traits": item.get("traits") or [],
        }
        if kind == "weapon":
            out["wtypeId"] = item.get("wtypeId", 0)
            out["wtype"] = tn("weaponTypes", item.get("wtypeId", 0))
        else:
            out["atypeId"] = item.get("atypeId", 0)
            out["atype"] = tn("armorTypes", item.get("atypeId", 0))
            out["etypeId"] = item.get("etypeId", 0)
            out["etype"] = tn("equipTypes", item.get("etypeId", 0))
        # 打造配方
        ing = note_blocks(note, "Crafting Ingredients")
        out["craft"] = ing[0] if ing else None
        return out

    weapons = [w for w in (build_equip(i, "weapon") for i in weapons_raw) if w]
    armors = [a for a in (build_equip(i, "armor") for i in armors_raw) if a]
    log(f"装备：武器 {len(weapons)} 件，防具 {len(armors)} 件")

    # 套装成员
    for it in weapons + armors:
        if it["set"] and it["set"] in set_by_name:
            set_by_name[it["set"]]["members"].append({
                "id": it["id"], "kind": it["kind"], "name": it["name"], "iconIndex": it["iconIndex"],
            })
    matched = sum(len(s["members"]) for s in sets)
    log(f"套装：{len(sets)} 套，已挂上 {matched} 件装备")
    orphan = [s["name"] for s in sets if not s["members"]]
    if orphan:
        log(f"  ⚠ 没有装备归属于这些套装：{orphan}")

    # 反向核对：装备上写的套装名，是否都有定义。
    # 这是数据本身的不一致（游戏里改过名或删过套装），不是提取错误，
    # 但要报出来，免得以为是脚本漏了。
    used_names = set()
    for it in weapons + armors:
        if it["set"]:
            used_names.add(it["set"])
    undefined = sorted(used_names - set(set_by_name.keys()))
    if undefined:
        log(f"  ⚠ 有装备引用了未定义的套装名（游戏数据本身如此）：{undefined}")
    # 只被分隔条目引用的套装（分隔条目不作为装备收录）
    sep_only = []
    for s in sets:
        if s["members"]:
            continue
        owners = []
        for raw, kind in ((weapons_raw, "weapon"), (armors_raw, "armor")):
            for i in raw:
                if not i or not is_separator(i.get("name")):
                    continue
                if note_get(i.get("note") or "", "Equip Set") == s["name"]:
                    owners.append(i["name"])
        if owners:
            sep_only.append((s["name"], owners))
    for nm, owners in sep_only:
        log(f"  · 「{nm}」的引用者只有分隔条目 {owners}，因此没有实际成员")

    wildcard = [it for it in weapons + armors if it["wildcard"]]
    log(f"万能散搭装（<Equip Set Wildcard>）：{len(wildcard)} 件")

    # ---------- 5. 技能 ----------
    skills = []
    for s in skills_raw:
        if not s or not keep_entry(s, args.include_unnamed):
            continue
        note = s.get("note") or ""
        dmg = s.get("damage") or {}
        w1 = s.get("requiredWtypeId1", 0)
        w2 = s.get("requiredWtypeId2", 0)
        wt = [tn("weaponTypes", x) for x in (w1, w2) if x]
        skills.append({
            "id": s["id"],
            "name": s["name"],
            "iconIndex": s.get("iconIndex", 0),
            "stypeId": s.get("stypeId", 0),
            "stype": tn("skillTypes", s.get("stypeId", 0)),
            # ⚠️ 技能的 description 字段**几乎都是空的**，真正的说明写在备注里：
            #      <Description: 一句话说明>
            #      <DamageInfo: 具体效果/数值，可多行>
            #    只读 description 会让所有技能浮窗都没有描述（我踩过）。
            "desc": clean_text(note_get(note, "Description", "") or s.get("description")),
            "detail": clean_text(note_get(note, "DamageInfo", "")),
            "mpCost": s.get("mpCost", 0),
            "tpCost": s.get("tpCost", 0),
            "formula": dmg.get("formula") or "",
            "damageType": dmg.get("type"),
            "variance": dmg.get("variance"),
            "critical": bool(dmg.get("critical")),
            "elementId": dmg.get("elementId", -1),
            "element": tn("elements", dmg.get("elementId", -1)) if dmg.get("elementId", -1) >= 0 else "",
            "repeats": s.get("repeats", 1),
            "scope": s.get("scope"),
            "occasion": s.get("occasion"),
            "weaponSkill": bool(w1 or w2),
            "weaponTypes": wt,
            "effects": s.get("effects") or [],
            "note": note,
        })
    log(f"技能：{len(skills)} 条（其中武器技能 {sum(1 for x in skills if x['weaponSkill'])} 条）")

    # ---------- 6. 状态 ----------
    states = []
    for s in states_raw:
        if not s or not keep_entry(s, args.include_unnamed):
            continue
        note = s.get("note") or ""
        desc = s.get("description")
        if not desc:
            desc = clean_text(note_get(note, "Description", ""))
        states.append({
            "id": s["id"],
            "name": s["name"],
            "iconIndex": s.get("iconIndex", 0),
            "desc": desc or "",
            "note": note,
        })
    log(f"状态：{len(states)} 条")

    # ---------- 7. 宠物 ----------
    skills_by_id = {x["id"]: x for x in skills}

    # 魔变装备：宠物备注里的 <DemonicArmor: 464,454> / <DemonicWeapon: 259,260>
    # 存的是装备 id，这里解析成图标 + 名称 + 功能（游戏的 description 就是效果说明），
    # 页面上用浮窗展示。
    equip_by = {}
    for w in weapons:
        equip_by[("weapon", w["id"])] = w
    for a in armors:
        equip_by[("armor", a["id"])] = a

    def resolve_equips(kind, ids):
        out = []
        for i in ids:
            it = equip_by.get((kind, i))
            if not it:
                out.append({"id": i, "kind": kind, "missing": True,
                            "name": "装备 #%d" % i, "iconIndex": 0, "desc": "", "range": {},
                            "type": ""})
                continue
            out.append({
                "id": it["id"], "kind": kind, "name": it["name"],
                "iconIndex": it["iconIndex"], "desc": it["desc"], "range": it["range"],
                "type": it.get("wtype") or it.get("atype") or "",
                "twoHanded": bool(it.get("twoHanded")),
                "set": it.get("set"),
            })
        return out

    pet_params = (plugins.get("BZ_PetSystem") or {}).get("parameters") or {}
    pet_cfg = {}
    if pet_params.get("petData"):
        try:
            for s in json.loads(pet_params["petData"]):
                o = json.loads(s)
                pet_cfg[int(o["actorId"])] = o
        except Exception as ex:
            log(f"⚠ 宠物配置解析失败：{ex}")
    skill_groups = {}
    if pet_params.get("skillGroups"):
        try:
            for s in json.loads(pet_params["skillGroups"]):
                o = json.loads(s)
                skill_groups[o.get("groupName")] = o
        except Exception as ex:
            log(f"⚠ 技能组解析失败：{ex}")
    log(f"宠物配置：{len(pet_cfg)} 条，技能组 {len(skill_groups)} 组")

    def skill_detail(sid):
        """把技能 id 解析成浮窗要用的完整字段。

        ⚠️ 技能说明要读备注里的 <Description> / <DamageInfo>，不能读 description 字段
        （那字段几乎都是空的）。这里统一处理，免得某个调用点漏掉 ——
        魔变专属技能最初就是用一行 lambda 单独拼的，只带了名称和图标，
        结果浮窗里没有描述。
        """
        sk = skills_by_id.get(sid) or {}
        return {
            "skillId": sid,
            "name": sk.get("name") or ("技能 #%d" % sid),
            "iconIndex": sk.get("iconIndex", 0),
            "stype": sk.get("stype", ""),
            "desc": sk.get("desc", ""),
            "detail": sk.get("detail", ""),
            "formula": sk.get("formula", ""),
            "mpCost": sk.get("mpCost", 0),
            "tpCost": sk.get("tpCost", 0),
        }

    def skills_of(raw_list):
        out = []
        if not raw_list:
            return out
        try:
            for s in json.loads(raw_list):
                o = json.loads(s)
                sid = int(o.get("skillId") or 0)
                if sid > 0:
                    item = skill_detail(sid)
                    item["probability"] = int(o.get("probability") or 0)
                    out.append(item)
        except Exception:
            pass
        return out

    def group_names(raw_list):
        out = []
        if not raw_list:
            return out
        try:
            for s in json.loads(raw_list):
                n = json.loads(s).get("groupName")
                if n:
                    out.append(n)
        except Exception:
            pass
        return out

    # 进化：道具上的 <PetEvolve: from, to> + <RequireLevel: N>
    evolutions = []
    for it in items_raw:
        if not it:
            continue
        note = it.get("note") or ""
        m = re.search(r"<PetEvolve\s*[:：]\s*([\d|,，\s]+?)\s*,\s*(\d+)\s*>", note, re.I)
        if not m:
            continue
        evolutions.append({
            "itemId": it["id"],
            "itemName": it["name"],
            "itemIconIndex": it.get("iconIndex", 0),
            "fromIds": parse_id_list(m.group(1)),
            "toId": int(m.group(2)),
            "requireLevel": int(note_get(note, "RequireLevel", 0) or 0),
            "assistIds": parse_id_list(note_get(note, "PetUnionEvolve", "") or "")
            + parse_id_list(note_get(note, "PetJointEvolve", "") or ""),
            "itemDesc": it.get("description") or "",
        })
    log(f"进化道具：{len(evolutions)} 条")

    actors = {a["id"]: a for a in actors_raw if a}
    pets = []
    for a in actors_raw:
        if not a or not (a.get("note") or "").find("<MKPet>") >= 0:
            continue
        note = a["note"]
        cfg = pet_cfg.get(a["id"], {})
        cls = classes.get(a.get("classId"))
        growth = {}
        gm = note_get(note, "PetParamGrowth")
        if gm:
            for kv in gm.split(","):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    k = k.strip().lower()
                    if k in PARAM_KEYS:
                        try:
                            growth[k] = {"value": float(v.strip()), "cn": PARAM_CN[PARAM_KEYS.index(k)]}
                        except ValueError:
                            pass
        # 这一只的进化去向 / 来源
        to_evos = [e for e in evolutions if a["id"] in e["fromIds"]]
        from_evos = [e for e in evolutions if e["toId"] == a["id"]]
        pets.append({
            "id": a["id"],
            "name": a["name"],
            "profile": a.get("profile") or "",
            "classId": a.get("classId"),
            "className": (cls or {}).get("name"),
            "maxLevel": a.get("maxLevel"),
            "growth": growth,
            "demonicArmor": parse_id_list(note_get(note, "DemonicArmor", "") or ""),
            "demonicWeapon": parse_id_list(note_get(note, "DemonicWeapon", "") or ""),
            # 解析后的魔变装备（含图标与功能说明），供页面浮窗使用
            "demonicArmorItems": resolve_equips(
                "armor", parse_id_list(note_get(note, "DemonicArmor", "") or "")),
            "demonicWeaponItems": resolve_equips(
                "weapon", parse_id_list(note_get(note, "DemonicWeapon", "") or "")),
            "captureFrom": {
                "enemyId": int(cfg["enemyId"]) if cfg.get("enemyId") else None,
                "enemy": (enemies_raw[int(cfg["enemyId"])]["name"]
                          if cfg.get("enemyId") and int(cfg["enemyId"]) < len(enemies_raw)
                          and enemies_raw[int(cfg["enemyId"])] else None),
                "difficulty": int(cfg.get("captureDifficulty") or 0) if cfg.get("captureDifficulty") else None,
                # 头像用的就是「要捕获的那只怪」的立绘文件名（见 7.5 的说明）
                "enemyBattlerName": (lambda eid: (
                    (enemies_raw[eid - 1] or {}).get("battlerName")
                    if 0 < eid <= len(enemies_raw) and enemies_raw[eid - 1] else None)
                )(int(cfg["enemyId"]) if cfg.get("enemyId") else 0),
            },
            "mutationSkills": skills_of(cfg.get("mutationSkills")),
            "demonicSkills": skills_of(cfg.get("demonicSkills")),
            "demonicExclusiveSkillId": int(cfg.get("demonicExclusiveSkillId") or 0),
            # 专属技能也要走统一的解析（含描述与效果），别单独拼字段
            "demonicExclusiveSkill": (skill_detail(int(cfg.get("demonicExclusiveSkillId") or 0))
                                     if int(cfg.get("demonicExclusiveSkillId") or 0) > 0 else None),
            "skillGroups": group_names(cfg.get("skillGroups")),
            "mutationGroups": group_names(cfg.get("mutationGroups")),
            "demonicGroups": group_names(cfg.get("demonicGroups")),
            "evolvesTo": [{"toId": e["toId"], "item": e["itemName"], "itemId": e["itemId"],
                           "requireLevel": e["requireLevel"], "assistIds": e["assistIds"]} for e in to_evos],
            "evolvesFrom": [{"fromId": f, "item": e["itemName"], "itemId": e["itemId"],
                             "requireLevel": e["requireLevel"]} for e in from_evos for f in e["fromIds"]],
        })
    log(f"宠物：{len(pets)} 只（其中 {sum(1 for p in pets if p['evolvesTo'])} 只有进化去向）")

    # ---------- 7.5 宠物头像 ----------
    # **正确的图源在「同名敌人的备注」里**，而不是 Actor 上的图片字段：
    #     <SV Battler: $BigMonster7>   立绘文件名
    #     <SV Sheet: 3x4>              网格 3 列 × 4 行
    #     <SV Row: 3>                  用第几行（1 起）
    # 同一张图靠「行」区分不同怪：水晶史莱姆 / 史莱姆魔王 / 将军史莱姆 / 元素史莱姆王
    # 都出自 $BigMonster7，行号分别是 3/4/1/2 ⇒ (图, 行) 去重后 **104 种**，
    # 也就是每只宠物都有自己的立绘。
    #
    # 之前走过的三条弯路（都验证过、都不对）：
    #   Actor.characterName  行走图   只有 7 种 —— 猪家族 10 只全长一样（同一只眼球怪）
    #   Actor.faceName       人形立绘
    #   Actor.battlerName    我方战斗图 = 人类角色
    #   Enemy.battlerName    只是占位，107 只里约七成都是 Slime
    # ⇒ 教训：**别按字段名猜图源**。真正的立绘写在敌人备注的尖括号标签里。
    #
    # 回退链（尽量让每只都有图；都没有就不放，不猜也不放占位图）：
    #   1) 同名敌人 → <SV Battler> 裁帧
    #   2) 同名敌人 → <Sideview Battler>（VisuMZ 写法）→ img/sv_actors 裁帧
    #   3) 名字包含宠物名的敌人 → <SV Battler>
    #   4) 同名敌人的 battlerName → img/sv_enemies 整张图
    key_hex = system.get("encryptionKey")
    char_dir = os.path.join(game, "img", "characters")
    sv_actor_dir = os.path.join(game, "img", "sv_actors")
    sv_enemy_dir = os.path.join(game, "img", "sv_enemies")
    pet_img_dir = os.path.join(REPO, "assets", "gamedata", "pets")

    def en_norm(s):
        """敌人名里带【】和空格，比较前先归一化"""
        return re.sub(r"[【】\s]", "", s or "")

    en_by_name = {}
    for en in enemies_raw:
        if en:
            en_by_name.setdefault(en_norm(en.get("name")), []).append(en)

    def find_enemy(pet_name):
        """按「同名 → 名字包含」的顺序找敌人"""
        stem = en_norm(pet_name)
        exact = en_by_name.get(stem)
        if exact:
            return exact[0]
        for key, lst in en_by_name.items():
            if stem and stem in key:
                return lst[0]
        return None

    def frame_from_sheet(png, grid, row):
        """按 <SV Sheet: 3x4> / <SV Row: n> 裁一帧（取第 1 列 = 站立帧）"""
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(png)).convert("RGBA")
        try:
            gc, gr = [int(x) for x in str(grid or "3x4").lower().split("x")]
        except ValueError:
            gc, gr = 3, 4
        if gc < 1 or gr < 1 or im.size[0] // gc < 8 or im.size[1] // gr < 8:
            return im
        cw, ch = im.size[0] // gc, im.size[1] // gr
        # <SV Row> 可能是多值（例如「1,19,28,47,62」），只取第一个
        parts = [x for x in re.split(r"[,\s]+", str(row or "1").strip()) if x]
        try:
            ri = max(0, min(gr - 1, int(parts[0]) - 1)) if parts else 0
        except ValueError:
            ri = 0
        return im.crop((1 * cw, ri * ch, 2 * cw, (ri + 1) * ch))

    n_img = 0
    n_missing = 0
    src_names = set()
    fallback_used = {}
    if key_hex and os.path.isdir(char_dir) and not args.no_icons:
        try:
            from PIL import Image
            import io
            os.makedirs(pet_img_dir, exist_ok=True)
            for f in os.listdir(pet_img_dir):      # 清掉旧图，避免改名后残留
                if f.endswith(".png"):
                    os.remove(os.path.join(pet_img_dir, f))
            for p in pets:
                en = find_enemy(p["name"])
                note = (en or {}).get("note") or ""
                frame = None
                used = None
                # 1) 同名敌人的 <SV Battler>
                sb = note_get(note, "SV Battler", "")
                if sb:
                    src = os.path.join(char_dir, sb + ".png_")
                    if os.path.exists(src):
                        png = decrypt_rpgmv(src, key_hex)
                        if png and png[:8] == b"\x89PNG\r\n\x1a\n":
                            frame = frame_from_sheet(png, note_get(note, "SV Sheet", "3x4"),
                                                     note_get(note, "SV Row", "1"))
                            used = "sv-battler"
                            src_names.add(sb)
                # 2) VisuMZ 的 <Sideview Battler>（图在 sv_actors，9 列 × 6 行）
                if frame is None:
                    sv = note_get(note, "Sideview Battler", "")
                    if sv:
                        src = os.path.join(sv_actor_dir, sv + ".png_")
                        if os.path.exists(src):
                            png = decrypt_rpgmv(src, key_hex)
                            if png and png[:8] == b"\x89PNG\r\n\x1a\n":
                                frame = frame_from_sheet(png, "9x6", 2)
                                used = "sideview-battler"
                                src_names.add(sv)
                # 3) 换一个「名字包含本宠物」且带 <SV Battler> 的敌人
                if frame is None:
                    stem = en_norm(p["name"])
                    for key, lst in en_by_name.items():
                        if not stem or stem not in key:
                            continue
                        for alt in lst:
                            alt_note = alt.get("note") or ""
                            alt_sb = note_get(alt_note, "SV Battler", "")
                            if not alt_sb:
                                continue
                            src = os.path.join(char_dir, alt_sb + ".png_")
                            if os.path.exists(src):
                                png = decrypt_rpgmv(src, key_hex)
                                if png and png[:8] == b"\x89PNG\r\n\x1a\n":
                                    frame = frame_from_sheet(
                                        png, note_get(alt_note, "SV Sheet", "3x4"),
                                        note_get(alt_note, "SV Row", "1"))
                                    used = "sv-battler-alt"
                                    src_names.add(alt_sb)
                                    break
                        if frame is not None:
                            break
                # 4) 兜底：敌人的 battlerName → sv_enemies 整张图
                if frame is None:
                    bn = (en or {}).get("battlerName")
                    if bn:
                        src = os.path.join(sv_enemy_dir, bn + ".png_")
                        if os.path.exists(src):
                            png = decrypt_rpgmv(src, key_hex)
                            if png and png[:8] == b"\x89PNG\r\n\x1a\n":
                                frame = Image.open(io.BytesIO(png)).convert("RGBA")
                                used = "sv-enemy-fallback"
                                src_names.add(bn)
                if frame is None:
                    n_missing += 1
                    continue
                out = os.path.join(pet_img_dir, "%d.png" % p["id"])
                # ⚠️ 量化前**不能** convert("RGB")：会丢 alpha，
                #    透明背景变成不透明近白色，图标在浅色背景上"隐形"且不报错。
                frame.quantize(colors=256, method=Image.FASTOCTREE).save(
                    out, "PNG", optimize=True)
                p["sprite"] = "/assets/gamedata/pets/%d.png" % p["id"]
                p["artSource"] = used
                fallback_used[used] = fallback_used.get(used, 0) + 1
                n_img += 1
            total = sum(os.path.getsize(os.path.join(pet_img_dir, f))
                        for f in os.listdir(pet_img_dir)) if os.path.isdir(pet_img_dir) else 0
            log(f"宠物头像：{n_img} / {len(pets)} 只取到立绘（缺 {n_missing}）；"
                f"来源分布 {fallback_used}，共用 {len(src_names)} 张原图，"
                f"合计 {total / 1024:.0f}KB")
        except ImportError:
            log("宠物头像：没装 Pillow，跳过")

    # ---------- 7.6 进化链（按阶段合并，同阶段的不同形态是分支） ----------
    # 需求：由同一个初始魔物衍生出的多条链要合并成**一条**完整链；
    #       同一阶段出现的不同进化型作为该阶段的**分支**。
    #
    # 做法（比逐条走路径更贴合需求）：
    #   1) 把进化关系看成无向图，取连通分量 —— 一个分量就是「同源」的一组宠物
    #   2) 分量内「不作为任何宠物的进化目标」的宠物即根（初始魔物）
    #   3) 从根做 BFS，层号 = 到根的最短进化步数 ⇒ 层号就是「阶段」
    #   4) 每个形态记下自己的「来路」（进化道具、所需等级、联合进化所需宠物）
    #
    # 于是 16 →(兽符A) 17|22|23 →(兽符B) 18 会渲染成：
    #   阶段0: 16      阶段1: 17、22、23（三个分支）      阶段2: 18
    # 而不是三条各自重复一遍的线性链。
    pets_by_id = {p["id"]: p for p in pets}

    def detail_of(pid):
        p = pets_by_id.get(pid)
        if not p:
            return None
        return {
            "petId": pid,
            "name": p["name"],
            "className": p["className"],
            "sprite": p.get("sprite"),
            "profile": p["profile"],
            "growth": p["growth"],
            "demonicExclusiveSkill": p.get("demonicExclusiveSkill"),
            "demonicSkills": p["demonicSkills"],
            "mutationSkills": p["mutationSkills"],
            "demonicArmorItems": p.get("demonicArmorItems") or [],
            "demonicWeaponItems": p.get("demonicWeaponItems") or [],
        }

    # 只保留两端都能对上宠物的进化边
    pet_edges = []
    for e in evolutions:
        if e["toId"] not in pets_by_id:
            continue
        frm = [f for f in e["fromIds"] if f in pets_by_id]
        if not frm:
            continue
        pet_edges.append({
            "fromIds": frm, "toId": e["toId"],
            "itemId": e["itemId"], "itemName": e["itemName"],
            "itemIconIndex": e["itemIconIndex"], "requireLevel": e["requireLevel"],
            "assistNames": [pets_by_id[i]["name"] for i in e["assistIds"] if i in pets_by_id],
        })

    adj = {}
    for e in pet_edges:
        for f in e["fromIds"]:
            adj.setdefault(f, set()).add(e["toId"])
            adj.setdefault(e["toId"], set()).add(f)

    groups = []
    visited = set()
    for start in sorted(pets_by_id):
        if start in visited or start not in adj:
            continue
        comp, stack = set(), [start]
        while stack:
            n = stack.pop()
            if n in comp:
                continue
            comp.add(n)
            stack.extend(adj.get(n, ()) - comp)
        visited |= comp

        comp_edges = [e for e in pet_edges
                      if e["toId"] in comp and any(f in comp for f in e["fromIds"])]
        incoming = {e["toId"] for e in comp_edges}
        roots = sorted(n for n in comp if n not in incoming)
        if not roots:
            # 理论上不会有环，真遇到就退化为取最小 id，避免整组丢掉
            roots = [min(comp)]

        level = {r: 0 for r in roots}
        queue = list(roots)
        while queue:
            n = queue.pop(0)
            for m in sorted(adj.get(n, ())):
                if m not in level:
                    level[m] = level[n] + 1
                    queue.append(m)
        # 分量内若有 BFS 到不了的节点（数据异常），兜到最后一层，别丢
        for n in sorted(comp):
            if n not in level:
                level[n] = max(level.values(), default=0) + 1

        stages = []
        for L in range(max(level.values()) + 1):
            forms = []
            for n in sorted(k for k, v in level.items() if v == L):
                det = detail_of(n)
                if not det:
                    continue
                # 来路：所有「上一层 → 本形态」的道具（同名同等级的去重）
                via, seen_via = [], set()
                for e in comp_edges:
                    if e["toId"] != n:
                        continue
                    if L == 0 or not any(level.get(f) == L - 1 for f in e["fromIds"]):
                        continue
                    key = (e["itemName"], e["requireLevel"])
                    if key in seen_via:
                        continue
                    seen_via.add(key)
                    via.append({"itemId": e["itemId"], "itemName": e["itemName"],
                                "itemIconIndex": e["itemIconIndex"],
                                "requireLevel": e["requireLevel"],
                                "assistNames": e["assistNames"]})
                det["via"] = via
                forms.append(det)
            if forms:
                stages.append({"level": L, "forms": forms})

        groups.append({
            "rootId": roots[0],
            "rootName": pets_by_id[roots[0]]["name"],
            "size": len(comp),
            "depth": max(level.values()),
            "stages": stages,
        })

    in_chain = set()
    for g in groups:
        for st in g["stages"]:
            for f in st["forms"]:
                in_chain.add(f["petId"])
    standalone = [p["id"] for p in pets if p["id"] not in in_chain]
    # 深链、大组、有分支的排前面
    groups.sort(key=lambda g: (-g["depth"], -g["size"], g["rootName"]))
    branched = sum(1 for g in groups if any(len(s["forms"]) > 1 for s in g["stages"]))
    log(f"进化链：{len(groups)} 条（最深 {max((g['depth'] for g in groups), default=0)} 级，"
        f"共 {sum(g['size'] for g in groups)} 只；其中 {branched} 条含分支），"
        f"未参与进化的宠物 {len(standalone)} 只")

    # ---------- 8. 图标 ----------
    icon_meta = {"cell": ICON_CELL, "cols": ICON_COLS, "file": None, "count": 0}
    if not args.no_icons:
        src = os.path.join(game, "img", "system", "IconSet.png_")
        key_hex = system.get("encryptionKey")
        dst_dir = os.path.join(REPO, "assets", "gamedata")
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, "iconset.png")
        if os.path.exists(src) and key_hex:
            png = decrypt_rpgmv(src, key_hex)
            if png and png[:8] == b"\x89PNG\r\n\x1a\n":
                w = int.from_bytes(png[16:20], "big")
                h = int.from_bytes(png[20:24], "big")
                icon_meta.update({"cols": w // ICON_CELL, "rows": h // ICON_CELL,
                                  "count": (w // ICON_CELL) * (h // ICON_CELL),
                                  "file": "/assets/gamedata/iconset.png"})
                try:
                    from PIL import Image
                    import io
                    im = Image.open(io.BytesIO(png)).convert("RGBA")
                    # ⚠️ 这里**不能**先 convert("RGB")：
                    #    图标的背景是「透明白」(255,255,255,0)，convert("RGB") 会丢掉 alpha，
                    #    透明背景变成不透明的近白色 —— 图标于是在浅色纸面上彻底看不见，
                    #    而且**不会报任何错误**（我踩过：页面结构、图标元素、请求全都正常，
                    #    就是看不见）。FASTOCTREE 的调色板量化支持 alpha，体积反而更小。
                    im.quantize(colors=256, method=Image.FASTOCTREE).save(
                        dst, "PNG", optimize=True)

                    # 写完自查：抽一格确认背景仍是透明的。
                    # 这类「静默失效」必须靠断言拦，人眼在低分辨率截图上根本看不出来。
                    chk = Image.open(dst).convert("RGBA")
                    sample = chk.crop((192, 1088, 224, 1120))
                    px = list(sample.getdata())
                    transparent = sum(1 for q in px if q[3] == 0)
                    if transparent < 100:
                        log(f"  ✗ 图标雪碧图丢失透明度（该格只有 {transparent}/1024 个透明像素）"
                            f" —— 图标会在浅色背景上不可见，请检查量化方式")
                        return 1
                    log(f"图标：{w}x{h}，{icon_meta['count']} 个（{w // ICON_CELL} 列 × "
                        f"{h // ICON_CELL} 行）  解密 {len(png) / 1048576:.2f}MB → "
                        f"量化 {os.path.getsize(dst) / 1048576:.2f}MB（透明度已校验）")
                except ImportError:
                    open(dst, "wb").write(png)
                    log(f"图标：{w}x{h}（没装 Pillow，直接写原图 {len(png) / 1048576:.2f}MB）")
            else:
                log("⚠ 图标解密失败（PNG 头不对）")
        else:
            log("⚠ 找不到 IconSet.png_ 或 encryptionKey")
    else:
        log("图标：已跳过（--no-icons）")

    # ---------- 9. 输出 ----------
    meta = {
        "types": types,
        "paramKeys": PARAM_KEYS,
        "paramCn": PARAM_CN,
        "floatPct": FLOAT_PCT,
        "enhancePct": ENHANCE_PCT,
        "enhanceMax": ENHANCE_MAX,
        # 区间倍率直接算好写进数据，页面就不必在 Liquid 里做浮点运算
        "rangeFormula": {
            "lowMul": round(1 - FLOAT_PCT / 100.0, 3),
            "enhanceMul": round(enhance_mult, 3),
            "highMul": round((1 + FLOAT_PCT / 100.0) * enhance_mult, 3),
        },
        "icons": icon_meta,
        # 被排除的条目数（分隔项 + 空白占位 + 无名的内部技能）。
        # 页面会如实说明，免得读者以为数据不全。
        "excluded": {
            "weapons": len([x for x in weapons_raw if x]) - len(weapons),
            "armors": len([x for x in armors_raw if x]) - len(armors),
            "skills": len([x for x in skills_raw if x]) - len(skills),
            "states": len([x for x in states_raw if x]) - len(states),
        },
        "includeUnnamed": bool(args.include_unnamed),
        "counts": {
            "weapons": len(weapons), "armors": len(armors), "sets": len(sets),
            "wildcard": len(wildcard), "skills": len(skills),
            "states": len(states), "pets": len(pets), "evolutions": len(evolutions),
            "skillGroups": len(skill_groups),
        },
    }

    gd = os.path.join(REPO, "_data", "gamedata")
    write_json(os.path.join(gd, "equipment.json"),
               {"weapons": weapons, "armors": armors, "sets": sets, "wildcard": wildcard,
                # 装备引用了、但套装定义里没有的名字。页面直接读这个字段，
                # 不必在 Liquid 里做集合差集（那样又绕又容易算错）。
                "undefinedSets": undefined})
    write_json(os.path.join(gd, "skills.json"), skills)
    write_json(os.path.join(gd, "states.json"), states)
    write_json(os.path.join(gd, "pets.json"),
               {"pets": pets, "evolutions": evolutions, "skillGroups": skill_groups,
                "chainGroups": groups, "standalone": standalone})
    write_json(os.path.join(gd, "meta.json"), meta)

    log("")
    log("已写 _data/gamedata/：equipment / skills / states / pets / meta")
    for name in ("equipment", "skills", "states", "pets", "meta"):
        p = os.path.join(gd, name + ".json")
        log(f"    {name}.json  {os.path.getsize(p) / 1024:.0f}KB")
    log("")
    log("完成。接下来：npm run check && npm run publish")
    return 0


if __name__ == "__main__":
    sys.exit(main())
