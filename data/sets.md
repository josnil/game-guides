---
title: 套装
layout: default
permalink: /data/sets/
---

{%- assign sets = site.data.gamedata.equipment.sets -%}
{%- assign items = site.data.gamedata.equipment.weapons | concat: site.data.gamedata.equipment.armors -%}

# 套装
{% include gd_subnav.html active="sets" %}


共 **{{ sets.size }}** 套。每套装到指定件数就会激活对应档位的加成，件数越多效果越强。

{%- for s in sets %}
<section class="gd-set">
  <div class="gd-set__head">
    {%- include gd_icon.html idx=s.iconIndex label=s.name -%}
    <h2 class="gd-set__name">{{ s.name }}</h2>
    <span class="gd-set__count">
      {%- if s.members.size > 0 -%}
        共 {{ s.members.size }} 件
      {%- else -%}
        无归属装备
      {%- endif -%}
    </span>
  </div>

  {%- if s.pieces.size > 0 -%}
    <ul class="gd-set__bonuses">
      {%- for pc in s.pieces -%}
        <li>
          <span class="gd-set__pieces">{{ pc.count }} 件</span>
          <span>{{ pc.labels | join: ' · ' }}</span>
        </li>
      {%- endfor -%}
    </ul>
  {%- else -%}
    <p class="gd-empty">这一套没有任何件数加成。</p>
  {%- endif -%}

  {%- if s.members.size > 0 -%}
    <ul class="gd-set__members">
      {%- for m in s.members -%}
        <li>
          {%- include gd_icon.html idx=m.iconIndex small=true label=m.name -%}
          {%- comment -%}
            用 ID 做锚点而不是名称：名称可能重复，也可能含空格和特殊字符，
            直接当锚点在浏览器里对不上。
          {%- endcomment -%}
          {%- if m.kind == 'weapon' -%}
            <a href="{{ '/data/weapons/' | relative_url }}#gd-weapon-{{ m.id }}">{{ m.name }}</a>
          {%- else -%}
            <a href="{{ '/data/armors/' | relative_url }}#gd-armor-{{ m.id }}">{{ m.name }}</a>
          {%- endif -%}
        </li>
      {%- endfor -%}
    </ul>
  {%- else -%}
    {%- comment -%}
      游戏数据里有的套装没有装备归属（例如「时空套装」的引用者是个分隔条目，
      「冥王套装 / 古尸套装 / 强魔套装」则是装备引用了套装定义里不存在的名字）。
      这里如实说明，不假装它是完整的。
    {%- endcomment -%}
    <p class="gd-empty">
      游戏数据里没有装备归属于这一套 —— 可能是该套装已被改名或移除，
      而装备上的旧引用还在。本站如实呈现，不做修饰。
    </p>
  {%- endif -%}
</section>
{%- endfor %}

{%- comment -%}
  反向列出「装备引用了、但套装定义里没有」的名字。
  这是游戏数据本身的不一致，单独说明免得读者以为是本站漏了。
  名单由生成脚本算好（equipment.json 的 undefinedSets），页面不做集合运算。
{%- endcomment -%}
{%- assign missing = site.data.gamedata.equipment.undefinedSets -%}
{%- if missing.size > 0 %}
  <section class="wb-note">
    <h2>装备引用了但未定义的套装名</h2>
    <p>
      {%- for n in missing -%}
        <span class="gd-tag gd-tag--set">{{ n }}</span>
      {%- endfor -%}
    </p>
    <p>
      这些名字出现在装备的套装标记里，但游戏本体的套装定义中并不存在，
      因此它们不会触发任何加成。属于游戏数据的遗留问题，不是提取遗漏。
    </p>
  </section>
{%- endif %}
