---
title: 游戏地图
layout: default
permalink: /map/
---

# 世界大地图

{% include wb_world_map.html %}

## 全部地点

下表与地图上的标记一一对应。窄屏下地图标记不好点，用这里的链接更稳妥。

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-地点">按地点筛选</label>
    <input type="search" id="f-地点" data-gd-filter placeholder="输入地点名筛选，例如「沼泽」">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的条目。换个关键词试试。</p>

  <div class="gd-table-wrap">
<table class="gd-table">
  <thead>
    <tr>
      <th scope="col">地点</th>
      <th scope="col">出入口</th>
      <th scope="col">图上位置</th>
    </tr>
  </thead>
  <tbody>
  {%- for p in site.data.maps.places -%}
    <tr>
      <td>
        {%- if p.url -%}
          <a href="{{ p.url | relative_url }}">{{ p.title }}</a>
        {%- else -%}
          {{ p.title }}<span class="wb-offmark">（地图数据未收录）</span>
        {%- endif -%}
      </td>
      <td>{{ p.exits }}</td>
      <td>{{ p.x }}% , {{ p.y }}%</td>
    </tr>
  {%- endfor -%}
  </tbody>
</table>
  </div>
</div>


{%- comment -%}
  下面这段是给维护者看的：数据怎么来的、怎么更新。
  正式站点上不需要读者看到操作细节，所以收在 <details> 里。
{%- endcomment -%}
<details class="wb-note">
  <summary>这张地图是怎么生成的</summary>
  <p>
    地图图片与地点坐标全部来自游戏本体的 <code>data</code> 目录：
    地点取自地图 <code>Map028.json</code> 中的<strong>场所移动事件</strong>，
    其图块坐标即按钮位置；图片取自 <code>outputimg</code> 目录。
  </p>
  <p>
    游戏更新后，在本机执行一次 <code>python tools/build-maps.py</code> 重新生成即可。
  </p>
</details>
