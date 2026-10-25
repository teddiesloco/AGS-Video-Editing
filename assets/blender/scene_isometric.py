"""AGS Blender 3D — sơ đồ 3 khối isometric 01 INTAKE -> 02 AI CORE -> 03 OUTCOME, đèn studio 3 điểm, camera trượt.
Chạy trong `blender --background --python scene_isometric.py -- <json>`; ghi khung PNG f_####.png vào frames_dir."""
import json
import math
import sys

import bpy

A = json.loads(sys.argv[sys.argv.index("--") + 1])
W, H, N = A["width"], A["height"], A["frames"]


def lin(hexs):
    c = [int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


NEON, SIGNAL, PAPER, INK = (lin(h) for h in ("#A8FF3E", "#1F6F3D", "#F4F4EF", "#0E1116"))
sc = bpy.context.scene


def setup(bg):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for eng in A["engines"]:
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps, r.fps_base = W, H, 100, A["fps"], 1.0
    sc.frame_start, sc.frame_end = 1, N
    r.image_settings.file_format, r.image_settings.color_mode = "PNG", "RGB"
    r.filepath = A["frames_dir"] + "/f_"
    sc.view_settings.view_transform = "Standard"
    if r.engine == "BLENDER_WORKBENCH":
        sc.display.shading.light, sc.display.shading.color_type = "STUDIO", "MATERIAL"
    else:
        sc.eevee.taa_render_samples = A["samples"]
    world = bpy.data.worlds.new("ags")
    sc.world = world
    world.color = bg[:3]
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = bg
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"


def mat(rgba, rough=0.45, flat=False):
    m = bpy.data.materials.new("ags")
    m.diffuse_color = rgba
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1) if flat else rgba
    b.inputs["Roughness"].default_value = rough
    if flat:  # tự phát sáng đúng mã màu token, không bị đèn làm lệch
        b.inputs["Specular IOR Level"].default_value = 0.0
        b.inputs["Emission Color"].default_value = rgba
        b.inputs["Emission Strength"].default_value = 1.0
    return m


def prim(op, m, **kw):
    op(**kw)
    ob = bpy.context.active_object
    ob.data.materials.append(m)
    return ob


def light(kind, loc, energy, rgba=(1, 1, 1, 1), size=2.0):
    data = bpy.data.lights.new("l", kind)
    data.energy, data.color = energy, rgba[:3]
    if kind == "AREA":
        data.size = size
    ob = bpy.data.objects.new("l", data)
    sc.collection.objects.link(ob)
    ob.location = loc
    return ob


def camera(loc, lens=50.0, target=None):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    cam.location, cam.data.lens = loc, lens
    x0, y0, x1, y1 = A["safe_box"]
    # Trục camera rơi vào tâm vùng an toàn 9:16 (shift tính theo cạnh dài = chiều cao).
    cam.data.shift_x = (W / 2 - (x0 + x1) / 2) / H
    cam.data.shift_y = ((y0 + y1) / 2 - H / 2) / H
    if target:
        con = cam.constraints.new("TRACK_TO")
        con.target, con.track_axis, con.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
    sc.camera = cam
    return cam


def title(cam, y_px, h_px, rgba):
    if not A["title"]:
        return
    cu = bpy.data.curves.new("title", "FONT")
    cu.body, cu.align_x, cu.align_y = A["title"], "CENTER", "CENTER"
    if A["font"]:
        cu.font = bpy.data.fonts.load(A["font"], check_existing=True)
    d = 3.0
    k = cam.data.ortho_scale / H if cam.data.type == "ORTHO" else d * cam.data.sensor_width / cam.data.lens / H
    x0, _, x1, _ = A["safe_box"]
    ob = bpy.data.objects.new("title", cu)
    sc.collection.objects.link(ob)
    ob.data.materials.append(mat(rgba, flat=True))
    ob.parent = cam
    ob.location = (((x0 + x1) / 2 - (W / 2 - cam.data.shift_x * H)) * k, -(y_px - (H / 2 + cam.data.shift_y * H)) * k, -d)
    cu.size = h_px * k
    bpy.context.view_layer.update()
    max_w = (x1 - x0) * 0.86 * k
    if ob.dimensions.x > max_w:
        ob.scale = (max_w / ob.dimensions.x,) * 3



setup(PAPER)
WHITE = lin("#FFFFFF")
step, size = 4.2, 1.8
down, right = (0.7071, -0.7071), (0.7071, 0.7071)  # hướng xuống / sang phải trên màn hình (camera xoay 45°)
glow = mat(NEON, flat=True)
iso_rot = (math.radians(54.736), 0, math.radians(45))
for i, (label, rgba) in enumerate((("01 INTAKE", INK), ("02 AI CORE", SIGNAL), ("03 OUTCOME", NEON))):
    t = i - 1
    x, y = down[0] * step * t, down[1] * step * t
    blk = prim(bpy.ops.mesh.primitive_cube_add, mat(rgba, rough=0.5), size=1, location=(x, y, 0))
    blk.scale = (size, size, 1.0)
    bevel = blk.modifiers.new("bevel", "BEVEL")
    bevel.width, bevel.segments = 0.05, 3
    if i == 1:
        top = prim(bpy.ops.mesh.primitive_cube_add, glow, size=1, location=(0, 0, 0.5))
        top.scale = (0.55, 0.55, 0.12)
        top.parent = blk
    a, b = max(2, int(N * (0.05 + 0.3 * i))), max(3, int(N * (0.3 + 0.3 * i)))
    for f, s in ((1, 0.02), (a, 0.02), (b, 1.0)):
        blk.scale = (size, size, s)
        blk.location = (x, y, s / 2)
        blk.keyframe_insert("scale", frame=f)
        blk.keyframe_insert("location", frame=f)
    cu = bpy.data.curves.new("label", "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = label, 0.5, "LEFT", "CENTER"
    if A["font"]:
        cu.font = bpy.data.fonts.load(A["font"], check_existing=True)
    lab = bpy.data.objects.new("label", cu)
    sc.collection.objects.link(lab)
    lab.data.materials.append(mat(INK, flat=True))
    lab.location = (x + right[0] * 1.55, y + right[1] * 1.55, 0.6)
    lab.rotation_euler = iso_rot
    if i < 2:
        ln = prim(bpy.ops.mesh.primitive_cube_add, glow, size=1, location=(x, y, 0.15))
        ln.rotation_euler = (0, 0, math.radians(-45))
        for f, s in ((1, 0.001), (b, 0.001), (max(b + 1, int(N * (0.45 + 0.3 * i))), 1.0)):
            ln.scale = (step * s, 0.14, 0.14)
            ln.location = (x + down[0] * step * s / 2, y + down[1] * step * s / 2, 0.15)
            ln.keyframe_insert("scale", frame=f)
            ln.keyframe_insert("location", frame=f)
light("AREA", (4, -6, 8), 900, WHITE, size=5)
light("AREA", (-7, -2, 4), 250, WHITE, size=5)
light("AREA", (-2, 7, 6), 500, NEON, size=3)
# Camera isometric (orthographic) trượt dọc chuỗi khối từ 01 xuống 03.
cam = camera((0, 0, 0))
cam.data.type, cam.data.ortho_scale, cam.data.clip_end = "ORTHO", 19.0, 200.0
cam.rotation_euler = iso_rot
back = (0.7071 * 0.8165, -0.7071 * 0.8165, 0.5774)
for f, t, zoom in ((1, -1.1, 19.0), (N, 0.1, 18.2)):
    cam.location = tuple(30 * back[k] + (down[k] * t + right[k] * 1.0 if k < 2 else 0.6) for k in range(3))
    cam.data.ortho_scale = zoom
    cam.keyframe_insert("location", frame=f)
    cam.data.keyframe_insert("ortho_scale", frame=f)
title(cam, 330, 56, SIGNAL)
bpy.ops.render.render(animation=True)
