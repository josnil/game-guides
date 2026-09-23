---
title: 待复核清单
layout: default
nav_order: 30
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

# 待复核清单

这里列出的攻略，其适用的游戏版本已经不在支持列表中（见 `_data/versions.yml` 的 `supported`）。
它们可能仍然有效，但需要人工确认一次。

**共 {{ stale | size }} 篇需要复核。**

{% if stale.size > 0 %}
<ul class="vg-stale-list">
{% for g in stale %}
<li><a href="{{ g.url | relative_url }}">{{ g.title }}</a> —— 基于 {{ g.game_version }}{% if g.last_modified_date %}，最后更新 {{ g.last_modified_date | date: "%Y-%m-%d" }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
当前没有待复核的攻略。
{% endif %}

---

## 复核完之后怎么做

1. 如果内容仍然有效：把该攻略 front matter 里的 `game_version` 改成它实际适用的新版本号（例如 `"2.4"`）。
2. 如果内容已经失效：直接改写成新版本的做法，或者删掉这篇文章。
3. 如果只是部分失效：在正文对应位置插入提示框，并说明哪一段不适用：

   ```
   {: .outdated }
   若你的游戏版本低于 2.4，本打法的第二段闪避不成立。
   ```

改完之后，本清单会自动少一篇。
