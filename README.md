# DeltaWorlds Tools

**Version 1.0.1 Alpha** · Made by OCM =)  
Tested on **Blender 4.2** and **Blender 5.1**

A Blender add-on for preparing and exporting skinned avatars for **DeltaWorlds / ActiveWorlds** (CAV-style DirectX `.x`), in the same spirit as Ultimate Unwrap.

## Features

- **Import FBX** with avatar-friendly settings (scale 1, no animation, leaf bones / connect / auto bone orientation), placed at the 3D cursor
- **Fix Missing Textures** (searches the FBX folder and parents, like Find Missing Files)
- **Scale Face / Body bones** in Edit Mode (Individual Origins; disconnects linked bones, keeps parenting)
- **Bone renamer** with suggestions for Bip01, Mixamo, Rocketbox, and other common rigs → `aw_*` names
- **Accessories**: maps leftover bones to `aw_obj` / `aw_obj2` / `aw_obj3` and `aw_hair`…`aw_hair4` when appropriate
- **Arm Position** tools (sternum / shoulder / elbow / wrist) + Apply / Reset Rest Pose
- **Convert Textures** (clean materials, resize, JPG/PNG, DeltaWorlds-safe names)
- **Export DirectX `.x`** (skinned mesh, materials, optional zip + copy textures beside the `.x`)

## Install

1. Download **`DeltaWorldsTools.zip`** from the [Releases](../../releases) page  
   (use the zip attached to the release — not “Source code”)
2. In Blender: **Edit → Preferences → Add-ons → Install…**
3. Select `DeltaWorldsTools.zip` and enable **DeltaWorlds Tools**
4. Open the **N-panel** in the 3D View → tab **DeltaWorlds**

Optional: set default Import FBX / Export folders and texture prefix under the add-on’s preferences, then click **Apply**.

## Requirements

- Blender **4.2** or newer (5.1 supported)
- Built-in **FBX** importer enabled (Preferences → Add-ons → search “FBX”)

## Typical workflow

1. **Import FBX** (or use your own armature)
2. **Fix Missing Textures** if maps are pink/missing
3. **Scan Armature** → check suggestions → **Apply Renames**
4. Adjust **Arm Position** / face-body scale if needed → **Apply as Rest Pose**
5. **Convert Textures** (JPG recommended for DeltaWorlds)
6. **Apply Scale/Rotation** (or **Apply All**)
7. **Export DirectX**

## License

GPL-2.0-or-later (same family as Blender add-ons). See the header in `__init__.py`.

## Credits

Made by **OCM =)**  
Built for the DeltaWorlds / ActiveWorlds community.
