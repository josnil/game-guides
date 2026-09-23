# -*- coding: utf-8 -*-
"""map_overrides.yml 解析与应用的回归测试

用法： python tools/test-overrides.py     （或 npm run test）

覆盖：正常解析 / 容错写法 / 空文件 / 十种错误输入必须带行号报错 /
      端到端（临时覆盖 -> 生成 -> 断言产物 -> 还原 -> 断言回到初始值）/
      控制台数据文件的一致性

跑完会自动还原 _data/map_overrides.yml 并重新生成，不留副作用。
"""
import importlib.util
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "tools", "build-maps.py")

spec = importlib.util.spec_from_file_location("buildmaps", SCRIPT)
bm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bm)

ok = 0
fail = 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {name}")
    else:
        fail += 1
        print(f"  ✗ {name}" + (f"  —— {detail}" if detail else ""))


TMP = os.path.join(REPO, "_tmp_override_test.yml")


def parse(text):
    with open(TMP, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return bm.load_overrides(TMP)


def expect_error(name, text, must_contain):
    try:
        parse(text)
        check(name, False, "本该报错却通过了")
    except ValueError as e:
        check(name, must_contain in str(e), f"报错信息里没有「{must_contain}」：{e}")


print("=== 1. 正常解析（三种段落）===")
r = parse(
    '# 注释行\n'
    '\n'
    '"42":\n'
    '  remove:\n'
    '    - "19,28"\n'
    '    - "12,34"\n'
    '  add:\n'
    '    - "5,5"\n'
    '  label:\n'
    '    "34,18": 商城入口\n'
    '    "5,5": 隐藏宝箱\n'
    '\n'
    '"27":\n'
    '  remove:\n'
    '    - "10,6"\n'
)
check("两张地图", set(r.keys()) == {"42", "27"}, str(r.keys()))
check("42 删两个", r["42"]["remove"] == [(19, 28), (12, 34)], str(r["42"]["remove"]))
check("42 加一个", r["42"]["add"] == [(5, 5)], str(r["42"]["add"]))
check("42 浮窗两个", len(r["42"]["label"]) == 2, str(r["42"]["label"]))
check("浮窗文字正确", r["42"]["label"][(34, 18)] == "商城入口", str(r["42"]["label"]))
check("27 没有 add/label", r["27"]["add"] == [] and r["27"]["label"] == {})

print("")
print("=== 2. 容错：中文逗号 / 无引号 / 单引号 / 更深缩进 ===")
r = parse('"42":\n    remove:\n        - 19，28\n        - \'7,8\'\n        - 1,2\n'
          '    label:\n        "3,4":  前后带空格  \n')
check("中文逗号被接受", (19, 28) in r["42"]["remove"], str(r["42"]["remove"]))
check("单引号被接受", (7, 8) in r["42"]["remove"], str(r["42"]["remove"]))
check("无引号被接受", (1, 2) in r["42"]["remove"], str(r["42"]["remove"]))
check("缩进 4/8 空格也能认", len(r["42"]["remove"]) == 3, str(r["42"]["remove"]))
check("浮窗文字两端空格被去掉", r["42"]["label"].get((3, 4)) == "前后带空格",
      repr(r["42"]["label"].get((3, 4))))

print("")
print("=== 3. 空文件 / 只有注释 ===")
check("空文件返回空字典", parse("") == {})
check("只有注释返回空字典", parse("# 什么都没有\n\n# 再来一行\n") == {})

print("")
print("=== 4. 错误输入必须报错并指出行号 ===")
expect_error("地图 id 少了冒号", '"42"\n  remove:\n    - "1,2"\n', "第 1 行")
expect_error("地图 id 不是数字", '"abc":\n  remove:\n    - "1,2"\n', "第 1 行")
expect_error("段名拼错", '"42":\n  del:\n    - "1,2"\n', "只支持 remove / add / label")
expect_error("坐标不是整数", '"42":\n  remove:\n    - "a,b"\n', "第 3 行")
expect_error("坐标只有一个数", '"42":\n  remove:\n    - "19"\n', "第 3 行")
expect_error("条目没写减号", '"42":\n  remove:\n    "19,28"\n', "要以 `-` 开头")
expect_error("没有地图 id", 'remove:\n  - "1,2"\n', "缺少所属的地图 id")
expect_error("浮窗写成列表", '"42":\n  label:\n    - "3,4"\n', "浮窗要写成")
expect_error("浮窗没写文字", '"42":\n  label:\n    "3,4":\n', "没有浮窗文字")
expect_error("浮窗坐标不是整数", '"42":\n  label:\n    "a,b": 文字\n', "第 3 行")

print("")
print("=== 5. 端到端：覆盖真的会改变产物 ===")
OVR = os.path.join(REPO, "_data", "map_overrides.yml")
EV = os.path.join(REPO, "_data", "map_events.json")
CD = os.path.join(REPO, "tools", "map-console-data.js")
backup = open(OVR, "r", encoding="utf-8").read()
before = json.load(open(EV, "r", encoding="utf-8"))
n42_before = len(before["42"])
t0 = before["42"][0]
tile = f'{t0["tx"]},{t0["ty"]}'
new_tile = "1,1"


def run_gen():
    old = sys.argv
    sys.argv = ["build-maps.py"]
    try:
        return bm.main()
    finally:
        sys.argv = old


try:
    with open(OVR, "w", encoding="utf-8", newline="\n") as f:
        f.write(f'"42":\n  remove:\n    - "{tile}"\n  add:\n    - "{new_tile}"\n'
                f'  label:\n    "{new_tile}": 我加的测试点\n')
    check("生成器退出码为 0", run_gen() == 0)

    after = json.load(open(EV, "r", encoding="utf-8"))
    check(f"42 号图打点数不变（删1加1）：{n42_before} → {len(after['42'])}",
          len(after["42"]) == n42_before)
    tiles_after = {(m["tx"], m["ty"]) for m in after["42"]}
    check(f"被删的 {tile} 已不在结果里", tuple(int(x) for x in tile.split(",")) not in tiles_after)
    check(f"新增的 {new_tile} 在结果里", (1, 1) in tiles_after)

    lbl = [m for m in after["42"] if m.get("label")]
    check("浮窗文字写进了产物", len(lbl) == 1 and lbl[0]["label"] == "我加的测试点",
          str(lbl))

    print("")
    print("=== 6. 控制台数据文件 ===")
    check("map-console-data.js 已生成", os.path.exists(CD))
    txt = open(CD, "r", encoding="utf-8").read()
    check("以 window.WB_MAP_DATA 开头赋值", "window.WB_MAP_DATA = {" in txt)
    payload = txt.split("window.WB_MAP_DATA = ", 1)[1].rstrip().rstrip(";")
    data = json.loads(payload)
    check("含 19 张地图", len(data["maps"]) == 19, str(len(data["maps"])))
    check("含每图原始打点 original", all("original" in m for m in data["maps"].values()))
    orig = {tuple(p) for p in data["maps"]["42"]["original"]}
    check("original 仍保留被删的那个点（证明它是覆盖前的数据）",
          tuple(int(x) for x in tile.split(",")) in orig,
          f"原文件是空的，42 号图游戏原始应有 {n42_before} 个点")
    check("original 不含新增的点", (1, 1) not in orig)
    check(f"original 数量 = 游戏原始值 {n42_before}", len(orig) == n42_before,
          f"{len(orig)} vs {n42_before}")
    check("含 overrides 回显", data["maps"]["42"]["overrides"]["label"].get("1,1") == "我加的测试点")
    check("events 与 maps 一致", len(data["events"]["42"]) == len(after["42"]))

    print("")
    print("=== 7. 卫生检查 ===")
    bad = 0
    for mid, ms in after.items():
        for m in ms:
            if not (0 < m["x"] < 100 and 0 < m["y"] < 100):
                bad += 1
    check("打点百分比都在 (0,100)", bad == 0, f"{bad} 个越界")
finally:
    with open(OVR, "w", encoding="utf-8", newline="\n") as f:
        f.write(backup)
    run_gen()
    if os.path.exists(TMP):
        os.remove(TMP)
    now = json.load(open(EV, "r", encoding="utf-8"))
    check("还原后 42 号图打点数回到初始值", len(now["42"]) == n42_before,
          f'{len(now["42"])} vs {n42_before}')
    check("还原后没有残留浮窗",
          not any(m.get("label") for m in now["42"]),
          str([m for m in now["42"] if m.get("label")]))

print("")
print(f"结果：{ok} 通过，{fail} 失败")
sys.exit(0 if fail == 0 else 1)
