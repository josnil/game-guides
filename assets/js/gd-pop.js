/* ============================================================
   浮窗（悬停或点击都弹出）
   ------------------------------------------------------------
   用在宠物页的「魔变技能 / 魔变专属技能 / 魔变装备」上：单元格里放不下详情，
   鼠标悬停看一眼最方便；触屏没有 hover，所以点击也要能开。

   结构：
     <span class="gd-pop">
       <button class="gd-pop__btn" aria-expanded="false">魔变技能 · 2</button>
       <span class="gd-pop__panel" role="tooltip">…</span>
     </span>

   ⚠️ 面板用的是 position: fixed，坐标由这里算。
      原因：浮窗长在表格里，而表格容器有 overflow-x: auto（宽表必须能横向滚动），
      absolute 定位的浮窗会被那个滚动容器裁掉。
      改成 fixed 后它脱离所有会裁剪的祖先，「能横向滚动」和「浮窗完整」就不再冲突。
      ⇒ 所以**不要**把它改回 absolute，除非同时去掉容器的 overflow。

   行为：
     - 悬停 / 键盘聚焦：CSS 负责显示，本脚本负责定位（面板初始在屏幕外，不会闪）
     - 点击按钮：切换 is-open（给触屏用）
     - Esc 或点别处：关掉
     - 滚动 / 缩放：跟随重定位
     - aria-expanded 跟随状态更新，读屏用户也能感知
   ============================================================ */
(function () {
  "use strict";

  var GAP = 8;   // 浮窗与按钮之间的间距
  var EDGE = 8;  // 离视口边缘至少留这么多

  /** 把面板放到按钮附近：优先上方，放不下就下方，水平方向做边界收敛 */
  function place(pop) {
    var btn = pop.querySelector(".gd-pop__btn");
    var panel = pop.querySelector(".gd-pop__panel");
    if (!btn || !panel) return;

    var b = btn.getBoundingClientRect();
    var pw = panel.offsetWidth;
    var ph = panel.offsetHeight;
    if (!pw || !ph) return; // 还没渲染出来（例如所在标签页不可见），下次再说

    var top = b.top - ph - GAP;                    // 默认在按钮上方
    if (top < EDGE) top = b.bottom + GAP;          // 上方不够 → 放到下方
    if (top + ph > window.innerHeight - EDGE) {    // 下方也不够 → 贴住视口底部
      top = Math.max(EDGE, window.innerHeight - ph - EDGE);
    }

    var left = b.left + b.width / 2 - pw / 2;      // 与按钮居中对齐
    if (left + pw > window.innerWidth - EDGE) left = window.innerWidth - pw - EDGE;
    if (left < EDGE) left = EDGE;

    panel.style.top = Math.round(top) + "px";
    panel.style.left = Math.round(left) + "px";
  }

  function closeAll(except) {
    Array.prototype.forEach.call(document.querySelectorAll(".gd-pop.is-open"), function (p) {
      if (p === except) return;
      p.classList.remove("is-open");
      var b = p.querySelector(".gd-pop__btn");
      if (b) b.setAttribute("aria-expanded", "false");
    });
  }

  // 滚动/缩放时重定位（用 rAF 合并连续事件）
  var raf = 0;
  function reflow() {
    if (raf) return;
    raf = window.requestAnimationFrame(function () {
      raf = 0;
      // 点击打开的那些
      Array.prototype.forEach.call(document.querySelectorAll(".gd-pop.is-open"), place);
      // 悬停打开的那个（:hover 不走 is-open）
      var hovered = document.querySelector(".gd-pop:hover");
      if (hovered) place(hovered);
    });
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll(".gd-pop"), function (pop) {
      var btn = pop.querySelector(".gd-pop__btn");
      if (!btn) return;

      // 悬停/聚焦时先定位好，CSS 再把它显示出来 —— 面板初始在屏幕外，不会闪
      btn.addEventListener("mouseenter", function () { place(pop); });
      btn.addEventListener("focus", function () { place(pop); });

      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var open = pop.classList.toggle("is-open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) {
          closeAll(pop);
          place(pop);
        }
      });

      // 面板自己也要能接收点击（比如以后放链接），别被下面的关闭逻辑吃掉
      var panel = pop.querySelector(".gd-pop__panel");
      if (panel) {
        panel.addEventListener("click", function (ev) { ev.stopPropagation(); });
      }
    });

    document.addEventListener("click", function () { closeAll(null); });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") closeAll(null);
    });
    // capture: true —— 表格容器内部的滚动也要能收到
    window.addEventListener("scroll", reflow, true);
    window.addEventListener("resize", reflow);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
