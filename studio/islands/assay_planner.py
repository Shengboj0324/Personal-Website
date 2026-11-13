"""ZenithSync Assay Planner: which wells to measure next in an organoid drug-response
experiment. Pool plate with three chosen wells, shared-control threads, the held-back
audit plate, and the dose-response curve wall with its uncertainty band."""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Vector

from kit import *

# palette (from the project's demo UI)
INK_G = '#16352f'
ACCENT = '#116d55'
MINT = '#5c9784'
MINT_L = '#9cc7b3'
PALE = '#f1f5f1'
LINE = '#d9e4df'
NAVY = '#171e2b'
NAVY_B = '#2c3b58'
AMBER = '#f2a93b'
GLASS = '#dcefee'
LAB = '#f8faf6'
PEACH = '#ef9f8a'
MEDIUM = '#f6d8d0'

FLOOR = 0.075          # top of the tiled lab floor

# well-plate layout (plate-local units; u = columns, v = rows, z = up from plate bottom)
PW, PD, PT = 3.66, 1.80, 0.30
PITCH = 0.36
WELL_R = 0.145
WELL_DEPTH = 0.12
CTRL_U = -1.53
COL_U = [CTRL_U + 1.5 * PITCH + PITCH * c for c in range(8)]      # 8 doses
ROW_V = [-0.24, 0.12, 0.48]                                        # 3 replicates


class Frame:
    """A local coordinate frame: origin + XYZ euler rotation in degrees."""

    def __init__(self, origin, rot=(0, 0, 0)):
        self.o = Vector(origin)
        self.rot = tuple(rot)
        self.m = Euler([math.radians(a) for a in rot]).to_matrix()

    def pt(self, p):
        return tuple(self.o + self.m @ Vector(p))

    def r(self, local=(0, 0, 0)):
        e = (self.m @ Euler([math.radians(a) for a in local]).to_matrix()).to_euler()
        return tuple(math.degrees(a) for a in e)


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def rrect(w, d, r, n=5):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90),
                       (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _link(bm, name, m, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for c in (m if isinstance(m, (list, tuple)) else [m]):
        ob.data.materials.append(c if isinstance(c, bpy.types.Material) else mat(c))
    for p in me.polygons:
        p.use_smooth = smooth
    return ob


def ring(name, profile, loc, rot, m, verts=14):
    """Open revolved band (no caps). Profile runs inner-bottom -> over the top -> outer-bottom."""
    bm = bmesh.new()
    loops = [[bm.verts.new((r * math.cos(TAU * i / verts), r * math.sin(TAU * i / verts), z))
              for i in range(verts)] for r, z in profile]
    for a, b in zip(loops, loops[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], b[i], b[j], a[j]))
    ob = _link(bm, name, m)
    return place(ob, loc, rot)


def thin(ob, br=2):
    ob.data.bevel_resolution = br
    return ob


def sbox(name, size, loc, rot=(0, 0, 0), m=LAB, bevel=0.03):
    return box(name, size, loc, rot, m, bevel=bevel, seg=2)


def _clip(poly, x0, x1, y0, y1):
    """Sutherland-Hodgman: clip a polygon to an axis-aligned rectangle."""
    def cut(pts, axis, lim, keep_less):
        out = []
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            pin = (p[axis] <= lim) if keep_less else (p[axis] >= lim)
            qin = (q[axis] <= lim) if keep_less else (q[axis] >= lim)
            if pin:
                out.append(p)
            if pin != qin:
                t = (lim - p[axis]) / (q[axis] - p[axis])
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        return out
    for axis, lim, less in ((0, x0, False), (0, x1, True), (1, y0, False), (1, y1, True)):
        if len(poly) < 3:
            return []
        poly = cut(poly, axis, lim, less)
    return poly


def _area(poly):
    return 0.5 * sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))


def tiled_floor(outline, inside, pitch=0.8, gap=0.04, z_grout=0.045, z_top=FLOOR, ch=0.02):
    """Raised lab floor: a grout slab following `outline`, covered with chamfered tiles
    that are clipped to the same shape."""
    bm = bmesh.new()
    topv = [bm.verts.new((x * 1.006, y * 1.006, z_grout)) for x, y in outline]
    lowv = [bm.verts.new((x * 1.006, y * 1.006, -0.03)) for x, y in outline]
    bm.faces.new(topv)
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new((lowv[i], lowv[j], topv[j], topv[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _link(bm, 'floor_grout', '#c3d6cc', smooth=False)

    rng = random.Random(4)
    bm = bmesh.new()
    h = pitch / 2 - gap / 2
    for i in range(-9, 10):
        for j in range(-9, 10):
            cx, cy = i * pitch, j * pitch
            sq = [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]
            if all(inside(x, y) for x, y in sq):
                poly = sq
            else:
                poly = _clip(list(outline), cx - h, cx + h, cy - h, cy + h)
                clean = []
                for p in poly:
                    if not clean or math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 0.02:
                        clean.append(p)
                if len(clean) > 2 and math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < 0.02:
                    clean.pop()
                poly = clean
                if len(poly) < 3 or _area(poly) < 0.07:
                    continue
            n = len(poly)
            gx, gy = sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n
            lo = [bm.verts.new((x, y, z_grout - 0.005)) for x, y in poly]
            mid = [bm.verts.new((x, y, z_top - ch)) for x, y in poly]
            top = []
            for x, y in poly:
                d = math.hypot(gx - x, gy - y) or 1
                top.append(bm.verts.new((x + (gx - x) / d * ch * 1.3, y + (gy - y) / d * ch * 1.3, z_top)))
            k = (i + j) % 2
            if rng.random() < 0.09:
                k = 2
            faces = [bm.faces.new(top)]
            for a in range(n):
                b = (a + 1) % n
                faces.append(bm.faces.new((lo[a], lo[b], mid[b], mid[a])))
                faces.append(bm.faces.new((mid[a], mid[b], top[b], top[a])))
            for f in faces:
                f.material_index = k
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _link(bm, 'floor_tiles', ['#eaf2ed', '#dfebe5', '#cfe2d8'], smooth=False)


def tbox(name, size, loc, rot=(0, 0, 0), m=LAB, bevel=0.012):
    return box(name, size, loc, rot, m, bevel=bevel, seg=1)


def daisy(name, loc, h=0.24, petal=WHITE, heart=SUNSHINE):
    x, y, z = loc
    cyl(name + '_stem', 0.018, h, (x, y, z + h / 2), m=LEAF_DARK, verts=5, bevel=0)
    cyl(name + '_petal', 0.085, 0.04, (x, y, z + h), m=petal, verts=8, bevel=0.014, seg=1)
    cyl(name + '_heart', 0.04, 0.04, (x, y, z + h + 0.03), m=heart, r2=0.02, verts=6, bevel=0)


# ------------------------------------------------------------------ well plate
def well_plate(tag, F, glow=()):
    """Identical 8 x 3 treatment + 3 control plate. `glow` lists (col, row); col -1 = control."""
    body = prism(f'{tag}_body', rrect(PW, PD, 0.2), PT, F.pt((0, 0, 0)), F.rot, LAB, bevel=0.045)
    wells = [(c, r, CTRL_U if c < 0 else COL_U[c], ROW_V[r]) for c in range(-1, 8) for r in range(3)]
    cutters = [cyl(f'{tag}_cut_{c}_{r}', WELL_R, 0.3, F.pt((u, v, PT - WELL_DEPTH + 0.15)), F.rot,
                   '#c9d8d1', verts=16, bevel=0) for c, r, u, v in wells]
    cut = join(cutters, f'{tag}_cut')
    mod = body.modifiers.new('wells', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cut
    mod.solver = 'EXACT'
    try:
        mod.material_mode = 'TRANSFER'
    except Exception:
        pass
    body = join([body], f'{tag}_body')
    bpy.data.objects.remove(cut, do_unlink=True)
    for poly in body.data.polygons:          # the big pierced top and bottom faces shade flat
        if poly.area > 0.5:
            poly.use_smooth = False

    prof = [(WELL_R - 0.004, -0.02), (WELL_R - 0.002, 0.022), (WELL_R + 0.016, 0.034),
            (WELL_R + 0.034, 0.022), (WELL_R + 0.04, -0.005)]
    glow_m = mat('#7a4a10', 0.4, emit=1.15, emit_color=AMBER, name='amber_glow')
    glowing = []
    for c, r, u, v in wells:
        if (c, r) in glow:
            liq = cyl(f'{tag}_glowliq_{c}_{r}', WELL_R - 0.006, 0.1, F.pt((u, v, PT - 0.075)), F.rot,
                      glow_m, verts=16, bevel=0.02, seg=2)
            rim = ring(f'{tag}_glowrim_{c}_{r}', prof, F.pt((u, v, PT)), F.rot, glow_m, 16)
            g = join([liq, rim], f'{tag}_glow_{"ctrl" if c < 0 else c + 1}')
            set_origin(g, F.pt((u, v, PT)))
            glowing.append(g)
            continue
        if c < 0:
            lc, rc = '#3f6fae', NAVY_B
        else:
            resp = 1 / (1 + math.exp(0.8 * (c - 3.5)))          # response falls as dose rises
            t = 0.5 * (c / 7) + 0.5 * (1 - resp)
            lc, rc = mix('#14795c', '#dcefee', t), '#e3ebe6'
        cyl(f'{tag}_liq_{c}_{r}', WELL_R - 0.006, 0.07, F.pt((u, v, PT - 0.095)), F.rot,
            mat(lc, 0.3, coat=0.5), verts=14, bevel=0)
        ring(f'{tag}_rim_{c}_{r}', prof, F.pt((u, v, PT)), F.rot, rc)
    # divider that sets the control column apart, and a rising-dose wedge under the 8 columns
    sbox(f'{tag}_divider', (0.055, 1.22, 0.05), F.pt(((CTRL_U + COL_U[0]) / 2, 0.12, PT + 0.012)), F.rot, MINT, 0.02)
    w = COL_U[7] - COL_U[0] + 0.24
    prism(f'{tag}_wedge', [(0, 0), (w, 0), (w, 0.2), (0, 0.035)], 0.035, F.pt((COL_U[0] - 0.12, -0.74, PT - 0.005)),
          F.rot, MINT, bevel=0.012, seg=2)
    sphere(f'{tag}_ctrl_dot', 0.06, F.pt((CTRL_U, -0.64, PT)), (1, 1, 0.5), NAVY_B, 12)
    return body, glowing


def plate_station(tag, G, tilt, hf, colour, toe, glow=()):
    """Wedge plinth carrying a tilted plate. G is a ground frame (rotation about Z only)."""
    depth = PD * math.cos(math.radians(tilt)) + 0.34
    width = PW + 0.34
    hb = hf + depth * math.tan(math.radians(tilt))
    prism(f'{tag}_plinth', [(-depth / 2, 0), (depth / 2, 0), (depth / 2, hb), (-depth / 2, hf)], width,
          G.pt((-width / 2, 0, 0)), G.r((90, 0, 90)), colour, bevel=0.05)
    box(f'{tag}_toe', (width + 0.12, depth + 0.12, 0.09), G.pt((0, 0, 0.045)), G.rot, toe, bevel=0.03, seg=2)
    F = Frame(G.pt((0, 0, (hf + hb) / 2)), (tilt, 0, G.rot[2]))
    for k, u in enumerate((-1.1, 1.1)):           # stops that keep the plate from sliding
        sbox(f'{tag}_stop_{k}', (0.42, 0.08, 0.16), F.pt((u, -PD / 2 - 0.035, 0.06)), F.rot, STEEL, 0.025)
    body, glowing = well_plate(tag, F, glow)
    return F, glowing, (width, depth, hf, hb)


def thread(name, a, b, colour, r=0.022):
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    h = 0.40 + 0.25 * L
    up = Vector((0, 0, 1))
    pts = [a, a + d * 0.04 + up * h * 0.75, (a + b) / 2 + up * h * 1.12, b - d * 0.04 + up * h * 0.75, b]
    return thin(tube(name, [tuple(p) for p in pts], r, colour, res=7), 1)


# ------------------------------------------------------------------ props
def bottle(name, loc, r=0.2, h=0.7, cap=NAVY_B, liquid=MINT, fill=0.6, emit=0.0):
    x, y, z = loc
    gm = mat(GLASS, 0.25, coat=0.6)
    lathe(name, [(0, 0), (r * 0.9, 0), (r, 0.04), (r, h * 0.6), (r * 0.82, h * 0.72), (r * 0.42, h * 0.8),
                 (r * 0.42, h * 0.9), (0, h * 0.9)], loc, m=gm, verts=18)
    cyl(name + '_cap', r * 0.52, h * 0.14, (x, y, z + h * 0.93), m=cap, verts=14, bevel=0.02, seg=2)
    top = h * 0.6 * fill
    lm = mat(liquid, 0.35, emit=emit) if emit else mat(liquid, 0.35)
    liq = ring(name + '_liquid', [(r - 0.012, top), (r + 0.014, top - 0.014), (r + 0.014, 0.064), (r - 0.012, 0.05)],
               loc, (0, 0, 0), lm, 18)
    return liq


def tip_box(name, G, colour=MINT, open_lid=False):
    sbox(name, (0.62, 0.44, 0.26), G.pt((0, 0, 0.13)), G.rot, colour, 0.04)
    sbox(name + '_rack', (0.56, 0.38, 0.05), G.pt((0, 0, 0.275)), G.rot, LAB, 0.015)
    if open_lid:
        for i in range(5):
            for j in range(3):
                cyl(f'{name}_tip_{i}_{j}', 0.035, 0.06, G.pt((-0.2 + i * 0.1, -0.11 + j * 0.11, 0.315)), G.rot,
                    mat(GLASS, 0.3), verts=8, bevel=0)
        sbox(name + '_lid', (0.62, 0.05, 0.42), G.pt((0, 0.245, 0.44)), G.r((-12, 0, 0)), mat(GLASS, 0.3), 0.02)
    else:
        sbox(name + '_lid', (0.64, 0.46, 0.1), G.pt((0, 0, 0.34)), G.rot, mat(GLASS, 0.3), 0.03)


def small_tree(name, loc, h, crown, seed, leaf, leaf2):
    x, y, z = loc
    cyl(name + '_trunk', 0.09 * h, h * 0.62, (x, y, z + h * 0.31), m='#8a7560', r2=0.06 * h, verts=10, bevel=0)
    blob(name + '_c0', crown, (x, y, z + h * 0.8), (1, 1, 0.92), leaf, seed)
    blob(name + '_c1', crown * 0.62, (x + crown * 0.55, y - crown * 0.25, z + h * 0.62), (1, 1, 0.9), leaf2, seed + 1)
    blob(name + '_c2', crown * 0.55, (x - crown * 0.5, y + crown * 0.2, z + h * 0.95), (1, 1, 0.9), leaf, seed + 2)


# ------------------------------------------------------------------ build
RATIO = None        # set by build(): (x, y) -> distance from centre as a fraction of the island radius


def build(mode='preview'):
    global RATIO
    reset()
    setup_world()
    R, SQ = 5.4, (1.03, 0.99)
    base, radius_at = island_base(R=R, seed=23, top='#aedbb6', lip='#8cc49e', soil='#dccdb2', soil2='#bca98c',
                                  rock_c='#98a5a5', lobes=((2, 0.03), (3, 0.03), (5, 0.015)), squash=SQ)

    def rim(a_deg, k=1.0):
        a = math.radians(a_deg)
        rr = radius_at(a) * k
        return rr * SQ[0] * math.cos(a), rr * SQ[1] * math.sin(a)

    def ratio(x, y):
        a = math.atan2(y / SQ[1], x / SQ[0])
        return math.hypot(x / SQ[0], y / SQ[1]) / radius_at(a)

    RATIO = ratio
    SLAB = 0.875
    tiled_floor([rim(a, SLAB) for a in range(0, 360, 3)], lambda x, y: ratio(x, y) < SLAB)

    # ---------------------------------------------------------------- 1. pool plate + chosen wells
    PG = Frame((-0.6, -2.0, FLOOR), (0, 0, -8))
    glow = ((-1, 1), (2, 0), (4, 0))          # one control well + doses 3 and 5 of the front row
    PF, glowing, pdim = plate_station('pool', PG, 12, 0.3, MINT, INK_G, glow)
    for k, g in enumerate(glowing):
        animate(g, 'pulse', speed=1.1 + 0.15 * k)

    # ---------------------------------------------------------------- 2. shared-control threads
    thread_c = '#27344f'
    src = Vector(PF.pt((CTRL_U, ROW_V[1], PT + 0.16)))
    cyl('thread_stem', 0.03, 0.2, PF.pt((CTRL_U, ROW_V[1], PT + 0.07)), PF.rot, thread_c, verts=8, bevel=0)
    sphere('thread_knot', 0.075, tuple(src), m=thread_c, seg=12)
    targets = [(0, 2), (1, 1), (2, 0), (3, 2), (4, 0), (5, 1), (6, 2), (7, 1)]
    for k, (c, r) in enumerate(targets):
        end = PF.pt((COL_U[c], ROW_V[r], PT + 0.0))
        thread(f'thread_{k}', src, end, thread_c)
        sphere(f'thread_bead_{k}', 0.05, end, m=thread_c, seg=8)

    # ---------------------------------------------------------------- 3. audit plate behind a rope barrier
    AG = Frame((2.1, 1.6, FLOOR), (0, 0, -30))
    AF, _, adim = plate_station('audit', AG, 24, 0.55, '#51627f', NAVY_B)
    aw, ad, ahf, ahb = adim
    # back of the plinth: service hatch and vent slats
    sbox('audit_hatch', (1.3, 0.05, 0.8), AG.pt((-0.8, ad / 2 + 0.01, 0.62)), AG.rot, '#6b7c98', 0.03)
    sphere('audit_hatch_knob', 0.045, AG.pt((-0.3, ad / 2 + 0.05, 0.62)), m=STEEL, seg=8)
    for i in range(4):
        tbox(f'audit_vent_{i}', (0.9, 0.05, 0.06), AG.pt((1.0, ad / 2 + 0.01, 0.4 + i * 0.15)), AG.rot, NAVY_B, 0.015)
    posts = [(-2.2, 0.35), (-2.2, -1.42), (-0.74, -1.42), (0.74, -1.42), (2.2, -1.42), (2.2, 0.35)]
    for i, (u, d) in enumerate(posts):
        cyl(f'rope_base_{i}', 0.17, 0.06, AG.pt((u, d, 0.03)), m=NAVY_B, verts=12, bevel=0.02, seg=1)
        cyl(f'rope_post_{i}', 0.042, 0.7, AG.pt((u, d, 0.39)), m=STEEL, verts=8, bevel=0)
        sphere(f'rope_ball_{i}', 0.08, AG.pt((u, d, 0.78)), m=NAVY_B, seg=10)
    for i, ((u0, d0), (u1, d1)) in enumerate(zip(posts, posts[1:])):
        pts = [AG.pt((u0 + (u1 - u0) * t, d0 + (d1 - d0) * t, 0.68 - 0.2 * math.sin(math.pi * t))) for t in (0, 0.25, 0.5, 0.75, 1)]
        thin(tube(f'rope_{i}', pts, 0.032, MINT, res=5), 1)
    # padlock on the front rope: this plate is held back
    sbox('audit_lock', (0.24, 0.1, 0.2), AG.pt((0, -1.47, 0.34)), AG.rot, NAVY_B, 0.035)
    torus('audit_shackle', 0.075, 0.022, AG.pt((0, -1.47, 0.46)), AG.r((90, 0, 0)), STEEL, seg=12, ring=6)
    sphere('audit_keyhole', 0.028, AG.pt((0, -1.525, 0.34)), m=STEEL, seg=8)

    # ---------------------------------------------------------------- 4. curve wall
    rz = -5
    WG = Frame((-1.5, 2.3, FLOOR), (0, 0, rz))
    WF = Frame(WG.o, (-10, 0, rz))            # leans back like an easel
    for s in (-1, 1):
        sbox(f'wall_foot_{s}', (0.24, 1.5, 0.11), WG.pt((s * 1.2, 0.4, 0.055)), WG.rot, INK_G, 0.035)
        sbox(f'wall_leg_{s}', (0.14, 0.14, 0.95), WF.pt((s * 1.2, 0.02, 0.45)), WF.rot, INK_G, 0.03)
        thin(tube(f'wall_strut_{s}', [WF.pt((s * 1.2, 0.1, 2.35)), WG.pt((s * 1.2, 1.05, 0.1))], 0.045, INK_G,
                  smooth_curve=False), 2)
    sbox('wall_cross', (2.4, 0.08, 0.09), WF.pt((0, 0.02, 0.42)), WF.rot, INK_G, 0.025)
    thin(tube('wall_back_cross', [WG.pt((-1.2, 1.0, 0.14)), WG.pt((1.2, 1.0, 0.14))], 0.04, INK_G, smooth_curve=False), 2)
    Z0 = 0.82                                 # board bottom (frame-local)
    box('wall_board', (3.0, 0.12, 2.2), WF.pt((0, 0, Z0 + 1.1)), WF.rot, '#f6f9f6', bevel=0.03, seg=2)
    sbox('wall_frame_t', (3.16, 0.2, 0.1), WF.pt((0, 0, Z0 + 2.23)), WF.rot, INK_G, 0.035)
    sbox('wall_frame_b', (3.16, 0.2, 0.1), WF.pt((0, 0, Z0 - 0.03)), WF.rot, INK_G, 0.035)
    for s in (-1, 1):
        sbox(f'wall_frame_s{s}', (0.1, 0.2, 2.36), WF.pt((s * 1.53, 0, Z0 + 1.1)), WF.rot, INK_G, 0.035)
    sbox('wall_batten', (2.7, 0.07, 0.14), WF.pt((0, 0.09, Z0 + 1.5)), WF.rot, MINT, 0.02)
    sbox('wall_batten2', (2.7, 0.07, 0.14), WF.pt((0, 0.09, Z0 + 0.6)), WF.rot, MINT, 0.02)

    DF = -0.06                                # board front face (local d)
    ax_u, ax_z = -1.24, Z0 + 0.3
    thin(tube('axis_y', [WF.pt((ax_u, DF - 0.02, Z0 + 2.04)), WF.pt((ax_u, DF - 0.02, ax_z))], 0.028, INK_G,
              smooth_curve=False), 2)
    thin(tube('axis_x', [WF.pt((ax_u, DF - 0.02, ax_z)), WF.pt((1.36, DF - 0.02, ax_z))], 0.028, INK_G,
              smooth_curve=False), 2)
    sphere('axis_corner', 0.04, WF.pt((ax_u, DF - 0.02, ax_z)), m=INK_G, seg=8)
    STEP = 0.31
    marks = [-0.97 + STEP * i for i in range(8)]                  # the 8 measured doses
    pinch = [0.1, 0.1, 0.17, 0.1, 0.17, 0.1, 0.1, 0.1]           # doses 3 and 5 are the least pinned down
    WIDE, FLARE = 0.25, 0.31

    def resp(u):
        return Z0 + 0.7 + 1.08 / (1 + math.exp(4.3 * (u - 0.12)))

    def half(u):
        if u <= marks[0]:
            return pinch[0] + (FLARE - pinch[0]) * math.sin(min((marks[0] - u) / 0.22, 1) * math.pi / 2) ** 2
        if u >= marks[-1]:
            return pinch[-1] + (FLARE - pinch[-1]) * math.sin(min((u - marks[-1]) / 0.22, 1) * math.pi / 2) ** 2
        i = min(7, max(0, round((u - marks[0]) / STEP)))
        f = abs(u - marks[i]) / (STEP / 2)
        return pinch[i] + (WIDE - pinch[i]) * math.sin(f * math.pi / 2) ** 2

    u_a, u_b = -1.17, 1.36
    us = [u_a + (u_b - u_a) * i / 64 for i in range(65)]
    # translucent-looking band: a pale relief between the two limit curves
    bm = bmesh.new()
    rows = []
    for u in us:
        zt, zb = resp(u) + half(u), resp(u) - half(u)
        rows.append([bm.verts.new(WF.pt((u, DF - 0.03, zt))), bm.verts.new(WF.pt((u, DF - 0.03, zb))),
                     bm.verts.new(WF.pt((u, DF + 0.02, zb))), bm.verts.new(WF.pt((u, DF + 0.02, zt)))])
    for a, b in zip(rows, rows[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _link(bm, 'curve_band_fill', '#cde7da', smooth=False)
    thin(tube('curve_band_hi', [WF.pt((u, DF - 0.04, resp(u) + half(u))) for u in us], 0.024, MINT_L, smooth_curve=False), 1)
    thin(tube('curve_band_lo', [WF.pt((u, DF - 0.04, resp(u) - half(u))) for u in us], 0.024, MINT_L, smooth_curve=False), 1)
    thin(tube('curve_line', [WF.pt((u, DF - 0.07, resp(u))) for u in us[::2]], 0.052, ACCENT, smooth_curve=False), 3)
    for i, u in enumerate(marks):
        z, hh = resp(u), half(u) + 0.05
        cyl(f'curve_bar_{i}', 0.02, 2 * hh, WF.pt((u, DF - 0.115, z)), WF.rot, NAVY, verts=6, bevel=0)
        for s in (-1, 1):
            tbox(f'curve_cap_{i}_{s}', (0.12, 0.04, 0.04), WF.pt((u, DF - 0.115, z + s * hh)), WF.rot, NAVY, 0.01)
        sphere(f'curve_mark_{i}', 0.07, WF.pt((u, DF - 0.135, z)), m=AMBER if i in (2, 4) else NAVY_B, seg=12)
    # rising-dose wedge under the x axis (same symbol as on the plates)
    prism('axis_wedge', [(0, 0), (2.4, 0), (2.4, 0.15), (0, 0.035)], 0.04, WF.pt((marks[0] - 0.1, DF + 0.005, Z0 + 0.07)),
          WF.r((90, 0, 0)), MINT, bevel=0.012, seg=2)

    # model unit at the wall's foot, wired to the pool plate
    MB = Frame(WG.pt((0.35, -0.8, 0)), (0, 0, rz - 12))
    sbox('model_box', (0.62, 0.46, 0.5), MB.pt((0, 0, 0.25)), MB.rot, NAVY_B, 0.05)
    for i in range(3):
        tbox(f'model_vent_{i}', (0.36, 0.03, 0.045), MB.pt((-0.07, -0.235, 0.16 + i * 0.1)), MB.rot, MINT, 0.012)
    sphere('model_led', 0.045, MB.pt((0.22, -0.235, 0.38)), m=mat('#7ff0c0', 0.3, emit=4, emit_color='#5fe8b0'), seg=8)
    tbox('model_handle', (0.3, 0.08, 0.05), MB.pt((0, 0, 0.52)), MB.rot, STEEL, 0.02)

    # ---------------------------------------------------------------- 5. multichannel pipette on its stand
    P = Frame((3.0, -1.85, FLOOR), (0, 0, -33))
    box('pip_base', (1.75, 1.05, 0.12), P.pt((0, 0.1, 0.06)), P.rot, '#e3e9e8', bevel=0.04, seg=2)
    cyl('pip_post', 0.07, 3.15, P.pt((0, 0.5, 0.12 + 1.575)), P.rot, STEEL_DARK, verts=12, bevel=0.02, seg=1)
    sphere('pip_post_cap', 0.09, P.pt((0, 0.5, 3.28)), m=NAVY_B, seg=10)
    tbox('pip_arm', (0.12, 0.62, 0.1), P.pt((0, 0.24, 3.11)), P.rot, STEEL_DARK, 0.03)
    tbox('pip_fork_link', (0.1, 0.42, 0.08), P.pt((0, 0.3, 2.1)), P.rot, STEEL_DARK, 0.025)
    tbox('pip_fork', (0.52, 0.09, 0.1), P.pt((0, 0.1, 2.1)), P.rot, STEEL_DARK, 0.025)
    pd = -0.12
    box('pip_handle', (0.44, 0.38, 1.3), P.pt((0, pd, 2.625)), P.rot, MINT, bevel=0.15, seg=3)
    sbox('pip_hook', (0.16, 0.36, 0.09), P.pt((0, 0.2, 3.205)), P.rot, MINT, 0.035)
    cyl('pip_rod', 0.05, 0.26, P.pt((0, pd, 3.38)), P.rot, STEEL, verts=8, bevel=0)
    cyl('pip_knob', 0.16, 0.11, P.pt((0, pd, 3.55)), P.rot, NAVY_B, verts=14, bevel=0.03, seg=2)
    sbox('pip_eject', (0.13, 0.15, 0.1), P.pt((0.12, 0.02, 3.285)), P.rot, AMBER, 0.03)
    sbox('pip_window', (0.25, 0.05, 0.36), P.pt((0, pd - 0.18, 2.82)), P.rot, NAVY, 0.02)
    cyl('pip_dial', 0.08, 0.06, P.pt((0, pd - 0.185, 2.44)), P.r((90, 0, 0)), AMBER, verts=12, bevel=0.015, seg=1)
    prism('pip_shoulder', [(-0.86, 0), (0.86, 0), (0.21, 0.42), (-0.21, 0.42)], 0.32, P.pt((0, pd + 0.16, 1.62)),
          P.r((90, 0, 0)), LAB, bevel=0.05, seg=2)
    box('pip_manifold', (1.78, 0.36, 0.34), P.pt((0, pd, 1.47)), P.rot, LAB, bevel=0.07, seg=3)
    sbox('pip_band', (1.8, 0.38, 0.08), P.pt((0, pd, 1.44)), P.rot, ACCENT, 0.02)
    tips_u = [(i - 3.5) * 0.2 for i in range(8)]
    for i, u in enumerate(tips_u):
        cyl(f'pip_nozzle_{i}', 0.06, 0.18, P.pt((u, pd, 1.23)), P.rot, STEEL, verts=10, bevel=0)
        cyl(f'pip_tip_{i}', 0.022, 0.46, P.pt((u, pd, 0.93)), P.rot, mat(GLASS, 0.25, coat=0.5), r2=0.065, verts=10, bevel=0)
    box('pip_trough', (1.9, 0.5, 0.3), P.pt((0, pd, 0.27)), P.rot, mat(GLASS, 0.3, coat=0.4), bevel=0.05, seg=2)
    sbox('pip_trough_liquid', (1.72, 0.34, 0.03), P.pt((0, pd, 0.425)), P.rot, mat('#7fc3a8', 0.3, coat=0.5), 0.012)
    drop = lathe('pip_drop', [(0, -0.09), (0.055, -0.072), (0.085, -0.012), (0.06, 0.05), (0.02, 0.105), (0, 0.11)],
                 P.pt((tips_u[5], pd, 0.585)), m=mat('#2f9c7c', 0.25, coat=0.6), verts=12)
    animate(drop, 'bob', amp=0.03, speed=1.6)

    # ---------------------------------------------------------------- 6. organoid dish under the microscope
    M = Frame((-3.45, -0.65, FLOOR), (0, 0, 4))
    box('scope_base', (1.15, 1.4, 0.16), M.pt((0, 0, 0.08)), M.rot, LAB, bevel=0.06, seg=3)
    cyl('scope_stage', 0.5, 0.04, M.pt((0, -0.18, 0.17)), M.rot, NAVY_B, verts=28, bevel=0.012, seg=1)
    dz = 0.19
    lathe('dish', [(0, 0), (0.41, 0), (0.44, 0.03), (0.44, 0.16), (0.405, 0.16), (0.405, 0.05), (0, 0.05)],
          M.pt((0, -0.18, dz)), m=mat(GLASS, 0.25, coat=0.6), verts=28)
    cyl('dish_medium', 0.4, 0.05, M.pt((0, -0.18, dz + 0.07)), M.rot, mat(MEDIUM, 0.3, coat=0.4), verts=24, bevel=0)
    orgs = []
    for i, (du, dd, r) in enumerate([(0, 0, 0.13), (0.17, 0.05, 0.1), (-0.15, 0.08, 0.095), (0.04, -0.17, 0.09),
                                     (-0.13, -0.11, 0.075), (0.16, -0.13, 0.07), (0.02, 0.19, 0.075)]):
        orgs.append(blob(f'organoid_{i}', r, M.pt((du, -0.18 + dd, dz + 0.095 + r * 0.62)), (1, 1, 0.85),
                         mat(PEACH if i % 3 else '#f4b3a0', 0.5, sheen=0.3), seed=20 + i, bumps=0.3, seg=3))
    organoids = join(orgs, 'organoids')
    set_origin(organoids, M.pt((0, -0.18, dz + 0.095)))
    animate(organoids, 'bob', amp=0.018, speed=0.8)
    cyl('scope_pillar', 0.09, 1.7, M.pt((0, 0.5, 0.16 + 0.85)), M.rot, STEEL_DARK, verts=12, bevel=0.02, seg=1)
    sbox('scope_carriage', (0.36, 0.3, 0.42), M.pt((0, 0.5, 1.52)), M.rot, LAB, 0.05)
    cyl('scope_knob', 0.11, 0.56, M.pt((0, 0.5, 1.45)), M.r((0, 90, 0)), NAVY_B, verts=12, bevel=0.03, seg=1)
    sbox('scope_arm', (0.3, 0.75, 0.2), M.pt((0, 0.13, 1.62)), M.rot, LAB, 0.05)
    box('scope_head', (0.54, 0.52, 0.42), M.pt((0, -0.18, 1.64)), M.rot, MINT, bevel=0.1, seg=3)
    cyl('scope_objective', 0.12, 0.38, M.pt((0, -0.18, 1.26)), M.rot, STEEL_DARK, r2=0.19, verts=14, bevel=0.02, seg=1)
    torus('scope_ringlight', 0.17, 0.04, M.pt((0, -0.18, 1.08)), M.rot,
          mat('#fff6d8', 0.3, emit=3.5, emit_color='#fff0c0'), seg=16, ring=6)
    for s in (-1, 1):
        cyl(f'scope_eye_{s}', 0.075, 0.5, M.pt((s * 0.14, -0.39, 2.0)), M.r((35, 0, 0)), LAB, verts=10, bevel=0.02, seg=1)
        cyl(f'scope_cup_{s}', 0.095, 0.09, M.pt((s * 0.14, -0.53, 2.2)), M.r((35, 0, 0)), NAVY, verts=10, bevel=0.02, seg=1)

    # lab stool in front of the microscope
    sx, sy = M.pt((0.2, -1.3, 0))[:2]
    for i in range(5):
        a = TAU * i / 5 + 0.3
        tbox(f'stool_leg_{i}', (0.34, 0.07, 0.05), (sx + 0.17 * math.cos(a), sy + 0.17 * math.sin(a), FLOOR + 0.09),
             (0, 0, math.degrees(a)), STEEL_DARK, 0.02)
        sphere(f'stool_wheel_{i}', 0.045, (sx + 0.32 * math.cos(a), sy + 0.32 * math.sin(a), FLOOR + 0.045), m=NAVY, seg=8)
    cyl('stool_post', 0.045, 0.62, (sx, sy, FLOOR + 0.4), m=STEEL, verts=8, bevel=0)
    torus('stool_ring', 0.22, 0.022, (sx, sy, FLOOR + 0.36), m=STEEL, seg=16, ring=6)
    for i in range(3):
        a = TAU * i / 3
        cyl(f'stool_spoke_{i}', 0.016, 0.22, (sx + 0.11 * math.cos(a), sy + 0.11 * math.sin(a), FLOOR + 0.36),
            (0, 90, math.degrees(a)), STEEL, verts=6, bevel=0)
    cyl('stool_seat', 0.33, 0.07, (sx, sy, FLOOR + 0.73), m=STEEL_DARK, verts=18, bevel=0.02, seg=1)
    cyl('stool_cushion', 0.31, 0.1, (sx, sy, FLOOR + 0.81), m=ACCENT, verts=18, bevel=0.045, seg=3)

    # ---------------------------------------------------------------- rolling cart with reagents
    crz = 76
    C = Frame((-3.6, 1.3, FLOOR), (0, 0, crz))
    for i, (u, d) in enumerate(((-0.56, -0.3), (0.56, -0.3), (0.56, 0.3), (-0.56, 0.3))):
        sphere(f'cart_wheel_{i}', 0.075, C.pt((u, d, 0.075)), m=NAVY, seg=8)
        cyl(f'cart_leg_{i}', 0.032, 1.0, C.pt((u, d, 0.63)), C.rot, STEEL, verts=8, bevel=0)
    sbox('cart_shelf_lo', (1.28, 0.74, 0.07), C.pt((0, 0, 0.36)), C.rot, '#e3e9e8', 0.025)
    sbox('cart_shelf_hi', (1.28, 0.74, 0.07), C.pt((0, 0, 1.1)), C.rot, '#e3e9e8', 0.025)
    thin(tube('cart_handle', [C.pt((0.56, -0.3, 1.1)), C.pt((0.82, -0.3, 1.32)), C.pt((0.82, 0.3, 1.32)), C.pt((0.56, 0.3, 1.1))],
              0.03, STEEL_DARK, smooth_curve=False), 2)
    top = 1.135
    bottle('cart_bottle_a', C.pt((-0.36, 0.1, top)), 0.17, 0.62, NAVY_B, '#6fb79c', 0.7)
    bottle('cart_bottle_b', C.pt((0.02, -0.1, top)), 0.13, 0.46, AMBER, '#3f6fae', 0.5)
    bottle('cart_bottle_c', C.pt((0.3, 0.14, top)), 0.11, 0.38, MINT, '#e9cf9a', 0.6)
    tip_box('cart_tips', Frame(C.pt((-0.2, 0, 0.395)), (0, 0, crz + 6)), MINT)
    sbox('cart_crate', (0.4, 0.5, 0.3), C.pt((0.36, 0, 0.545)), C.rot, '#51627f', 0.04)

    # ---------------------------------------------------------------- ground detail
    # big reagent bottle whose liquid pulses, with two smaller ones
    bx, by = 2.0, -0.95
    big_liq = bottle('reagent_big', (bx, by, FLOOR), 0.25, 0.92, NAVY_B, '#39b48a', 0.66, emit=1.6)
    animate(big_liq, 'pulse', speed=0.7)
    bottle('reagent_mid', (bx + 0.44, by + 0.22, FLOOR), 0.16, 0.6, MINT, '#3f6fae', 0.5)
    bottle('reagent_small', (bx + 0.08, by + 0.45, FLOOR), 0.12, 0.42, AMBER, '#e9cf9a', 0.55)

    # tip boxes near the pipette
    tip_box('tips_a', Frame((2.25, -3.2, FLOOR), (0, 0, 14)), MINT)
    tip_box('tips_b', Frame((2.27, -3.22, FLOOR + 0.39), (0, 0, 24)), '#51627f')
    tip_box('tips_open', Frame((2.95, -3.05, FLOOR), (0, 0, -22)), MINT, open_lid=True)

    # timer: a round dial on a tilted body, in front of the pool plate
    T = Frame((1.55, -3.75, FLOOR + 0.275), (68, 0, 12))
    cyl('timer_body', 0.27, 0.15, T.pt((0, 0, 0)), T.rot, ACCENT, verts=20, bevel=0.04, seg=2)
    cyl('timer_face', 0.215, 0.03, T.pt((0, 0, 0.075)), T.rot, LAB, verts=20, bevel=0.008, seg=1)
    for i in range(12):
        a = TAU * i / 12
        box(f'timer_tick_{i}', (0.03, 0.045 if i % 3 else 0.075, 0.03),
            T.pt((0.172 * math.sin(a), 0.172 * math.cos(a), 0.088)), T.r((0, 0, -math.degrees(a))), NAVY, bevel=0)
    tbox('timer_hand', (0.04, 0.16, 0.03), T.pt((0.045, 0.055, 0.103)), T.r((0, 0, -40)), AMBER, 0.008)
    sphere('timer_pin', 0.03, T.pt((0, 0, 0.1)), m=NAVY, seg=8)
    cyl('timer_button', 0.05, 0.1, T.pt((0, 0.3, 0)), T.r((90, 0, 0)), AMBER, verts=10, bevel=0.015, seg=1)
    tbox('timer_stand', (0.3, 0.3, 0.07), (1.59, -3.63, FLOOR + 0.035), (0, 0, 12), NAVY_B, 0.02)

    # tube rack and wash bottle in front of the pool plate
    TR = Frame((-1.75, -3.8, FLOOR), (0, 0, 9))
    sbox('rack_base', (0.95, 0.34, 0.06), TR.pt((0, 0, 0.03)), TR.rot, MINT, 0.02)
    sbox('rack_top', (0.95, 0.34, 0.05), TR.pt((0, 0, 0.3)), TR.rot, MINT, 0.02)
    for s in (-1, 1):
        tbox(f'rack_end_{s}', (0.06, 0.34, 0.3), TR.pt((s * 0.445, 0, 0.165)), TR.rot, MINT, 0.02)
    for i in range(5):
        u = -0.32 + i * 0.16
        cyl(f'rack_tube_{i}', 0.055, 0.44, TR.pt((u, 0, 0.28)), TR.rot, mat(GLASS, 0.25, coat=0.5), verts=10, bevel=0.02, seg=1)
        cyl(f'rack_cap_{i}', 0.068, 0.08, TR.pt((u, 0, 0.53)), TR.rot, (ACCENT, NAVY_B, AMBER, NAVY_B, ACCENT)[i], verts=10, bevel=0.015, seg=1)
    wx, wy = -2.55, -3.45
    lathe('wash_bottle', [(0, 0), (0.15, 0), (0.17, 0.04), (0.17, 0.36), (0.1, 0.46), (0.1, 0.5), (0, 0.5)],
          (wx, wy, FLOOR), m=mat(LAB, 0.35, coat=0.3), verts=16)
    cyl('wash_cap', 0.11, 0.08, (wx, wy, FLOOR + 0.53), m=ACCENT, verts=12, bevel=0.02, seg=1)
    thin(tube('wash_spout', [(wx, wy, FLOOR + 0.55), (wx, wy, FLOOR + 0.72), (wx + 0.08, wy - 0.05, FLOOR + 0.78),
                             (wx + 0.26, wy - 0.16, FLOOR + 0.7)], 0.024, ACCENT, res=6), 1)

    # gas cylinder and storage crates at the back
    gx, gy = 0.3, 3.75
    cyl('gas_base', 0.27, 0.07, (gx, gy, FLOOR + 0.035), m=NAVY_B, verts=16, bevel=0.02, seg=1)
    lathe('gas_cylinder', [(0, 0), (0.2, 0), (0.21, 0.04), (0.21, 1.15), (0.17, 1.3), (0.08, 1.38), (0.08, 1.46), (0, 1.46)],
          (gx, gy, FLOOR + 0.07), m=STEEL, verts=18)
    ring('gas_band', [(0.2, 1.02), (0.222, 1.0), (0.222, 0.86), (0.2, 0.84)], (gx, gy, FLOOR + 0.07), (0, 0, 0), ACCENT, 18)
    cyl('gas_valve', 0.06, 0.12, (gx, gy, FLOOR + 1.58), m=NAVY_B, verts=10, bevel=0.02, seg=1)
    cyl('gas_wheel', 0.11, 0.04, (gx, gy, FLOOR + 1.66), m=AMBER, verts=10, bevel=0.012, seg=1)
    sbox('crate_a', (0.62, 0.46, 0.4), WG.pt((0.25, 0.55, 0.2)), WG.r((0, 0, 12)), '#51627f', 0.04)
    sbox('crate_a_lid', (0.66, 0.5, 0.07), WG.pt((0.25, 0.55, 0.42)), WG.r((0, 0, 12)), '#e3e9e8', 0.025)
    sbox('crate_b', (0.5, 0.4, 0.34), WG.pt((-0.45, 0.6, 0.17)), WG.r((0, 0, -9)), MINT, 0.04)
    sbox('crate_b_lid', (0.54, 0.44, 0.07), WG.pt((-0.45, 0.6, 0.36)), WG.r((0, 0, -9)), '#e3e9e8', 0.025)

    # floor grating in the aisle
    GR = Frame((-0.75, 0.2, FLOOR), (0, 0, -8))
    tbox('grate_frame', (1.5, 0.56, 0.03), GR.pt((0, 0, 0.012)), GR.rot, STEEL_DARK, 0.012)
    box('grate_pit', (1.36, 0.42, 0.03), GR.pt((0, 0, 0.016)), GR.rot, NAVY, bevel=0)
    for i in range(9):
        tbox(f'grate_bar_{i}', (0.07, 0.42, 0.035), GR.pt((-0.6 + i * 0.15, 0, 0.022)), GR.rot, STEEL, 0.012)

    # cables on the floor
    cz = FLOOR + 0.03
    back = PG.pt((0.9, pdim[1] / 2 + 0.02, 0.12))
    m0 = MB.pt((0.2, -0.25, 0.1))
    thin(tube('cable_model_pool', [m0, (m0[0] + 0.1, m0[1] - 0.3, cz), (-0.2, 0.9, cz), (0.45, 0.35, cz), (0.7, -0.3, cz),
                                   (0.5, -0.75, cz), (back[0], back[1] + 0.25, cz), back], 0.032, NAVY_B, res=6), 1)
    thin(tube('cable_model_wall', [MB.pt((0.3, 0.1, 0.12)), MB.pt((0.6, 0.2, 0.03)), WG.pt((1.2, -0.25, 0.03)),
                                   WG.pt((1.2, 0.02, 0.2))], 0.028, NAVY_B, res=6), 1)
    thin(tube('cable_scope', [M.pt((0.3, 0.7, 0.1)), M.pt((0.42, 0.95, 0.03)), (-2.8, 1.1, cz), (-2.95, 1.7, cz),
                              WG.pt((-1.2, -0.4, 0.03)), WG.pt((-1.2, -0.05, 0.2))], 0.028, '#51627f', res=6), 1)

    # small potted plant
    px, py = -2.3, 0.45
    lathe('plant_pot', [(0, 0), (0.17, 0), (0.24, 0.3), (0.26, 0.3), (0.26, 0.36), (0.2, 0.36), (0.2, 0.3), (0, 0.3)],
          (px, py, FLOOR), m=LAB, verts=16)
    cyl('plant_soil', 0.2, 0.04, (px, py, FLOOR + 0.31), m='#7a6a58', verts=12, bevel=0)
    for i in range(6):
        a = TAU * i / 6 + 0.4
        lean = 22 + 10 * (i % 2)
        sphere(f'plant_leaf_{i}', 0.2, (px + 0.12 * math.cos(a), py + 0.12 * math.sin(a), FLOOR + 0.56 + 0.05 * (i % 2)),
               (0.32, 0.12, 1.0), LEAF if i % 2 else '#74c07a', 8, rot=(lean * math.sin(a), -lean * math.cos(a), math.degrees(a)))

    # ---------------------------------------------------------------- planted edge
    trees = [(100, 1.6, 0.6), (42, 1.4, 0.52), (171, 1.3, 0.5)]
    for i, (a, h, c) in enumerate(trees):
        x, y = rim(a, 0.94)
        small_tree(f'tree_{i}', (x, y, 0), h, c, 30 + i * 3, ('#6bb878', LEAF, '#7cc48a')[i], ('#4b9c69', LEAF_DARK, '#58a66b')[i])
    rng = random.Random(5)
    a = 0.0
    k = 0
    n_rock = 0
    while a < 352:
        kind = rng.choice(['bush', 'tuft', 'tuft', 'flower', 'flower', 'rock', 'bush'])
        x, y = rim(a, rng.uniform(0.94, 0.955))
        if not any(abs((a - t[0] + 180) % 360 - 180) < 8 for t in trees):
            if kind == 'rock' and n_rock >= 4:
                kind = 'tuft'
            if kind == 'bush':
                r = rng.uniform(0.2, 0.3)
                blob(f'bush_{k}', r, (x, y, r * 0.5), (1.2, 1.1, 0.75), rng.choice([LEAF, '#74c07a', '#8fcf95']), k, seg=3)
            elif kind == 'tuft':
                grass_tuft(f'tuft_{k}', (x, y, 0), h=rng.uniform(0.2, 0.3), n=4, m='#6fb57c', seed=k)
            elif kind == 'flower':
                for j in range(2):
                    fx, fy = rim(a + j * 3.2, 0.94 + 0.015 * j)
                    daisy(f'flower_{k}_{j}', (fx, fy, 0), 0.2 + 0.06 * j, (WHITE, AMBER, '#f7fbf8')[(k + j) % 3])
            else:
                n_rock += 1
                rock(f'rock_{k}', rng.uniform(0.16, 0.24), (x, y, 0.02), '#aab5b3' if k % 2 else '#98a5a5', seed=k)
        a += rng.uniform(6.5, 10.5)
        k += 1
    for i, (a, r) in enumerate([(-62, 0.36), (118, 0.3), (205, 0.42), (15, 0.3)]):
        x, y = rim(a, 0.99)
        rock(f'shore_rock_{i}', r, (x, y, WATER_Z + 0.12), '#aab5b3' if i % 2 else '#98a5a5', seed=40 + i)

    # one marker buoy off the front-left shore
    bx2, by2 = rim(-14, 1.15)
    buoy = join([lathe('buoy_body', [(0, -0.22), (0.2, -0.16), (0.26, 0.0), (0.2, 0.2), (0.07, 0.3), (0.07, 0.5), (0, 0.5)],
                       (bx2, by2, WATER_Z + 0.06), m=MINT, verts=18),
                 torus('buoy_band', 0.262, 0.022, (bx2, by2, WATER_Z + 0.06), m=LAB, seg=18, ring=6),
                 sphere('buoy_light', 0.06, (bx2, by2, WATER_Z + 0.6), m=mat('#eafff4', 0.3, emit=3.5, emit_color='#bff5dc'), seg=10)],
                'buoy')
    set_origin(buoy, (bx2, by2, WATER_Z))
    animate(buoy, 'bob', amp=0.05, speed=0.9, tilt=5)

    # ---------------------------------------------------------------- hotspots
    hotspot(1, PF.pt(((COL_U[2] + COL_U[4]) / 2, ROW_V[0], PT + 0.55)))
    hotspot(2, PF.pt(((CTRL_U + COL_U[5]) / 2, ROW_V[1], PT + 1.55)))
    hotspot(3, WF.pt((0, 0, Z0 + 2.55)))
    hotspot(4, AF.pt((0, 0.1, PT + 0.75)))

    finish('assay-planner', mode, cam_loc=(-10.0, -14.3, 8.8), cam_target=(0.1, -0.3, 0.6), lens=50)
