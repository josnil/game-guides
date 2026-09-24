---
title: 技能
layout: default
permalink: /data/skills/
---

{%- assign gd = site.data.gamedata.meta -%}
{%- assign items = site.data.gamedata.skills -%}
{%- assign weaponSkills = items | where: 'weaponSkill', true -%}

# 技能
{% include gd_subnav.html active="skills" %}


共 **{{ items.size }}** 条，其中**武器技能 {{ weaponSkills.size }}** 条。

类型：{{ gd.types.skillTypes | slice: 1, 5 | join: ' / ' }}。

{% include gd_excluded.html kind="skills" %}

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-skills">按名称筛选技能</label>
    <input type="search" id="f-skills" data-gd-filter placeholder="输入名称筛选，例如「拳」">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的技能。换个关键词试试。</p>

  {% include gd_table_hint.html %}

<div class="gd-table-wrap">
    <table class="gd-table">
      <thead>
        <tr>
          <th scope="col">名称</th>
          <th scope="col">类型</th>
          <th scope="col">伤害公式</th>
          <th scope="col" class="gd-num">消耗</th>
          <th scope="col">武器需求</th>
          <th scope="col">说明</th>
        </tr>
      </thead>
      <tbody>
      {%- for s in items -%}
        <tr id="gd-skill-{{ s.id }}"
            data-name="{{ s.name }} {{ s.stype }} {% for w in s.weaponTypes %}{{ w }} {% endfor %}">
          <td>
            <span class="gd-name">
              {%- include gd_icon.html idx=s.iconIndex label=s.name -%}
              <span>{{ s.name }}</span>
            </span>
          </td>
          <td>{{ s.stype }}</td>
          <td class="gd-range">
            {%- if s.formula and s.formula != '' -%}
              <code>{{ s.formula }}</code>
              {%- if s.variance and s.variance != 0 %} <span class="gd-tag">浮动 {{ s.variance }}%</span>{% endif -%}
              {%- if s.critical %} <span class="gd-tag">可暴击</span>{% endif -%}
            {%- else -%}
              —
            {%- endif -%}
          </td>
          <td class="gd-num">
            {%- if s.mpCost and s.mpCost > 0 -%}MP {{ s.mpCost }}{%- endif -%}
            {%- if s.mpCost and s.mpCost > 0 and s.tpCost and s.tpCost > 0 %} / {% endif -%}
            {%- if s.tpCost and s.tpCost > 0 -%}TP {{ s.tpCost }}{%- endif -%}
            {%- unless s.mpCost and s.mpCost > 0 -%}{%- unless s.tpCost and s.tpCost > 0 -%}—{%- endunless -%}{%- endunless -%}
          </td>
          <td>
            {%- if s.weaponSkill -%}
              {%- for w in s.weaponTypes -%}
                <span class="gd-tag gd-tag--set">{{ w }}</span>
              {%- endfor -%}
            {%- else -%}
              否
            {%- endif -%}
          </td>
          <td>
            {%- if s.desc and s.desc != '' -%}{{ s.desc | newline_to_br }}{%- else -%}—{%- endif -%}
            {%- if s.repeats and s.repeats > 1 %} <span class="gd-tag">×{{ s.repeats }} 次</span>{% endif -%}
            {%- if s.element and s.element != '' %} <span class="gd-tag">{{ s.element }}属性</span>{% endif -%}
          </td>
        </tr>
      {%- endfor -%}
      </tbody>
    </table>
  </div>
</div>

<details class="wb-note">
  <summary>「伤害公式」怎么读</summary>
  <p>
    公式来自游戏数据库，写法是 RPG Maker 的脚本表达式：
    <code>a</code> 是攻击方、<code>b</code> 是防守方，
    <code>a.atk</code> 即攻击方的攻击力。例如 <code>a.atk * 2 - b.def * 1</code>
    表示「攻击力 ×2 再减去对方防御」。
  </p>
  <p>
    <strong>武器技能</strong>是指必须装备对应类型武器才能使用的技能（表里已在「武器需求」标出）；
    其余技能填「否」，任何武器或空手都能用。
  </p>
</details>
