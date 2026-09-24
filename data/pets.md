---
title: 宠物
layout: default
permalink: /data/pets/
---

{%- assign wbPetData = site.data.gamedata.pets -%}
{%- assign wbPets = wbPetData.pets -%}
{%- assign wbGroups = wbPetData.chainGroups -%}
{%- assign wbStandalone = wbPetData.standalone -%}
{%- assign wbBranchy = 0 -%}
{%- for wbG in wbGroups -%}
  {%- for wbSt in wbG.stages -%}
    {%- if wbSt.forms.size > 1 -%}{%- assign wbBranchy = wbBranchy | plus: 1 -%}{%- break -%}{%- endif -%}
  {%- endfor -%}
{%- endfor -%}

# 宠物

{% include gd_subnav.html active="pets" %}

共 **{{ wbPets.size }}** 只，形成 **{{ wbGroups.size }}** 条进化链（其中 {{ wbBranchy }} 条含分支）。

同一个初始形态衍生出的多形态已经**合并为一条链**；同一阶段出现的不同进化型，作为该阶段的**分支**并列展示。

---

## 进化链

{%- comment -%}
  ⚠️ 这里必须用 <div markdown="0"> 把整段包起来，让 Kramdown 跳过 Markdown 处理。
  原因：Liquid 的 `{%- ... %}` 会**吃掉标签前面的空白（包括换行）**，
  于是 `## 进化链` 与紧随其后的 `<section>` 之间那个空行消失了 ——
  两者被并成同一段，标题变成「进化链&lt;section class="gd-chain"&gt;」，
  后面的缩进 HTML 还会被当成代码块整段转义，页面上直接显示原始标签。
  markdown="0" 让 Kramdown 原样透传这段内容，从根上避免这类空白敏感性。
{%- endcomment -%}
<div markdown="0">
{%- for wbG in wbGroups %}
{%- assign wbHasBranch = false -%}
{%- for wbSt in wbG.stages -%}
  {%- if wbSt.forms.size > 1 -%}{%- assign wbHasBranch = true -%}{%- endif -%}
{%- endfor -%}
<section class="gd-chain">
  <div class="gd-chain__title">
    <span class="gd-chain__name">{{ wbG.rootName }}</span>
    <span class="gd-chain__count">
      {{ wbG.depth }} 级进化 · 共 {{ wbG.size }} 种形态
      {%- if wbHasBranch %} · 含分支{% endif -%}
    </span>
  </div>

  {%- for wbSt in wbG.stages %}
    <div class="gd-chain__stage">
      <span class="gd-chain__level">{{ wbSt.level }} 阶</span>
      <div class="gd-chain__forms">
        {%- for wbF in wbSt.forms %}
          <div class="gd-chain__branch">
            {%- comment -%}
              来路：第 0 阶没有；其余每支显示自己用的进化道具与所需等级。
              联合进化还会列出需要带在身边的辅助宠物。
            {%- endcomment -%}
            {%- for wbV in wbF.via -%}
              <span class="gd-chain__via">
                {%- include gd_icon.html idx=wbV.itemIconIndex small=true label=wbV.itemName -%}
                <span class="gd-chain__via-name">{{ wbV.itemName }}</span>
                {%- if wbV.requireLevel and wbV.requireLevel > 0 -%}
                  <span>{{ wbV.requireLevel }} 级</span>
                {%- endif -%}
                {%- if wbV.assistNames.size > 0 -%}
                  <span>需 {{ wbV.assistNames | join: '、' }}</span>
                {%- endif -%}
              </span>
            {%- endfor -%}

            <span class="gd-pet">
              {%- if wbF.sprite -%}
                <img src="{{ wbF.sprite | relative_url }}" width="48" height="48" alt=""
                     style="image-rendering: pixelated">
              {%- endif -%}
              <span>
                <b>{{ wbF.name }}</b>
                {%- if wbF.className -%}<br><span class="gd-range">{{ wbF.className }}</span>{%- endif -%}
              </span>
            </span>

            {%- if wbF.growth.size > 0 -%}
              <span class="gd-pet__meta">
                <span>成长
                  {%- for wbPair in wbF.growth -%}
                    {{ wbPair[1].cn }}+{{ wbPair[1].value }}{% unless forloop.last %} {% endunless %}
                  {%- endfor -%}
                </span>
              </span>
            {%- endif -%}

            {%- include gd_pet_pops.html pet=wbF -%}
          </div>
        {%- endfor -%}
      </div>
    </div>
  {%- endfor %}
</section>
{%- endfor %}
</div>

---

## 全部宠物

未参与进化链的 {{ wbStandalone.size }} 只也在下表。**魔变技能与魔变装备**收在浮窗里 ——
鼠标悬停，或点一下标签即可展开。

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
          <th scope="col">成长</th>
          <th scope="col">进化</th>
          <th scope="col">魔变</th>
        </tr>
      </thead>
      <tbody>
      {%- for wbP in wbPets -%}
        <tr id="gd-pet-{{ wbP.id }}" data-name="{{ wbP.name }} {{ wbP.className }}">
          <td>
            <span class="gd-name">
              {%- if wbP.sprite -%}
                <img src="{{ wbP.sprite | relative_url }}" width="32" height="32" alt=""
                     style="image-rendering: pixelated">
              {%- endif -%}
              <span>{{ wbP.name }}</span>
            </span>
          </td>
          <td>{{ wbP.className }}</td>
          <td class="gd-range">
            {%- if wbP.growth.size > 0 -%}
              {%- for wbPair in wbP.growth -%}
                {{ wbPair[1].cn }} +{{ wbPair[1].value }}{% unless forloop.last %}、{% endunless %}
              {%- endfor -%}
            {%- else -%}
              —
            {%- endif -%}
          </td>
          <td class="gd-range">
            {%- if wbP.evolvesTo.size > 0 -%}
              {%- for wbE in wbP.evolvesTo -%}
                经「{{ wbE.item }}」{% if wbE.requireLevel and wbE.requireLevel > 0 %}（{{ wbE.requireLevel }} 级）{% endif %}
                → {{ wbPets | where: 'id', wbE.toId | map: 'name' | first }}{% unless forloop.last %}；{% endunless %}
              {%- endfor -%}
            {%- elsif wbP.evolvesFrom.size > 0 -%}
              终态
            {%- else -%}
              无
            {%- endif -%}
          </td>
          <td>{% include gd_pet_pops.html pet=wbP %}</td>
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
    进化关系写在<strong>进化道具</strong>（兽符）上：
    <code>&lt;PetEvolve: 进化前, 进化后&gt;</code> 与 <code>&lt;RequireLevel: 等级&gt;</code>，
    联合进化还需要额外的辅助宠物。魔变技能与魔变装备来自宠物系统配置与宠物备注。
  </p>
  <p>
    宠物头像从游戏的<strong>行走图</strong>里取（宠物没有图标索引），
    取朝下站立的那一帧；取不到行走图的宠物就不显示头像。
  </p>
</details>
