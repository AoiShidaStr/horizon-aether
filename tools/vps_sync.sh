#!/bin/sh
# From this PC: copy the mod's sources to the build VPS and stage them into a
# worktree of the Horizon clone at /opt/build/horizon.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VPS="root@<VPS>"
KEY="$HOME<SSH_KEY>"
ssh -o BatchMode=yes -i "$KEY" "$VPS" '
  mkdir -p /opt/build/mods/aether /opt/build/mods/aether/tools
  if [ ! -d /opt/build/wt/aether ]; then
    cd /opt/build/horizon && git worktree add --detach /opt/build/wt/aether
  fi
'
tar -C "$ROOT" --exclude=./target --exclude=./.build --exclude=__pycache__ -cf - . | \
  ssh -o BatchMode=yes -i "$KEY" "$VPS" 'tar --no-same-owner -C /opt/build/mods/aether -xf - && bash /opt/build/mods/aether/tools/vps_stage.sh'
