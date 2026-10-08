# 1. deinit（你已经做了，推荐加-f强制）
git submodule deinit -f notes

# 2. 手动清理core.worktree（解决这个warning）
git -C .git/modules/notes config --unset core.worktree

# 3. 删除父仓库内的模块缓存
rm -rf .git/modules/notes

# 4. git rm，删掉工作区目录 + 索引里的gitlink记录
git rm -f notes

# 5. 手动编辑 .gitmodules，删掉 [submodule "notes"] 这一段

# 6. 提交
git add .gitmodules
git commit -m "remove submodule notes"

