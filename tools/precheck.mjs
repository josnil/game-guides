#!/usr/bin/env node
// ============================================================
// 本地预检脚本
// ------------------------------------------------------------
// 用途：本机没有 Ruby，无法 `bundle exec jekyll build` 本地验证。
// 这个脚本用 Node 把「最容易推上去才发现的错误」提前拦下来。
//
// 用法：
//   npm install          # 只需装一次
//   npm run check        # 或 node tools/precheck.mjs
//
// 重要：这只是「近似」校验。Jekyll 用的是 Ruby 的 YAML 解析器
// 和 Liquid 模板引擎，本脚本用 js-yaml 与字符串计数做近似判断。
// **GitHub Actions 的构建结果才是唯一权威。**
// ============================================================

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

// ------------------------------------------------------------
// js-yaml 是可选依赖：装了才能做真正的 YAML 校验，没装就降级。
// ------------------------------------------------------------
let yaml = null;
try {
  yaml = require("js-yaml");
} catch {
  // 下面会给出提示
}

const errors = [];
const warnings = [];
const E = (file, msg) => errors.push({ file, msg });
const W = (file, msg) => warnings.push({ file, msg });

const rel = (p) => path.relative(ROOT, p).split(path.sep).join("/");

function walk(dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ent.name.startsWith(".")) continue;
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) out.push(...walk(p));
    else out.push(p);
  }
  return out;
}

function read(p) {
  return fs.readFileSync(p, "utf8").replace(/^\uFEFF/, ""); // 去掉可能存在的 UTF-8 BOM
}

function splitFrontMatter(src) {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---(\r?\n|$)/);
  if (!m) return null;
  return { raw: m[1], body: src.slice(m[0].length) };
}

const count = (s, sub) => s.split(sub).length - 1;

function checkLiquid(file, body) {
  for (const [open, close] of [["{%", "%}"], ["{{", "}}"]]) {
    const a = count(body, open);
    const b = count(body, close);
    if (a !== b) {
      E(file, `Liquid 分隔符疑似不配对：${open} 出现 ${a} 次，${close} 出现 ${b} 次（最高频的构建报错就是这个）`);
    }
  }
  // 正文里想原样显示 {{ }} 必须用 {% raw %} 包住
  const raws = count(body, "{% raw %}") + count(body, "{%- raw -%}");
  const endRaws = count(body, "{% endraw %}") + count(body, "{%- endraw -%}");
  if (raws !== endRaws) E(file, `{% raw %} 与 {% endraw %} 数量不一致（${raws} vs ${endRaws}）`);
}

const THEME_LAYOUTS = new Set([
  "default", "page", "post", "home", "about", "collection", "child", "raw", "minimal",
]);

// ============================================================
// 1. _config.yml
// ============================================================
const CONFIG = path.join(ROOT, "_config.yml");
let cfg = null;

if (!fs.existsSync(CONFIG)) {
  E("_config.yml", "文件不存在");
} else if (!yaml) {
  W("_config.yml", "未安装 js-yaml，跳过 YAML 深度校验（请先运行 npm install）");
} else {
  try {
    cfg = yaml.load(read(CONFIG));
  } catch (e) {
    E("_config.yml", `YAML 解析失败：${e.message}`);
  }
}

if (cfg) {
  const f = "_config.yml";

  if (!cfg.url) {
    E(f, "缺少 url：jekyll-seo-tag 与 sitemap 需要它生成绝对地址");
  } else if (/^https?:\/\/[^/]+\/.+/.test(String(cfg.url))) {
    E(f, `url 只应写到域名，不要带仓库路径。当前值 "${cfg.url}" 会让全站链接错乱。改为 https://<用户名>.github.io`);
  }

  if (cfg.baseurl !== undefined && cfg.baseurl !== "") {
    E(f, `不要设置 baseurl（当前为 "${cfg.baseurl}"）：它由 GitHub Actions 的 configure-pages 注入。写死会导致「用户站点/项目站点」切换时路径全错`);
  }

  if (cfg.theme !== "just-the-docs") {
    W(f, `theme 不是 just-the-docs（当前 ${JSON.stringify(cfg.theme)}），请确认 Gemfile 里也锁了对应主题版本`);
  }

  if (!Array.isArray(cfg.plugins)) {
    E(f, "plugins 必须是数组");
  } else {
    // 这里的插件必须同时出现在 Gemfile 的 :jekyll_plugins 组里，否则构建报 could not be found
    const gemfile = fs.existsSync(path.join(ROOT, "Gemfile")) ? read(path.join(ROOT, "Gemfile")) : "";
    for (const p of cfg.plugins) {
      if (!gemfile.includes(p)) E(f, `插件 ${p} 没有写在 Gemfile 里，Jekyll 会报 "could not be found"`);
    }
  }

  const g = cfg.collections && cfg.collections.guides;
  if (!g) E(f, "缺少 collections.guides 配置");
  else {
    if (g.output !== true) E(f, "collections.guides.output 必须为 true，否则攻略不会被渲染成页面");
    if (!g.permalink) E(f, "collections.guides.permalink 缺失，建议写成 /guides/:path/");
  }
}

// ============================================================
// 2. Gemfile
// ============================================================
const GEMFILE = path.join(ROOT, "Gemfile");
if (!fs.existsSync(GEMFILE)) {
  E("Gemfile", "文件不存在");
} else {
  const gf = read(GEMFILE);
  if (!/gem\s+["']jekyll["']/.test(gf)) E("Gemfile", "没有声明 jekyll");
  if (!/gem\s+["']just-the-docs["']\s*,\s*["']\d/.test(gf)) {
    W("Gemfile", "just-the-docs 没有锁定具体版本号。官方迁移文档明确：未固定版本的主题会在下次构建时自动升级，可能导致站点突然走样");
  }
}

// ============================================================
// 3. 工作流
// ============================================================
const WF = path.join(ROOT, ".github", "workflows", "pages.yml");
if (!fs.existsSync(WF)) {
  E(".github/workflows/pages.yml", "文件不存在，Pages 不会自动构建");
} else {
  const wf = read(WF);
  const f = ".github/workflows/pages.yml";

  if (wf.includes("jekyll-build-pages")) {
    E(f, "检测到 actions/jekyll-build-pages：它会忽略仓库里的 Gemfile、退回内置 Jekyll 3.10.0，主题与插件锁版全部失效。请改用 ruby/setup-ruby + bundle exec jekyll build");
  }
  if (!wf.includes("bundle exec jekyll build")) {
    E(f, "没有找到 `bundle exec jekyll build` 步骤");
  }
  if (!wf.includes("--baseurl")) {
    E(f, "构建命令没有传 --baseurl，项目站点形态下样式与图片会 404");
  }
  if (!/id-token:\s*write/.test(wf)) E(f, "缺少 permissions: id-token: write，部署会报 OIDC 错误");
  if (!/pages:\s*write/.test(wf)) E(f, "缺少 permissions: pages: write，部署会 403");
  if (!/configure-pages@/.test(wf)) E(f, "没有使用 actions/configure-pages");
  if (!/deploy-pages@/.test(wf)) E(f, "没有使用 actions/deploy-pages");
}

// ============================================================
// 4. _data/versions.yml
// ============================================================
const VERSIONS = path.join(ROOT, "_data", "versions.yml");
let historyIds = new Set();
let supported = null;
let currentVersion = null;

if (!fs.existsSync(VERSIONS)) {
  E("_data/versions.yml", "文件不存在，版本过期机制无法工作");
} else if (yaml) {
  const f = "_data/versions.yml";
  let vd = null;
  try {
    vd = yaml.load(read(VERSIONS));
  } catch (e) {
    E(f, `YAML 解析失败：${e.message}`);
  }
  if (vd) {
    if (typeof vd.current !== "string") {
      E(f, `current 必须是字符串（加引号）。当前解析成 ${typeof vd.current}，版本号会丢精度`);
    } else {
      currentVersion = vd.current;
    }
    if (!Array.isArray(vd.history)) {
      E(f, "history 必须是数组");
    } else {
      for (const item of vd.history) {
        if (typeof item.id !== "string") {
          E(f, `history 里的 id ${JSON.stringify(item.id)} 必须是字符串（加引号），否则和攻略里的 game_version 比对会失败`);
        } else {
          historyIds.add(item.id);
        }
        if (!item.name) W(f, `history 里的 ${JSON.stringify(item.id)} 缺少 name`);
      }
    }
    if (!Array.isArray(vd.supported)) {
      E(f, "supported 必须是数组");
    } else {
      supported = vd.supported;
      for (const s of vd.supported) {
        if (typeof s !== "string") E(f, `supported 里的 ${JSON.stringify(s)} 必须是字符串（加引号）`);
        if (!historyIds.has(s)) W(f, `supported 里的 "${s}" 没有出现在 history 中`);
      }
      if (typeof vd.current === "string" && !vd.supported.includes(vd.current)) {
        E(f, `current "${vd.current}" 不在 supported 列表里，当前版本的攻略会被误判为过期`);
      }
    }
  }
} else {
  W("_data/versions.yml", "未安装 js-yaml，跳过校验");
}

// ============================================================
// 5. 攻略文件
// ============================================================
const GUIDES_DIR = path.join(ROOT, "_guides");
const guideFiles = walk(GUIDES_DIR).filter((p) => p.endsWith(".md"));
const guides = [];
const titles = new Map(); // title -> file
const pendingParents = []; // 收集所有 parent 声明，循环结束后统一校验

if (guideFiles.length === 0) {
  W("_guides/", "目录下没有任何 .md 攻略文件");
}

for (const p of guideFiles) {
  const f = rel(p);
  const src = read(p);
  const fm = splitFrontMatter(src);

  if (!fm) {
    E(f, "缺少 front matter（文件必须以 --- 开头、以 --- 结束）");
    continue;
  }

  let data = null;
  if (yaml) {
    try {
      data = yaml.load(fm.raw) || {};
    } catch (e) {
      E(f, `front matter YAML 解析失败：${e.message}（常见原因：标题里有半角冒号没加引号）`);
      continue;
    }
  } else {
    data = {};
  }

  const isIndex = path.basename(p) === "index.md";
  guides.push({ file: f, data, isIndex, path: p });

  if (typeof data.title !== "string" || !data.title.trim()) {
    E(f, "缺少 title，或 title 不是字符串");
  } else {
    if (titles.has(data.title)) {
      E(f, `title "${data.title}" 与 ${titles.get(data.title)} 重复。just-the-docs 的导航要求全站 title 唯一`);
    } else {
      titles.set(data.title, f);
    }
    if (/[:：]\s/.test(data.title) && !/^["']/.test(fm.raw.match(/title:\s*(.*)/)?.[1] ?? "")) {
      W(f, `title 里含半角冒号，建议整体加引号（如 title: "..."），否则 YAML 可能解析失败`);
    }
  }

  if (isIndex) {
    if (data.nav_order === undefined) W(f, "分类索引页建议写 nav_order，否则导航顺序不确定");
  } else {
    for (const key of ["game_version", "mode", "difficulty"]) {
      if (data[key] === undefined || data[key] === "") E(f, `缺少必填字段 ${key}`);
    }
    if (data.game_version !== undefined && typeof data.game_version !== "string") {
      E(f, `game_version 必须是字符串（加引号）。当前被解析成 ${typeof data.game_version}，写成 2.4 会被当成浮点数，1.10 甚至会被吃掉变成 1.1，过期判定会全乱`);
    }
    if (typeof data.game_version === "string" && historyIds.size > 0 && !historyIds.has(data.game_version)) {
      E(f, `game_version "${data.game_version}" 不在 _data/versions.yml 的 history 里（版本号拼错了？）`);
    }
    if (!data.last_modified_date && !data.date) {
      W(f, "建议补 last_modified_date，首页的「最近更新」和待复核清单会用到它");
    }
  }

  if (data.parent) {
    // 父页面可能出现在后续文件里，这里只记录，最后统一校验
    pendingParents.push({ file: f, parent: data.parent });
  }

  if (data.layout && !THEME_LAYOUTS.has(data.layout) && !fs.existsSync(path.join(ROOT, "_layouts", `${data.layout}.html`))) {
    E(f, `layout "${data.layout}" 在 _layouts/ 下不存在，也不是主题内置布局`);
  }

  checkLiquid(f, fm.body);

  // 检查 include 引用
  const includeRe = /\{%-?\s*include(?:_cached)?\s+([\w./-]+)/g;
  let m;
  while ((m = includeRe.exec(fm.body)) !== null) {
    const inc = m[1];
    if (!fs.existsSync(path.join(ROOT, "_includes", inc))) {
      W(f, `引用了 _includes/${inc}，但本地 _includes/ 下没有这个文件（若主题自带可忽略）`);
    }
  }
}

// 统一校验 parent 是否存在（必须在所有文件都读完、titles 收集完整之后）
for (const { file, parent } of pendingParents) {
  if (!titles.has(parent)) {
    E(file, `parent "${parent}" 找不到对应的页面。just-the-docs 里 parent 必须精确匹配另一个页面的 title`);
  }
}

// ============================================================
// 6. 链接检查
// ------------------------------------------------------------
// 这一节是为了拦住一类真实踩过的坑：正文里写 {{ '/outdated/' | relative_url }}，
// 但 Jekyll 对根目录的 .md 页面默认生成 /outdated.html，两者不匹配 → 线上 404。
// ============================================================
const knownUrls = new Set();

// 6.1 所有页面（_guides 是 collection，单独在 6.2 处理）
//     不能只看根目录：stages/xxx.md 这类子目录页面也要纳入，
//     否则侧边栏指向它们的链接会被误报成死链。
for (const p of walk(ROOT)) {
  if (!p.endsWith(".md")) continue;
  if (path.basename(p) === "README.md") continue;
  if (p.includes(`${path.sep}node_modules${path.sep}`)) continue;
  if (p.startsWith(GUIDES_DIR + path.sep)) continue; // collection 交给 6.2
  if (rel(p).startsWith("tools/")) continue; // 不参与构建

  const f = rel(p);
  const fm = splitFrontMatter(read(p));
  let data = {};
  if (fm && yaml) {
    try {
      data = yaml.load(fm.raw) || {};
    } catch {
      data = {};
    }
  }

  const base = path.basename(p, ".md");
  // 注意：path.relative 对「同一目录」返回的是空字符串，不是 "."。
  // 早期版本拿 "." 判断根目录，结果 index.md 没被算成 "/"，首页链接被误报成死链。
  const dirRaw = path.relative(ROOT, path.dirname(p));
  const dirRel = dirRaw === "" ? "" : dirRaw.split(path.sep).join("/");
  const isRoot = dirRel === "";

  if (data.permalink) {
    knownUrls.add(String(data.permalink));
  } else if (base === "index") {
    knownUrls.add(isRoot ? "/" : `/${dirRel}/`);
  } else {
    const guess = isRoot ? `/${base}.html` : `/${dirRel}/${base}.html`;
    const pretty = isRoot ? `/${base}/` : `/${dirRel}/${base}/`;
    knownUrls.add(guess);
    W(
      f,
      `没有写 permalink，这一页的网址会是 ${guess}（带 .html 后缀）。若别处用 ${pretty} 链接它就会 404 —— 建议补一行 permalink: ${pretty}`
    );
  }
}

// 6.2 攻略集合生成的 URL
for (const g of guides) {
  const relFromGuides = path.relative(GUIDES_DIR, g.path).split(path.sep).join("/");
  if (g.isIndex) {
    const dir = path.dirname(relFromGuides);
    knownUrls.add(dir === "." ? "/guides/" : `/guides/${dir}/`);
  } else {
    knownUrls.add(`/guides/${relFromGuides.replace(/\.md$/, "")}/`);
  }
}

// 6.3 收集所有 relative_url 引用并逐个核对
// 注意两件事：
//   1) README.md 不参与构建（_config.yml 里 exclude 了），它里面的写法都是示例，不能当真实引用
//   2) HTML 注释里的引用也是示例（Jekyll 仍然会渲染它，但不指向真实文件），要剔除
const LINK_RE = /\{\{-?\s*['"](\/[^'"]*)['"]\s*\|\s*relative_url\s*-?\}\}/g;
const stripComments = (s) => s.replace(/<!--[\s\S]*?-->/g, "");

const linkSources = [
  ...guideFiles,
  ...walk(ROOT).filter(
    (x) => path.dirname(x) === ROOT && x.endsWith(".md") && !x.endsWith("README.md")
  ),
];

let linkCount = 0;
for (const p of linkSources) {
  const f = rel(p);
  const src = stripComments(read(p));
  let m;
  LINK_RE.lastIndex = 0;
  while ((m = LINK_RE.exec(src)) !== null) {
    linkCount++;
    const target = m[1];
    if (target.startsWith("/assets/") || target.startsWith("/tools/")) {
      // 静态文件：核对磁盘上是否存在
      const local = path.join(ROOT, target.replace(/^\//, ""));
      if (!fs.existsSync(local)) E(f, `引用了不存在的静态文件：${target}`);
      continue;
    }
    if (!knownUrls.has(target)) {
      const hint = knownUrls.has(target.replace(/\/$/, ".html"))
        ? `（写成 ${target.replace(/\/$/, ".html")} 才是对的）`
        : "";
      E(f, `链接目标 ${target} 在站点里不存在 —— 生成后会是 404 ${hint}`);
    }
  }
}

// 6.4 数据驱动的导航
// ------------------------------------------------------------
// 顶部导航与侧边栏的地址来自 _data/*.yml，模板里写的是
// {{ item.url | relative_url }}（变量而非字面量），6.3 抓不到。
// 所以这里直接读数据文件，逐个核对目标页面是否存在。
// 这正是「改了 permalink 或改了 slug，却忘了同步菜单」这类错误的拦截点。
// ------------------------------------------------------------
function loadData(name) {
  const p = path.join(ROOT, "_data", name);
  if (!fs.existsSync(p)) return null;
  if (!yaml) return null;
  try {
    return yaml.load(read(p));
  } catch (e) {
    E(`_data/${name}`, `YAML 解析失败：${e.message}`);
    return null;
  }
}

function checkNavTarget(label, url) {
  if (!url) return;
  if (knownUrls.has(url)) return;
  const alt = String(url).replace(/\/$/, ".html");
  const hint = knownUrls.has(alt)
    ? `（写成 ${alt} 才是对的）`
    : "（站点里没有这个地址：页面不存在，或者少了 permalink）";
  E(label, `导航指向 ${url}，但目标不存在 ${hint}`);
}

const navItems = loadData("site_nav.yml");
if (Array.isArray(navItems)) {
  if (navItems.length === 0) W("_data/site_nav.yml", "顶部导航是空的");
  for (const item of navItems) checkNavTarget("_data/site_nav.yml", item.url);
}

const stageItems = loadData("stages.yml");
if (Array.isArray(stageItems)) {
  if (stageItems.length === 0) W("_data/stages.yml", "阶段攻略没有任何条目");
  for (const s of stageItems) {
    if (!s.slug) {
      E("_data/stages.yml", `条目「${s.name || "?"}」缺少 slug`);
      continue;
    }
    checkNavTarget("_data/stages.yml", `/stages/${s.slug}/`);
  }
}

const pets = loadData("pets.yml");
if (pets && Array.isArray(pets.items)) {
  for (const it of pets.items) checkNavTarget("_data/pets.yml", it.url);
}

// ============================================================
// 7. 其他
// ============================================================
if (fs.existsSync(path.join(ROOT, "CNAME"))) {
  W("CNAME", "仓库里存在 CNAME 文件。官方文档明确：它不会自动添加或移除自定义域名，必须去 Settings → Pages 里配置");
}

if (!fs.existsSync(path.join(ROOT, ".gitignore"))) {
  W(".gitignore", "不存在，_site/ 等产物可能被提交进仓库");
}

if (!fs.existsSync(path.join(ROOT, "Gemfile.lock"))) {
  const autoCommit =
    fs.existsSync(WF) && /Commit Gemfile\.lock on first run/.test(read(WF));
  if (autoCommit) {
    W(
      "Gemfile.lock",
      "尚未生成 —— 这是正常的。首次推送到 main 之后，工作流会自动把它提交回仓库，你不需要手动操作"
    );
  } else {
    W(
      "Gemfile.lock",
      "尚未提交，且工作流里没有自动提交步骤。请把 Actions 日志里打印出的内容保存为本文件并提交"
    );
  }
}

// ============================================================
// 输出
// ============================================================
const guideCount = guides.filter((g) => !g.isIndex).length;
const indexCount = guides.length - guideCount;

console.log("");
console.log("游戏攻略站 · 本地预检");
console.log("=".repeat(52));
console.log(`扫描到 ${guideCount} 篇攻略、${indexCount} 个分类索引页`);
if (supported) {
  console.log(`版本库：current = ${currentVersion ?? "?"}，supported = [${supported.join(", ")}]`);
}
console.log("");

if (!yaml) {
  console.log("!! 未安装 js-yaml —— YAML 深度校验已跳过。请先运行： npm install");
  console.log("");
}

if (warnings.length) {
  console.log(`警告 ${warnings.length} 条（不阻塞构建，但建议处理）：`);
  for (const w of warnings) console.log(`  · ${w.file} —— ${w.msg}`);
  console.log("");
}

if (errors.length) {
  console.log(`错误 ${errors.length} 条（这些会导致构建失败或站点错乱）：`);
  for (const e of errors) console.log(`  x ${e.file} —— ${e.msg}`);
  console.log("");
  console.log("预检未通过。修掉上面这些再推送到 GitHub。");
  // 注意：这里不能用 process.exit(1)。
  // Node 在 stdout 不是终端（被管道、子进程、CI 捕获）时，
  // process.exit() 会截断尚未刷出的输出 —— 调用方只能收到空输出和一个非零码，
  // 完全看不到错在哪。用 exitCode 让进程自然退出，输出才会被完整写出。
  process.exitCode = 1;
} else {
  console.log(`OK: ${guideCount} 篇攻略全部通过`);
  console.log("");
  console.log("提醒：这只是近似校验。最终以 GitHub Actions 的构建结果为准。");
  process.exitCode = 0;
}
