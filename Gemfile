# frozen_string_literal: true

source "https://rubygems.org"

# Jekyll 4.x
# 注意：不要改用 actions/jekyll-build-pages 这个 action —— 它跑的是容器内的
# github-pages gem，只会对仓库里的 Gemfile 打一条 warning 而不使用它，实际会
# 退回内置的 Jekyll 3.10.0，本文件里的所有锁版就都失效了。
# CI 走的是 ruby/setup-ruby + bundle exec jekyll build。
gem "jekyll", "~> 4.4.1"

# 主题：必须锁死具体版本。
# 官方迁移文档明确说明：未固定版本的主题会在下次构建时自动升级到最新版。
gem "just-the-docs", "0.12.0"

group :jekyll_plugins do
  gem "jekyll-sitemap"
  gem "jekyll-seo-tag"
  gem "jekyll-include-cache"
end

# Ruby 3.0 起 webrick 不再随标准库提供。
# 只有将来在本地跑 `bundle exec jekyll serve` 并报
# "cannot load such file -- webrick" 时，才需要取消下面这行的注释。
# gem "webrick", "~> 1.8"
