---
title: 万能散搭装
layout: default
permalink: /data/wildcard/
---

{%- assign items = site.data.gamedata.equipment.wildcard -%}

# 万能散搭装
{% include gd_subnav.html active="wildcard" %}


共 **{{ items.size }}** 件，都是带 `Equip Set Wildcard` 效果的装备。

## 这个效果是什么意思

游戏里的套装效果需要「同时装备同一套装的多件」才会激活。而这类装备的效果是：

> **给角色身上已装备的每一个套装各 +1 件。**

也就是说，它本身不属于任何套装，但穿上之后**能让所有正在生效的套装件数都往上跳一档**。
举例：你穿了 4 件黄金套装（下一档在 5 件），再戴一件万能散搭装，就直接吃到 5 件档位的加成。

若有多套套装同时生效，这个 +1 会**分别**作用在每一套上。

{%- assign scoped = items | where_exp: 'i', 'i.wildcardSets != nil' -%}
{%- if scoped.size > 0 -%}
  其中 {{ scoped.size }} 件是**限定范围**的，只对指定的套装生效。
{%- endif -%}

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-wild">按名称筛选</label>
    <input type="search" id="f-wild" data-gd-filter placeholder="输入名称筛选">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的装备。</p>

  {% include gd_table_hint.html %}

<div class="gd-table-wrap">
    <table class="gd-table">
      <thead>
        <tr>
          <th scope="col">名称</th>
          <th scope="col">类别</th>
          <th scope="col">类型</th>
          <th scope="col">属性区间</th>
          <th scope="col">生效范围</th>
          <th scope="col">掉落来源</th>
        </tr>
      </thead>
      <tbody>
      {%- for it in items -%}
        {%- assign ty = it.wtype | default: it.atype -%}
        <tr data-name="{{ it.name }} {{ ty }} {% for d in it.dropFrom %}{{ d.enemy }} {% endfor %}">
          <td>
            <span class="gd-name">
              {%- include gd_icon.html idx=it.iconIndex label=it.name -%}
              <span>{{ it.name }}</span>
            </span>
          </td>
          <td>{% if it.kind == 'weapon' %}武器{% else %}防具{% endif %}</td>
          <td>{{ ty }}</td>
          <td class="gd-range">{% include gd_range.html range=it.range %}</td>
          <td>
            {%- if it.wildcardSets -%}
              <span class="gd-tag">仅限 {{ it.wildcardSets }}</span>
            {%- else -%}
              <span class="gd-tag gd-tag--wild">所有套装</span>
            {%- endif -%}
          </td>
          <td class="gd-range">
            {%- if it.dropFrom.size > 0 -%}
              {%- for d in it.dropFrom -%}
                {{ d.enemy }}{% if d.rate %} {{ d.rate }}%{% endif %}{% unless forloop.last %}、{% endunless %}
              {%- endfor -%}
            {%- else -%}
              —
            {%- endif -%}
          </td>
        </tr>
      {%- endfor -%}
      </tbody>
    </table>
  </div>
</div>

<p>
  各套装的具体档位加成见 <a href="{{ '/data/sets/' | relative_url }}">套装</a>；
  装备的完整属性与掉落见 <a href="{{ '/data/weapons/' | relative_url }}">武器</a>、
  <a href="{{ '/data/armors/' | relative_url }}">防具</a>。
</p>
