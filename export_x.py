# ##### BEGIN GPL LICENSE BLOCK #####
# DeltaWorlds / ActiveWorlds DirectX .x exporter v0.8
# Uses Ultimate Unwrap axis matrix so matrixOffset matches working UU files
# ##### END GPL LICENSE BLOCK #####

import bpy
from mathutils import Matrix, Vector
from pathlib import Path

EXPORTER_VERSION = "1.0.5 Alpha"


def mat4_to_x(m, indent=0):
    pad = " " * indent
    r = m.to_3x3()
    t = m.to_translation()
    lines = [
        pad + f"{r[0][0]:.6f}, {r[0][1]:.6f}, {r[0][2]:.6f}, 0.000000,",
        pad + f"{r[1][0]:.6f}, {r[1][1]:.6f}, {r[1][2]:.6f}, 0.000000,",
        pad + f"{r[2][0]:.6f}, {r[2][1]:.6f}, {r[2][2]:.6f}, 0.000000,",
        pad + f"{t[0]:.6f}, {t[1]:.6f}, {t[2]:.6f}, 1.000000;;",
    ]
    return "\n".join(lines)


def make_axis_matrix(axis_conversion, scale=0.01):
    s = scale
    if axis_conversion == "UU":
        # UU style: (x,y,z) -> (s*x, -s*z, s*y)
        return Matrix((
            (s,  0,  0, 0),
            (0,  0, -s, 0),
            (0,  s,  0, 0),
            (0,  0,  0, 1),
        ))
    elif axis_conversion == "NONE":
        return Matrix((
            (s, 0, 0, 0),
            (0, s, 0, 0),
            (0, 0, s, 0),
            (0, 0, 0, 1),
        ))
    else:
        # Simple Y-up: (x,y,z) -> (s*x, s*z, -s*y)
        return Matrix((
            (s,  0, 0, 0),
            (0,  0, s, 0),
            (0, -s, 0, 0),
            (0,  0, 0, 1),
        ))


def parent_relative_matrix(bone):
    if bone.parent:
        return bone.parent.matrix_local.inverted() @ bone.matrix_local
    return bone.matrix_local.copy()


def collect_bones(arm_obj, only_aw=True):
    """Collect bone frames for the .x hierarchy.

    only_aw=True (default): skip bones whose names do not start with 'aw_'.
    When an intermediate bone is skipped, its transform is accumulated so
    children keep the correct parent-relative matrix relative to the nearest
    kept ancestor.
    """
    arm = arm_obj.data
    bones = []

    def walk(bone, parent_name, accumulated=None):
        local = parent_relative_matrix(bone)
        if accumulated is not None:
            local = accumulated @ local

        is_aw = bone.name.lower().startswith("aw_")
        if is_aw or not only_aw:
            bones.append((bone.name, parent_name, local))
            next_parent = bone.name
            next_acc = None
        else:
            # skip this bone; children inherit nearest kept parent + accumulated mat
            next_parent = parent_name
            next_acc = local

        for child in bone.children:
            walk(child, next_parent, next_acc)

    for root in arm.bones:
        if root.parent is None:
            walk(root, None, None)
    return bones


def find_skinned_meshes(arm_obj, only_selected=False):
    result = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if only_selected and not obj.select_get():
            continue
        for mod in obj.modifiers:
            if mod.type == "ARMATURE" and mod.object == arm_obj:
                result.append(obj)
                break
        if obj.parent == arm_obj and obj not in result:
            result.append(obj)
    return result


def _mat_basecolor_texture_name(mat):
    """Best-effort filename of the image plugged into Principled Base Color."""
    if not mat:
        return None
    if mat.use_nodes and mat.node_tree:
        principled = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if principled:
            inp = principled.inputs.get("Base Color")
            if inp and inp.is_linked:
                node = inp.links[0].from_node
                visited = set()
                while node and node not in visited:
                    visited.add(node)
                    if node.type == "TEX_IMAGE" and node.image:
                        img = node.image
                        if img.filepath:
                            return Path(bpy.path.abspath(img.filepath)).name
                        return Path(img.name).name
                    advanced = False
                    for s in node.inputs:
                        if s.is_linked:
                            node = s.links[0].from_node
                            advanced = True
                            break
                    if not advanced:
                        break
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                img = n.image
                if img.filepath:
                    return Path(bpy.path.abspath(img.filepath)).name
                return Path(img.name).name
    return None


def collect_mesh_materials(mesh_obj):
    """Return list of texture filenames, one per material slot (None if none)."""
    result = []
    for slot in mesh_obj.material_slots:
        result.append(_mat_basecolor_texture_name(slot.material))
    if not result:
        result = [None]
    return result


def find_texture_name(mesh_obj):
    """Back-compat: first available texture name."""
    for t in collect_mesh_materials(mesh_obj):
        if t:
            return t
    return None


def extract_mesh_data(mesh_obj, arm_obj, mesh_xform, flip_v=True, flip_faces=False):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = mesh_obj.evaluated_get(depsgraph)
    me = eval_obj.to_mesh()
    me.calc_loop_triangles()

    vg_to_bone = {i: vg.name for i, vg in enumerate(mesh_obj.vertex_groups)}
    obj_to_arm = arm_obj.matrix_world.inverted() @ mesh_obj.matrix_world
    uv_layer = me.uv_layers.active

    key_to_new = {}
    new_verts = []
    new_normals = []
    new_uvs = []

    def get_uv(loop_index):
        if uv_layer is None:
            return (0.0, 0.0)
        uv = uv_layer.data[loop_index].uv
        u, v = float(uv[0]), float(uv[1])
        if flip_v:
            v = 1.0 - v
        return (u, v)

    faces = []
    face_mat_indices = []
    n_slots = max(1, len(mesh_obj.material_slots))
    for tri in me.loop_triangles:
        face_idxs = []
        for i in range(3):
            vi = tri.vertices[i]
            li = tri.loops[i]
            u, v = get_uv(li)
            key = (vi, round(u, 5), round(v, 5))
            if key not in key_to_new:
                key_to_new[key] = len(new_verts)
                co = mesh_xform @ (obj_to_arm @ me.vertices[vi].co)
                n = (mesh_xform.to_3x3() @ (obj_to_arm.to_3x3() @ me.vertices[vi].normal)).normalized()
                new_verts.append(co)
                new_normals.append(n)
                new_uvs.append((u, v))
            face_idxs.append(key_to_new[key])
        if flip_faces:
            face_idxs = face_idxs[::-1]
        faces.append(face_idxs)
        mi = int(getattr(tri, "material_index", 0)) % n_slots
        face_mat_indices.append(mi)

    new_to_orig = {new_i: vi for (vi, _, _), new_i in key_to_new.items()}
    weights_by_bone = {}
    for new_i, orig_vi in new_to_orig.items():
        v = me.vertices[orig_vi]
        for g in v.groups:
            bone_name = vg_to_bone.get(g.group)
            if bone_name is None:
                continue
            weights_by_bone.setdefault(bone_name, []).append((new_i, g.weight))

    eval_obj.to_mesh_clear()
    return new_verts, faces, new_normals, new_uvs, weights_by_bone, face_mat_indices


def compute_matrix_offsets(arm_obj, bone_list, mesh_xform):
    """
    Inverse bind pose for DirectX skinning.
    mat4_to_x already lays translation in the last row; we additionally
    transpose the 3x3 so offsets match Ultimate Unwrap (fixes arm stretch).
    """
    offsets = {}
    arm = arm_obj.data
    for name, parent, _ in bone_list:
        bone = arm.bones.get(name)
        if bone is None:
            offsets[name] = Matrix.Identity(4)
            continue
        bind = mesh_xform @ bone.matrix_local
        try:
            inv = bind.inverted()
            # Transpose rotation, keep translation
            r = inv.to_3x3().transposed()
            tr = inv.to_translation()
            m = r.to_4x4()
            m.translation = tr
            offsets[name] = m
        except Exception:
            offsets[name] = Matrix.Identity(4)
    return offsets


def write_templates(f):
    f.write("xof 0303txt 0032\n\n")
    f.write(f"// DeltaWorlds / ActiveWorlds DirectX .x exporter v{EXPORTER_VERSION}\n")
    f.write("// Compatible with Ultimate Unwrap style CAV avatars\n\n")

    templates = [
        ("Header", "3D82AB43-62DA-11cf-AB39-0020AF71E433",
         "WORD major;\n WORD minor;\n DWORD flags;"),
        ("Vector", "3D82AB5E-62DA-11cf-AB39-0020AF71E433",
         "FLOAT x;\n FLOAT y;\n FLOAT z;"),
        ("Coords2d", "F6F23F44-7686-11cf-8F52-0040333594A3",
         "FLOAT u;\n FLOAT v;"),
        ("Matrix4x4", "F6F23F45-7686-11cf-8F52-0040333594A3",
         "array FLOAT matrix[16];"),
        ("ColorRGBA", "35FF44E0-6C7C-11cf-8F52-0040333594A3",
         "FLOAT red;\n FLOAT green;\n FLOAT blue;\n FLOAT alpha;"),
        ("ColorRGB", "D3E16E81-7835-11cf-8F52-0040333594A3",
         "FLOAT red;\n FLOAT green;\n FLOAT blue;"),
        ("Material", "3D82AB4D-62DA-11cf-AB39-0020AF71E433",
         "ColorRGBA faceColor;\n FLOAT power;\n ColorRGB specularColor;\n ColorRGB emissiveColor;"),
        ("TextureFilename", "A42790E1-7810-11cf-8F52-0040333594A3",
         "STRING filename;"),
        ("MeshFace", "3D82AB5F-62DA-11cf-AB39-0020AF71E433",
         "DWORD nFaceVertexIndices;\n array DWORD faceVertexIndices[nFaceVertexIndices];"),
        ("MeshTextureCoords", "F6F23F40-7686-11cf-8F52-0040333594A3",
         "DWORD nTextureCoords;\n array Coords2d textureCoords[nTextureCoords];"),
        ("MeshMaterialList", "F6F23F42-7686-11cf-8F52-0040333594A3",
         "DWORD nMaterials;\n DWORD nFaceIndexes;\n array DWORD faceIndexes[nFaceIndexes];\n [Material]"),
        ("MeshNormals", "F6F23F43-7686-11cf-8F52-0040333594A3",
         "DWORD nNormals;\n array Vector normals[nNormals];\n DWORD nFaceNormals;\n array MeshFace faceNormals[nFaceNormals];"),
        ("MeshVertexColors", "1630B821-7842-11cf-8F52-0040333594A3",
         "DWORD nVertexColors;\n array IndexedColor vertexColors[nVertexColors];"),
        ("IndexedColor", "1630B820-7842-11cf-8F52-0040333594A3",
         "DWORD index;\n ColorRGBA indexColor;"),
        ("Mesh", "3D82AB44-62DA-11cf-AB39-0020AF71E433",
         "DWORD nVertices;\n array Vector vertices[nVertices];\n DWORD nFaces;\n array MeshFace faces[nFaces];"),
        ("FrameTransformMatrix", "F6F23F41-7686-11cf-8F52-0040333594A3",
         "Matrix4x4 frameMatrix;"),
        ("Frame", "3D82AB46-62DA-11cf-AB39-0020AF71E433", "[...]"),
        ("XSkinMeshHeader", "3CF169CE-FF7C-44ab-93C0-F78F62D172E2",
         "WORD nMaxSkinWeightsPerVertex;\n WORD nMaxSkinWeightsPerFace;\n WORD nBones;"),
        ("SkinWeights", "6F0D123B-BAD2-4167-A0D0-80224F25FABB",
         "STRING transformNodeName;\n DWORD nWeights;\n array DWORD vertexIndices[nWeights];\n array FLOAT weights[nWeights];\n Matrix4x4 matrixOffset;"),
        ("AnimTicksPerSecond", "9E415A43-7BA6-4a73-8743-B73D47E88476",
         "DWORD AnimTicksPerSecond;"),
    ]
    for name, guid, body in templates:
        f.write(f"template {name} {{\n <{guid}>\n {body}\n}}\n\n")
    f.write("AnimTicksPerSecond {\n 4800;\n}\n\n")


def write_bone_hierarchy(f, bone_list, indent=6):
    children = {}
    for name, parent, _ in bone_list:
        children.setdefault(parent, []).append(name)
    rest = {name: mat for name, _, mat in bone_list}

    def write_frame(name, level):
        pad = " " * level
        f.write(f"{pad}Frame {name} {{\n")
        f.write(f"{pad}   FrameTransformMatrix {{\n")
        f.write(mat4_to_x(rest[name], level + 6))
        f.write(f"\n{pad}   }}\n")
        for child in children.get(name, []):
            write_frame(child, level + 3)
        f.write(f"{pad}}}\n")

    for name, parent, _ in bone_list:
        if parent is None:
            write_frame(name, indent)


def generate_backfaces_data(verts, faces, normals, uvs, weights_by_bone, face_mat_indices=None, offset=0.0005):
    """
    Duplicate every triangle with reversed winding and flipped normals.
    Vertices are nudged slightly along -normal so coplanar front/back
    faces do not z-fight (the usual cause of flickering shadows on skirts).
    Skin weights are copied to the new vertices.
    """
    from mathutils import Vector
    new_verts = list(verts)
    new_normals = list(normals)
    new_uvs = list(uvs) if uvs else None
    new_faces = list(faces)
    new_face_mats = list(face_mat_indices) if face_mat_indices is not None else [0] * len(faces)

    back_of = {}
    for i, (v, n) in enumerate(zip(verts, normals)):
        nn = (-n).normalized() if n.length > 1e-8 else Vector((0, 0, -1))
        bv = v + nn * offset
        back_of[i] = len(new_verts)
        new_verts.append(bv)
        new_normals.append(nn)
        if new_uvs is not None:
            new_uvs.append(uvs[i])

    for fi, face in enumerate(faces):
        new_faces.append([back_of[i] for i in reversed(face)])
        new_face_mats.append(new_face_mats[fi] if fi < len(new_face_mats) else 0)

    new_weights = {bone: list(wlist) for bone, wlist in weights_by_bone.items()}
    for bone, wlist in weights_by_bone.items():
        for vi, w in wlist:
            if vi in back_of:
                new_weights[bone].append((back_of[vi], w))

    return new_verts, new_faces, new_normals, new_uvs, new_weights, new_face_mats



def write_mesh(f, mesh_name, verts, faces, normals, uvs, weights_by_bone,
               matrix_offsets, materials=None, face_mat_indices=None,
               export_normals=True, export_uvs=True,
               ambient=0.8, diffuse=0.35, specular=0.5, opacity=1.0,
               specular_power=128.0, export_vertex_colors=True):
    f.write(f"   Mesh {mesh_name} {{\n")

    f.write(f"    {len(verts)};\n")
    for i, v in enumerate(verts):
        comma = "," if i < len(verts) - 1 else ";"
        f.write(f"    {v.x:.6f}; {v.y:.6f}; {v.z:.6f};{comma}\n")

    f.write(f"    {len(faces)};\n")
    for i, face in enumerate(faces):
        comma = "," if i < len(faces) - 1 else ";"
        idx = ",".join(str(x) for x in face)
        f.write(f"    {len(face)}; {idx};{comma}\n")

    if export_normals and normals:
        f.write("    MeshNormals {\n")
        f.write(f"     {len(normals)};\n")
        for i, n in enumerate(normals):
            comma = "," if i < len(normals) - 1 else ";"
            f.write(f"     {n.x:.6f}; {n.y:.6f}; {n.z:.6f};{comma}\n")
        f.write(f"     {len(faces)};\n")
        for i, face in enumerate(faces):
            comma = "," if i < len(faces) - 1 else ";"
            idx = ",".join(str(x) for x in face)
            f.write(f"     {len(face)}; {idx};{comma}\n")
        f.write("    }\n")

    if export_uvs and uvs:
        f.write("    MeshTextureCoords {\n")
        f.write(f"     {len(uvs)};\n")
        for i, uv in enumerate(uvs):
            comma = "," if i < len(uvs) - 1 else ";"
            f.write(f"     {uv[0]:.6f}; {uv[1]:.6f};{comma}\n")
        f.write("    }\n")

    # Vertex colors (UU always writes solid white — some renderers use them for lighting)
    if export_vertex_colors:
        f.write("    MeshVertexColors {\n")
        f.write(f"     {len(verts)};\n")
        for i in range(len(verts)):
            comma = "," if i < len(verts) - 1 else ";"
            f.write(f"     {i}; 1.000000; 1.000000; 1.000000; 1.000000;{comma}\n")
        f.write("    }\n")

    # materials: list of texture filename strings (or None)
    if not materials:
        materials = [None]
    if face_mat_indices is None:
        face_mat_indices = [0] * len(faces)
    # clamp indices
    nmat = len(materials)
    face_mat_indices = [min(max(0, int(i)), nmat - 1) for i in face_mat_indices]

    f.write("    MeshMaterialList {\n")
    f.write(f"     {nmat};\n")
    f.write(f"     {len(faces)};\n")
    for i in range(len(faces)):
        comma = "," if i < len(faces) - 1 else ";"
        f.write(f"     {face_mat_indices[i]}{comma}\n")
    for mi, texture_name in enumerate(materials):
        f.write(f"     Material Material_{mi + 1} {{\n")
        f.write(f"      {diffuse:.6f}; {diffuse:.6f}; {diffuse:.6f}; {opacity:.6f};;\n")
        f.write(f"      {specular_power:.6f};\n")
        f.write(f"      {specular:.6f}; {specular:.6f}; {specular:.6f};;\n")
        f.write(f"      {ambient:.6f}; {ambient:.6f}; {ambient:.6f};;\n")
        if texture_name:
            f.write("      TextureFilename {\n")
            f.write(f'       "{texture_name}";\n')
            f.write("      }\n")
        f.write("     }\n")
    f.write("    }\n")

    # Only export skin weights for aw_* bones (non-AW names break DeltaWorlds)
    aw_weights = {
        b: w for b, w in weights_by_bone.items()
        if w and str(b).lower().startswith("aw_")
    }
    n_bones = len(aw_weights)
    f.write("    XSkinMeshHeader {\n")
    f.write("     4;\n")
    f.write("     12;\n")
    f.write(f"     {n_bones};\n")
    f.write("    }\n")

    for bone_name, wlist in aw_weights.items():
        if not wlist:
            continue
        f.write("    SkinWeights {\n")
        f.write(f'     "{bone_name}";\n')
        f.write(f"     {len(wlist)};\n")
        for i, (vi, w) in enumerate(wlist):
            comma = "," if i < len(wlist) - 1 else ";"
            f.write(f"     {vi}{comma}\n")
        for i, (vi, w) in enumerate(wlist):
            comma = "," if i < len(wlist) - 1 else ";"
            f.write(f"     {w:.6f}{comma}\n")
        offset = matrix_offsets.get(bone_name, Matrix.Identity(4))
        f.write(mat4_to_x(offset, 5))
        f.write("\n    }\n")

    f.write("   }\n")


def copy_textures_next_to_x(filepath, mesh_payloads):
    """Copy texture files referenced by materials into the .x output folder."""
    import shutil
    out_dir = Path(filepath).parent
    copied = []
    seen = set()
    for payload in mesh_payloads:
        for tex in payload.get("materials") or []:
            if not tex or tex in seen:
                continue
            seen.add(tex)
            img = None
            for im in bpy.data.images:
                name = Path(im.name).name
                if name == tex or (im.filepath and Path(bpy.path.abspath(im.filepath)).name == tex):
                    img = im
                    break
            if img is None:
                continue
            src = bpy.path.abspath(img.filepath) if img.filepath else ""
            if not src or not Path(src).is_file():
                continue
            dst = out_dir / Path(src).name
            try:
                if Path(src).resolve() == dst.resolve():
                    copied.append(dst.name)
                    continue
            except Exception:
                pass
            try:
                shutil.copy2(src, dst)
                copied.append(dst.name)
            except Exception as e:
                print(f"  Texture copy failed {src} → {dst}: {e}")
    return copied


def save(context, filepath, global_scale=1.0, axis_conversion="YUP",
         export_normals=True, export_uvs=True, export_materials=True,
         flip_uv_v=True, flip_faces=False,
         only_selected=False,
         mat_ambient=0.8, mat_diffuse=0.35, mat_specular=0.5, mat_opacity=1.0,
         mat_specular_power=128.0, export_vertex_colors=False,
         generate_backfaces=False, backface_offset=0.0005,
         export_as_zip=False,
         **kwargs):

    arm_obj = None
    if context.object and context.object.type == "ARMATURE":
        arm_obj = context.object
    else:
        for obj in context.selected_objects:
            if obj.type == "ARMATURE":
                arm_obj = obj
                break
    if arm_obj is None:
        for obj in context.scene.objects:
            if obj.type == "ARMATURE":
                arm_obj = obj
                break
    if arm_obj is None:
        print("ERROR: No armature found")
        return {"CANCELLED"}

    meshes = find_skinned_meshes(arm_obj, only_selected)
    if not meshes:
        print("ERROR: No skinned meshes found")
        return {"CANCELLED"}

    mesh_xform = make_axis_matrix(axis_conversion, global_scale)
    armature_matrix = mesh_xform

    bone_list = collect_bones(arm_obj)
    matrix_offsets = compute_matrix_offsets(arm_obj, bone_list, mesh_xform)

    # Prepare each skinned mesh (multi-material + multi-mesh support)
    mesh_payloads = []
    for mesh_obj in meshes:
        materials = collect_mesh_materials(mesh_obj)
        verts, faces, normals, uvs, weights_by_bone, face_mat_indices = extract_mesh_data(
            mesh_obj, arm_obj, mesh_xform,
            flip_v=flip_uv_v, flip_faces=flip_faces,
        )
        if generate_backfaces:
            verts, faces, normals, uvs, weights_by_bone, face_mat_indices = generate_backfaces_data(
                verts, faces, normals, uvs, weights_by_bone,
                face_mat_indices=face_mat_indices, offset=backface_offset,
            )
            print(f"  Backfaces on {mesh_obj.name}: verts now {len(verts)}")
        mesh_payloads.append({
            "name": mesh_obj.name,
            "verts": verts,
            "faces": faces,
            "normals": normals,
            "uvs": uvs,
            "weights": weights_by_bone,
            "materials": materials,
            "face_mats": face_mat_indices,
        })
        print(f"  Mesh {mesh_obj.name}: {len(verts)} verts, {len(faces)} faces, "
              f"{len(materials)} material(s): {[m or '(none)' for m in materials]}")

    filepath = Path(filepath)
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        write_templates(f)

        f.write("   Frame Armature {\n")
        f.write("      FrameTransformMatrix {\n")
        f.write(mat4_to_x(armature_matrix, 7))
        f.write("\n      }\n\n")
        write_bone_hierarchy(f, bone_list, indent=6)
        f.write("   }\n\n")

        for mi, payload in enumerate(mesh_payloads):
            frame_name = "char1" if mi == 0 else f"char{mi + 1}"
            f.write(f"   Frame {frame_name} {{\n")
            f.write("      FrameTransformMatrix {\n")
            f.write("       1.000000, 0.000000, 0.000000, 0.000000,\n")
            f.write("       0.000000, 1.000000, 0.000000, 0.000000,\n")
            f.write("       0.000000, 0.000000, 1.000000, 0.000000,\n")
            f.write("       0.000000, 0.000000, 0.000000, 1.000000;;\n")
            f.write("      }\n\n")

            write_mesh(
                f, frame_name,
                payload["verts"], payload["faces"], payload["normals"], payload["uvs"],
                payload["weights"], matrix_offsets,
                materials=payload["materials"],
                face_mat_indices=payload["face_mats"],
                export_normals=export_normals, export_uvs=export_uvs,
                ambient=mat_ambient, diffuse=mat_diffuse,
                specular=mat_specular, opacity=mat_opacity,
                specular_power=mat_specular_power,
                export_vertex_colors=export_vertex_colors,
            )
            f.write("   }\n")

    total_verts = sum(len(p["verts"]) for p in mesh_payloads)
    print(f"[DeltaWorlds X v{EXPORTER_VERSION}] → {filepath}")
    print(f"  Axis: {axis_conversion}, Bones: {len(bone_list)}, Verts: {total_verts}")
    print(f"  Meshes exported: {len(mesh_payloads)}")

    # Copy textures next to the .x (not into the zip)
    copy_with_x = True
    try:
        copy_with_x = bool(context.scene.dw_tex_copy_with_x)
    except Exception:
        copy_with_x = True
    if copy_with_x:
        copied = copy_textures_next_to_x(filepath, mesh_payloads)
        if copied:
            print(f"  Textures copied: {', '.join(copied)}")
        else:
            print("  Textures: none copied (already in place or not found on disk)")

    if export_as_zip:
        import zipfile
        zip_path = filepath.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(filepath, arcname=filepath.name)
        # remove the loose .x so only the zip remains (textures stay beside it)
        try:
            filepath.unlink()
        except Exception:
            pass
        print(f"  Packaged → {zip_path}")

    return {"FINISHED"}
