# 游戏攻略站（Jekyll + GitHub Pages）

用 Jekyll 4 + just-the-docs 主题搭建的攻略站，托管在 GitHub Pages 上，由 GitHub Actions 自动构建。
**本机不需要安装 Ruby** —— 构建全部在云端完成，本地只用编辑器写 Markdown。

核心特点：**每篇攻略标注适用的游戏版本，游戏更新后只需改一处，全站自动标记出过期攻略。**

---

## 一、目录结构

```
game-guides/
├── _config.yml                     ← 站点全局配置（只有换域名/换仓库时才需要改）
├── Gemfile                         ← 依赖与主题版本锁（重要，别删）
├── index.md                        ← 首页
├── versions.md                     ← /versions/ 按版本查攻略
├── outdated.md                     ← /outdated/ 待复核清单（自动生成）
├── _data/
│   └── versions.yml                ← 版本库：全站「是否过期」的唯一真源
├── _guides/                        ← 所有攻略都放这里
│   ├── boss/index.md               ← 分类页（父页面）
│   ├── boss/shadow-tree.md         ← 攻略正文
│   ├── mode/index.md
│   ├── mode/speedrun-basics.md
│   ├── system/index.md
│   └── system/settings.md
├── _includes/
│   ├── version_badge.html          ← 版本徽章（绿=有效 / 红=可能过期）
│   └── guide_meta.html             ← 攻略头部元信息条
├── _layouts/guide.html             ← 攻略版式
├── _sass/custom/custom.scss        ← 自定义样式（主题升级不会覆盖）
├── assets/images/guides/           ← 攻略配图
├── tools/precheck.mjs              ← 本地预检脚本
├── .gitattributes                  ← 统一换行符为 LF（跨平台协作防 diff 噪音）
└── .github/workflows/pages.yml     ← 自动构建 + 部署
```

---

## 二、一次性设置

### 第 1 步：在 GitHub 上建仓库

1. 打开 github.com → 右上角 **+** → **New repository**
2. Repository name 填你想起的名字，例如 `game-guides`
3. 选 **Public**（Pages 在免费账号下只对公开仓库开放）
4. **不要**勾选 "Add a README file"，直接 **Create repository**

### 第 2 步：把 Pages 的构建来源设成 GitHub Actions（必须最先做）

仓库页面 → **Settings** → 左侧 **「Code, planning, and automation」** 分组下的 **Pages** →
**Build and deployment** → **Source** 下拉框选 **GitHub Actions**。

> 这一步必须最先做。否则第一次构建时 `configure-pages` 会报
> `Get Pages site failed`，因为仓库还没有开启 Pages。

### 第 3 步：把本项目文件传上去

两种方式，选一种即可。

#### 方式 A · 网页上传（不用配任何凭据，推荐先用这个）

1. 在仓库页面点 **Add file → Upload files**
2. 把本项目的**所有文件和文件夹**拖进去（`_config.yml`、`Gemfile`、`index.md`、`_guides/`、`_data/`、`_includes/`、`_layouts/`、`_sass/`、`assets/`、`tools/`、`package.json`、`versions.md`、`outdated.md`）
3. 点 **Commit changes**

⚠️ **有两处网页上传会漏掉，必须手动补**（网页拖拽会跳过以 `.` 开头的文件）：

- **`.github/workflows/pages.yml`** —— 没有它就不会自动构建
  做法：**Add file → Create new file**，文件名框里输入 `.github/workflows/pages.yml`
  （输入斜杠会自动建目录），把文件内容粘进去，Commit
- **`.gitignore`** —— 可选但建议补
  做法同上，文件名输入 `.gitignore`

`Gemfile.lock` 不用传，见第五步。

#### 方式 B · 本地 git 推送

先探测本机 git 有没有凭据助手（有的话首次 push 会弹浏览器授权）：

```bash
git config --get credential.helper ; git credential-manager --version
```

有输出 → 可以走这条路；没有任何输出 → 走方式 A，或用 token（见第六节）。

```bash
cd 项目目录
git config --global user.name  "你的名字"
git config --global user.email "你的邮箱"
git init -b main
git add .
git commit -m "初始化攻略站"
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

---

## 三、日常写作：新增一篇攻略

1. 在 `_guides/` 下选一个分类目录（`boss` / `mode` / `system`），新建一个 `.md` 文件
   **文件名不用带日期**，用英文小写短横线，例如 `nightmare-king.md`
2. 文件开头必须写 front matter：

```yaml
---
title: "夜魇之王：无伤打法"      # 标题。含半角冒号时整体加引号
parent: BOSS 攻略               # 必须精确匹配某个分类页的 title
nav_order: 30                   # 同级的排序

game_version: "2.4"             # 适用版本。必须加引号！
mode: "boss"
difficulty: "噩梦"
tags: ["无伤", "机制"]
last_modified_date: 2026-09-23
---
```

3. 正文直接用 Markdown 写。几个常用写法：

```markdown
* TOC
{:toc}

## 小节标题

表格、列表、代码块都正常用。

{: .tip }
想强调的技巧，用这个提示框。

{: .outdated }
某一段在某版本之后不适用时，用这个红色提示框。
```

4. 本地跑一次预检，再提交：

```bash
npm install     # 只需第一次
npm run check
```

看到 `OK: N 篇攻略全部通过` 再提交。

### 图片怎么放

图片放 `assets/images/guides/<文章文件名>/` 下，正文里**必须**这样引用：

```markdown
![一阶段站位]({{ '/assets/images/guides/shadow-tree/01-站位.png' | relative_url }})
```

`relative_url` 会自动拼上正确的路径前缀。**直接写 `/assets/...` 或完整网址，将来换域名就会 404。**

### 内链怎么放

```markdown
[BOSS 攻略]({{ '/guides/boss/' | relative_url }})
[幽影树打法]({{ '/guides/boss/shadow-tree/' | relative_url }})
```

规律：攻略的网址就是 `_guides/` 下的目录层级，`_guides/boss/shadow-tree.md` → `/guides/boss/shadow-tree/`。

### 一键发布：`npm run publish`

不想记上面那串命令的话，用这一个：

```bash
npm run publish                                  # 自动生成提交信息
npm run publish -- -m "改了幽影树攻略"            # 自己写提交信息
npm run publish -- --dry-run                     # 干跑：只预检，不提交不推送
npm run publish -- --no-watch                    # 推完就结束，不跟踪构建
```

它按顺序做五件事：

| 步骤 | 做什么 | 失败会怎样 |
| --- | --- | --- |
| 0 | 检查是否在 git 仓库、列出改动文件 | 不是 git 仓库就停 |
| 1 | 跑 `tools/precheck.mjs` | **预检不通过直接中止，不会推坏内容上去** |
| 2 | `git add -A` + `git commit` | — |
| 3 | `git pull --rebase`（关键！） | 冲突时提示你手动解决后再跑一次 |
| 4 | `git push` | — |
| 5 | 查询构建结果，成功就打印站点地址 | API 限流时优雅退化成打印 Actions 链接 |

第 3 步的 `pull --rebase` 是必须的：工作流里的机器人会把 `Gemfile.lock` 提交回仓库，
你的本地克隆会落后一个 commit，直接 push 会被拒绝。

第 5 步用 GitHub 的公开 API 查询，**未登录状态下每小时只能查 60 次**，
所以频繁发布会看到「触发了限流」的提示——这不是错误，去 Actions 页面看即可。

### 每天的流程长什么样

```bash
# 1. 写内容（改 Markdown、加攻略、改 _data/versions.yml）
# 2. 发布
npm run publish -- -m "新增 XX 攻略"
# 3. 等它打印出「✓ 构建与部署成功」和站点地址
```

---

## 四、游戏更新后怎么维护（这是本站的核心机制）

游戏发新版本时，**你只需要改 `_data/versions.yml`**：

```yaml
current: "2.5"
supported: ["2.5", "2.4", "2.3"]     # 把不再支持的版本号从这里删掉
history:
  - id: "2.5"
    name: "2.5 版本"
    released: 2026-09-20
    status: current
  # ...下面照旧
```

改完推送，全站会自动重算：

- 所有 `game_version` 不在 `supported` 里的攻略，页顶徽章**自动变红**
- `/outdated/` 页面**自动列出**这些攻略，形成待复核清单
- `/versions/` 页面的分组也跟着变

**你不需要逐篇去改文章。** 复核完某篇之后，只要把它的 `game_version` 改成实际适用的版本，它就会自动从待复核清单里消失。

---

## 五、推送之后：从 Actions 到站点上线

这一节把「代码推上去之后到底会发生什么」逐步写清楚。如果你卡住的地方是按了提交之后不知道下一步点哪里，看 §5.1 ~ §5.4；如果是要处理 `Gemfile.lock`，直接看 §5.5。

### 5.1 推送成功后你会看到什么

只要仓库的 `main` 分支上出现了新 commit，GitHub 就会自动跑一次构建。确认方法：

1. 打开 `https://github.com/<用户名>/<仓库名>`
2. 点顶部横排最后一个页签 **Actions**
3. 左侧列表里会出现一条记录，名字是 **Build & Deploy Jekyll site**，前面有一个黄色转圈小圆点 = 正在跑

> **说明**：如果你用的是「网页 Upload files」方式，提交本身就等于推送，所以这里会立刻出现记录。
> **如果 Actions 页签里空空如也**，说明 `.github/workflows/pages.yml` 这个文件没上传成功——
> 它是以 `.` 开头的目录，网页拖拽会跳过它，必须用 Add file → Create new file 手动建（见 §2 方式 A）。

### 5.2 怎么看构建结果

点进那条记录（列表里的标题），进入这次运行的详情页。左侧会列出本次运行包含的 **job**：

| 情况 | 你会看到几个 job | 含义 |
| --- | --- | --- |
| 你推到了 `main` | 两个：**build** 和 **deploy** | 先构建、再部署 |
| 你在 PR 里（别的分支） | 只有一个：**build** | 只做校验，**不会**动线上站点 |

**怎么判断成功**：job 名左边是绿色对勾 ✅ = 通过；红色叉 ❌ = 失败。

**失败了怎么看原因**：

1. 点左侧那个红色的 job 名（例如 `build`）
2. 右侧会出现一行行步骤，出问题的那一步会展开成红色
3. 点那一步，就能看到完整日志。翻到日志最下面，错误通常在最末尾
4. 拿到错误原文，对照 **§9 常见报错排查** 那张表修

日志里看到这些就是好兆头：

```
done in 2.4 seconds
Generating... /guides/boss/shadow-tree/
```

**每次改完代码重新推，都会重新跑一遍**，不需要手动点任何按钮。

### 5.3 怎么让站点正式上线

**如果你直接推到了 `main`**：不用做任何事。上面 §5.1 那次运行里会自动出现 `deploy` job，跑完站点就上线了。

**如果你是走 PR 流程（推荐，更安全）**：

1. 打开仓库首页 → 点顶部 **Pull requests** 页签
2. 找到你那个 PR，先确认上面显示 **All checks have passed**（说明 build 绿了）
3. 点绿色的 **Merge pull request** 按钮
4. 再点 **Confirm merge**
5. 合并这个动作本身又是一次对 `main` 的推送 → 自动触发新一轮运行 → 这次会带上 `deploy` job

`deploy` 跑完大约 1 分钟，站点就上线了。

### 5.4 站点地址在哪看

三种地方都能看到：

1. **最直接**：仓库 → **Settings** → **Pages**，页面顶部会显示地址，旁边有 **Visit site** 按钮
2. 在 Actions 里点进那次运行 → 点左侧 **deploy** job → 里面有一行 `page_url`，就是线上地址
3. 自己拼：
   - **用户站点**（仓库名 = `<用户名>.github.io`）：`https://<用户名>.github.io/`
   - **项目站点**（仓库名是别的）：`https://<用户名>.github.io/<仓库名>/`

> 打开后如果是 404：先等 2 分钟（首次部署稍慢），再去 §5.2 确认 build 和 deploy 都是绿的。
> 如果两个 job 都绿但页面没样式，是 `_config.yml` 里 `url:` 填错了，见 §8。

### 5.5 Gemfile.lock：现在你什么都不用做

先说明白：**`Gemfile.lock` 缺着，站点照样能正常上线**，它只是「把依赖版本钉死」的加固项。
所以这一步不该成为卡住你的地方。

因为本机没有 Ruby，这个文件没法在本地生成，只能由 CI 生成。工作流已经改成**自动完成**：

**它做什么**：第一次在 `main` 上构建时，工作流会把 CI 解析出的 `Gemfile.lock` 自动提交回你的仓库。
之后就有了，不需要再做第二次。

**你怎么确认它成功了**：

1. Actions → 点进那次在 `main` 上的运行 → 点左侧 **build**
2. 找到名为 **Commit Gemfile.lock on first run** 的步骤，展开
3. 看到提交成功的输出 = 完成
4. 或者更省事：回仓库首页看文件列表，根目录多出了 `Gemfile.lock` 文件，就是成了

**一个需要知道的副作用**：这是机器人提交的一个 commit，会让你的**本地克隆**落后一个版本。
如果你以后用本地 `git push`，先执行一次 `git pull` 再推，否则会被拒绝。
（用网页上传的人不会遇到这个问题。）

**前提：仓库要允许工作流写入**（这一步很容易漏，漏了自动提交会静默失败）

新仓库的默认设置是**只读**，即使工作流里写了 `contents: write` 也无法提权，`git push` 会失败。
去开一下（只需一次）：

> 仓库 → **Settings** → 左侧 **Actions** → **General** → 拉到最下面
> **Workflow permissions** → 选 **Read and write permissions** → **保存**
> 成功后页面顶部会显示 `Default workflow permissions settings saved.`

**如果还是失败了**（比如仓库开了分支保护）：工作流会在 Actions 里打出黄色警告，
**构建和部署都不受影响**，站点照常上线。你想手动补的话：

1. Actions → 那次运行 → **build** job → 展开 **Print resolved Gemfile.lock (fallback record)**
2. 复制展开区域里的全部内容
3. 仓库首页 → **Add file** → **Create new file**
4. 文件名输入 `Gemfile.lock`，把内容粘进编辑区，**Commit changes**

（这个 `Gemfile.lock` **不要**加进 `.gitignore`。）

### 5.6 在这一步卡住的常见情况

| 现象 | 原因 | 怎么办 |
| --- | --- | --- |
| Actions 页签里没有运行记录 | workflow 文件没上传 | 用 Create new file 手动建 `.github/workflows/pages.yml`（见 §2 方式 A） |
| 运行一直转圈超过 10 分钟 | 队列排队或卡住 | 点进运行页右上角 **Cancel workflow**，然后重新推一次（随便改个字符再提交也行） |
| 找不到 `deploy` job | 你推的不是 `main` 分支 | 默认 `deploy` 只在 `main` 上跑；去 Pull requests 页签把 PR 合并掉 |
| 找不到 `Commit Gemfile.lock` 这一步 | 你还没推到 `main`，或 workflow 文件是旧版 | 推到 `main` 后才会执行；确认 workflow 文件里这段存在 |
| `git push` 被拒绝，提示 behind | 机器人已经提交过一次 | 先 `git pull` 再 `git push` |
| 构建失败提示 `Get Pages site failed` | 没做 §2 第 2 步 | Settings → Pages → Source 选 `GitHub Actions` |
| 打开链接 404 | 首次部署还没完成 / 地址拼错 | 等 2 分钟；地址规则见 §5.4 |

---

## 六、如果要用 token（可选）

只有当你想在本地一键 `git push`、而本机 git 又没带凭据助手时才需要。

1. GitHub → Settings → Developer settings → **Personal access tokens → Fine-grained tokens**
2. **不要**用 classic token
3. Repository access 只勾这一个仓库
4. Permissions 只要 **Contents: Read and write**
5. Expiration 设 **7 天**

用的时候把它当作密码：

```bash
git push https://<你的用户名>@github.com/<用户名>/<仓库名>.git main
# 提示输入密码时，粘贴 token
```

用完立刻去 GitHub 把 token 吊销。

> 更好的做法：**不要把 token 明文写进任何文件或对话里。**
> 如果确实需要保存，存在仓库外的独立文件并尽快删除。

---

## 七、绑定自定义域名（可选，以后再做）

1. 仓库 → **Settings → Pages → Custom domain**，填你的域名，例如 `guide.example.com`，点 **Save**
2. 去你的域名服务商加 DNS 记录：
   - 子域名（如 `guide.example.com`）→ 加一条 **CNAME**，值填 `<你的用户名>.github.io`
     **不要**带仓库名，也**不要**填 `*.pages.github.io`
   - 根域名（如 `example.com`）→ 加 4 条 **A** 记录：
     `185.199.108.153`、`185.199.109.153`、`185.199.110.153`、`185.199.111.153`
3. DNS 生效最长要 24 小时。生效后回 Settings → Pages 勾上 **Enforce HTTPS**（这个选项也要等 DNS 生效后才可用，最长同样 24 小时）
4. 生效后把 `_config.yml` 里的 `url:` 改成 `https://guide.example.com`，提交

⚠️ **不要**在仓库里放 `CNAME` 文件。GitHub 官方文档明确写了：
*仓库里的 CNAME 文件不会自动添加或移除自定义域名，必须通过仓库设置或 API 配置。*
照老教程放 CNAME 文件是无效操作。

---

## 八、换仓库形态 / 换域名

**只改 `_config.yml` 里的 `url:` 这一行**，`baseurl` 永远不要在 `_config.yml` 里写。

| 形态 | 访问地址 | `url:` 该填 |
| --- | --- | --- |
| 用户站点 | `https://<用户名>.github.io/` | `https://<用户名>.github.io` |
| 项目站点 | `https://<用户名>.github.io/<仓库名>/` | `https://<用户名>.github.io` |
| 自定义域名 | `https://你的域名` | `https://你的域名` |

`baseurl`（项目站点需要的 `/仓库名`）由 Actions 里的 `configure-pages` 自动注入到
`--baseurl` 参数，所以你不用管。

---

## 九、常见报错排查

构建失败时，去仓库 **Actions** 页签点进那次运行，看是哪个 job、哪一步红的，
再点开那一步的日志，按下面的表对照。

| 日志里的关键词 | 原因 | 怎么修 |
| --- | --- | --- |
| `Liquid syntax error` | 正文里 `{% %}` 或 `{{ }}` 漏闭合 | 检查报错文件名对应位置；想原样显示 `{{ }}` 要用 `{% raw %}` 包住 |
| `YAML Exception ... mapping values are not allowed in this context` | front matter 里标题含半角冒号 | 把 title 整体加引号，或把 `:` 换成全角 `：` |
| `could not find layout` | 写了不存在的 layout | 本项目的攻略统一用 `guide`（已由 `_config.yml` 的 defaults 自动指定） |
| `Dependency Error ... could not be found` | `_config.yml` 的 `plugins:` 里列了 Gemfile 中没有的插件 | 两边保持一致 |
| `Get Pages site failed` | 没有先做「第 2 步」 | 去 Settings → Pages 把 Source 设为 GitHub Actions |
| `Error: Deployment failed, try again later` | 环境或权限问题 | 检查 Settings → Pages 的 Source；确认 workflow 里 `id-token: write` 与 `pages: write` 都在 |
| `done in ... seconds` 但页面 404 | `url` / `baseurl` 配错 | 对照第八节；`url` 只写到域名 |
| 页面在，但没有样式 | 同上，或主题没装上 | 确认 `Gemfile` 与 `_config.yml` 里都是 `just-the-docs` |

**改动前先开 PR**：把改动推到非 `main` 分支并开 Pull Request 时，工作流**只构建、不部署**，
构建失败碰不到线上站点。确认 CI 变绿了再合并到 `main`。

---

## 十、本地预检脚本说明

`tools/precheck.mjs` 会在推送前检查：

- 所有攻略的 front matter 是否合法、必填字段（`title` / `game_version` / `mode` / `difficulty`）是否齐全
- `game_version` 是否**写成了字符串**（不加引号会被 YAML 当浮点数，`1.10` 会变成 `1.1`）
- `game_version` 是否真的存在于 `_data/versions.yml`（防版本号拼错）
- `parent` 是否精确匹配到了某个分类页的 `title`（这是导航最容易坏的地方）
- 全站 `title` 是否唯一（just-the-docs 的硬性要求）
- 每个文件的 Liquid 分隔符是否配对
- `_config.yml` / `_data/versions.yml` 是否可解析、`url` 是否正确、有没有误写 `baseurl`
- 工作流里有没有误用 `actions/jekyll-build-pages`（它会忽略 Gemfile、退回 Jekyll 3.10.0）

```bash
npm install     # 第一次
npm run check
```

> **注意**：这只是近似校验。Jekyll 实际用的是 Ruby 的 YAML 解析器和 Liquid 模板引擎，
> 本脚本用 js-yaml 与字符串计数做近似判断。**最终以 GitHub Actions 的构建结果为准。**

---

## 十一、以后想在本地预览（可选）

现在这套流程完全不需要本地 Ruby。如果你以后想要「改一下刷一下」的即时预览：

1. 装 **Ruby 3.3.x with DevKit**（RubyInstaller）
2. `gem install bundler`
3. 在项目根目录 `bundle install`
4. `bundle exec jekyll serve --livereload`

注意事项：

- 本地预览时用 `bundle exec jekyll serve --baseurl ""`，**不要**把 baseurl 写进 `_config.yml`
- 如果报 `cannot load such file -- webrick`，把 `Gemfile` 里 `gem "webrick", "~> 1.8"` 的注释去掉
- 如果 `Gemfile.lock` 是在 Windows 上生成的，里面会有 `x86_64-mingw-ucrt` 平台，
  与 CI 的 Linux 不匹配，需要在项目里执行 `bundle lock --add-platform x86_64-linux`

---

## 十二、开始之前要改的地方

本项目里是占位内容，正式用之前请替换：

| 位置 | 现在的内容 | 改成 |
| --- | --- | --- |
| `_config.yml` | `title: 游戏名 攻略站` | 你的站点名 |
| `_config.yml` | `description:` | 你的站点描述 |
| `_config.yml` | `url: https://example.github.io` | 见第八节 |
| `_data/versions.yml` | 2.1 ~ 2.4 的示例版本 | 你的游戏真实版本号 |
| `_guides/**` | 4 篇示例攻略 | 你的真实攻略（或直接删掉重写） |
| `index.md` | 首页文案 | 按需调整 |
