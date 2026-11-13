"""Sailbot: a lakeside test station for the school's autonomous trimaran.

Boat shed and slipway (a second trimaran on its cradle), a wind mast on the high
ground, the polar board, the simulator desk, a compass rose and a GPS tripod, and
in the cove the four-buoy station-keeping box plus the lone search buoy.
"""
import math
import random

import bmesh
from mathutils import Matrix, Vector

import kit as K
from kit import *
from islands.boat import build_trimaran, move, wire

TEAL = '#325963'
TEAL_DEEP = '#244a52'
SKY = '#c8dce0'
ORANGE = '#f26a3d'
SANDP = '#eddfbc'
LAWN = '#bcd6a6'
LAWN_LIP = '#a2c794'
PINE = '#3f7468'
PINE_2 = '#4f8a78'
DARK = '#2b3b3f'
PLANK = '#d39c66'
ROPE = '#e9dcc3'

WIND = Vector((0.94, -0.34, 0.0)).normalized()     # the way the wind blows
SX = -1.9                                          # slipway centre line
BOX = (1.3, -4.45, 2.8)                            # station-keeping square: centre x, y, side


# ---------------------------------------------------------------- outline
def _target_radius(a):
    """Crescent in polar form: a round back with a concave lake shore cut into the front."""
    ro = 4.85 * (1 + 0.045 * math.cos(2 * a) + 0.018 * math.sin(3 * a + 0.7) + 0.012 * math.sin(5 * a + 2.0))
    s, c = math.sin(a), math.cos(a)
    if s < -0.05:
        # shore: y = -(1.7 + 0.17 (x - 0.5)^2), intersected with the ray at angle a
        qa, qb, qc = 0.17 * c * c, s - 0.17 * c, 1.7 + 0.17 * 0.25
        if abs(qa) < 1e-9:
            r = -qc / qb
        else:
            disc = qb * qb - 4 * qa * qc
            r = (-qb - math.sqrt(disc)) / (2 * qa) if disc >= 0 else 1e9
        if r > 0:
            ro = min(ro, r)
    return ro


def crescent(harmonics=18, n=720):
    """Fourier-fit the target outline and express it as `lobes` for island_base.
    Each harmonic gets two lobes: with the two random phases the kit assigns them,
    two amplitudes are enough to reach any amplitude and phase."""
    samples = [_target_radius(TAU * i / n) for i in range(n)]
    R = sum(samples) / n
    coef = []
    for k in range(1, harmonics + 1):
        ck = 2 / n * sum(v * math.cos(k * TAU * i / n) for i, v in enumerate(samples))
        sk = 2 / n * sum(v * math.sin(k * TAU * i / n) for i, v in enumerate(samples))
        w = math.pi * k / (harmonics + 1)
        sig = math.sin(w) / w                       # Lanczos factor: no ringing at the horns
        coef.append((k, ck * sig / R, sk * sig / R))
    for seed in range(1, 100000):
        rng = random.Random(seed)
        ph = [rng.uniform(0, TAU) for _ in range(2 * harmonics)]
        if min(abs(math.sin(ph[2 * i + 1] - ph[2 * i])) for i in range(harmonics)) > 0.5:
            break
    lobes = []
    for i, (k, c, s) in enumerate(coef):
        p1, p2 = ph[2 * i], ph[2 * i + 1]
        det = math.sin(p2 - p1)
        lobes.append((k, (s * math.sin(p2) - c * math.cos(p2)) / det))
        lobes.append((k, (c * math.cos(p1) - s * math.sin(p1)) / det))
    return R, tuple(lobes), seed


# ---------------------------------------------------------------- small helpers
def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, bevel=0.06, seg=None):
    """kit.box with a bevel resolution that follows the part's size (triangle budget)."""
    if seg is None:
        seg = 3 if max(size) > 1.6 else (2 if max(size) > 0.7 else 1)
    return K.box(name, size, loc, rot, m, bevel, seg)


def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, r2=None, verts=32, bevel=0.04, seg=None):
    if seg is None:
        seg = 2 if r > 0.25 else 1
    return K.cyl(name, r, h, loc, rot, m, r2, verts, bevel, seg)


def warm():
    return mat('#fff3c4', 0.3, emit=5.0, emit_color='#ffd98a')


def beam(name, p0, p1, w=0.08, d=None, m=WOOD, bevel=0.015, rnd=False, verts=8):
    """Square (or round) bar between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    length = (p1 - p0).length
    if rnd:
        ob = cyl(name, w / 2, length, m=m, verts=verts, bevel=min(bevel, w * 0.2))
    else:
        ob = box(name, (w, d or w, length), m=m, bevel=bevel, seg=2)
    ob.location = (p0 + p1) / 2
    ob.rotation_euler = (p1 - p0).to_track_quat('Z', 'Y').to_euler()
    return ob


def slab_xz(name, outline, thick, y_front, m, bevel=0.0):
    """Plate with its outline in (X, Z), from y_front back to y_front + thick."""
    return prism(name, outline, thick, (0, y_front + thick, 0), (90, 0, 0), m, bevel=bevel, seg=2)


def polar_speed(th):
    """Boat speed (0..1) against the angle off the wind, in degrees. Built from the
    velocity made good so the optimum sits exactly at 49.3 deg upwind and 124.4 deg
    downwind; nothing inside the 30 deg no-go zone."""
    up, dn = 49.3, 124.4
    ku, kd = (math.pi / 2) / math.radians(90 - up), (math.pi / 2) / math.radians(dn - 90)
    c = math.cos(math.radians(th))
    if th <= 30:
        return 0.0
    if abs(th - 90) < 1e-6:
        return 1.0
    if th < up:
        return math.sin(math.pi / 2 * (th - 30) / (up - 30)) / ku / c
    if th < 90:
        return math.sin(math.pi / 2 * (90 - th) / (90 - up)) / ku / c
    if th <= dn:
        return math.sin(math.pi / 2 * (th - 90) / (dn - 90)) / kd / -c
    return (1 - 0.5 * ((th - dn) / (180 - dn)) ** 2) / kd / -c


# ---------------------------------------------------------------- pieces
def beach(radius_at, x_left=-3.05, x_right=-0.8, n=44):
    """Sand apron on the cove's rim that slopes down into the lake."""
    def rim(a):
        r = radius_at(a)
        return Vector((r * math.cos(a), r * math.sin(a)))

    def angle_for(x):
        a = math.radians(-92)
        while rim(a).x > x:
            a -= math.radians(0.05)
        return a

    a0, a1 = angle_for(x_left), angle_for(x_right)
    dense = [a0 + (a1 - a0) * i / 600 for i in range(601)]
    acc = [0.0]
    for p, q in zip(dense, dense[1:]):
        acc.append(acc[-1] + (rim(q) - rim(p)).length)
    bm = bmesh.new()
    cols, j = [], 0
    for i in range(n + 1):
        want = acc[-1] * i / n
        while j < 600 and acc[j + 1] < want:
            j += 1
        a = dense[j]
        p = rim(a)
        t = (rim(a + 1e-3) - rim(a - 1e-3)).normalized()
        out = Vector((t.y, -t.x))
        tau = min(1.0, max(0.0, (p.x - x_left) / (x_right - x_left)))
        s = math.sin(math.pi * tau) ** 0.7
        rings = [(-(0.2 + 1.3 * s), 0.016), (-0.10, 0.016), (0.04 + 0.10 * s, -0.05 - 0.04 * s),
                 (0.06 + 0.72 * s, -0.08 - 0.52 * s), (0.06 + 1.55 * s, -0.08 - 1.17 * s),
                 (0.06 + 1.55 * s, -0.3 - 1.2 * s), (-0.3, -0.3 - 1.2 * s)]
        cols.append([bm.verts.new((p.x + out.x * o, p.y + out.y * o, z)) for o, z in rings])
    for ca, cb in zip(cols, cols[1:]):
        for q in range(6):
            bm.faces.new((ca[q], ca[q + 1], cb[q + 1], cb[q]))
    bm.faces.new(cols[0])
    bm.faces.new(list(reversed(cols[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = K._obj_from_bmesh(bm, 'beach')
    K._finish(ob, 'beach', SANDP, angle=35)
    return rim(angle_for(SX)).y


def slipway(y_top, y_r0, y_end=-5.1, z_top=0.13, z_end=-1.34):
    """Level launching deck in front of the shed, then a planked ramp into the lake."""
    n = round((y_top - y_r0) / 0.31)
    pitch = (y_top - y_r0) / n
    for i in range(n):
        box(f'deck_plank_{i}', (1.36, pitch - 0.03, 0.07), (SX, y_top - pitch * (i + 0.5), z_top - 0.035),
            (0, 0, (i % 3 - 1) * 0.7), WOOD if i % 2 else PLANK, bevel=0.02, seg=1)
    for s in (-1, 1):
        box(f'deck_sleeper_{s}', (0.12, y_top - y_r0, 0.07), (SX + s * 0.52, (y_top + y_r0) / 2, 0.028),
            m=WOOD_DARK, bevel=0.015)
        box(f'rail_flat_{s}', (0.05, 2.2 - y_r0, 0.04), (SX + s * 0.38, (2.2 + y_r0) / 2, z_top + 0.02), m=DARK, bevel=0.012)
    p0, p1 = Vector((SX, y_r0, z_top)), Vector((SX, y_end, z_end))
    length = (p1 - p0).length
    th = math.atan2(z_top - z_end, y_r0 - y_end)
    deg = math.degrees(th)
    u = Vector((0, -math.cos(th), -math.sin(th)))
    nrm = Vector((0, -math.sin(th), math.cos(th)))
    m = round(length / 0.31)
    pitch = length / m
    for i in range(m):
        c = p0 + u * (pitch * (i + 0.5)) - nrm * 0.035
        box(f'ramp_plank_{i}', (1.36, pitch - 0.03, 0.07), c, (deg, 0, (i % 3 - 1) * 0.7), PLANK if i % 2 else WOOD, bevel=0.02, seg=1)
    mid = (p0 + p1) / 2
    for s in (-1, 1):
        off = Vector((s * 0.52, 0, 0))
        box(f'ramp_stringer_{s}', (0.12, length, 0.09), mid + off - nrm * 0.115, (deg, 0, 0), WOOD_DARK, bevel=0.015)
        box(f'rail_ramp_{s}', (0.05, length, 0.04), mid + Vector((s * 0.38, 0, 0)) + nrm * 0.02, (deg, 0, 0), DARK, bevel=0.012)
    for i, t in enumerate((0.3, 0.62, 0.94)):
        q = p0 + u * (length * t)
        box(f'ramp_tie_{i}', (1.6, 0.11, 0.09), q - nrm * 0.2, (deg, 0, 0), WOOD_DARK, bevel=0.015)
        for s in (-1, 1):
            top = q.z + 0.24
            cyl(f'ramp_pile_{i}_{s}', 0.085, top + 2.0, (SX + s * 0.78, q.y, (top - 2.0) / 2), m=WOOD_DARK, verts=12, bevel=0.02)
            cyl(f'ramp_cap_{i}_{s}', 0.105, 0.06, (SX + s * 0.78, q.y, top + 0.02), m=ROPE, verts=12, bevel=0.02)
    return deg


def shed(cx=SX, y0=0.25, w=2.8, d=2.5, zf=0.13, top=1.5):
    """Boat shed: three walls, a wide open front and a teal gable roof."""
    y1, cy, wh = y0 + d, y0 + d / 2, top - zf
    box('shed_floor', (w + 0.1, d + 0.06, zf), (cx, cy + 0.03, zf / 2), m='#d8cdb6', bevel=0.03)
    glass = mat('#bfe0e6', 0.25, emit=0.45, emit_color='#ffe7b0')
    for s, tag in ((-1, 'l'), (1, 'r')):
        wx = cx + s * (w / 2 - 0.06)
        box(f'shed_wall_{tag}', (0.12, d, wh), (wx, cy, zf + wh / 2), m=WHITE, bevel=0.03)
        for i in (0, 1, 4, 5):
            box(f'shed_batten_{tag}_{i}', (0.035, 0.07, wh - 0.08), (wx + s * 0.07, y0 + 0.28 + i * (d - 0.5) / 5, zf + wh / 2),
                m='#ebe4d4', bevel=0.012, seg=2)
        box(f'shed_winframe_{tag}', (0.05, 0.78, 0.6), (wx + s * 0.065, cy + 0.03, 0.92), m=TEAL_DEEP, bevel=0.02, seg=2)
        box(f'shed_window_{tag}', (0.05, 0.64, 0.46), (wx + s * 0.08, cy + 0.03, 0.92), m=glass, bevel=0.015, seg=2)
        box(f'shed_winbar_{tag}', (0.05, 0.035, 0.46), (wx + s * 0.09, cy + 0.03, 0.92), m=TEAL_DEEP, bevel=0.008, seg=2)
        box(f'shed_post_{tag}', (0.17, 0.17, wh), (wx, y0 + 0.03, zf + wh / 2), m=TEAL_DEEP, bevel=0.03)
    box('shed_wall_back', (w, 0.12, wh), (cx, y1 - 0.06, zf + wh / 2), m=WHITE, bevel=0.03)
    # the back of the shed: a window, a ladder and a rain barrel
    box('shed_winframe_b', (0.9, 0.05, 0.6), (cx - 0.5, y1 + 0.005, 0.95), m=TEAL_DEEP, bevel=0.02)
    box('shed_window_b', (0.76, 0.05, 0.46), (cx - 0.5, y1 + 0.02, 0.95), m=glass, bevel=0.015)
    box('shed_winbar_b', (0.035, 0.05, 0.46), (cx - 0.5, y1 + 0.03, 0.95), m=TEAL_DEEP, bevel=0.008)
    for s in (-1, 1):
        beam(f'ladder_rail_{s}', (cx + 0.75 + s * 0.2, y1 + 0.5, 0.0), (cx + 0.75 + s * 0.2, y1 + 0.04, 1.45), 0.05, m=WOOD, bevel=0.012)
    for i in range(5):
        t = 0.14 + 0.18 * i
        box(f'ladder_rung_{i}', (0.42, 0.04, 0.04), (cx + 0.75, y1 + 0.5 - 0.46 * t, 1.45 * t), m=WOOD_DARK, bevel=0.01)
    lathe('rain_barrel', [(0, 0), (0.2, 0), (0.25, 0.26), (0.2, 0.52), (0, 0.52)], (cx - 1.1, y1 + 0.32, 0.0), m=WOOD_DARK, verts=16)
    torus('rain_barrel_hoop', 0.245, 0.018, (cx - 1.1, y1 + 0.32, 0.26), m=DARK, seg=16, ring=4)
    cyl('rain_barrel_water', 0.17, 0.02, (cx - 1.1, y1 + 0.32, 0.515), m=SKY, verts=14, bevel=0)
    box('shed_lintel', (w + 0.08, 0.18, 0.18), (cx, y0 + 0.03, top - 0.07), m=TEAL_DEEP, bevel=0.03)
    prism('shed_roof', [(-w / 2 - 0.3, 0), (w / 2 + 0.3, 0), (0, 1.0)], d + 0.56, (cx, y1 + 0.28, top), (90, 0, 0), TEAL, bevel=0.06)
    box('shed_ridge', (0.14, d + 0.62, 0.09), (cx, cy, top + 0.98), m=TEAL_DEEP, bevel=0.03)
    fy = y0 - 0.28                                  # the roof's front face
    for tag, yy in (('front', fy - 0.05), ('back', y1 + 0.28)):
        slab_xz(f'shed_gable_{tag}', [(cx - w / 2 + 0.12, top + 0.07), (cx + w / 2 - 0.12, top + 0.07), (cx, top + 0.84)], 0.05, yy, CREAM, bevel=0.015)
    cyl('shed_vent_frame', 0.25, 0.05, (cx, fy - 0.065, top + 0.36), (90, 0, 0), TEAL_DEEP, verts=24, bevel=0.015)
    cyl('shed_vent', 0.19, 0.05, (cx, fy - 0.08, top + 0.36), (90, 0, 0), glass, verts=24, bevel=0.015)
    cyl('shed_flag_pole', 0.022, 0.8, (cx, fy + 0.12, top + 1.4), m=DARK, verts=8, bevel=0)
    sphere('shed_flag_ball', 0.04, (cx, fy + 0.12, top + 1.82), m=CORAL, seg=8)
    pen = K.prism('shed_pennant', [(0, 0), (0.5, 0.11), (0, 0.24)], 0.03, (cx, fy + 0.135, top + 1.5), (90, 0, 0), CORAL, bevel=0.008, seg=1)
    pen.rotation_euler.z = math.atan2(WIND.y, WIND.x)
    # inside: workbench, sail roll, shelf, lamp
    by = y1 - 0.42
    box('bench_top', (1.9, 0.5, 0.07), (cx, by, 0.83), m=WOOD, bevel=0.02)
    for sx in (-0.85, 0.85):
        for sy in (-0.18, 0.18):
            box(f'bench_leg_{sx}_{sy}', (0.08, 0.08, 0.68), (cx + sx, by + sy, zf + 0.34), m=WOOD_DARK, bevel=0.015, seg=2)
    box('bench_shelf', (1.7, 0.4, 0.04), (cx, by, 0.42), m=WOOD_DARK, bevel=0.012, seg=2)
    box('bench_vise', (0.14, 0.2, 0.14), (cx - 0.7, by - 0.14, 0.93), m=TEAL, bevel=0.03, seg=2)
    box('bench_case', (0.42, 0.26, 0.2), (cx + 0.55, by + 0.02, 0.96), (0, 0, 8), CORAL, bevel=0.03)
    cyl('bench_spool', 0.1, 0.16, (cx + 0.02, by, 0.945), m=ROPE, verts=14, bevel=0.03)
    cyl('sail_roll', 0.09, 2.0, (cx, y1 - 0.2, 1.22), (0, 90, 0), CREAM, verts=14, bevel=0.03)
    for i, dx in enumerate((-0.7, 0.0, 0.7)):
        torus(f'sail_roll_tie_{i}', 0.095, 0.016, (cx + dx, y1 - 0.2, 1.22), (0, 90, 0), CORAL, seg=14, ring=6)
        box(f'sail_roll_hook_{i}', (0.05, 0.16, 0.05), (cx + dx + 0.12, y1 - 0.17, 1.11), m=WOOD_DARK, bevel=0.012, seg=2)
    cyl('shed_lamp_cord', 0.012, 0.25, (cx, y0 + 1.1, top - 0.125), m=DARK, verts=6, bevel=0)
    lathe('shed_lamp_shade', [(0.03, 0.12), (0.17, 0.0), (0.19, 0.0), (0.05, 0.14)], (cx, y0 + 1.1, top - 0.36), m=TEAL_DEEP, verts=16)
    sphere('shed_lamp', 0.075, (cx, y0 + 1.1, top - 0.36), m=warm(), seg=12)


def cradle_and_boat(y=-0.9, z_deck=0.13):
    """Launching cradle on the rails with the second trimaran, sail furled."""
    zr = z_deck + 0.04
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f'cradle_wheel_{sx}_{sy}', 0.075, 0.06, (SX + sx * 0.38, y + sy * 0.47, zr + 0.07), (0, 90, 0), DARK, verts=14, bevel=0.015)
        box(f'cradle_side_{sx}', (0.08, 1.24, 0.08), (SX + sx * 0.38, y, zr + 0.175), m=TEAL, bevel=0.02)
    sc = 0.88                                        # the second boat is a little smaller than the hero
    oz = zr + 0.335 + 0.14 * sc                      # the boat's waterline height on the cradle
    kz = oz - 0.14 * sc                              # underside of the main hull
    for i, sy in enumerate((-0.42, 0.42)):
        box(f'cradle_cross_{i}', (0.94, 0.1, 0.08), (SX, y + sy, zr + 0.25), m=TEAL, bevel=0.02)
        xs = [-0.19 + 0.38 * k / 10 for k in range(11)]
        notch = [(x, kz + 0.02 + 0.09 * min(1.0, abs(x) / 0.135) ** 2.2) for x in reversed(xs)]
        slab_xz(f'cradle_saddle_{i}', [(-0.19, zr + 0.28), (0.19, zr + 0.28)] + notch, 0.09,
                y + sy - 0.045, WOOD, bevel=0.012).location.x = SX
    parts = build_trimaran('slipboat', 'mid', sail='furled', boom_angle=0.0, vane_angle=-110.0)
    move(parts['static'] + [parts['sail'], parts['rudder'], parts['vane']], (SX, y, oz), rot_z=180, scale=sc)
    # painter from the bow to a cleat on the deck
    wire('slipboat_painter', [(SX, y - 0.97 * sc, oz + 0.25 * sc), (SX + 0.2, y - 1.12, oz - 0.05), (SX + 0.78, y - 1.0, z_deck + 0.12),
                              (SX + 0.62, y - 0.6, z_deck + 0.02)], 0.014, ROPE, smooth=True, res=4)
    return oz


def wind_mast(x, y, z0):
    """Tall weather mast: fixed cross arms, a big vane and a striped windsock."""
    cyl('wm_pad', 0.36, 0.14, (x, y, z0 + 0.02), m='#d8d2c4', verts=20, bevel=0.03)
    h, zb = 3.6, z0 + 0.08
    lathe('wm_pole', [(0, 0), (0.09, 0), (0.045, h), (0, h)], (x, y, zb), m=WHITE, verts=14)
    for k, z in enumerate((0.75, 1.75, 2.75)):
        r0, r1 = 0.09 - 0.045 * (z - 0.16) / h, 0.09 - 0.045 * (z + 0.16) / h
        lathe(f'wm_band_{k}', [(r0 + 0.01, z - 0.16), (r1 + 0.01, z + 0.16)], (x, y, zb), m=CORAL, verts=14)
    top = zb + h
    for k, a in enumerate((20, 110)):
        dx, dy = 0.34 * math.cos(math.radians(a)), 0.34 * math.sin(math.radians(a))
        beam(f'wm_cross_{k}', (x - dx, y - dy, top - 0.3), (x + dx, y + dy, top - 0.3), 0.03, m=DARK, rnd=True, verts=6)
        for s in (-1, 1):
            sphere(f'wm_cross_ball_{k}_{s}', 0.045, (x + s * dx, y + s * dy, top - 0.3), m=TEAL if s > 0 or k else CORAL, seg=10)
    for k, a in enumerate((75, 195, 305)):
        gx, gy = x + 1.0 * math.cos(math.radians(a)), y + 1.0 * math.sin(math.radians(a))
        gz = mound_h(1.0)
        wire(f'wm_guy_{k}', [(x, y, zb + 2.3), (gx, gy, gz)], 0.011, DARK)
        cyl(f'wm_peg_{k}', 0.035, 0.16, (gx, gy, gz + 0.04), (0, 0, 0), WOOD_DARK, verts=8, bevel=0.01)
    # vane: built nose toward +Y, then turned to face the wind
    vz = top + 0.2
    vane = join([cyl('vane_pin', 0.022, 0.34, (x, y, top + 0.1), m=DARK, verts=8, bevel=0.005),
                 box('vane_arm', (0.04, 1.36, 0.04), (x, y - 0.1, vz), m=DARK, bevel=0.012, seg=2),
                 K.prism('vane_fin', [(y - 0.36, vz - 0.03), (y - 0.76, vz - 0.22), (y - 0.8, vz + 0.3), (y - 0.42, vz + 0.07)],
                         0.04, (x - 0.02, 0, 0), (90, 0, 90), CORAL, bevel=0.012, seg=2),
                 cyl('vane_head', 0.085, 0.24, (x, y + 0.66, vz), (-90, 0, 0), CORAL, r2=0.0, verts=12, bevel=0.01),
                 sphere('vane_hub', 0.06, (x, y, vz), m=WHITE, seg=10)], 'vane')
    set_origin(vane, (x, y, top))
    vane.data.transform(Matrix.Rotation(math.atan2(-(-WIND.x), -WIND.y), 4, 'Z'))
    animate(vane, 'sway', amp=12, speed=0.9, axis='z')
    # windsock: built along +Z from its swivel, then laid downwind with a little droop
    parts = [torus('sock_hoop', 0.21, 0.02, (0, 0, 0), m=WHITE, seg=20, ring=6),
             cyl('sock_mouth', 0.19, 0.02, (0, 0, 0.0), m=TEAL_DEEP, verts=20, bevel=0)]
    for i in range(5):
        r0, r1 = 0.21 - 0.024 * i, 0.21 - 0.024 * (i + 1)
        parts.append(lathe(f'sock_{i}', [(r0, 0.21 * i + 0.012), (r1, 0.21 * (i + 1) + 0.012)], m=CORAL if i % 2 == 0 else WHITE, verts=20))
    for i in range(4):
        a = TAU * i / 4
        parts.append(beam(f'sock_bridle_{i}', (0, 0, -0.3), (0.21 * math.cos(a), 0.21 * math.sin(a), 0), 0.018, m=DARK, rnd=True, verts=6))
    sock = join(parts, 'windsock')
    set_origin(sock, (0, 0, -0.3))
    aim = Vector((WIND.x, WIND.y, -0.24)).normalized()
    sock.data.transform(Vector((0, 0, 1)).rotation_difference(aim).to_matrix().to_4x4())
    sz = zb + 3.0
    sock.location = Vector((x, y, sz)) + WIND * 0.1
    torus('sock_swivel', 0.075, 0.02, (x, y, sz), m=DARK, seg=14, ring=6)
    animate(sock, 'sway', amp=10, speed=1.3, axis='z')
    return top + 0.5


MOUND = [(0, 0.72), (0.42, 0.7), (0.8, 0.55), (1.1, 0.28), (1.28, 0.07), (1.35, 0.0)]


def mound_h(r):
    for (r0, z0), (r1, z1) in zip(MOUND, MOUND[1:]):
        if r <= r1:
            return z0 + (z1 - z0) * (r - r0) / (r1 - r0)
    return 0.0


def polar_board(x, y, alpha=-32.0, tilt=10.0, cz=1.95):
    """Upright polar diagram: rings, butterfly speed lobes, optimum-angle markers."""
    parts = [cyl('pb_disc', 1.0, 0.08, (0, 0, -0.04), m=PAPER, verts=40, bevel=0.02, seg=1),
             torus('pb_rim', 1.0, 0.055, (0, 0, -0.03), m=TEAL_DEEP, seg=40, ring=6)]
    for i, r in enumerate((0.3, 0.6, 0.9)):
        parts.append(torus(f'pb_ring_{i}', r, 0.014, (0, 0, 0.004), m='#9dbcc4', seg=32, ring=4))
    for i in range(12):
        a = TAU * i / 12
        parts.append(box(f'pb_spoke_{i}', (0.014, 0.9, 0.012), (0.45 * math.sin(a), 0.45 * math.cos(a), 0.006),
                         (0, 0, -math.degrees(a)), '#b6ccd0', bevel=0))
    # no-go zone: the wind comes from the top of the board
    wedge = [(0, 0)] + [(0.9 * math.sin(math.radians(t)), 0.9 * math.cos(math.radians(t))) for t in range(30, -31, -6)]
    parts.append(prism('pb_nogo', wedge, 0.014, m='#f5d3c4', bevel=0))
    lobe = []
    for i in range(0, 51):
        th = 30 + i * 3
        r = 0.88 * polar_speed(th)
        lobe.append((r * math.sin(math.radians(th)), r * math.cos(math.radians(th))))
    parts.append(prism('pb_lobe_r', list(reversed(lobe)), 0.045, m=TEAL, bevel=0.012, seg=1))
    parts.append(prism('pb_lobe_l', [(-px, py) for px, py in lobe], 0.045, m=TEAL, bevel=0.012, seg=1))
    for th, tag, c_peg, c_dot in ((49.3, 'up', CORAL, WHITE), (124.4, 'down', WHITE, CORAL)):
        for s in (-1, 1):
            dx, dy = s * math.sin(math.radians(th)), math.cos(math.radians(th))
            parts.append(box(f'pb_ray_{tag}_{s}', (0.024, 0.98, 0.022), (dx * 0.49, dy * 0.49, 0.052),
                             (0, 0, -s * th), CORAL, bevel=0.006, seg=2))
            r = 0.88 * polar_speed(th)
            parts.append(cyl(f'pb_peg_{tag}_{s}', 0.07, 0.1, (dx * r, dy * r, 0.07), m=c_peg, verts=14, bevel=0.02))
            parts.append(sphere(f'pb_dot_{tag}_{s}', 0.032, (dx * r, dy * r, 0.12), (1, 1, 0.6), c_dot, 10))
            parts.append(sphere(f'pb_knob_{tag}_{s}', 0.065, (dx * 1.0, dy * 1.0, 0.03), m=CORAL, seg=8))
    parts.append(prism('pb_boat', [(0, 0.13), (-0.05, -0.01), (-0.04, -0.1), (0.04, -0.1), (0.05, -0.01)], 0.07, m=WHITE, bevel=0.015, seg=2))
    parts.append(sphere('pb_boat_dot', 0.025, (0, -0.02, 0.075), (1, 1, 0.6), CORAL, 8))
    parts.append(prism('pb_wind_head', [(-0.14, 1.2), (0, 0.96), (0.14, 1.2)], 0.06, (0, 0, 0.03), m=TEAL_DEEP, bevel=0.015, seg=2))
    parts.append(box('pb_wind_stem', (0.06, 0.26, 0.06), (0, 1.3, 0.06), m=TEAL_DEEP, bevel=0.015, seg=2))
    # frame (posts run down to the ground in the board's own tilted plane) and the back of the disc
    y_gnd = -(cz + 0.02) / math.cos(math.radians(tilt))
    for s in (-1, 1):
        parts.append(box(f'pb_post_{s}', (0.11, 0.55 - y_gnd, 0.11), (s * 0.62, (0.55 + y_gnd) / 2, -0.135), m=WOOD, bevel=0.02, seg=2))
    parts.append(box('pb_ledge', (1.5, 0.1, 0.2), (0, -1.07, -0.08), m=WOOD_DARK, bevel=0.02, seg=2))
    parts.append(box('pb_top_bar', (1.35, 0.09, 0.09), (0, 0.5, -0.135), m=WOOD_DARK, bevel=0.02, seg=2))
    parts.append(box('pb_low_bar', (1.35, 0.09, 0.09), (0, y_gnd + 0.5, -0.135), m=WOOD_DARK, bevel=0.02, seg=2))
    parts.append(cyl('pb_back', 0.9, 0.03, (0, 0, -0.09), m=SKY, verts=32, bevel=0.01, seg=1))
    parts.append(torus('pb_back_ring', 0.55, 0.02, (0, 0, -0.105), m=TEAL, seg=28, ring=4))
    mtx = (Matrix.Translation((x, y, cz)) @ Matrix.Rotation(math.radians(alpha), 4, 'Z')
           @ Matrix.Rotation(math.radians(90 - tilt), 4, 'X'))
    move(parts, (x, y, cz), rot_z=alpha, rot_x=90 - tilt)
    back = Vector((-math.sin(math.radians(alpha)), math.cos(math.radians(alpha)), 0))
    for s in (-1, 1):
        p = mtx @ Vector((s * 0.62, 0.3, -0.19))
        foot = Vector((p.x, p.y, 0)) + back * 0.9
        beam(f'pb_strut_{s}', p, foot, 0.09, m=WOOD_DARK, bevel=0.02)
        cyl(f'pb_foot_{s}', 0.12, 0.05, (foot.x, foot.y, 0.02), m='#d8d2c4', verts=10, bevel=0.015)
    return mtx @ Vector((0, 1.55, 0))


def sim_desk(x, y, alpha=-22.0):
    """Simulator desk under an awning: monitor with a lake, a tacking track and the boat."""
    parts = []
    add = parts.append
    add(box('sd_floor', (2.1, 1.55, 0.07), (0, 0, 0.035), m='#dfd2b6', bevel=0.02))
    for i in range(6):
        add(box(f'sd_floor_gap_{i}', (0.02, 1.5, 0.012), (-0.875 + 0.35 * i, 0, 0.072), m='#c9b998', bevel=0))
    # awning
    zf, zb_ = 1.98, 1.66
    for sx in (-1, 1):
        add(beam(f'sd_post_f_{sx}', (sx * 0.95, -0.66, 0.06), (sx * 0.95, -0.66, zf), 0.075, m=WHITE, rnd=True, verts=10))
        add(beam(f'sd_post_b_{sx}', (sx * 0.95, 0.66, 0.06), (sx * 0.95, 0.66, zb_), 0.075, m=WHITE, rnd=True, verts=10))
    slope = math.degrees(math.atan2(zb_ - zf, 1.32))
    for i in range(7):
        add(box(f'sd_awning_{i}', (0.305, 1.74, 0.045), (-0.915 + 0.305 * i, 0, (zf + zb_) / 2 + 0.03), (slope, 0, 0),
                TEAL if i % 2 == 0 else CREAM, bevel=0.015, seg=1))
    for i in range(7):
        add(box(f'sd_valance_{i}', (0.305, 0.04, 0.16), (-0.915 + 0.305 * i, -0.87, zf + 0.125 - 0.1), (0, 0, 0),
                TEAL if i % 2 == 0 else CREAM, bevel=0.015, seg=1))
    # desk
    dz = 0.78
    add(box('sd_desk', (1.42, 0.66, 0.07), (0, 0.05, dz - 0.035), m=WOOD, bevel=0.025))
    for sx in (-0.63, 0.63):
        for sy in (-0.2, 0.3):
            add(box(f'sd_leg_{sx}_{sy}', (0.07, 0.07, dz - 0.13), (sx, sy, 0.07 + (dz - 0.13) / 2), m=WOOD_DARK, bevel=0.015, seg=2))
    add(box('sd_drawer', (0.4, 0.5, 0.3), (0.42, 0.07, dz - 0.22), m=WOOD_DARK, bevel=0.02))
    add(sphere('sd_knob', 0.025, (0.42, -0.19, dz - 0.2), m=CORAL, seg=8))
    # monitor
    mx, my, mz = -0.3, 0.16, dz + 0.36
    add(box('sd_mon_base', (0.3, 0.2, 0.03), (mx, my + 0.03, dz + 0.015), m=DARK, bevel=0.01, seg=2))
    add(box('sd_mon_neck', (0.07, 0.05, 0.16), (mx, my + 0.05, dz + 0.09), m=DARK, bevel=0.01, seg=2))
    add(box('sd_mon_bezel', (0.8, 0.07, 0.54), (mx, my, mz), m=DARK, bevel=0.03))
    ys = my - 0.035                                  # bezel front
    scr = [box('scr_glass', (0.72, 0.012, 0.46), (mx, ys - 0.004, mz), m=mat('#1f4048', 0.3, emit=1.1, emit_color='#2b6470'), bevel=0)]
    lake = [((0.27 + 0.035 * math.sin(2 * t + 0.5) + 0.02 * math.sin(3 * t)) * math.cos(t) * 1.12,
             (0.27 + 0.035 * math.sin(2 * t + 0.5) + 0.02 * math.sin(3 * t)) * math.sin(t) * 0.66) for t in
            [TAU * i / 28 for i in range(28)]]
    lk = slab_xz('scr_lake', [(mx + px, mz + pz) for px, pz in lake], 0.008, ys - 0.016,
                 mat('#8fd6d2', 0.4, emit=2.2, emit_color='#7fd3cf'))
    scr.append(lk)
    glow_w = mat(WHITE, 0.4, emit=4.5)
    glow_c = mat(CORAL, 0.4, emit=5.0)
    glow_o = mat(ORANGE, 0.4, emit=5.0)
    track = [(-0.2, -0.105), (-0.07, -0.035), (-0.15, 0.045), (-0.02, 0.1)]
    k = 0
    for (ax, az), (bx, bz) in zip(track, track[1:]):
        seg_len = math.hypot(bx - ax, bz - az)
        n = max(2, round(seg_len / 0.05))
        ang = math.degrees(math.atan2(bz - az, bx - ax))
        for i in range(n):
            t = (i + 0.35) / n
            scr.append(box(f'scr_dash_{k}', (0.028, 0.008, 0.012), (mx + ax + (bx - ax) * t, ys - 0.022, mz + az + (bz - az) * t),
                           (0, -ang, 0), glow_w, bevel=0))
            k += 1
    scr.append(slab_xz('scr_boat', [(mx - 0.045, mz + 0.085), (mx + 0.03, mz + 0.118), (mx - 0.02, mz + 0.145)], 0.012, ys - 0.03, glow_c))
    for i, (px, pz) in enumerate(((0.1, -0.06), (0.2, -0.06), (0.1, 0.04), (0.2, 0.04))):
        scr.append(box(f'scr_buoy_{i}', (0.026, 0.012, 0.026), (mx + px, ys - 0.024, mz + pz), (0, 45, 0), glow_o, bevel=0))
    monitor = join(scr, 'monitor')
    add(monitor)
    # desk things
    add(box('sd_keyboard', (0.4, 0.14, 0.025), (mx + 0.02, -0.15, dz + 0.012), (0, 0, 3), '#e9e3d3', bevel=0.008, seg=2))
    add(box('sd_keys', (0.36, 0.1, 0.012), (mx + 0.02, -0.15, dz + 0.028), (0, 0, 3), '#9fb3b8', bevel=0.004, seg=2))
    add(sphere('sd_mouse', 0.04, (mx + 0.33, -0.14, dz + 0.012), (0.8, 1.2, 0.5), WHITE, 10))
    add(lathe('sd_mug', [(0, 0), (0.045, 0), (0.05, 0.1), (0.04, 0.1), (0.035, 0.03), (0, 0.03)], (mx - 0.33, -0.14, dz), m=CORAL, verts=12))
    # telemetry radio with a whip antenna
    add(box('sd_radio', (0.2, 0.14, 0.11), (0.52, 0.24, dz + 0.055), (0, 0, -8), TEAL, bevel=0.02, seg=2))
    add(cyl('sd_radio_whip', 0.011, 0.5, (0.59, 0.27, dz + 0.36), (0, 4, 0), DARK, verts=6, bevel=0))
    add(sphere('sd_radio_tip', 0.02, (0.607, 0.27, dz + 0.61), m=CORAL, seg=8))
    add(sphere('sd_radio_led', 0.016, (0.46, 0.165, dz + 0.085), m=mat('#d9ffd0', 0.3, emit=4.0, emit_color='#9be8a0'), seg=8))
    # the desk-size trimaran on its stand
    bx, by_, bz = 0.34, -0.06, dz + 0.105
    for i, dx in enumerate((-0.09, 0.09)):
        add(box(f'sd_model_stand_{i}', (0.035, 0.11, 0.085), (bx + dx, by_, dz + 0.04), m=WOOD_DARK, bevel=0.008, seg=2))
    mini = build_trimaran('model', 'mini', sail='set', boom_angle=12.0, vane_angle=30.0)
    parts.extend(move(mini['static'] + [mini['sail'], mini['rudder'], mini['vane']], (bx, by_, bz), rot_z=80, scale=0.2))
    # stool, battery box and cable
    add(cyl('sd_stool_seat', 0.2, 0.07, (-0.42, -0.62, 0.55), m=CORAL, verts=18, bevel=0.03))
    for i in range(3):
        a = TAU * i / 3 + 0.4
        add(beam(f'sd_stool_leg_{i}', (-0.42 + 0.2 * math.cos(a), -0.62 + 0.2 * math.sin(a), 0.06), (-0.42 + 0.1 * math.cos(a), -0.62 + 0.1 * math.sin(a), 0.53),
                 0.045, m=WOOD_DARK, rnd=True, verts=8))
    add(box('sd_battery', (0.34, 0.24, 0.24), (0.72, 0.52, 0.19), (0, 0, 10), TEAL_DEEP, bevel=0.03))
    add(box('sd_battery_cap', (0.36, 0.26, 0.05), (0.72, 0.52, 0.325), (0, 0, 10), CORAL, bevel=0.015, seg=2))
    add(wire('sd_cable', [(0.6, 0.5, 0.25), (0.45, 0.48, 0.12), (0.3, 0.42, 0.08), (0.2, 0.36, 0.3), (0.12, 0.33, dz - 0.06)], 0.014, DARK, smooth=True, res=3))
    move(parts, (x, y, 0), rot_z=alpha)
    m = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(alpha), 4, 'Z')
    set_origin(monitor, m @ Vector((mx, ys, mz)))
    animate(monitor, 'pulse', speed=0.8)
    return m @ Vector((mx, 0.0, 2.25))


def compass_rose(x, y, r=0.95):
    """Eight-point rose set flat into the ground; the coral point is north (+Y)."""
    cyl('rose_stone', r, 0.03, (x, y, 0.012), m='#e9e1cd', verts=36, bevel=0.01, seg=1)
    cyl('rose_inner', r - 0.1, 0.03, (x, y, 0.02), m=SANDP, verts=36, bevel=0.008, seg=1)
    torus('rose_line', r - 0.25, 0.014, (x, y, 0.036), m=TEAL, seg=32, ring=4)
    for i in range(8):
        long = i % 2 == 0
        ln, wd = (r - 0.07, 0.14) if long else (r - 0.36, 0.1)
        h = 0.02 if long else 0.014
        for s in (-1, 1):
            c = (CORAL if s > 0 else '#f6b9a6') if i == 0 else (TEAL if s > 0 else PAPER)
            prism(f'rose_pt_{i}_{s}', [(0, 0), (s * wd, wd * 1.05), (0, ln)] if s > 0 else [(0, 0), (0, ln), (s * wd, wd * 1.05)],
                  h, (x, y, 0.034), (0, 0, -45 * i), c, bevel=0)
    cyl('rose_hub', 0.09, 0.03, (x, y, 0.065), m=CORAL, verts=14, bevel=0.01)
    for i in range(16):
        a = TAU * (i + 0.5) / 16
        box(f'rose_tick_{i}', (0.025, 0.07, 0.008), (x + (r - 0.05) * math.sin(a), y + (r - 0.05) * math.cos(a), 0.038),
            (0, 0, -math.degrees(a)), TEAL, bevel=0)


def gps_tripod(x, y):
    for i in range(3):
        a = TAU * i / 3 + 0.5
        beam(f'gps_leg_{i}', (x + 0.44 * math.cos(a), y + 0.44 * math.sin(a), 0.0), (x + 0.04 * math.cos(a), y + 0.04 * math.sin(a), 1.12),
             0.055, m=WOOD, rnd=True, verts=8)
        cyl(f'gps_shoe_{i}', 0.045, 0.05, (x + 0.44 * math.cos(a), y + 0.44 * math.sin(a), 0.025), m=DARK, verts=8, bevel=0.01)
    cyl('gps_head', 0.1, 0.09, (x, y, 1.13), m=DARK, verts=12, bevel=0.02)
    cyl('gps_stem', 0.022, 0.22, (x, y, 1.28), m=STEEL_DARK, verts=8, bevel=0)
    cyl('gps_plane', 0.21, 0.035, (x, y, 1.4), m=TEAL, verts=20, bevel=0.012)
    lathe('gps_dome', [(0, 0), (0.14, 0), (0.15, 0.03), (0.125, 0.09), (0.06, 0.13), (0, 0.14)], (x, y, 1.415), m=WHITE, verts=18)
    box('gps_logger', (0.26, 0.2, 0.16), (x + 0.5, y - 0.28, 0.08), (0, 0, 20), CORAL, bevel=0.03)
    wire('gps_cable', [(x, y, 1.1), (x + 0.1, y - 0.06, 0.6), (x + 0.3, y - 0.18, 0.05), (x + 0.45, y - 0.25, 0.14)], 0.012, DARK, smooth=True, res=3)


def bench(x, y, rot):
    parts = []
    for sx in (-0.46, 0.46):
        parts.append(box(f'seat_leg_{sx}', (0.08, 0.44, 0.42), (sx, 0, 0.21), m=TEAL_DEEP, bevel=0.03))
        parts.append(box(f'seat_back_{sx}', (0.07, 0.06, 0.5), (sx, 0.22, 0.64), (-8, 0, 0), TEAL_DEEP, bevel=0.02))
    for i, dy in enumerate((-0.15, 0.0, 0.15)):
        parts.append(box(f'seat_slat_{i}', (1.2, 0.13, 0.045), (0, dy, 0.44), m=WOOD if i % 2 else PLANK, bevel=0.015))
    for i, dz in enumerate((0.62, 0.8)):
        parts.append(box(f'seat_rest_{i}', (1.2, 0.045, 0.12), (0, 0.2 + 0.025 * i * 1.0, dz), (-8, 0, 0), PLANK if i else WOOD, bevel=0.015))
    move(parts, (x, y, 0), rot_z=rot)


def paint_can(name, x, y, color, z=0.0, open_=False):
    lathe(name, [(0, 0), (0.1, 0), (0.1, 0.19), (0.107, 0.2), (0.107, 0.215), (0, 0.215)], (x, y, z), m=STEEL, verts=14)
    cyl(name + '_lid', 0.085, 0.02, (x, y, z + 0.22), m=color, verts=14, bevel=0.005)
    cyl(name + '_label', 0.104, 0.09, (x, y, z + 0.1), m=color, verts=14, bevel=0)
    if open_:
        box(name + '_brush', (0.035, 0.3, 0.025), (x + 0.02, y, z + 0.24), (0, 0, 35), WOOD, bevel=0.008, seg=2)


def rope_coil(name, x, y, z=0.0, r=0.22, turns=3):
    for i in range(turns):
        torus(f'{name}_{i}', r - i * 0.014, 0.036, (x, y, z + 0.04 + i * 0.062), m=ROPE, seg=20, ring=6)
    wire(name + '_tail', [(x + r, y, z + 0.04), (x + r + 0.12, y + 0.16, z + 0.03), (x + r + 0.02, y + 0.34, z + 0.03)], 0.033, ROPE, smooth=True, res=3).data.bevel_resolution = 2


def pine_tree(name, loc, h=1.8, r=0.55, leaf=PINE, tiers=3):
    """Toy conifer like kit.pine, with fewer facets."""
    x, y, z = loc
    cyl(name + '_trunk', 0.07 * h, h * 0.3, (x, y, z + h * 0.15), m=WOOD_DARK, verts=8, bevel=0.01)
    for i in range(tiers):
        k = 1 - i * 0.24
        cyl(f'{name}_t{i}', r * k, h * 0.42, (x, y, z + h * (0.42 + i * 0.22)), m=leaf, r2=0.02, verts=14, bevel=0.03, seg=1)


def reeds(name, x, y, n=5, seed=0):
    """Cattails standing in the shallows."""
    rng = random.Random(seed)
    for i in range(n):
        a, dd = rng.uniform(0, TAU), rng.uniform(0.0, 0.22)
        px, py = x + dd * math.cos(a), y + dd * math.sin(a)
        h = rng.uniform(0.75, 1.25)
        lean = (rng.uniform(-7, 7), rng.uniform(-7, 7), 0)
        cyl(f'{name}_stem_{i}', 0.02, h + 0.5, (px, py, WATER_Z - 0.5 + (h + 0.5) / 2), lean, LEAF_DARK, r2=0.012, verts=6, bevel=0)
        if i % 3 != 2:
            cyl(f'{name}_head_{i}', 0.042, 0.2, (px, py, WATER_Z + h - 0.16), lean, '#8a623f', verts=8, bevel=0.02)
        else:
            cyl(f'{name}_leaf_{i}', 0.035, h * 0.8 + 0.4, (px + 0.04, py, WATER_Z - 0.4 + (h * 0.8 + 0.4) / 2), (lean[0] + 6, lean[1] - 8, 0), LEAF, r2=0.004,
                verts=6, bevel=0)


def buoy(name, x, y, speed, lone=False):
    if lone:
        body = [(0, -0.3), (0.25, -0.2), (0.35, 0.02), (0.31, 0.22), (0.17, 0.4), (0.07, 0.45), (0.07, 0.62), (0, 0.62)]
        band_r, light_z = 0.352, 0.7
    else:
        body = [(0, -0.24), (0.21, -0.17), (0.28, 0.0), (0.21, 0.21), (0.08, 0.32), (0.08, 0.56), (0, 0.56)]
        band_r, light_z = 0.282, 0.64
    z = WATER_Z + 0.06
    parts = [lathe(name + '_body', body, (x, y, z), m=ORANGE, verts=18),
             torus(name + '_band', band_r, 0.022, (x, y, z + (0.02 if lone else 0.0)), m=WHITE, seg=18, ring=4),
             sphere(name + '_light', 0.06, (x, y, z + light_z), m=mat('#fff3c4', 0.3, emit=4, emit_color='#ffd98a'), seg=8)]
    if lone:
        parts.append(torus(name + '_ring', 0.11, 0.022, (x, y, z + 0.5), (90, 0, 0), WHITE, seg=12, ring=4))
    b = join(parts, name)
    set_origin(b, (x, y, WATER_Z))
    animate(b, 'bob', amp=0.05, speed=speed, tilt=5)
    return b


# ---------------------------------------------------------------- the island
def build(mode='preview'):
    reset()
    setup_world()
    R, lobes, seed = crescent()
    base, radius_at = island_base(R=R, seed=seed, top=LAWN, lip=LAWN_LIP, soil='#d9c39d', soil2='#bda27c',
                                  rock_c='#93a3a5', lobes=lobes, segments=128)

    def rim(deg, k=1.0):
        a = math.radians(deg)
        r = radius_at(a) * k
        return r * math.cos(a), r * math.sin(a)

    # --- cove: sand, slipway, shed and the boat on its cradle
    shore_y = beach(radius_at)
    slipway(0.25, shore_y + 0.6)
    shed()
    cradle_and_boat()

    # --- high ground with the wind mast, out on the right where the wind arrives clean
    mx, my = 3.7, -0.1
    lathe('mound', MOUND, (mx, my, -0.02), m='#aecf9a', verts=40)
    for i, (a, d, r) in enumerate([(30, 1.1, 0.5), (95, 1.1, 0.42), (150, 1.0, 0.34), (-28, 1.15, 0.36), (62, 0.7, 0.42)]):
        rock(f'mound_rock_{i}', r, (mx + d * math.cos(math.radians(a)), my + d * math.sin(math.radians(a)), mound_h(d) + r * 0.12),
             '#a3b0b1' if i % 2 else '#93a3a5', seed=i + 21, squash=0.62)
    for i, d in enumerate((1.22, 0.96, 0.7, 0.46)):
        a = math.radians(205)
        box(f'mound_step_{i}', (0.6, 0.32, 0.12), (mx + d * math.cos(a), my + d * math.sin(a), mound_h(d) + 0.03), (0, 0, 25),
            '#ddd6c6', bevel=0.04, seg=2)
    vane_top = wind_mast(mx, my, 0.7)

    # --- polar board at the back, simulator desk in the middle, compass rose and GPS on the left horn
    board_top = polar_board(2.2, 2.35, alpha=-34.0)
    desk_top = sim_desk(1.1, 0.3)
    compass_rose(-3.65, -1.45)
    gps_tripod(-4.1, 0.15)
    bench(1.35, -1.22, 8)

    # --- workshop spill-over by the deck: trestle with the spare rudder, toolbox, paint
    tx, ty = -0.72, -0.5
    box('trestle_top', (0.12, 0.95, 0.09), (tx, ty, 0.58), (0, 0, 12), WOOD, bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c, s_ = math.cos(math.radians(12)), math.sin(math.radians(12))
            ex, ey = -sy * 0.38 * s_, sy * 0.38 * c
            beam(f'trestle_leg_{sx}_{sy}', (tx + ex + sx * 0.24 * c, ty + ey + sx * 0.24 * s_, 0.0), (tx + ex + sx * 0.03 * c, ty + ey + sx * 0.03 * s_, 0.56),
                 0.07, m=WOOD_DARK, bevel=0.015)
    rud = [slab_xz('spare_blade', [(-0.09, 0.0), (0.07, 0.02), (0.1, 0.38), (0.09, 0.62), (-0.05, 0.62), (-0.1, 0.3)], 0.045, -0.022, CORAL, bevel=0.014),
           cyl('spare_stock', 0.02, 0.5, (-0.02, 0, 0.6), m=DARK, verts=8, bevel=0)]
    move(rud, (tx + 0.1, ty - 0.15, 0.0), rot_z=102, rot_x=-24)
    box('toolbox', (0.52, 0.26, 0.2), (-0.5, -1.38, 0.1), (0, 0, -18), CORAL, bevel=0.035, seg=2)
    box('toolbox_lid', (0.54, 0.28, 0.06), (-0.5, -1.38, 0.215), (0, 0, -18), '#d9644a', bevel=0.02)
    wire('toolbox_handle', [(-0.62, -1.34, 0.24), (-0.59, -1.35, 0.33), (-0.41, -1.41, 0.33), (-0.38, -1.42, 0.24)], 0.018, DARK, smooth=True, res=3)
    paint_can('paint_a', -1.02, -1.25, CORAL, open_=True)
    paint_can('paint_b', -0.82, -1.08, TEAL)
    paint_can('paint_c', -0.93, -1.17, WHITE, z=0.225)
    rope_coil('coil_a', -3.05, -2.45)
    rope_coil('coil_b', 3.0, -2.0, r=0.19, turns=2)
    box('crate_a', (0.46, 0.46, 0.4), (-2.98, -0.2, 0.2), (0, 0, 14), '#d7a66f', bevel=0.04, seg=2)
    box('crate_b', (0.36, 0.36, 0.32), (-2.94, -0.22, 0.56), (0, 0, -12), '#e2b47e', bevel=0.04, seg=2)

    # lamp post on the tip of the right horn, marking the mouth of the cove
    lx, ly = 3.3, -2.35
    cyl('lamp_post', 0.04, 1.5, (lx, ly, 0.75), m=TEAL_DEEP, verts=10, bevel=0.01)
    cyl('lamp_foot', 0.1, 0.08, (lx, ly, 0.04), m=TEAL_DEEP, verts=12, bevel=0.02)
    sphere('lamp_glow', 0.13, (lx, ly, 1.6), (1, 1, 1.15), warm(), 14)
    lathe('lamp_cap', [(0.17, 0), (0.03, 0.12), (0, 0.12)], (lx, ly, 1.71), m=TEAL_DEEP, verts=14)

    # pebbles and a mooring post on the sand
    for i, (x, y, r) in enumerate([(-2.8, -2.5, 0.07), (-2.62, -2.72, 0.05), (-1.0, -1.85, 0.06), (-2.9, -2.95, 0.05)]):
        sphere(f'pebble_{i}', r, (x, y, 0.03), (1.2, 1, 0.55), '#cfc8b8' if i % 2 else '#b8c2c2', 8)
    cyl('mooring_post', 0.07, 0.5, (-2.72, -2.85, 0.25), m=WOOD_DARK, verts=10, bevel=0.02)
    cyl('mooring_cap', 0.085, 0.05, (-2.72, -2.85, 0.52), m=ROPE, verts=10, bevel=0.015)
    torus('mooring_loop', 0.09, 0.022, (-2.72, -2.85, 0.33), m=ROPE, seg=12, ring=4)
    # --- stepping stones
    stones = [(-0.95, 0.1), (-0.5, 0.2), (0.15, -0.75), (0.45, -1.2), (1.85, -1.05), (2.35, -0.75), (1.7, 1.45), (1.6, 1.85),
              (-2.75, -1.0), (-2.9, -0.65), (-3.45, -0.3), (-3.75, -0.05)]
    for i, (x, y) in enumerate(stones):
        cyl(f'stone_{i}', 0.19 + 0.03 * (i % 3), 0.05, (x, y, 0.02), (0, 0, i * 37), '#e6dfcf', verts=9, bevel=0.02)

    # --- vegetation
    pine_tree('pine_a', (-4.05, 1.9, 0), 2.2, 0.62, leaf=PINE)
    pine_tree('pine_b', (-3.6, 2.9, 0), 1.7, 0.5, leaf=PINE_2)
    pine_tree('pine_c', (-2.3, 3.85, 0), 2.5, 0.68, leaf=PINE)
    pine_tree('pine_d', (-1.1, 4.0, 0), 1.6, 0.48, leaf=PINE_2)
    pine_tree('pine_e', (0.2, 3.75, 0), 2.1, 0.56, leaf=PINE)
    pine_tree('pine_f', (4.05, 2.2, 0), 1.5, 0.46, leaf=PINE_2)
    tree('tree_a', (0.55, 2.65, 0), 1.5, 0.6, leaf='#7dbb8c', leaf2='#5a9f7a', seed=9)
    for i, (x, y, r) in enumerate([(4.25, 1.5, 0.32), (3.55, 2.6, 0.3), (-4.4, 0.95, 0.3), (-4.55, -0.5, 0.26),
                                   (3.6, -2.05, 0.28), (-3.5, -2.75, 0.26), (-0.15, 1.9, 0.24)]):
        bush(f'bush_{i}', (x, y, 0), r, '#7dbb8c' if i % 2 else '#69ab80', seed=i)
    for i, (x, y) in enumerate([(4.7, 0.9), (2.9, 1.3), (-0.2, 0.9), (0.35, -1.3), (-4.5, -1.6), (2.1, -1.9), (4.3, -1.5), (-3.1, 3.5),
                                (1.3, 4.1), (-3.7, -2.6), (2.75, -2.25), (-4.6, 1.3), (-2.75, -1.6)]):
        grass_tuft(f'tuft_{i}', (x, y, 0), seed=i, m='#7fb884')
    for i, (x, y) in enumerate([(0.0, 2.2), (4.6, 0.3), (-4.3, -0.4), (2.6, -1.5), (3.1, 1.75), (-2.9, -3.1)]):
        flower(f'flower_{i}', (x, y, 0), 0.24, (CORAL, WHITE, CORAL)[i % 3], heart=SUNSHINE)

    # --- shore: rocks on the rim and in the shallows, reeds at the horns
    for i, (deg, k, r) in enumerate([(-141, 1.0, 0.42), (-150, 1.02, 0.3), (-41, 1.0, 0.38), (-31, 1.02, 0.3), (22, 0.99, 0.34),
                                     (168, 0.99, 0.36), (100, 1.0, 0.3), (-58, 0.96, 0.24)]):
        x, y = rim(deg, k)
        rock(f'shore_rock_{i}', r, (x, y, -0.06 if k < 1.0 else -0.12), '#a3b0b1' if i % 2 else '#93a3a5', seed=i + 40)
    for i, (deg, k, r) in enumerate([(-137, 1.09, 0.34), (-45, 1.08, 0.3), (-36, 1.1, 0.22), (-146, 1.1, 0.24)]):
        x, y = rim(deg, k)
        rock(f'lake_rock_{i}', r, (x, y, WATER_Z + 0.02), '#93a3a5', seed=i + 60, squash=0.6)
    for i, (deg, k, n) in enumerate([(-52, 1.07, 5), (-62, 1.1, 4), (-20, 1.05, 4), (-158, 1.05, 4)]):
        x, y = rim(deg, k)
        reeds(f'reeds_{i}', x, y, n, seed=i)

    # --- the lake: station-keeping box (exactly four buoys) and the lone search buoy
    cx, cy, side = BOX
    for i, (sx, sy) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        buoy(f'buoy_box_{i}', cx + sx * side / 2, cy + sy * side / 2, 0.85 + 0.12 * i)
    buoy('buoy_search', -5.0, -3.6, 0.75, lone=True)

    hotspot(1, (mx, my, vane_top))
    hotspot(2, board_top)
    hotspot(3, desk_top)
    hotspot(4, (cx, cy, WATER_Z + 0.9))
    finish('sailbot', mode, cam_loc=(-10.4, -16.6, 9.7), cam_target=(0.25, -0.9, 0.8), lens=50)
