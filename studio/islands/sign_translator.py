"""Language in motion: Sign-Translator. A two-camera capture studio, a rigged clay
avatar mid-sign, the 4 x 8 code rack, a 24-frame film strip and the measuring gauge.
Research in progress, so the island shows a studio and its instruments, not a result."""
import math

import bmesh
import kit
from kit import *
from mathutils import Euler, Matrix, Vector

# palette
TEAL_DEEP = '#243e3b'
TEAL = '#2f5a55'
TEAL_MID = '#4f9a8e'
SAGE = '#c8dab8'
SCREEN = '#7fcf9a'
RIG = '#a9c9e6'
RIG_DARK = '#8fb4d6'
GRAPHITE = '#2b3432'
AMBER = '#f2b45c'
GREY = '#9aa3a3'
PART_COLOURS = ('#9dc0e0', '#efe4cc', '#7fcf9a', AMBER)      # body, left hand, right hand, face
GLOW_COLOURS = ('#8cc4f5', '#fff0cf', '#74e79c', '#ffb23e')


# ---------------------------------------------------------------- local helpers
_kit_box, _kit_cyl = box, cyl


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, bevel=0.06, seg=None):
    """kit.box with bevel segments chosen by size, to stay inside the triangle budget."""
    if seg is None:
        seg = 3 if min(size) > 0.3 else (2 if min(size) > 0.09 else 1)
    return _kit_box(name, size, loc, rot, m, bevel, seg)


def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, r2=None, verts=32, bevel=0.04, seg=None):
    if seg is None:
        seg = 3 if r > 0.5 else (2 if r > 0.1 else 1)
    return _kit_cyl(name, r, h, loc, rot, m, r2, verts, bevel, seg)


class Frame:
    """A local coordinate frame: origin plus rotation. Front of a prop is local -Y."""

    def __init__(self, origin, rz=0.0, rx=0.0, M=None):
        self.o = Vector(origin)
        self.M = M if M is not None else (Matrix.Rotation(math.radians(rz), 3, 'Z')
                                          @ Matrix.Rotation(math.radians(rx), 3, 'X'))

    def p(self, x, y, z):
        return self.o + self.M @ Vector((x, y, z))

    def d(self, x, y, z):
        return self.M @ Vector((x, y, z))

    def put(self, ob, loc, rot=(0, 0, 0)):
        R = Euler([math.radians(a) for a in rot]).to_matrix()
        ob.location = self.p(*loc)
        ob.rotation_euler = (self.M @ R).to_euler()
        return ob

    def sub(self, loc, rz=0.0, rx=0.0):
        return Frame(self.p(*loc), M=self.M @ Matrix.Rotation(math.radians(rz), 3, 'Z')
                     @ Matrix.Rotation(math.radians(rx), 3, 'X'))


def bone(name, p0, p1, r0, r1=None, m=RIG, verts=12, n=4):
    """Tapered capsule from p0 to p1 (the rig's bones)."""
    p0, p1 = Vector(p0), Vector(p1)
    r1 = r0 if r1 is None else r1
    length = (p1 - p0).length
    prof = []
    for i in range(n + 1):
        a = -math.pi / 2 + (math.pi / 2) * i / n
        prof.append((r0 * math.cos(a), r0 * math.sin(a)))
    for i in range(n + 1):
        a = (math.pi / 2) * i / n
        prof.append((r1 * math.cos(a), length + r1 * math.sin(a)))
    ob = lathe(name, prof, m=m, verts=verts)
    ob.location = p0
    ob.rotation_euler = (p1 - p0).to_track_quat('Z', 'Y').to_euler()
    return ob


def elbow_ik(S, W, l1, l2, pole):
    d = W - S
    dist = min(d.length, (l1 + l2) * 0.999)
    u = d.normalized()
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    pp = pole - pole.dot(u) * u
    pp.normalize()
    return S + u * a + pp * h


def apply_rotation(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return ob


def multi_box(name, items, m):
    """Many plain boxes in one mesh. items: (centre, 3x3 matrix, (sx, sy, sz))."""
    bm = bmesh.new()
    for c, M, size in items:
        geom = bmesh.ops.create_cube(bm, size=1)
        for v in geom['verts']:
            v.co = c + M @ Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = kit._obj_from_bmesh(bm, name)
    return kit._finish(ob, name, m, smooth=False)


def catmull(ctrl, per=18):
    P = [Vector((x, y, 0)) for x, y in ctrl]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * P[i]) + (-P[i - 1] + P[i + 1]) * t
                              + (2 * P[i - 1] - 5 * P[i] + 4 * P[i + 1] - P[i + 2]) * t * t
                              + (-P[i - 1] + 3 * P[i] - 3 * P[i + 1] + P[i + 2]) * t ** 3))
    out.append(P[-2])
    return out


class Path:
    """Arc-length parametrised ground path."""

    def __init__(self, ctrl):
        self.pts = catmull(ctrl)
        self.cum = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.cum.append(self.cum[-1] + (b - a).length)
        self.length = self.cum[-1]

    def at(self, s):
        s = max(0.0, min(self.length, s))
        for i in range(len(self.cum) - 1):
            if self.cum[i + 1] >= s:
                break
        a, b = self.pts[i], self.pts[i + 1]
        seg = max(self.cum[i + 1] - self.cum[i], 1e-9)
        return a.lerp(b, (s - self.cum[i]) / seg), (b - a).normalized()

    def frame(self, s, z=0.0):
        p, t = self.at(s)
        n = Vector((-t.y, t.x, 0))
        M = Matrix((t, n, Vector((0, 0, 1)))).transposed()
        return Frame((p.x, p.y, z), M=M)


def band(name, path, s0, s1, h, t, z0, m, step=0.06):
    """Film strip standing on its edge along a path."""
    bm = bmesh.new()
    rings = []
    n = max(2, int((s1 - s0) / step))
    for i in range(n + 1):
        p, tg = path.at(s0 + (s1 - s0) * i / n)
        nx, ny = -tg.y * t / 2, tg.x * t / 2
        rings.append([bm.verts.new((p.x - nx, p.y - ny, z0)), bm.verts.new((p.x + nx, p.y + ny, z0)),
                      bm.verts.new((p.x + nx, p.y + ny, z0 + h)), bm.verts.new((p.x - nx, p.y - ny, z0 + h))])
    for a, b in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = kit._obj_from_bmesh(bm, name)
    return kit._finish(ob, name, m, angle=50)


def arc_pts(c, r, a0, a1, z, n=24):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)), z) for i in range(n + 1)]


# ---------------------------------------------------------------- avatar
def build_hand(tag, W, z_dir, y_dir, right, pose, parts, hs=1.0):
    """Palm plus five three-segment fingers. Returns the 15 knuckle joints and the fingertips."""
    Zh = z_dir.normalized()
    Yh = (y_dir - y_dir.dot(Zh) * Zh).normalized()          # palm normal
    Xh = Zh.cross(Yh) * (1 if right else -1)                # toward the thumb
    Mp = Matrix((Yh.cross(Zh), Yh, Zh)).transposed()
    rig = mat(RIG, 0.62)
    jm = mat(TEAL, 0.55)
    joints, tips = [], []

    parts.append(bone(f'{tag}_carpal', W, W + Zh * 0.09 * hs, 0.062 * hs, 0.075 * hs, rig, verts=10, n=3))
    palm = box(f'{tag}_palm', (0.27 * hs, 0.092 * hs, 0.25 * hs), m=rig, bevel=0.04 * hs, seg=4)
    palm.location = W + Zh * 0.19 * hs
    palm.rotation_euler = Mp.to_euler()
    parts.append(palm)

    def chain(name, base, fz, fy, lens, curls, r0, r1):
        p, ang = base, 0.0
        for k, (length, c) in enumerate(zip(lens, curls)):
            ang += math.radians(c)
            q = p + (fz * math.cos(ang) + fy * math.sin(ang)) * length * hs
            ra = (r0 + (r1 - r0) * k / 3) * hs
            rb = (r0 + (r1 - r0) * (k + 1) / 3) * hs
            parts.append(bone(f'{name}_b{k}', p, q, ra, rb, rig, verts=12, n=3))
            joints.append(sphere(f'{name}_j{k}', ra * 1.33, p, m=jm, seg=16))
            p = q
        tips.append(p)

    lens = {'index': (0.118, 0.082, 0.07), 'middle': (0.128, 0.09, 0.075),
            'ring': (0.118, 0.082, 0.07), 'pinky': (0.094, 0.066, 0.06)}
    xs = {'index': 0.099, 'middle': 0.034, 'ring': -0.032, 'pinky': -0.097}
    zs = {'index': 0.315, 'middle': 0.322, 'ring': 0.314, 'pinky': 0.296}
    for f in ('index', 'middle', 'ring', 'pinky'):
        sp = math.radians(pose['spread'][f])
        fz = Zh * math.cos(sp) + Xh * math.sin(sp)
        base = W + (Xh * xs[f] + Zh * zs[f]) * hs
        chain(f'{tag}_{f}', base, fz, Yh, lens[f], pose['curl'][f], 0.031, 0.026)
    tb = pose['thumb']
    u = (Xh * tb['dir'][0] + Yh * tb['dir'][1] + Zh * tb['dir'][2]).normalized()
    c = Xh * tb['toward'][0] + Yh * tb['toward'][1] + Zh * tb['toward'][2]
    v = (c - c.dot(u) * u).normalized()
    chain(f'{tag}_thumb', W + (Xh * 0.118 + Yh * 0.015 + Zh * 0.105) * hs, u, v,
          (0.11, 0.09, 0.075), tb['curl'], 0.037, 0.03)
    assert len(joints) == 15, len(joints)
    parts.extend(joints)
    return joints, tips


OPEN_HAND = {
    'spread': {'index': 11, 'middle': 2, 'ring': -8, 'pinky': -18},
    'curl': {'index': (6, 9, 7), 'middle': (4, 7, 6), 'ring': (7, 10, 8), 'pinky': (10, 12, 9)},
    'thumb': {'dir': (0.82, 0.12, 0.56), 'toward': (-0.3, 0.6, 0.7), 'curl': (4, 10, 8)},
}
CURVED_HAND = {
    'spread': {'index': 7, 'middle': 1, 'ring': -5, 'pinky': -11},
    'curl': {'index': (24, 34, 26), 'middle': (27, 36, 28), 'ring': (28, 36, 28), 'pinky': (27, 34, 26)},
    'thumb': {'dir': (0.72, 0.5, 0.42), 'toward': (-0.25, 0.8, 0.55), 'curl': (8, 22, 24)},
}


def build_avatar(base):
    """Neutral clay mannequin, facing -Y, feet on `base`. Returns (avatar, wrists, tips)."""
    rig = mat(RIG, 0.62)
    rig_d = mat(RIG_DARK, 0.62)
    jm = mat(TEAL, 0.55)
    parts = []

    def P(x, y, z):
        return base + Vector((x, y, z))

    for s in (-1, 1):
        parts.append(box(f'av_foot_{s}', (0.25, 0.44, 0.14), P(s * 0.2, -0.1, 0.07), (0, 0, -s * 7), rig_d,
                         bevel=0.065, seg=4))
        ank, knee, hip = P(s * 0.2, 0, 0.2), P(s * 0.2, -0.035, 0.68), P(s * 0.185, 0, 1.13)
        parts.append(bone(f'av_shin_{s}', ank, knee, 0.088, 0.108, rig))
        parts.append(bone(f'av_thigh_{s}', knee, hip, 0.112, 0.138, rig))
        parts.append(sphere(f'av_ankle_{s}', 0.112, ank, m=jm, seg=16))
        parts.append(sphere(f'av_knee_{s}', 0.138, knee, m=jm, seg=16))
    parts.append(bone('av_pelvis', P(-0.185, 0, 1.13), P(0.185, 0, 1.13), 0.15, 0.15, jm, verts=16))
    torso = lathe('av_torso', [(0, 1.15), (0.2, 1.16), (0.3, 1.25), (0.3, 1.38), (0.265, 1.56),
                               (0.285, 1.74), (0.35, 1.95), (0.37, 2.08), (0.335, 2.19), (0.19, 2.27),
                               (0.0, 2.29)], P(0, 0, 0), m=rig, verts=28)
    torso.scale = (1, 0.7, 1)
    parts.append(torso)
    parts.append(bone('av_neck', P(0, 0, 2.24), P(0, -0.012, 2.38), 0.098, 0.09, rig))
    parts.append(sphere('av_neck_joint', 0.116, P(0, 0, 2.29), m=jm, seg=16))
    parts.append(sphere('av_head', 0.272, P(0, -0.025, 2.56), (0.96, 0.99, 1.06), rig, 28))
    for s in (-1, 1):
        parts.append(sphere(f'av_eye_{s}', 0.029, P(s * 0.095, -0.272, 2.585), (1, 0.6, 1.25), mat(GRAPHITE, 0.4), 10))

    wrists, tips = {}, {}
    # avatar's left hand (world +X): open hand, palm forward. Right hand: curved hand, palm up.
    arms = {
        'l': dict(s=1, W=P(0.45, -0.46, 1.73), z=Vector((-0.14, -0.2, 1.0)), y=Vector((-0.38, -1.0, -0.15)),
                  pole=Vector((0.55, 0.3, -1.0)), pose=OPEN_HAND, right=False),
        'r': dict(s=-1, W=P(-0.41, -0.7, 1.58), z=Vector((0.34, -0.86, 0.3)), y=Vector((0.12, -0.3, 1.0)),
                  pole=Vector((-0.6, 0.35, -1.0)), pose=CURVED_HAND, right=True),
    }
    for key, a in arms.items():
        S = P(a['s'] * 0.475, 0, 2.1)
        E = elbow_ik(S, a['W'], 0.56, 0.5, a['pole'])
        parts.append(bone(f'av_upper_{key}', S, E, 0.106, 0.092, rig))
        parts.append(bone(f'av_fore_{key}', E, a['W'], 0.088, 0.068, rig))
        parts.append(sphere(f'av_shoulder_{key}', 0.145, S, m=jm, seg=16))
        parts.append(sphere(f'av_elbow_{key}', 0.126, E, m=jm, seg=16))
        _, tips[key] = build_hand(f'hand_{key}', a['W'], a['z'], a['y'], a['right'], a['pose'], parts, hs=1.08)
        wrists[key] = a['W']
    avatar = join(parts, 'avatar')
    return avatar, wrists, tips


# ---------------------------------------------------------------- props
def camera_rig(name, pos, yaw, lens_h):
    """Chunky studio camera on a tripod. Local +Y looks at the subject. Returns lens point."""
    F = Frame((pos[0], pos[1], 0), rz=yaw)
    g = mat(GRAPHITE, 0.6)
    top = lens_h - 0.36
    for i, a in enumerate((90, 210, 330)):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        tube(f'{name}_leg_{i}', [F.p(0.05 * ca, 0.05 * sa, top), F.p(0.56 * ca, 0.56 * sa, 0.04)], 0.04, g,
             smooth_curve=False)
        sphere(f'{name}_foot_{i}', 0.065, F.p(0.56 * ca, 0.56 * sa, 0.055), m=CREAM, seg=10)
    torus(f'{name}_spreader', 0.27, 0.022, F.p(0, 0, top * 0.52), m=g, seg=20, ring=6)
    cyl(f'{name}_column', 0.05, 0.3, F.p(0, 0, top + 0.02), m=STEEL_DARK, verts=10, bevel=0.01)
    cyl(f'{name}_hub', 0.1, 0.1, F.p(0, 0, top - 0.02), m=g, verts=14, bevel=0.02)
    cyl(f'{name}_head', 0.12, 0.08, F.p(0, 0, top + 0.15), m=TEAL, verts=16, bevel=0.02)
    tube(f'{name}_pan', [F.p(0.06, -0.05, top + 0.15), F.p(0.3, -0.5, top - 0.02)], 0.026, g, smooth_curve=False)
    sphere(f'{name}_pan_grip', 0.045, F.p(0.3, -0.5, top - 0.02), m=CREAM, seg=10)
    F.put(box(f'{name}_body', (0.36, 0.54, 0.34), m=g, bevel=0.07, seg=4), (0, 0, lens_h))
    F.put(box(f'{name}_band', (0.372, 0.1, 0.352), m=CREAM, bevel=0.02), (0, -0.08, lens_h))
    F.put(cyl(f'{name}_barrel', 0.13, 0.2, m=TEAL, r2=0.155, verts=20, bevel=0.02), (0, 0.36, lens_h), (-90, 0, 0))
    F.put(cyl(f'{name}_lens', 0.115, 0.04, m=mat('#fff0cf', 0.25, emit=4.0, emit_color='#ffd27a'), verts=20,
              bevel=0.01), (0, 0.455, lens_h), (-90, 0, 0))
    F.put(box(f'{name}_handle', (0.07, 0.34, 0.06), m=g, bevel=0.025), (0, 0.0, lens_h + 0.26))
    for k, y in enumerate((-0.13, 0.13)):
        F.put(box(f'{name}_handle_post_{k}', (0.05, 0.05, 0.1), m=g, bevel=0.015), (0, y, lens_h + 0.2))
    F.put(box(f'{name}_monitor', (0.26, 0.05, 0.18), m=g, bevel=0.02), (0.0, -0.3, lens_h + 0.02))
    F.put(box(f'{name}_monitor_face', (0.21, 0.02, 0.13), m=mat('#bfe6dc', 0.3, emit=1.2), bevel=0.008),
          (0.0, -0.325, lens_h + 0.02))
    return F.p(0, 0.475, lens_h), F


def softbox(name, pos, target, h, size=0.82):
    """Light stand with a softbox aimed at `target`."""
    g = mat(GRAPHITE, 0.6)
    x, y = pos
    for i, a in enumerate((80, 200, 320)):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        tube(f'{name}_leg_{i}', [(x, y, 0.5), (x + 0.42 * ca, y + 0.42 * sa, 0.035)], 0.03, g, smooth_curve=False)
    cyl(f'{name}_pole', 0.035, h - 0.03, (x, y, 0.03 + (h - 0.03) / 2), m=STEEL_DARK, verts=10, bevel=0.01)
    cyl(f'{name}_collar', 0.055, 0.1, (x, y, 0.5), m=g, verts=10, bevel=0.015)
    sphere(f'{name}_yoke', 0.075, (x, y, h), m=g, seg=12)
    top = Vector((x, y, h))
    aim = (Vector(target) - top).normalized()
    zl = -aim
    xl = Vector((aim.y, -aim.x, 0)).normalized()
    yl = zl.cross(xl)
    M = Matrix((xl, yl, zl)).transposed()
    centre = top + aim * 0.22
    shell = cyl(f'{name}_shell', size * 0.7071, 0.36, m=g, r2=0.15, verts=4, bevel=0.035)
    shell.location = centre
    shell.rotation_euler = (M @ Matrix.Rotation(math.radians(45), 3, 'Z')).to_euler()
    face = box(f'{name}_face', (size * 0.94, size * 0.94, 0.05), m=mat('#fff6e2', 0.5, emit=1.5, emit_color='#fff0cf'),
               bevel=0.02)
    face.location = centre + aim * 0.185
    face.rotation_euler = M.to_euler()
    rim = box(f'{name}_rim', (size * 1.02, size * 1.02, 0.045), m=CREAM, bevel=0.02)
    rim.location = centre + aim * 0.165
    rim.rotation_euler = M.to_euler()
    return [shell, face, rim]


def sandbag(name, loc, rz=0, m=TEAL):
    b = blob(name, 0.17, (loc[0], loc[1], loc[2] + 0.07), (1.35, 0.9, 0.5), m, seed=len(name) * 7 + int(abs(rz)),
             bumps=0.1, seg=2)
    b.rotation_euler = Euler((0, 0, math.radians(rz)))
    return b


def stick_figure(F, side, arms, m, out):
    """Tiny pose on a frame card. F is the card frame; side = +1/-1 picks the face."""
    y = side * 0.046

    def limb(p0, ang, length):
        a = math.radians(ang)
        cx, cz = p0[0] + math.cos(a) * length / 2, p0[1] + math.sin(a) * length / 2
        out.append(F.put(box('fig_limb', (length, 0.02, 0.027), m=m, bevel=0), (cx, y, cz), (0, -ang, 0)))

    out.append(F.put(sphere('fig_head', 0.034, m=m, seg=8, scale=(1, 0.35, 1)), (0, y, 0.082)))
    limb((0, -0.045), 90, 0.1)
    limb((0, -0.04), 245, 0.085)
    limb((0, -0.04), 295, 0.085)
    limb((0, 0.03), 180 - arms[0], 0.075)
    limb((0, 0.03), arms[1], 0.075)


# ---------------------------------------------------------------- build
def build(mode='preview'):
    reset()
    setup_world()
    base, radius_at = island_base(R=5.0, seed=27, top='#cddfc6', lip='#a9c8ac', soil='#7ea398',
                                  soil2='#5a857c', rock_c='#6c7d7a',
                                  lobes=((2, 0.04), (3, 0.05), (4, 0.02)))
    OX, OY = -0.1, 0.2                     # the studio layout is centred slightly off the origin
    for ob in (base, bpy.data.objects['base_stratum']):
        ob.location.x += OX
        ob.location.y += OY
    g = mat(GRAPHITE, 0.6)
    amber_glow = mat(AMBER, 0.35, emit=2.4, emit_color='#ffab3a')

    # ------------------------------------------------ 1. capture stage and avatar
    C = Vector((-0.3, 1.2, 0.0))
    lathe('stage', [(0, 0), (1.9, 0), (1.9, 0.06), (1.8, 0.085), (1.8, 0.16), (1.75, 0.2), (0, 0.2)],
          (C.x, C.y, 0), m=CREAM, verts=56)
    lathe('stage_trim', [(1.915, 0.0), (1.915, 0.045), (1.81, 0.045), (1.81, 0.0)], (C.x, C.y, 0.005), m=TEAL, verts=56)
    cyl('stage_mat', 1.6, 0.03, (C.x, C.y, 0.212), m='#93d7a9', verts=56, bevel=0.012)
    top_z = 0.227
    # green-screen backdrop: curved wall wrapping behind and to the avatar's right
    a0, a1, r_in, r_out, wall_h = 14, 172, 1.97, 2.1, 2.6
    n = 46
    outline = [(r_out * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r_out * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
               for i in range(n + 1)]
    outline += [(r_in * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r_in * math.sin(math.radians(a1 - (a1 - a0) * i / n)))
                for i in range(n + 1)]
    prism('green_screen', outline, wall_h, (C.x, C.y, 0), m=mat(SCREEN, 0.8), bevel=0.05)
    # plywood back of the flats, so the backdrop reads as a built set piece from behind
    nb = 30
    skin = [((r_out + 0.03) * math.cos(math.radians(a0 + 1.5 + (a1 - a0 - 3) * i / nb)),
             (r_out + 0.03) * math.sin(math.radians(a0 + 1.5 + (a1 - a0 - 3) * i / nb))) for i in range(nb + 1)]
    skin += [((r_out - 0.03) * math.cos(math.radians(a1 - 1.5 - (a1 - a0 - 3) * i / nb)),
              (r_out - 0.03) * math.sin(math.radians(a1 - 1.5 - (a1 - a0 - 3) * i / nb))) for i in range(nb + 1)]
    prism('screen_back', skin, wall_h - 0.12, (C.x, C.y, 0.05), m='#e6dcc4', bevel=0.012, seg=1)
    tube('screen_cap', arc_pts(C, (r_in + r_out) / 2, a0 + 1, a1 - 1, wall_h + 0.005, 16), 0.05, CREAM, res=3)
    tube('screen_foot', arc_pts(C, r_out + 0.02, a0 + 1, a1 - 1, 0.05, 16), 0.05, TEAL, res=3)
    for i, a in enumerate((48, 84, 120, 156)):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        box(f'brace_post_{i}', (0.1, 0.1, 2.3), (C.x + (r_out + 0.05) * ca, C.y + (r_out + 0.05) * sa, 1.15), (0, 0, a), g,
            bevel=0.025)
        tube(f'brace_{i}', [(C.x + (r_out + 0.08) * ca, C.y + (r_out + 0.08) * sa, 1.85),
                            (C.x + (r_out + 0.95) * ca, C.y + (r_out + 0.95) * sa, 0.05)], 0.04, g, smooth_curve=False)
        sandbag(f'brace_bag_{i}', (C.x + (r_out + 0.9) * ca, C.y + (r_out + 0.9) * sa, 0.0), a + 90,
                TEAL if i % 2 else '#3d6f69')
    tube('brace_rail', arc_pts(C, r_out + 0.11, 48, 156, 1.3, 10), 0.035, g, res=3)

    avatar, wrists, tips = build_avatar(Vector((C.x, C.y, top_z)))
    wrist_obs = {}
    for key, W in wrists.items():
        w = sphere(f'wrist_{key}', 0.098, W, m=amber_glow, seg=16)
        animate(w, 'pulse', speed=1.3 if key == 'l' else 1.6)
        wrist_obs[key] = w
    # tape marks on the stage
    tape = mat(AMBER, 0.7)
    box('tape_t_bar', (0.62, 0.075, 0.02), (C.x, C.y - 0.36, top_z + 0.008), m=tape, bevel=0.006)
    box('tape_t_stem', (0.075, 0.34, 0.02), (C.x, C.y - 0.56, top_z + 0.008), m=tape, bevel=0.006)
    for s in (-1, 1):
        box(f'tape_corner_{s}', (0.26, 0.07, 0.02), (C.x + s * 0.62, C.y + 0.25, top_z + 0.008), (0, 0, s * 40), WHITE,
            bevel=0.006)

    # ------------------------------------------------ 2. two cameras at 90 degrees
    lens_f, Ff = camera_rig('cam_front', (C.x, C.y - 3.4), 0, 1.62)
    lens_s, Fs = camera_rig('cam_side', (C.x + 3.4, C.y), 90, 1.78)
    ray_m = mat('#f2a744', 0.4, emit=1.7, emit_color='#f59f26')
    for cname, lens in (('front', lens_f), ('side', lens_s)):
        for key, W in wrists.items():
            tube(f'ray_{cname}_{key}', [tuple(lens), tuple(W)], 0.02, ray_m, smooth_curve=False)
    # dashed tape lines along both optical axes: they meet at a right angle under the avatar
    for i, y in enumerate((-2.15, -2.5)):
        box(f'axis_front_{i}', (0.075, 0.22, 0.02), (C.x, C.y + y, 0.008), m=WHITE, bevel=0.006)
    for i, x in enumerate((2.15, 2.5)):
        box(f'axis_side_{i}', (0.22, 0.075, 0.02), (C.x + x, C.y, 0.008), m=WHITE, bevel=0.006)
    for F, nm in ((Ff, 'f'), (Fs, 's')):
        for i, a in enumerate((90, 210, 330)):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            F.put(box(f'tape_foot_{nm}_{i}', (0.2, 0.06, 0.02), m=tape, bevel=0.006), (0.56 * ca, 0.56 * sa, 0.008),
                  (0, 0, a + 90))
    sandbag('cam_bag_f', tuple(Ff.p(0.5, -0.28, 0)), 20, '#3d6f69')
    sandbag('cam_bag_s', tuple(Fs.p(-0.5, -0.28, 0)), 110)

    # ------------------------------------------------ 3. the code rack: 4 parts x 8 residual stages
    R0 = Frame((-3.3, -0.8, 0), rz=0)
    cab_h = 0.5
    R0.put(box('rack_cabinet', (1.66, 0.56, cab_h), m=TEAL, bevel=0.06), (0, 0, cab_h / 2))
    R0.put(box('rack_cabinet_top', (1.72, 0.62, 0.06), m=CREAM, bevel=0.025), (0, 0, cab_h + 0.02))
    for i in range(3):
        R0.put(box(f'rack_vent_{i}', (0.34, 0.03, 0.035), m=TEAL_DEEP, bevel=0.01), (-0.42, -0.283, 0.17 + i * 0.08))
    for i in range(3):
        led = R0.put(sphere(f'rack_led_{i}', 0.03, m=amber_glow if i != 1 else mat(SCREEN, 0.4, emit=2.5), seg=8),
                     (0.2 + i * 0.13, -0.285, 0.33))
    R0.put(box('rack_slot', (0.05, 0.16, 0.47), m=TEAL_DEEP, bevel=0.015), (0.832, 0.0, 0.245))
    pz0, pitch_r, bh = 0.58, 0.17, 0.125
    panel_h = 1.46
    for s in (-1, 1):
        R0.put(box(f'rack_post_{s}', (0.1, 0.1, panel_h + 0.1), m=g, bevel=0.03), (s * 0.85, 0, cab_h + 0.04 + (panel_h + 0.1) / 2))
    R0.put(box('rack_panel', (1.62, 0.07, panel_h), m='#2c4b47', bevel=0.025), (0, 0, pz0 + panel_h / 2))
    beam_z = pz0 + panel_h + 0.05
    R0.put(box('rack_beam', (1.86, 0.16, 0.09), m=g, bevel=0.03), (0, 0, beam_z))
    R0.put(box('rack_back_box', (0.6, 0.14, 0.5), m=TEAL, bevel=0.04), (0.2, 0.1, 1.5))
    R0.put(box('rack_back_box2', (0.36, 0.12, 0.3), m=g, bevel=0.04), (-0.35, 0.09, 1.05))
    glow_pattern = {0: (0, 1, 3, 6), 1: (0, 2, 5), 2: (0, 1, 4, 7), 3: (0, 3, 5)}
    glow = ([], [])
    n_blocks = 0
    for c in range(4):
        xc = (c - 1.5) * 0.36
        for r in range(8):
            zc = pz0 + 0.0725 + bh / 2 + (7 - r) * pitch_r
            lit = r in glow_pattern[c]
            m = mat(GLOW_COLOURS[c], 0.4, emit=1.25) if lit else mat(PART_COLOURS[c], 0.7)
            b = R0.put(box(f'code_{c}_{r}', (0.27, 0.14, bh), m=m, bevel=0.03, seg=2), (xc, -0.09, zc))
            n_blocks += 1
            if lit:
                glow[(c + r) % 2].append(b)
    assert n_blocks == 32
    for k, grp in enumerate(glow):
        ob = join(grp, f'code_glow_{k}')
        animate(ob, 'pulse', speed=1.1 + 0.5 * k)
    # icons above the columns: torso, left hand, right hand, face
    iz = beam_z + 0.045
    dark = mat(GRAPHITE, 0.5)
    k = 1.42
    xi = [(c - 1.5) * 0.36 for c in range(4)]
    R0.put(prism('icon_torso', [(x * k, y * k) for x, y in ((-0.07, 0), (0.07, 0), (0.08, 0.1), (0.125, 0.17),
                                                           (0.105, 0.21), (0.042, 0.232), (-0.042, 0.232),
                                                           (-0.105, 0.21), (-0.125, 0.17), (-0.08, 0.1))], 0.09,
                 m=PART_COLOURS[0], bevel=0.02), (xi[0], 0.045, iz), (90, 0, 0))
    R0.put(cyl('icon_torso_neck', 0.045, 0.07, m=PART_COLOURS[0], verts=10, bevel=0.01), (xi[0], 0, iz + 0.25 * k))
    for c, thumb in ((1, 1), (2, -1)):
        col = PART_COLOURS[c]
        R0.put(box(f'icon_palm_{c}', (0.15 * k, 0.09, 0.12 * k), m=col, bevel=0.035), (xi[c], 0, iz + 0.06 * k))
        for j, (dx, fh) in enumerate(((-0.054, 0.075), (-0.018, 0.1), (0.018, 0.11), (0.054, 0.09))):
            R0.put(box(f'icon_finger_{c}_{j}', (0.032 * k, 0.075, fh * k), m=col, bevel=0.016),
                   (xi[c] + dx * thumb * k, 0, iz + (0.11 + fh / 2) * k))
        R0.put(box(f'icon_thumb_{c}', (0.036 * k, 0.075, 0.1 * k), m=col, bevel=0.016), (xi[c] + thumb * 0.095 * k, 0, iz + 0.09 * k),
               (0, thumb * 38, 0))
    R0.put(cyl('icon_face', 0.118 * k, 0.09, m=PART_COLOURS[3], verts=24, bevel=0.02), (xi[3], 0, iz + 0.125 * k), (90, 0, 0))
    for sgn in (-1, 1):
        R0.put(sphere(f'icon_eye_{sgn}', 0.028, m=dark, seg=8), (xi[3] + sgn * 0.058, -0.046, iz + 0.15 * k))
    R0.put(box('icon_mouth', (0.1, 0.03, 0.026), m=dark, bevel=0.008), (xi[3], -0.045, iz + 0.085 * k))

    # ------------------------------------------------ 4. film strip: 24 frames per second
    path = Path([(-2.8, -0.8), (-2.35, -0.8), (-1.9, -1.02), (-1.6, -1.7), (-1.75, -2.5), (-1.5, -3.3),
                 (-0.75, -3.78), (0.25, -3.6), (0.95, -3.75), (1.35, -4.1)])
    strip_h, strip_t = 0.42, 0.045
    band('film_strip', path, 0.0, path.length, strip_h, strip_t, 0.0, mat(GRAPHITE, 0.5))
    pe, _ = path.at(path.length)
    cyl('film_end', 0.05, strip_h + 0.06, (pe.x, pe.y, (strip_h + 0.06) / 2), m=CREAM, verts=12, bevel=0.015)
    lead = 0.62
    pitch = min(0.29, (path.length - lead - 0.1) / 24)
    card_w = pitch - 0.055
    poses = {3: (-50, -45), 8: (15, -40), 13: (40, -25), 18: (-30, 30), 22: (-10, 20)}
    bob_index = 13
    cards, figs, bob_parts, sprockets = [], [], [], []
    fig_m = mat(TEAL_DEEP, 0.5)
    for i in range(24):
        s = lead + (i + 0.5) * pitch
        lift = 0.2 if i == bob_index else 0.0
        F = path.frame(s, strip_h / 2 + lift)
        col = '#dcebf6' if i in poses else PAPER
        card = F.put(box(f'frame_{i:02d}', (card_w, 0.08, 0.27), m=col, bevel=0.022, seg=2), (0, 0, 0))
        tgt = bob_parts if i == bob_index else cards
        tgt.append(card)
        if i in poses:
            for side in (-1, 1):
                stick_figure(F, side, poses[i], fig_m, bob_parts if i == bob_index else figs)
        for k in range(3):
            Fq = path.frame(lead + (i + (k + 0.5) / 3) * pitch, 0)
            for z in (0.038, strip_h - 0.038):
                sprockets.append((Fq.p(0, 0, z), Fq.M, (0.045, strip_t + 0.016, 0.036)))
    assert len(cards) + 1 == 24
    join(cards, 'film_frames')
    join(figs, 'film_poses')
    multi_box('film_sprockets', sprockets, PAPER)
    bob_card = join(bob_parts, 'frame_card_bob')
    pb, _ = path.at(lead + (bob_index + 0.5) * pitch)
    set_origin(bob_card, (pb.x, pb.y, strip_h / 2 + 0.2))
    animate(bob_card, 'bob', amp=0.05, speed=1.1)

    # ------------------------------------------------ 5. the instrument: a dial gauge
    G = Frame((3.3, -1.25, 0))
    hub_z, dial_r = 1.5, 0.74
    lathe('gauge_base', [(0, 0), (0.46, 0), (0.46, 0.06), (0.4, 0.1), (0.13, 0.15), (0, 0.15)], tuple(G.p(0, 0, 0)), m=TEAL,
          verts=32)
    G.put(cyl('gauge_column', 0.075, 0.7, m=CREAM, verts=14, bevel=0.02), (0, 0, 0.47))
    G.put(cyl('gauge_collar', 0.11, 0.12, m=g, verts=14, bevel=0.03), (0, 0, 0.78))
    G.put(cyl('gauge_body', dial_r, 0.26, m=TEAL, verts=48, bevel=0.05), (0, 0, hub_z), (90, 0, 0))
    G.put(torus('gauge_rim', dial_r - 0.035, 0.05, m=CREAM, seg=48, ring=8), (0, -0.14, hub_z), (90, 0, 0))
    G.put(cyl('gauge_face', dial_r - 0.07, 0.05, m=PAPER, verts=48, bevel=0.01), (0, -0.135, hub_z), (90, 0, 0))
    G.put(box('gauge_back_box', (0.5, 0.12, 0.34), m=g, bevel=0.04), (0, 0.17, hub_z - 0.1))
    th0, th1 = 210.0, -30.0
    for i in range(13):
        th = th0 + (th1 - th0) * i / 12
        big = i % 3 == 0
        rr = 0.385 if big else 0.4
        G.put(box(f'gauge_tick_{i}', (0.03, 0.03, 0.11 if big else 0.07), m=g, bevel=0),
              (rr * math.cos(math.radians(th)), -0.165, hub_z + rr * math.sin(math.radians(th))), (0, 90 - th, 0))
    needle_th = 100.0
    marks = ((th0, GREY, 0.0), (needle_th, AMBER, 1.2), (th1, '#3fae6c', 0.0))      # blank, generated, real
    for i, (th, col, em) in enumerate(marks):
        G.put(box(f'gauge_mark_{i}', (0.17, 0.06, 0.16), m=mat(col, 0.5, emit=em, emit_color='#ffab3a' if em else None),
                  bevel=0.035, seg=2),
              (0.555 * math.cos(math.radians(th)), -0.175, hub_z + 0.555 * math.sin(math.radians(th))), (0, 90 - th, 0))
    needle = join([
        G.put(prism('needle_blade', [(-0.045, -0.13), (0.045, -0.13), (0.015, 0.46), (-0.015, 0.46)], 0.035, m=g, bevel=0.008,
                    seg=1), (0, -0.2, hub_z), (90, 90 - needle_th, 0)),
        G.put(cyl('needle_hub', 0.085, 0.07, m=CREAM, verts=18, bevel=0.02), (0, -0.215, hub_z), (90, 0, 0)),
        G.put(cyl('needle_pin', 0.035, 0.09, m=g, verts=10, bevel=0.01), (0, -0.22, hub_z), (90, 0, 0)),
    ], 'gauge_needle')
    apply_rotation(needle)
    set_origin(needle, tuple(G.p(0, -0.215, hub_z)))
    animate(needle, 'sway', amp=3.0, speed=0.8, axis='y')

    # ------------------------------------------------ ground detail
    # lights
    chest = (C.x, C.y, top_z + 1.9)
    softbox('softbox_a', (-3.2, 0.95), chest, 2.55)
    softbox('softbox_b', (2.5, 2.9), chest, 2.75)
    sandbag('light_bag_a', (-3.5, 1.22, 0), 60)
    sandbag('light_bag_b', (2.82, 3.12, 0), -30, '#3d6f69')
    # flight case with the laptop, and the empty director's stool
    K = Frame((1.5, -2.3, 0), rz=8)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        K.put(sphere(f'case_wheel_{i}', 0.055, m=g, seg=10), (sx * 0.4, sy * 0.22, 0.055))
    K.put(box('case_body', (1.0, 0.62, 0.52), m=TEAL, bevel=0.035), (0, 0, 0.34))
    K.put(box('case_seam', (1.02, 0.64, 0.05), m=STEEL, bevel=0.015), (0, 0, 0.42))
    for i, (sx, sy, sz) in enumerate([(a, b, c) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]):
        K.put(sphere(f'case_corner_{i}', 0.058, m=STEEL, seg=10), (sx * 0.475, sy * 0.285, 0.34 + sz * 0.235))
    for i, x in enumerate((-0.3, 0.3)):
        K.put(box(f'case_latch_{i}', (0.1, 0.035, 0.13), m=STEEL_DARK, bevel=0.015), (x, -0.315, 0.42))
    K.put(box('laptop_base', (0.56, 0.38, 0.04), m=STEEL, bevel=0.015), (-0.12, 0.0, 0.62))
    L = K.sub((-0.12, 0.19, 0.64), rx=-16)
    L.put(box('laptop_lid', (0.56, 0.035, 0.38), m=STEEL, bevel=0.015), (0, 0, 0.19))
    L.put(box('laptop_screen', (0.5, 0.014, 0.31), m=mat('#2c4b47', 0.3, emit=0.5, emit_color='#3f7f78'), bevel=0.006), (0, -0.02, 0.195))
    for i, col in enumerate(PART_COLOURS):
        L.put(box(f'laptop_chip_{i}', (0.075, 0.012, 0.075), m=mat(col, 0.4, emit=1.0), bevel=0.01),
              (-0.165 + i * 0.11, -0.03, 0.25))
    L.put(box('laptop_timeline', (0.4, 0.012, 0.026), m=PAPER, bevel=0.006), (0, -0.03, 0.12))
    L.put(box('laptop_playhead', (0.03, 0.014, 0.07), m=mat(AMBER, 0.4, emit=2.0), bevel=0.006), (-0.04, -0.032, 0.12))
    K.put(torus('tape_roll', 0.075, 0.034, m=tape, seg=18, ring=8), (0.33, -0.12, 0.634))
    St = Frame((1.62, -3.25, 0), rz=-12)
    for i, y in enumerate((-0.19, 0.19)):
        tube(f'stool_leg_a_{i}', [tuple(St.p(-0.25, y, 0.03)), tuple(St.p(0.25, y, 0.8))], 0.032, WOOD, smooth_curve=False)
        tube(f'stool_leg_b_{i}', [tuple(St.p(0.25, y, 0.03)), tuple(St.p(-0.25, y, 0.8))], 0.032, WOOD, smooth_curve=False)
    for i, x in enumerate((-0.25, 0.25)):
        tube(f'stool_rail_{i}', [tuple(St.p(x, -0.21, 0.8)), tuple(St.p(x, 0.21, 0.8))], 0.032, WOOD, smooth_curve=False)
        tube(f'stool_back_post_{i}', [tuple(St.p(x, -0.2, 0.8)), tuple(St.p(x, -0.23, 1.26))], 0.03, WOOD, smooth_curve=False)
    tube('stool_footrest', [tuple(St.p(-0.14, 0.19, 0.33)), tuple(St.p(0.14, 0.19, 0.33))], 0.028, WOOD, smooth_curve=False)
    St.put(box('stool_seat', (0.5, 0.42, 0.05), m=CREAM, bevel=0.02), (0, 0, 0.815))
    St.put(box('stool_back', (0.54, 0.045, 0.17), m=TEAL_MID, bevel=0.02), (0, -0.225, 1.17))
    # cables
    cable = mat(GRAPHITE, 0.55)
    z = 0.032
    tube('cable_front', [tuple(Ff.p(0.0, -0.15, z)), (0.2, -3.0, z), (0.7, -2.72, z), (0.95, -3.0, z), (1.3, -2.88, z),
                         tuple(K.p(-0.2, -0.36, z))], 0.03, cable, res=5)
    tube('cable_side', [tuple(Fs.p(0.0, 0.0, z)), (2.9, 0.6, z), (2.45, 0.1, z), (2.3, -0.6, z), (1.95, -1.3, z),
                        tuple(K.p(0.3, 0.36, z))], 0.03, cable, res=5)
    tube('cable_gauge', [tuple(G.p(-0.3, -0.1, z)), (2.65, -1.45, z), (2.3, -1.78, z), tuple(K.p(0.52, 0.2, z))], 0.028,
         mat(TEAL, 0.55), res=5)
    tube('cable_rack', [tuple(R0.p(-0.3, 0.3, z)), (-3.75, -0.1, z), (-3.3, 0.25, z), (-2.8, 0.05, z), (-2.45, 0.35, z),
                        (C.x - 1.93, C.y - 0.5, z)], 0.028, mat(TEAL, 0.55), res=5)
    tube('cable_light_a', [(-3.2, 0.95, z), (-3.0, 1.45, z), (-2.78, 1.62, z), (C.x + 2.13 * math.cos(math.radians(168)),
                                                                              C.y + 2.13 * math.sin(math.radians(168)), z)],
         0.028, cable, res=4)
    tube('cable_light_b', [(2.5, 2.9, z), (2.3, 3.5, z), (1.7, 4.0, z), (0.7, 4.42, z), (-0.3, 4.45, z), (-0.9, 4.22, z)],
         0.028, cable, res=5)
    box('power_box', (0.34, 0.22, 0.14), (-0.95, 4.2, 0.07), (0, 0, 10), g, bevel=0.04)
    sphere('power_led', 0.028, (-0.95, 4.14, 0.15), m=amber_glow, seg=8)
    # a cable drum behind the backdrop, and a spare case
    lathe('drum', [(0, 0), (0.3, 0), (0.3, 0.05), (0.14, 0.06), (0.14, 0.28), (0.3, 0.29), (0.3, 0.34), (0, 0.34)],
          (-2.6, 3.15, 0), m=WOOD, verts=24)
    for i in range(3):
        torus(f'drum_coil_{i}', 0.19, 0.035, (-2.6, 3.15, 0.1 + i * 0.065), m=cable, seg=20, ring=6)
    box('spare_case', (0.7, 0.5, 0.4), (2.9, -2.6, 0.2), (0, 0, 28), '#3d6f69', bevel=0.04)
    box('spare_case_seam', (0.72, 0.52, 0.04), (2.9, -2.6, 0.27), (0, 0, 28), STEEL, bevel=0.012)

    # sage shrubs, tufts and stones around the rim, kept clear of the equipment
    sages = ('#9fc2a0', '#86ad90', '#b3cfa6', '#79a287')
    keep = [(0.02, 4.23, .3), (-1.83, 3.84, .3), (1.74, 3.47, .3), (-3.09, 2.44, .3), (-0.95, 4.2, .3), (0.7, 4.42, .12),
            (-0.3, 4.45, .12), (1.7, 4.0, .12), (2.3, 3.5, .12), (2.5, 2.9, .5), (2.82, 3.12, .25), (3.38, 1.685, .2),
            (3.38, 0.7, .28), (3.3, -1.25, .52), (2.9, -2.6, .5), (1.62, -3.25, .42), (1.35, -4.1, .14), (0.95, -3.75, .12),
            (0.25, -3.6, .12), (-0.25, -3.72, .12), (-0.75, -3.78, .12), (-1.5, -3.3, .12), (-1.7, -2.9, .12),
            (-4.2, -0.8, .35), (-3.6, -0.8, .4), (-3.2, 0.95, .48), (-3.5, 1.22, .25), (-2.6, 3.15, .34),
            (-3.75, -0.1, .12), (-0.3, -2.2, .7), (1.5, -2.3, .7), (2.45, 0.1, .1), (2.3, -0.6, .1)]
    keep += [(C.x + 2.0 * math.cos(a), C.y + 2.0 * math.sin(a), 0.25) for a in [math.radians(d) for d in range(0, 360, 12)]]
    keep += [(path.at(path.length * i / 30)[0].x, path.at(path.length * i / 30)[0].y, 0.22) for i in range(31)]

    def rim(deg, k):
        a = math.radians(deg)
        r = radius_at(a) * k
        return (OX + r * math.cos(a), OY + r * math.sin(a), 0)

    def free(p, r):
        return all(math.hypot(p[0] - x, p[1] - y) > kr + r for x, y, kr in keep)

    n_shrub = 0
    for i, deg in enumerate((6, 31, 58, 77, 112, 137, 163, 181, 206, 229, 262, 301, 322, 347)):
        r = (0.4, 0.28, 0.36, 0.25, 0.42)[i % 5] * (0.7 if 235 < deg < 300 else 1.0)
        for k in (0.9, 0.85, 0.95):
            p = rim(deg, k)
            if free(p, r * 1.05):
                bush(f'shrub_{i}', p, r, sages[i % 4], seed=i + 3)
                keep.append((p[0], p[1], r * 1.1))
                n_shrub += 1
                break
    for i, (deg, k, r) in enumerate([(226, 0.6, 0.27), (318, 0.6, 0.22), (350, 0.62, 0.22)]):
        p = rim(deg, k)
        if free(p, r):
            bush(f'shrub_in_{i}', p, r, sages[(i + 2) % 4], seed=i + 60)
            keep.append((p[0], p[1], r * 1.1))
            n_shrub += 1
    n_tuft = 0
    for i, deg in enumerate(range(10, 360, 11)):
        p = rim(deg, (0.92, 0.78, 0.87, 0.7)[i % 4])
        if free(p, 0.14):
            grass_tuft(f'tuft_{i}', p, 0.26, n=4, m='#84ad8f', seed=i)
            keep.append((p[0], p[1], 0.14))
            n_tuft += 1
    n_stone = 0
    for i, deg in enumerate(range(20, 360, 29)):
        p = rim(deg, 0.93 if i % 2 else 0.8)
        r = 0.2 + 0.03 * (i % 3)
        if free(p, r * 0.8):
            rock(f'stone_{i}', r, (p[0], p[1], -0.01), '#9aa9a5' if i % 2 else '#b6c1bd', seed=i + 5)
            n_stone += 1
    print(f'[island] shrubs {n_shrub}, tufts {n_tuft}, stones {n_stone}')

    hotspot(1, tuple(Ff.p(0, 0, 2.25)))
    hl = max(tips['l'], key=lambda v: v.z)
    hotspot(2, ((wrists['l'].x + wrists['r'].x) / 2, wrists['l'].y - 0.1, hl.z + 0.22))
    hotspot(3, tuple(R0.p(0, 0, beam_z + 0.55)))
    hotspot(4, tuple(G.p(0, 0, hub_z + dial_r + 0.28)))
    finish('sign-translator', mode, cam_loc=(-9.5, -13.8, 8.3), cam_target=(-0.1, -0.2, 1.0), lens=50)
