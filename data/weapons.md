---
title: 武器
layout: default
permalink: /data/weapons/
---

{%- assign gd = site.data.gamedata.meta -%}
{%- assign items = site.data.gamedata.equipment.weapons -%}

# 武器
{% include gd_subnav.html active="weapons" %}


共 **{{ items.size }}** 件。属性显示为 **下界 ~ 上界**（见 [游戏数据总览]({{ '/data/' | relative_url }}) 里的区间说明）。

{% include gd_excluded.html kind="weapons" %}

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-weapons">按名称筛选武器</label>
    <input type="search" id="f-weapons" data-gd-filter placeholder="输入名称筛选，例如「黄金」">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的武器。换个关键词试试。</p>

  <div class="gd-table-wrap">
    <table class="gd-table">
      <thead>
        <tr>
          <th scope="col">名称</th>
          <th scope="col">类型</th>
          <th scope="col">属性区间</th>
          <th scope="col">需求</th>
          <th scope="col">掉落来源</th>
          <th scope="col">说明</th>
        </tr>
      </thead>
      <tbody>
      {%- for it in items -%}
        <tr id="gd-weapon-{{ it.id }}"
            data-name="{{ it.name }} {% for d in it.dropFrom %}{{ d.enemy }} {% endfor %}{{ it.set }} {{ it.wtype }}">
          <td>
            <span class="gd-name">
              {%- include gd_icon.html idx=it.iconIndex label=it.name -%}
              <span>{{ it.name }}</span>
            </span>
            {%- if it.set -%}<span class="gd-tag gd-tag--set">{{ it.set }}</span>{%- endif -%}
            {%- if it.twoHanded -%}<span class="gd-tag gd-tag--two">双手</span>{%- endif -%}
            {%- if it.wildcard -%}<span class="gd-tag gd-tag--wild">万能散搭</span>{%- endif -%}
          </td>
          <td>{{ it.wtype }}</td>
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
  <summary>关于「只手数」与类型</summary>
  <p>
    游戏的武器类型是按<strong>种类</strong>分的（{{ gd.types.weaponTypes | slice: 1, 9 | join: ' / ' }}），
    并不直接区分单手/双手。带 <code>&lt;双手持&gt;</code> 标记的武器即为双手武器，表中已标出「双手」；
    其余为单手。
  </p>
  <p>
    「二刀流」在游戏里是<strong>特性</strong>（来自职业、角色或武器本身），不是装备自身的属性，
    所以本表不按它分类。
  </p>
</details>
