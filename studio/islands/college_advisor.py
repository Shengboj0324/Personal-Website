"""CollegeAdvisor: an open-air campus library whose answers must pass a cite gate.

Five bookcases (the five collections), a gate that passes cited answers and sets
blank cards aside, a scale that weighs authoritative sources, and a reading desk
whose money figures come off a calculator tape."""
import math
import random

import bmesh
import kit
from kit import *

# palette (from the app theme)
INDIGO = '#6366F1'
DEEP = '#3f3d8f'
LAV = '#dedde7'
VIOLET = '#c8c5d6'
PINK = '#EC4899'
CYAN = '#06B6D4'
PAPERC = '#f9f7f0'
AMBER = '#f5a524'
MINT = '#34c77b'
GOLD = '#e3b04b'
STONE = '#e6e3ee'
STONE_D = '#cbc7da'
WARM = '#c98f5a'
WARM_D = '#9c6a42'
WARM_L = '#ddb07c'
LAWN = '#bfe0a4'
HEDGE = '#6fb57a'
HEDGE_D = '#559d68'


# ---------------------------------------------------------------- local helpers
class Frame:
    """A local ground frame: u = right, v = back (front is -v), w = up, turned by `deg`."""

    def __init__(self, origin, deg=0.0):
        self.o = origin if len(origin) == 3 else (origin[0], origin[1], 0.0)
        self.deg = deg
        a = math.radians(deg)
        self.c, self.s = math.cos(a), math.sin(a)

    def p(self, u=0.0, v=0.0, w=0.0):
        return (self.o[0] + u * self.c - v * self.s, self.o[1] + u * self.s + v * self.c, self.o[2] + w)

    def r(self, rx=0.0, ry=0.0, rz=0.0):
        return (rx, ry, rz + self.deg)


def tilted(centre, deg, a, b, c):
    """Point (a, b, c) of a slab tilted `deg` about its u axis, in frame coordinates."""
    t = math.radians(deg)
    return (centre[0] + a, centre[1] + b * math.cos(t) - c * math.sin(t),
            centre[2] + b * math.sin(t) + c * math.cos(t))


def arc_lathe(name, profile, a0, a1, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, steps=24, bevel=0.03, seg=2):
    """Sweep a closed (radius, z) profile around Z from a0 to a1 degrees, with end caps."""
    bm = bmesh.new()
    rings = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in profile])
    n = len(profile)
    for A, B in zip(rings, rings[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((A[k], A[j], B[j], B[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = kit._obj_from_bmesh(bm, name)
    kit._bevel(ob, bevel, seg)
    place(ob, loc, rot)
    return kit._finish(ob, name, m, angle=40)


def arc_pts(c, r, a0, a1, z, n=10):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))), z) for i in range(n)]


def rod(name, a, b, r=0.02, m=WHITE):
    ob = tube(name, [a, b], r, m, smooth_curve=False)
    ob.data.bevel_resolution = 2
    return ob


def strip(name, f, u0, path, width=0.2, thick=0.03, m=PAPERC, samples=6):
    """Flat tape of `width` (along u) following a smoothed (v, w) path in frame f."""
    pts = []
    n = len(path)
    for i in range(n - 1):
        p0, p1, p2, p3 = path[max(i - 1, 0)], path[i], path[i + 1], path[min(i + 2, n - 1)]
        for k in range(samples):
            t = k / samples
            pts.append(tuple(0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t * t
                                    + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t ** 3) for d in (0, 1)))
    pts.append(path[-1])
    bm = bmesh.new()
    rings = []
    for i, (v, w) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        tv, tw = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tv, tw) or 1.0
        nv, nw = -tw / L * thick / 2, tv / L * thick / 2
        rings.append([bm.verts.new(f.p(u0 + su * width / 2, v + sn * nv, w + sn * nw))
                      for su, sn in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for A, B in zip(rings, rings[1:]):
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new((A[k], A[j], B[j], B[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = kit._obj_from_bmesh(bm, name)
    return kit._finish(ob, name, m, angle=50)


def book(g, name, f, uvw, size=(0.36, 0.26, 0.07), cover=INDIGO, rz=0.0):
    """A closed book lying flat: two boards, a spine and a cream page block."""
    ff = Frame(f.p(*uvw), f.deg + rz)
    sx, sy, sz = size
    g.append(box(name + '_b0', (sx, sy, 0.016), ff.p(0, 0, 0.008), ff.r(), cover, 0.006, 1))
    g.append(box(name + '_b1', (sx, sy, 0.016), ff.p(0, 0, sz - 0.008), ff.r(), cover, 0.006, 1))
    g.append(box(name + '_sp', (0.03, sy, sz), ff.p(-sx / 2 + 0.015, 0, sz / 2), ff.r(), cover, 0.01, 1))
    g.append(box(name + '_pg', (sx - 0.045, sy - 0.03, sz - 0.03), ff.p(0.012, 0, sz / 2), ff.r(), PAPERC, 0.006, 1))
    return sz


def bookcase(i, f, accent, light, seed):
    """Tall case: card-catalogue drawers below, three shelves of spines above."""
    g = []
    W, D, H = 0.68, 0.38, 2.0
    rng = random.Random(seed)

    def b(name, size, uvw, m, bevel=0.02, seg=2, rot=(0, 0, 0)):
        ob = box(f'case{i}_{name}', size, f.p(*uvw), f.r(*rot), m, bevel, seg)
        g.append(ob)
        return ob

    b('plinth', (W + 0.08, D + 0.06, 0.12), (0, 0, 0.06), WARM_D, 0.03, 1)
    b('back', (W, 0.05, H - 0.2), (0, D / 2 - 0.025, H / 2), WARM_D, 0.01, 1)
    b('back_panel', (W - 0.16, 0.03, H - 0.62), (0, D / 2 + 0.006, H / 2 + 0.04), light, 0.012, 1)
    b('back_plate', (0.2, 0.03, 0.2), (0, D / 2 + 0.022, H / 2 + 0.35), accent, 0.012, 1, rot=(0, 45, 0))
    for s in (-1, 1):
        b(f'side{s}', (0.06, D, H - 0.2), (s * (W / 2 - 0.03), 0, H / 2), WARM, 0.02, 1)
    tops = [0.14 + k * 0.44 for k in range(4)]
    for k, wk in enumerate(tops):
        b(f'shelf{k}', (W - 0.1, D - 0.03, 0.04), (0, 0, wk - 0.02), WARM, 0.01, 1)
    b('cornice', (W + 0.12, D + 0.1, 0.12), (0, 0, H - 0.06), accent, 0.035)
    b('frieze', (W + 0.02, D + 0.02, 0.05), (0, 0, H - 0.145), WARM_L, 0.012, 1)
    # card-catalogue drawers
    b('drawer_block', (W - 0.12, D - 0.1, 0.38), (0, 0.02, 0.14 + 0.19), WARM_D, 0.01, 1)
    for r in range(2):
        for c in range(3):
            u, w = (c - 1) * 0.185, 0.14 + 0.1 + r * 0.2
            b(f'drawer{r}{c}', (0.165, 0.05, 0.17), (u, -D / 2 + 0.05, w), PAPERC, 0.018, 1)
            g.append(cyl(f'case{i}_knob{r}{c}', 0.028, 0.04, f.p(u, -D / 2 + 0.015, w - 0.01), f.r(90), accent,
                         verts=8, bevel=0))
    # spines
    for k in (1, 2, 3):
        u, end, n = -W / 2 + 0.07, W / 2 - 0.07, 0
        lean = (k + i) % 3 == 0
        while True:
            t = rng.uniform(0.055, 0.1)
            h = rng.uniform(0.25, 0.36)
            if u + t > end - (0.1 if lean else 0):
                break
            col = accent if rng.random() < 0.52 else rng.choice([light, PAPERC, DEEP, LAV, light])
            b(f'book{k}_{n}', (t - 0.008, 0.24, h), (u + t / 2, -0.03, tops[k] + h / 2), col, 0.012, 1)
            u += t
            n += 1
        if lean:
            b(f'book{k}_lean', (0.07, 0.24, 0.3), (u + 0.075, -0.03, tops[k] + 0.148), light, 0.012, 1, rot=(0, -16, 0))
    return g, W, D, H


def emblem(i, f, w0):
    """A small wordless finial on each case naming its collection."""
    g = []
    n = f'emblem{i}'
    if i == 0:      # financial-aid policies: coins
        for k in range(3):
            g.append(cyl(f'{n}_coin{k}', 0.1, 0.04, f.p(-0.08 + 0.012 * k, 0, w0 + 0.02 + 0.04 * k), f.r(), GOLD,
                         verts=14, bevel=0.012, seg=1))
        g.append(cyl(f'{n}_coin_up', 0.09, 0.04, f.p(0.14, 0, w0 + 0.088), f.r(90, 0, 20), GOLD, verts=14,
                     bevel=0.012, seg=1))
    elif i == 1:    # major admission requirements: mortarboard
        g.append(cyl(f'{n}_cap', 0.1, 0.09, f.p(0, 0, w0 + 0.045), f.r(), DEEP, verts=12, bevel=0.015, seg=1))
        g.append(box(f'{n}_board', (0.32, 0.32, 0.035), f.p(0, 0, w0 + 0.105), f.r(0, 0, 45), DEEP, 0.012, 1))
        g.append(cyl(f'{n}_button', 0.03, 0.03, f.p(0, 0, w0 + 0.135), f.r(), GOLD, verts=8, bevel=0.008, seg=1))
        g.append(rod(f'{n}_cord', f.p(0, 0, w0 + 0.13), f.p(0, -0.2, w0 + 0.125), 0.012, GOLD))
        g.append(box(f'{n}_tassel', (0.035, 0.035, 0.12), f.p(0, -0.21, w0 + 0.07), f.r(), AMBER, 0.012, 1))
    elif i == 2:    # Common Data Set figures: bars
        g.append(box(f'{n}_base', (0.4, 0.16, 0.035), f.p(0, 0, w0 + 0.0175), f.r(), STONE, 0.012, 1))
        for k, h in enumerate((0.11, 0.19, 0.28)):
            g.append(box(f'{n}_bar{k}', (0.09, 0.11, h), f.p(-0.12 + 0.12 * k, 0, w0 + 0.035 + h / 2), f.r(),
                         (CYAN, '#59d0e6', CYAN)[k], 0.018, 2))
    elif i == 3:    # transfer articulation agreements: two linked rings
        g.append(torus(f'{n}_ring_a', 0.095, 0.026, f.p(-0.05, 0, w0 + 0.118), f.r(90), MINT, seg=18, ring=6))
        g.append(torus(f'{n}_ring_b', 0.095, 0.026, f.p(0.04, 0, w0 + 0.118), f.r(90, 0, 90), GOLD, seg=18, ring=6))
    else:           # worked cited answers: a card with a ribbon
        g.append(box(f'{n}_base', (0.3, 0.14, 0.035), f.p(0, 0, w0 + 0.0175), f.r(), STONE, 0.012, 1))
        g.append(box(f'{n}_card', (0.26, 0.035, 0.2), f.p(0, 0.01, w0 + 0.13), f.r(-12), PAPERC, 0.012, 1))
        g.append(box(f'{n}_ribbon', (0.05, 0.02, 0.15), f.p(0.06, -0.012, w0 + 0.1), f.r(-12), PINK, 0.006, 1))
        g.append(box(f'{n}_line', (0.1, 0.02, 0.025), f.p(-0.05, -0.022, w0 + 0.17), f.r(-12), VIOLET, 0.006, 1))
    return g


def bench(name, f):
    g = []
    for s in (-1, 1):
        g.append(box(f'{name}_leg{s}', (0.1, 0.44, 0.36), f.p(s * 0.55, 0, 0.18), f.r(), DEEP, 0.03, 1))
        g.append(box(f'{name}_post{s}', (0.07, 0.07, 0.5), f.p(s * 0.55, 0.22, 0.58), f.r(-8), DEEP, 0.02, 1))
    for j in range(3):
        g.append(box(f'{name}_slat{j}', (1.42, 0.125, 0.05), f.p(0, -0.15 + j * 0.145, 0.385), f.r(), WARM if j != 1 else WARM_L, 0.018, 2))
    for j in range(2):
        g.append(box(f'{name}_back{j}', (1.42, 0.05, 0.13), f.p(0, 0.2 + j * 0.022, 0.6 + j * 0.17), f.r(-8), WARM_L if j else WARM, 0.018, 2))
    return join(g, name)


def topiary(name, loc, pot=INDIGO, leaf=HEDGE, r=0.26, h=0.5, seed=0):
    x, y, z = loc
    g = [lathe(name + '_pot', [(0, 0), (0.15, 0), (0.2, 0.26), (0.22, 0.26), (0.22, 0.32), (0.17, 0.32), (0.16, 0.28), (0, 0.28)],
               (x, y, z), m=pot, verts=16),
         cyl(name + '_stem', 0.035, h, (x, y, z + 0.28 + h / 2), m=WARM_D, verts=8, bevel=0),
         blob(name + '_ball', r, (x, y, z + 0.28 + h + r * 0.7), (1, 1, 0.95), leaf, seed, bumps=0.1, seg=3)]
    return join(g, name)


def planter(name, loc, pot=LAV, leaf=HEDGE, seed=0, s=1.0):
    x, y, z = loc
    g = [lathe(name + '_pot', [(0, 0), (0.17 * s, 0), (0.24 * s, 0.3 * s), (0.26 * s, 0.3 * s), (0.26 * s, 0.36 * s), (0.2 * s, 0.36 * s), (0, 0.33 * s)],
               (x, y, z), m=pot, verts=16),
         blob(name + '_leaf', 0.27 * s, (x, y, z + 0.52 * s), (1, 1, 0.85), leaf, seed, bumps=0.2, seg=3)]
    return join(g, name)


def bubble_outline(hw, hh, r, cz, n=6):
    pts = []
    corners = [((-hw + r, cz - hh + r), 180), ((hw - r, cz - hh + r), 270),
               ((hw - r, cz + hh - r), 0), ((-hw + r, cz + hh - r), 90)]
    for ci, ((cx, cy), a0) in enumerate(corners):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        if ci == 0:     # the tail hangs off the bottom edge
            pts += [(-hw + r + 0.1, cz - hh), (-hw + r - 0.1, cz - hh - 0.42), (-hw + r + 0.52, cz - hh)]
    return pts


# ---------------------------------------------------------------- island
def build(mode='preview'):
    reset()
    setup_world()
    base, radius_at = island_base(R=5.3, seed=23, top=LAWN, lip='#a6d08f', soil='#d9d2e2', soil2='#b9b1cd',
                                  rock_c='#9d9ab6', lobes=((2, 0.04), (3, 0.05), (5, 0.025)))
    E = (-0.4, 1.75)                      # centre of the oval plaza
    SY = 0.84                             # plaza depth / width
    A = (-0.4, 1.0)                       # centre of the bookcase arc and colonnade
    K = (-0.4, 1.15)                      # centre of the court inlay
    FZ = 0.2                              # plaza floor height

    def oval(a, r, z=0.0):
        return (E[0] + r * math.cos(math.radians(a)), E[1] + SY * r * math.sin(math.radians(a)), z)

    def on_arc(a, r, z=0.0):
        return (A[0] + r * math.cos(math.radians(a)), A[1] + r * math.sin(math.radians(a)), z)

    # ============================================================ 1. library pavilion
    for ob in (lathe('pav_step', [(0, 0), (3.22, 0), (3.22, 0.1), (0, 0.1)], (E[0], E[1], 0), m=STONE_D, verts=72, bevel=0.03),
               lathe('pav_floor', [(0, 0.1), (3.05, 0.1), (3.05, FZ), (0, FZ)], (E[0], E[1], 0), m=STONE, verts=72, bevel=0.03)):
        ob.scale = (1, SY, 1)
    g = [arc_lathe('pav_inlay', [(1.0, 0), (1.2, 0), (1.2, 0.012), (1.0, 0.012)], 0, 360, (K[0], K[1], FZ), m=INDIGO, steps=48, bevel=0),
         arc_lathe('pav_inlay2', [(1.3, 0), (1.35, 0), (1.35, 0.012), (1.3, 0.012)], 0, 360, (K[0], K[1], FZ), m=VIOLET, steps=48, bevel=0),
         cyl('pav_medallion', 0.36, 0.014, (K[0], K[1], FZ + 0.007), m=PINK, verts=8, bevel=0),
         cyl('pav_medallion2', 0.21, 0.014, (K[0], K[1], FZ + 0.019), (0, 0, 22.5), m=PAPERC, verts=8, bevel=0)]
    for k in range(16):
        a = TAU * (k + 0.5) / 16
        g.append(box(f'pav_tile_{k}', (0.2, 0.2, 0.024), (K[0] + 1.72 * math.cos(a), K[1] + 1.72 * math.sin(a), FZ),
                     (0, 0, math.degrees(a) + 45), (VIOLET, INDIGO)[k % 4 == 0], 0.006, 1))
    join(g, 'plaza_inlay')
    RC = 2.75                                            # radius of the gentle bookcase arc
    case_angles = (121, 105.5, 90, 74.5, 59)             # left to right from the default camera
    accents = ((AMBER, '#fbd38a'), (INDIGO, '#a5a7f8'), (CYAN, '#8adfee'), (MINT, '#a2e6c2'), (PINK, '#f7a8cf'))
    frames = []
    for i, (a, (acc, light)) in enumerate(zip(case_angles, accents)):
        f = Frame(on_arc(a, RC, FZ), a - 90)
        frames.append(f)
        g, W, D, H = bookcase(i, f, acc, light, seed=40 + i)
        join(g + emblem(i, f, H), f'bookcase_{i}')
    # brass ladder rail along the case fronts and the rolling ladder
    rail = tube('ladder_rail', [on_arc(52 + 76 * k / 8, RC - 0.26, FZ + 1.84) for k in range(9)], 0.022, GOLD, res=4)
    lf = frames[1]
    g = []
    for s in (-1, 1):
        g.append(rod(f'ladder_rail{s}', lf.p(0.1 + s * 0.17, -0.92, 0.07), lf.p(0.1 + s * 0.17, -0.27, 1.97), 0.03, WARM_L))
        g.append(cyl(f'ladder_wheel{s}', 0.06, 0.05, lf.p(0.1 + s * 0.2, -0.93, 0.06), lf.r(0, 90), DEEP, verts=12, bevel=0.012, seg=1))
        g.append(sphere(f'ladder_hook{s}', 0.045, lf.p(0.1 + s * 0.17, -0.265, 1.95), m=GOLD, seg=10))
    for j in range(6):
        t = (j + 0.8) / 6.6
        g.append(cyl(f'ladder_rung{j}', 0.022, 0.34, lf.p(0.1, -0.92 + 0.65 * t, 0.07 + 1.9 * t), lf.r(0, 90), WARM, verts=8, bevel=0))
    join(g, 'ladder')

    # colonnade
    CH = 2.62
    col_profile = [(0, 0), (0.21, 0), (0.21, 0.08), (0.17, 0.12), (0.14, 0.17), (0.118, CH - 0.24), (0.15, CH - 0.18),
                   (0.2, CH - 0.12), (0.2, CH), (0, CH)]
    col_angles = [51.25 + 15.5 * k for k in range(6)]
    for k, a in enumerate(col_angles):
        lathe(f'column_{k}', col_profile, on_arc(a, RC + 0.37, FZ), m=PAPERC, verts=16)
    arc_lathe('pav_entablature', [(RC - 0.13, 0), (RC + 0.71, 0), (RC + 0.71, 0.2), (RC - 0.13, 0.2)], 46, 134, (A[0], A[1], FZ + CH),
              m=STONE, steps=28, bevel=0.03)
    arc_lathe('pav_roof', [(RC - 0.3, 0), (RC + 0.9, 0), (RC + 0.9, 0.07), (RC + 0.32, 0.5), (RC + 0.26, 0.5), (RC - 0.3, 0.07)], 43.5, 136.5,
              (A[0], A[1], FZ + CH + 0.2), m=INDIGO, steps=28, bevel=0.03)
    tube('pav_ridge', [on_arc(43.5 + 93 * k / 9, RC + 0.29, FZ + CH + 0.72) for k in range(10)], 0.055, DEEP, res=3)
    for k, r in enumerate((RC - 0.3, RC + 0.9)):         # pale trim along both eaves
        tube(f'pav_eave_{k}', [on_arc(43.5 + 93 * j / 9, r, FZ + CH + 0.235) for j in range(10)], 0.042, LAV, res=3)
    join([sphere(f'pav_finial_{k}', 0.1, on_arc(a, RC + 0.29, FZ + CH + 0.81), m=GOLD, seg=12)
          for k, a in enumerate((43.5, 90, 136.5))], 'pav_finials')
    g = []
    for k in range(12):                                  # rafter tails under the inner eave
        a = 48 + 84 * k / 11
        g.append(box(f'pav_tail_{k}', (0.16, 0.09, 0.09), on_arc(a, RC - 0.17, FZ + CH + 0.11), (0, 0, a), LAV, 0.02, 1))
    join(g, 'pav_rafter_tails')

    # a book trolley on the plaza
    tf = Frame((K[0] + 1.35, K[1] + 0.35, FZ), 24)
    g = [box('trolley_body', (0.62, 0.36, 0.06), tf.p(0, 0, 0.16), tf.r(), DEEP, 0.02, 2),
         box('trolley_top', (0.62, 0.36, 0.05), tf.p(0, 0, 0.52), tf.r(), DEEP, 0.02, 2)]
    for su in (-1, 1):
        for sv in (-1, 1):
            g.append(cyl(f'trolley_leg{su}{sv}', 0.022, 0.5, tf.p(su * 0.27, sv * 0.14, 0.33), tf.r(), STEEL_DARK, verts=8, bevel=0))
            g.append(cyl(f'trolley_wheel{su}{sv}', 0.055, 0.04, tf.p(su * 0.27, sv * 0.14, 0.055), tf.r(0, 90), INK, verts=10, bevel=0.01, seg=1))
    g.append(rod('trolley_handle', tf.p(0.31, -0.14, 0.52), tf.p(0.44, -0.14, 0.72), 0.02, STEEL_DARK))
    g.append(rod('trolley_handle2', tf.p(0.31, 0.14, 0.52), tf.p(0.44, 0.14, 0.72), 0.02, STEEL_DARK))
    g.append(rod('trolley_grip', tf.p(0.44, -0.16, 0.72), tf.p(0.44, 0.16, 0.72), 0.024, PINK))
    z = 0.545
    for k, c in enumerate((CYAN, PAPERC, PINK)):
        z += book(g, f'trolley_book{k}', tf, (-0.08, 0, z), (0.34, 0.25, 0.07), c, (k - 1) * 11)
    for k, c in enumerate((AMBER, INDIGO, MINT, LAV)):
        g.append(box(f'trolley_low{k}', (0.07, 0.24, 0.26), tf.p(-0.2 + k * 0.085, 0, 0.19 + 0.13), tf.r(), c, 0.012, 1))
    join(g, 'trolley')

    # a library kick stool by the left-hand cases
    kx, ky, _ = on_arc(117, RC - 0.85)
    join([lathe('kick_stool', [(0, 0), (0.21, 0), (0.21, 0.04), (0.17, 0.2), (0.15, 0.24), (0, 0.24)], (kx, ky, FZ), m=PINK, verts=16),
          cyl('kick_stool_pad', 0.13, 0.02, (kx, ky, FZ + 0.25), m=DEEP, verts=14, bevel=0)], 'kick_stool')

    # ============================================================ paths
    g = []
    for i in range(7):
        x, y = 0.1 - 0.105 * i, -1.3 - 0.485 * i
        for s in (-1, 1):
            w = 0.38 + 0.03 * ((i + s) % 3)
            g.append(box(f'pave_{i}_{s}', (w, 0.4, 0.06), (x + s * 0.25, y + s * 0.05, 0.02 + 0.005 * ((i + s) % 3)),
                         (0, 0, -11 + ((i * 7 + s * 3) % 7 - 3)), STONE if (i + s) % 2 else STONE_D, 0.03, 2))
    join(g, 'paving')

    # ============================================================ 5. the question: speech bubble
    bf = Frame((-3.4, -2.3, 0), -8)
    BZ = 1.5
    g = [prism('bubble', bubble_outline(0.87, 0.57, 0.4, BZ), 0.44, bf.p(0, 0.22, 0), bf.r(90), INDIGO, bevel=0.09, seg=3)]
    for k, du in enumerate((-0.43, 0.0, 0.43)):
        for s in (-1, 1):
            g.append(sphere(f'bubble_dot_{k}_{s}', 0.155, bf.p(du, s * 0.2, BZ), (1, 0.8, 1), PAPERC, 14, rot=bf.r()))
    g += [lathe('bubble_base', [(0, 0), (0.44, 0), (0.44, 0.07), (0.32, 0.14), (0, 0.14)], bf.p(0.12, 0, 0), m=STONE_D, verts=28, bevel=0.02),
          cyl('bubble_post', 0.07, 0.86, bf.p(0.12, 0, 0.14 + 0.43), m=DEEP, verts=12, bevel=0),
          torus('bubble_collar', 0.085, 0.03, bf.p(0.12, 0, 0.9), m=GOLD, seg=16, ring=6)]
    join(g, 'speech_bubble')
    # dotted stepping stones from the bubble to the pavilion
    s0, s1, ctrl = (-2.75, -2.8), (-1.2, -1.02), (-1.75, -2.35)
    g = []
    for i in range(8):
        t = (i + 0.2) / 7.4
        x = (1 - t) ** 2 * s0[0] + 2 * t * (1 - t) * ctrl[0] + t * t * s1[0]
        y = (1 - t) ** 2 * s0[1] + 2 * t * (1 - t) * ctrl[1] + t * t * s1[1]
        g.append(cyl(f'step_dot_{i}', 0.14 + 0.03 * (i % 2), 0.06, (x, y, 0.022), (0, 0, i * 31), PAPERC if i % 2 else STONE_D,
                     verts=12, bevel=0.022, seg=1))
    join(g, 'stepping_stones')

    # ============================================================ 2. the cite gate
    gf = Frame((-0.22, -2.74, 0), -12)
    g = []
    for s in (-1, 1):
        g.append(box(f'gate_base{s}', (0.4, 0.46, 0.12), gf.p(s * 0.6, 0, 0.06), gf.r(), STONE_D, 0.03, 2))
        g.append(box(f'gate_pillar{s}', (0.3, 0.36, 1.0), gf.p(s * 0.6, 0, 0.6), gf.r(), STONE, 0.04, 2))
        g.append(box(f'gate_cap{s}', (0.37, 0.43, 0.08), gf.p(s * 0.6, 0, 1.1), gf.r(), STONE_D, 0.02, 2))
    g.append(arc_lathe('gate_arch', [(0.45, -0.17), (0.75, -0.17), (0.75, 0.17), (0.45, 0.17)], 0, 180, gf.p(0, 0, 1.14), gf.r(90),
                       m=INDIGO, steps=20, bevel=0.035))
    g.append(box('gate_keystone', (0.2, 0.4, 0.36), gf.p(0, 0, 1.14 + 0.6), gf.r(), PAPERC, 0.03, 2))
    g.append(box('gate_deck', (0.92, 0.32, 0.1), gf.p(0, 0, 1.14 + 0.78), gf.r(), DEEP, 0.03, 2))
    lamp_mats = (mat('#3ddc84', 0.3, emit=2.6, emit_color='#22c55e'), mat('#ffa62b', 0.3, emit=2.0, emit_color='#ff8a00'))
    for k, (s, lm) in enumerate(zip((-1, 1), lamp_mats)):
        g.append(cyl(f'gate_lamp_base{k}', 0.09, 0.07, gf.p(s * 0.26, 0, 2.005), m=INK, verts=12, bevel=0.015, seg=1))
        lamp = sphere(f'gate_lamp_{("green", "amber")[k]}', 0.135, gf.p(s * 0.26, 0, 2.15), m=lm, seg=14)
        animate(lamp, 'pulse', speed=1.1 + 0.5 * k)
        g.append(lathe(f'gate_lamp_cap{k}', [(0.11, 0), (0.03, 0.07), (0, 0.07)], gf.p(s * 0.26, 0, 2.255), m=INK, verts=12))
    join(g, 'cite_gate')
    # the answer card, passing through with its three citation ribbons
    cf = Frame(gf.p(0.0, -0.14, 0), gf.deg + 9)
    cz = 0.93
    g = [box('answer_card_body', (0.58, 0.045, 0.4), cf.p(0, 0, cz), cf.r(), PAPERC, 0.03, 2),
         box('answer_head', (0.3, 0.014, 0.05), cf.p(-0.08, -0.024, cz + 0.115), cf.r(), INDIGO, 0.006, 1),
         cyl('answer_tick', 0.04, 0.016, cf.p(0.19, -0.024, cz + 0.115), cf.r(90), MINT, verts=12, bevel=0.004, seg=1)]
    for k, (du, wd) in enumerate(((0.0, 0.46), (0.0, 0.46), (-0.08, 0.3))):
        g.append(box(f'answer_line{k}', (wd, 0.014, 0.028), cf.p(du, -0.024, cz + 0.03 - 0.065 * k), cf.r(), VIOLET, 0.006, 1))
    for k, (du, c) in enumerate(((-0.17, PINK), (0.0, CYAN), (0.17, AMBER))):
        g.append(prism(f'answer_ribbon{k}', [(-0.045, 0), (0, 0.05), (0.045, 0), (0.045, 0.27), (-0.045, 0.27)], 0.03,
                       cf.p(du, 0.05, cz - 0.43 - 0.02 * (k % 2)), cf.r(90), c, bevel=0.008, seg=1))
    card = join(g, 'answer_card')
    set_origin(card, cf.p(0, 0, cz))
    animate(card, 'bob', amp=0.05, speed=1.0)
    # the tray beside the gate: a blank card set aside (the abstention)
    tr = Frame(gf.p(1.22, -0.12, 0), gf.deg - 14)
    tc, tilt = (0, 0, 0.7), 14
    g = [cyl('tray_foot', 0.17, 0.05, tr.p(0, 0, 0.025), m=STONE_D, verts=14, bevel=0.015, seg=1),
         cyl('tray_post', 0.05, 0.62, tr.p(0, 0, 0.34), m=DEEP, verts=10, bevel=0),
         box('tray', (0.56, 0.42, 0.05), tr.p(*tilted(tc, tilt, 0, 0, 0)), tr.r(tilt), WARM, 0.02, 2)]
    for k, (a, b, sz) in enumerate(((0, -0.195, (0.56, 0.04, 0.07)), (0, 0.195, (0.56, 0.04, 0.07)),
                                    (-0.26, 0, (0.04, 0.42, 0.07)), (0.26, 0, (0.04, 0.42, 0.07)))):
        g.append(box(f'tray_rim{k}', sz, tr.p(*tilted(tc, tilt, a, b, 0.045)), tr.r(tilt), WARM_D, 0.015, 1))
    join(g, 'abstain_tray')
    box('blank_card', (0.4, 0.28, 0.03), tr.p(*tilted(tc, tilt, 0.0, 0.0, 0.041)), tr.r(tilt, 0, 7), PAPERC, 0.012, 2)

    # ============================================================ 3. the balance scale
    sx, sy, fz = 3.6, 0.6, 1.42
    join([lathe('scale_plinth', [(0, 0), (0.52, 0), (0.52, 0.09), (0.4, 0.15), (0, 0.15)], (sx, sy, 0), m=STONE_D, verts=28, bevel=0.02),
          lathe('scale_post', [(0, 0.15), (0.22, 0.15), (0.22, 0.2), (0.11, 0.3), (0.065, 0.44), (0.052, 1.22), (0.09, 1.28),
                               (0.09, 1.34), (0.055, 1.38), (0.055, 1.5), (0, 1.5)], (sx, sy, 0), m=GOLD, verts=16),
          sphere('scale_finial', 0.075, (sx, sy, 1.56), m=GOLD, seg=12)], 'scale_stand')
    g = [cyl('scale_hub', 0.075, 0.22, (sx, sy, fz), (90, 0, 0), DEEP, verts=14, bevel=0.02, seg=2),
         box('scale_arm', (1.72, 0.075, 0.085), (sx, sy, fz), (0, -8, 0), DEEP, 0.025, 2)]
    for s in (-1, 1):
        ex, ez = sx + s * 0.82 * math.cos(math.radians(8)), fz + s * 0.82 * math.sin(math.radians(8))
        pz = ez - 0.6
        g.append(sphere(f'scale_knob{s}', 0.055, (ex, sy, ez), m=GOLD, seg=10))
        for k, a in enumerate((90, 210, 330)):
            ar = math.radians(a)
            g.append(rod(f'scale_cord{s}{k}', (ex, sy, ez - 0.02), (ex + 0.32 * math.cos(ar), sy + 0.32 * math.sin(ar), pz + 0.045), 0.014, GOLD))
        g.append(lathe(f'scale_pan{s}', [(0, -0.03), (0.22, -0.02), (0.33, 0.03), (0.35, 0.055), (0.31, 0.05), (0.2, 0.005), (0, 0.0)],
                       (ex, sy, pz), m=GOLD, verts=24))
        if s == -1:     # heavy pan: a stack of documents under a rosette seal
            for k in range(5):
                g.append(box(f'scale_doc{k}', (0.36, 0.27, 0.042), (ex, sy, pz + 0.027 + k * 0.043), (0, 0, (k * 17) % 26 - 12),
                             (PAPERC, LAV, PAPERC, '#efe9d8', PAPERC)[k], 0.012, 1))
            top = pz + 0.006 + 5 * 0.043
            for k in range(2):
                g.append(cyl(f'scale_seal_frill{k}', 0.125, 0.022, (ex, sy, top + 0.011), (0, 0, k * 22.5), '#c9287a', verts=8, bevel=0.008, seg=1))
            g.append(cyl('scale_seal', 0.085, 0.04, (ex, sy, top + 0.02), m=PINK, verts=14, bevel=0.012, seg=1))
            g.append(cyl('scale_seal_boss', 0.04, 0.02, (ex, sy, top + 0.048), m=GOLD, verts=10, bevel=0.006, seg=1))
            for k, rz in enumerate((-115, -65)):
                g.append(prism(f'scale_seal_tail{k}', [(-0.035, 0), (0, 0.04), (0.035, 0), (0.035, 0.2), (-0.035, 0.2)], 0.02,
                               (ex + 0.17 * math.cos(math.radians(rz)), sy + 0.17 * math.sin(math.radians(rz)), top + 0.001),
                               (0, 0, rz + 90), PINK, bevel=0.005, seg=1))
        else:           # light pan: one loose sheet
            g.append(box('scale_sheet', (0.3, 0.22, 0.03), (ex, sy, pz + 0.03), (5, -4, 28), PAPERC, 0.01, 1))
    beam = join(g, 'scale_beam')
    set_origin(beam, (sx, sy, fz))
    animate(beam, 'sway', amp=2.5, speed=0.7, axis='y')

    # ============================================================ 4. reading desk and calculator
    df = Frame((2.45, -2.45, 0), -30)
    lathe('desk_pad', [(0.0, 0.012), (1.22, 0.012), (1.3, -0.02)], df.p(0, -0.1, 0), m=STONE, verts=40)
    T = 0.845
    g = [box('desk_top', (1.95, 0.98, 0.09), df.p(0, 0, 0.8), df.r(), WARM, 0.035, 3)]
    for su in (-1, 1):
        for sv in (-1, 1):
            g.append(box(f'desk_leg{su}{sv}', (0.12, 0.12, 0.76), df.p(su * 0.86, sv * 0.38, 0.38), df.r(), WARM_D, 0.03, 2))
        g.append(box(f'desk_apron{su}', (1.66, 0.06, 0.14), df.p(0, su * 0.38, 0.69), df.r(), WARM_D, 0.02, 1))
    g.append(box('desk_drawers', (0.5, 0.74, 0.44), df.p(0.56, 0, 0.54), df.r(), WARM_D, 0.03, 2))
    for k in range(2):
        g.append(box(f'desk_drawer{k}', (0.42, 0.04, 0.17), df.p(0.56, -0.375, 0.44 + k * 0.2), df.r(), WARM_L, 0.018, 1))
        g.append(sphere(f'desk_knob{k}', 0.03, df.p(0.56, -0.4, 0.44 + k * 0.2), m=GOLD, seg=8))
    join(g, 'desk')
    # open book
    bu, bv = -0.36, -0.14
    g = [box('book_cover', (0.76, 0.5, 0.03), df.p(bu, bv, T + 0.015), df.r(), DEEP, 0.012, 2),
         box('book_gutter', (0.03, 0.46, 0.05), df.p(bu, bv, T + 0.05), df.r(), VIOLET, 0.01, 1)]
    hi = {(-1, 1): CYAN, (1, 0): AMBER, (1, 2): PINK}
    targets = {}
    for s in (-1, 1):
        g.append(box(f'book_page{s}', (0.35, 0.46, 0.06), df.p(bu + s * 0.183, bv, T + 0.06), df.r(0, s * 4, 0), PAPERC, 0.022, 2))
        for k in range(4):
            c = hi.get((s, k), VIOLET)
            pos = df.p(bu + s * 0.183, bv + 0.14 - k * 0.09, T + 0.096)
            g.append(box(f'book_line{s}{k}', (0.24, 0.03, 0.014), pos, df.r(0, s * 4, 0), c, 0.005, 1))
            if (s, k) in hi:
                targets[hi[(s, k)]] = pos
    g.append(box('book_ribbon', (0.045, 0.2, 0.014), df.p(bu + 0.03, bv - 0.28, T + 0.012), df.r(0, 0, 8), PINK, 0.005, 1))
    join(g, 'open_book')
    # pin board with three index cards, each tied by a thread to a highlighted line
    bc, btilt = (-0.36, 0.38, T + 0.36), -9
    g = [box('board', (1.0, 0.05, 0.56), df.p(*tilted(bc, btilt, 0, 0, 0)), df.r(btilt), '#dcbd8f', 0.02, 2),
         box('board_frame', (1.06, 0.04, 0.62), df.p(*tilted(bc, btilt, 0, 0.012, 0)), df.r(btilt), WARM_D, 0.02, 2)]
    for s in (-1, 1):
        g.append(box(f'board_foot{s}', (0.07, 0.26, 0.06), df.p(bc[0] + s * 0.4, 0.37, T + 0.03), df.r(), WARM_D, 0.015, 1))
    join(g, 'pin_board')
    for k, (a, c) in enumerate(((-0.31, CYAN), (0.0, AMBER), (0.31, PINK))):
        cc = 0.05 + 0.03 * (k % 2)
        g = [box(f'index_card_{k}', (0.24, 0.022, 0.17), df.p(*tilted(bc, btilt, a, -0.038, cc)), df.r(btilt, 0, (k - 1) * 4), PAPERC, 0.01, 1),
             box(f'index_band_{k}', (0.24, 0.012, 0.035), df.p(*tilted(bc, btilt, a, -0.052, cc + 0.05)), df.r(btilt, 0, (k - 1) * 4), c, 0.004, 1)]
        for j in range(2):
            g.append(box(f'index_line_{k}{j}', (0.17, 0.012, 0.016), df.p(*tilted(bc, btilt, a - 0.02, -0.052, cc - 0.005 - j * 0.04)),
                         df.r(btilt, 0, (k - 1) * 4), VIOLET, 0.004, 1))
        pin = df.p(*tilted(bc, btilt, a, -0.06, cc + 0.1))
        g.append(sphere(f'index_pin_{k}', 0.03, pin, m=c, seg=8))
        join(g, f'index_card_{k}')
        end = targets[c]
        mid = ((pin[0] + end[0]) / 2, (pin[1] + end[1]) / 2, min(pin[2], end[2]) + 0.1)
        th = tube(f'thread_{k}', [pin, mid, (end[0], end[1], end[2] + 0.012)], 0.014, c, res=6)
        th.data.bevel_resolution = 2
        join([th, sphere(f'thread_knot_{k}', 0.024, (end[0], end[1], end[2] + 0.012), m=c, seg=8)], f'thread_{k}')
    # desk lamp
    join([cyl('desk_lamp_base', 0.12, 0.045, df.p(-0.83, 0.2, T + 0.022), m=DEEP, verts=14, bevel=0.015, seg=1),
          tube('desk_lamp_arm', [df.p(-0.83, 0.2, T + 0.04), df.p(-0.9, 0.24, T + 0.42), df.p(-0.8, 0.12, T + 0.7),
                                 df.p(-0.6, -0.02, T + 0.66)], 0.024, DEEP, res=6),
          cyl('desk_lamp_shade', 0.17, 0.17, df.p(-0.56, -0.05, T + 0.6), df.r(-18, -30, 0), INDIGO, r2=0.06, verts=16, bevel=0.02, seg=1)],
         'desk_lamp')
    bulb = sphere('desk_lamp_bulb', 0.075, df.p(-0.52, -0.075, T + 0.535), m=mat('#fff3c4', 0.3, emit=6.0, emit_color='#ffd27a'), seg=12)
    # pencil cup
    g = [cyl('pencil_cup', 0.065, 0.14, df.p(-0.82, -0.32, T + 0.07), m=PINK, verts=12, bevel=0.015, seg=1)]
    for k, (c, rx, ry) in enumerate(((AMBER, 10, 8), (CYAN, -9, 12), (INDIGO, 4, -12))):
        g.append(cyl(f'pencil_{k}', 0.016, 0.24, df.p(-0.82 + (k - 1) * 0.02, -0.32, T + 0.17), df.r(rx, ry, 0), c, verts=6, bevel=0))
    join(g, 'pencil_cup')
    # the deterministic calculator and its paper tape
    ct = 12
    cc0 = (0.55, -0.06, T + 0.36 * math.sin(math.radians(ct)) + 0.11 * math.cos(math.radians(ct)))
    g = [box('calc_body', (0.56, 0.72, 0.22), df.p(*cc0), df.r(ct), DEEP, 0.05, 3),
         box('calc_foot', (0.54, 0.5, 0.12), df.p(0.55, 0.04, T + 0.06), df.r(), DEEP, 0.03, 2),
         box('calc_bezel', (0.46, 0.17, 0.03), df.p(*tilted(cc0, ct, 0, 0.14, 0.112)), df.r(ct), INK, 0.012, 1)]
    for i in range(4):
        for j in range(4):
            c = LAV
            if i == 3:
                c = INDIGO
            if (i, j) == (3, 0):
                c = PINK
            if (i, j) == (0, 3):
                c = AMBER
            g.append(box(f'calc_key{i}{j}', (0.09, 0.075, 0.05), df.p(*tilted(cc0, ct, -0.168 + 0.112 * i, -0.285 + 0.098 * j, 0.122)),
                         df.r(ct), c, 0.016, 1))
    g.append(box('calc_printer', (0.46, 0.13, 0.1), df.p(*tilted(cc0, ct, 0, 0.29, 0.13)), df.r(ct), INK, 0.03, 2))
    g.append(cyl('calc_roll', 0.075, 0.3, df.p(*tilted(cc0, ct, 0, 0.36, 0.2)), df.r(0, 90, 0), PAPERC, verts=14, bevel=0.012, seg=1))
    join(g, 'calculator')
    box('calc_display', (0.4, 0.115, 0.02), df.p(*tilted(cc0, ct, 0, 0.14, 0.13)), df.r(ct),
        mat('#b6f1fa', 0.3, emit=1.6, emit_color=CYAN), 0.008, 1)
    slot = tilted(cc0, ct, 0, 0.29, 0.17)
    v0, w0 = slot[1], slot[2]
    g = [strip('calc_tape', df, 0.55, [(v0, w0), (v0 - 0.03, w0 + 0.22), (v0 - 0.02, w0 + 0.46), (v0 + 0.1, w0 + 0.62),
                                       (v0 + 0.27, w0 + 0.58), (v0 + 0.33, w0 + 0.42), (v0 + 0.26, w0 + 0.3),
                                       (v0 + 0.16, w0 + 0.34), (v0 + 0.17, w0 + 0.44)], 0.24, 0.03, PAPERC)]
    for k in range(4):
        g.append(box(f'calc_tape_line{k}', (0.11 + 0.04 * (k % 2), 0.012, 0.022),
                     df.p(0.55 + 0.02 - 0.02 * (k % 2), v0 - 0.045, w0 + 0.12 + k * 0.075), df.r(-4), DEEP if k != 3 else PINK, 0.004, 1))
    join(g, 'calc_tape')
    # stool
    stf = Frame(df.p(-0.3, -0.98, 0), df.deg)
    g = [cyl('stool_seat', 0.21, 0.07, stf.p(0, 0, 0.455), m=WARM_L, verts=16, bevel=0.025, seg=2),
         cyl('stool_cushion', 0.185, 0.05, stf.p(0, 0, 0.51), m=INDIGO, verts=16, bevel=0.022, seg=2)]
    for k in range(3):
        a = TAU * k / 3 + 0.4
        g.append(rod(f'stool_leg{k}', stf.p(0.1 * math.cos(a), 0.1 * math.sin(a), 0.43), stf.p(0.2 * math.cos(a), 0.2 * math.sin(a), 0.02), 0.03, WARM_D))
    join(g, 'stool')

    # ============================================================ ground detail
    ba = Frame((4.1, -0.75, 0), -62)
    bench('bench_a', ba)
    bench('bench_b', Frame((-4.2, 0.75, 0), -72))
    # a stack of loose pages on a stone block, the top one lifting
    pf = Frame((1.3, -3.85, 0), 24)
    g = [box('page_block', (0.52, 0.42, 0.3), pf.p(0, 0, 0.15), pf.r(), STONE_D, 0.05, 2)]
    for k in range(4):
        g.append(box(f'page_{k}', (0.36, 0.27, 0.03), pf.p(0.01 * k, 0, 0.316 + k * 0.03), pf.r(0, 0, k * 11 - 14),
                     (PAPERC, LAV, PAPERC, '#efe9d8')[k], 0.01, 1))
    join(g, 'page_stack')
    page = box('loose_page', (0.36, 0.27, 0.03), pf.p(0.03, -0.02, 0.62), pf.r(12, -9, 31), PAPERC, 0.01, 1)
    animate(page, 'bob', amp=0.07, speed=0.8)
    box('bench_cushion', (0.4, 0.34, 0.07), ba.p(-0.36, -0.01, 0.445), ba.r(0, 0, 4), PINK, 0.03, 2)
    g = []
    z = 0.41
    for k, c in enumerate((INDIGO, PINK)):
        z += book(g, f'bench_book{k}', ba, (0.35, 0.0, z), (0.34, 0.25, 0.075), c, k * 14 - 5)
    join(g, 'bench_books')
    # lamp post
    lx, ly = -4.0, -0.65
    join([lathe('lamp_base', [(0, 0), (0.17, 0), (0.17, 0.08), (0.08, 0.2), (0, 0.2)], (lx, ly, 0), m=DEEP, verts=14),
          cyl('lamp_pole', 0.045, 1.7, (lx, ly, 1.0), m=DEEP, verts=10, bevel=0),
          cyl('lamp_collar', 0.11, 0.05, (lx, ly, 1.86), m=DEEP, verts=12, bevel=0.015, seg=1),
          lathe('lamp_cap', [(0.13, 0), (0.03, 0.09), (0, 0.09)], (lx, ly, 2.2), m=DEEP, verts=12)], 'lamp_post')
    sphere('lamp_globe', 0.19, (lx, ly, 2.05), m=mat('#fff3c4', 0.3, emit=3.5, emit_color='#ffd98a'), seg=16)
    # stacked books on the ground
    for n, (x, y, rz, cols) in enumerate((((1.2, -1.75, 30, (CYAN, DEEP, AMBER, PAPERC))), ((-2.3, 1.0, -15, (PINK, INDIGO, LAV))),
                                          ((2.1, -4.0, 55, (MINT, INDIGO))))):
        g, z = [], 0.005
        sf = Frame((x, y, FZ if n == 1 else 0), rz)
        for k, c in enumerate(cols):
            z += book(g, f'stack{n}_{k}', sf, (0.02 * (k % 2), 0, z), (0.4 - 0.03 * k, 0.29 - 0.02 * k, 0.085), c, (k * 23) % 31 - 14)
        join(g, f'book_stack_{n}')
    # topiaries and planters
    for k, a in enumerate((267, 290)):
        topiary(f'topiary_{k}', oval(a, 2.72, FZ), seed=k)
    planter('planter_a', (0.75, -2.0, 0), LAV, HEDGE, 3)
    planter('planter_b', (-1.75, -3.45, 0), INDIGO, '#7cc587', 5, 0.9)
    planter('planter_c', (3.75, -1.55, 0), LAV, HEDGE_D, 8, 0.9)
    # low hedges around the plaza
    hp = [(3.42, 0), (3.72, 0), (3.72, 0.3), (3.42, 0.3)]
    for k, (a0, a1) in enumerate(((148, 194), (204, 249), (297, 322), (346, 388))):
        h = arc_lathe(f'hedge_{k}', hp, a0, a1, (E[0], E[1], 0), m=HEDGE if k % 2 else HEDGE_D, steps=max(6, (a1 - a0) // 5), bevel=0.11, seg=3)
        h.scale = (1, SY, 1)
    # trees and bushes
    join(tree('tree_a', (-4.38, 1.98, 0), 2.2, 0.82, leaf='#7cc587', leaf2='#5fae76', seed=3), 'tree_a')
    join(tree('tree_b', (3.5, 3.05, 0), 2.0, 0.74, leaf='#f6bcd9', leaf2='#ef9cc6', seed=6), 'tree_b')
    for i, (x, y, r) in enumerate([(-3.2, 3.9, 0.34), (2.5, 4.0, 0.3), (-4.6, -1.3, 0.3), (4.55, 1.6, 0.3), (0.5, -4.5, 0.26), (-2.6, -3.9, 0.24),
                                   (3.6, -2.9, 0.26)]):
        blob(f'bush_{i}', r, (x, y, r * 0.55), (1.2, 1.1, 0.75), HEDGE if i % 2 else '#7cc587', seed=i, seg=2)
    for i, (x, y) in enumerate([(-3.9, -1.5), (-1.2, -4.1), (0.2, -4.75), (2.2, -4.2), (4.7, 0.3), (2.9, 1.45), (-4.7, 0.2),
                                (-3.9, 3.2), (3.0, 4.2), (-2.4, -1.5)]):
        join(grass_tuft(f'tuft_{i}', (x, y, 0), seed=i, m='#8cc98a'), f'tuft_{i}')
    for i, (x, y) in enumerate([(-2.9, -3.6), (-1.5, -2.9), (0.9, -2.9), (1.9, -0.9), (4.4, 1.0), (-4.4, -0.2), (2.6, 2.3), (-0.9, -4.3),
                                (-3.8, 2.9), (4.2, 2.3), (1.6, -4.55), (-3.2, -0.4)]):
        join(flower(f'flower_{i}', (x, y, 0), 0.24, (PINK, '#a5a7f8', PAPERC)[i % 3], SUNSHINE), f'flower_{i}')
    # scattered cards on the lawn
    for i, (x, y, rz, c) in enumerate([(0.75, -3.45, 20, PAPERC), (0.75, -4.2, -35, LAV), (-1.0, -3.3, 50, PAPERC), (1.7, -1.3, 12, PAPERC),
                                       (2.7, -0.6, -20, LAV), (-2.6, -1.2, 70, PAPERC), (1.9, -4.3, 40, PAPERC)]):
        box(f'card_{i}', (0.26, 0.18, 0.03), (x, y, 0.02), (0, 0, rz), c, 0.01, 1)
    for i, (x, y, r) in enumerate([(4.75, -1.9, 0.3), (-4.75, -2.1, 0.34), (-1.9, -4.65, 0.24), (3.0, -4.0, 0.22)]):
        rock(f'shore_rock_{i}', r, (x, y, -0.03), '#b9b6cc' if i % 2 else '#a5a2bd', seed=i + 4)

    hotspot(1, on_arc(90, RC - 0.45, FZ + 2.45))
    hotspot(2, gf.p(0, 0, 2.5))
    hotspot(3, (sx, sy, 1.9))
    hotspot(4, df.p(0.15, 0, T + 1.0))
    finish('college-advisor', mode, cam_loc=(-10.1, -15.5, 9.2), cam_target=(0.05, 0.0, 1.0), lens=50)
