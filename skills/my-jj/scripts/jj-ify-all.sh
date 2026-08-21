#!/usr/bin/env bash
# 批量把 git 仓库 jj 化（colocate）。
# 用法: jj-ify-all.sh [根目录...]   默认扫描 ~/ghq/github.com/*/*
# 规则: 有 .git 且无 .jj 的仓库才转换；jj git init --colocate 对脏工作区安全。
set -uo pipefail
if [ $# -gt 0 ]; then ROOTS=("$@"); else ROOTS=("$HOME"/ghq/github.com/*/); fi
[ ${#ROOTS[@]} -eq 0 ] && ROOTS=("$HOME"/ghq/github.com/*/)

converted=0; skipped=0; failed=0
for gitdir in $(find "${ROOTS[@]}" -maxdepth 3 -name .git -type d 2>/dev/null); do
  repo=$(dirname "$gitdir")
  [ -e "$repo/.jj" ] && continue
  if (cd "$repo" && jj git init --colocate >/dev/null 2>&1); then
    # 跟踪所有远端 bookmark，便于 jj git push
    (cd "$repo" && for b in $(jj bookmark list --all 2>/dev/null | grep -oE '^[^ ]+' | head -20); do
       jj bookmark track "$b" --remote=origin >/dev/null 2>&1
     done)
    echo "✓ jj 化: $repo"; converted=$((converted+1))
  else
    echo "✗ 失败: $repo"; failed=$((failed+1))
  fi
done
echo "--- 转换 $converted，跳过(已 jj) $skipped，失败 $failed"
