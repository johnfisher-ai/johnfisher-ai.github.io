#!/usr/bin/env bash
# Runs every check on the rendered site. From the repository root: bash tools/checks/run.sh
# Needs Java 11+, Node 18+ and a Chromium; set CHROMIUM to its path if Playwright has not installed one.
set -u
cd "$(dirname "$0")"
[ -d node_modules ] || npm install --no-audit --no-fund >/dev/null
DOCS="$(cd ../../docs && pwd)"
status=0
echo "== HTML validator"
java -jar node_modules/vnu-jar/build/dist/vnu.jar --skip-non-html --errors-only "$DOCS" || status=1
echo "== Links, anchors and page standards"
python3 sitecheck.py "$DOCS" || status=1
echo "== Accessibility (axe) and sideways scroll"
python3 -m http.server 8765 --directory "$DOCS" >/dev/null 2>&1 &
server=$!
sleep 1
node axe-check.mjs http://localhost:8765/ "$DOCS" ${CHROMIUM:-} || status=1
kill $server
exit $status
