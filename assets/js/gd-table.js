/* ============================================================
   游戏数据页的表格筛选
   ------------------------------------------------------------
   数据量很大（防具 613 件、技能 1221 条），纯静态表格翻起来很痛苦。
   这里给每张表加一个「按名称筛选」的输入框：输入即过滤行、并实时报出条数。

   设计要点（按无障碍要求）：
     - input 有 label（sr-only，不占版面）
     - 结果数量用 aria-live 播报，读屏用户也知道筛完剩几条
     - 不用动画，天然满足 prefers-reduced-motion
     - 表里没有一行匹配时给出明确提示，而不是留一片空白
   ============================================================ */
(function () {
  "use strict";

  function initOne(root) {
    var input = root.querySelector("[data-gd-filter]");
    var table = root.querySelector("table");
    var countEl = root.querySelector("[data-gd-count]");
    var emptyEl = root.querySelector("[data-gd-empty]");
    if (!input || !table) return;

    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    var total = rows.length;

    function apply() {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (tr) {
        var hit = !q || (tr.getAttribute("data-name") || "").toLowerCase().indexOf(q) !== -1;
        tr.hidden = !hit;
        if (hit) shown++;
      });
      if (countEl) countEl.textContent = q ? "命中 " + shown + " / " + total : "共 " + total + " 条";
      if (emptyEl) emptyEl.hidden = shown !== 0;
    }

    input.addEventListener("input", apply);
    input.addEventListener("search", apply);
    apply();
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-gd-table]"), initOne);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
