"""AGS Blender 3D — lô đất BĐS nhô cao + cột mốc ranh giới phát sáng #A8FF3E + camera bay quỹ đạo.
Chạy trong `blender --background --python scene_bds.py -- <json>`; ghi khung PNG f_####.png vào frames_dir."""
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


setup(INK)
# Bệ khu đất + các lô lân cận thấp, lô chính nhô cao dần trong 35% đầu clip.
prim(bpy.ops.mesh.primitive_cube_add, mat(SIGNAL, rough=0.8), size=1, location=(0, 0, -0.1)).scale = (5.6, 4.6, 0.2)
for x, y, sx, sy in ((-1.9, 1.4, 1.4, 1.2), (1.9, -1.5, 1.4, 1.0), (1.9, 1.3, 1.3, 1.4), (-1.9, -1.3, 1.3, 1.3)):
    prim(bpy.ops.mesh.primitive_cube_add, mat(INK, rough=0.7), size=1, location=(x, y, 0.08)).scale = (sx, sy, 0.16)
corners = [(-1.0, -0.8), (1.1, -0.7), (0.9, 0.9), (-0.9, 0.8)]
mesh = bpy.data.meshes.new("lot")
top, base = [(x, y, 1.0) for x, y in corners], [(x, y, 0.0) for x, y in corners]
mesh.from_pydata(base + top, [], [(3, 2, 1, 0), (4, 5, 6, 7)] + [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)])
lot = bpy.data.objects.new("lot", mesh)
sc.collection.objects.link(lot)
lot.data.materials.append(mat(PAPER, rough=0.55))
height = 0.9
for f, s in ((1, 0.02), (max(2, int(N * 0.35)), height)):
    lot.scale = (1, 1, s)
    lot.keyframe_insert("scale", frame=f)
glow = mat(NEON, flat=True)
for i, (x, y) in enumerate(corners):
    prim(bpy.ops.mesh.primitive_cylinder_add, glow, radius=0.07, depth=1.5, location=(x, y, 0.75))
    light("POINT", (x, y, 1.2), 60, NEON)
    nx, ny = corners[(i + 1) % 4]
    edge = prim(bpy.ops.mesh.primitive_cube_add, glow, size=1, location=((x + nx) / 2, (y + ny) / 2, height + 0.02))
    edge.scale = (math.hypot(nx - x, ny - y), 0.04, 0.04)
    edge.rotation_euler = (0, 0, math.atan2(ny - y, nx - x))
light("AREA", (3, -3, 6), 600, PAPER, size=4)
light("AREA", (-4, 2, 4), 150, PAPER, size=4)
# Camera bay quỹ đạo quanh lô đất (36°/giây), hạ dần độ cao.
pivot = bpy.data.objects.new("orbit", None)
sc.collection.objects.link(pivot)
pivot.location = (0, 0, 0.35)
cam = camera((0, -26.0, 18.3), lens=50, target=pivot)
cam.parent = pivot
for f, ang, z in ((1, 0.0, 18.3), (N, math.radians(36 * N / A["fps"]), 15.5)):
    pivot.rotation_euler = (0, 0, ang)
    pivot.keyframe_insert("rotation_euler", frame=f)
    cam.location = (0, -26.0, z)
    cam.keyframe_insert("location", frame=f)
title(cam, 420, 64, NEON)
bpy.ops.render.render(animation=True)
