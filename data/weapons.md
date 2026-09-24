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

  {%- comment -%}
    分类筛选：持握（单手/双手/双刀流）与类型（拳爪/剑/…）。
    与上面的名称搜索叠加生效（AND）。
    ⚠️ 「双刀流」判定的是武器的特性 code=55（装备槽类型），不是名称里有没有「双刀」二字 ——
       正式武器里备注含「二刀流」的只有 1 件测试武器。
  {%- endcomment -%}
  {%- assign wbHands = "单手,双手,双刀流" | split: "," -%}
  {%- assign wbWtypes = "拳爪,剑,弓,斧,枪,法杖,书,宠物武器,手里剑" | split: "," -%}

  <div class="gd-facets" data-gd-facets="hand">
    <span class="gd-facets__label">持握</span>
    <button type="button" class="gd-chip is-on" data-facet-value="" aria-pressed="true">全部 <span class="gd-chip__n">{{ items.size }}</span></button>
    {%- for h in wbHands -%}
      {%- assign hn = items | where: "handType", h | size -%}
      {%- if hn > 0 -%}
        <button type="button" class="gd-chip" data-facet-value="{{ h }}" aria-pressed="false">{{ h }} <span class="gd-chip__n">{{ hn }}</span></button>
      {%- endif -%}
    {%- endfor -%}
  </div>

  <div class="gd-facets" data-gd-facets="wtype">
    <span class="gd-facets__label">类型</span>
    <button type="button" class="gd-chip is-on" data-facet-value="" aria-pressed="true">全部 <span class="gd-chip__n">{{ items.size }}</span></button>
    {%- for t in wbWtypes -%}
      {%- assign tn = items | where: "wtype", t | size -%}
      {%- if tn > 0 -%}
        <button type="button" class="gd-chip" data-facet-value="{{ t }}" aria-pressed="false">{{ t }} <span class="gd-chip__n">{{ tn }}</span></button>
      {%- endif -%}
    {%- endfor -%}
  </div>

  {% include gd_table_hint.html %}

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
            data-hand="{{ it.handType }}"
            data-wtype="{{ it.wtype }}"
            data-name="{{ it.name }} {% for d in it.dropFrom %}{{ d.enemy }} {% endfor %}{{ it.set }} {{ it.wtype }}">
          <td>
            <span class="gd-name">
              {%- include gd_icon.html idx=it.iconIndex label=it.name -%}
              <span>{{ it.name }}</span>
            </span>
            {%- if it.set -%}<span class="gd-tag gd-tag--set">{{ it.set }}</span>{%- endif -%}
            {%- if it.handType == "双刀流" -%}<span class="gd-tag gd-tag--dual">双刀流</span>
            {%- elsif it.handType == "双手" -%}<span class="gd-tag gd-tag--two">双手</span>{%- endif -%}
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
