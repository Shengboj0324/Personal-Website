"""Hero sailboat: the autonomous trimaran that carries the visitor between islands.

Origin at the waterline amidships, bow toward +Y, waterline z = 0.
`build_trimaran()` is reused by islands/sailbot.py (cradle boat and desk model).
"""
import math

import bmesh
import bpy
from mathutils import Matrix

import kit as K
from kit import *

HULL = WHITE
DECK = '#e6dfcd'
SPAR = '#2b3b3f'
CLOTH = '#f4ecd8'
SEAM = '#d9cba9'
TEAL = '#325963'
TEAL_DEEP = '#244a52'
PANEL = '#27445a'
ROPE = '#e9dcc3'

MAST_Y = 0.25          # the mast is stepped on the forward crossbeam
AFT_AKA_Y = -0.45
AMA_X = 0.69           # 0.6 m at 1.15 units per metre
AMA_Y = -0.06
BOOM_Z = 0.52
MAST_TOP = 2.56
SHEET_R = 0.70         # mainsheet attachment, measured along the boom from the mast

_SECTIONS = {
    9: (0.0, 0.10, 0.27, 0.45, 0.62, 0.77, 0.89, 0.97, 1.0),
    7: (0.0, 0.10, 0.27, 0.50, 0.75, 0.93, 1.0),
    5: (0.0, 0.12, 0.30, 0.70, 1.0),
}


# ---------------------------------------------------------------- helpers
def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, r2=None, verts=32, bevel=0.04, seg=1):
    """kit.cyl with a single bevel segment: these parts are all small."""
    return K.cyl(name, r, h, loc, rot, m, r2, verts, bevel, seg)


def wire(name, points, r=0.008, m=STEEL_DARK, smooth=False, res=4):
    """Thin line or rope: kit.tube with a six-sided section."""
    ob = tube(name, points, r, m, smooth_curve=smooth, res=res)
    ob.data.bevel_resolution = 1
    return ob


def move(objs, loc=(0, 0, 0), rot_z=0.0, scale=1.0, rot_x=0.0):
    """Place a group built at the origin: scale, pitch (X), heading (Z), translate."""
    m = (Matrix.Translation(loc) @ Matrix.Rotation(math.radians(rot_z), 4, 'Z')
         @ Matrix.Rotation(math.radians(rot_x), 4, 'X') @ Matrix.Scale(scale, 4))
    flat = []
    for o in objs:
        flat.extend(o if isinstance(o, (list, tuple)) else [o])
    for o in flat:
        o.matrix_basis = m @ o.matrix_basis
    return flat


def plate_yz(name, outline, thick, x=0.0, m=WHITE, bevel=0.008):
    """Thin plate whose outline is given in the (Y, Z) plane, centred on x."""
    return prism(name, outline, thick, (x - thick / 2, 0, 0), (90, 0, 90), m, bevel=bevel, seg=2)


def _hull(name, length, half_beam, free_mid, free_bow, draft, x0=0.0, y0=0.0, stern_beam=0.62,
          stations=22, pts=9, exp=2.4, bevel=0.012):
    """Lofted hull: pointed raked bow, rounded bilge, flat transom, crowned deck.
    Slots: 0 topsides, 1 stripe under the sheer, 2 deck."""
    S = _SECTIONS[pts]
    n = len(S)
    tm = 0.42                       # station of maximum beam
    bm = bmesh.new()
    loops = []
    for i in range(stations):
        t = i / (stations - 1)
        if t < tm:
            ua, u = (tm - t) / tm, 0.0
            k = stern_beam + (1 - stern_beam) * math.cos(math.pi / 2 * ua)
        else:
            ua, u = 0.0, (t - tm) / (1 - tm)
            k = 1 - u ** 2.2
        b = max(half_beam * k, 0.011)
        sheer = free_mid + (free_bow - free_mid) * u ** 2 + 0.012 * ua ** 2
        keel = -draft * (1 - 0.85 * u ** 2.5) * (1 - 0.6 * ua ** 2)
        y = -length / 2 + length * t

        def vert(x, z):
            yy = y + (0.34 * u ** 3 - 0.12 * ua ** 3) * (z - keel)
            return bm.verts.new((x0 + x, y0 + yy, z))

        side = [(b * (1 - s ** exp) ** (1 / exp), sheer - s * (sheer - keel)) for s in S]
        ring = [vert(-x, z) for x, z in side]
        ring += [vert(x, z) for x, z in reversed(side[:-1])]
        ring.append(vert(0, sheer + 0.13 * half_beam * k))
        loops.append(ring)
    m = 2 * n
    for a, b_ in zip(loops, loops[1:]):
        for q in range(m):
            f = bm.faces.new((a[q], a[(q + 1) % m], b_[(q + 1) % m], b_[q]))
            if q in (1, m - 4):
                f.material_index = 1
            elif q >= m - 2:
                f.material_index = 2
    bm.faces.new(loops[0])
    bm.faces.new(list(reversed(loops[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = K._obj_from_bmesh(bm, name)
    for c in (HULL, CORAL, DECK):
        ob.data.materials.append(mat(c))
    K._finish(ob, name, None, angle=42)
    K._bevel(ob, bevel, 2)
    return ob


def _aka(name, y, width=0.12, thick=0.05, z_end=0.085, z_mid=0.2, m=HULL, n=14, soft=True):
    """Arched crossbeam from ama deck to ama deck, resting on the main hull."""
    half = AMA_X + 0.055
    xs = [-half + 2 * half * i / n for i in range(n + 1)]

    def zb(x):
        return z_end + (z_mid - z_end) * math.cos(math.pi / 2 * x / half) ** 0.75

    outline = [(x, zb(x)) for x in xs] + [(x, zb(x) + thick) for x in reversed(xs)]
    return prism(name, outline, width, (0, y + width / 2, 0), (90, 0, 0), m, bevel=0.016 if soft else 0, seg=2)


def _sail_cloth(name, foot, height, z0, nu=8, rows=4, depth=0.13, twist=11.0):
    """Bellied triangular mainsail in four panels (the top one coral) with stitched seams.
    The luff runs up the mast and the belly is toward +X."""
    edges = (0.0, 0.24, 0.48, 0.72, 1.0)
    seam = 0.007
    vs, slots = [0.0], []
    for k in range(4):
        lo = edges[k] + (seam if k else 0.0)
        hi = edges[k + 1] - (seam if k < 3 else 0.0)
        if k:
            vs.append(lo); slots.append(1)                 # seam strip
        for r in range(1, rows + 1):
            vs.append(lo + (hi - lo) * r / rows); slots.append(2 if k == 3 else 0)
    bm = bmesh.new()
    grid = []
    for v in vs:
        chord = foot * (1 - v) + 0.09 * v + 0.13 * math.sin(math.pi * v ** 0.9)
        tw = math.radians(twist) * v
        row = []
        for i in range(nu + 1):
            u = i / nu
            d = 0.04 + u * chord
            x = depth * (0.55 + 0.45 * math.sin(math.pi * v)) * chord * (u ** 0.75) * (1 - u) / 0.3027
            row.append(bm.verts.new((x * math.cos(tw) + d * math.sin(tw),
                                     MAST_Y - d * math.cos(tw) + x * math.sin(tw),
                                     z0 + v * height)))
        grid.append(row)
    for j, slot in enumerate(slots):
        for i in range(nu):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.material_index = slot
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = K._obj_from_bmesh(bm, name)
    # a little self-illumination stands in for light coming through the cloth
    ob.data.materials.append(mat(CLOTH, rough=0.85, sheen=0.3, emit=0.3))
    ob.data.materials.append(mat(SEAM, rough=0.85, emit=0.2))
    ob.data.materials.append(mat(CORAL, rough=0.85, sheen=0.3, emit=0.3))
    K._finish(ob, name, None, angle=60)
    so = ob.modifiers.new('thick', 'SOLIDIFY')
    so.thickness = 0.03
    so.offset = 0.0
    return ob


def _cleat(name, x, y, z, rot_z=0):
    return [cyl(name + '_p', 0.012, 0.03, (x, y, z + 0.015), m=STEEL_DARK, verts=6, bevel=0),
            box(name + '_h', (0.022, 0.085, 0.018), (x, y, z + 0.036), (0, 0, rot_z), STEEL, bevel=0.008, seg=2)]


# ---------------------------------------------------------------- the boat
def build_trimaran(prefix='boat', lod='hero', sail='set', boom_angle=14.0, vane_angle=36.0):
    """Build the trimaran at the origin. lod: 'hero' | 'mid' | 'mini'. sail: 'set' | 'furled'.
    Returns {'static': [...], 'sail': ob, 'rudder': ob, 'vane': ob} (nothing is tagged)."""
    p = prefix
    st, pts = {'hero': (22, 9), 'mid': (16, 7), 'mini': (9, 5)}[lod]
    hero, mini = lod == 'hero', lod == 'mini'
    rv = 6 if mini else 10                     # round-section vertex count
    static = []

    # --- hulls: vaka 1.8 m, amas 1.5 m, 0.6 m to each side
    static.append(_hull(p + '_vaka', 1.96, 0.17, 0.19, 0.27, 0.14, stations=st, pts=pts, bevel=0 if mini else 0.012))
    for s, tag in ((-1, 'port'), (1, 'stbd')):
        static.append(_hull(f'{p}_ama_{tag}', 1.70, 0.078, 0.105, 0.15, 0.07, x0=s * AMA_X, y0=AMA_Y,
                            stern_beam=0.5, stations=max(8, st - 4), pts=7 if hero else 5, bevel=0 if mini else 0.008))
    aka_n = {'hero': 14, 'mid': 10, 'mini': 6}[lod]
    static.append(_aka(p + '_aka_fore', MAST_Y, n=aka_n, soft=not mini))
    static.append(_aka(p + '_aka_aft', AFT_AKA_Y, n=aka_n, soft=not mini))

    # --- mast and standing rigging
    static.append(cyl(p + '_mast', 0.032, MAST_TOP - 0.24, (0, MAST_Y, (MAST_TOP + 0.24) / 2), m=SPAR,
                      r2=0.017, verts=rv + 2, bevel=0.004))
    if not mini:
        static.append(cyl(p + '_mast_step', 0.055, 0.05, (0, MAST_Y, 0.265), m=STEEL_DARK, verts=rv + 2, bevel=0.012))
    if not mini:
        static.append(wire(p + '_forestay', [(0, MAST_Y + 0.02, 2.05), (0, 0.97, 0.275)]))
        for s, tag in ((-1, 'port'), (1, 'stbd')):
            static.append(wire(f'{p}_shroud_{tag}', [(s * 0.012, MAST_Y, 1.8), (s * AMA_X, MAST_Y - 0.02, 0.15)]))
            static.append(sphere(f'{p}_chainplate_{tag}', 0.02, (s * AMA_X, MAST_Y - 0.02, 0.145), m=STEEL_DARK, seg=8))
        static.append(sphere(p + '_stemhead', 0.022, (0, 0.97, 0.275), m=STEEL_DARK, seg=8))

    # --- sail and boom (one moving object, pivot on the mast axis at boom height)
    boom_len = 1.22
    sail_parts = []
    if sail == 'set':
        cloth = _sail_cloth(p + '_cloth', 1.12, 1.9, BOOM_Z + 0.045,
                            nu=4 if mini else 8, rows=1 if mini else 3)
        sail_parts.append(cloth)
        if not mini:                               # hoops that hold the luff to the mast
            for i in range(5):
                sail_parts.append(torus(f'{p}_hoop_{i}', 0.047, 0.009, (0, MAST_Y, BOOM_Z + 0.2 + i * 0.4), m=STEEL_DARK,
                                        seg=10, ring=4))
    sail_parts.append(cyl(p + '_boom', 0.024, boom_len, (0, MAST_Y - 0.02 - boom_len / 2, BOOM_Z), (90, 0, 0),
                          SPAR, verts=rv, bevel=0.006))
    sail_parts.append(sphere(p + '_gooseneck', 0.04, (0, MAST_Y, BOOM_Z), m=STEEL_DARK, seg=8))
    if sail == 'furled':
        sail_parts.append(cyl(p + '_furl', 0.06, 1.02, (0, MAST_Y - 0.62, BOOM_Z + 0.07), (90, 0, 0), CLOTH,
                              r2=0.045, verts=12, bevel=0.03))
        for i, d in enumerate((0.22, 0.6, 0.98)):
            sail_parts.append(torus(f'{p}_tie_{i}', 0.062 - 0.006 * i, 0.012, (0, MAST_Y - d, BOOM_Z + 0.06),
                                    (90, 0, 0), CORAL, seg=12, ring=6))
    if not mini:
        sail_parts.append(sphere(p + '_clew', 0.03, (0, MAST_Y - 0.02 - boom_len, BOOM_Z), m=CORAL, seg=8))
        sy = MAST_Y - SHEET_R
        sail_parts.append(wire(p + '_sheet', [(0, sy, BOOM_Z - 0.02), (0, sy, 0.335)], 0.009, ROPE))
        sail_parts.append(box(p + '_car', (0.05, 0.04, 0.045), (0, sy, 0.315), m=STEEL_DARK, bevel=0.012, seg=2))
    sail_ob = join(sail_parts, p + '_sail' if p != 'boat' else 'sail')
    set_origin(sail_ob, (0, MAST_Y, BOOM_Z))
    sail_ob.data.transform(Matrix.Rotation(math.radians(boom_angle), 4, 'Z'))

    # --- rudder (0.3 m blade), pivot on its pintle line at the transom
    ry = -1.045
    rud = [plate_yz(p + '_blade', [(ry + 0.035, 0.13), (ry - 0.085, 0.13), (ry - 0.1, -0.08), (ry - 0.085, -0.34),
                                   (ry - 0.02, -0.37), (ry + 0.03, -0.12)], 0.036, 0, CORAL, bevel=0.012),
           cyl(p + '_stock', 0.014, 0.42, (0, ry + 0.012, 0.1), m=SPAR, verts=6, bevel=0)]
    if not mini:
        rud.append(box(p + '_tiller', (0.03, 0.17, 0.026), (0, ry + 0.085, 0.3), m=SPAR, bevel=0.01, seg=2))
    rudder = join(rud, p + '_rudder' if p != 'boat' else 'rudder')
    set_origin(rudder, (0, ry + 0.012, 0.1))

    # --- wind vane at the masthead: nose into the wind, coral tail fin
    vz = MAST_TOP + 0.07
    vane_parts = [cyl(p + '_vane_pin', 0.011, 0.1, (0, MAST_Y, MAST_TOP + 0.04), m=STEEL_DARK, verts=6, bevel=0),
                  box(p + '_vane_arm', (0.02, 0.36, 0.02), (0, MAST_Y - 0.02, vz), m=SPAR, bevel=0.006, seg=2),
                  plate_yz(p + '_vane_fin', [(MAST_Y - 0.11, vz - 0.012), (MAST_Y - 0.26, vz - 0.07), (MAST_Y - 0.27, vz + 0.09),
                                             (MAST_Y - 0.12, vz + 0.02)], 0.022, 0, CORAL, bevel=0.006),
                  sphere(p + '_vane_nose', 0.026, (0, MAST_Y + 0.17, vz), (1, 1.5, 1), SPAR, seg=8)]
    vane = join(vane_parts, p + '_vane' if p != 'boat' else 'vane')
    set_origin(vane, (0, MAST_Y, MAST_TOP))
    vane.data.transform(Matrix.Rotation(math.radians(vane_angle), 4, 'Z'))

    if mini:
        return {'static': static, 'sail': sail_ob, 'rudder': rudder, 'vane': vane}

    # --- deck gear
    dz = 0.205                                  # main deck height near amidships
    # mainsheet traveller: an arc centred on the mast so the sheet car can follow the boom
    arc = [(SHEET_R * math.sin(math.radians(a)), MAST_Y - SHEET_R * math.cos(math.radians(a)), 0.3)
           for a in (-26, -13, 0, 13, 26)]
    static.append(wire(p + '_traveller', arc, 0.011, STEEL, smooth=True, res=3))
    for i, a in enumerate((-26, 0, 26)):
        x, y = SHEET_R * math.sin(math.radians(a)), MAST_Y - SHEET_R * math.cos(math.radians(a))
        static.append(cyl(f'{p}_trav_post_{i}', 0.011, 0.085, (x, y, 0.262), m=STEEL_DARK, verts=6, bevel=0))
    # sail winch
    wy = -0.66
    static.append(lathe(p + '_winch', [(0, 0), (0.06, 0), (0.06, 0.014), (0.036, 0.022), (0.036, 0.062), (0.06, 0.07),
                                       (0.06, 0.084), (0, 0.084)], (0, wy, dz + 0.012), m=STEEL, verts=14))
    static.append(cyl(p + '_winch_rope', 0.044, 0.034, (0, wy, dz + 0.054), m=ROPE, verts=14, bevel=0.008))
    static.append(sphere(p + '_winch_cap', 0.022, (0, wy, dz + 0.1), (1, 1, 0.6), CORAL, seg=8))
    static.append(wire(p + '_winch_line', [(0, wy + 0.045, dz + 0.055), (0, MAST_Y - SHEET_R, 0.3)], 0.008, ROPE))
    # electronics box with status lamp, just aft of the mast
    ey = -0.02
    static.append(box(p + '_ebox', (0.2, 0.2, 0.1), (0, ey, dz + 0.055), m=TEAL, bevel=0.025))
    static.append(box(p + '_ebox_lid', (0.215, 0.215, 0.022), (0, ey, dz + 0.112), m=TEAL_DEEP, bevel=0.01, seg=2))
    static.append(sphere(p + '_ebox_led', 0.017, (0.06, ey - 0.06, dz + 0.127), m=mat('#d9ffd0', 0.3, emit=4.0, emit_color='#9be8a0'), seg=8))
    # hatch
    hy = -0.26
    static.append(box(p + '_hatch_rim', (0.2, 0.17, 0.02), (0, hy, dz + 0.02), m=STEEL_DARK, bevel=0.008, seg=2))
    static.append(box(p + '_hatch', (0.17, 0.14, 0.03), (0, hy, dz + 0.032), m=WHITE, bevel=0.012, seg=2))
    static.append(box(p + '_hatch_grip', (0.07, 0.018, 0.016), (0, hy, dz + 0.052), m=CORAL, bevel=0.006, seg=2))
    # GPS antenna on a short post, aft
    gy = -0.85
    static.append(cyl(p + '_gps_post', 0.012, 0.16, (0, gy, dz + 0.08), m=STEEL_DARK, verts=6, bevel=0))
    static.append(lathe(p + '_gps', [(0, 0), (0.05, 0), (0.055, 0.012), (0.045, 0.034), (0.02, 0.046), (0, 0.048)],
                        (0, gy, dz + 0.155), m=WHITE, verts=12))
    # solar panel on the foredeck
    py = 0.57
    static.append(box(p + '_solar', (0.185, 0.26, 0.022), (0, py, dz + 0.035), (3, 0, 0), PANEL, bevel=0.008, seg=2))
    for i, dy in enumerate((-0.065, 0.0, 0.065)):
        static.append(box(f'{p}_solar_line_{i}', (0.165, 0.008, 0.006), (0, py + dy, dz + 0.047 + dy * 0.052), (3, 0, 0),
                          '#6f93a8', bevel=0))
    static.append(box(p + '_solar_mid', (0.008, 0.24, 0.006), (0, py, dz + 0.047), (3, 0, 0), '#6f93a8', bevel=0))
    # cleats
    static += _cleat(p + '_cleat_bow', 0, 0.83, dz + 0.035)
    for s, tag in ((-1, 'p'), (1, 's')):
        static += _cleat(f'{p}_cleat_{tag}', s * 0.085, -0.96, dz - 0.012, rot_z=s * 12)
        # ama deck plates
        static.append(cyl(f'{p}_ama_plate_{tag}', 0.034, 0.014, (s * AMA_X, AMA_Y - 0.12, 0.119), m=STEEL, verts=10, bevel=0.004))
    # coral pennant on a whip at the starboard ama's stern (clear of the boom's swing)
    fx, fy = AMA_X, AMA_Y - 0.66
    static.append(cyl(p + '_whip', 0.011, 0.5, (fx, fy, 0.34), m=SPAR, verts=6, bevel=0))
    pen = plate_yz(p + '_pennant', [(fy - 0.005, 0.46), (fy - 0.25, 0.525), (fy - 0.005, 0.59)], 0.02, fx, CORAL, bevel=0.005)
    set_origin(pen, (fx, fy, 0.52))
    pen.data.transform(Matrix.Rotation(math.radians(vane_angle), 4, 'Z'))
    static.append(pen)
    static.append(sphere(p + '_whip_ball', 0.02, (fx, fy, 0.6), m=SPAR, seg=8))
    return {'static': static, 'sail': sail_ob, 'rudder': rudder, 'vane': vane}


def build(mode='preview'):
    reset()
    setup_world(sea=False)
    # matte stand-in for the site's water so the preview shows the boat afloat
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=60)
    water = K._obj_from_bmesh(bm, 'water_helper')
    water.data.materials.append(mat(SEA, rough=0.6))
    water['helper'] = True

    parts = build_trimaran('boat', 'hero')
    animate(parts['sail'], 'sway', amp=6, speed=0.8, axis='z')
    animate(parts['rudder'], 'sway', amp=10, speed=1.1, axis='z')
    animate(parts['vane'], 'sway', amp=14, speed=1.7, axis='z')
    finish('boat', mode, cam_loc=(-4.2, -5.2, 3.0), cam_target=(0, 0, 0.9), lens=50)
