---
title: 状态
layout: default
permalink: /data/states/
---

{%- assign items = site.data.gamedata.states -%}
{%- assign withDesc = items | where_exp: 's', 's.desc != ""' -%}

# 状态
{% include gd_subnav.html active="states" %}


共 **{{ items.size }}** 条（其中 {{ withDesc.size }} 条有说明文字）。

{% include gd_excluded.html kind="states" %}

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-states">按名称或说明筛选状态</label>
    <input type="search" id="f-states" data-gd-filter placeholder="输入名称或效果关键词，例如「中毒」">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的状态。换个关键词试试。</p>

  <div class="gd-table-wrap">
    <table class="gd-table">
      <thead>
        <tr>
          <th scope="col" style="width:4rem">图标</th>
          <th scope="col" style="width:12rem">名称</th>
          <th scope="col">具体描述</th>
        </tr>
      </thead>
      <tbody>
      {%- for s in items -%}
        <tr id="gd-state-{{ s.id }}" data-name="{{ s.name }} {{ s.desc }}">
          <td>{% include gd_icon.html idx=s.iconIndex label=s.name %}</td>
          <td>{{ s.name }}</td>
          <td>
            {%- if s.desc and s.desc != '' -%}
              {{ s.desc | newline_to_br }}
            {%- else -%}
              <span class="gd-range">游戏内没有写说明</span>
            {%- endif -%}
          </td>
        </tr>
      {%- endfor -%}
      </tbody>
    </table>
  </div>
</div>

<details class="wb-note">
  <summary>为什么有些状态没有说明</summary>
  <p>
    游戏数据库的状态条目本身<strong>没有 description 字段</strong>，
    说明文字写在条目的备注里（<code>&lt;Description: 文本&gt;</code>）。
    本站读取的就是这个备注；确实没写的条目会照实标出「游戏内没有写说明」，
    不替它编内容。
  </p>
</details>
