#!/usr/bin/env bash
# Rebuild site from Facebook Page posts; commit+push only if content changed.
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py >/dev/null
# ignore pure timestamp churn: compare without "Last updated" line and sitemap lastmod
if git diff --quiet -I 'Last updated' -I '<lastmod>' -- . && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  git checkout -- index.html sitemap.xml 2>/dev/null || true
  echo "no changes"; exit 0
fi
git add -A
git -c user.name=phraison28-sudo -c user.email=phraison28-sudo@users.noreply.github.com commit -qm "Auto update $(date -u +%Y-%m-%dT%H:%MZ)"
git push -q origin main
echo "pushed"
