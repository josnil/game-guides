---
title: 首页
layout: default
nav_order: 1
---

{%- assign supported = site.data.versions.supported -%}
{%- assign stale = "" | split: "" -%}
{%- for g in site.guides -%}
  {%- assign gv = g.game_version -%}
  {%- if gv and gv != "" -%}
    {%- assign ok = false -%}
    {%- if supported contains gv -%}{%- assign ok = true -%}{%- endif -%}
    {%- unless ok -%}{%- assign stale = stale | push: g -%}{%- endunless -%}
  {%- endif -%}
{%- endfor -%}
{%- assign dated = site.guides | where_exp: "g", "g.last_modified_date" -%}
{%- assign recent = dated | sort: "last_modified_date" | reverse -%}

# {{ site.title }}

本站按**游戏版本**管理攻略有效性：每篇攻略都标注了它适用的游戏版本，
当游戏更新、某个版本被移出支持列表时，相关攻略会**自动**被标记为「可能已过期」。

**当前收录：{{ site.guides | size }} 篇 · 当前版本 {{ site.data.versions.current }} · 待复核 {{ stale | size }} 篇**

## 按分类查

| 分类 | 内容 |
| --- | --- |
| [BOSS 攻略]({{ '/guides/boss/' | relative_url }}) | 各 BOSS 的阶段拆解与打法 |
| [玩法攻略]({{ '/guides/mode/' | relative_url }}) | 速通、无伤、收集等玩法向内容 |
| [系统攻略]({{ '/guides/system/' | relative_url }}) | 设置、机制、数值等原理向内容 |

## 常用入口

- [按版本查攻略]({{ '/versions/' | relative_url }})：想知道某个版本有哪些攻略，从这里进
- [待复核清单]({{ '/outdated/' | relative_url }})：基于旧版本、可能需要更新的攻略

## 最近更新

{% if recent.size > 0 %}
{% for g in recent limit: 5 %}
- [{{ g.title }}]({{ g.url | relative_url }}) —— {{ g.last_modified_date | date: "%Y-%m-%d" }}
{% endfor %}
{% else %}
暂无内容。
{% endif %}

---

> 用站内搜索（页面上方的搜索框，或按 <kbd>/</kbd>）可以直接搜标题与正文关键词。
