---
title: 阶段攻略
layout: default
permalink: /stages/
---

{%- assign wbStages = site.data.stages -%}

# 阶段攻略

按大陆顺序推进。左侧索引与下面的清单一致，点任意一项进入该大陆的攻略。

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-阶段">按大陆筛选</label>
    <input type="search" id="f-阶段" data-gd-filter placeholder="输入大陆名筛选，例如「黄金」">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的条目。换个关键词试试。</p>

  <div class="gd-table-wrap">
<table class="gd-table">
  <thead>
    <tr>
      <th scope="col" style="width:4.5rem">序号</th>
      <th scope="col">大陆</th>
      <th scope="col">攻略</th>
    </tr>
  </thead>
  <tbody>
  {%- for wbSt in wbStages -%}
    {%- assign wbStUrl = '/stages/' | append: wbSt.slug | append: '/' -%}
    <tr>
      <td class="gd-range">{{ wbSt.index }}</td>
      <td>{{ wbSt.name }}</td>
      <td><a href="{{ wbStUrl | relative_url }}">{{ wbSt.name }} 攻略</a></td>
    </tr>
  {%- endfor -%}
  </tbody>
</table>
  </div>
</div>


{% include wb_todo.html hint="各大陆的具体内容按序号逐个补充；每篇写好后左侧索引会自动识别当前页。" %}
