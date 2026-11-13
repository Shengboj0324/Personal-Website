"""iGEM 2024, team LCG-China: "Science, clearly told".

A culture bench on the left (the lab), the project's public face on the right (the wiki
billboard with its sitemap, the ExploreAid proposal stall), a modular plasmid ring between
them, and the gold medal out front.
"""
import math
from contextlib import contextmanager

import kit
from kit import *

PLUM = '#38253d'
VIOLET = '#6b4a8c'
MAGENTA = '#c2569b'
ORANGE = '#f29b4c'
GOLD_PALE = '#ffedb2'
PAPERC = '#f6f1e4'
GLASS = '#d9eef2'
MEADOW = '#cfd9a8'
LILAC = '#b9a7d6'
LINE = '#cfc6da'          # neutral "text line" grey-lilac
STONE = '#eee8f1'         # plinths and podiums

LAB = ((-2.45, 0.85, 0.0), 10, 1.12)       # placement (loc, rz, scale) of each set piece
RING = ((0.1, 2.8, 0.0), -30, 1.0)
WIKI = ((2.9, 1.7, 0.0), -25, 1.0)
STALL = ((2.6, -2.6, 0.0), -24, 1.1)
MEDAL = ((-1.0, -3.3, 0.0), -20, 1.15)
MASCOT = ((-3.2, -2.2, 0.0), -15, 1.12)


# ---------------------------------------------------------------- local helpers
@contextmanager
def group(loc=(0, 0, 0), rz=0.0, rot=None, s=1.0):
    """Everything created inside the block is built in local coordinates, then moved."""
    before = {o.name for o in bpy.context.scene.objects}
    yield
    e = Euler([math.radians(a) for a in (rot or (0, 0, rz))])
    M = Matrix.Translation(loc) @ e.to_matrix().to_4x4() @ Matrix.Scale(s, 4)
    for ob in bpy.context.scene.objects:
        if ob.name not in before:
            ob.matrix_basis = M @ ob.matrix_basis
    bpy.context.view_layer.update()


def begin():
    """Start collecting a prop: returns a marker of the objects that already exist."""
    return {o.name for o in bpy.context.scene.objects}


def end(mark, name, keep=()):
    """Merge everything built since `mark` into one object (except names in `keep`)."""
    obs = [o for o in bpy.context.scene.objects
           if o.name not in mark and o.name not in keep and o.type in ('MESH', 'CURVE', 'FONT')]
    return join(obs, name) if obs else None


def world(placement, p):
    loc, rz, s = placement
    return tuple(Matrix.Translation(loc) @ Matrix.Rotation(math.radians(rz), 4, 'Z') @ Matrix.Scale(s, 4) @ Vector(p))


def wire(name, points, r, m, res=4, sides=2):
    """Kit tube with a lighter cross-section, for thin cables and connectors."""
    ob = tube(name, points, r, m, res=res)
    ob.data.bevel_resolution = sides
    return ob


def freeze(ob):
    """Apply rotation and scale so the object's axes match the world (clean pivots)."""
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return ob


def rod(name, p0, p1, r, m, verts=10, bevel=0.0):
    """Straight cylinder between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    v = p1 - p0
    ob = cyl(name, r, v.length, (p0 + p1) / 2, m=m, verts=verts, bevel=bevel)
    ob.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    return ob


def rrect(w, h, r, n=4):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def plate(name, w, h, d, loc, m, r=0.06, n=4, bevel=0.012):
    """Rounded-rectangle plate facing -Y: w along X, h along Z, d thick, centred on loc."""
    x, y, z = loc
    r = min(r, w / 2 - 0.004, h / 2 - 0.004)
    return prism(name, rrect(w, h, r, n), d, (x, y + d / 2, z), (90, 0, 0), m, bevel=bevel, seg=2)


def arc_tube(name, R, r, a0, a1, m, n=14, ring=12):
    """Thick tube along an arc in the XZ plane (centre at the origin), angles in degrees."""
    bm = bmesh.new()
    loops = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        c = Vector((math.cos(a), 0, math.sin(a)))
        loops.append([bm.verts.new(c * (R + r * math.cos(TAU * j / ring)) +
                                   Vector((0, r * math.sin(TAU * j / ring), 0))) for j in range(ring)])
    for A, B in zip(loops, loops[1:]):
        for j in range(ring):
            k = (j + 1) % ring
            bm.faces.new((A[j], A[k], B[k], B[j]))
    bm.faces.new(loops[0])
    bm.faces.new(list(reversed(loops[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = kit._obj_from_bmesh(bm, name)
    return kit._finish(ob, name, m, angle=50)


def sheet(name, fn, nu, nv, m, thickness=0.035):
    """Soft sheet from a parametric surface fn(u, v) -> (x, y, z), u and v in 0..1."""
    bm = bmesh.new()
    grid = [[bm.verts.new(fn(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = kit._obj_from_bmesh(bm, name)
    mod = ob.modifiers.new('solid', 'SOLIDIFY')
    mod.thickness = thickness
    mod.offset = 0
    return kit._finish(ob, name, m, angle=60)


# ---------------------------------------------------------------- lab glassware
def flask(name, loc, s, liquid, glass, fill=0.5, glow=0.0):
    """Erlenmeyer flask; the liquid is a band hugging the cone (no real transparency)."""
    x, y, z = loc
    mark = begin()
    R0, Rn, hc, hn, z1 = 0.2 * s, 0.065 * s, 0.34 * s, 0.5 * s, 0.03 * s
    lathe(name + '_glass', [(0, 0), (R0 - 0.02 * s, 0), (R0, z1), (Rn, hc), (Rn, hn - 0.03 * s),
                            (Rn + 0.022 * s, hn - 0.01 * s), (Rn + 0.022 * s, hn), (0, hn)],
          (x, y, z), m=glass, verts=20)
    zt = z1 + fill * (hc - z1)
    rt = R0 + (Rn - R0) * (zt - z1) / (hc - z1)
    lm = mat(liquid, 0.3, emit=glow, emit_color=liquid) if glow else mat(liquid, 0.3)
    lq = lathe(name + '_liquid', [(R0 - 0.014 * s, 0.006), (R0 + 0.007, z1), (rt + 0.007, zt)],
               (x, y, z), m=lm, verts=20)
    cyl(name + '_plug', Rn * 0.95, 0.07 * s, (x, y, z + hn + 0.02 * s), m=PAPERC, verts=12, bevel=0.015)
    end(mark, name, keep=(lq.name,) if glow else ())
    return lq


def petri(name, loc, glass, colonies=0, seed=0):
    x, y, z = loc
    cyl(name, 0.17, 0.05, (x, y, z + 0.025), m=glass, verts=20, bevel=0.012, seg=1)
    if colonies:
        cyl(name + '_agar', 0.148, 0.014, (x, y, z + 0.052), m=GOLD_PALE, verts=20, bevel=0)
        rng = random.Random(seed)
        for i in range(colonies):
            a, d = rng.uniform(0, TAU), 0.118 * math.sqrt(rng.uniform(0.02, 1))
            cyl(f'{name}_col_{i}', rng.uniform(0.016, 0.028), 0.03, (x + d * math.cos(a), y + d * math.sin(a), z + 0.056),
                m=(WHITE, MAGENTA, ORANGE)[i % 3], verts=6, bevel=0)


def stool(name, loc, seat):
    x, y, z = loc
    mark = begin()
    cyl(name + '_base', 0.19, 0.05, (x, y, z + 0.025), m=PLUM, verts=16, bevel=0.015, seg=1)
    cyl(name + '_post', 0.04, 0.46, (x, y, z + 0.27), m=STEEL_DARK, verts=10, bevel=0)
    torus(name + '_ring', 0.15, 0.022, (x, y, z + 0.24), m=STEEL_DARK, seg=18, ring=6)
    cyl(name + '_seat', 0.22, 0.1, (x, y, z + 0.54), m=seat, verts=20, bevel=0.04, seg=2)
    end(mark, name)


def crate(name, size, loc, rz, c='#e3c9a2', trim='#c9a67b'):
    x, y, z = loc
    mark = begin()
    with group(loc=(x, y, z), rz=rz):
        box(name, (size, size, size), (0, 0, size / 2), m=c, bevel=0.035, seg=2)
        for k, dz in enumerate((0.26, 0.74)):
            box(f'{name}_slat_{k}', (size + 0.03, size + 0.03, size * 0.13), (0, 0, size * dz), m=trim, bevel=0.015, seg=2)
    end(mark, name)


# ---------------------------------------------------------------- 1. culture station
def culture_station(glass, pell):
    FL = 0.055                                   # top of the lab floor tiles
    mark = begin()
    for i in range(4):
        for j in range(3):
            box(f'lab_tile_{i}{j}', (0.69, 0.69, 0.06), (-1.08 + i * 0.72, -1.12 + j * 0.72, 0.025),
                m='#e7f1f2' if (i + j) % 2 else '#d2e4e8', bevel=0.02, seg=2)
    end(mark, 'lab_floor')
    mark = begin()
    box('bench_kick', (2.3, 0.86, 0.1), (0, 0.05, FL + 0.05), m=PLUM, bevel=0.02, seg=2)
    box('bench_body', (2.44, 1.0, 0.68), (0, 0.03, FL + 0.44), m='#efe9f3', bevel=0.05)
    box('bench_top', (2.66, 1.18, 0.1), (0, 0, FL + 0.83), m='#4b3552', bevel=0.04)
    T = FL + 0.88                                # bench surface
    for k, sx in enumerate((-0.6, 0.6)):         # back panels and vent slots
        box(f'bench_backpanel_{k}', (1.04, 0.05, 0.52), (sx, 0.545, FL + 0.44), m=LILAC, bevel=0.03, seg=2)
        for j in range(3):
            box(f'bench_vent_{k}{j}', (0.5, 0.04, 0.045), (sx, 0.565, FL + 0.56 - 0.1 * j), m=VIOLET, bevel=0.012, seg=1)
    for k, sx in enumerate((-0.6, 0.6)):
        box(f'bench_drawer_{k}', (1.04, 0.05, 0.2), (sx, -0.485, FL + 0.62), m=LILAC, bevel=0.03, seg=2)
        box(f'bench_door_{k}', (1.04, 0.05, 0.34), (sx, -0.485, FL + 0.31), m=LILAC, bevel=0.03, seg=2)
        sphere(f'bench_knob_{k}', 0.045, (sx, -0.52, FL + 0.62), m=ORANGE, seg=10)
        box(f'bench_pull_{k}', (0.05, 0.045, 0.16), (sx * 0.3, -0.52, FL + 0.33), m=ORANGE, bevel=0.02, seg=2)

    end(mark, 'bench')

    # shallow tray with culture medium
    mark = begin()
    tx, ty = -0.2, -0.08
    tray = mat('#bfe0e8', 0.25, coat=0.5)
    box('tray_base', (1.04, 0.64, 0.04), (tx, ty, T + 0.02), m=tray, bevel=0.015, seg=2)
    for k, s in enumerate((-1, 1)):
        box(f'tray_long_{k}', (1.08, 0.05, 0.15), (tx, ty + s * 0.3, T + 0.075), m=tray, bevel=0.02, seg=2)
        box(f'tray_short_{k}', (0.05, 0.6, 0.15), (tx + s * 0.515, ty, T + 0.075), m=tray, bevel=0.02, seg=2)
    box('tray_medium', (0.98, 0.55, 0.07), (tx, ty, T + 0.075), m=mat('#f3c489', 0.22), bevel=0.0)
    z0 = T + 0.122
    end(mark, 'culture_tray')

    # the cellulose pellicle: floating on the medium, one end lifted out by tweezers
    def pel(u, v):
        if u < 0.55:
            t = 0.0
            x, z = -0.43 + (u / 0.55) * 0.53, 0.0
        else:
            t = (u - 0.55) / 0.45
            x, z = 0.10 + 0.24 * math.sin(t * math.pi / 2), 0.6 * (1 - math.cos(t * math.pi / 2))
        wy = 0.46 * (1 - 0.52 * t ** 1.4)
        x += 0.045 * math.sin(v * math.pi * 3) * t * (1 - t) * 2.4
        return (tx + x, ty + (v - 0.5) * wy, z0 + z)
    sheet('pellicle', pel, 20, 6, pell, 0.036)
    gx, gz = tx + 0.34, z0 + 0.6                  # where the tweezers grip
    mark = begin()
    for k, s in enumerate((-1, 1)):
        box(f'tweezer_{k}', (0.034, 0.08, 0.44), (gx + s * 0.042, ty, gz + 0.17), (0, s * 6, 0), STEEL, bevel=0.012, seg=2)
    box('tweezer_head', (0.16, 0.1, 0.09), (gx, ty, gz + 0.41), m=MAGENTA, bevel=0.03, seg=2)
    ry = ty + 0.5
    rod('clamp_arm', (gx, ty - 0.04, gz + 0.41), (gx, ry + 0.06, gz + 0.41), 0.03, STEEL)
    cyl('clamp_rod', 0.035, gz + 0.52 - T, (gx, ry, (gz + 0.52 + T) / 2), m=STEEL, verts=10, bevel=0)
    box('clamp_boss', (0.11, 0.11, 0.11), (gx, ry, gz + 0.41), m=PLUM, bevel=0.03, seg=2)
    box('clamp_base', (0.36, 0.26, 0.05), (gx, ry, T + 0.025), m=STEEL, bevel=0.02, seg=2)
    end(mark, 'clamp_stand')

    # three flasks (one glows) and the petri dishes
    lq = flask('flask_a', (0.80, -0.26, T), 1.15, ORANGE, glass, 0.52, glow=2.2)
    flask('flask_b', (1.03, 0.2, T), 0.95, MAGENTA, glass, 0.42)
    flask('flask_c', (0.58, 0.28, T), 0.8, VIOLET, glass, 0.6)
    mark = begin()
    for i in range(3):
        petri(f'petri_{i}', (-1.03 + 0.012 * (i % 2), -0.27 + 0.01 * i, T + 0.052 * i), glass,
              colonies=10 if i == 2 else 0, seed=4)
    end(mark, 'petri_stack')
    mark = begin()
    petri('petri_open', (-1.0, 0.18, T), glass, colonies=12, seed=9)
    end(mark, 'petri_open')

    # gooseneck lamp over the tray
    lx, ly = -0.8, 0.47
    mark = begin()
    cyl('lamp_base', 0.11, 0.05, (lx, ly, T + 0.025), m=MAGENTA, verts=16, bevel=0.015, seg=1)
    wire('lamp_neck', [(lx, ly, T + 0.05), (lx, ly, T + 0.55), (lx + 0.03, ly - 0.06, T + 0.86),
                       (lx + 0.17, ly - 0.22, T + 0.95), (lx + 0.3, ly - 0.36, T + 0.9)], 0.028, STEEL, res=6)
    with group(loc=(lx + 0.32, ly - 0.38, T + 0.88), rot=(24, -22, 0)):
        lathe('lamp_shade', [(0, 0.07), (0.05, 0.07), (0.075, 0.03), (0.2, -0.15), (0.17, -0.15), (0.05, -0.01), (0, -0.01)],
              m=MAGENTA, verts=20)
        sphere('lamp_bulb', 0.085, (0, 0, -0.09), m=mat('#fff3c4', 0.3, emit=5.0, emit_color='#ffd98a'), seg=12)
    end(mark, 'bench_lamp', keep=('lamp_bulb',))

    # stools, crates, bin
    stool('stool_a', (-0.35, -1.02, FL), ORANGE)
    stool('stool_b', (0.72, -1.2, FL), MAGENTA)
    return lq, (gx, ty, gz + 0.72)


# ---------------------------------------------------------------- 2. plasmid sculpture
def plasmid():
    R, r = 1.08, 0.17
    mark = begin()
    lathe('plinth', [(0, 0), (0.96, 0), (0.96, 0.12), (0.82, 0.2), (0.82, 0.42), (0.88, 0.5), (0, 0.5)], m=STONE, verts=36)
    torus('plinth_band', 0.83, 0.025, (0, 0, 0.31), m=VIOLET, seg=36, ring=6)
    end(mark, 'plinth')
    parts = [cyl('pl_turntable', 0.6, 0.12, (0, 0, 0.56), m=PLUM, verts=28, bevel=0.03, seg=2),
             box('pl_saddle', (0.74, 0.46, 0.3), (0, 0, 0.77), m=STONE, bevel=0.06)]
    cz = 0.62 + 0.05 + r + R
    C = Vector((0, 0, cz))
    segs = [(-140, -40, PLUM, 0.0), (-40, 30, ORANGE, 0.0), (30, 95, MAGENTA, 0.3),
            (95, 150, '#ffd98a', 0.0), (150, 220, VIOLET, 0.0)]
    gap = 2.6

    def on_ring(a_deg, rad=R):
        a = math.radians(a_deg)
        return Vector((rad * math.cos(a), 0, rad * math.sin(a)))

    offs = []
    for i, (a0, a1, c, pull) in enumerate(segs):
        d = on_ring((a0 + a1) / 2, pull) + C
        offs.append(d)
        seg = arc_tube(f'pl_seg_{i}', R, r, a0 + gap, a1 - gap, c)
        seg.location = d
        parts.append(seg)
        for k, a in enumerate((a0 + gap + 2.4, a1 - gap - 2.4)):          # connector collars
            parts.append(cyl(f'pl_collar_{i}{k}', r + 0.04, 0.1, on_ring(a) + d, (0, -a, 0), PAPERC, verts=16, bevel=0.02, seg=1))
        n_rung = max(2, round((a1 - a0) / 16))                             # base-pair teeth
        for k in range(n_rung):
            a = a0 + (a1 - a0) * (k + 0.5) / n_rung
            parts.append(rod(f'pl_rung_{i}{k}', on_ring(a, R - r + 0.03) + d, on_ring(a, R - r - 0.15) + d, 0.04, PAPERC, 8))
    for i, (a0, a1, c, pull) in enumerate(segs):                           # joints
        j = (i + 1) % len(segs)
        if pull == 0 and segs[j][3] == 0:
            parts.append(cyl(f'pl_peg_{i}', 0.085, 0.2, on_ring(a1) + C, (0, -a1, 0), '#8d6fb0', verts=12, bevel=0))
        else:                                                              # slide-out rail
            parts.append(rod(f'pl_rail_{i}', on_ring(a1 - gap - 1.5) + offs[i], on_ring(a1 + gap + 1.5) + offs[j], 0.05, STEEL, 10))
    ring = join(parts, 'plasmid')
    set_origin(ring, (0, 0, 0.5))
    return cz + R + r


def spare_module():
    """One spare module resting on its connector ends by the plinth: the ring can be re-assembled."""
    R, r = 1.08, 0.17
    mark = begin()
    zc = -R * math.sin(math.radians(52)) + 0.1
    arc_tube('spare_seg', R, r, 52, 128, '#8fd3de', n=10).location = (0, 0, zc)
    for k, a in enumerate((54.5, 125.5)):
        ar = math.radians(a)
        cyl(f'spare_collar_{k}', r + 0.04, 0.1, (R * math.cos(ar), 0, zc + R * math.sin(ar)), (0, -a, 0), PAPERC, verts=16, bevel=0.02, seg=1)
    for k in range(4):
        ar = math.radians(52 + 76 * (k + 0.5) / 4)
        rod(f'spare_rung_{k}', (math.cos(ar) * (R - r + 0.03), 0, zc + math.sin(ar) * (R - r + 0.03)),
            (math.cos(ar) * (R - r - 0.13), 0, zc + math.sin(ar) * (R - r - 0.13)), 0.04, PAPERC, 8)
    end(mark, 'spare_module')


# ---------------------------------------------------------------- 3. bacterium mascot
def bacterium():
    mark = begin()
    lathe('bac_ped', [(0, 0), (0.54, 0), (0.54, 0.1), (0.43, 0.17), (0.43, 0.3), (0, 0.3)], m=STONE, verts=28)
    torus('bac_ped_band', 0.435, 0.025, (0, 0, 0.24), m=MAGENTA, seg=28, ring=6)
    cyl('bac_rod', 0.045, 0.52, (0.02, 0, 0.56), m=STEEL_DARK, verts=10, bevel=0)
    end(mark, 'mascot_pedestal')
    with group(loc=(0, 0, 1.04), rot=(0, -30, 0)):
        r, hl = 0.27, 0.23
        mark = begin()
        prof = [(0, -0.5)] + [(r * math.cos(math.radians(a)), -hl + r * math.sin(math.radians(a))) for a in range(-75, 1, 15)]
        prof += [(r * math.cos(math.radians(a)), hl + r * math.sin(math.radians(a))) for a in range(0, 76, 15)] + [(0, 0.5)]
        lathe('bac_body', prof, rot=(0, 90, 0), m=ORANGE, verts=24)
        for k, sz in enumerate((-0.115, 0.115)):
            sphere(f'bac_eye_{k}', 0.066, (0.2, -0.243, sz), (1, 0.55, 1), WHITE, 12)
            sphere(f'bac_pupil_{k}', 0.036, (0.195, -0.275, sz * 0.96), (1, 0.6, 1), PLUM, 10)
            sphere(f'bac_cheek_{k}', 0.046, (0.085, -0.228, sz * 1.42), (1, 0.4, 1), MAGENTA, 10)
        wire('bac_smile', [(0.085, -0.262, -0.07), (0.035, -0.272, -0.045), (0.015, -0.276, 0), (0.035, -0.272, 0.045),
                           (0.085, -0.262, 0.07)], 0.019, PLUM, res=4, sides=2)
        end(mark, 'bacterium')
        tail = Vector((-0.46, 0, 0))
        fl = []
        for k, (ay, az, ph) in enumerate(((0.0, 0.1, 0.0), (0.32, -0.2, 2.1), (-0.3, -0.16, 4.0))):
            d = Vector((-1, ay, az)).normalized()
            w = d.cross(Vector((0.3, 1, 0.2)) if k else Vector((0, 1, 0))).normalized()
            pts = []
            for i in range(9):
                s = i / 8
                pts.append(tuple(tail + d * (0.72 * s) + w * (0.075 * math.sin(TAU * 1.5 * s + ph) * min(1, s * 3))))
            fl.append(wire(f'bac_flag_{k}', pts, 0.034, VIOLET, res=4, sides=2))
        f = join(fl, 'flagella')
        set_origin(f, tuple(tail))


# ---------------------------------------------------------------- 4. the wiki
def page_card(name, loc, accent, tilt=-25):
    x, y, z = loc
    mark = begin()
    with group(loc=loc, rot=(tilt, 0, 0)):
        plate(name, 0.7, 0.5, 0.07, (0, 0, 0), PAPERC, r=0.07, n=3)
        plate(name + '_head', 0.56, 0.11, 0.03, (0, -0.045, 0.13), accent, r=0.035, n=2, bevel=0.008)
        box(name + '_img', (0.2, 0.03, 0.2), (-0.18, -0.045, -0.07), m=accent, bevel=0.02, seg=1)
        box(name + '_l1', (0.3, 0.03, 0.05), (0.13, -0.045, -0.01), m=LINE, bevel=0.012, seg=1)
        box(name + '_l2', (0.22, 0.03, 0.05), (0.09, -0.045, -0.12), m=LINE, bevel=0.012, seg=1)
    cyl(name + '_post', 0.04, z - 0.04, (x, y + 0.045, (z - 0.04) / 2), m=PLUM, verts=8, bevel=0)
    cyl(name + '_foot', 0.16, 0.05, (x, y + 0.045, 0.035), m=PLUM, verts=14, bevel=0.015, seg=1)
    end(mark, name)
    s, c = math.sin(math.radians(-tilt)), math.cos(math.radians(-tilt))
    return Vector((x, y + 0.25 * s, z + 0.25 * c)), Vector((x, y - 0.25 * s, z - 0.25 * c))   # top, bottom edge


def wiki():
    W, H, zc = 2.9, 2.0, 1.82
    mark = begin()
    for k, s in enumerate((-1, 1)):
        box(f'bb_foot_{k}', (0.46, 0.7, 0.1), (s * 1.0, 0.04, 0.05), m=VIOLET, bevel=0.04)
        box(f'bb_leg_{k}', (0.18, 0.18, 0.84), (s * 1.0, 0.04, 0.5), m=PLUM, bevel=0.04)
    rod('bb_brace', (-1.0, 0.04, 0.42), (1.0, 0.04, 0.42), 0.04, PLUM)
    plate('bb_frame', W, H, 0.22, (0, 0, zc), PLUM, r=0.2, n=6, bevel=0.03)
    plate('bb_page', W - 0.26, H - 0.56, 0.04, (0, -0.12, zc - 0.15), PAPERC, r=0.07)
    zt = zc + H / 2 - 0.225                        # title bar centre
    for k, c in enumerate((ORANGE, '#ffd97a', MAGENTA)):                   # the three dots
        sphere(f'bb_dot_{k}', 0.066, (-1.2 + 0.2 * k, -0.115, zt), (1, 0.5, 1), mat(c, 0.4, emit=1.2), 12)
    plate('bb_address', 1.5, 0.16, 0.04, (0.32, -0.115, zt), '#cdbfe6', r=0.08)
    y1 = -0.15                                     # blocks standing proud of the page
    zp = zc - 0.15
    sphere('bb_logo', 0.07, (-1.12, -0.14, zp + 0.59), (1, 0.45, 1), MAGENTA, 12)
    for k in range(3):
        plate(f'bb_nav_{k}', 0.26, 0.07, 0.03, (0.48 + 0.31 * k, y1, zp + 0.59), LILAC, r=0.035, n=3)
    # hero image tile: sun over two hills (the universal "picture" glyph)
    plate('bb_hero', 1.3, 0.8, 0.05, (-0.58, y1, zp + 0.05), '#cdbfe6', r=0.07)
    sphere('bb_sun', 0.11, (-0.2, y1 - 0.03, zp + 0.25), (1, 0.4, 1), mat(GOLD_PALE, 0.4, emit=1.5), 14)
    prism('bb_hill_a', [(-0.56, 0), (0.2, 0), (-0.22, 0.44)], 0.04, (-0.62, y1 - 0.02, zp - 0.33), (90, 0, 0), VIOLET, bevel=0.03, seg=2)
    prism('bb_hill_b', [(-0.3, 0), (0.42, 0), (0.1, 0.3)], 0.05, (-0.42, y1 - 0.025, zp - 0.33), (90, 0, 0), MAGENTA, bevel=0.03, seg=2)
    plate('bb_heading', 0.8, 0.12, 0.03, (0.67, y1, zp + 0.36), PLUM, r=0.04, n=3)
    for k, ln in enumerate((0.85, 0.85, 0.62)):
        plate(f'bb_line_{k}', ln, 0.06, 0.03, (0.27 + ln / 2, y1, zp + 0.19 - 0.12 * k), LINE, r=0.03, n=3)
    plate('bb_button', 0.5, 0.17, 0.05, (0.52, y1 - 0.005, zp - 0.24), mat(ORANGE, 0.4, emit=1.6), r=0.08)
    plate('bb_scroll', 0.05, 0.5, 0.03, (1.25, y1, zp + 0.2), LINE, r=0.02, n=3)
    # three image tiles carrying the lab's subjects as icons: ring, cell, cross
    for k, c in enumerate(('#c4e4ea', GOLD_PALE, '#ecc9df')):
        plate(f'bb_tile_{k}', 0.78, 0.3, 0.04, (-0.86 + 0.86 * k, y1, zp - 0.555), c, r=0.06)
    torus('bb_icon_ring', 0.08, 0.03, (-0.86, y1 - 0.035, zp - 0.555), (90, 0, 0), VIOLET, seg=18, ring=6)
    box('bb_icon_cell', (0.24, 0.05, 0.1), (0.0, y1 - 0.03, zp - 0.555), (0, -18, 0), ORANGE, bevel=0.045, seg=3)
    box('bb_icon_cross_h', (0.19, 0.05, 0.065), (0.86, y1 - 0.03, zp - 0.555), m=MAGENTA, bevel=0.015, seg=2)
    box('bb_icon_cross_v', (0.065, 0.05, 0.19), (0.86, y1 - 0.031, zp - 0.555), m=MAGENTA, bevel=0.015, seg=2)
    # back of the billboard
    box('bb_back', (2.46, 0.05, 1.56), (0, 0.125, zc), m='#a48bcc', bevel=0.02, seg=2)
    for k, dz in enumerate((-0.62, 0.62)):
        box(f'bb_rib_{k}', (2.56, 0.07, 0.1), (0, 0.17, zc + dz), m=VIOLET, bevel=0.02, seg=2)
    box('bb_junction', (0.42, 0.12, 0.32), (0.85, 0.2, zc - 0.1), m=PLUM, bevel=0.03, seg=2)
    sphere('bb_junction_led', 0.04, (0.95, 0.27, zc - 0.02), m=mat(ORANGE, 0.4, emit=3), seg=8)
    for k, (dx, dz, rz, c) in enumerate(((-0.75, 0.08, 4, MAGENTA), (-0.2, -0.05, -5, ORANGE), (0.3, 0.12, 3, VIOLET))):
        box(f'bb_draft_{k}', (0.42, 0.03, 0.54), (dx, 0.165, zc + dz), (0, rz, 0), PAPERC, bevel=0.012, seg=1)   # pinned drafts
        box(f'bb_draft_head_{k}', (0.3, 0.03, 0.07), (dx, 0.178, zc + dz + 0.17), (0, rz, 0), c, bevel=0.01, seg=1)
        box(f'bb_draft_line_{k}', (0.3, 0.03, 0.04), (dx, 0.178, zc + dz + 0.03), (0, rz, 0), LINE, bevel=0.01, seg=1)
        box(f'bb_draft_line2_{k}', (0.2, 0.03, 0.04), (dx - 0.04, 0.178, zc + dz - 0.08), (0, rz, 0), LINE, bevel=0.01, seg=1)
    end(mark, 'billboard')
    # cursor hovering over the button
    arrow = [(0, 0), (0, -0.5), (0.12, -0.38), (0.2, -0.56), (0.28, -0.52), (0.2, -0.34), (0.36, -0.34)]
    big = [((x - 0.13) * 1.26 + 0.13, (y + 0.31) * 1.2 - 0.31) for x, y in arrow]
    cur = join([prism('cursor_face', arrow, 0.06, (0.72, -0.36, zp - 0.2), (90, 0, 0), WHITE, bevel=0.012, seg=2),
                prism('cursor_edge', big, 0.05, (0.72, -0.335, zp - 0.2), (90, 0, 0), PLUM, bevel=0.012, seg=2)], 'cursor')
    set_origin(cur, (0.85, -0.37, zp - 0.45))

    # sitemap: 1 home page, 3 sections, 2 sub-pages, linked by tubes
    top0, bot0 = page_card('page_home', (0, -1.25, 1.12), PLUM)
    kids = [page_card(f'page_sec_{k}', (x, y, 0.7), c)
            for k, (x, y, c) in enumerate(((-1.12, -2.0, MAGENTA), (0, -2.12, ORANGE), (1.12, -2.0, VIOLET)))]
    leaves = [page_card(f'page_leaf_{k}', (x, -2.92, 0.36), LILAC) for k, x in enumerate((-0.5, 0.5))]
    link = mat(ORANGE, 0.5)
    mark = begin()
    sphere('link_hub_0', 0.07, bot0, m=link, seg=10)
    for k, (t, b) in enumerate(kids):
        rod(f'link_a_{k}', bot0, t, 0.034, link, 8)
        sphere(f'link_end_a_{k}', 0.055, t, m=link, seg=8)
    sphere('link_hub_1', 0.065, kids[1][1], m=link, seg=10)
    for k, (t, b) in enumerate(leaves):
        rod(f'link_b_{k}', kids[1][1], t, 0.034, link, 8)
        sphere(f'link_end_b_{k}', 0.055, t, m=link, seg=8)
    end(mark, 'sitemap_links')
    return zc + H / 2


# ---------------------------------------------------------------- 5. ExploreAid stall
def explore_stall(pell):
    TT = 0.76
    mark = begin()
    box('st_top', (1.78, 0.98, 0.08), (0, 0, TT - 0.04), m='#ead9bd', bevel=0.03)
    box('st_cloth', (1.6, 0.05, 0.42), (0, -0.44, TT - 0.29), m=LILAC, bevel=0.02, seg=2)
    for k, s in enumerate((-1, 1)):
        box(f'st_side_{k}', (0.05, 0.8, 0.42), (s * 0.82, 0, TT - 0.29), m=LILAC, bevel=0.02, seg=2)
    for i, (sx, sy) in enumerate(((-0.82, -0.42), (0.82, -0.42), (-0.82, 0.42), (0.82, 0.42))):
        h = 1.74 if sy < 0 else 2.02
        cyl(f'st_post_{i}', 0.045, h, (sx, sy, h / 2), m=PLUM, verts=10, bevel=0)
    rod('st_beam_back', (-0.9, 0.42, 2.0), (0.9, 0.42, 2.0), 0.04, PLUM)
    rod('st_beam_front', (-0.9, -0.42, 1.72), (0.9, -0.42, 1.72), 0.04, PLUM)
    end(mark, 'stall')
    mark = begin()
    for i in range(6):
        x = -0.75 + i * 0.3
        box(f'st_awn_{i}', (0.3, 1.16, 0.05), (x, 0, 1.9), (19, 0, 0), PAPERC if i % 2 else MAGENTA, bevel=0.02, seg=2)
        box(f'st_val_{i}', (0.3, 0.05, 0.17), (x, -0.555, 1.645), m=MAGENTA if i % 2 else PAPERC, bevel=0.035, seg=2)
    end(mark, 'stall_awning')
    # first-aid cross sign above the stall
    mark = begin()
    cyl('st_mast', 0.04, 0.4, (0, 0.44, 2.18), m=PLUM, verts=10, bevel=0)
    cyl('st_sign', 0.31, 0.1, (0, 0.44, 2.66), (90, 0, 0), PAPERC, verts=28, bevel=0.02, seg=1)
    torus('st_sign_rim', 0.31, 0.04, (0, 0.44, 2.66), (90, 0, 0), PLUM, seg=28, ring=8)
    box('st_cross_h', (0.38, 0.16, 0.125), (0, 0.44, 2.66), m=ORANGE, bevel=0.02, seg=2)
    box('st_cross_v', (0.125, 0.162, 0.38), (0, 0.44, 2.66), m=ORANGE, bevel=0.02, seg=2)
    end(mark, 'stall_cross_sign')
    # sheet samples on a display board
    mark = begin()
    box('st_board', (1.0, 0.46, 0.04), (-0.33, -0.17, TT + 0.02), m=PLUM, bevel=0.015, seg=2)
    for i, (dx, rz) in enumerate(((-0.31, -6), (0.0, 4), (0.31, 9))):
        box(f'st_sample_{i}', (0.26, 0.33, 0.036), (-0.33 + dx, -0.17, TT + 0.058), (0, 0, rz), pell, bevel=0.014, seg=2)
    end(mark, 'stall_samples')
    # one roll of bandage, its tail running off the table edge
    mark = begin()
    roll_m = mat('#f8f1de', 0.55, sheen=0.4)
    cyl('st_roll', 0.165, 0.26, (0.48, 0.07, TT + 0.2), (0, 90, 0), roll_m, verts=24, bevel=0.03)
    cyl('st_roll_core', 0.06, 0.28, (0.48, 0.07, TT + 0.2), (0, 90, 0), ORANGE, verts=12, bevel=0.01, seg=2)

    def tail(u, v):
        x = 0.37 + 0.22 * v
        if u < 0.6:
            return (x, 0.07 - (u / 0.6) * 0.53, TT + 0.019)
        t = (u - 0.6) / 0.4
        if t < 0.45:
            a = (t / 0.45) * math.pi / 2
            return (x, -0.46 - 0.07 * math.sin(a), TT + 0.019 - 0.07 * (1 - math.cos(a)))
        return (x, -0.53, TT - 0.051 - (t - 0.45) / 0.55 * 0.26)
    sheet('st_roll_tail', tail, 18, 2, roll_m, 0.034)
    end(mark, 'bandage_roll')
    # clipboard: the business plan (a proposal, so only abstract lines)
    mark = begin()
    with group(loc=(-0.42, 0.3, TT + 0.205), rot=(-22, 0, 0)):
        plate('st_clip_board', 0.36, 0.44, 0.04, (0, 0, 0), '#c9a37a', r=0.04)
        plate('st_clip_paper', 0.3, 0.36, 0.02, (0, -0.03, -0.02), PAPERC, r=0.02, n=2)
        box('st_clip_clip', (0.14, 0.05, 0.05), (0, -0.035, 0.19), m=STEEL_DARK, bevel=0.015, seg=2)
        for k, ln in enumerate((0.22, 0.22, 0.14)):
            box(f'st_clip_l{k}', (ln, 0.03, 0.035), (-0.11 + ln / 2, -0.04, 0.08 - 0.075 * k), m=LINE, bevel=0.01, seg=2)
        sphere('st_clip_dot', 0.035, (0.08, -0.04, -0.1), (1, 0.5, 1), ORANGE, 10)
    rod('st_clip_prop', (-0.42, 0.34, TT + 0.3), (-0.42, 0.46, TT), 0.025, STEEL_DARK, 8)
    end(mark, 'stall_clipboard')
    mark = begin()
    lathe('st_pot', [(0, 0), (0.075, 0), (0.1, 0.13), (0, 0.13)], (0.5, 0.36, TT), m=VIOLET, verts=14)
    flower('st_pot_flower', (0.5, 0.36, TT + 0.1), 0.2, LILAC, GOLD_PALE)
    end(mark, 'stall_flower_pot')


# ---------------------------------------------------------------- 6. gold medal
def medal_stand():
    gold = mat('#f7c443', 0.4, metallic=0.2)
    gold_d = mat('#e3a530', 0.42, metallic=0.2)
    mark = begin()
    cyl('md_base', 0.64, 0.16, (0, 0, 0.08), m=STONE, verts=28, bevel=0.04, seg=2)
    cyl('md_step', 0.46, 0.16, (0, 0, 0.24), m=LILAC, verts=28, bevel=0.04, seg=2)
    for k, s in enumerate((-1, 1)):
        cyl(f'md_post_{k}', 0.04, 1.3, (s * 0.42, 0, 0.97), m=PLUM, verts=10, bevel=0)
        sphere(f'md_finial_{k}', 0.07, (s * 0.42, 0, 1.67), m=gold, seg=12)
    zb = 1.56
    rod('md_bar', (-0.5, 0, zb), (0.5, 0, zb), 0.04, PLUM)
    end(mark, 'medal_stand')
    zm = 0.8
    star = []
    for k in range(10):
        a = math.radians(90 + 36 * k)
        rr = 0.19 if k % 2 == 0 else 0.085
        star.append((rr * math.cos(a), rr * math.sin(a)))
    parts = [cyl('md_disc', 0.34, 0.08, (0, 0, zm), (90, 0, 0), gold, verts=32, bevel=0.02),
             torus('md_rim', 0.33, 0.04, (0, 0, zm), (90, 0, 0), gold_d, seg=32, ring=8),
             prism('md_star', star, 0.14, (0, 0.07, zm), (90, 0, 0), mat('#ffe394', 0.35, metallic=0.1), bevel=0.012, seg=2),
             torus('md_loop', 0.06, 0.024, (0, 0, zm + 0.39), (90, 0, 0), gold_d, seg=14, ring=6)]
    L = math.hypot(0.17, zb - (zm + 0.42))
    ang = math.degrees(math.atan2(0.17, zb - (zm + 0.42)))
    for k, (s, c) in enumerate(((-1, MAGENTA), (1, VIOLET))):
        parts.append(box(f'md_ribbon_{k}', (0.13, 0.04, L + 0.06), (s * 0.085, 0, (zb + zm + 0.42) / 2), (0, s * ang, 0), c, bevel=0.015, seg=2))
        parts.append(box(f'md_wrap_{k}', (0.14, 0.12, 0.12), (s * 0.17, 0, zb), m=c, bevel=0.035, seg=2))
    m = join(parts, 'medal')
    set_origin(m, (0, 0, zb))


# ---------------------------------------------------------------- island
def build(mode='preview'):
    reset()
    setup_world()
    base, radius_at = island_base(R=5.05, seed=280, top=MEADOW, lip='#b9c88f', soil='#d9bba2', soil2='#a98aa6',
                                  rock_c='#a39fb0', lobes=((2, 0.05), (3, 0.035), (4, 0.02)))

    def on_top(tag, x, y, margin=0.0):
        """Warn when a ground prop would sit past the flat top of the island."""
        d, lim = math.hypot(x, y) + margin, 0.9 * radius_at(math.atan2(y, x))
        if d > lim:
            print(f'[kit] WARN {tag} at ({x:.2f}, {y:.2f}) is {d - lim:.2f} past the flat top')
        return (x, y, 0)

    glass = mat(GLASS, 0.2, coat=0.6)
    pell = mat('#f8f0dc', 0.42, emit=0.22, emit_color=GOLD_PALE, coat=0.4, sheen=0.5)

    # plaza under the wiki and its sitemap
    on_top('plaza', 2.42, 0.32, 2.05)
    lathe('plaza', [(0.0, 0.014), (1.9, 0.014), (2.07, -0.02), (2.12, -0.08)], (2.42, 0.32, 0), m='#d6cce6', verts=48)

    with group(LAB[0], rz=LAB[1], s=LAB[2]):
        flask_liquid, hs1 = culture_station(glass, pell)
        hotspot(1, hs1)
    with group(RING[0], rz=RING[1], s=RING[2]):
        ring_top = plasmid()
        hotspot(2, (0, 0, ring_top + 0.3))
    with group(WIKI[0], rz=WIKI[1], s=WIKI[2]):
        bb_top = wiki()
        hotspot(3, (0, -0.1, bb_top + 0.28))
    with group(STALL[0], rz=STALL[1], s=STALL[2]):
        explore_stall(pell)
        hotspot(4, (0, -0.35, 2.15))
    with group(MEDAL[0], rz=MEDAL[1], s=MEDAL[2]):
        medal_stand()
    with group(MASCOT[0], rz=MASCOT[1], s=MASCOT[2]):
        bacterium()
    with group((0.2, -0.3, 0), rz=-35):
        spare_module()

    # movers (frozen so their pivots are world-aligned); hotspots keep position only
    D = bpy.data.objects
    for n in range(1, 5):
        D[f'hs_{n}'].rotation_euler = (0, 0, 0)
        D[f'hs_{n}'].scale = (1, 1, 1)
    animate(freeze(D['plasmid']), 'spin', axis='z', speed=0.3)
    animate(freeze(D['medal']), 'bob', amp=0.03, speed=1.1)
    animate(freeze(D['cursor']), 'bob', amp=0.05, speed=1.5)
    animate(freeze(D['flagella']), 'sway', amp=10, speed=2.0, axis='z')
    animate(freeze(join([flask_liquid], 'flask_glow')), 'pulse', speed=1.1)
    animate(freeze(join([D['lamp_bulb']], 'lamp_glow')), 'pulse', speed=0.7)

    # crates: lab supplies on the left, stall stock on the right
    ca, cb = world(LAB, (-1.72, -0.75, 0)), world(LAB, (-1.76, -0.18, 0))
    crate('crate_a', 0.5, on_top('crate_a', ca[0], ca[1], 0.3), 22)
    crate('crate_b', 0.42, on_top('crate_b', cb[0], cb[1], 0.3), -8)
    crate('crate_c', 0.36, (ca[0], ca[1], 0.5), 48, '#d9b98c', '#bf9a6c')
    cc, cd = world(STALL, (-1.32, 0.12, 0)), world(STALL, (-1.3, -0.42, 0))
    crate('crate_d', 0.46, (cc[0], cc[1], 0), -14, '#d9b98c', '#bf9a6c')
    crate('crate_e', 0.38, (cd[0], cd[1], 0), 12)

    # path: lab -> plaza and billboard, with a spur past the medal to the stall
    for i, (x, y) in enumerate([(-0.62, 0.72), (-0.18, 0.9), (0.28, 0.98), (0.76, 1.06), (1.24, 1.2), (1.7, 1.4),
                                (-0.7, -1.05), (-0.8, -1.65), (-0.9, -2.2), (-0.05, -2.95), (0.5, -2.8), (1.02, -2.62)]):
        cyl(f'stone_{i}', 0.2 + 0.03 * (i % 3), 0.05, (x, y, 0.02), (0, 0, i * 37), '#efe9dc', verts=9, bevel=0.02, seg=1)

    # cables: bench -> billboard (the lab feeds the wiki) and a power box for the turntable
    a, b = world(LAB, (1.2, 0.5, 0)), world(WIKI, (-1.0, 0.3, 0))
    wire('cable_main', [(a[0], a[1], 0.5), (a[0] + 0.06, a[1] + 0.2, 0.3), (a[0] + 0.1, a[1] + 0.34, 0.1), (-0.85, 1.9, 0.09),
                        (-0.45, 1.55, 0.035), (0.1, 1.42, 0.035), (0.7, 1.6, 0.035), (1.25, 1.62, 0.035),
                        (b[0] - 0.35, b[1] - 0.3, 0.035), (b[0], b[1], 0.07)], 0.035, PLUM, res=6, sides=2)
    mark = begin()
    box('power_box', (0.34, 0.26, 0.24), (-1.12, 3.2, 0.12), (0, 0, 20), PLUM, bevel=0.04, seg=2)
    sphere('power_led', 0.04, (-1.17, 3.08, 0.2), m=mat(ORANGE, 0.4, emit=3), seg=8)
    wire('cable_ring', [(-1.0, 3.2, 0.1), (-0.9, 3.36, 0.035), (-0.75, 3.38, 0.035), (-0.66, 3.25, 0.06)], 0.03, PLUM, res=5)
    end(mark, 'power_box')

    # street lamp on the public side
    lpx, lpy = 4.12, 0.3
    on_top('street_lamp', lpx, lpy, 0.15)
    mark = begin()
    cyl('lamp_post_foot', 0.14, 0.08, (lpx, lpy, 0.05), m=PLUM, verts=14, bevel=0.02, seg=1)
    cyl('lamp_post', 0.04, 1.5, (lpx, lpy, 0.8), m=PLUM, verts=10, bevel=0)
    sphere('lamp_post_globe', 0.15, (lpx, lpy, 1.66), (1, 1, 1.1), mat('#fff0c2', 0.3, emit=5.0, emit_color='#ffd98a'), 14)
    lathe('lamp_post_cap', [(0.17, 0), (0.03, 0.11), (0, 0.11)], (lpx, lpy, 1.78), m=PLUM, verts=14)
    end(mark, 'street_lamp')

    # vegetation: lilac-blossom trees, bushes, flowers
    join(tree('tree_a', on_top('tree_a', -2.5, 3.3, 0.2), 2.05, 0.84, leaf='#c3b1e3', leaf2='#a48bcc', seed=3), 'tree_lilac')
    join(tree('tree_b', on_top('tree_b', 2.4, 3.55, 0.2), 1.7, 0.7, leaf='#a9c98b', leaf2='#8bb878', seed=6), 'tree_green')
    for i, (x, y, r) in enumerate([(-1.3, 3.85, 0.34), (1.4, 3.8, 0.3), (3.6, 2.0, 0.28), (-3.35, 2.6, 0.3),
                                   (1.3, -3.85, 0.32), (-2.15, -3.3, 0.28), (4.15, -1.35, 0.26), (0.35, -3.75, 0.24)]):
        mark = begin()
        bush(f'bush_{i}', on_top(f'bush_{i}', x, y, r), r, '#a9c98b' if i % 2 else '#8bb878', seed=i)
        if i % 2 == 0:                                                     # lilac blossom on every other bush
            for k in range(4):
                a = TAU * k / 4 + i
                sphere(f'bush_{i}_bloom_{k}', 0.065, (x + r * 0.5 * math.cos(a), y + r * 0.5 * math.sin(a), r * (1.2 if k % 2 else 1.12)),
                       (1, 1, 0.7), LILAC if k % 2 else '#e3b6d6', 8)
        end(mark, f'bush_{i}')
    for i, (x, y) in enumerate([(-1.75, -1.35), (-2.5, -3.1), (0.5, -1.65), (0.9, -3.4), (1.9, -3.7), (-1.9, -2.5),
                                (-4.25, -2.0), (-0.5, 4.0), (0.7, 4.15), (4.3, 1.5), (3.6, -1.15), (-4.0, 2.2), (-1.6, 2.6),
                                (3.4, 3.0)]):
        join(flower(f'lilac_{i}', on_top(f'lilac_{i}', x, y), 0.24 + 0.04 * (i % 3), LILAC if i % 4 else '#e3b6d6', GOLD_PALE, '#8fae6e'),
             f'lilac_{i}')
    for i, (x, y) in enumerate([(-2.05, -1.75), (0.1, -2.3), (1.0, -4.1), (-3.1, -3.2), (-4.45, 0.95), (0.2, 4.2),
                                (2.9, 3.45), (4.45, -0.6), (-0.3, -4.05), (1.7, -1.5), (-4.3, -1.3)]):
        join(grass_tuft(f'tuft_{i}', on_top(f'tuft_{i}', x, y), m='#a5b97a', seed=i), f'tuft_{i}')
    for i, a in enumerate((205, 318, 262, 12, 132)):
        r = (0.36, 0.3, 0.26, 0.3, 0.3)[i]
        d = radius_at(math.radians(a)) * 0.93
        rock(f'shore_rock_{i}', r, (d * math.cos(math.radians(a)), d * math.sin(math.radians(a)), -0.1),
             '#a39fb0' if i % 2 else '#b9b5c4', seed=i + 20)
    for i, (x, y, r) in enumerate([(-1.05, -1.75, 0.12), (0.85, -2.25, 0.1), (-2.7, -1.25, 0.11), (3.75, 2.75, 0.13)]):
        rock(f'pebble_{i}', r, (x, y, 0.03), '#c9c4d2', seed=i + 40)

    finish('igem', mode, cam_loc=(-9.6, -14.4, 8.5), cam_target=(0.1, -0.3, 0.95), lens=50)
