#!/usr/bin/env python3
"""Generate the Aether content half (blocks, items, entities, textures, lang).

Everything here is ORIGINAL: the JSON is written for Horizon's content API 0.2
and the textures are procedural placeholders drawn by this script (no asset of
the upstream Java mod is copied). See NOTICE.md.

Run: python tools/gen_content.py
"""
import hashlib
import json
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONTENT = os.path.join(ROOT, "content")
ID = "aether"

# ---------------------------------------------------------------------------
# Palettes (r, g, b) used by the placeholder textures.

BLOCKS = {
    # name: (template, palette, extra block properties, texture kind)
    "aether_grass": ("minecraft:grass_block", (126, 196, 96), {}, "grass"),
    "aether_dirt": ("minecraft:dirt", (128, 96, 66), {}, "noise"),
    "holystone": ("minecraft:stone", (176, 176, 168), {}, "stone"),
    "mossy_holystone": ("minecraft:mossy_cobblestone", (150, 170, 140), {}, "moss"),
    "icestone": ("minecraft:packed_ice", (150, 205, 240), {}, "ice"),
    "aercloud": ("minecraft:white_wool", (238, 244, 250), {"hardness": 0.2}, "cloud"),
    "golden_aercloud": ("minecraft:white_wool", (244, 214, 110), {"hardness": 0.2}, "cloud"),
    "ambrosium_ore": ("minecraft:coal_ore", (168, 160, 128), {"light": 7}, "ore_ambrosium"),
    "zanite_ore": ("minecraft:iron_ore", (168, 140, 190), {}, "ore_zanite"),
    "gravitite_ore": ("minecraft:gold_ore", (170, 150, 120), {}, "ore_gravitite"),
    "skyroot_planks": ("minecraft:oak_planks", (176, 146, 96), {}, "planks"),
    "skyroot_crafting_table": ("minecraft:crafting_table", (176, 146, 96), {}, "table"),
    "incubator": ("minecraft:furnace", (150, 140, 130), {"light": 0}, "table"),
}

ITEMS = {
    # name: (template, palette, kind)
    "ambrosium_shard": ("minecraft:flint", (226, 200, 90), "shard"),
    "zanite_gemstone": ("minecraft:amethyst_shard", (170, 120, 210), "gem"),
    "enchanted_gravitite": ("minecraft:amethyst_shard", (196, 160, 230), "gem"),
    "skyroot_stick": ("minecraft:stick", (176, 146, 96), "stick"),
    "swet_jelly": ("minecraft:slime_ball", (150, 220, 200), "gem"),
    "blue_berry": ("minecraft:sweet_berries", (90, 110, 220), "berry"),
    "white_apple": ("minecraft:apple", (240, 240, 228), "apple"),
    "healing_stone": ("minecraft:ghast_tear", (200, 240, 200), "gem"),
    "golden_amber": ("minecraft:flint", (240, 180, 60), "gem"),
    "golden_feather": ("minecraft:feather", (240, 200, 80), "feather"),
    "cloud_parachute": ("minecraft:paper", (238, 244, 250), "parachute"),
    "valkyrie_lance": ("minecraft:iron_sword", (220, 220, 230), "sword"),
    "lightning_sword": ("minecraft:iron_sword", (140, 200, 255), "sword"),
    "phoenix_bow": ("minecraft:bow", (240, 150, 60), "bow"),
}

# Tools and armour, built in three materials.
MATERIALS = {
    "skyroot": ((176, 146, 96), "wooden", ("sword", "pickaxe", "axe", "shovel")),
    "zanite": ((170, 120, 210), "stone", ("sword", "pickaxe", "axe", "shovel")),
    "gravitite": ((196, 160, 230), "iron", ("sword", "pickaxe", "axe", "shovel")),
}
ARMOUR = {
    "skyroot": None,  # the Aether has no skyroot armour
    "zanite": ((170, 120, 210), "iron", ("helmet", "chestplate", "leggings", "boots")),
    "gravitite": ((196, 160, 230), "diamond", ("helmet", "chestplate", "leggings", "boots")),
}

ENTITIES = {
    # name: (attributes, loot entries)
    "slider": {
        "minecraft:max_health": 100.0,
        "minecraft:movement_speed": 0.25,
        "minecraft:attack_damage": 8.0,
        "minecraft:armor": 12.0,
        "minecraft:knockback_resistance": 1.0,
        "minecraft:follow_range": 40.0,
        "minecraft:spawn_reinforcements": 0.0,
    },
    "valkyrie_queen": {
        "minecraft:max_health": 120.0,
        "minecraft:movement_speed": 0.3,
        "minecraft:attack_damage": 10.0,
        "minecraft:armor": 8.0,
        "minecraft:knockback_resistance": 0.6,
        "minecraft:follow_range": 40.0,
        "minecraft:spawn_reinforcements": 0.0,
    },
    "sun_spirit": {
        "minecraft:max_health": 80.0,
        "minecraft:movement_speed": 0.28,
        "minecraft:attack_damage": 7.0,
        "minecraft:armor": 4.0,
        "minecraft:knockback_resistance": 0.4,
        "minecraft:follow_range": 40.0,
        "minecraft:spawn_reinforcements": 0.0,
    },
}

MOB_LOOT = {
    "slider": ("minecraft:redstone", 4, 8),
    "valkyrie_queen": ("aether:golden_feather", 2, 4),
    "sun_spirit": ("minecraft:blaze_powder", 3, 6),
}

BLOCK_LOOT = {
    # block: (item, min, max)
    "ambrosium_ore": ("aether:ambrosium_shard", 1, 3),
    "zanite_ore": ("aether:zanite_gemstone", 1, 2),
    "gravitite_ore": ("aether:enchanted_gravitite", 1, 1),
    "icestone": ("aether:icestone", 1, 1),
}


# ---------------------------------------------------------------------------
# PNG writer (no external dependency).

def png(width, height, pixels):
    raw = b"".join(b"\x00" + bytes(pixels[y]) for y in range(height))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def rng(seed):
    n = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)

    def next_int(bound):
        nonlocal n
        n = (n * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        return (n >> 33) % bound

    return next_int


def shade(c, factor):
    return tuple(max(0, min(255, int(v * factor))) for v in c)


def draw_block(name, base, kind):
    r = rng("aether:" + name)
    rows = []
    for y in range(16):
        row = []
        for x in range(16):
            f = 0.86 + r(28) / 100.0
            c = shade(base, f)
            if kind == "grass" and y < 4:
                c = shade((110, 180, 84), 0.9 + r(20) / 100.0)
            elif kind == "stone" and r(100) < 5:
                c = shade(base, 0.72)
            elif kind == "moss" and r(100) < 22:
                c = shade((104, 150, 90), 0.9 + r(20) / 100.0)
            elif kind == "ice" and r(100) < 8:
                c = (222, 246, 255)
            elif kind == "cloud" and (r(100) < 10 or y % 4 == 0):
                c = (255, 255, 255)
            elif kind == "ore_ambrosium" and 3 <= x <= 6 and 3 <= y <= 6:
                c = shade((240, 214, 96), 0.9 + r(20) / 100.0)
            elif kind == "ore_ambrosium" and 10 <= x <= 13 and 9 <= y <= 12:
                c = shade((240, 214, 96), 0.9 + r(20) / 100.0)
            elif kind == "ore_zanite" and 4 <= x <= 7 and 10 <= y <= 13:
                c = shade((180, 130, 220), 0.9 + r(20) / 100.0)
            elif kind == "ore_gravitite" and 9 <= x <= 12 and 3 <= y <= 6:
                c = shade((226, 190, 250), 0.9 + r(20) / 100.0)
            elif kind == "planks" and y % 4 == 3:
                c = shade(base, 0.7)
            elif kind == "table" and (x < 2 or y < 2):
                c = shade(base, 0.7)
            row.extend((c[0], c[1], c[2], 255))
        rows.append(row)
    return png(16, 16, rows)


def blank():
    return [[0] * 64 for _ in range(16)]


def rect(px, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if 0 <= x < 16 and 0 <= y < 16:
                i = x * 4
                px[y][i:i + 4] = [c[0], c[1], c[2], 255]


def dark(c):
    return shade(c, 0.65)


def draw_item(name, base, kind):
    px = blank()
    if kind in ("sword",):
        for i in range(3, 13):
            rect(px, i, 15 - i, i, 15 - i, dark(base))
        rect(px, 4, 13, 5, 14, (120, 96, 60))
        rect(px, 12, 3, 13, 4, base)
    elif kind in ("pickaxe", "axe", "shovel"):
        for i in range(4, 13):
            rect(px, i, 15 - i, i, 15 - i, (120, 96, 60))
        if kind == "pickaxe":
            rect(px, 9, 2, 14, 3, base)
            rect(px, 11, 2, 12, 5, base)
        elif kind == "axe":
            rect(px, 10, 1, 14, 6, base)
        else:
            rect(px, 10, 1, 13, 6, base)
    elif kind == "helmet":
        rect(px, 3, 4, 12, 10, base)
        rect(px, 4, 11, 11, 12, dark(base))
        rect(px, 5, 7, 10, 9, (30, 30, 40))
    elif kind == "chestplate":
        rect(px, 3, 3, 12, 12, base)
        rect(px, 1, 4, 2, 9, base)
        rect(px, 13, 4, 14, 9, base)
    elif kind == "leggings":
        rect(px, 3, 3, 12, 8, base)
        rect(px, 3, 8, 6, 14, base)
        rect(px, 9, 8, 12, 14, base)
    elif kind == "boots":
        rect(px, 3, 8, 6, 12, base)
        rect(px, 3, 12, 8, 14, base)
        rect(px, 9, 8, 12, 12, base)
        rect(px, 8, 12, 13, 14, base)
    elif kind == "shard":
        rect(px, 6, 6, 9, 11, base)
        rect(px, 7, 3, 8, 6, shade(base, 1.15))
    elif kind == "gem":
        rect(px, 5, 6, 10, 11, base)
        rect(px, 6, 4, 9, 6, shade(base, 1.2))
        rect(px, 6, 11, 9, 13, dark(base))
    elif kind == "stick":
        for i in range(3, 13):
            rect(px, i, 15 - i, i + 1, 15 - i, base)
    elif kind == "berry":
        for cx, cy in ((6, 8), (9, 6), (8, 11)):
            rect(px, cx, cy, cx + 2, cy + 2, base)
    elif kind == "apple":
        rect(px, 4, 5, 11, 12, base)
        rect(px, 7, 2, 8, 5, (120, 90, 50))
    elif kind == "feather":
        for i in range(3, 13):
            rect(px, 15 - i, i, 16 - i, i, base)
    elif kind == "parachute":
        rect(px, 3, 3, 12, 8, base)
        rect(px, 5, 8, 10, 13, shade(base, 0.9))
    elif kind == "bow":
        for i in range(3, 13):
            rect(px, 4, i, 5, i, (120, 96, 60))
            rect(px, 12, i, 13, i, (120, 96, 60))
        rect(px, 5, 3, 12, 4, base)
    else:
        rect(px, 4, 4, 11, 11, base)
    return png(16, 16, px)


# ---------------------------------------------------------------------------
# File writers.

def write(path, data):
    full = os.path.join(CONTENT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if isinstance(data, bytes):
        with open(full, "wb") as f:
            f.write(data)
    else:
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2)
            f.write("\n")


def main():
    langs = {"en_us": {}, "fr_fr": {}}
    langs["en_us"]["itemGroup.aether.group"] = "The Aether"
    langs["fr_fr"]["itemGroup.aether.group"] = "L'Ether"

    tab_items = []

    for name, (template, palette, props, kind) in BLOCKS.items():
        definition = {"template": template, "item": True}
        if props:
            definition["properties"] = props
        write("data/%s/horizon/block/%s.json" % (ID, name), definition)
        write("assets/%s/blockstates/%s.json" % (ID, name),
              {"variants": {"": {"model": "%s:block/%s" % (ID, name)}}})
        write("assets/%s/models/block/%s.json" % (ID, name),
              {"parent": "minecraft:block/cube_all",
               "textures": {"all": "%s:block/%s" % (ID, name)}})
        write("assets/%s/items/%s.json" % (ID, name),
              {"model": {"type": "minecraft:model", "model": "%s:block/%s" % (ID, name)}})
        write("assets/%s/textures/block/%s.png" % (ID, name),
              draw_block(name, palette, kind))
        langs["en_us"][  "block.%s.%s" % (ID, name)] = pretty(name)
        langs["fr_fr"]["block.%s.%s" % (ID, name)] = pretty(name, fr=True)
        tab_items.append("%s:%s" % (ID, name))
        if name in BLOCK_LOOT:
            item, lo, hi = BLOCK_LOOT[name]
            write("data/%s/loot_table/blocks/%s.json" % (ID, name), {
                "type": "minecraft:block",
                "pools": [{
                    "rolls": 1,
                    "bonus_rolls": 0,
                    "entries": [{
                        "type": "minecraft:item",
                        "name": item,
                        "functions": [{
                            "function": "minecraft:set_count",
                            "count": {"type": "minecraft:uniform", "min": lo, "max": hi},
                            "add": False,
                        }],
                    }],
                }],
            })

    item_files = []
    for name, (template, palette, kind) in ITEMS.items():
        write("data/%s/horizon/item/%s.json" % (ID, name), {"template": template})
        write("assets/%s/items/%s.json" % (ID, name),
              {"model": {"type": "minecraft:model", "model": "%s:item/%s" % (ID, name)}})
        write("assets/%s/models/item/%s.json" % (ID, name),
              {"parent": "minecraft:item/generated",
               "textures": {"layer0": "%s:item/%s" % (ID, name)}})
        write("assets/%s/textures/item/%s.png" % (ID, name),
              draw_item(name, palette, kind))
        langs["en_us"]["item.%s.%s" % (ID, name)] = pretty(name)
        langs["fr_fr"]["item.%s.%s" % (ID, name)] = pretty(name, fr=True)
        tab_items.append("%s:%s" % (ID, name))
        item_files.append(name)

    for material, (palette, vanilla, tools) in MATERIALS.items():
        for tool in tools:
            name = "%s_%s" % (material, tool)
            write("data/%s/horizon/item/%s.json" % (ID, name),
                  {"template": "minecraft:%s_%s" % (vanilla, tool)})
            write("assets/%s/items/%s.json" % (ID, name),
                  {"model": {"type": "minecraft:model", "model": "%s:item/%s" % (ID, name)}})
            write("assets/%s/models/item/%s.json" % (ID, name),
                  {"parent": "minecraft:item/handheld",
                   "textures": {"layer0": "%s:item/%s" % (ID, name)}})
            write("assets/%s/textures/item/%s.png" % (ID, name),
                  draw_item(name, palette, tool))
            langs["en_us"]["item.%s.%s" % (ID, name)] = pretty(name)
            langs["fr_fr"]["item.%s.%s" % (ID, name)] = pretty(name, fr=True)
            tab_items.append("%s:%s" % (ID, name))
            item_files.append(name)

    for material, armour in ARMOUR.items():
        if not armour:
            continue
        palette, vanilla, pieces = armour
        for piece in pieces:
            name = "%s_%s" % (material, piece)
            write("data/%s/horizon/item/%s.json" % (ID, name),
                  {"template": "minecraft:%s_%s" % (vanilla, piece)})
            write("assets/%s/items/%s.json" % (ID, name),
                  {"model": {"type": "minecraft:model", "model": "%s:item/%s" % (ID, name)}})
            write("assets/%s/models/item/%s.json" % (ID, name),
                  {"parent": "minecraft:item/generated",
                   "textures": {"layer0": "%s:item/%s" % (ID, name)}})
            write("assets/%s/textures/item/%s.png" % (ID, name),
                  draw_item(name, palette, piece))
            langs["en_us"]["item.%s.%s" % (ID, name)] = pretty(name)
            langs["fr_fr"]["item.%s.%s" % (ID, name)] = pretty(name, fr=True)
            tab_items.append("%s:%s" % (ID, name))
            item_files.append(name)

    for name, attributes in ENTITIES.items():
        write("data/%s/horizon/entity_type/%s.json" % (ID, name),
              {"template": "minecraft:zombie", "attributes": attributes})
        item, lo, hi = MOB_LOOT[name]
        write("data/%s/loot_table/entities/%s.json" % (ID, name), {
            "type": "minecraft:entity",
            "pools": [{
                "rolls": 1,
                "bonus_rolls": 0,
                "entries": [{
                    "type": "minecraft:item",
                    "name": item,
                    "functions": [{
                        "function": "minecraft:set_count",
                        "count": {"type": "minecraft:uniform", "min": lo, "max": hi},
                        "add": False,
                    }, {
                        "function": "minecraft:enchanted_count_increase",
                        "count": {"type": "minecraft:uniform", "min": 0, "max": 1},
                        "enchantment": "minecraft:looting",
                    }],
                }],
            }],
        })
        langs["en_us"]["entity.%s.%s" % (ID, name)] = pretty(name)
        langs["fr_fr"]["entity.%s.%s" % (ID, name)] = pretty(name, fr=True)

    write("data/%s/horizon/creative_tab/%s.json" % (ID, ID),
          {"title": "itemGroup.aether.group",
           "icon": "aether:ambrosium_shard",
           "items": tab_items})

    recipes = {
        "skyroot_planks": (["#"], {"#": "aether:skyroot_crafting_table"}, {"id": "aether:skyroot_planks", "count": 4}),
        "skyroot_stick": (["#", "#"], {"#": "aether:skyroot_planks"}, {"id": "aether:skyroot_stick", "count": 4}),
        "zanite_pickaxe": (["ZZZ", " S ", " S "], {"Z": "aether:zanite_gemstone", "S": "aether:skyroot_stick"}, {"id": "aether:zanite_pickaxe"}),
        "zanite_sword": (["Z", "Z", "S"], {"Z": "aether:zanite_gemstone", "S": "aether:skyroot_stick"}, {"id": "aether:zanite_sword"}),
        "gravitite_pickaxe": (["GGG", " S ", " S "], {"G": "aether:enchanted_gravitite", "S": "aether:skyroot_stick"}, {"id": "aether:gravitite_pickaxe"}),
        "gravitite_sword": (["G", "G", "S"], {"G": "aether:enchanted_gravitite", "S": "aether:skyroot_stick"}, {"id": "aether:gravitite_sword"}),
        "healing_stone": (["AAA", "AWA", "AAA"], {"A": "aether:ambrosium_shard", "W": "aether:white_apple"}, {"id": "aether:healing_stone"}),
        "golden_amber": (["AA", "AA"], {"A": "aether:ambrosium_shard"}, {"id": "aether:golden_amber"}),
        "skyroot_crafting_table": (["PP", "PP"], {"P": "aether:skyroot_planks"}, {"id": "aether:skyroot_crafting_table"}),
    }
    for name, (pattern, key, result) in recipes.items():
        write("data/%s/recipe/%s.json" % (ID, name), {
            "type": "minecraft:crafting_shaped",
            "pattern": pattern,
            "key": key,
            "result": result,
        })

    # Mining tags so the ores and stone can be broken with the right tool.
    pickaxe = ["aether:holystone", "aether:mossy_holystone", "aether:icestone",
               "aether:ambrosium_ore", "aether:zanite_ore", "aether:gravitite_ore",
               "aether:incubator"]
    write("data/minecraft/tags/block/mineable/pickaxe.json", {"values": pickaxe})
    write("data/minecraft/tags/block/mineable/axe.json",
          {"values": ["aether:skyroot_planks", "aether:skyroot_crafting_table"]})
    write("data/minecraft/tags/block/mineable/shovel.json",
          {"values": ["aether:aether_grass", "aether:aether_dirt", "aether:aercloud",
                      "aether:golden_aercloud"]})

    for lang, strings in langs.items():
        write("assets/%s/lang/%s.json" % (ID, lang), strings)

    print("content generated: %d blocks, %d items, %d entities"
          % (len(BLOCKS), len(tab_items) - len(BLOCKS), len(ENTITIES)))


def pretty(name, fr=False):
    words = name.split("_")
    special = {"aether": "Aether", "skyroot": "Skyroot", "zanite": "Zanite",
               "gravitite": "Gravitite", "aercloud": "Aercloud", "icestone": "Icestone",
               "holystone": "Holystone", "ambrosium": "Ambrosium", "swet": "Swet"}
    if fr:
        special.update({"aether": "Éther", "berry": "baie", "apple": "pomme",
                        "cloud": "nuage", "stone": "pierre", "grass": "herbe"})
    return " ".join(special.get(w, w.capitalize()) for w in words)


if __name__ == "__main__":
    main()
