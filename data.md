---
title: 游戏数据
layout: default
permalink: /data/
---

# 游戏数据
{% include gd_subnav.html active="" %}


{%- assign gd = site.data.gamedata.meta -%}
{%- assign c = gd.counts -%}
{%- assign rf = gd.rangeFormula -%}

本站数据全部从游戏本体提取，不是手工录入的。

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-数据分类">按分类或说明筛选</label>
    <input type="search" id="f-数据分类" data-gd-filter placeholder="输入分类名筛选，例如「技能」">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的条目。换个关键词试试。</p>

  <div class="gd-table-wrap">
<table class="gd-table">
  <thead>
    <tr><th scope="col">分类</th><th scope="col" class="gd-num">条目数</th><th scope="col">说明</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="{{ '/data/weapons/' | relative_url }}">武器</a></td>
      <td class="gd-num">{{ c.weapons }}</td>
      <td>{{ gd.types.weaponTypes | slice: 1, 9 | join: ' / ' }}，区分单手与双手</td>
    </tr>
    <tr>
      <td><a href="{{ '/data/armors/' | relative_url }}">防具</a></td>
      <td class="gd-num">{{ c.armors }}</td>
      <td>{{ gd.types.armorTypes | slice: 1, 10 | join: ' / ' }}</td>
    </tr>
    <tr>
      <td><a href="{{ '/data/sets/' | relative_url }}">套装</a></td>
      <td class="gd-num">{{ c.sets }}</td>
      <td>各套装的件数档位加成与所含装备</td>
    </tr>
    <tr>
      <td><a href="{{ '/data/wildcard/' | relative_url }}">万能散搭装</a></td>
      <td class="gd-num">{{ c.wildcard }}</td>
      <td>带「所有套装 +1」效果的散件</td>
    </tr>
    <tr>
      <td><a href="{{ '/data/skills/' | relative_url }}">技能</a></td>
      <td class="gd-num">{{ c.skills }}</td>
      <td>{{ gd.types.skillTypes | slice: 1, 5 | join: ' / ' }}，含伤害公式与武器需求</td>
    </tr>
    <tr>
      <td><a href="{{ '/data/states/' | relative_url }}">状态</a></td>
      <td class="gd-num">{{ c.states }}</td>
      <td>图标与效果说明</td>
    </tr>
    <tr>
      <td><a href="{{ '/data/pets/' | relative_url }}">宠物</a></td>
      <td class="gd-num">{{ c.pets }}</td>
      <td>进化链、进化等级与条件、专属技能与魔变技能</td>
    </tr>
  </tbody>
</table>
  </div>
</div>


## 装备属性为什么是一个区间

游戏里的装备属性**不是固定值**，浮动来自两处：

| 来源 | 幅度 | 说明 |
| --- | --- | --- |
| 掉落时的随机浮动 | ±{{ gd.floatPct }}% | 敌人掉落装备时，八维属性在原值上下随机 |
| 随机强化 | 每次 +{{ gd.enhancePct }}%，最多 {{ gd.enhanceMax }} 次 | 强化看运气，所以本站的上界按强化满计算 |

于是本站给出的区间是：

- **下界** = 基础值 × {{ rf.lowMul }}
- **上界** = 基础值 × {{ rf.highMul }}（= {{ gd.floatPct }}% 浮动 × 强化满 {{ rf.enhanceMul }}）

举例：某件武器基础攻击 25 → 区间 **20 ~ 44**。
当然，这里没有计算难度加成，难度加成请玩家自行计算（地狱属性*1.3）

{%- comment -%}
  倍率由生成脚本算好写进 meta.json，游戏改配置后页面数字自动跟着变。
{%- endcomment -%}

<details class="wb-note">
  <summary>数据是怎么来的</summary>
  <p>
    全部由本机脚本 <code>python tools/build-gamedata.py</code> 从游戏本体的
    <code>data</code> 目录提取：装备与技能读数据库文件，套装读装备套装插件的配置，
    宠物读宠物系统配置与进化道具，图标从加密的 <code>IconSet</code> 解密得到。
  </p>
  <p>
    游戏更新后重跑一次脚本即可，不需要手工维护。若数据里存在游戏本身的遗留问题
    （例如装备引用了未定义的套装名），脚本会在运行时提示，本站也照实呈现。
  </p>
</details>
