"""Shared Blender kit for the portfolio's island dioramas.

Every island script imports this module, builds geometry with the helpers below,
and calls `finish(slug)`. The kit owns the look: palette handling, matte "clay"
materials, soft bevels, one sun and sky shared by every island, the preview and
hero renders, the light bake, and the glTF export.

Run:  blender -b -P studio/run.py -- <slug> [preview|hero|bake|all]

Conventions
- Units: 1 unit is roughly 1 m of a toy world. Z is up. The island top is z = 0,
  the sea surface is z = WATER_Z. Keep everything inside a radius of about 6.
- The viewer usually looks from the front-left (negative Y, slightly negative X),
  so compose the "face" of the island toward -Y.
- Never rotate an island after baking: the sun direction is shared world-wide.
- Name objects meaningfully. Objects tagged with `animate()` stay separate nodes
  in the export so the website can move them; everything else is merged.
"""
import math
import os
import random
import sys
import time

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'out')            # previews, .blend files (not committed)
PUBLIC = os.path.join(os.path.dirname(ROOT), 'assets', 'world')  # shipped assets
WATER_Z = -1.0
SUN_DIR = Vector((0.64, -0.36, 0.68)).normalized()   # direction TOWARD the sun
TAU = math.tau

# Shared neutrals. Island-specific colours live in each island script.
INK = '#22302b'
PAPER = '#f6f1e4'
CREAM = '#efe6d2'
SAND = '#e9d3a7'
SOIL = '#c79a6b'
SOIL_DARK = '#a67a52'
ROCK = '#9aa0a3'
ROCK_DARK = '#7d8589'
GRASS = '#9ccf7f'
GRASS_DARK = '#6fb26a'
LEAF = '#58a66b'
LEAF_DARK = '#3d8a5c'
WOOD = '#c98f5a'
WOOD_DARK = '#9c6a42'
WHITE = '#fbf8f0'
STEEL = '#c9d2d6'
STEEL_DARK = '#8f9ba3'
CORAL = '#f0785a'
SUNSHINE = '#f7c65b'
SEA = '#6cc5bd'
SEA_DEEP = '#2f8f95'
BUOY = '#f26a3d'

_materials = {}


# ---------------------------------------------------------------- basics
def srgb(hex_color, alpha=1.0):
    """'#rrggbb' -> linear RGBA tuple for Blender."""
    h = hex_color.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, alpha)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _materials.clear()
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    return scene


def mat(hex_color, rough=0.72, emit=0.0, metallic=0.0, coat=0.0, name=None,
        emit_color=None, sheen=0.0, alpha=1.0):
    """Matte clay material, cached by its parameters."""
    key = name or f'{hex_color}_{rough}_{emit}_{metallic}_{coat}_{sheen}_{alpha}_{emit_color}'
    if key in _materials:
        return _materials[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = srgb(hex_color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Sheen Weight'].default_value = sheen
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    if emit:
        b.inputs['Emission Color'].default_value = srgb(emit_color or hex_color)
        b.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = srgb(hex_color)
    _materials[key] = m
    return m


def _as_mat(m):
    return m if isinstance(m, bpy.types.Material) else mat(m)


def _finish(ob, name, m, smooth=True, angle=40):
    ob.name = name
    ob.data.name = name
    if m is not None:
        ob.data.materials.clear()
        ob.data.materials.append(_as_mat(m))
    if smooth and ob.type == 'MESH':
        for p in ob.data.polygons:
            p.use_smooth = True
        try:
            ob.data.set_sharp_from_angle(angle=math.radians(angle))
        except Exception:
            pass
    return ob


def _bevel(ob, width, segments=3):
    if width and width > 0:
        mod = ob.modifiers.new('bevel', 'BEVEL')
        mod.width = width
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(35)
        mod.harden_normals = False
    return ob


def _obj_from_bmesh(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def place(ob, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    ob.location = loc
    ob.rotation_euler = Euler([math.radians(a) for a in rot])
    if scale is not None:
        ob.scale = scale if hasattr(scale, '__len__') else (scale,) * 3
    return ob


# ---------------------------------------------------------------- primitives
def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, bevel=0.06, seg=3):
    """Rounded box. `size` is full extents (x, y, z); `loc` is its centre."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    ob = _obj_from_bmesh(bm, name)
    _bevel(ob, min(bevel, min(size) * 0.45), seg)
    place(ob, loc, rot)
    return _finish(ob, name, m)


def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, r2=None, verts=32,
        bevel=0.04, seg=3):
    """Cylinder or cone frustum (r at the bottom, r2 at the top), centred on loc."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=r, radius2=r if r2 is None else r2, depth=h)
    ob = _obj_from_bmesh(bm, name)
    _bevel(ob, min(bevel, h * 0.45, max(r, 0.01) * 0.6), seg)
    place(ob, loc, rot)
    return _finish(ob, name, m)


def sphere(name, r, loc=(0, 0, 0), scale=(1, 1, 1), m=WHITE, seg=28, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=r)
    ob = _obj_from_bmesh(bm, name)
    place(ob, loc, rot, scale)
    return _finish(ob, name, m)


def torus(name, R, r, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, seg=40, ring=12):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg,
                                     minor_segments=ring)
    ob = bpy.context.object
    place(ob, loc, rot)
    return _finish(ob, name, m)


def lathe(name, profile, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, verts=40, bevel=0.0):
    """Revolve a profile [(radius, z), ...] around Z. Great for pots, flasks, buoys."""
    bm = bmesh.new()
    rings = []
    for radius, z in profile:
        if radius <= 1e-5:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((radius * math.cos(TAU * i / verts),
                                        radius * math.sin(TAU * i / verts), z))
                          for i in range(verts)])
    for a, b in zip(rings, rings[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = _obj_from_bmesh(bm, name)
    _bevel(ob, bevel)
    place(ob, loc, rot)
    return _finish(ob, name, m, angle=50)


def prism(name, outline, h, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, bevel=0.05, seg=3):
    """Extrude a 2D outline [(x, y), ...] (counter-clockwise) upward by h from z=0."""
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, 0)) for x, y in outline]
    top = [bm.verts.new((x, y, h)) for x, y in outline]
    n = len(outline)
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = _obj_from_bmesh(bm, name)
    _bevel(ob, bevel, seg)
    place(ob, loc, rot)
    return _finish(ob, name, m)


def tube(name, points, r=0.05, m=WHITE, closed=False, smooth_curve=True, res=10, cap=True):
    """Round tube through 3D points. Use for ropes, pipes, rails, curves and arcs."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 4
    cu.resolution_u = res
    cu.use_fill_caps = cap
    if smooth_curve:
        sp = cu.splines.new('NURBS')
        sp.points.add(len(points) - 1)
        for p, co in zip(sp.points, points):
            p.co = (*co, 1)
        sp.use_endpoint_u = not closed
        sp.use_cyclic_u = closed
        sp.order_u = min(4, len(points))
    else:
        sp = cu.splines.new('POLY')
        sp.points.add(len(points) - 1)
        for p, co in zip(sp.points, points):
            p.co = (*co, 1)
        sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(_as_mat(m))
    return ob


def ribbon(name, points, width=0.3, thickness=0.03, m=WHITE, twist=None):
    """Flat band following 3D points (a curve with a rectangular profile)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.extrude = width / 2
    cu.bevel_depth = thickness / 2
    cu.bevel_resolution = 1
    cu.resolution_u = 12
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS')
    sp.points.add(len(points) - 1)
    for i, (p, co) in enumerate(zip(sp.points, points)):
        p.co = (*co, 1)
        if twist:
            p.tilt = math.radians(twist[i] if hasattr(twist, '__len__') else twist)
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(points))
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(_as_mat(m))
    return ob


def text(name, body, size=0.5, depth=0.06, loc=(0, 0, 0), rot=(90, 0, 0), m=INK,
         align='CENTER', bevel=0.006):
    """Extruded lettering. Use for numerals and short identifiers only: the website
    is translated into ten languages, so avoid English words inside the 3D world."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = depth / 2
    cu.bevel_depth = bevel
    cu.bevel_resolution = 1
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.resolution_u = 4
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(_as_mat(m))
    place(ob, loc, rot)
    return ob


def blob(name, r, loc=(0, 0, 0), scale=(1, 1, 1), m=LEAF, seed=0, bumps=0.18, seg=3):
    """Soft lumpy ball: foliage, clouds, bushes, boulders (with low `seg`)."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=seg, radius=r)
    offs = [Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
            for _ in range(7)]
    amps = [rng.uniform(0.4, 1.0) for _ in offs]
    for v in bm.verts:
        d = v.co.normalized()
        k = sum(a * max(0.0, d.dot(o)) ** 3 for a, o in zip(amps, offs))
        v.co = d * r * (1 + bumps * (k - 0.6))
    ob = _obj_from_bmesh(bm, name)
    place(ob, loc, (0, 0, rng.uniform(0, 360)), scale)
    return _finish(ob, name, m, angle=70)


def rock(name, r, loc=(0, 0, 0), m=ROCK, seed=0, squash=0.7):
    """Faceted boulder."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    for v in bm.verts:
        v.co *= 1 + rng.uniform(-0.2, 0.2)
        v.co.z *= squash
    ob = _obj_from_bmesh(bm, name)
    _bevel(ob, r * 0.12, 2)
    place(ob, loc, (rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(0, 360)))
    return _finish(ob, name, m, angle=25)


# ---------------------------------------------------------------- scenery
def island_base(R=5.0, seed=1, top=GRASS, lip=None, soil=SOIL, soil2=SOIL_DARK,
                rock_c=ROCK, lobes=((2, 0.05), (3, 0.06), (5, 0.03)), squash=(1.0, 1.0),
                segments=96, name='base'):
    """Layered island: a soft top, an overhanging lip, soil strata and a rock foot.
    Returns (object, radius_at(angle_radians)) so props can be placed near the edge."""
    rng = random.Random(seed)
    phases = [rng.uniform(0, TAU) for _ in lobes]

    def radius_at(a):
        return R * (1 + sum(amp * math.sin(k * a + ph) for (k, amp), ph in zip(lobes, phases)))

    # (scale, z, material slot)
    rings = [(0.55, 0.0, 0), (0.90, 0.0, 0), (0.972, -0.025, 0), (1.0, -0.10, 0),
             (1.005, -0.20, 1), (0.99, -0.27, 1), (0.955, -0.31, 2), (0.945, -0.52, 2),
             (0.94, -0.80, 2), (0.925, -0.84, 3), (0.90, -1.05, 3), (0.80, -1.6, 3),
             (0.55, -2.0, 3)]
    bm = bmesh.new()
    loops = []
    for s, z, _ in rings:
        loops.append([bm.verts.new((radius_at(TAU * i / segments) * s * squash[0] * math.cos(TAU * i / segments),
                                    radius_at(TAU * i / segments) * s * squash[1] * math.sin(TAU * i / segments), z))
                      for i in range(segments)])
    top_face = bm.faces.new(loops[0])
    top_face.material_index = 0
    for idx, (a, b) in enumerate(zip(loops, loops[1:])):
        slot = rings[idx + 1][2]
        for i in range(segments):
            j = (i + 1) % segments
            f = bm.faces.new((a[i], b[i], b[j], a[j]))
            f.material_index = slot
    bm.faces.new(list(reversed(loops[-1]))).material_index = 3
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = _obj_from_bmesh(bm, name)
    for c in (top, lip or top, soil, rock_c):
        ob.data.materials.append(_as_mat(c))
    # a second, darker soil stripe is added as a thin band object for strata
    band = lathe(name + '_stratum', [(0.0, -0.53), (R * 0.9, -0.53), (R * 0.9, -0.62), (0.0, -0.62)],
                 m=soil2, verts=segments)
    for v in band.data.vertices:
        a = math.atan2(v.co.y, v.co.x)
        d = math.hypot(v.co.x, v.co.y)
        if d > 0.01:
            k = radius_at(a) * 0.952 / (R * 0.9)
            v.co.x *= k * squash[0]; v.co.y *= k * squash[1]
    _finish(ob, name, None, angle=30)
    return ob, radius_at


def tree(name, loc, h=1.6, crown=0.7, trunk=WOOD_DARK, leaf=LEAF, leaf2=LEAF_DARK, seed=0, lean=0):
    """Round-crowned toy tree made of three foliage blobs."""
    rng = random.Random(seed)
    x, y, z = loc
    parts = [cyl(name + '_trunk', 0.09 * h, h * 0.62, (x, y, z + h * 0.31), (lean, 0, 0), trunk,
                 r2=0.06 * h, verts=14, bevel=0.01)]
    parts.append(blob(name + '_c0', crown, (x, y, z + h * 0.78), (1, 1, 0.92), leaf, seed))
    parts.append(blob(name + '_c1', crown * 0.66, (x + crown * 0.55, y - crown * 0.2, z + h * 0.62),
                      (1, 1, 0.9), leaf2, seed + 1))
    parts.append(blob(name + '_c2', crown * 0.58, (x - crown * 0.5, y + crown * 0.25, z + h * 0.92),
                      (1, 1, 0.9), leaf, seed + 2))
    return parts


def pine(name, loc, h=1.8, r=0.55, trunk=WOOD_DARK, leaf=LEAF_DARK, tiers=3):
    x, y, z = loc
    parts = [cyl(name + '_trunk', 0.07 * h, h * 0.3, (x, y, z + h * 0.15), m=trunk, verts=12, bevel=0.01)]
    for i in range(tiers):
        k = 1 - i * 0.24
        parts.append(cyl(f'{name}_t{i}', r * k, h * 0.42, (x, y, z + h * (0.42 + i * 0.22)), m=leaf,
                         r2=0.02, verts=20, bevel=0.03))
    return parts


def bush(name, loc, r=0.35, leaf=LEAF, seed=0):
    return blob(name, r, (loc[0], loc[1], loc[2] + r * 0.55), (1.2, 1.1, 0.75), leaf, seed)


def grass_tuft(name, loc, h=0.28, n=5, m=GRASS_DARK, seed=0):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        a = rng.uniform(0, TAU)
        d = rng.uniform(0.0, 0.08)
        out.append(cyl(f'{name}_{i}', 0.035, h * rng.uniform(0.7, 1.15),
                       (loc[0] + d * math.cos(a), loc[1] + d * math.sin(a), loc[2] + h * 0.4),
                       (rng.uniform(-18, 18), rng.uniform(-18, 18), 0), m, r2=0.004, verts=6, bevel=0))
    return out


def flower(name, loc, h=0.3, petal=CORAL, heart=SUNSHINE, stem=LEAF_DARK):
    x, y, z = loc
    return [cyl(name + '_stem', 0.018, h, (x, y, z + h / 2), m=stem, verts=6, bevel=0),
            sphere(name + '_petal', 0.085, (x, y, z + h), (1, 1, 0.45), petal, 12),
            sphere(name + '_heart', 0.04, (x, y, z + h + 0.03), (1, 1, 0.7), heart, 10)]


def cloud(name, loc, s=1.0, seed=0, m=WHITE):
    rng = random.Random(seed)
    out = []
    for i, (dx, r) in enumerate([(-0.9, 0.55), (-0.3, 0.8), (0.45, 0.7), (1.05, 0.5)]):
        out.append(blob(f'{name}_{i}', r * s, (loc[0] + dx * s, loc[1] + rng.uniform(-0.15, 0.15) * s,
                                              loc[2] + rng.uniform(-0.05, 0.12) * s),
                        (1.1, 0.9, 0.72), m, seed + i, bumps=0.1))
    return out


def sign_post(name, loc, numeral, h=1.0, board=PAPER, post=WOOD_DARK, ink=INK, rot_z=0):
    """Small numbered marker; numerals only (the site is multilingual)."""
    x, y, z = loc
    p = cyl(name + '_post', 0.045, h, (x, y, z + h / 2), m=post, verts=10, bevel=0.01)
    b = box(name + '_board', (0.62, 0.07, 0.4), (x, y, z + h * 0.92), (0, 0, rot_z), board, bevel=0.03)
    t = text(name + '_num', numeral, 0.26, 0.03, (x, y, z + h * 0.92), (90, 0, rot_z), ink)
    t.location += Vector((math.sin(math.radians(rot_z)) * 0.045, -math.cos(math.radians(rot_z)) * 0.045, 0))
    return [p, b, t]


# ---------------------------------------------------------------- tags
def animate(ob, kind, **params):
    """Mark an object so it stays a separate node and the website animates it.
    kinds: 'spin' (axis='z', speed=rad/s), 'bob' (amp, speed), 'sway' (amp deg, speed),
           'pulse' (speed; brightness), 'orbit' (radius, speed, around object origin).
    Give the object an origin that makes sense as a pivot (use set_origin)."""
    ob['anim'] = kind
    for k, v in params.items():
        ob['anim_' + k] = v
    return ob


def set_origin(ob, point):
    """Move the object's origin (pivot) to a world-space point without moving it."""
    p = Vector(point)
    bpy.context.view_layer.update()
    delta = ob.matrix_world.inverted() @ p
    if ob.type == 'MESH':
        ob.data.transform(Matrix.Translation(-delta))
    elif ob.type in ('CURVE', 'FONT'):
        ob.data.transform(Matrix.Translation(-delta))
    ob.matrix_world.translation = p
    bpy.context.view_layer.update()
    return ob


def join(objects, name):
    """Merge several mesh/curve/text objects into one mesh object (applies modifiers)."""
    flat = []
    for o in objects:
        flat.extend(o if isinstance(o, (list, tuple)) else [o])
    bpy.ops.object.select_all(action='DESELECT')
    for o in flat:
        o.select_set(True)
    bpy.context.view_layer.objects.active = flat[0]
    bpy.ops.object.convert(target='MESH')
    if len(flat) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob


def hotspot(n, loc):
    """Numbered point of interest; the website places a label here and can fly to it."""
    e = bpy.data.objects.new(f'hs_{n}', None)
    e.empty_display_size = 0.2
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def keep_material(ob):
    """Exclude from the light bake and export with its own (emissive/image) material.
    Use sparingly: screens showing a real image, or pure-emission glow shapes."""
    ob['keep_material'] = True
    return ob


def image_material(name, path, emit=1.0):
    """Unlit image material for screens; path is absolute."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path)
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(tex.outputs['Color'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = emit
    b.inputs['Roughness'].default_value = 0.4
    return m


def screen(name, size, loc, rot, image_path, emit=1.0):
    """Flat image plane (x = width, z = height before rotation), e.g. a phone screen."""
    bm = bmesh.new()
    w, h = size[0] / 2, size[1] / 2
    vs = [bm.verts.new(c) for c in ((-w, 0, -h), (w, 0, -h), (w, 0, h), (-w, 0, h))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new('UVMap')
    for loop, co in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = co
    ob = _obj_from_bmesh(bm, name)
    ob.data.materials.append(image_material(name + '_mat', image_path, emit))
    place(ob, loc, rot)
    return keep_material(ob)


# ---------------------------------------------------------------- light, camera, render
def setup_world(scene=None, sea=True, sea_color=SEA, exposure=-0.22):
    scene = scene or bpy.context.scene
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = 'GPU'
    except Exception:
        scene.cycles.device = 'CPU'
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 4
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.view_settings.view_transform = os.environ.get('KIT_VIEW', 'Standard')
    try:
        scene.view_settings.look = os.environ.get('KIT_LOOK', 'None')
    except Exception as exc:
        print('[kit] look not set:', exc)
    scene.view_settings.exposure = exposure
    scene.render.film_transparent = False

    world = bpy.data.worlds.new('sky')
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes['Background']
    coord = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    mapr = nt.nodes.new('ShaderNodeMapRange')
    nt.links.new(coord.outputs['Generated'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], mapr.inputs['Value'])
    mapr.inputs['From Min'].default_value = -0.15
    mapr.inputs['From Max'].default_value = 0.9
    nt.links.new(mapr.outputs['Result'], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = srgb('#fbe9cf')
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = srgb('#a9d6ee')
    mid = ramp.color_ramp.elements.new(0.35)
    mid.color = srgb('#dcecea')
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0

    sun_data = bpy.data.lights.new('sun', 'SUN')
    sun_data.energy = 4.6
    sun_data.angle = math.radians(9)
    sun_data.color = srgb('#fff1dc')[:3]
    sun = bpy.data.objects.new('sun', sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (-SUN_DIR).to_track_quat('-Z', 'Y').to_euler()
    sun['helper'] = True

    if sea:
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=96, radius=90)
        plane = _obj_from_bmesh(bm, 'sea_helper')
        plane.location.z = WATER_Z
        m = bpy.data.materials.new('sea_helper')
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes['Principled BSDF']
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        length = nt.nodes.new('ShaderNodeVectorMath')
        length.operation = 'LENGTH'
        nt.links.new(geo.outputs['Position'], length.inputs[0])
        scale = nt.nodes.new('ShaderNodeMapRange')
        scale.inputs['From Min'].default_value = 3.5
        scale.inputs['From Max'].default_value = 34.0
        nt.links.new(length.outputs['Value'], scale.inputs['Value'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = srgb('#aeeedb')
        ramp.color_ramp.elements[1].color = srgb('#4fb4b8')
        mid = ramp.color_ramp.elements.new(0.16)
        mid.color = srgb(sea_color)
        nt.links.new(scale.outputs['Result'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.22
        noise = nt.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 1.6
        noise.inputs['Detail'].default_value = 3.0
        bump = nt.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.12
        bump.inputs['Distance'].default_value = 0.2
        nt.links.new(geo.outputs['Position'], noise.inputs['Vector'])
        nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
        plane.data.materials.append(m)
        plane['helper'] = True
    return scene


def camera(loc=(-9.5, -13.5, 8.2), target=(0, 0, 0.6), lens=50, name='cam', fstop=None):
    scene = bpy.context.scene
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_data.clip_end = 400
    cam = bpy.data.objects.new(name, cam_data)
    scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if fstop:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = (Vector(target) - Vector(loc)).length
        cam_data.dof.aperture_fstop = fstop
    cam['helper'] = True
    scene.camera = cam
    return cam


def render(path, res=(1100, 825), samples=96, cam=None):
    scene = bpy.context.scene
    if cam:
        scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.cycles.samples = samples
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f'[kit] rendered {path} in {time.time() - t:.1f}s')


def stats():
    deps = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for ob in bpy.context.scene.objects:
        if ob.get('helper') or ob.type not in ('MESH', 'CURVE', 'FONT'):
            continue
        me = ob.evaluated_get(deps).to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        ob.evaluated_get(deps).to_mesh_clear()
    print(f'[kit] triangles: {tris:,}')
    return tris


# ---------------------------------------------------------------- bake and export
def _exportables():
    return [o for o in bpy.context.scene.objects
            if not o.get('helper') and o.type in ('MESH', 'CURVE', 'FONT')]


def bake_and_export(slug, atlas=4096, samples=192, final=2048):
    """Merge static geometry, unwrap everything into one atlas, bake full lighting
    with Cycles, and export `<slug>.glb` plus `<slug>.webp` into assets/world/."""
    scene = bpy.context.scene
    os.makedirs(PUBLIC, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    obs = _exportables()
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.convert(target='MESH')
    obs = _exportables()

    # Glass and beams (alpha below 1) cannot live in an opaque light atlas: split them out.
    def see_through(material):
        if material is None or not material.use_nodes:
            return False
        node = material.node_tree.nodes.get('Principled BSDF')
        return bool(node) and node.inputs['Alpha'].default_value < 0.999
    for o in list(obs):
        if o.get('keep_material'):
            continue
        flags = [see_through(slot.material) for slot in o.material_slots]
        if any(flags) and not all(flags):
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.mesh.separate(type='MATERIAL')
    obs = _exportables()
    for o in obs:
        if not o.get('keep_material') and o.material_slots and all(see_through(slot.material) for slot in o.material_slots):
            o['keep_material'] = True
            o['glass'] = True
            for slot in o.material_slots:
                slot.material.surface_render_method = 'BLENDED'
    kept = [o for o in obs if o.get('keep_material')]
    moving = [o for o in obs if o.get('anim') and not o.get('keep_material')]
    static = [o for o in obs if not o.get('anim') and not o.get('keep_material')]
    bpy.ops.object.select_all(action='DESELECT')
    for o in static:
        o.select_set(True)
    bpy.context.view_layer.objects.active = static[0]
    if len(static) > 1:
        bpy.ops.object.join()
    merged = bpy.context.view_layer.objects.active
    merged.name = 'static'
    targets = [merged] + moving

    # one shared UV atlas
    bpy.ops.object.select_all(action='DESELECT')
    for o in targets:
        o.select_set(True)
        while o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers[0])
        o.data.uv_layers.new(name='UVMap')
    bpy.context.view_layer.objects.active = merged
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0,
                             scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT')
    try:
        bpy.ops.uv.pack_islands(margin=0.0022, rotate=True, margin_method='FRACTION')
    except TypeError:
        bpy.ops.uv.pack_islands(margin=0.0022)
    bpy.ops.object.mode_set(mode='OBJECT')

    image = bpy.data.images.new(f'{slug}_bake', atlas, atlas, float_buffer=True, alpha=False)
    seen = set()
    for o in targets:
        for slot in o.material_slots:
            m = slot.material
            if m is None or m.name in seen:
                continue
            seen.add(m.name)
            node = m.node_tree.nodes.new('ShaderNodeTexImage')
            node.image = image
            m.node_tree.nodes.active = node
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.bake.margin = 24
    scene.render.bake.use_clear = True
    t = time.time()
    bpy.ops.object.bake(type='COMBINED')
    print(f'[kit] baked {slug} in {time.time() - t:.1f}s')
    png = os.path.join(OUT, f'{slug}_bake.png')
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    image.save_render(png, scene=scene)

    # one neutral material for everything baked; the site swaps in the atlas
    baked = bpy.data.materials.new('BAKED')
    baked.use_nodes = True
    for o in targets:
        o.data.materials.clear()
        o.data.materials.append(baked)
    bpy.ops.object.select_all(action='DESELECT')
    for o in targets + kept:
        o.select_set(True)
    for o in scene.objects:
        if o.type == 'EMPTY' and o.name.startswith('hs_'):
            o.select_set(True)
    glb = os.path.join(PUBLIC, f'{slug}.glb')
    bpy.ops.export_scene.gltf(
        filepath=glb, export_format='GLB', use_selection=True, export_apply=True,
        export_normals=False, export_tangents=False, export_extras=True, export_yup=True,
        export_animations=False, export_cameras=False, export_lights=False,
        export_image_format='WEBP', export_image_quality=88,
        export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14, export_draco_texcoord_quantization=12)
    print(f'[kit] exported {glb} ({os.path.getsize(glb) / 1024:.0f} KB)')
    return png


def export_lit(slug):
    """Export with real materials and normals, for objects the site lights itself (the boat)."""
    os.makedirs(PUBLIC, exist_ok=True)
    obs = _exportables()
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.convert(target='MESH')
    obs = _exportables()
    moving = [o for o in obs if o.get('anim')]
    static = [o for o in obs if not o.get('anim')]
    bpy.ops.object.select_all(action='DESELECT')
    for o in static:
        o.select_set(True)
    bpy.context.view_layer.objects.active = static[0]
    if len(static) > 1:
        bpy.ops.object.join()
    bpy.context.view_layer.objects.active.name = 'hull'
    bpy.ops.object.select_all(action='DESELECT')
    for o in _exportables():
        o.select_set(True)
    glb = os.path.join(PUBLIC, f'{slug}.glb')
    bpy.ops.export_scene.gltf(
        filepath=glb, export_format='GLB', use_selection=True, export_apply=True,
        export_normals=True, export_tangents=False, export_extras=True, export_yup=True,
        export_animations=False, export_cameras=False, export_lights=False, export_texcoords=False,
        export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14, export_draco_normal_quantization=10)
    print(f'[kit] exported lit {glb} ({os.path.getsize(glb) / 1024:.0f} KB)')


def save_blend(slug):
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{slug}.blend'))


def finish(slug, mode='preview', cam_loc=(-9.5, -13.5, 8.2), cam_target=(0, 0, 0.6), lens=50,
           hero_loc=None, hero_target=None, hero_lens=None):
    """Call at the end of an island script. Modes: preview, views, hero, bake, all, lit."""
    os.makedirs(OUT, exist_ok=True)
    stats()
    cam = camera(cam_loc, cam_target, lens)
    if mode in ('preview', 'views'):
        render(os.path.join(OUT, f'{slug}_preview.png'), (1100, 825), 80, cam)
    if mode == 'views':
        for tag, loc in (('back', (9.5, 13.5, 8.2)), ('top', (0.01, -0.5, 21)),
                         ('low', (-6.5, -14.5, 2.4)), ('right', (13.5, -9.0, 7.0))):
            c = camera(loc, cam_target, lens, 'cam_' + tag)
            render(os.path.join(OUT, f'{slug}_{tag}.png'), (900, 675), 64, c)
    if mode in ('hero', 'all'):
        c = camera(hero_loc or cam_loc, hero_target or cam_target, hero_lens or lens, 'cam_hero', fstop=0.75)
        render(os.path.join(OUT, f'{slug}_hero.png'), (2000, 1500), 256, c)
    if mode == 'lit':
        export_lit(slug)
    if mode in ('bake', 'all'):
        save_blend(slug)
        bake_and_export(slug)
