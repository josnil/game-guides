---
title: 按版本查攻略
layout: default
nav_order: 20

# 根目录的 .md 页面默认会生成 /versions.html；写死 permalink 才能得到干净的 /versions/
permalink: /versions/
---

# 按版本查攻略

游戏每次大版本更新都会改动一部分机制。下面按版本倒序列出各版本的攻略，
方便你在确认自己游戏版本之后，直接找到对得上的内容。

{% for v in site.data.versions.history %}
{%- assign items = site.guides | where: "game_version", v.id -%}

## {{ v.name }}
{% if v.released %}

发布时间：{{ v.released | date: "%Y-%m-%d" }}{% if v.status == "current" %} · **当前版本**{% elsif v.status == "outdated" %} · 已停止支持{% endif %}
{% endif %}

{% if items.size > 0 %}
{% for g in items %}
- [{{ g.title }}]({{ g.url | relative_url }}){% if g.difficulty %} —— 难度：{{ g.difficulty }}{% endif %}
{% endfor %}
{% else %}
这个版本暂时还没有攻略。
{% endif %}

{% endfor %}
