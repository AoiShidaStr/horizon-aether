# Provenance

The Aether is a Minecraft mod first published by Gilded Games; its current
NeoForge source (`The-Aether-Team/The-Aether`) is LGPL-3.0. This Horizon port
is a **clean-room reimplementation**: it was written from public behaviour
descriptions (the Aether wiki's boss, block and item pages) and from Horizon's
own documentation. **No file of the upstream mod was copied or translated**,
no upstream code, texture, model, sound or data file is contained here.

- Block, item, entity and recipe definitions in `content/` were written for
  Horizon's content API 0.2.
- All textures in `content/assets/aether/textures/` are procedural
  placeholders drawn by `tools/gen_content.py` (16x16 noise/shape images in
  the Aether's colour family), not upstream art.
- The native crate in `mixins/aether/api/` is original Rust written against
  `horizon-client`'s mod API.

Trademark and mod-origin names ("The Aether", "Slider", "Valkyrie Queen",
"Sun Spirit", "Ambrosium", "Zanite", "Gravitite", ...) belong to their
authors; they are used only to describe what this port imitates.

This port is MIT-licensed (`LICENSE`); its MIT licence applies only to the
original work in this folder.
