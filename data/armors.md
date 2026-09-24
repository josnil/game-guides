---
title: 防具
layout: default
permalink: /data/armors/
---

{%- assign gd = site.data.gamedata.meta -%}
{%- assign items = site.data.gamedata.equipment.armors -%}

# 防具
{% include gd_subnav.html active="armors" %}


共 **{{ items.size }}** 件。属性显示为 **下界 ~ 上界**（见 [游戏数据总览]({{ '/data/' | relative_url }}) 里的区间说明）。

{% include gd_excluded.html kind="armors" %}

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-armors">按名称筛选防具</label>
    <input type="search" id="f-armors" data-gd-filter placeholder="输入名称筛选，例如「重甲」">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的防具。换个关键词试试。</p>

  {% include gd_table_hint.html %}

<div class="gd-table-wrap">
    <table class="gd-table">
      <thead>
        <tr>
          <th scope="col">名称</th>
          <th scope="col">类别</th>
          <th scope="col">部位</th>
          <th scope="col">属性区间</th>
          <th scope="col">需求</th>
          <th scope="col">掉落来源</th>
          <th scope="col">说明</th>
        </tr>
      </thead>
      <tbody>
      {%- for it in items -%}
        <tr id="gd-armor-{{ it.id }}"
            data-name="{{ it.name }} {{ it.atype }} {{ it.etype }} {% for d in it.dropFrom %}{{ d.enemy }} {% endfor %}{{ it.set }}">
          <td>
            <span class="gd-name">
              {%- include gd_icon.html idx=it.iconIndex label=it.name -%}
              <span>{{ it.name }}</span>
            </span>
            {%- if it.set -%}<span class="gd-tag gd-tag--set">{{ it.set }}</span>{%- endif -%}
            {%- if it.wildcard -%}<span class="gd-tag gd-tag--wild">万能散搭</span>{%- endif -%}
          </td>
          <td>{{ it.atype }}</td>
          <td>{{ it.etype }}</td>
          <td class="gd-range">{% include gd_range.html range=it.range %}</td>
          <td class="gd-range">
            {%- if it.reqRaw -%}{{ it.reqRaw }}{%- endif -%}
            {%- if it.classOnly -%}<span class="gd-tag">限职业 {{ it.classOnly }}</span>{%- endif -%}
            {%- unless it.reqRaw or it.classOnly -%}—{%- endunless -%}
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
          <td>{{ it.desc | newline_to_br }}</td>
        </tr>
      {%- endfor -%}
      </tbody>
    </table>
  </div>
</div>

<details class="wb-note">
  <summary>类别与部位的区别</summary>
  <p>
    <strong>类别</strong>是防具的材质/性质（{{ gd.types.armorTypes | slice: 1, 10 | join: ' / ' }}），
    <strong>部位</strong>是它穿在哪（{{ gd.types.equipTypes | slice: 3, 11 | join: ' / ' }}）。
    同一件防具两者都有，例如「黄金头冠」是<strong>轻甲</strong>、部位是<strong>头部</strong>。
  </p>
</details>
