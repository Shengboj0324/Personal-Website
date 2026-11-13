"""Phoenix: "Beyond the heat map" - urban heat vulnerability research.

A tilted tract-map table (369 relief tiles on the inferno ramp) is scanned by a
Landsat-style satellite. Cyan outlines mark the 37 hottest tracts, coral pins the 37
highest-priority tracts; only 17 tiles carry both. A cooling station, three profile
totems and a thermometer stand in a Sonoran-desert setting.
The heat field is illustrative (made up), not real data.
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

from kit import *

SAND_TOP = '#e9c5a7'
PALE = '#f1dcc2'
TERRA = '#c9744f'
RUST = '#793c27'
ADOBE = '#dd9d76'
CYAN = '#4fd0e0'
P_RED, P_GOLD, P_TEAL = '#d9503f', '#e8b33e', '#2f9c95'
CACTUS = '#6f9f6a'
CACTUS_D = '#5c8c5d'
PIN = '#ef5a48'
WATER = '#3f8fd6'
DRY = '#c4a96c'
SAGE = '#a9b08a'
INFERNO = ['#2a0f4a', '#8a2a6b', '#d94f3d', '#f79b2e', '#fbe36a']

N_TRACTS, N_TOP, N_BOTH = 369, 37, 17
S = 0.15                      # tile spacing (centre to centre)
APO = S * 0.45                # tile apothem
TILT, YAW = 12.0, -6.0        # table tilt toward the viewer, slight turn
SLAB_W, SLAB_L, SLAB_T = 3.7, 4.6, 0.16
C = Vector((-1.0, -0.15, 0.9))   # centre of the slab's top surface


# ---------------------------------------------------------------- small helpers
def _rgb(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a, b, t):
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b)))


def inferno(t):
    t = min(max(t, 0.0), 1.0) * 4
    i = min(int(t), 3)
    return mix(INFERNO[i], INFERNO[i + 1], t - i)


def mesh_obj(name, bm, mats, matrix=None, smooth=False):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for m in mats:
        me.materials.append(m if isinstance(m, bpy.types.Material) else mat(m))
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if matrix is not None:
        ob.matrix_world = matrix
    return ob


def hex_ring(bm, u, v, apothem, z):
    r = apothem / math.cos(math.pi / 6)
    return [bm.verts.new((u + r * math.cos(math.radians(30 + 60 * k)),
                          v + r * math.sin(math.radians(30 + 60 * k)), z)) for k in range(6)]


def bridge(bm, a, b, mi=0):
    n = len(a)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((a[k], a[j], b[j], b[k])).material_index = mi


def add_tile(bm, u, v, h, mi, chamfer=0.02):
    """Six-sided prism with a chamfered top edge: sides + chamfer + top, no bottom."""
    b = hex_ring(bm, u, v, APO, 0.0)
    m = hex_ring(bm, u, v, APO, h - chamfer)
    t = hex_ring(bm, u, v, APO - chamfer, h)
    bridge(bm, b, m, mi)
    bridge(bm, m, t, mi)
    bm.faces.new(t).material_index = mi


def add_collar(bm, u, v, h):
    """Cyan outline ring hugging the top of a tile (material slot 1)."""
    o0 = hex_ring(bm, u, v, APO + 0.006, h - 0.05)
    o1 = hex_ring(bm, u, v, APO + 0.006, h + 0.014)
    i1 = hex_ring(bm, u, v, APO - 0.016, h + 0.014)
    i0 = hex_ring(bm, u, v, APO - 0.016, h - 0.008)
    bridge(bm, o0, o1, 1)
    bridge(bm, o1, i1, 1)
    bridge(bm, i1, i0, 1)


def add_post(bm, u, v, z0, length, r, sides=6):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides, radius1=r, radius2=r,
                          depth=length, matrix=Matrix.Translation((u, v, z0 + length / 2)))


def ball(name, r, loc, scale=(1, 1, 1), m=WHITE, u=8, v=5, rot=(0, 0, 0)):
    """Low-polygon sphere for small details (the kit sphere never drops below 8 rings)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    ob = mesh_obj(name, bm, [m], smooth=True)
    return place(ob, loc, rot, scale)


def group(name, *prefixes):
    """Join every static object whose name starts with one of the prefixes into one prop."""
    obs = [o for o in bpy.context.scene.objects
           if o.type in ('MESH', 'CURVE') and not o.get('anim') and not o.get('helper') and o.name.startswith(prefixes)]
    return join(obs, name)


def add_ball(bm, u, v, z, r):
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r,
                              matrix=Matrix.Translation((u, v, z)))


# ---------------------------------------------------------------- the made-up city
def _g(u, v, cu, cv, ru, rv):
    return math.exp(-(((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2))


def city_shape(u, v):
    """Insideness of the city outline: tall body, an arm to the west, a lobe to the south."""
    def e(cu, cv, ru, rv):
        return 1 - ((u - cu) / ru) ** 2 - ((v - cv) / rv) ** 2
    f = max(e(0.69, 0.31, 0.80, 1.50),      # main body, taller north-south
            e(-0.33, -0.13, 1.14, 0.44),    # arm to the west
            e(0.91, -1.55, 0.55, 0.50),     # lobe to the south
            e(0.39, 1.41, 0.60, 0.42))      # northern shoulder
    return f + 0.05 * math.sin(4.1 * u + 2.3 * v + 0.6) + 0.04 * math.sin(7.3 * v - 3.1 * u)


def heat_field(u, v):
    h = 0.30
    h += 0.80 * _g(u, v, 0.57, -0.17, 0.60, 0.62)    # hot core
    h += 0.50 * _g(u, v, -0.66, -0.15, 0.52, 0.32)   # paved western arm
    h += 0.28 * _g(u, v, 1.00, 0.92, 0.38, 0.42)
    h -= 0.50 * _g(u, v, 1.06, 0.31, 0.25, 0.27)     # vegetated pocket
    h -= 0.42 * _g(u, v, 0.32, 1.50, 0.52, 0.38)     # cooler northern edge
    h -= 0.36 * _g(u, v, 0.93, -1.62, 0.40, 0.38)    # greener southern lobe
    h -= 0.30 * _g(u, v, 0.22, 0.75, 0.23, 0.23)     # park
    h += 0.05 * math.sin(9.0 * u + 1.3) * math.cos(8.0 * v + 0.4) + 0.03 * math.sin(15 * u - 11 * v)
    return h


def burden_field(u, v):
    """Stand-in for built burden + exposure + sensitivity (also made up)."""
    return (0.9 * _g(u, v, 0.39, -0.80, 0.60, 0.38) + 0.7 * _g(u, v, -0.90, -0.32, 0.40, 0.28)
            + 0.04 * math.sin(11 * u + 5 * v))


def make_tracts():
    cands = []
    for j in range(-18, 19):
        for i in range(-16, 17):
            u = S * (i + 0.5 * (j % 2)) + 0.03
            v = S * 0.8660254 * j - 0.02
            cands.append((city_shape(u, v), u, v))
    cands.sort(reverse=True)
    cells = [(u, v) for _, u, v in cands[:N_TRACTS]]
    raw = [heat_field(u, v) for u, v in cells]
    lo, hi = min(raw), max(raw)
    rank = {i: k for k, i in enumerate(sorted(range(len(raw)), key=lambda i: raw[i]))}
    heat = [0.55 * (r - lo) / (hi - lo) + 0.45 * rank[i] / (len(raw) - 1) for i, r in enumerate(raw)]
    prio = [0.5 * heat[i] + 0.5 * burden_field(u, v) for i, (u, v) in enumerate(cells)]
    order = sorted(range(len(cells)), key=lambda i: (-heat[i], i))
    hot = order[:N_TOP]
    hot_set = set(hot)
    both = sorted(hot, key=lambda i: (-prio[i], i))[:N_BOTH]
    only_prio = sorted((i for i in range(len(cells)) if i not in hot_set),
                       key=lambda i: (-prio[i], i))[:N_TOP - N_BOTH]
    return cells, heat, hot, both, only_prio


# ---------------------------------------------------------------- desert plants
def saguaro(name, x, y, h, r, arms, m=CACTUS):
    """Rounded column with upturned arms. arms: (angle_deg, z_start, reach, rise)."""
    parts = [lathe(name + '_trunk', [(0, 0), (r * 0.9, 0), (r, h * 0.25), (r, h - r * 0.95),
                                     (r * 0.88, h - r * 0.5), (r * 0.55, h - r * 0.13), (0, h)],
                   (x, y, 0), m=m, verts=14)]
    for i, (ang, z0, reach, rise) in enumerate(arms):
        ar = r * 0.6
        dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        ex, ey = x + dx * (r + reach), y + dy * (r + reach)
        pts = [(x + dx * r * 0.2, y + dy * r * 0.2, z0), (ex, ey, z0 - 0.02),
               (ex, ey, z0 + rise * 0.35), (ex, ey, z0 + rise)]
        parts.append(tube(f'{name}_arm{i}', pts, ar, m, res=6))
        parts.append(ball(f'{name}_tip{i}', ar, (ex, ey, z0 + rise), m=m, u=12, v=6))
    for i in range(3):
        a = TAU * i / 3 + h
        parts.append(ball(f'{name}_bloom{i}', r * 0.2, (x + r * 0.42 * math.cos(a), y + r * 0.42 * math.sin(a),
                                                        h - r * 0.12), (1, 1, 0.7), WHITE, 6, 4))
    return join(parts, name)


def prickly_pear(name, x, y, s=1.0, seed=0, fruit='#c2476f'):
    rng = random.Random(seed)
    out = []
    yaw0 = rng.uniform(0, 180)
    base = []
    for i in range(3):
        r = s * rng.uniform(0.2, 0.26)
        a = math.radians(yaw0 + i * 120 + rng.uniform(-20, 20))
        px, py = x + 0.16 * s * math.cos(a), y + 0.16 * s * math.sin(a)
        yaw = yaw0 + i * 55 + rng.uniform(-15, 15)
        out.append(ball(f'{name}_pad{i}', r, (px, py, r * 0.95), (0.9, 0.3, 1.1), CACTUS if i % 2 else CACTUS_D, 10, 6,
                        rot=(rng.uniform(-10, 10), rng.uniform(-12, 12), yaw)))
        base.append((px, py, r, yaw))
    for i, (px, py, r, yaw) in enumerate(base[:2 + seed % 2]):
        side = 1 if i % 2 else -1
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        r2 = r * 0.72
        ux, uy, uz = px + side * ca * r * 0.5, py + side * sa * r * 0.5, r * 1.75 + r2 * 0.55
        out.append(ball(f'{name}_up{i}', r2, (ux, uy, uz), (0.9, 0.3, 1.1), CACTUS, 10, 6, rot=(0, side * 22, yaw)))
        out.append(ball(f'{name}_fruit{i}', r * 0.2, (ux + side * ca * r2 * 0.3, uy + side * sa * r2 * 0.3,
                                                      uz + r2 * 1.05), (1, 1, 1.25), fruit, 6, 4))
        out.append(ball(f'{name}_fruitb{i}', r * 0.17, (px - side * ca * r * 0.45, py - side * sa * r * 0.45,
                                                       r * 1.9), (1, 1, 1.25), fruit, 6, 4))
    return join(out, name)


def agave(name, x, y, s=1.0, m='#86b3a0', n=9):
    out = []
    for i in range(n):
        a = 360 * i / n
        lean = 52 if i % 2 else 34
        ln = s * (0.42 if i % 2 else 0.5)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        off = math.sin(math.radians(lean)) * ln / 2
        out.append(cyl(f'{name}_{i}', 0.07 * s, ln, (x + ca * off, y + sa * off, math.cos(math.radians(lean)) * ln / 2 + 0.02),
                       (0, lean, a), m, r2=0.008, verts=6, bevel=0))
    return join(out, name)


def ocotillo(name, x, y, h=1.4, seed=0, n=7):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        a = 360 * i / n + rng.uniform(-15, 15)
        lean = rng.uniform(9, 26)
        ln = h * rng.uniform(0.72, 1.0)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        sl, cl = math.sin(math.radians(lean)), math.cos(math.radians(lean))
        out.append(cyl(f'{name}_{i}', 0.036, ln, (x + ca * sl * ln / 2, y + sa * sl * ln / 2, cl * ln / 2), (0, lean, a),
                       '#8f9c6c', r2=0.02, verts=6, bevel=0))
        out.append(ball(f'{name}_tip{i}', 0.045, (x + ca * sl * ln, y + sa * sl * ln, cl * ln), (1, 1, 1.7), P_RED, 6, 4,
                        rot=(0, lean, a)))
    return join(out, name)


def barrel_cactus(name, x, y, r=0.2):
    return join([ball(name + '_body', r, (x, y, r * 0.95), (1, 1, 1.12), CACTUS_D, 12, 7),
                 ball(name + '_crown', r * 0.32, (x, y, r * 1.98), (1, 1, 0.5), P_GOLD, 8, 4)], name)


# ---------------------------------------------------------------- build
def build(mode='preview'):
    reset()
    setup_world()
    base, radius_at = island_base(R=5.5, seed=23, top=SAND_TOP, lip='#dfb190', soil=TERRA, soil2=RUST,
                                  rock_c='#8f4d38', lobes=((2, 0.045), (3, 0.04), (4, 0.03)))

    rot = Euler((math.radians(TILT), 0, math.radians(YAW))).to_matrix()
    M = Matrix.Translation(C) @ rot.to_4x4()
    yaw_m = Matrix.Rotation(math.radians(YAW), 3, 'Z')
    TROT = (TILT, 0, YAW)

    def W(u, v, w=0.0):
        """Table-local (east, north, up from the slab top) -> world."""
        return tuple(M @ Vector((u, v, w)))

    def G(u, q, z=0.0):
        """Ground plan under the table: yawed but not tilted."""
        p = yaw_m @ Vector((u, q, 0))
        return (C.x + p.x, C.y + p.y, z)

    # paler dry-wash patches break up the sand
    for k, (x, y, r, sc) in enumerate(((3.05, -1.45, 1.75, (1.12, 0.92, 1)), (-1.75, -3.9, 1.3, (1.55, 0.6, 1)),
                                       (-3.6, 1.5, 1.2, (0.8, 1.3, 1)))):
        w = lathe(f'wash_{k}', [(0.0, 0.012), (r * 0.84, 0.012), (r * 0.97, -0.004), (r, -0.03)], (x, y, 0), m=PALE, verts=36)
        w.scale = sc

    # ------------------------------------------------ 1. tract-map table
    box('map_slab', (SLAB_W, SLAB_L, SLAB_T), W(0, 0, -SLAB_T / 2), TROT, PAPER, bevel=0.03, seg=2)
    for i, sx in enumerate((-1, 1)):
        box(f'map_rim_side{i}', (0.14, SLAB_L + 0.14, 0.25), W(sx * SLAB_W / 2, 0, -0.065), TROT, TERRA, bevel=0.04, seg=2)
        box(f'map_rim_end{i}', (SLAB_W + 0.14, 0.14, 0.25), W(0, sx * SLAB_L / 2, -0.065), TROT, TERRA, bevel=0.04, seg=2)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        ball(f'map_corner{i}', 0.085, W(sx * SLAB_W / 2, sy * SLAB_L / 2, 0.07), m=RUST, u=10, v=6)

    # adobe trestle panels following the tilted underside
    tt, st, ct = math.tan(math.radians(TILT)), math.sin(math.radians(TILT)), math.cos(math.radians(TILT))

    def under(q):
        return C.z + (q - SLAB_T * st) * tt - SLAB_T * ct + 0.035
    q0, q1 = -2.05, 2.05
    arch = [(0.55 - 0.62 * math.cos(math.pi * k / 8), 0.5 * math.sin(math.pi * k / 8)) for k in range(9)]
    outline = [(q0, 0), (arch[0][0], 0)] + arch[1:-1] + [(arch[-1][0], 0), (q1, 0), (q1, under(q1)), (q0, under(q0))]
    for i, u0 in enumerate((-1.52, 1.24)):
        prism(f'map_trestle{i}', outline, 0.28, G(u0, 0, 0), (90, 0, 90 + YAW), ADOBE, bevel=0.04, seg=2)
    box('map_stretcher_front', (2.8, 0.16, 0.14), G(0, -1.75, 0.12), (0, 0, YAW), RUST, bevel=0.03, seg=2)
    box('map_stretcher_back', (2.8, 0.16, 0.16), G(0, 1.82, 0.72), (0, 0, YAW), RUST, bevel=0.03, seg=2)

    # the 369 tiles
    cells, heat, hot, both, only_prio = make_tracts()
    bands = 12
    tile_mats = [mat(inferno(k / (bands - 1)), 0.7, emit=0.45 * max(0.0, (k / (bands - 1) - 0.72) / 0.28))
                 for k in range(bands)]
    height = [0.07 + 0.40 * t ** 1.5 for t in heat]
    bm = bmesh.new()
    for (u, v), t, h in zip(cells, heat, height):
        add_tile(bm, u, v, h, min(bands - 1, int(t * bands)))
    mesh_obj('tract_tiles', bm, tile_mats, M)

    # 37 hottest: cyan outline + cyan post
    post_len, short_len, head_r = 0.42, 0.13, 0.06
    bm = bmesh.new()
    for i in hot:
        u, v = cells[i]
        add_collar(bm, u, v, height[i])
        add_post(bm, u, v, height[i] - 0.01, post_len + 0.01, 0.023)
        if i not in both:
            add_post(bm, u, v, height[i] + post_len - 0.005, 0.035, 0.04)   # flat cyan cap
    mesh_obj('hot_outline_37', bm, [mat(CYAN, 0.4, emit=1.2), mat(CYAN, 0.55, emit=0.45)], M)
    # 20 priority-only tiles: short white post
    bm = bmesh.new()
    for i in only_prio:
        u, v = cells[i]
        add_post(bm, u, v, height[i] - 0.01, short_len + 0.01, 0.022)
        add_post(bm, u, v, height[i] - 0.01, 0.03, 0.05, 8)               # white foot
    mesh_obj('priority_posts_20', bm, [mat(WHITE, 0.5)], M)
    # 37 coral pin heads: 17 on cyan posts, 20 on white posts
    bm = bmesh.new()
    for i in both:
        add_ball(bm, cells[i][0], cells[i][1], height[i] + post_len + head_r * 0.6, head_r)
    for i in only_prio:
        add_ball(bm, cells[i][0], cells[i][1], height[i] + short_len + head_r * 0.6, head_r)
    mesh_obj('priority_pins_37', bm, [mat(PIN, 0.4, emit=0.4)], M, smooth=True)
    us = [c[0] for c in cells]
    vs = [c[1] for c in cells]
    print(f'[kit] phoenix tiles={len(cells)} hot={len(hot)} both={len(both)} hot_only={len(hot) - len(both)} '
          f'priority_only={len(only_prio)} pins={len(both) + len(only_prio)} '
          f'u=[{min(us):.2f},{max(us):.2f}] v=[{min(vs):.2f},{max(vs):.2f}]')
    assert (len(cells), len(hot), len(both), len(only_prio)) == (N_TRACTS, N_TOP, N_BOTH, N_TOP - N_BOTH)
    assert not set(hot) & set(only_prio)

    # legend: one stepped bar running up the heat ramp, and a north arrow
    steps = [box(f'legend_{k}', (0.15, 0.2, 0.05 + 0.06 * k), W(-1.6 + 0.15 * k, -2.0, (0.05 + 0.06 * k) / 2 - 0.004),
                 TROT, mat(inferno(k / 4), 0.7), bevel=0.012, seg=1) for k in range(5)]
    join(steps, 'legend_ramp')
    prism('north_arrow', [(0, 0.3), (-0.15, 0.02), (-0.05, 0.05), (-0.05, -0.24), (0.05, -0.24), (0.05, 0.05), (0.15, 0.02)],
          0.05, W(-1.45, 1.78, -0.004), TROT, RUST, bevel=0.012, seg=1)

    # ------------------------------------------------ 3. Landsat-style satellite on an arc
    vf = 0.52                                   # the swath crosses the map here
    sx, sy, _ = W(0.4, vf, 0)
    sz = 4.2
    SR = (0, 0, YAW)

    def SL(dx, dy, dz):
        p = yaw_m @ Vector((dx, dy, 0))
        return (sx + p.x, sy + p.y, sz + dz)
    sat = [box('sat_body', (0.5, 0.48, 0.62), SL(0, 0, 0), SR, PAPER, bevel=0.06),
           box('sat_foil', (0.53, 0.51, 0.24), SL(0, 0, -0.1), SR, P_GOLD, bevel=0.03, seg=2),
           box('sat_pack', (0.2, 0.1, 0.22), SL(0.08, -0.27, 0.16), SR, TERRA, bevel=0.03, seg=2),
           cyl('sat_barrel', 0.17, 0.36, SL(0, 0, -0.47), m=STEEL_DARK, verts=20, bevel=0.03, seg=2),
           torus('sat_hood', 0.17, 0.03, SL(0, 0, -0.64), m=STEEL, seg=20, ring=6),
           cyl('sat_lens', 0.12, 0.04, SL(0, 0, -0.645), m=mat(CYAN, 0.3, emit=3.0), verts=16, bevel=0.01, seg=1),
           ball('sat_mount', 0.1, SL(0, 0, 0.36), m=RUST, u=12, v=6),
           cyl('sat_dish_rod', 0.025, 0.2, SL(-0.15, 0.12, 0.4), m=STEEL_DARK, verts=8, bevel=0),
           cyl('sat_dish', 0.03, 0.1, SL(-0.15, 0.12, 0.53), (0, -24, YAW), WHITE, r2=0.16, verts=16, bevel=0.01, seg=1)]
    for s in (-1, 1):
        sat.append(cyl(f'sat_boom{s}', 0.035, 0.34, SL(s * 0.4, 0, 0.02), (0, 90, YAW), STEEL_DARK, verts=8, bevel=0))
        pc = s * 1.0
        sat.append(box(f'sat_panel{s}', (0.9, 0.54, 0.05), SL(pc, 0, 0.02), (18, 0, YAW), '#2f4f86', bevel=0.02, seg=2))
        for k, dx in enumerate((-0.3, 0.0, 0.3)):
            sat.append(box(f'sat_cell{s}_{k}', (0.025, 0.55, 0.066), SL(pc + dx, 0, 0.02), (18, 0, YAW), STEEL, bevel=0.006, seg=1))
        sat.append(box(f'sat_spar{s}', (0.91, 0.025, 0.066), SL(pc, 0, 0.02), (18, 0, YAW), STEEL, bevel=0.006, seg=1))
    sat = join(sat, 'satellite')
    set_origin(sat, (sx, sy, sz + 0.36))
    animate(sat, 'sway', amp=9, speed=0.5, axis='z')

    ax, ay = 2.0, 2.95
    tube('sat_arc', [(ax, ay, 0.3), (ax + 0.25, ay + 0.3, 2.7), (ax - 0.55, ay - 0.55, 4.45),
                     (sx + 0.55, sy + 0.75, 4.97), (sx, sy, sz + 0.4)], 0.055, RUST, res=10)
    lathe('sat_arc_base', [(0, 0), (0.42, 0), (0.42, 0.1), (0.3, 0.16), (0.16, 0.34), (0.1, 0.5), (0, 0.5)],
          (ax, ay, 0), m=TERRA, verts=20)
    torus('sat_arc_collar', 0.13, 0.04, (ax, ay, 0.42), m=RUST, seg=16, ring=6)

    # scan fan: a thin, faint emissive swath from the sensor down to one row of the map
    near = [i for i, (u, v) in enumerate(cells) if abs(v - vf) < S * 0.6]
    fan_w = max(height[i] for i in near) + 0.05
    apex = Vector((sx, sy, sz - 0.66))
    sw_a = Vector(W(min(cells[i][0] for i in near) - 0.1, vf, fan_w))
    sw_b = Vector(W(max(cells[i][0] for i in near) + 0.1, vf, fan_w))
    nrm = (M.to_3x3() @ Vector((0, 1, 0))) * 0.016
    bm = bmesh.new()
    front = [bm.verts.new(p - nrm) for p in (apex, sw_a, sw_b)]
    back = [bm.verts.new(p + nrm) for p in (apex, sw_a, sw_b)]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    bridge(bm, front, back)
    fan = mesh_obj('scan_fan', bm, [mat(CYAN, 0.5, emit=1.6, alpha=0.1, name='scan_fan')])
    edge = mat(CYAN, 0.4, emit=3.0, alpha=0.85, name='scan_edge')
    beam = join([fan, tube('scan_swath', [tuple(sw_a), tuple(sw_b)], 0.024, edge, smooth_curve=False),
                 tube('scan_ray_a', [tuple(apex), tuple(sw_a)], 0.015, edge, smooth_curve=False),
                 tube('scan_ray_b', [tuple(apex), tuple(sw_b)], 0.015, edge, smooth_curve=False)], 'scan_beam')
    beam.visible_shadow = False
    keep_material(beam)
    animate(beam, 'pulse', speed=1.1)

    # ------------------------------------------------ 4. cooling station
    cx, cy = 3.15, -1.2
    box('cool_pad', (2.5, 2.0, 0.07), (cx, cy, 0.03), m=PALE, bevel=0.03, seg=2)
    slope = 10
    zc = 1.66
    for i, (px, py) in enumerate(((-0.98, -0.72), (0.98, -0.72), (-0.98, 0.72), (0.98, 0.72))):
        top = zc + py * math.tan(math.radians(slope)) - 0.02
        cyl(f'cool_post{i}', 0.055, top - 0.05, (cx + px, cy + py, 0.05 + (top - 0.05) / 2), m=WHITE, verts=12, bevel=0.015, seg=1)
        cyl(f'cool_foot{i}', 0.1, 0.07, (cx + px, cy + py, 0.1), m=STEEL_DARK, verts=12, bevel=0.02, seg=1)
    box('cool_canopy', (2.36, 1.84, 0.09), (cx, cy, zc), (slope, 0, 0), PAPER, bevel=0.035)
    for i, dx in enumerate((-0.92, -0.46, 0.0, 0.46, 0.92)):
        box(f'cool_stripe{i}', (0.2, 1.85, 0.105), (cx + dx, cy, zc), (slope, 0, 0), WATER, bevel=0.03, seg=2)
    # bench
    bx, by = cx + 0.02, cy + 0.5
    box('bench_seat', (1.0, 0.32, 0.07), (bx, by, 0.42), m=WOOD, bevel=0.025, seg=2)
    box('bench_back', (1.0, 0.07, 0.26), (bx, by + 0.16, 0.7), (-8, 0, 0), WOOD, bevel=0.025, seg=2)
    for s in (-1, 1):
        box(f'bench_leg{s}', (0.08, 0.3, 0.36), (bx + s * 0.4, by, 0.23), m=WOOD_DARK, bevel=0.02, seg=1)
        box(f'bench_stile{s}', (0.07, 0.07, 0.5), (bx + s * 0.4, by + 0.15, 0.6), (-8, 0, 0), WOOD_DARK, bevel=0.02, seg=1)
    # water cooler
    wx, wy = cx - 0.78, cy + 0.42
    box('cooler_body', (0.34, 0.34, 0.74), (wx, wy, 0.43), m=WHITE, bevel=0.05)
    lathe('cooler_bottle', [(0, 0), (0.06, 0), (0.07, 0.06), (0.15, 0.13), (0.15, 0.4), (0.11, 0.46), (0, 0.46)],
          (wx, wy, 0.79), m=mat('#7cc0ee', 0.25, emit=0.25), verts=16)
    box('cooler_panel', (0.24, 0.03, 0.16), (wx, wy - 0.17, 0.6), m=STEEL, bevel=0.01, seg=1)
    box('cooler_tap_cold', (0.05, 0.07, 0.06), (wx - 0.06, wy - 0.2, 0.6), m=WATER, bevel=0.012, seg=1)
    box('cooler_tap_warm', (0.05, 0.07, 0.06), (wx + 0.06, wy - 0.2, 0.6), m=P_RED, bevel=0.012, seg=1)
    box('cooler_tray', (0.26, 0.1, 0.03), (wx, wy - 0.2, 0.46), m=STEEL_DARK, bevel=0.01, seg=1)
    # misting fan (rotor spins about world Y)
    fx, fy, fz = cx + 0.84, cy - 0.3, 1.02
    cyl('fan_base', 0.2, 0.07, (fx, fy, 0.1), m=STEEL_DARK, verts=16, bevel=0.02, seg=1)
    cyl('fan_pole', 0.035, 0.9, (fx, fy, 0.56), m=STEEL, verts=10, bevel=0)
    cyl('fan_motor', 0.1, 0.22, (fx, fy + 0.07, fz), (90, 0, 0), WHITE, verts=14, bevel=0.03, seg=2)
    torus('fan_cage_front', 0.31, 0.022, (fx, fy - 0.1, fz), (90, 0, 0), STEEL, seg=20, ring=6)
    torus('fan_cage_back', 0.31, 0.022, (fx, fy + 0.02, fz), (90, 0, 0), STEEL, seg=20, ring=6)
    for k in range(4):
        a = TAU * k / 4 + 0.4
        cyl(f'fan_cage_rib{k}', 0.016, 0.13, (fx + 0.31 * math.cos(a), fy - 0.04, fz + 0.31 * math.sin(a)), (90, 0, 0),
            STEEL, verts=6, bevel=0)
    mist = mat('#9fd8f2', 0.3, emit=0.6)
    for k in range(6):
        a = TAU * k / 6
        ball(f'fan_mist{k}', 0.038, (fx + 0.31 * math.cos(a), fy - 0.125, fz + 0.31 * math.sin(a)), m=mist, u=6, v=4)
    rotor = [ball('fan_hub', 0.065, (fx, fy - 0.04, fz), m=WATER, u=8, v=5)]
    for k in range(3):
        a = 120 * k + 20
        rotor.append(ball(f'fan_blade{k}', 0.1, (fx + 0.155 * math.sin(math.radians(a)), fy - 0.04,
                                                 fz + 0.155 * math.cos(math.radians(a))),
                          (0.8, 0.16, 1.4), '#8fc6e8', 8, 5, rot=(22, a, 0)))
    rotor = join(rotor, 'fan_rotor')
    set_origin(rotor, (fx, fy - 0.04, fz))
    animate(rotor, 'spin', axis='y', speed=7.0)
    # water-drop sign (a drop on both faces of a round board)
    gx, gy, gth, gz = cx, cy - 0.86, -20, 2.12
    nx, ny = math.sin(math.radians(gth)), -math.cos(math.radians(gth))
    cyl('drop_post', 0.05, 0.42, (gx, gy, 1.66), m=WHITE, verts=12, bevel=0.01, seg=1)
    cyl('drop_foot', 0.1, 0.07, (gx, gy, 1.55), (slope, 0, 0), STEEL_DARK, verts=12, bevel=0.02, seg=1)
    cyl('drop_board', 0.4, 0.08, (gx, gy, gz), (90, 0, gth), WHITE, verts=28, bevel=0.025, seg=2)
    torus('drop_ring', 0.4, 0.035, (gx, gy, gz), (90, 0, gth), WATER, seg=28, ring=6)
    drop_m = mat(WATER, 0.35, emit=0.7)
    for k, off in enumerate((0.05, -0.05)):
        drop = lathe(f'drop_sign{k}', [(0, 0), (0.11, 0.025), (0.185, 0.12), (0.19, 0.2), (0.14, 0.32), (0.06, 0.45), (0, 0.54)],
                     (gx + nx * off, gy + ny * off, gz - 0.25), (0, 0, gth), drop_m, verts=16)
        drop.scale = (1, 0.3, 1)

    # ------------------------------------------------ 5. three profile totems
    for k, (tx, ty, col) in enumerate(((-2.75, -3.72, P_RED), (-1.7, -4.02, P_GOLD), (-0.65, -4.18, P_TEAL))):
        lathe(f'totem_{k}', [(0, 0), (0.37, 0), (0.37, 0.08), (0.3, 0.13), (0.3, 0.5), (0.37, 0.55), (0.37, 0.64), (0, 0.64)],
              (tx, ty, 0), m=col, verts=20)
        z = 0.64
        if k == 0:      # dense built-up block
            for j, (dx, dy, w, hh) in enumerate(((-0.1, 0.06, 0.22, 0.56), (0.13, -0.04, 0.2, 0.38), (-0.06, -0.17, 0.17, 0.24),
                                                 (0.14, 0.17, 0.16, 0.28))):
                box(f'totem_bld{j}', (w, w, hh), (tx + dx, ty + dy, z + hh / 2 - 0.01), (0, 0, 8), PAPER, bevel=0.02, seg=2)
                box(f'totem_bld_cap{j}', (w * 0.8, w * 0.8, 0.04), (tx + dx, ty + dy, z + hh), (0, 0, 8), col, bevel=0.012, seg=1)
        elif k == 1:    # a house and a distance marker
            box('totem_house', (0.3, 0.26, 0.2), (tx - 0.12, ty + 0.03, z + 0.09), m=PAPER, bevel=0.02, seg=2)
            prism('totem_house_roof', [(-0.2, 0), (0.2, 0), (0, 0.17)], 0.3, (tx - 0.12, ty + 0.18, z + 0.18), (90, 0, 0),
                  TERRA, bevel=0.02, seg=2)
            for j in range(3):
                cyl(f'totem_dash{j}', 0.03, 0.03, (tx + 0.06 + j * 0.065, ty - 0.2 + j * 0.03, z + 0.005), m=RUST, verts=8,
                    bevel=0.008, seg=1)
            cyl('totem_marker_post', 0.028, 0.42, (tx + 0.24, ty - 0.08, z + 0.2), m=WHITE, verts=8, bevel=0)
            box('totem_marker', (0.15, 0.05, 0.15), (tx + 0.24, ty - 0.08, z + 0.45), (0, 45, -25), col, bevel=0.015, seg=1)
        else:           # a tree
            cyl('totem_tree_trunk', 0.05, 0.3, (tx, ty, z + 0.14), m=WOOD_DARK, r2=0.035, verts=8, bevel=0.005, seg=1)
            blob('totem_tree_a', 0.24, (tx, ty, z + 0.44), (1, 1, 0.92), CACTUS, 3, seg=2)
            blob('totem_tree_b', 0.15, (tx + 0.14, ty - 0.05, z + 0.34), (1, 1, 0.9), CACTUS_D, 4, seg=2)

    # ------------------------------------------------ data corner
    # eleven Landsat scenes, combined per pixel: a stack of exactly 11 plates
    kx, ky = 1.3, -3.45
    box('scene_plinth', (0.7, 0.7, 0.2), (kx, ky, 0.1), (0, 0, 12), TERRA, bevel=0.04, seg=2)
    for k in range(11):
        box(f'scene_{k}', (0.52, 0.52, 0.04), (kx + 0.012 * math.sin(k * 2.1), ky + 0.012 * math.cos(k * 1.7), 0.22 + 0.047 * k),
            (0, 0, 12 + (k % 3 - 1) * 5), mat(inferno(0.12 + 0.08 * k), 0.7), bevel=0.012, seg=1)
    # the three layers joined per tract: vegetation, paved surface, census
    rx, ry, rth = 0.28, -3.72, -14
    rm = Matrix.Rotation(math.radians(rth), 3, 'Z')

    def RK(dx, dy, z):
        p = rm @ Vector((dx, dy, 0))
        return (rx + p.x, ry + p.y, z)
    for i, (dx, dy) in enumerate(((-0.26, -0.26), (0.26, -0.26), (-0.26, 0.26), (0.26, 0.26))):
        cyl(f'layer_rod{i}', 0.026, 0.98, RK(dx, dy, 0.49), m=RUST, verts=8, bevel=0)
        ball(f'layer_knob{i}', 0.045, RK(dx, dy, 0.99), m=RUST, u=8, v=5)
    for i, (z, colr) in enumerate(((0.2, CACTUS), (0.5, STEEL), (0.8, PAPER))):
        box(f'layer_plate{i}', (0.62, 0.62, 0.05), RK(0, 0, z), (0, 0, rth), colr, bevel=0.015, seg=1)
    for i, (dx, dy, r) in enumerate(((-0.12, 0.08, 0.1), (0.12, -0.06, 0.08), (0.06, 0.15, 0.06), (-0.1, -0.14, 0.06))):
        ball(f'layer_veg{i}', r, RK(dx, dy, 0.225 + r * 0.5), (1, 1, 0.8), CACTUS_D, 8, 5)
    box('layer_road_a', (0.5, 0.09, 0.02), RK(0, 0.04, 0.53), (0, 0, rth), STEEL_DARK, bevel=0.006, seg=1)
    box('layer_road_b', (0.09, 0.5, 0.022), RK(-0.08, 0, 0.53), (0, 0, rth), STEEL_DARK, bevel=0.006, seg=1)
    for i, (dx, dy, hh) in enumerate(((-0.14, 0.12, 0.16), (0.02, -0.02, 0.12), (0.15, 0.1, 0.14), (-0.08, -0.15, 0.1), (0.14, -0.14, 0.12))):
        cyl(f'layer_person{i}', 0.04, hh, RK(dx, dy, 0.825 + hh / 2), m=(TERRA, P_GOLD, P_TEAL)[i % 3], r2=0.02, verts=8, bevel=0)
        ball(f'layer_head{i}', 0.036, RK(dx, dy, 0.825 + hh + 0.025), m=PALE, u=8, v=5)

    # ------------------------------------------------ thermometer sculpture
    hx, hy, hth = -4.25, 0.75, -38
    hnx, hny = math.sin(math.radians(hth)), -math.cos(math.radians(hth))
    lathe('thermo_plinth', [(0, 0), (0.52, 0), (0.52, 0.1), (0.44, 0.16), (0, 0.16)], (hx, hy, 0), m=RUST, verts=20)
    stadium = [(0.3 * math.cos(a), 0.3 * math.sin(a) - 0.72) for a in [math.pi + math.pi * k / 8 for k in range(9)]] + \
              [(0.3 * math.cos(a), 0.3 * math.sin(a) + 0.72) for a in [math.pi * k / 8 for k in range(9)]]
    prism('thermo_board', stadium, 0.1, (hx - hnx * 0.1, hy - hny * 0.1, 1.16), (90, 0, hth), PAPER, bevel=0.03, seg=2)
    tx0, ty0 = hx + hnx * 0.16, hy + hny * 0.16
    col = lathe('thermo_column', [(0, 0), (0.12, 0.02), (0.2, 0.09), (0.235, 0.22), (0.2, 0.36), (0.13, 0.43), (0.095, 0.5),
                                  (0.095, 1.28), (0, 1.28)], (tx0, ty0, 0.15),
                m=mat('#e23b2c', 0.35, emit=1.2, emit_color='#f0402c'), verts=16)
    animate(col, 'pulse', speed=0.8)
    lathe('thermo_glass', [(0.095, 1.28), (0.095, 1.72), (0.07, 1.8), (0, 1.83)], (tx0, ty0, 0.15), m=WHITE, verts=16)
    ca, sa = math.cos(math.radians(hth)), math.sin(math.radians(hth))
    for k, zz in enumerate((0.8, 1.85)):
        box(f'thermo_clip{k}', (0.3, 0.2, 0.06), (hx + hnx * 0.1, hy + hny * 0.1, zz), (0, 0, hth), STEEL_DARK, bevel=0.02, seg=1)
    for k in range(9):
        ln = 0.13 if k % 2 == 0 else 0.08
        off = 0.26 - ln / 2
        box(f'thermo_tick{k}', (ln, 0.03, 0.035), (hx + ca * off + hnx * 0.005, hy + sa * off + hny * 0.005, 0.72 + 0.13 * k),
            (0, 0, hth), RUST, bevel=0.008, seg=1)
    # spine and brace so the back reads as a finished object
    box('thermo_spine', (0.16, 0.08, 1.7), (hx - hnx * 0.13, hy - hny * 0.13, 1.0), (0, 0, hth), TERRA, bevel=0.03, seg=1)
    box('thermo_brace', (0.12, 0.5, 0.1), (hx - hnx * 0.3, hy - hny * 0.3, 0.42), (48, 0, hth), TERRA, bevel=0.03, seg=1)

    # ------------------------------------------------ pale sun disc on a stand
    ux, uy, uth, uz = 4.5, 1.95, -30, 2.8
    unx, uny = math.sin(math.radians(uth)), -math.cos(math.radians(uth))
    lathe('sun_base', [(0, 0), (0.34, 0), (0.34, 0.08), (0.14, 0.2), (0.07, 0.32), (0, 0.32)], (ux, uy, 0), m=TERRA, verts=16)
    cyl('sun_pole', 0.05, uz - 0.6, (ux, uy, (uz - 0.6) / 2 + 0.15), m=RUST, verts=10, bevel=0.01, seg=1)
    sun = [cyl('sun_face', 0.5, 0.1, (ux, uy, uz), (90, 0, uth), mat('#fdebb4', 0.5, emit=1.2, emit_color='#ffd98a'),
               verts=28, bevel=0.035, seg=2)]
    ca, sa = math.cos(math.radians(uth)), math.sin(math.radians(uth))
    for k in range(10):
        ph = 360 * k / 10
        cp, sp = math.cos(math.radians(ph)), math.sin(math.radians(ph))
        rr = 0.7
        sun.append(box(f'sun_ray{k}', (0.2, 0.08, 0.08), (ux + ca * cp * rr, uy + sa * cp * rr, uz + sp * rr),
                       (0, -ph, uth), P_GOLD, bevel=0.03, seg=1))
    ball('sun_hub', 0.09, (ux - unx * 0.07, uy - uny * 0.07, uz), m=RUST, u=10, v=6)
    join(sun, 'sun_disc')

    # ------------------------------------------------ 6. desert setting
    saguaro('saguaro_tall', -2.35, 3.55, 3.0, 0.27, [(200, 1.25, 0.34, 0.95), (15, 1.7, 0.3, 0.75)])
    saguaro('saguaro_mid', 3.25, 3.05, 2.15, 0.23, [(-30, 0.95, 0.28, 0.7), (160, 1.2, 0.24, 0.45)])
    saguaro('saguaro_small', -4.45, -1.55, 1.35, 0.19, [(165, 0.5, 0.2, 0.45), (-10, 0.72, 0.16, 0.3)])

    # low adobe wall behind the cooling station
    box('wall_main', (2.3, 0.36, 0.72), (3.45, 0.42, 0.36), (0, 0, -6), ADOBE, bevel=0.1)
    box('wall_step', (0.9, 0.38, 0.46), (4.72, 0.02, 0.23), (0, 0, -38), ADOBE, bevel=0.1)
    box('wall_pier', (0.5, 0.5, 1.05), (2.2, 0.55, 0.52), (0, 0, -6), ADOBE, bevel=0.1)
    box('wall_pier_cap', (0.6, 0.6, 0.1), (2.2, 0.55, 1.08), (0, 0, -6), TERRA, bevel=0.035, seg=2)
    for k in range(4):
        cyl(f'wall_viga{k}', 0.05, 0.5, (2.85 + k * 0.45, 0.32 - k * 0.047, 0.55), (90, 0, -6), WOOD_DARK, verts=8, bevel=0.01, seg=1)
    lathe('wall_pot', [(0, 0), (0.1, 0), (0.16, 0.12), (0.13, 0.24), (0.09, 0.27), (0.11, 0.3), (0, 0.3)], (2.2, 0.55, 1.13),
          m=TERRA, verts=12)

    for k, (x, y, s) in enumerate(((-3.7, 2.55, 1.0), (0.2, 3.95, 0.9), (4.55, -0.75, 0.8), (-3.35, -3.0, 0.85), (2.1, -4.05, 0.9))):
        prickly_pear(f'pear_{k}', x, y, s, seed=k + 3)
    agave('agave_a', -1.05, 4.25, 1.0)
    agave('agave_b', 4.05, 3.1, 0.85)
    agave('agave_c', -4.6, -0.35, 0.8)
    barrel_cactus('barrel_a', 0.75, -4.55, 0.2)
    barrel_cactus('barrel_b', -3.55, 3.55, 0.17)
    barrel_cactus('barrel_c', 2.75, 1.5, 0.18)

    ocotillo('ocotillo_a', 0.9, 4.05, 1.5, seed=2)
    ocotillo('ocotillo_b', -4.85, 1.35, 1.15, seed=5, n=6)
    ocotillo('ocotillo_c', 4.6, -2.75, 1.0, seed=8, n=6)

    rocks = [(-3.15, 3.9, 0.62), (-1.55, 4.45, 0.4), (-4.55, 2.1, 0.45), (1.05, 4.35, 0.5), (4.75, 2.9, 0.42), (3.6, -3.55, 0.4),
             (-4.1, -2.55, 0.36), (-1.9, -4.75, 0.3), (2.75, 3.95, 0.36), (5.0, 0.95, 0.3), (-4.95, 0.1, 0.28), (0.0, -5.0, 0.26)]
    for k, (x, y, r) in enumerate(rocks):
        rock(f'redrock_{k}', r, (x, y, r * 0.3), ('#b8684b', '#a2573d', '#8f4d38')[k % 3], seed=k + 40, squash=0.68)
    rock('redrock_top', 0.3, (-3.0, 3.95, 0.52), '#c47a5a', seed=77, squash=0.6)

    for k, (x, y) in enumerate(((-3.9, 1.9), (1.2, 3.3), (4.6, 0.2), (-2.2, -3.3), (2.25, -3.3), (3.9, -2.9), (-0.2, 4.6),
                                (-4.75, -0.95), (-0.35, -4.9), (-3.6, -3.55), (3.9, 2.2), (-1.7, 3.0))):
        join(grass_tuft(f'dry_{k}', (x, y, 0), h=0.26, n=6, m=DRY if k % 2 else '#b39a5e', seed=k + 5), f'dry_{k}')
    for k, (x, y, r) in enumerate(((1.75, 4.2, 0.28), (-4.3, 2.75, 0.24), (4.4, -2.3, 0.22), (-2.6, -4.3, 0.22), (5.0, 1.6, 0.2))):
        blob(f'sage_{k}', r, (x, y, r * 0.5), (1.2, 1.1, 0.75), SAGE if k % 2 else '#b9b58c', seed=k + 9, seg=2)

    rng = random.Random(4)
    pebbles = []
    busy = [(3.15, -1.2, 1.75), (3.5, 0.4, 1.4), (-4.25, 0.75, 0.75), (-1.7, -4.0, 1.6), (0.8, -3.6, 1.0), (2.0, 2.95, 0.6),
            (4.5, 1.95, 0.5), (-2.35, 3.55, 0.5), (3.25, 3.05, 0.5), (-4.45, -1.55, 0.45), (C.x, C.y, 3.05)]
    k = 0
    while len(pebbles) < 18:
        k += 1
        a, d = rng.uniform(0, TAU), rng.uniform(3.2, 4.7)
        r = rng.uniform(0.06, 0.11)
        if any(math.hypot(d * math.cos(a) - bx_, d * math.sin(a) - by_) < br for bx_, by_, br in busy):
            continue
        pebbles.append(ball(f'pebble_{k}', r, (d * math.cos(a), d * math.sin(a), r * 0.3), (1.2, 0.9, 0.6),
                            ('#b8684b', '#a2573d', '#d7a27e')[k % 3], 6, 4, rot=(0, 0, rng.uniform(0, 180))))
    join(pebbles, 'pebbles')

    # flat paving from the map toward the cooling station (the heat-relief route)
    for k, (x, y) in enumerate(((0.75, -2.75), (1.25, -2.45), (1.75, -2.72), (2.0, -3.2), (-0.3, -3.25), (-1.1, -3.2),
                                (-2.0, -3.05), (1.95, 0.4), (1.75, 1.2), (1.9, 1.95))):
        cyl(f'paver_{k}', 0.2 + 0.03 * (k % 3), 0.05, (x, y, 0.02), (0, 0, k * 41), PALE if k % 2 else '#e3b796', verts=8,
            bevel=0.02, seg=1)

    # data cable from the satellite mast to the map table
    tube('data_cable', [(ax - 0.3, ay - 0.2, 0.04), (1.45, 2.75, 0.03), (1.0, 2.2, 0.03), (0.75, 2.45, 0.03), G(1.2, 2.02, 0.03),
                        G(1.2, 2.0, 0.3)], 0.03, '#4b3b3a', res=6)

    # tidy: one object per prop (animated parts stay separate)
    group('map_table', 'map_')
    group('satellite_mast', 'sat_arc')
    group('shade_canopy', 'cool_')
    group('bench', 'bench_')
    group('water_cooler', 'cooler_')
    group('misting_fan', 'fan_')
    group('water_drop_sign', 'drop_')
    group('profile_red', 'totem_0', 'totem_bld')
    group('profile_gold', 'totem_1', 'totem_house', 'totem_dash', 'totem_marker')
    group('profile_teal', 'totem_2', 'totem_tree')
    group('landsat_scenes_11', 'scene_')
    group('layer_rack', 'layer_')
    group('thermometer', 'thermo_')
    group('sun_stand', 'sun_')
    group('adobe_wall', 'wall_')
    group('pavers', 'paver_')

    # ------------------------------------------------ hotspots
    hotspot(1, (sx, sy, 4.92))
    hotspot(2, W(0.95, 1.5, 0.7))
    core = [i for i in both if cells[i][0] > -0.1] or both     # the larger group of doubly-marked tiles
    bu = sum(cells[i][0] for i in core) / len(core)
    bv = sum(cells[i][1] for i in core) / len(core)
    hotspot(3, W(bu, bv, 1.1))
    hotspot(4, (gx, gy, 2.72))
    finish('phoenix', mode, cam_loc=(-10.0, -15.0, 9.0), cam_target=(0.0, -0.4, 1.2), lens=50)
