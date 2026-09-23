/* ============================================================
   浮窗（悬停或点击都弹出）
   ------------------------------------------------------------
   用在宠物页的「魔变技能 / 魔变专属技能」上：单元格里放不下技能详情，
   鼠标悬停看一眼最方便；触屏没有 hover，所以点击也要能开。

   结构：
     <span class="gd-pop">
       <button class="gd-pop__btn" aria-expanded="false">魔变技能 · 2</button>
       <span class="gd-pop__panel" role="tooltip">…</span>
     </span>

   行为：
     - 悬停 / 键盘聚焦：由 CSS 负责显示（无需 JS）
     - 点击按钮：切换 is-open（给触屏用）
     - Esc 或点别处：关掉
     - aria-expanded 跟随状态更新，读屏用户也能感知
   ============================================================ */
(function () {
  "use strict";

  function closeAll(except) {
    Array.prototype.forEach.call(document.querySelectorAll(".gd-pop.is-open"), function (p) {
      if (p === except) return;
      p.classList.remove("is-open");
      var b = p.querySelector(".gd-pop__btn");
      if (b) b.setAttribute("aria-expanded", "false");
    });
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll(".gd-pop"), function (pop) {
      var btn = pop.querySelector(".gd-pop__btn");
      if (!btn) return;

      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var open = pop.classList.toggle("is-open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) closeAll(pop);
      });

      // 面板自己也要能接收点击（比如以后放链接），别被上面的关闭逻辑吃掉
      var panel = pop.querySelector(".gd-pop__panel");
      if (panel) {
        panel.addEventListener("click", function (ev) { ev.stopPropagation(); });
      }
    });

    document.addEventListener("click", function () { closeAll(null); });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") closeAll(null);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
