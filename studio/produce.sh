#!/bin/bash
# Bake, render and package one or more islands:  studio/produce.sh phoenix releaf ...
# Writes assets/world/<slug>.glb, <slug>.webp (2K light atlas), <slug>-1k.webp, <slug>-hero.webp, <slug>-card.webp.
set -u
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
for slug in "$@"; do
  echo "== $slug"
  "$BLENDER" -b -P studio/run.py -- "$slug" all 2>&1 | grep -E "\[kit\]|Error|Traceback|line [0-9]|rror:" 
  [ -f "studio/out/${slug}_bake.png" ] || { echo "!! no bake for $slug"; continue; }
  cwebp -quiet -q 86 -resize 2048 2048 "studio/out/${slug}_bake.png" -o "assets/world/${slug}.webp"
  cwebp -quiet -q 84 -resize 1024 1024 "studio/out/${slug}_bake.png" -o "assets/world/${slug}-1k.webp"
  cwebp -quiet -q 84 -resize 1800 1350 "studio/out/${slug}_hero.png" -o "assets/world/${slug}-hero.webp"
  cwebp -quiet -q 82 -resize 960 720 "studio/out/${slug}_hero.png" -o "assets/world/${slug}-card.webp"
  ls -la assets/world/${slug}* | awk '{print $5, $9}'
done
echo "== done"
