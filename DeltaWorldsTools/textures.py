"""Texture conversion utilities for DeltaWorlds / ActiveWorlds compatibility."""

from __future__ import annotations

import os
import re
from pathlib import Path

import bpy


def sanitize_dw_name(name: str, prefix: str = "") -> str:
    """Lowercase, spaces/special → underscores, apply prefix. Strip extension."""
    stem = Path(name).stem
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    prefix = (prefix or "").lower()
    prefix = re.sub(r"[^a-z0-9_]+", "_", prefix)
    if prefix and not prefix.endswith("_"):
        # keep trailing underscore if user typed it; otherwise don't force one
        pass
    if prefix and stem.startswith(prefix):
        return stem
    return f"{prefix}{stem}" if prefix else stem


def _find_basecolor_image_node(mat: bpy.types.Material):
    """Return (tex_node, image) connected to Principled BSDF Base Color, or (None, None)."""
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None, None
    nt = mat.node_tree
    principled = None
    for n in nt.nodes:
        if n.type == "BSDF_PRINCIPLED":
            principled = n
            break
    if not principled:
        return None, None
    inp = principled.inputs.get("Base Color")
    if not inp or not inp.is_linked:
        # try unconnected image node as fallback
        for n in nt.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                return n, n.image
        return None, None
    link = inp.links[0]
    from_node = link.from_node
    # Walk through common intermediate nodes (RGB, gamma, etc.) to find TEX_IMAGE
    visited = set()
    node = from_node
    while node and node not in visited:
        visited.add(node)
        if node.type == "TEX_IMAGE" and node.image:
            return node, node.image
        # follow first color-like input
        for socket in node.inputs:
            if socket.is_linked and socket.links:
                node = socket.links[0].from_node
                break
        else:
            break
    return None, None


def simplify_material_nodes(mat: bpy.types.Material, image: bpy.types.Image) -> bool:
    """
    Strip material to: Image Texture → Principled BSDF Base Color → Material Output.
    Returns True on success.
    """
    if not mat.use_nodes:
        mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links

    # Clear everything
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    tex = nodes.new("ShaderNodeTexImage")
    tex.location = (-300, 0)
    tex.image = image

    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # DeltaWorlds-friendly defaults
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = 1.0
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 0.0
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 1.0
    return True


def _resize_max(w: int, h: int, max_dim: int = 2048):
    if w <= max_dim and h <= max_dim:
        return w, h
    scale = max_dim / float(max(w, h))
    return max(1, int(round(w * scale))), max(1, int(round(h * scale)))


def convert_image_file(
    src_image: bpy.types.Image,
    out_format: str,
    prefix: str = "",
    target_size: int = 2048,
    keep_aspect: bool = True,
    max_jpg_bytes: int = 1_000_000,
) -> bpy.types.Image | None:
    """
    Resize/compress and save a new image next to the source file.
    out_format: 'JPEG' or 'PNG'
    Returns the new bpy Image datablock (loaded), or None on failure.
    """
    # Resolve source path (works for jpg/png/tga/bmp/tif/dds/webp and packed images)
    src_path = ""
    if src_image.filepath:
        src_path = bpy.path.abspath(src_image.filepath)
    if src_path and os.path.isfile(src_path):
        folder = str(Path(src_path).parent)
        base_name = Path(src_path).name
    else:
        # Packed or generated image — save next to the .blend (or cwd)
        blend = bpy.data.filepath
        folder = str(Path(blend).parent) if blend else os.getcwd()
        base_name = src_image.name
        # Ensure pixels are available for packed images
        try:
            if src_image.packed_file:
                src_image.unpack(method="USE_ORIGINAL")
                if src_image.filepath:
                    p2 = bpy.path.abspath(src_image.filepath)
                    if os.path.isfile(p2):
                        folder = str(Path(p2).parent)
                        base_name = Path(p2).name
        except Exception:
            pass

    stem = sanitize_dw_name(base_name, prefix)
    ext = ".jpg" if out_format.upper() in ("JPEG", "JPG") else ".png"
    out_path = os.path.join(folder, stem + ext)

    # Work on a copy so we don't destroy the original datablock in-place oddly
    # Ensure pixels are loaded
    try:
        src_image.pixels[0]
    except Exception:
        try:
            src_image.reload()
        except Exception:
            pass

    w, h = src_image.size
    if w < 1 or h < 1:
        return None
    target_size = max(1, int(target_size))
    if keep_aspect:
        nw, nh = _resize_max(w, h, target_size)
    else:
        # Force both dimensions to target_size (may stretch)
        nw, nh = target_size, target_size

    # Create temporary image, copy pixels (with optional scale)
    tmp_name = f"_dw_tmp_{stem}"
    if tmp_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[tmp_name])
    tmp = bpy.data.images.new(tmp_name, width=w, height=h, alpha=True)
    try:
        # copy pixels
        if len(src_image.pixels) == len(tmp.pixels):
            tmp.pixels = src_image.pixels[:]
        else:
            # different depth — try pack/reload path via save of source
            tmp.pixels = src_image.pixels[:]
        if (nw, nh) != (w, h):
            tmp.scale(nw, nh)

        if out_format.upper() in ("JPEG", "JPG"):
            # Iteratively reduce quality to fit under max_jpg_bytes
            quality = 95
            saved = False
            while quality >= 20:
                tmp.filepath_raw = out_path
                tmp.file_format = "JPEG"
                # Blender 4.x uses save with scene settings; set quality via image settings
                # Use save_render style via image.save() after setting format
                try:
                    # Blender stores JPEG quality on scene.render.image_settings when using save_render
                    # For image.save(), set:
                    tmp.save()
                except Exception:
                    # fallback: write via save_render to a temp scene setting
                    pass

                # Better approach: use image.filepath_raw + save with format
                # Blender 4.2 Image.save() respects image.file_format
                # Quality is controlled by context scene for some versions — try both
                scene = bpy.context.scene
                old_fmt = scene.render.image_settings.file_format
                old_q = scene.render.image_settings.quality
                old_c = scene.render.image_settings.color_mode
                try:
                    scene.render.image_settings.file_format = "JPEG"
                    scene.render.image_settings.quality = quality
                    scene.render.image_settings.color_mode = "RGB"
                    tmp.filepath_raw = out_path
                    tmp.file_format = "JPEG"
                    # save_render works more reliably for quality
                    tmp.save_render(out_path)
                finally:
                    scene.render.image_settings.file_format = old_fmt
                    scene.render.image_settings.quality = old_q
                    scene.render.image_settings.color_mode = old_c

                if os.path.isfile(out_path) and os.path.getsize(out_path) <= max_jpg_bytes:
                    saved = True
                    break
                quality -= 10
            if not saved and os.path.isfile(out_path):
                # accept best effort at quality 20
                saved = True
            if not saved:
                return None
        else:
            scene = bpy.context.scene
            old_fmt = scene.render.image_settings.file_format
            old_c = scene.render.image_settings.color_mode
            old_depth = scene.render.image_settings.color_depth
            try:
                scene.render.image_settings.file_format = "PNG"
                scene.render.image_settings.color_mode = "RGBA"
                scene.render.image_settings.color_depth = "8"
                tmp.filepath_raw = out_path
                tmp.file_format = "PNG"
                tmp.save_render(out_path)
            finally:
                scene.render.image_settings.file_format = old_fmt
                scene.render.image_settings.color_mode = old_c
                scene.render.image_settings.color_depth = old_depth
            if not os.path.isfile(out_path):
                return None
    finally:
        bpy.data.images.remove(tmp)

    # Load result as a proper image datablock
    # Remove existing with same filepath if present
    for img in list(bpy.data.images):
        if bpy.path.abspath(img.filepath) == out_path and img.name != stem + ext:
            pass
    new_img = bpy.data.images.load(out_path, check_existing=True)
    new_img.name = stem + ext
    return new_img


def iter_target_materials(context, only_selected: bool):
    """Yield unique materials to process."""
    mats = []
    seen = set()
    if only_selected:
        objs = [o for o in context.selected_objects if o.type == "MESH"]
        if not objs and context.object and context.object.type == "MESH":
            objs = [context.object]
        for obj in objs:
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.name not in seen:
                    seen.add(mat.name)
                    mats.append(mat)
    else:
        for mat in bpy.data.materials:
            if mat.name not in seen:
                seen.add(mat.name)
                mats.append(mat)
    return mats


def convert_scene_textures(
    context,
    out_format: str,
    prefix: str = "",
    only_selected: bool = False,
    target_size: int = 1024,
    keep_aspect: bool = True,
    max_jpg_bytes: int = 1_000_000,
):
    """
    Convert all (or selected) materials' base-color textures.
    Supports common formats Blender can load (jpg/png/tga/bmp/tif/dds/webp/hdr…).
    Returns (success_count, fail_count, messages)
    """
    mats = iter_target_materials(context, only_selected)
    ok, fail = 0, 0
    messages = []
    for mat in mats:
        tex_node, image = _find_basecolor_image_node(mat)
        if not image:
            messages.append(f"{mat.name}: no base-color image, skipped")
            fail += 1
            continue
        new_img = convert_image_file(
            image,
            out_format,
            prefix=prefix,
            target_size=target_size,
            keep_aspect=keep_aspect,
            max_jpg_bytes=max_jpg_bytes,
        )
        if not new_img:
            messages.append(f"{mat.name}: convert failed for {image.name}")
            fail += 1
            continue
        simplify_material_nodes(mat, new_img)
        messages.append(f"{mat.name}: → {new_img.name}")
        ok += 1
    return ok, fail, messages
