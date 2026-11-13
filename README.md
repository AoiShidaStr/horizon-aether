# The Aether for Horizon

A Horizon port of [The Aether](https://github.com/The-Aether-Team/The-Aether)
(LGPL-3.0): sky islands, their ores and gear, and the mod's three bosses.

This is a **clean-room reimplementation** written from public behaviour
descriptions (the Aether wiki) and Horizon's docs. No upstream code, asset,
model, sound or data file is copied; all textures are procedural placeholders
from `tools/gen_content.py`. See `NOTICE.md`. The port itself is MIT
(`LICENSE`).

## What is here

| Part | Contents |
| --- | --- |
| `aether.hmod` (`side = "both"`) | 13 blocks (aether grass, aether dirt, holystone, mossy holystone, icestone, aercloud, golden aercloud, ambrosium/zanite/gravitite ore, skyroot planks, skyroot crafting table, incubator), 34 items (ambrosium shard, zanite gemstone, enchanted gravitite, skyroot stick, swet jelly, blue berry, white apple, healing stone, golden amber, golden feather, cloud parachute, valkyrie lance, lightning sword, phoenix bow, skyroot/zanite/gravitite tools, zanite/gravitite armour), 3 boss entity types, loot tables, mining tags, 9 recipes, creative tab, en_us + fr_fr |
| `aether.hnmod` | The three bosses' goals (chase + melee with per-boss reach, cooldown and speed), their box and daylight-burning rule, the Slider's immunity to projectiles, the Sun Spirit's immunity to fire, and no drowned conversion |

The bosses are Horizon entity types on the `minecraft:zombie` template (the
content API's living-mob template), given their own attributes, size and
goals:

- `aether:slider` — 100 HP, slow wide blows (reach 10.84²), arrow-proof.
- `aether:valkyrie_queen` — 120 HP, fast blows, burns in daylight like an
  undead.
- `aether:sun_spirit` — 80 HP, fire-proof, does not burn in daylight.

## Install

Both halves use the id `aether`.

1. `aether.hmod` in `horizon-mods/` and `mod.aether:true` in
   `horizon-mods.txt`.
2. `aether.hnmod` in `horizon-native-mods/`; rebuild the game with the
   launcher (**Mods** page, or `horizon-launcher native-build mods/aether --trust-native-code`;
   a dedicated server needs `--server-output <dir>`).
3. Server and clients need the same `.hmod` (the mod list compares it).

```
/summon aether:slider
/summon aether:valkyrie_queen
/summon aether:sun_spirit
/give @s aether:zanite_pickaxe
```

## Build

```sh
python tools/gen_content.py    # write/reset the content JSON and textures
python tools/pack.py           # target/aether.hmod and target/aether.hnmod
sh tools/vps_sync.sh           # copy + stage on the build VPS, then:
# on the VPS, in /opt/build/wt/aether:
#   CARGO_TARGET_DIR=/opt/build/target cargo test -p mod-aether
#   CARGO_TARGET_DIR=/opt/build/target cargo check -p horizon-native-game
#   CARGO_TARGET_DIR=/opt/build/target cargo build -p horizon-native-game --no-default-features
```

The native crate is pinned to Horizon `a85af177a82504f357ff10d5d40d0b7230e2ac32`.

## Done / Missing

Done (checked on the build VPS against Horizon `a85af177a`):

| Check | State |
| --- | --- |
| `cargo test -p mod-aether` | 5 passed, 0 failed |
| `cargo check -p horizon-native-game` (client flavour) | finished, exit 0 |
| `cargo build -p horizon-native-game --no-default-features` (dedicated server engine with the mod) | finished, exit 0 |

- Content mod: blocks, items, ores with drops, recipes, loot, tags, creative
  tab, two languages, procedural textures. Packs to `target/aether.hmod`
  (63 824 bytes).
- Native mod: goals, sizes, immunities, no conversions; unit tests for the
  boss table and the damage-type sets. Packs to `target/aether.hnmod`
  (7 837 bytes).
- VPS scripts in `tools/` (`vps_sync.sh` copies and stages, `vps_stage.sh`
  reproduces the launcher's native staging).

Missing (honest list):

- **No Aether dimension and no glowstone portal.** Horizon's content API has
  no data-driven dimension in this revision, and a native dimension needs far
  more than one session; the islands are not generated anywhere yet. This is
  the biggest gap: today the mod adds content to the overworld.
- **No custom models, textures or animations for the bosses.** They use the
  zombie template's model and texture. The native API can draw a mob
  (`native_mob_submit`), but no model/geo was written.
- **No sounds** (upstream's audio is not copied; original placeholders were
  not made).
- Boss abilities beyond melee (Slider charge, Queen lances, Sun Spirit fire
  attacks) are not implemented; only their melee, immunities and size.
- Dungeons, accessories (parachutes, pendants), aether mobs other than the
  three bosses, and the Aether's own progression are absent.
- `cargo horizon-mod check` was not run: the tool is not installed on the
  build PC or the VPS.
- Not yet smoke-tested in a running game: the native half reached
  compile/test level only. In particular the content definitions (block/item
  templates, entity types, loot) were not loaded by a running server yet.

Status: **partial**.
