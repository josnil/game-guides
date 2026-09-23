---
title: 宠物
layout: default
permalink: /data/pets/
---

{%- assign data = site.data.gamedata.pets -%}
{%- assign pets = data.pets -%}
{%- assign chains = data.chains -%}
{%- assign standalone = data.standalone -%}

# 宠物
{% include gd_subnav.html active="pets" %}


共 **{{ pets.size }}** 只，形成 **{{ chains.size }}** 条进化链（最长 {{ chains.first.steps.size }} 级）。

<div class="gd-kv">
  <span>捕获方式：<b>击败对应敌人后概率捕获</b>，也可以用兽符进化</span>
  <span>进化所需等级写在进化道具上</span>
</div>

---

## 进化链

{%- for c in chains %}
<section class="gd-chain">
  <div class="gd-chain__steps">
    {%- for step in c.steps -%}
      {%- assign pet = pets | where: 'id', step.petId | first -%}

      {%- comment -%}
        第一级之前没有「进化需求」，所以只在非首级前面插箭头。
      {%- endcomment -%}
      {%- if step.itemName -%}
        <span class="gd-chain__arrow">
          {%- include gd_icon.html idx=step.itemIconIndex small=true label=step.itemName -%}
          <span>{{ step.itemName }}</span>
          {%- if step.requireLevel and step.requireLevel > 0 -%}
            <span>{{ step.requireLevel }} 级</span>
          {%- endif -%}
          {%- if step.assistNames.size > 0 -%}
            <span>需 {{ step.assistNames | join: '、' }}</span>
          {%- endif -%}
        </span>
      {%- endif -%}

      <span class="gd-pet">
        {%- if step.sprite -%}
          <img src="{{ step.sprite | relative_url }}" width="48" height="48" alt="" style="image-rendering: pixelated">
        {%- endif -%}
        <span>
          <b>{{ step.name }}</b>
          {%- if step.className -%}<br><span class="gd-range">{{ step.className }}</span>{%- endif -%}
        </span>
      </span>
    {%- endfor -%}
  </div>

  {%- comment -%}
    链上每一级的细节（成长、专属技能、魔变技能）放在下面按级列出，
    免得把卡片挤爆。只显示有内容的项。
  {%- endcomment -%}
  {%- for step in c.steps -%}
    {%- assign pet = pets | where: 'id', step.petId | first -%}
    {%- if pet -%}
      {%- assign hasInfo = false -%}
      {%- if pet.growth.size > 0 or pet.demonicSkills.size > 0 or pet.demonicExclusiveSkill or pet.captureFrom.enemy -%}
        {%- assign hasInfo = true -%}
      {%- endif -%}
      {%- if hasInfo -%}
        <div class="gd-kv">
          <span><b>{{ pet.name }}</b></span>
          {%- if pet.captureFrom.enemy -%}
            <span>捕获自：<b>{{ pet.captureFrom.enemy }}</b>{% if pet.captureFrom.difficulty %}（难度 {{ pet.captureFrom.difficulty }}）{% endif %}</span>
          {%- endif -%}
          {%- if pet.growth.size > 0 -%}
            <span>成长：
              {%- for pair in pet.growth -%}
                {{ pair[1].cn }} +{{ pair[1].value }}{% unless forloop.last %}、{% endunless %}
              {%- endfor -%}
            </span>
          {%- endif -%}
          {%- if pet.demonicExclusiveSkill -%}
            <span>魔变专属技能：<b>{{ pet.demonicExclusiveSkill.name }}</b></span>
          {%- endif -%}
          {%- if pet.demonicSkills.size > 0 -%}
            <span>魔变技能：
              {%- for sk in pet.demonicSkills -%}
                {{ sk.name }}{% if sk.probability and sk.probability < 100 %}（{{ sk.probability }}%）{% endif %}{% unless forloop.last %}、{% endunless %}
              {%- endfor -%}
            </span>
          {%- endif -%}
        </div>
      {%- endif -%}
    {%- endif -%}
  {%- endfor -%}
</section>
{%- endfor %}

---

## 全部宠物

未参与进化链的宠物 {{ standalone.size }} 只也在下表里。

<div data-gd-table>
  <div class="gd-toolbar">
    <label class="sr-only" for="f-pets">按名称筛选宠物</label>
    <input type="search" id="f-pets" data-gd-filter placeholder="输入名称筛选，例如「史莱姆」">
    <span class="gd-count" data-gd-count aria-live="polite"></span>
  </div>
  <p class="gd-empty" data-gd-empty hidden>没有匹配的宠物。换个关键词试试。</p>

  <div class="gd-table-wrap">
    <table class="gd-table">
      <thead>
        <tr>
          <th scope="col">宠物</th>
          <th scope="col">阶级</th>
          <th scope="col">捕获来源</th>
          <th scope="col">成长</th>
          <th scope="col">进化</th>
          <th scope="col">魔变技能</th>
        </tr>
      </thead>
      <tbody>
      {%- for p in pets -%}
        <tr id="gd-pet-{{ p.id }}" data-name="{{ p.name }} {{ p.className }} {% if p.captureFrom.enemy %}{{ p.captureFrom.enemy }}{% endif %}">
          <td>
            <span class="gd-name">
              {%- if p.sprite -%}
                <img src="{{ p.sprite | relative_url }}" width="32" height="32" alt="" style="image-rendering: pixelated">
              {%- endif -%}
              <span>{{ p.name }}</span>
            </span>
          </td>
          <td>{{ p.className }}</td>
          <td class="gd-range">
            {%- if p.captureFrom.enemy -%}
              {{ p.captureFrom.enemy }}{% if p.captureFrom.difficulty %} · 难度 {{ p.captureFrom.difficulty }}{% endif %}
            {%- else -%}
              —
            {%- endif -%}
          </td>
          <td class="gd-range">
            {%- if p.growth.size > 0 -%}
              {%- for pair in p.growth -%}
                {{ pair[1].cn }} +{{ pair[1].value }}{% unless forloop.last %}、{% endunless %}
              {%- endfor -%}
            {%- else -%}
              —
            {%- endif -%}
          </td>
          <td class="gd-range">
            {%- if p.evolvesTo.size > 0 -%}
              {%- for e in p.evolvesTo -%}
                经「{{ e.item }}」{% if e.requireLevel and e.requireLevel > 0 %}（{{ e.requireLevel }} 级）{% endif %}
                → {{ pets | where: 'id', e.toId | map: 'name' | first }}{% unless forloop.last %}；{% endunless %}
              {%- endfor -%}
            {%- elsif p.evolvesFrom.size > 0 -%}
              终态
            {%- else -%}
              无
            {%- endif -%}
          </td>
          <td class="gd-range">
            {%- if p.demonicExclusiveSkill -%}
              <span class="gd-tag gd-tag--set">专属 · {{ p.demonicExclusiveSkill.name }}</span>
            {%- endif -%}
            {%- for sk in p.demonicSkills -%}
              <span class="gd-tag">{{ sk.name }}</span>
            {%- endfor -%}
            {%- if p.demonicSkills.size == 0 -%}
              {%- unless p.demonicExclusiveSkill -%}—{%- endunless -%}
            {%- endif -%}
          </td>
        </tr>
      {%- endfor -%}
      </tbody>
    </table>
  </div>
</div>

<details class="wb-note">
  <summary>这些数据是怎么来的</summary>
  <p>
    宠物是游戏里的「角色」，靠备注标记 <code>&lt;MKPet&gt;</code> 识别；
    捕获来源、难度、变异与魔变技能来自宠物系统插件的配置；
    进化关系写在<strong>进化道具</strong>（兽符）上：
    <code>&lt;PetEvolve: 进化前, 进化后&gt;</code> 与 <code>&lt;RequireLevel: 等级&gt;</code>，
    联合进化还需要额外的辅助宠物。
  </p>
  <p>
    宠物头像从游戏的行走图里取——宠物没有图标索引，形象存在角色行走图中，
    取朝下站立的那一帧。
  </p>
</details>
