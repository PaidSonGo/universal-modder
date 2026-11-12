#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# Installs upstream REA for a local Sandbox Reply Lab bridge.
# Deliberately does not touch any application data or Android security settings.

if [[ "${PREFIX:-}" != *com.termux* ]]; then
  echo "This installer must run inside Termux." >&2
  exit 2
fi

if command -v termux-battery-status >/dev/null 2>&1; then
  level="$(termux-battery-status 2>/dev/null | python -c 'import json,sys; d=json.load(sys.stdin); print(d.get("percentage",100))' 2>/dev/null || echo 100)"
  charging="$(termux-battery-status 2>/dev/null | python -c 'import json,sys; d=json.load(sys.stdin); print(str(d.get("plugged","")).upper())' 2>/dev/null || true)"
  if [[ "$level" =~ ^[0-9]+$ ]] && (( level < 20 )) && [[ "$charging" != "PLUGGED_AC" && "$charging" != "PLUGGED_USB" && "$charging" != "PLUGGED_WIRELESS" ]]; then
    echo "Battery $level% and not charging. Connect power before building REA." >&2
    exit 3
  fi
fi

command -v git >/dev/null || { echo "Install git: pkg install git" >&2; exit 4; }
command -v node >/dev/null || { echo "Install supported Node.js: pkg install nodejs-lts" >&2; exit 4; }
command -v python >/dev/null || { echo "Install Python: pkg install python" >&2; exit 4; }
command -v npm >/dev/null || { echo "npm is missing; install a Termux Node.js package with npm" >&2; exit 4; }

node -e 'const v=process.versions.node.split(".").map(Number); if(!((v[0]===22&&v[1]>=19)||(v[0]===24&&v[1]>=11)||(v[0]>=26))){throw new Error("REA requires Node 22.19+, 24.11+, or 26+")}'

mkdir -p "$HOME/srl-upstream"
upstream="$HOME/srl-upstream/rea"
if [[ -e "$upstream" && ! -d "$upstream/.git" ]]; then
  echo "The target exists and is not a git checkout: $upstream" >&2
  exit 5
fi
if [[ ! -d "$upstream/.git" ]]; then
  git clone --depth=1 --branch main https://github.com/PaidSonGo/rea.git "$upstream"
else
  echo "Using existing checkout (no git reset, pull, or overwrite): $upstream"
fi

cd "$upstream"
test -f package-lock.json && test -f scripts/rea.mjs || {
  echo "REA checkout does not have expected files" >&2; exit 6;
}
echo "REA upstream version: $(node -p 'require("./package.json").version')"
echo "Installing pinned npm and REA dependencies"
npm exec --yes --package=npm@11.16.0 -- npm ci
npm exec --yes --package=npm@11.16.0 -- npm run build:termux
test -f dist/cli-runtime/cli.js || {
  echo "REA build did not produce CLI runtime" >&2; exit 7;
}
echo "REA runtime OK; launch the loopback bridge with:"
echo "python \"$HOME/srl-integration/integrations/sandbox-reply-lab/rea_local_server.py\" --rea-dir \"$upstream\""
