#!/usr/bin/env node
// ============================================================
// 一条命令完成发布：预检 → 提交 → 推送 →（尽力）跟踪构建结果
// ------------------------------------------------------------
// 用法：
//   npm run publish                  # 自动生成提交信息
//   npm run publish -- -m "改了幽影树攻略"
//   npm run publish -- --dry-run     # 只跑预检和 git 状态，不提交不推送
//   npm run publish -- --no-watch    # 推完就结束，不跟踪 CI
// ============================================================

import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argv = process.argv.slice(2);
const dryRun = argv.includes("--dry-run");
const noWatch = argv.includes("--no-watch");
const msgIdx = argv.indexOf("-m");
const customMsg = msgIdx >= 0 ? argv[msgIdx + 1] : null;

const C = {
  dim: (s) => `\x1b[2m${s}\x1b[0m`,
  ok: (s) => `\x1b[32m${s}\x1b[0m`,
  warn: (s) => `\x1b[33m${s}\x1b[0m`,
  err: (s) => `\x1b[31m${s}\x1b[0m`,
  b: (s) => `\x1b[1m${s}\x1b[0m`,
};

function git(args, opts = {}) {
  return execFileSync("git", args, {
    cwd: ROOT,
    encoding: "utf8",
    stdio: opts.stdio || ["ignore", "pipe", "pipe"],
  });
}

function step(n, title) {
  console.log("");
  console.log(C.b(`[${n}] ${title}`));
}

function die(msg) {
  console.log("");
  console.log(C.err("✗ " + msg));
  process.exit(1);
}

// ------------------------------------------------------------
console.log(C.b("攻略站发布流程"));
console.log(C.dim("目录：" + ROOT + (dryRun ? "   （--dry-run 模式，不会提交或推送）" : "")));

// --- 0. 基本检查 -------------------------------------------------
step(0, "检查仓库状态");
let branch = "";
try {
  branch = git(["rev-parse", "--abbrev-ref", "HEAD"]).trim();
} catch {
  die("这里不是 git 仓库。请先确认你在 game-guides 目录下。");
}
console.log(`  当前分支：${branch}`);
if (branch !== "main") {
  console.log(
    C.warn(`  注意：当前不在 main 分支。推送到非 main 分支只会触发「构建校验」，不会部署上线。`)
  );
}

let status = "";
try {
  status = git(["status", "--porcelain"]).trim();
} catch {}

if (!status) {
  console.log(C.ok("  没有未提交的改动 —— 无需发布。"));
  process.exit(0);
}
const changed = status.split("\n").filter(Boolean);
console.log(`  检测到 ${changed.length} 处改动：`);
changed.slice(0, 20).forEach((l) => console.log(C.dim("    " + l)));
if (changed.length > 20) console.log(C.dim(`    ...另外 ${changed.length - 20} 处`));

// --- 1. 预检 -----------------------------------------------------
step(1, "本地预检（tools/precheck.mjs）");

// 直接在同一个进程里运行预检，不另起子进程。
//
// 为什么不用 execFileSync 起子进程：在受限环境下 node 再 spawn node 会报 EBUSY
// （子进程根本没被创建），此时 stdout 是空的、退出码非 0，
// 与「预检真的发现了错误」在表象上几乎一样 —— 会把本来能发布的改动误判成失败。
// 改成同进程运行后，既没有这个歧义，也更快。
//
// precheck.mjs 的契约是：打印报告 + 用 process.exitCode 表达成败。
// 所以这里先把它临时归零，跑完再读回来，然后把 exitCode 还原成发布流程自己的。
const keepExitCode = process.exitCode;
process.exitCode = 0;
await import("./precheck.mjs");
const precheckCode = process.exitCode;
process.exitCode = keepExitCode || 0;

if (precheckCode !== 0) {
  die("预检未通过。修掉上面的错误再发布（这才是它的意义）。");
}
console.log(C.ok("  预检通过"));

// --- 2. 提交 -----------------------------------------------------
step(2, "提交改动");
let commitMsg = customMsg;
if (!commitMsg) {
  const files = changed.map((l) => l.replace(/^\s*\S+\s+/, "").trim());
  const names = files.slice(0, 3).join(", ");
  commitMsg =
    files.length <= 3 ? `更新：${names}` : `更新 ${files.length} 个文件（含 ${names} 等）`;
}
console.log("  提交信息：" + commitMsg);

if (dryRun) {
  console.log(C.warn("  --dry-run：跳过 git add / commit / push"));
} else {
  git(["add", "-A"], { stdio: "inherit" });
  try {
    git(["commit", "-m", commitMsg], { stdio: "inherit" });
  } catch {
    die("提交失败（可能没有实际改动）。");
  }
}

// --- 3. 同步远端（机器人可能提交过 Gemfile.lock）-------------------
step(3, "同步远端");
if (dryRun) {
  console.log(C.warn("  --dry-run：跳过 git pull"));
} else {
  try {
    const out = git(["pull", "--rebase", "origin", branch]);
    console.log("  " + (out.trim() || "已是最新"));
  } catch (e) {
    const out = ((e.stdout || "") + "" + (e.stderr || "")).trim();
    console.log(C.warn("  pull --rebase 未完全成功，输出如下："));
    console.log("  " + out.split("\n").join("\n  "));
    die(
      "同步远端失败。如果是冲突：手动解决后执行 `git rebase --continue`，再重新运行 npm run publish。"
    );
  }
}

// --- 4. 推送 -----------------------------------------------------
step(4, "推送到 GitHub");
if (dryRun) {
  console.log(C.warn("  --dry-run：跳过 git push"));
} else {
  try {
    git(["push", "origin", branch], { stdio: "inherit" });
  } catch {
    die("推送失败。常见原因：远端有新提交（重跑本命令会自动 pull 后再推）、SSH 密钥失效。");
  }
  console.log(C.ok("  已推送"));
}

if (dryRun) {
  console.log("");
  console.log(C.ok("dry-run 完成。去掉 --dry-run 就会真正发布。"));
  process.exit(0);
}

// --- 5. 跟踪构建（尽力而为）--------------------------------------
if (noWatch) {
  console.log("");
  console.log("Actions 页面：https://github.com/" + remoteSlug() + "/actions");
  process.exit(0);
}

step(5, "跟踪构建结果");
const slug = remoteSlug();
if (!slug) {
  console.log(C.warn("  无法识别远端仓库地址，跳过跟踪。"));
  process.exit(0);
}

const sleep = (ms) => new Promise((s) => setTimeout(s, ms));
const UA = { "User-Agent": "publish-script", Accept: "application/vnd.github+json" };
let headSha = "";
try {
  headSha = git(["rev-parse", "HEAD"]).trim();
} catch {}

let announced = false;
for (let i = 0; i < 30; i++) {
  await sleep(8000);
  let runs;
  try {
    const r = await fetch(`https://api.github.com/repos/${slug}/actions/runs?per_page=5`, {
      headers: UA,
    });
    if (r.status === 403) {
      console.log(
        C.warn("  GitHub API 触发了限流（未认证每小时 60 次）。请自行到 Actions 页面查看：")
      );
      console.log("  https://github.com/" + slug + "/actions");
      process.exit(0);
    }
    if (r.status !== 200) throw new Error("HTTP " + r.status);
    runs = await r.json();
  } catch (e) {
    console.log(C.warn("  查询失败（" + e.message + "），请到 Actions 页面查看。"));
    process.exit(0);
  }
  const run = (runs.workflow_runs || []).find((x) => x.head_sha === headSha);
  if (!run) {
    if (!announced) {
      console.log(C.dim("  等待工作流被创建 ..."));
      announced = true;
    }
    continue;
  }
  console.log(`  run#${run.run_number}  ${run.status}/${run.conclusion || "-"}`);
  if (run.status === "completed") {
    console.log("");
    if (run.conclusion === "success") {
      console.log(C.ok("✓ 构建与部署成功"));
      console.log("");
      console.log("  站点地址：https://" + slug.split("/")[0] + ".github.io/" + slug.split("/")[1] + "/");
      console.log("  运行详情：" + run.html_url);
      console.log(C.dim("  （CDN 刷新通常还要 10~60 秒，页面没变就稍等一下再刷新）"));
    } else {
      console.log(C.err("✗ 构建失败：" + run.conclusion));
      console.log("  去看日志定位：" + run.html_url);
      process.exit(1);
    }
    process.exit(0);
  }
}
console.log(C.warn("  超时未等到结果，请到 Actions 页面查看：https://github.com/" + slug + "/actions"));

function remoteSlug() {
  try {
    const url = git(["remote", "get-url", "origin"]).trim();
    const m = url.match(/github\.com[:/]([^/]+)\/([^/]+?)(?:\.git)?$/);
    return m ? `${m[1]}/${m[2]}` : null;
  } catch {
    return null;
  }
}
