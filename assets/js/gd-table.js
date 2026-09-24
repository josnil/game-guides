/* ============================================================
   数据表的筛选与排序
   ------------------------------------------------------------
   数据量很大（防具 613 件、技能 1067 条），纯静态表格翻起来很痛苦。
   这里给每张表两件事：

     筛选：工具栏里的输入框，输入即过滤行、并实时报出条数
     排序：点表头切换升/降序，再点一次反向

   设计要点：
     - input 有 label（sr-only，不占版面）
     - 结果数量用 aria-live 播报；排序状态写在 th 的 aria-sort 上
     - 排序用按钮包裹表头文字，键盘可达（Tab 到、回车触发）
     - 不用动画，天然满足 prefers-reduced-motion
     - 表里没有一行匹配时给出明确提示，而不是留一片空白

   ── 排序怎么取「值」 ──
   td 上有 data-sort 就用它，否则用单元格文字。
   列类型默认按内容猜：**≥60% 的非空单元格含数字 ⇒ 当数值列**，
   这样「攻击 2~6」「level >= 5」「MP 30」会取第一个数字来比大小（正是想按它排）。
   猜错了也不要紧，只是排出来的顺序没意义 —— 用筛选照样能定位。
   想明确指定时，在 th 上写 data-sort-type="num" 或 "text"。
   空值永远排在最后（无论升序降序），不会插在中间。
   ============================================================ */
(function () {
  "use strict";

  var NUM_RE = /-?\d+(?:\.\d+)?/;

  function firstNumber(text) {
    var m = (text || "").match(NUM_RE);
    return m ? parseFloat(m[0]) : null;
  }

  function cellText(td) {
    if (!td) return "";
    var attr = td.getAttribute("data-sort");
    var raw = attr === null ? td.textContent : attr;
    return (raw || "").replace(/\s+/g, " ").trim();
  }

  /* ---------------- 排序 ---------------- */

  function initSort(table) {
    var head = table.tHead;
    var tbody = table.tBodies[0];
    if (!head || !head.rows.length || !tbody) return;

    var rows = Array.prototype.slice.call(tbody.rows);
    if (rows.length < 2) return;

    var ths = Array.prototype.slice.call(head.rows[head.rows.length - 1].cells);
    if (!ths.length) return;

    // 逐列判定：有没有内容、要不要按数字比
    var cols = ths.map(function (th, i) {
      var forced = (th.getAttribute("data-sort-type") || "").toLowerCase();
      var vals = rows.map(function (tr) { return cellText(tr.cells[i]); });
      var filled = vals.filter(function (v) { return v !== ""; });
      var numeric = false;
      if (filled.length) {
        if (forced === "num") {
          numeric = true;
        } else if (forced === "text") {
          numeric = false;
        } else {
          var withNum = filled.filter(function (v) { return firstNumber(v) !== null; }).length;
          numeric = withNum / filled.length >= 0.6;
        }
      }
      return { index: i, numeric: numeric, sortable: filled.length > 0 };
    });

    var state = { col: -1, dir: 1 };

    function sortBy(col, dir) {
      var spec = cols[col];
      var indexed = rows.map(function (tr, i) { return { tr: tr, at: i }; });

      indexed.sort(function (a, b) {
        var ta = cellText(a.tr.cells[col]);
        var tb = cellText(b.tr.cells[col]);

        if (spec.numeric) {
          var na = firstNumber(ta);
          var nb = firstNumber(tb);
          // 空值恒定排在最后，不随升降序翻转
          if (na === null && nb !== null) return 1;
          if (nb === null && na !== null) return -1;
          if (na !== null && nb !== null && na !== nb) return (na - nb) * dir;
        } else if (ta !== tb) {
          // 中文按拼音排更符合直觉
          return ta.localeCompare(tb, "zh-Hans-CN") * dir;
        }
        return a.at - b.at; // 并列时保持原有顺序，避免每次点击都乱跳
      });

      var frag = document.createDocumentFragment();
      for (var i = 0; i < indexed.length; i++) frag.appendChild(indexed[i].tr);
      tbody.appendChild(frag);
    }

    function paint() {
      buttons.forEach(function (btn, i) {
        var th = ths[i];
        var on = state.col === i;
        btn.classList.toggle("is-asc", on && state.dir === 1);
        btn.classList.toggle("is-desc", on && state.dir === -1);
        th.setAttribute("aria-sort", on ? (state.dir === 1 ? "ascending" : "descending") : "none");
      });
    }

    var buttons = ths.map(function (th, i) {
      if (!cols[i].sortable) return null;

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "gd-sort";
      btn.textContent = th.textContent.trim();
      // 提示「可点」
      btn.title = "点击按「" + btn.textContent + "」排序";
      th.textContent = "";
      th.appendChild(btn);
      th.setAttribute("aria-sort", "none");
      th.classList.add("gd-th--sortable");

      btn.addEventListener("click", function () {
        // 同一列再点就反向；换列则从升序开始
        var dir = state.col === i && state.dir === 1 ? -1 : 1;
        state.col = i;
        state.dir = dir;
        sortBy(i, dir);
        paint();
      });
      return btn;
    });

    paint();
  }

  /* ---------------- 筛选 ---------------- */

  function initFilter(root) {
    var input = root.querySelector("[data-gd-filter]");
    var table = root.querySelector("table");
    var countEl = root.querySelector("[data-gd-count]");
    var emptyEl = root.querySelector("[data-gd-empty]");
    if (!input || !table) return;

    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    var total = rows.length;

    // 优先用 data-name（模板里精心拼好的：名称 + 掉落来源 + 类型…），
    // 没有就退回整行文字 —— 这样临时加的小表也能直接筛。
    function haystack(tr) {
      var dn = tr.getAttribute("data-name");
      return (dn === null ? tr.textContent : dn).toLowerCase();
    }

    function apply() {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (tr) {
        var hit = !q || haystack(tr).indexOf(q) !== -1;
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

  /* ---------------- 入口 ---------------- */

  function init() {
    // 排序：所有数据表都自动生效，不需要页面加任何标记
    Array.prototype.forEach.call(document.querySelectorAll("table.gd-table"), initSort);
    // 筛选：带工具栏的表格
    Array.prototype.forEach.call(document.querySelectorAll("[data-gd-table]"), initFilter);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
