#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从《暗渊崛起》的游戏数据生成世界地图与各地点页面。

 ---------------------------------------------------------------------------
 为什么是「本地生成 + 提交产物」，而不是构建时读取：
   GitHub Actions 的构建机读不到你 D 盘里的游戏目录。
   所以这个脚本在【你本机】跑一次，把图片和数据写进仓库，Jekyll 只负责渲染。
   游戏更新后再跑一次即可。

 用法：
   python tools/build-maps.py                 # 用默认游戏路径
   python tools/build-maps.py --game "D:/其他路径/暗渊崛起"
   python tools/build-maps.py --no-images      # 只更新数据，不处理图片

 依赖：
   Pillow（用于压缩图片）。没装也能跑，只是会直接复制原图，
   仓库会因此变大（原图合计约 88MB）。
       pip install Pillow

 读取（严格对应 data 文件夹结构）：
   <GAME>/data/MapInfos.json        地图树：id / name / parentId
   <GAME>/data/Map<3位id>.json      每张地图：width / height / events[]
   <GAME>/outputimg/Map_<id>_<名称>.png   每张地图的渲染图

 写入：
   _data/maps.json        世界地图信息 + 各地点（含按钮百分比坐标）
   _data/map_events.json  每张地图的事件位置（百分比坐标，供打点用）
   map/<id>.md            每个地点的页面
   assets/maps/*.png      压缩后的地图图片
---------------------------------------------------------------------------
"""

import argparse
import json
import os
import re
import shutil
import sys

DEFAULT_GAME = r"D:\steam\steamapps\common\暗渊崛起"
# 脚本位于 <repo>/tools/，所以仓库根是上一级
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TILE = 48          # RPG Maker MZ 的图块像素
WORLD_MAX_W = 1800  # 世界地图压缩后最大宽度
MAP_MAX_W = 1400    # 地点地图压缩后最大宽度


def log(msg=""):
    print(msg, flush=True)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def norm(s):
    """规范化地图名：去掉空白，便于容错匹配（例：'火之洞窟内部 2' vs '火之洞窟内部2'）"""
    return re.sub(r"\s+", "", s or "")


def tile_to_pct(tx, ty, width, height):
    """图块坐标 -> 百分比坐标（图块中心）"""
    return round((tx + 0.5) / width * 100, 4), round((ty + 0.5) / height * 100, 4)


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=os.environ.get("AYJQ_GAME", DEFAULT_GAME))
    ap.add_argument("--no-images", action="store_true", help="只更新数据，不处理图片")
    args = ap.parse_args()

    game = args.game
    data_dir = os.path.join(game, "data")
    img_dir = os.path.join(game, "outputimg")

    log("=" * 70)
    log("《暗渊崛起》地图数据生成")
    log("=" * 70)
    log("游戏目录：" + game)
    if not os.path.isdir(data_dir):
        log("✗ 找不到 data 目录：" + data_dir)
        return 1
    if not os.path.isdir(img_dir):
        log("✗ 找不到 outputimg 目录：" + img_dir)
        return 1

    # ---------- 1. 读地图树 ----------
    infos = read_json(os.path.join(data_dir, "MapInfos.json"))
    by_id = {}
    by_norm_name = {}
    for m in infos:
        if not m:
            continue
        by_id[m["id"]] = m
        by_norm_name.setdefault(norm(m["name"]), m["id"])
    log(f"地图树：{len(by_id)} 张地图")

    # ---------- 2. 定位世界大地图（按名字，不写死 id）----------
    world = None
    for m in by_id.values():
        if "世界大地图" in (m["name"] or ""):
            world = m
            break
    if world is None:
        log("✗ 地图树里找不到「世界大地图」")
        return 1
    wid = world["id"]
    log(f"世界大地图：id={wid} name={world['name']}")

    def map_path(mid):
        return os.path.join(data_dir, f"Map{mid:03d}.json")

    world_map = read_json(map_path(wid))
    WW, WH = world_map["width"], world_map["height"]
    log(f"世界大地图尺寸：{WW}x{WH} 格  →  {WW*TILE}x{WH*TILE} px")
    log(f"世界大地图事件：{len([e for e in world_map.get('events', []) if e])} 个")

    # ---------- 3. 从「场所移动（X）」事件里提取地点 ----------
    # 这是本方案的关键：世界地图上每个传送事件的位置就是该地点的按钮位置。
    spots = {}
    for e in world_map.get("events", []):
        if not e or not e.get("name"):
            continue
        m = re.match(r"^场所移动[（(](.+?)[）)]$", e["name"])
        if not m:
            continue
        spots.setdefault(m.group(1), []).append((e["x"], e["y"]))

    log(f"从世界地图提取到 {len(spots)} 个地点")

    # ---------- 4. 图片处理（可选）----------
    out_img_dir = os.path.join(REPO, "assets", "maps")
    have_pil = False
    if not args.no_images:
        try:
            from PIL import Image  # noqa: F401
            have_pil = True
        except ImportError:
            log("")
            log("⚠ 没装 Pillow，将直接复制原图（仓库会变大）。")
            log("  建议先执行： pip install Pillow")
        os.makedirs(out_img_dir, exist_ok=True)
        # 清掉旧图，避免改名后残留
        for f in os.listdir(out_img_dir):
            if f.endswith(".png"):
                os.remove(os.path.join(out_img_dir, f))

    def build_image(mid, name, max_w):
        """返回 (web相对路径, 宽, 高)；找不到源图返回 None"""
        src = os.path.join(img_dir, f"Map_{mid}_{name}.png")
        if not os.path.exists(src):
            # 名字里可能有全角/半角差异，扫一遍目录兜底
            prefix = f"Map_{mid}_"
            cand = [f for f in os.listdir(img_dir) if f.startswith(prefix) and f.endswith(".png")]
            if not cand:
                return None
            src = os.path.join(img_dir, cand[0])
        if args.no_images:
            return None

        rel = f"/assets/maps/{mid}.png"
        dst = os.path.join(out_img_dir, f"{mid}.png")
        if have_pil:
            from PIL import Image
            im = Image.open(src).convert("RGBA")
            w, h = im.size
            scale = min(1.0, max_w / w)
            if scale < 1.0:
                # 像素图必须 NEAREST，否则边缘会糊
                im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.NEAREST)
            w, h = im.size
            # 调色板量化：像素图颜色数有限，几乎无损但体积骤降
            im.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT,
                                       dither=Image.NONE).save(dst, "PNG", optimize=True)
        else:
            shutil.copyfile(src, dst)
            w = h = 0
        return (rel, w, h)

    # ---------- 5. 世界地图条目 ----------
    world_entry = {"title": world["name"], "id": wid, "url": "/map/"}
    if not args.no_images:
        r = build_image(wid, world["name"], WORLD_MAX_W)
        if r:
            world_entry["image"], world_entry["w"], world_entry["h"] = r[0], r[1], r[2]
            log(f"  世界地图图片：{r[0]}  {r[1]}x{r[2]}")

    # ---------- 6. 各地点 ----------
    places = []
    missing_img = []
    missing_map = []
    for name, pts in sorted(spots.items()):
        mid = by_norm_name.get(norm(name))
        avg_x = sum(p[0] for p in pts) / len(pts)
        avg_y = sum(p[1] for p in pts) / len(pts)
        px, py = tile_to_pct(avg_x, avg_y, WW, WH)

        entry = {
            "title": name,
            "mapId": mid,
            "exits": len(pts),
            "x": px,
            "y": py,
        }
        if mid is None:
            missing_map.append(name)
            entry["url"] = None
        else:
            entry["url"] = f"/map/{mid}/"

        if mid is not None and not args.no_images:
            r = build_image(mid, by_id[mid]["name"], MAP_MAX_W)
            if r:
                entry["image"], entry["w"], entry["h"] = r[0], r[1], r[2]
            else:
                missing_img.append(f"{name}(id={mid})")
        places.append(entry)

    log("")
    log(f"地点条目：{len(places)} 个（其中 {sum(1 for p in places if p['url'])} 个可跳转）")
    if missing_map:
        log("  ⚠ 地图树里找不到对应地图（不会生成可点击按钮）：")
        for n in missing_map:
            log(f"      {n}")
    if missing_img:
        log("  ⚠ outputimg 里找不到图片：")
        for n in missing_img:
            log(f"      {n}")

    # 按世界地图上的位置排序（先上后下、先左后右），侧边栏读起来更自然
    places.sort(key=lambda p: (round(p["y"] / 5), p["x"]))

    write_json(os.path.join(REPO, "_data", "maps.json"),
               {"world": world_entry, "places": places})
    log("  已写 _data/maps.json")

    # ---------- 7. 每张地图的事件位置 ----------
    events_by_map = {}
    for p in places:
        mid = p["mapId"]
        if mid is None:
            continue
        mp = read_json(map_path(mid))
        W, H = mp["width"], mp["height"]
        tiles = set()
        for e in mp.get("events", []):
            if e:
                tiles.add((e["x"], e["y"]))
        marks = []
        for tx, ty in sorted(tiles):
            x, y = tile_to_pct(tx, ty, W, H)
            marks.append({"x": x, "y": y})
        events_by_map[str(mid)] = marks

    write_json(os.path.join(REPO, "_data", "map_events.json"), events_by_map)
    total_marks = sum(len(v) for v in events_by_map.values())
    log(f"  已写 _data/map_events.json（{len(events_by_map)} 张图，共 {total_marks} 个事件位置）")

    # ---------- 8. 各地点页面 ----------
    map_dir = os.path.join(REPO, "map")
    os.makedirs(map_dir, exist_ok=True)
    for f in os.listdir(map_dir):
        if f.endswith(".md"):
            os.remove(os.path.join(map_dir, f))

    written = 0
    for p in places:
        mid = p["mapId"]
        if mid is None or "image" not in p:
            continue
        cnt = len(events_by_map.get(str(mid), []))
        body = f"""---
title: {p["title"]}
layout: default
permalink: /map/{mid}/
map_id: {mid}
map_title: {p["title"]}
map_src: {p["image"]}
map_w: {p["w"]}
map_h: {p["h"]}
map_events: {cnt}
map_exits: {p["exits"]}
---

# {p["title"]}

{{% include wb_map_view.html map_id="{(mid)}" src=p.map_src alt=p.map_title w=p.map_w h=p.map_h count=p.map_events exits=p.map_exits %}}

<p class="wb-map__back"><a href="{{{{ '/map/' | relative_url }}}}">← 返回世界大地图</a></p>
"""
        with open(os.path.join(map_dir, f"{mid}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        written += 1
    log(f"  已写 map/*.md（{written} 个地点页面）")

    # ---------- 9. 统计 ----------
    if not args.no_images:
        total = sum(os.path.getsize(os.path.join(out_img_dir, f))
                    for f in os.listdir(out_img_dir) if f.endswith(".png"))
        log("")
        log(f"图片输出：assets/maps/ 共 {len(os.listdir(out_img_dir))} 个文件，"
            f"{total/1048576:.2f} MB")

    log("")
    log("完成。接下来：")
    log("  npm run check           # 预检")
    log("  npm run publish -- -m \"更新地图数据\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
