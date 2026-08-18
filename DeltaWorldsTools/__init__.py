# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "DeltaWorlds Tools (1.0 Alpha)",
    "author": "Custom for DeltaWorlds / ActiveWorlds CAV avatars",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "File > Export > DeltaWorlds DirectX (.x)  |  N-Panel > DeltaWorlds",
    "description": "Import FBX, rename bones, convert textures, and export DirectX .x for DeltaWorlds / ActiveWorlds (Ultimate Unwrap style). Works on Blender 4.2+",
    "category": "Import-Export",
}

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
    IntProperty,
)
from bpy_extras.io_utils import ExportHelper, ImportHelper



def _addon_prefs(context=None):
    """Return addon preferences (persistent across Blender sessions)."""
    addon_key = __package__ if __package__ else __name__
    try:
        return bpy.context.preferences.addons[addon_key].preferences
    except Exception:
        return None


class DW_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__ if __package__ else __name__

    tex_prefix: StringProperty(
        name="Texture Prefix",
        description="Default prefix for Convert Textures / Retexture filenames (e.g. ocm_). Saved between Blender sessions",
        default="",
    )
    import_fbx_dir: StringProperty(
        name="Import FBX Folder",
        description="Folder the Import FBX file browser opens in by default",
        default="",
        subtype="DIR_PATH",
    )
    export_x_dir: StringProperty(
        name="Export DirectX Folder",
        description="Folder the Export DirectX file browser opens in by default",
        default="",
        subtype="DIR_PATH",
    )
    show_about: BoolProperty(
        name="About",
        description="Show about information",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(self, "tex_prefix")
        layout.prop(self, "import_fbx_dir", text="Import FBX Folder")
        layout.prop(self, "export_x_dir", text="Export DirectX Folder")
        layout.separator()
        layout.operator("deltaworlds.apply_preferences", text="Apply", icon="CHECKMARK")
        layout.separator()
        box = layout.box()
        row = box.row()
        row.prop(
            self,
            "show_about",
            text="About:",
            icon="TRIA_DOWN" if self.show_about else "TRIA_RIGHT",
            emboss=False,
        )
        if self.show_about:
            col = box.column()
            col.label(text="Made By OCM =)")
            col.label(text="Tested on Blender 4.2 and 5.1")
            col.label(text="Version 1.0 Alpha")


def _update_tex_prefix(self, context):
    """Write scene prefix into addon preferences so it survives restarts."""
    prefs = _addon_prefs(context)
    if prefs is not None:
        if prefs.tex_prefix != self.dw_tex_prefix:
            prefs.tex_prefix = self.dw_tex_prefix


def _update_show_bones(self, context):
    """Toggle bone name labels + In Front on every armature in the scene."""
    show = bool(self.dw_viewport_show_bones)
    for obj in context.scene.objects:
        if obj.type != "ARMATURE":
            continue
        obj.show_in_front = show
        # Bone names in viewport
        try:
            obj.data.show_names = show
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Export operator
# ---------------------------------------------------------------------------

class ExportDeltaWorldsX(bpy.types.Operator, ExportHelper):
    """Export armature + skinned mesh(es) to DeltaWorlds/ActiveWorlds DirectX .x (Ultimate Unwrap style)"""
    bl_idname = "export_scene.deltaworlds_x"
    bl_label = "Export DeltaWorlds DirectX (.x)"
    bl_options = {"PRESET"}

    filename_ext = ".x"
    filter_glob: StringProperty(default="*.x", options={"HIDDEN"})

    def invoke(self, context, event):
        prefs = _addon_prefs(context)
        if prefs and prefs.export_x_dir:
            import os
            # Prefer last used name if any, else empty filename in default dir
            name = os.path.basename(self.filepath) if self.filepath else ""
            self.filepath = os.path.join(prefs.export_x_dir, name)
        return ExportHelper.invoke(self, context, event)

    global_scale: FloatProperty(
        name="Global Scale",
        description="Scale written into the Armature frame. Use 1.0 if model is already human-sized in Blender; use 0.01 for full-size Blender units",
        default=1.0,
        min=0.0001,
        max=100.0,
    )

    axis_conversion: EnumProperty(
        name="Axis Conversion",
        description="How to convert Blender Z-up to the target space",
        items=(
            ("UU", "Ultimate Unwrap style", "Match the matrix UU writes"),
            ("YUP", "Simple Y-up", "Basic Z-up → Y-up flip"),
            ("NONE", "None", "No axis conversion"),
        ),
        default="YUP",
    )


    export_normals: BoolProperty(name="Export Normals", default=True)
    export_uvs: BoolProperty(name="Export UVs", default=True)

    flip_uv_v: BoolProperty(
        name="Flip UV V",
        description="Flip V coordinate (try toggling if texture is scrambled)",
        default=True,
    )

    flip_faces: BoolProperty(
        name="Flip Face Winding",
        description="Reverse triangle order (try if model looks inside-out)",
        default=False,
    )

    export_materials: BoolProperty(name="Export Materials", default=True)

    export_vertex_colors: BoolProperty(
        name="Export Vertex Colors",
        description="Write solid-white MeshVertexColors (ON = flatter lighting; OFF = normal lighting)",
        default=False,
    )

    mat_ambient: FloatProperty(
        name="Ambient",
        description="Ambient fill (written as emissive in .x). Higher = softer shadows. Default 0.8",
        default=0.8, min=0.0, max=1.0,
    )
    mat_diffuse: FloatProperty(
        name="Diffuse",
        description="Diffuse face color strength. Lower = less harsh lighting contrast. Default 0.35",
        default=0.35, min=0.0, max=1.0,
    )
    mat_specular: FloatProperty(
        name="Specular",
        description="Specular highlight strength",
        default=0.5, min=0.0, max=1.0,
    )
    mat_opacity: FloatProperty(
        name="Opacity",
        description="Material alpha / opacity",
        default=1.0, min=0.0, max=1.0,
    )
    mat_specular_power: FloatProperty(
        name="Specular Power",
        description="Shininess exponent (UU uses 128)",
        default=128.0, min=1.0, max=1024.0,
    )

    generate_backfaces: BoolProperty(
        name="Generate Backfaces",
        description="Duplicate every face with flipped normals (for skirts/open meshes). Slightly offsets inner faces to avoid z-fighting shadows",
        default=False,
    )
    backface_offset: FloatProperty(
        name="Backface Offset",
        description="How far to push generated inner faces along -normal (prevents z-fighting)",
        default=0.0005, min=0.0, max=0.1,
    )

    export_as_zip: BoolProperty(
        name="Export as ZIP",
        description="Package the .x into a .zip with the same base name (and remove the loose .x)",
        default=False,
    )

    only_selected: BoolProperty(
        name="Only Selected",
        description="Export only selected objects",
        default=False,
    )

    def execute(self, context):
        from . import export_x
        keywords = self.as_keywords(ignore=("check_existing", "filter_glob"))
        return export_x.save(context, **keywords)


def menu_func_export(self, context):
    self.layout.operator(ExportDeltaWorldsX.bl_idname, text="DeltaWorlds DirectX (.x)")


# ---------------------------------------------------------------------------
# Bone rename N-Panel
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STERNUM_L = ("aw_lfsternum", "aw_sternuml", "lfsternum", "sternuml")
_STERNUM_R = ("aw_rtsternum", "aw_sternumr", "rtsternum", "sternumr")
_SHOULDER_L = ("aw_lfshoulder", "aw_shoulderl", "lfshoulder", "shoulderl")
_SHOULDER_R = ("aw_rtshoulder", "aw_shoulderr", "rtshoulder", "shoulderr")
_ELBOW_L = ("aw_lfelbow", "aw_elbowl", "lfelbow", "elbowl")
_ELBOW_R = ("aw_rtelbow", "aw_elbowr", "rtelbow", "elbowr")
_WRIST_L = ("aw_lfwrist", "aw_wristl", "lfwrist", "wristl")
_WRIST_R = ("aw_rtwrist", "aw_wristr", "rtwrist", "wristr")


def _armature_enum_items(self, context):
    items = []
    if context and context.scene:
        for obj in context.scene.objects:
            if obj.type == "ARMATURE":
                items.append((obj.name, obj.name, f"Armature: {obj.name}"))
    if not items:
        items.append(("NONE", "(no armature in scene)", ""))
    return items


def _get_armature(context):
    """Prefer the N-panel armature dropdown, then active/selected."""
    name = getattr(context.scene, "dw_armature_name", "") or ""
    if name and name != "NONE":
        obj = context.scene.objects.get(name)
        if obj and obj.type == "ARMATURE":
            return obj
    arm = context.object
    if arm and arm.type == "ARMATURE":
        return arm
    for obj in context.selected_objects:
        if obj.type == "ARMATURE":
            return obj
    for obj in context.scene.objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def _find_pose_bone(arm_obj, candidates):
    """Return first pose bone matching any name in candidates (case-insensitive)."""
    lower_map = {b.name.lower(): b for b in arm_obj.pose.bones}
    for c in candidates:
        b = lower_map.get(c.lower())
        if b is not None:
            return b
    return None


def _armature_has_arm_bones(arm_obj):
    has_s = bool(_find_pose_bone(arm_obj, _STERNUM_L) and _find_pose_bone(arm_obj, _STERNUM_R))
    has_sh = bool(_find_pose_bone(arm_obj, _SHOULDER_L) and _find_pose_bone(arm_obj, _SHOULDER_R))
    has_e = bool(_find_pose_bone(arm_obj, _ELBOW_L) and _find_pose_bone(arm_obj, _ELBOW_R))
    has_w = bool(_find_pose_bone(arm_obj, _WRIST_L) and _find_pose_bone(arm_obj, _WRIST_R))
    return has_s, has_sh, has_e, has_w


def _rotate_pbone_global(arm_obj, pbone, axis, degrees):
    """Rotate a pose bone around a global-axis-aligned axis through its own head."""
    from mathutils import Matrix, Vector
    from math import radians

    if axis == "Y":
        world_axis = Vector((0.0, 1.0, 0.0))
    elif axis == "Z":
        world_axis = Vector((0.0, 0.0, 1.0))
    elif axis == "X":
        world_axis = Vector((1.0, 0.0, 0.0))
    else:
        world_axis = Vector((0.0, 1.0, 0.0))

    arm_mat3 = arm_obj.matrix_world.to_3x3()
    axis_arm = (arm_mat3.inverted() @ world_axis).normalized()
    head = pbone.matrix.to_translation()
    T_neg = Matrix.Translation(-head)
    T_pos = Matrix.Translation(head)
    R = Matrix.Rotation(radians(degrees), 4, axis_arm)
    pbone.matrix = T_pos @ R @ T_neg @ pbone.matrix



class DWBoneMapItem(bpy.types.PropertyGroup):
    bone_name: StringProperty(name="Current")
    new_name: StringProperty(name="Rename To")
    status: StringProperty(name="Status")
    selected: BoolProperty(name="", default=True)


class DW_UL_bone_map(bpy.types.UIList):
    """Scrollable list of bones → AW name suggestions."""
    bl_idname = "DW_UL_bone_map"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            row.prop(item, "selected", text="")
            # current bone name (read-only)
            row.label(text=item.bone_name)
            if item.status == "OK":
                row.label(text="", icon="CHECKMARK")
            else:
                row.prop(item, "new_name", text="")
                if item.status == "suggest":
                    row.label(text="", icon="FORWARD")
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text=item.bone_name)


class DW_OT_scan_bones(bpy.types.Operator):
    bl_idname = "deltaworlds.scan_bones"
    bl_label = "Scan Armature"
    bl_description = "Read bones from the selected armature, suggest ActiveWorlds/DeltaWorlds names, show bone names In Front as Octahedral, and save a rest-pose restore point"

    def execute(self, context):
        from . import bones as bone_mod
        scene = context.scene
        items = scene.dw_bone_map
        items.clear()

        arm = _get_armature(context)
        if arm is not None:
            context.view_layer.objects.active = arm
            _show_armature_bones(arm)
            # Remember rest pose baseline for Reset Rest Pose
            if "dw_rest_pose_snapshot" not in arm:
                _snapshot_rest_pose(arm)
        if arm is None or arm.type != "ARMATURE":
            self.report({"ERROR"}, "No armature found — pick one in the dropdown")
            return {"CANCELLED"}

        # Two-pass mapping: body/face first, then accessories (obj/hair)
        bone_names = [b.name for b in arm.data.bones]
        for bone_name, sug, status in bone_mod.build_suggestions(bone_names):
            item = items.add()
            item.bone_name = bone_name
            if status == "OK":
                item.new_name = ""
                item.status = "OK"
                item.selected = False
            elif sug:
                item.new_name = sug
                item.status = "suggest"
                item.selected = True
            else:
                item.new_name = ""
                item.status = "—"
                item.selected = False

        self.report({"INFO"}, f"Scanned {len(items)} bones")
        return {"FINISHED"}


class DW_OT_apply_bone_renames(bpy.types.Operator):
    bl_idname = "deltaworlds.apply_bone_renames"
    bl_label = "Apply Renames"
    bl_description = "Scan the armature for bone-name suggestions, then apply checked renames, rename unused bones to aw_unused*, and update vertex groups"
    bl_options = {"UNDO"}

    def execute(self, context):
        # Always scan first so suggestions are current
        bpy.ops.deltaworlds.scan_bones()
        scene = context.scene
        items = scene.dw_bone_map

        arm = _get_armature(context)
        if arm is None or arm.type != "ARMATURE":
            self.report({"ERROR"}, "No armature found — pick one in the dropdown")
            return {"CANCELLED"}

        # Collect renames from checked rows that have a target name
        renames = []
        for item in items:
            if not item.selected:
                continue
            old = item.bone_name
            new = item.new_name.strip()
            if not new or new == old:
                continue
            if new in arm.data.bones and new != old:
                self.report({"ERROR"}, f"Target name already exists: {new}")
                return {"CANCELLED"}
            renames.append((old, new))

        context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="OBJECT")

        # Rename bones
        for old, new in renames:
            bone = arm.data.bones.get(old)
            if bone:
                bone.name = new

        # Find meshes using this armature
        meshes = []
        for obj in context.scene.objects:
            if obj.type != "MESH":
                continue
            for mod in obj.modifiers:
                if mod.type == "ARMATURE" and mod.object == arm:
                    meshes.append(obj)
                    break
            if obj.parent == arm and obj not in meshes:
                meshes.append(obj)

        # Rename vertex groups
        for obj in meshes:
            for old, new in renames:
                vg = obj.vertex_groups.get(old)
                if vg:
                    vg.name = new

        deleted = 0
        renamed_unused = 0

        if getattr(scene, "dw_rename_unused_bones", True):
            # Rename leftover non-aw_* bones to aw_unused1, aw_unused2, …
            # so skin weights (tongue, etc.) stay bound without breaking DW.
            bpy.ops.object.mode_set(mode="OBJECT")
            leftover = [b for b in arm.data.bones if not b.name.lower().startswith("aw_")]
            # pick a free starting index
            used_nums = set()
            for b in arm.data.bones:
                n = b.name.lower()
                if n.startswith("aw_unused"):
                    tail = n[len("aw_unused"):]
                    if tail.isdigit():
                        used_nums.add(int(tail))
            next_i = 1
            for bone in leftover:
                while next_i in used_nums:
                    next_i += 1
                new_name = f"aw_unused{next_i}"
                used_nums.add(next_i)
                old_name = bone.name
                bone.name = new_name
                # rename matching vertex groups
                for obj in meshes:
                    vg = obj.vertex_groups.get(old_name)
                    if vg:
                        vg.name = new_name
                renamed_unused += 1
                next_i += 1

        elif getattr(scene, "dw_delete_unused_bones", False):
            # Delete any bone that does not start with aw_ (after renames).
            # Reparent children to the deleted bone's parent first.
            bpy.ops.object.mode_set(mode="EDIT")
            ebones = arm.data.edit_bones
            to_delete = [b.name for b in ebones if not b.name.lower().startswith("aw_")]
            safety = 0
            while to_delete and safety < 1000:
                safety += 1
                progress = False
                still = []
                for name in to_delete:
                    eb = ebones.get(name)
                    if eb is None:
                        continue
                    parent = eb.parent
                    for child in list(eb.children):
                        child.parent = parent
                    try:
                        ebones.remove(eb)
                        deleted += 1
                        progress = True
                    except Exception:
                        still.append(name)
                to_delete = still
                if not progress:
                    break
            bpy.ops.object.mode_set(mode="OBJECT")

            bone_names = {b.name for b in arm.data.bones}
            for obj in meshes:
                for vg in list(obj.vertex_groups):
                    if vg.name not in bone_names:
                        obj.vertex_groups.remove(vg)

        # Snapshot rest pose under the new bone names
        _snapshot_rest_pose(arm)

        # Refresh scan list
        bpy.ops.deltaworlds.scan_bones()
        msg = f"Renamed {len(renames)} bones"
        if renamed_unused:
            msg += f", tagged {renamed_unused} as aw_unused*"
        if deleted:
            msg += f", deleted {deleted} non-aw bones"
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class DW_PT_bone_panel(bpy.types.Panel):
    bl_label = "DeltaWorlds DirectX Exporter"
    bl_idname = "DW_PT_bone_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DeltaWorlds"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        def _section(parent, prop_name, title, icon="NONE"):
            box = parent.box()
            row = box.row()
            row.prop(
                scene, prop_name,
                text=title,
                icon="TRIA_DOWN" if getattr(scene, prop_name, False) else "TRIA_RIGHT",
                emboss=False,
            )
            return box if getattr(scene, prop_name, False) else None

        def _small_dir_buttons(row, scope):
            """Compact Down/Up operators for face or body bone scaling."""
            for text, direction in (("Down", "down"), ("Up", "up")):
                sub = row.row(align=True)
                sub.scale_x = 0.55
                op = sub.operator("deltaworlds.scale_face_bones", text=text)
                op.direction = direction
                op.scope = scope

        # ----- FBX (expanded by default) -----
        box = _section(layout, "dw_show_fbx", "FBX", "IMPORT")
        if box:
            row = box.row()
            row.enabled = _fbx_importer_available()
            row.operator("deltaworlds.import_fbx", text="Import FBX", icon="IMPORT")
            if not _fbx_importer_available():
                box.label(text="Enable FBX addon in Preferences", icon="ERROR")
            box.operator("deltaworlds.fix_missing_textures", text="Fix Missing Textures", icon="IMAGE_DATA")
            box.operator("deltaworlds.scan_bones", text="Scan Armature", icon="ARMATURE_DATA")
            row = box.row(align=True)
            row.label(text="Scale Face Bones:")
            _small_dir_buttons(row, "face")
            row = box.row(align=True)
            row.label(text="Scale Body Bones:")
            _small_dir_buttons(row, "body")

        # ----- Bone Names (includes former Armature options) -----
        box = _section(layout, "dw_show_bones", "Bone Names", "BONE_DATA")
        if box:
            box.operator("deltaworlds.apply_bone_renames", text="Apply Renames", icon="CHECKMARK")
            box.prop(scene, "dw_armature_name", text="Armature")
            box.prop(scene, "dw_rename_unused_bones")
            box.prop(scene, "dw_delete_unused_bones")
            items = scene.dw_bone_map
            if not items:
                box.label(text="Scan an armature to list bones", icon="INFO")
            else:
                box.template_list(
                    "DW_UL_bone_map", "",
                    scene, "dw_bone_map",
                    scene, "dw_bone_map_index",
                    rows=12,
                )

        # ----- Arm Position -----
        box = _section(layout, "dw_show_armpos", "Arm Position", "BONE_DATA")
        if box:
            row = box.row(align=True)
            row.label(text="(Apply bone names first!)")
            row.operator("deltaworlds.apply_bone_renames", text="Apply Now", icon="CHECKMARK")

            arm = _get_armature(context)
            has_sternum = has_shoulder = has_elbow = has_wrist = False
            if arm:
                has_sternum, has_shoulder, has_elbow, has_wrist = _armature_has_arm_bones(arm)

            def _dir_row(parent, label, target, enabled, missing_msg):
                row = parent.row(align=True)
                row.label(text=label)
                for text, direction in (("Up", "up"), ("Down", "down"), ("Front", "front"), ("Back", "back")):
                    col = row.column(align=True)
                    col.enabled = enabled
                    col.scale_x = 0.7
                    op = col.operator("deltaworlds.adjust_arm_bones", text=text)
                    op.target = target
                    op.direction = direction
                if not enabled:
                    parent.label(text=missing_msg, icon="INFO")

            _dir_row(box, "Sternum:", "sternum", has_sternum, "Need aw_lf/rtsternum")
            _dir_row(box, "Shoulder:", "shoulder", has_shoulder, "Need aw_lf/rtshoulder")
            _dir_row(box, "Elbow:", "elbow", has_elbow, "Need aw_lf/rtelbow")
            _dir_row(box, "Wrist:", "wrist", has_wrist, "Need aw_lf/rtwrist")

            row = box.row(align=True)
            row.enabled = has_sternum or has_shoulder or has_elbow or has_wrist
            row.operator("deltaworlds.apply_arm_rest_pose", text="Apply as Rest Pose", icon="CHECKMARK")
            row.operator("deltaworlds.reset_rest_pose", text="Reset Rest Pose", icon="LOOP_BACK")

            row = box.row(align=True)
            row.operator("deltaworlds.save_arm_preset", text="Save Preset", icon="FILE_TICK")
            row.operator("deltaworlds.load_arm_preset", text="Load Preset", icon="FILEBROWSER")
            try:
                import json
                hist = json.loads(context.scene.get("dw_arm_history", "[]") or "[]")
                n = len(hist)
            except Exception:
                n = 0
            last = context.scene.get("dw_arm_preset_path", "")
            if n or last:
                sub = box.column()
                if n:
                    row = sub.row(align=True)
                    row.label(text=f"Recorded steps: {n}")
                    row.operator("deltaworlds.reset_arm_history", text="Reset")
                if last:
                    from pathlib import Path as _P
                    sub.label(text=f"Last preset: {_P(last).name}")

        # ----- Convert Textures -----
        box = _section(layout, "dw_show_textures", "Convert Textures", "IMAGE_DATA")
        if box:
            box.prop(scene, "dw_tex_only_selected")
            box.prop(scene, "dw_tex_prefix")
            # Texture Size + up/down steppers
            row = box.row(align=True)
            row.prop(scene, "dw_tex_size", text="Texture Size")
            sub = row.row(align=True)
            sub.scale_x = 1.1
            op = sub.operator("deltaworlds.step_tex_size", text="", icon="TRIA_UP")
            op.direction = "up"
            op = sub.operator("deltaworlds.step_tex_size", text="", icon="TRIA_DOWN")
            op.direction = "down"
            # Max File Size + up/down steppers
            row = box.row(align=True)
            row.prop(scene, "dw_tex_max_kb", text="Max Size (KB)")
            sub = row.row(align=True)
            sub.scale_x = 1.1
            op = sub.operator("deltaworlds.step_tex_max_kb", text="", icon="TRIA_UP")
            op.direction = "up"
            op = sub.operator("deltaworlds.step_tex_max_kb", text="", icon="TRIA_DOWN")
            op.direction = "down"
            row = box.row(align=True)
            row.prop(scene, "dw_tex_keep_aspect")
            row.prop(scene, "dw_tex_copy_with_x")
            row = box.row(align=True)
            row.label(text="Convert to:")
            op = row.operator("deltaworlds.convert_textures", text=".jpg")
            op.file_format = "JPEG"
            op = row.operator("deltaworlds.convert_textures", text=".png")
            op.file_format = "PNG"

        # ----- Export -----
        layout.separator()
        layout.operator("deltaworlds.auto_rename", text="Auto Rename", icon="ARMATURE_DATA")
        # Retexture label reflects last format this session
        fmt = scene.get("dw_retexture_format", "JPEG") or "JPEG"
        retex_label = "Retexture PNG" if fmt == "PNG" else "Retexture JPG"
        layout.operator("deltaworlds.apply_texture", text=retex_label, icon="IMAGE_DATA")
        layout.operator("deltaworlds.apply_arm_rest_pose", text="Apply Rest Pose", icon="CHECKMARK")
        layout.operator("deltaworlds.apply_scale", text="Apply Scale/Rotation", icon="OBJECT_ORIGIN")
        layout.operator("deltaworlds.apply_all", text="Apply All", icon="CHECKMARK")
        layout.operator("deltaworlds.export_directx", text="Export DirectX", icon="EXPORT")

class DW_OT_adjust_arm_bones(bpy.types.Operator):
    bl_idname = "deltaworlds.adjust_arm_bones"
    bl_label = "Adjust Arm Bones"
    bl_description = "Rotate sternum/shoulder/elbow around global axes to pose the arms"
    bl_options = {"UNDO"}

    target: StringProperty(default="sternum")   # sternum | shoulder | elbow
    direction: StringProperty(default="up")     # up | down | front | back

    def execute(self, context):
        arm = _get_armature(context)
        if not arm:
            self.report({"ERROR"}, "Select an armature")
            return {"CANCELLED"}

        context.view_layer.objects.active = arm
        if arm.mode != "POSE":
            bpy.ops.object.mode_set(mode="POSE")

        if self.target == "sternum":
            left_c, right_c = _STERNUM_L, _STERNUM_R
            label = "Sternum"
        elif self.target == "shoulder":
            left_c, right_c = _SHOULDER_L, _SHOULDER_R
            label = "Shoulder"
        elif self.target == "elbow":
            left_c, right_c = _ELBOW_L, _ELBOW_R
            label = "Elbow"
        elif self.target == "wrist":
            left_c, right_c = _WRIST_L, _WRIST_R
            label = "Wrist"
        else:
            self.report({"ERROR"}, f"Unknown target: {self.target}")
            return {"CANCELLED"}

        left_pb = _find_pose_bone(arm, left_c)
        right_pb = _find_pose_bone(arm, right_c)
        if not left_pb or not right_pb:
            self.report({"ERROR"}, f"{label} bones not found (need AW names)")
            return {"CANCELLED"}

        # Global-axis amounts
        # Up/Down: global Y, ±10°.  UP → L -10, R +10
        # Front/Back: global Z, ±2.5° (half of previous)
        if self.direction == "up":
            axis, l_deg, r_deg = "Y", -10.0, 10.0
        elif self.direction == "down":
            axis, l_deg, r_deg = "Y", 10.0, -10.0
        elif self.direction == "front":
            axis, l_deg, r_deg = "Z", -2.5, 2.5
        elif self.direction == "back":
            axis, l_deg, r_deg = "Z", 2.5, -2.5
        else:
            self.report({"ERROR"}, f"Unknown direction: {self.direction}")
            return {"CANCELLED"}

        _rotate_pbone_global(arm, left_pb, axis, l_deg)
        _rotate_pbone_global(arm, right_pb, axis, r_deg)

        # Record step for preset (invisible counter)
        try:
            import json
            hist = []
            raw = context.scene.get("dw_arm_history", "[]")
            hist = json.loads(raw) if raw else []
            hist.append({"target": self.target, "direction": self.direction})
            context.scene["dw_arm_history"] = json.dumps(hist)
        except Exception:
            pass

        self.report(
            {"INFO"},
            f"{label} {self.direction}: L {l_deg:+.0f}° / R {r_deg:+.0f}° global {axis}",
        )
        return {"FINISHED"}


class DW_OT_apply_arm_rest_pose(bpy.types.Operator):
    bl_idname = "deltaworlds.apply_arm_rest_pose"
    bl_label = "Apply as Rest Pose"
    bl_description = "Apply the current pose as the new rest pose and freeze skinned mesh vertices so the mesh does not jump. Saves a restore point for Reset Rest Pose"
    bl_options = {"UNDO"}

    def execute(self, context):
        arm = _get_armature(context)
        if not arm:
            self.report({"ERROR"}, "Select an armature")
            return {"CANCELLED"}

        # Always snapshot current rest pose so Reset can undo THIS apply
        _snapshot_rest_pose(arm)

        # Find meshes deformed by this armature
        mesh_objects = []
        for obj in context.scene.objects:
            if obj.type != "MESH":
                continue
            for mod in obj.modifiers:
                if mod.type == "ARMATURE" and mod.object == arm:
                    mesh_objects.append(obj)
                    break
            else:
                if obj.parent == arm:
                    mesh_objects.append(obj)

        # Snapshot the visually deformed vertex positions (object space)
        depsgraph = context.evaluated_depsgraph_get()
        saved_coords = {}
        for obj in mesh_objects:
            eval_obj = obj.evaluated_get(depsgraph)
            try:
                eval_mesh = eval_obj.to_mesh()
            except Exception:
                continue
            if len(eval_mesh.vertices) != len(obj.data.vertices):
                # Topology changed by other modifiers — skip freeze for safety
                eval_obj.to_mesh_clear()
                self.report(
                    {"WARNING"},
                    f"{obj.name}: vertex count mismatch after eval; mesh not frozen",
                )
                continue
            saved_coords[obj.name] = [v.co.copy() for v in eval_mesh.vertices]
            eval_obj.to_mesh_clear()

        # Apply pose as rest pose on the armature
        context.view_layer.objects.active = arm
        if arm.mode != "POSE":
            bpy.ops.object.mode_set(mode="POSE")
        bpy.ops.pose.armature_apply()

        # Write the deformed positions back so the mesh matches the new rest pose
        for obj in mesh_objects:
            coords = saved_coords.get(obj.name)
            if not coords:
                continue
            me = obj.data
            for i, co in enumerate(coords):
                me.vertices[i].co = co
            me.update()

        # Back to pose mode for continued tweaking
        if arm.mode != "POSE":
            bpy.ops.object.mode_set(mode="POSE")

        # Clear arm-adjust history — new baseline
        context.scene["dw_arm_history"] = "[]"

        self.report(
            {"INFO"},
            f"Rest pose applied; froze {len(saved_coords)} mesh(es)",
        )
        return {"FINISHED"}



class DW_OT_save_arm_preset(bpy.types.Operator):
    bl_idname = "deltaworlds.save_arm_preset"
    bl_label = "Save Arm Preset"
    bl_description = "Save the sequence of arm Up/Down/Front/Back presses to a preset file"

    filepath: StringProperty(subtype="FILE_PATH")
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def invoke(self, context, event):
        last = context.scene.get("dw_arm_preset_path", "")
        if last:
            self.filepath = last
        else:
            self.filepath = "arm_preset.json"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        import json
        from pathlib import Path as P
        raw = context.scene.get("dw_arm_history", "[]")
        try:
            hist = json.loads(raw) if raw else []
        except Exception:
            hist = []
        if not hist:
            self.report({"WARNING"}, "No arm adjustments recorded yet")
            return {"CANCELLED"}
        path = P(bpy.path.abspath(self.filepath))
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")
        path.write_text(json.dumps({"version": 1, "steps": hist}, indent=2))
        context.scene["dw_arm_preset_path"] = str(path)
        self.report({"INFO"}, f"Saved {len(hist)} steps → {path.name}")
        return {"FINISHED"}


class DW_OT_load_arm_preset(bpy.types.Operator):
    bl_idname = "deltaworlds.load_arm_preset"
    bl_label = "Load Arm Preset"
    bl_description = "Load a preset and replay the arm adjustments"
    bl_options = {"UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def invoke(self, context, event):
        last = context.scene.get("dw_arm_preset_path", "")
        if last:
            self.filepath = last
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        import json
        from pathlib import Path as P
        path = P(bpy.path.abspath(self.filepath))
        if not path.exists():
            self.report({"ERROR"}, f"File not found: {path}")
            return {"CANCELLED"}
        try:
            data = json.loads(path.read_text())
            steps = data.get("steps", data if isinstance(data, list) else [])
        except Exception as e:
            self.report({"ERROR"}, f"Could not read preset: {e}")
            return {"CANCELLED"}

        context.scene["dw_arm_preset_path"] = str(path)
        # Reset history then replay
        context.scene["dw_arm_history"] = "[]"

        for step in steps:
            target = step.get("target", "")
            direction = step.get("direction", "")
            if not target or not direction:
                continue
            bpy.ops.deltaworlds.adjust_arm_bones(target=target, direction=direction)

        self.report({"INFO"}, f"Loaded {len(steps)} steps from {path.name}")
        return {"FINISHED"}


class DW_OT_export_directx(bpy.types.Operator):
    bl_idname = "deltaworlds.export_directx"
    bl_label = "Export DirectX"
    bl_description = "Open the DeltaWorlds .x export dialog"

    def execute(self, context):
        # Invoke the export operator so the file browser + options appear
        bpy.ops.export_scene.deltaworlds_x("INVOKE_DEFAULT")
        return {"FINISHED"}



class DW_OT_convert_textures(bpy.types.Operator):
    bl_idname = "deltaworlds.convert_textures"
    bl_label = "Convert Textures"
    bl_description = "Strip material nodes to Base Color only, resize/compress images, set Roughness=1 Metallic=0 Alpha=1, and save DeltaWorlds-safe filenames"
    bl_options = {"REGISTER", "UNDO"}

    file_format: StringProperty(default="JPEG")  # JPEG | PNG

    def execute(self, context):
        from . import textures as texmod
        scene = context.scene
        # Remember last convert format for Retexture this session
        scene["dw_retexture_format"] = self.file_format

        ok, fail, messages = texmod.convert_scene_textures(
            context,
            out_format=self.file_format,
            prefix=scene.dw_tex_prefix,
            only_selected=scene.dw_tex_only_selected,
            target_size=scene.dw_tex_size,
            keep_aspect=scene.dw_tex_keep_aspect,
            max_jpg_bytes=int(scene.dw_tex_max_kb) * 1024,
        )
        for m in messages[:20]:
            print(f"[DeltaWorlds Textures] {m}")
        if fail and not ok:
            self.report({"ERROR"}, f"Texture convert failed ({fail} materials)")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Converted {ok} material(s), {fail} skipped")
        return {"FINISHED"}



class DW_OT_reset_arm_history(bpy.types.Operator):
    bl_idname = "deltaworlds.reset_arm_history"
    bl_label = "Reset"
    bl_description = "Clear recorded arm-position steps so a new preset can be recorded"

    def execute(self, context):
        context.scene["dw_arm_history"] = "[]"
        self.report({"INFO"}, "Arm position recording cleared")
        return {"FINISHED"}


class DW_OT_apply_scale(bpy.types.Operator):
    bl_idname = "deltaworlds.apply_scale"
    bl_label = "Apply Scale/Rotation"
    bl_description = "Apply Scale and Rotation (Ctrl+A) on the armature and every mesh skinned to it"
    bl_options = {"UNDO"}

    def execute(self, context):
        arm = _get_armature(context)
        if not arm:
            self.report({"ERROR"}, "Select an armature")
            return {"CANCELLED"}

        # Find meshes
        meshes = []
        for obj in context.scene.objects:
            if obj.type != "MESH":
                continue
            for mod in obj.modifiers:
                if mod.type == "ARMATURE" and mod.object == arm:
                    meshes.append(obj)
                    break
            if obj.parent == arm and obj not in meshes:
                meshes.append(obj)

        bpy.ops.object.mode_set(mode="OBJECT")
        # Deselect all
        for o in context.view_layer.objects:
            o.select_set(False)

        # Apply scale + rotation on armature
        arm.select_set(True)
        context.view_layer.objects.active = arm
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # Apply scale + rotation on meshes
        arm.select_set(False)
        for m in meshes:
            m.select_set(True)
            context.view_layer.objects.active = m
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            m.select_set(False)

        arm.select_set(True)
        context.view_layer.objects.active = arm
        self.report({"INFO"}, f"Applied scale+rotation on armature + {len(meshes)} mesh(es)")
        return {"FINISHED"}



def _skinned_meshes_for_arm(arm):
    meshes = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        for mod in obj.modifiers:
            if mod.type == "ARMATURE" and mod.object == arm:
                meshes.append(obj)
                break
        else:
            if obj.parent == arm:
                meshes.append(obj)
    return meshes


def _snapshot_rest_pose(arm):
    """Store current rest bones + skinned mesh vertex positions for Reset."""
    import json
    data = {}
    for b in arm.data.bones:
        head = b.head_local
        tail = b.tail_local
        m = b.matrix_local
        data[b.name] = {
            "head": [float(head[0]), float(head[1]), float(head[2])],
            "tail": [float(tail[0]), float(tail[1]), float(tail[2])],
            "matrix": [float(m[i][j]) for i in range(4) for j in range(4)],
        }
    arm["dw_rest_pose_snapshot"] = json.dumps(data)

    mesh_data = {}
    for obj in _skinned_meshes_for_arm(arm):
        mesh_data[obj.name] = [[float(c) for c in v.co] for v in obj.data.vertices]
    arm["dw_rest_mesh_snapshot"] = json.dumps(mesh_data)
    return len(data)



def _restore_rest_pose(arm):
    """Restore rest pose bones AND mesh verts from snapshot (like inverse of Apply Rest Pose)."""
    import json
    from mathutils import Matrix, Vector
    import bpy

    raw = arm.get("dw_rest_pose_snapshot")
    if not raw:
        return False, "No saved rest pose yet — use Apply Rest Pose once first (it saves a restore point)"
    try:
        data = json.loads(raw)
    except Exception as e:
        return False, f"Corrupt rest-pose snapshot: {e}"

    if bpy.context.view_layer.objects.active != arm:
        bpy.context.view_layer.objects.active = arm
    if arm.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    ebones = arm.data.edit_bones

    connect_state = {eb.name: eb.use_connect for eb in ebones}
    for eb in ebones:
        eb.use_connect = False

    restored = 0
    for name, info in data.items():
        eb = ebones.get(name)
        if eb is None:
            continue
        if isinstance(info, dict) and "head" in info and "tail" in info:
            eb.head = Vector(info["head"])
            eb.tail = Vector(info["tail"])
            if "matrix" in info:
                flat = info["matrix"]
                mat = Matrix((flat[0:4], flat[4:8], flat[8:12], flat[12:16]))
                try:
                    eb.matrix = mat
                except Exception:
                    pass
            restored += 1
        elif isinstance(info, list) and len(info) == 16:
            mat = Matrix((info[0:4], info[4:8], info[8:12], info[12:16]))
            try:
                eb.matrix = mat
                restored += 1
            except Exception:
                pass

    for name, flag in connect_state.items():
        eb = ebones.get(name)
        if eb is not None:
            eb.use_connect = flag

    bpy.ops.object.mode_set(mode="OBJECT")

    # Clear pose transforms
    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    bpy.ops.object.mode_set(mode="OBJECT")

    # Restore mesh object-space verts from snapshot
    mesh_raw = arm.get("dw_rest_mesh_snapshot")
    mesh_restored = 0
    if mesh_raw:
        try:
            mesh_data = json.loads(mesh_raw)
            for obj in _skinned_meshes_for_arm(arm):
                coords = mesh_data.get(obj.name)
                if not coords or len(coords) != len(obj.data.vertices):
                    continue
                for i, co in enumerate(coords):
                    obj.data.vertices[i].co = Vector(co)
                obj.data.update()
                mesh_restored += 1
        except Exception as e:
            print(f"[DeltaWorlds] mesh restore failed: {e}")

    if restored == 0:
        return False, (
            f"Restored 0 bones (snapshot had {len(data)}). "
            "Bone names may have changed — Apply Rest Pose again to save a new restore point."
        )
    return True, f"Restored rest pose for {restored} bones, {mesh_restored} mesh(es)"



class DW_OT_reset_rest_pose(bpy.types.Operator):
    bl_idname = "deltaworlds.reset_rest_pose"
    bl_label = "Reset Rest Pose"
    bl_description = "Restore the previous rest pose AND mesh vertex positions from the last saved restore point (undo Apply as Rest Pose / arm adjustments)"
    bl_options = {"UNDO"}

    def execute(self, context):
        arm = _get_armature(context)
        if not arm:
            self.report({"ERROR"}, "No armature selected")
            return {"CANCELLED"}
        context.view_layer.objects.active = arm
        ok, msg = _restore_rest_pose(arm)
        if not ok:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class DW_OT_apply_all(bpy.types.Operator):
    bl_idname = "deltaworlds.apply_all"
    bl_label = "Apply All"
    bl_description = "One-click pipeline: Scan+Apply Renames → Apply Rest Pose → Apply Scale/Rotation on armature and meshes"
    bl_options = {"UNDO"}

    def execute(self, context):
        arm = _get_armature(context)
        if not arm:
            self.report({"ERROR"}, "No armature selected")
            return {"CANCELLED"}

        scene = context.scene

        # 1) Apply renames if a scan list exists
        if len(scene.dw_bone_map) > 0:
            bpy.ops.deltaworlds.apply_bone_renames()

        # 2) Snapshot original rest pose once, then apply current pose as rest
        context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="POSE")
        bpy.ops.deltaworlds.apply_arm_rest_pose()

        # 3-6) Scale + rotation on armature and meshes
        bpy.ops.deltaworlds.apply_scale()

        self.report({"INFO"}, "Apply All complete")
        return {"FINISHED"}



class DW_OT_auto_rename(bpy.types.Operator):
    bl_idname = "deltaworlds.auto_rename"
    bl_label = "Auto Rename"
    bl_description = "Scan the armature in the dropdown (or first found) and immediately apply ActiveWorlds bone renames"
    bl_options = {"UNDO"}

    def execute(self, context):
        arm = _get_armature(context)
        if not arm:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}
        context.view_layer.objects.active = arm
        bpy.ops.deltaworlds.scan_bones()
        bpy.ops.deltaworlds.apply_bone_renames()
        self.report({"INFO"}, "Auto Rename complete")
        return {"FINISHED"}


class DW_OT_apply_texture(bpy.types.Operator):
    bl_idname = "deltaworlds.apply_texture"
    bl_label = "Retexture"
    bl_description = "Convert textures with the current Convert Textures settings. Uses the last .jpg/.png choice from this session (Retexture JPG or Retexture PNG)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        fmt = context.scene.get("dw_retexture_format", "JPEG") or "JPEG"
        if fmt not in ("JPEG", "PNG"):
            fmt = "JPEG"
        return bpy.ops.deltaworlds.convert_textures(file_format=fmt)



def _fbx_importer_available():
    """True if any FBX import operator is available (4.2 classic or 5.x)."""
    try:
        if hasattr(bpy.ops.import_scene, "fbx"):
            return True
    except Exception:
        pass
    try:
        if hasattr(bpy.ops.wm, "fbx_import"):
            return True
    except Exception:
        pass
    return False


def _call_fbx_import(**kwargs):
    """Call the best available FBX importer with our forced settings.

    Blender 4.2+: import_scene.fbx (shown as Legacy in 5.x — preferred for CAV avatars).
    Blender 5.x also has wm.fbx_import (newer) as fallback.
    """
    # Prefer classic/legacy importer — matches the user's 5.1 'FBX Legacy' workflow
    if hasattr(bpy.ops.import_scene, "fbx"):
        try:
            return bpy.ops.import_scene.fbx(**kwargs)
        except TypeError:
            # Older/newer property set — retry essentials only
            basic = {
                "filepath": kwargs.get("filepath", ""),
                "global_scale": kwargs.get("global_scale", 1.0),
            }
            for key in ("use_anim", "ignore_leaf_bones", "force_connect_children",
                        "automatic_bone_orientation"):
                if key in kwargs:
                    basic[key] = kwargs[key]
            try:
                return bpy.ops.import_scene.fbx(**basic)
            except TypeError:
                return bpy.ops.import_scene.fbx(
                    filepath=kwargs.get("filepath", ""),
                    global_scale=kwargs.get("global_scale", 1.0),
                )
    if hasattr(bpy.ops.wm, "fbx_import"):
        slim = {k: v for k, v in kwargs.items() if k in (
            "filepath", "global_scale", "use_anim", "ignore_leaf_bones",
            "force_connect_children", "automatic_bone_orientation",
        )}
        try:
            return bpy.ops.wm.fbx_import(**slim)
        except TypeError:
            return bpy.ops.wm.fbx_import(filepath=kwargs.get("filepath", ""))
    raise RuntimeError("No FBX importer found — enable Import-Export: FBX format in Preferences")


class DW_OT_import_fbx(bpy.types.Operator, ImportHelper):
    """Import FBX with DeltaWorlds-friendly armature settings, at the 3D cursor."""
    bl_idname = "deltaworlds.import_fbx"
    bl_label = "Import FBX"
    bl_description = (
        "Import .fbx with Scale=1, Animation off, Ignore Leaf Bones, Force Connect Children, "
        "Automatic Bone Orientation. Places the avatar at the 3D cursor and switches to Material Preview. "
        "Uses FBX Legacy importer when available (best for CAV avatars on Blender 4.2 and 5.x)."
    )
    bl_options = {"UNDO", "PRESET"}

    filename_ext = ".fbx"
    filter_glob: StringProperty(default="*.fbx;*.FBX", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return _fbx_importer_available()

    def invoke(self, context, event):
        # Switch visible 3D views to Material Preview before the file browser opens
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != "VIEW_3D":
                    continue
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        if space.shading.type != "MATERIAL":
                            space.shading.type = "MATERIAL"
        # Default folder from preferences
        prefs = _addon_prefs(context)
        if prefs and prefs.import_fbx_dir:
            self.filepath = prefs.import_fbx_dir
            if not self.filepath.endswith(("\\", "/", "\\")):
                # Ensure browser opens in folder - filepath as dir + sep
                import os
                self.filepath = os.path.join(prefs.import_fbx_dir, "")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        filepath = self.filepath
        if not filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}

        cursor = context.scene.cursor.location.copy()
        before = set(context.scene.objects)

        # Forced settings (Blender 4.2 io_scene_fbx property names)
        kwargs = dict(
            filepath=filepath,
            global_scale=1.0,
            use_anim=False,
            ignore_leaf_bones=True,
            force_connect_children=True,
            automatic_bone_orientation=True,
        )
        try:
            _call_fbx_import(**kwargs)
        except TypeError as e:
            # Older/newer FBX addon may use slightly different names — retry stripped
            self.report({"WARNING"}, f"FBX import with full settings failed ({e}); retrying minimal")
            try:
                _call_fbx_import(filepath=filepath, global_scale=1.0)
            except Exception as e2:
                self.report({"ERROR"}, f"FBX import failed: {e2}")
                return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"FBX import failed: {e}")
            return {"CANCELLED"}

        imported = [o for o in context.scene.objects if o not in before]
        if not imported:
            self.report({"WARNING"}, "Import finished but no new objects detected")
            return {"FINISHED"}

        # Move root imported objects to the 3D cursor (children follow if parented)
        roots = [o for o in imported if o.parent not in imported]
        if not roots:
            roots = imported
        for obj in roots:
            obj.location = obj.location + cursor

        # Select imported, prefer armature as active
        for o in context.view_layer.objects:
            o.select_set(False)
        arm = None
        for o in imported:
            o.select_set(True)
            if o.type == "ARMATURE":
                arm = o
        context.view_layer.objects.active = arm or roots[0]

        # Seed armature dropdown if possible
        if arm is not None:
            try:
                context.scene.dw_armature_name = arm.name
            except Exception:
                pass

        # Remember FBX folder for Fix Missing Textures
        try:
            from pathlib import Path as _P
            context.scene["dw_last_fbx_dir"] = str(_P(filepath).parent)
        except Exception:
            pass

        self.report(
            {"INFO"},
            f"Imported {len(imported)} object(s) at cursor"
            + (f" (armature: {arm.name})" if arm else ""),
        )
        return {"FINISHED"}



class DW_OT_fix_missing_textures(bpy.types.Operator):
    bl_idname = "deltaworlds.fix_missing_textures"
    bl_label = "Fix Missing Textures"
    bl_description = (
        "Relink missing textures by searching the last FBX import folder (and its subfolders), "
        "then parent folders, then the .blend folder — same idea as File > External Data > Find Missing Files"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from pathlib import Path as P
        import os

        def search_tree(root_dir, filename, max_depth=8):
            """Recursive search under root_dir (like Blender's Find Missing Files)."""
            if not root_dir or not filename:
                return None
            target = filename.lower()
            root = P(root_dir)
            if not root.is_dir():
                return None
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    # Limit how deep we recurse within this root
                    try:
                        rel = P(dirpath).relative_to(root)
                        depth = len(rel.parts)
                    except Exception:
                        depth = 0
                    if depth > max_depth:
                        dirnames[:] = []
                        continue
                    # Skip huge/irrelevant trees
                    skip = {".git", "__pycache__", "node_modules", ".svn"}
                    dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
                    for f in filenames:
                        if f.lower() == target:
                            return P(dirpath) / f
            except Exception as e:
                print(f"[DeltaWorlds] search error in {root}: {e}")
            return None

        def search_up(start_dir, filename, max_levels=20):
            """At each folder level, search that folder and all subfolders, then go up one."""
            if not start_dir or not filename:
                return None
            current = P(start_dir)
            for level in range(max_levels):
                print(f"[DeltaWorlds] Scanning tree (level {level}): {current}")
                found = search_tree(current, filename, max_depth=8)
                if found is not None:
                    return found
                parent = current.parent
                if parent == current:
                    break
                current = parent
            return None

        def image_is_missing(img):
            if img is None:
                return False
            if img.packed_file:
                return False
            if img.name.startswith("Render Result") or img.name.startswith("Viewer Node"):
                return False
            fp = img.filepath
            if not fp:
                try:
                    return img.size[0] == 0
                except Exception:
                    return True
            return not os.path.isfile(bpy.path.abspath(fp))

        def collect_images():
            """Images used by material Base Color slots first, then any other missing images."""
            ordered = []
            seen = set()
            for mat in bpy.data.materials:
                if not mat or not mat.use_nodes or not mat.node_tree:
                    continue
                principled = next(
                    (n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"),
                    None,
                )
                nodes_to_check = []
                if principled:
                    inp = principled.inputs.get("Base Color")
                    if inp and inp.is_linked:
                        node = inp.links[0].from_node
                        visited = set()
                        while node and node not in visited:
                            visited.add(node)
                            if node.type == "TEX_IMAGE":
                                nodes_to_check.append(node)
                                break
                            nxt = None
                            for s in node.inputs:
                                if s.is_linked:
                                    nxt = s.links[0].from_node
                                    break
                            node = nxt
                for n in mat.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n not in nodes_to_check:
                        nodes_to_check.append(n)
                for n in nodes_to_check:
                    if n.image and n.image.name not in seen:
                        seen.add(n.image.name)
                        ordered.append(n.image)
            for img in bpy.data.images:
                if img.name not in seen:
                    seen.add(img.name)
                    ordered.append(img)
            return ordered

        # --- Search roots: last FBX dir first, then .blend dir ---
        fbx_dir = context.scene.get("dw_last_fbx_dir", "") or ""
        blend = bpy.data.filepath
        blend_dir = str(P(blend).parent) if blend else ""

        search_roots = []
        if fbx_dir and os.path.isdir(fbx_dir):
            search_roots.append(fbx_dir)
        if blend_dir and blend_dir not in search_roots and os.path.isdir(blend_dir):
            search_roots.append(blend_dir)
        if not search_roots:
            search_roots.append(os.getcwd())

        print(f"[DeltaWorlds] Fix textures search roots: {search_roots}")

        fixed = []
        missing_still = []

        for img in collect_images():
            if not image_is_missing(img):
                continue

            # Candidate filenames
            names = []
            if img.filepath:
                names.append(P(bpy.path.abspath(img.filepath)).name)
                names.append(P(img.filepath).name)
            names.append(P(img.name).name)
            # unique preserve order
            cand_names = []
            for n in names:
                if n and n not in cand_names:
                    cand_names.append(n)

            found = None
            used_name = cand_names[0] if cand_names else img.name
            for root in search_roots:
                for cand in cand_names:
                    print(f"[DeltaWorlds] Looking for '{cand}' starting in {root}")
                    found = search_up(root, cand)
                    if found is not None:
                        used_name = cand
                        break
                if found is not None:
                    break

            if found is None:
                missing_still.append(used_name)
                print(f"[DeltaWorlds] Could not find: {used_name}")
                continue

            try:
                img.filepath = str(found)
                img.source = "FILE"
                img.reload()
                fixed.append(f"{used_name} → {found}")
                print(f"[DeltaWorlds] Fixed texture: {used_name} → {found}")
            except Exception as e:
                missing_still.append(f"{used_name} ({e})")
                print(f"[DeltaWorlds] Failed to relink {used_name}: {e}")

        if not fixed and not missing_still:
            self.report({"INFO"}, "No missing textures detected")
        elif missing_still and not fixed:
            self.report({"ERROR"}, f"Could not find! ({len(missing_still)} missing)")
        elif missing_still:
            self.report(
                {"WARNING"},
                f"Fixed {len(fixed)}, could not find {len(missing_still)} — see console",
            )
        else:
            self.report({"INFO"}, f"Fixed {len(fixed)} texture(s)")
        return {"FINISHED"}





def _show_armature_bones(arm):
    """Show bone names, In Front, Octahedral display."""
    if arm is None or arm.type != "ARMATURE":
        return
    arm.show_in_front = True
    try:
        arm.data.show_names = True
    except Exception:
        pass
    try:
        arm.data.display_type = "OCTAHEDRAL"
    except Exception:
        pass

def _find_head_bone(arm_obj):
    """Best-effort detect the head bone on an armature."""
    import re
    patterns = [
        re.compile(r"^aw_head$", re.I),
        re.compile(r"^head$", re.I),
        re.compile(r"bip0?1[_\s\-]?head$", re.I),
        re.compile(r"mixamorig:?head$", re.I),
        re.compile(r"mixamo[_\s\-]?head$", re.I),
        re.compile(r"^head\.\d+$", re.I),
        re.compile(r"01head", re.I),
        re.compile(r"[_\-]head$", re.I),
        re.compile(r"^head[_\-]", re.I),
    ]
    bones = list(arm_obj.data.bones)
    # Prefer exact-ish matches first
    for pat in patterns:
        for b in bones:
            if pat.search(b.name):
                return arm_obj.pose.bones.get(b.name)
    # Last resort: any bone with 'head' in the name that is not a helper like 'forehead tip' only if no better
    for b in bones:
        n = b.name.lower()
        if "head" in n and "ahead" not in n:
            return arm_obj.pose.bones.get(b.name)
    return None


def _iter_bone_descendants(pose_bone):
    """Yield pose_bone's children, grandchildren, … (not including pose_bone itself)."""
    stack = list(pose_bone.children)
    while stack:
        pb = stack.pop()
        yield pb
        stack.extend(list(pb.children))


class DW_OT_scale_face_bones(bpy.types.Operator):
    bl_idname = "deltaworlds.scale_face_bones"
    bl_label = "Scale Face Bones"
    bl_description = (
        "Disconnect target bones (keep parenting), then scale in Edit Mode with "
        "Individual Origins so heads/offsets stay put and only bone lengths change"
    )
    bl_options = {"UNDO"}

    direction: StringProperty(default="down")  # down | up
    scope: StringProperty(default="face")  # face | body

    def execute(self, context):
        arm = _get_armature(context)
        if not arm:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}

        context.view_layer.objects.active = arm
        head = _find_head_bone(arm)
        factor = 0.75 if self.direction == "down" else 1.25

        if self.scope == "face":
            if head is None:
                self.report({"ERROR"}, "Could not find a Head bone")
                return {"CANCELLED"}
            names = [pb.name for pb in _iter_bone_descendants(head)]
            if not names:
                self.report({"WARNING"}, f"Head bone '{head.name}' has no children")
                return {"CANCELLED"}
            label = f"face bones under '{head.name}'"
        else:
            # Body = everything except face descendants; INCLUDE the head bone itself
            face_only = set()
            if head is not None:
                face_only.update(pb.name for pb in _iter_bone_descendants(head))
            names = [b.name for b in arm.data.bones if b.name not in face_only]
            if not names:
                self.report({"WARNING"}, "No body bones to scale")
                return {"CANCELLED"}
            label = "body bones (incl. head)"

        bpy.ops.object.mode_set(mode="EDIT")
        ebones = arm.data.edit_bones

        # 1) Disconnect (keep parent) so heads are free — same as face bones
        #    Do NOT reconnect afterward; offsets must stay after scale.
        disconnected = 0
        for name in names:
            eb = ebones.get(name)
            if eb is None:
                continue
            if eb.use_connect:
                eb.use_connect = False
                disconnected += 1

        # 2) Select targets
        for eb in ebones:
            eb.select = False
            eb.select_head = False
            eb.select_tail = False

        selected = 0
        for name in names:
            eb = ebones.get(name)
            if eb is None:
                continue
            eb.select = True
            eb.select_head = True
            eb.select_tail = True
            selected += 1

        if selected == 0:
            bpy.ops.object.mode_set(mode="OBJECT")
            self.report({"WARNING"}, "No editable bones found to scale")
            return {"CANCELLED"}

        # 3) Scale with Individual Origins (heads fixed, lengths change)
        context.view_layer.objects.active = arm
        ts = context.scene.tool_settings
        prev_pivot = ts.transform_pivot_point
        ts.transform_pivot_point = "INDIVIDUAL_ORIGINS"
        try:
            bpy.ops.transform.resize(
                value=(factor, factor, factor),
                orient_type="GLOBAL",
            )
        except Exception as e:
            ts.transform_pivot_point = prev_pivot
            bpy.ops.object.mode_set(mode="OBJECT")
            self.report({"ERROR"}, f"Scale failed: {e}")
            return {"CANCELLED"}
        ts.transform_pivot_point = prev_pivot

        bpy.ops.object.mode_set(mode="OBJECT")

        msg = (
            f"Scaled {selected} {label} "
            f"{'down' if factor < 1 else 'up'} ×{factor:.2f}"
        )
        if disconnected:
            msg += f" (disconnected {disconnected} linked bones, parents kept)"
        self.report({"INFO"}, msg)
        return {"FINISHED"}




_TEX_SIZE_STEPS = (128, 256, 512, 1024, 2048, 4096)
_TEX_MAX_KB_STEPS = (10, 25, 50, 100, 200, 400, 600, 800, 1024, 1536, 2048, 4096, 10240)


class DW_OT_step_tex_size(bpy.types.Operator):
    bl_idname = "deltaworlds.step_tex_size"
    bl_label = "Step Texture Size"
    bl_description = "Cycle texture size through 128 → 256 → 512 → 1024 → 2048 → 4096"
    bl_options = {"INTERNAL"}

    direction: StringProperty(default="up")  # up | down

    def execute(self, context):
        scene = context.scene
        cur = int(scene.dw_tex_size)
        steps = list(_TEX_SIZE_STEPS)
        if cur in steps:
            idx = steps.index(cur)
            idx = min(idx + 1, len(steps) - 1) if self.direction == "up" else max(idx - 1, 0)
        else:
            above = [s for s in steps if s > cur]
            below = [s for s in steps if s < cur]
            if self.direction == "up":
                idx = steps.index(above[0]) if above else len(steps) - 1
            else:
                idx = steps.index(below[-1]) if below else 0
        scene.dw_tex_size = steps[idx]
        return {"FINISHED"}


class DW_OT_step_tex_max_kb(bpy.types.Operator):
    bl_idname = "deltaworlds.step_tex_max_kb"
    bl_label = "Step Max File Size"
    bl_description = "Cycle max file size through 10KB … 10MB presets"
    bl_options = {"INTERNAL"}

    direction: StringProperty(default="up")  # up | down

    def execute(self, context):
        scene = context.scene
        cur = int(scene.dw_tex_max_kb)
        steps = list(_TEX_MAX_KB_STEPS)
        if cur in steps:
            idx = steps.index(cur)
            idx = min(idx + 1, len(steps) - 1) if self.direction == "up" else max(idx - 1, 0)
        else:
            above = [s for s in steps if s > cur]
            below = [s for s in steps if s < cur]
            if self.direction == "up":
                idx = steps.index(above[0]) if above else len(steps) - 1
            else:
                idx = steps.index(below[-1]) if below else 0
        scene.dw_tex_max_kb = steps[idx]
        return {"FINISHED"}



class DW_OT_apply_preferences(bpy.types.Operator):
    bl_idname = "deltaworlds.apply_preferences"
    bl_label = "Apply"
    bl_description = "Apply preference values to the current Blender session (N-panel prefix and default folders)"
    bl_options = {"REGISTER"}

    def execute(self, context):
        prefs = _addon_prefs(context)
        if prefs is None:
            self.report({"ERROR"}, "Could not access addon preferences")
            return {"CANCELLED"}
        # Sync prefix into every scene so the N-panel updates immediately
        for scene in bpy.data.scenes:
            scene.dw_tex_prefix = prefs.tex_prefix or ""
        self.report({"INFO"}, "Preferences applied")
        return {"FINISHED"}


classes = (
    DW_AddonPreferences,
    DW_OT_apply_preferences,
    DW_OT_step_tex_size,
    DW_OT_step_tex_max_kb,
    DW_OT_scale_face_bones,
    DW_OT_import_fbx,
    DW_OT_fix_missing_textures,
    ExportDeltaWorldsX,
    DWBoneMapItem,
    DW_UL_bone_map,
    DW_OT_scan_bones,
    DW_OT_apply_bone_renames,
    DW_OT_adjust_arm_bones,
    DW_OT_apply_arm_rest_pose,
    DW_OT_save_arm_preset,
    DW_OT_load_arm_preset,
    DW_OT_export_directx,
    DW_OT_convert_textures,
    DW_OT_reset_arm_history,
    DW_OT_apply_scale,
    DW_OT_reset_rest_pose,
    DW_OT_apply_all,
    DW_OT_auto_rename,
    DW_OT_apply_texture,
    DW_PT_bone_panel,
)



@bpy.app.handlers.persistent
def _dw_load_post(_dummy):
    prefs = _addon_prefs()
    if prefs is None:
        return
    for scene in bpy.data.scenes:
        if not scene.dw_tex_prefix and prefs.tex_prefix:
            scene.dw_tex_prefix = prefs.tex_prefix


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.Scene.dw_bone_map = CollectionProperty(type=DWBoneMapItem)
    bpy.types.Scene.dw_bone_map_index = IntProperty(name="Bone Map Index", default=0)
    bpy.types.Scene.dw_viewport_show_bones = BoolProperty(
        name="Show bones",
        description="Show bone names on all armatures and draw them In Front",
        default=False,
        update=_update_show_bones,
    )
    bpy.types.Scene.dw_rename_unused_bones = BoolProperty(
        name="Rename unused bones",
        description="Rename leftover non-AW bones to aw_unused1, aw_unused2, … so skin weights (tongue, etc.) stay bound and DeltaWorlds still accepts the hierarchy",
        default=True,
        update=lambda self, ctx: (
            setattr(self, "dw_delete_unused_bones", False)
            if getattr(self, "dw_rename_unused_bones", False)
            and getattr(self, "dw_delete_unused_bones", False)
            else None
        ),
    )
    bpy.types.Scene.dw_delete_unused_bones = BoolProperty(
        name="Delete unused bones",
        description="Delete bones that do not get an aw_* name (reparents children, removes matching vertex groups). Mutually exclusive with Rename unused bones",
        default=False,
        update=lambda self, ctx: (
            setattr(self, "dw_rename_unused_bones", False)
            if getattr(self, "dw_delete_unused_bones", False)
            and getattr(self, "dw_rename_unused_bones", False)
            else None
        ),
    )
    bpy.types.Scene.dw_armature_name = EnumProperty(
        name="Armature",
        description="Armature targeted by Scan, Apply Renames, Arm Position, Scale Face/Body, and Apply All",
        items=_armature_enum_items,
    )
    bpy.types.Scene.dw_tex_prefix = StringProperty(
        name="Prefix",
        description="Prefix for converted texture filenames (e.g. ocm_) — remembered between sessions",
        default="",
        update=_update_tex_prefix,
    )
    bpy.types.Scene.dw_tex_only_selected = BoolProperty(
        name="Only Selected Meshes",
        description="When checked, only convert materials on the selected mesh object(s). Select one or multiple meshes in the viewport",
        default=False,
    )
    bpy.types.Scene.dw_tex_size = IntProperty(
        name="Texture Size",
        description="Target size in pixels. With Keep ratio: longest side matches this size. Use ▲/▼ to step 128→256→…→4096",
        default=1024,
        min=16,
        max=8192,
    )

    bpy.types.Scene.dw_tex_max_kb = IntProperty(
        name="Max Size (KB)",
        description="Maximum JPEG file size in KB. Use ▲/▼ to step through 10KB…10MB presets. PNG ignores this limit",
        default=600,
        min=10,
        max=10240,
    )

    bpy.types.Scene.dw_tex_keep_aspect = BoolProperty(
        name="Keep ratio",
        description="Preserve aspect ratio when resizing (scale longest side to Texture Size)",
        default=True,
    )
    bpy.types.Scene.dw_tex_copy_with_x = BoolProperty(
        name="Export with .x",
        description="On Export DirectX, copy used texture files next to the .x (not inside a zip)",
        default=True,
    )
    bpy.types.Scene.dw_show_fbx = BoolProperty(name="FBX", default=True)
    bpy.types.Scene.dw_show_armature = BoolProperty(name="Armature", default=False)
    bpy.types.Scene.dw_show_bones = BoolProperty(name="Bone Names", default=False)
    bpy.types.Scene.dw_show_armpos = BoolProperty(name="Arm Position", default=False)
    bpy.types.Scene.dw_show_textures = BoolProperty(name="Convert Textures", default=False)

    bpy.app.handlers.load_post.append(_dw_load_post)
    # seed prefix from prefs into current scenes
    prefs = _addon_prefs()
    if prefs and prefs.tex_prefix:
        for scene in bpy.data.scenes:
            if not scene.dw_tex_prefix:
                scene.dw_tex_prefix = prefs.tex_prefix


def unregister():
    if _dw_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_dw_load_post)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    del bpy.types.Scene.dw_bone_map
    del bpy.types.Scene.dw_bone_map_index
    del bpy.types.Scene.dw_viewport_show_bones
    del bpy.types.Scene.dw_rename_unused_bones
    del bpy.types.Scene.dw_delete_unused_bones
    del bpy.types.Scene.dw_armature_name
    del bpy.types.Scene.dw_tex_prefix
    del bpy.types.Scene.dw_tex_only_selected
    del bpy.types.Scene.dw_tex_size
    del bpy.types.Scene.dw_tex_max_kb
    del bpy.types.Scene.dw_tex_keep_aspect
    del bpy.types.Scene.dw_tex_copy_with_x
    del bpy.types.Scene.dw_show_textures
    del bpy.types.Scene.dw_show_armpos
    del bpy.types.Scene.dw_show_bones
    del bpy.types.Scene.dw_show_fbx
    del bpy.types.Scene.dw_show_armature
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
