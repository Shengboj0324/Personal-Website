"""Releaf: an iOS app for everyday sustainability.

A giant phone running the on-device waste classifier, the five-bin sorting line,
the knowledge-graph mobile, "My Tree" with its 11 levels and water drops, the
upcycling workbench and the passive carbon tracker (walk, bicycle, bus, car).
"""
import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

import kit
from kit import *

# palette (Releaf design system)
EMERALD = '#0FA968'
EM_LIGHT = '#34D399'
EM_DEEP = '#0B7E4E'
FOREST = '#0A3D2C'
CLAY = '#E2774E'
CLAY_DARK = '#c25f3a'
CITRON = '#C2EE4A'
OFF = '#F6F7F2'
STONE = '#e9ecdf'
DROP = '#4fb7e8'
BLUE = '#4b9fd8'
BLUE_DARK = '#357fb5'
CHAR = '#5a6763'
CHAR_DARK = '#3d4845'
GLASS = '#cfeef0'
CARD = '#d9aa74'
DARK = '#18231f'
SCREEN_IMG = '/Users/jiangshengbo/Personal-Website/assets/releaf.webp'

R = math.radians


# ---------------------------------------------------------------- local helpers
def flat(obs):
    out = []
    for o in (obs if isinstance(obs, (list, tuple)) else [obs]):
        if isinstance(o, (list, tuple)):
            out.extend(flat(o))
        else:
            out.append(o)
    return out


def xf(obs, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Move a group of freshly built objects as one rigid body (rotate, then translate)."""
    m = Matrix.Translation(loc) @ Euler([R(a) for a in rot]).to_matrix().to_4x4()
    for o in flat(obs):
        o.matrix_basis = m @ o.matrix_basis
    return obs


def group(name, parts):
    return join(flat(parts), name)


def freeze(ob):
    """Apply the object's transform to its mesh so its rotation is identity."""
    ob.data.transform(ob.matrix_basis)
    ob.matrix_basis = Matrix.Identity(4)
    return ob


def tbox(name, size, loc, rot=(0, 0, 0), m=WHITE, taper=(0.86, 1.0), bevel=0.06, seg=3):
    """Rounded box whose bottom is narrower than its top (a bin body)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        kx, ky = taper if v.co.z < 0 else (1, 1)
        v.co.x *= size[0] * kx
        v.co.y *= size[1] * ky
        v.co.z *= size[2]
    ob = kit._obj_from_bmesh(bm, name)
    kit._bevel(ob, bevel, seg)
    place(ob, loc, rot)
    return kit._finish(ob, name, m)


def sbox(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, bevel=0.06, seg=2):
    """Rounded box with a two-segment bevel, for small props."""
    return box(name, size, loc, rot, m, bevel, seg)


def rrect(w, h, r, n=6):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = R(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def tr(outline, ang=0.0, s=1.0, dx=0.0, dy=0.0, mirror=False):
    c, sn = math.cos(R(ang)), math.sin(R(ang))
    out = []
    for x, y in outline:
        if mirror:
            x = -x
        out.append((dx + s * (x * c - y * sn), dy + s * (x * sn + y * c)))
    return out


def circle(r, n=12, sy=1.0):
    return [(r * math.cos(TAU * i / n), r * sy * math.sin(TAU * i / n)) for i in range(n)]


def arc_arrow(a0, sweep=76, rad=0.125, w=0.052, head=0.04, n=6):
    ro, ri = rad + w / 2, rad - w / 2
    pts = [(ro * math.cos(R(a0 + sweep * i / n)), ro * math.sin(R(a0 + sweep * i / n))) for i in range(n + 1)]
    a1, at = R(a0 + sweep), R(a0 + sweep + 32)
    pts.append(((ro + head) * math.cos(a1), (ro + head) * math.sin(a1)))
    pts.append((rad * math.cos(at), rad * math.sin(at)))
    pts.append(((ri - head) * math.cos(a1), (ri - head) * math.sin(a1)))
    pts += [(ri * math.cos(R(a0 + sweep * i / n)), ri * math.sin(R(a0 + sweep * i / n))) for i in range(n, -1, -1)]
    return pts


def leaf_outline(length=0.22, width=0.075, n=7):
    top = [(-length / 2 + length * i / n, width * math.sin(math.pi * i / n) ** 0.8) for i in range(n + 1)]
    bot = [(-length / 2 + length * i / n, -width * math.sin(math.pi * i / n) ** 0.8) for i in range(n - 1, 0, -1)]
    return top + bot


def heart_outline(s=0.3, n=28):
    pts = []
    for i in range(n):
        t = TAU * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * s / 32, (y + 2.5) * s / 32))
    return pts


BOLT = [(0.03, 0.2), (-0.12, -0.03), (-0.015, -0.03), (-0.06, -0.2), (0.12, 0.045), (0.015, 0.045), (0.085, 0.2)]


def sym(name, outline, m, y=-0.25, z=0.4, depth=0.035, bevel=0.008):
    """Flat emblem standing on a -Y face: outline (x, up) extruded toward the viewer."""
    return prism(name, outline, depth, (0, y + 0.005, z), (90, 0, 0), m, bevel=bevel, seg=1)


def teardrop(name, loc, s=1.0, m=None):
    prof = [(0, -0.17), (0.085, -0.145), (0.14, -0.07), (0.155, 0.01), (0.125, 0.1), (0.07, 0.2),
            (0.025, 0.29), (0, 0.33)]
    return lathe(name, [(r * s, z * s) for r, z in prof], loc, m=m, verts=14)


def seedling(name, loc, s=1.0, pot=CLAY, leaf=EM_LIGHT, twist=0):
    parts = [lathe(name + '_pot', [(0, 0), (0.1 * s, 0), (0.135 * s, 0.17 * s), (0.155 * s, 0.17 * s),
                                    (0.155 * s, 0.22 * s), (0, 0.22 * s)], m=pot, verts=14),
             cyl(name + '_soil', 0.13 * s, 0.03, (0, 0, 0.215 * s), m='#6b4a33', verts=14, bevel=0),
             cyl(name + '_stem', 0.018, 0.2 * s, (0, 0, 0.32 * s), m=EM_DEEP, verts=6, bevel=0),
             sphere(name + '_l0', 0.085 * s, (-0.075 * s, 0, 0.44 * s), (1.25, 0.62, 0.34), leaf, 8, (0, 28, 0)),
             sphere(name + '_l1', 0.075 * s, (0.07 * s, 0, 0.46 * s), (1.25, 0.62, 0.34), leaf, 8, (0, -32, 0))]
    xf(parts, loc, (0, 0, twist))
    return parts


# ---------------------------------------------------------------- hero pieces
def build_phone(px, py, rz):
    ph, pw = 3.44, 1.70
    sh = 3.2
    sw = sh * 700 / 1443
    body = [prism('phone_body', rrect(pw, ph, 0.2), 0.13, (0, 0.07, ph / 2), (90, 0, 0), DARK, bevel=0.03, seg=2),
            prism('phone_glass', rrect(pw - 0.06, ph - 0.06, 0.175), 0.03, (0, -0.05, ph / 2), (90, 0, 0),
                  mat('#0e1513', 0.3), bevel=0.008),
            prism('phone_back', rrect(pw - 0.12, ph - 0.12, 0.15), 0.03, (0, 0.05, ph / 2), (-90, 0, 0), EM_DEEP,
                  bevel=0.01),
            prism('phone_cam_bump', rrect(0.62, 0.62, 0.15), 0.05, (0.42, 0.07, ph - 0.52), (-90, 0, 0), FOREST,
                  bevel=0.02),
            sbox('phone_btn_r', (0.04, 0.07, 0.36), (pw / 2 + 0.006, 0, ph - 0.95), m=CHAR_DARK, bevel=0.015),
            sbox('phone_btn_l0', (0.04, 0.07, 0.2), (-pw / 2 - 0.006, 0, ph - 0.75), m=CHAR_DARK, bevel=0.015),
            sbox('phone_btn_l1', (0.04, 0.07, 0.2), (-pw / 2 - 0.006, 0, ph - 1.02), m=CHAR_DARK, bevel=0.015)]
    for i, (lx, lz) in enumerate(((0.29, ph - 0.39), (0.29, ph - 0.65), (0.55, ph - 0.52))):
        body.append(cyl(f'phone_lens_ring_{i}', 0.115, 0.04, (lx, 0.125, lz), (90, 0, 0), STEEL_DARK, verts=16,
                        bevel=0.01, seg=1))
        body.append(cyl(f'phone_lens_{i}', 0.08, 0.03, (lx, 0.14, lz), (90, 0, 0), mat('#0d1513', 0.15, coat=0.6),
                        verts=14, bevel=0.008, seg=1))
    body.append(cyl('phone_flash', 0.04, 0.03, (0.56, 0.125, ph - 0.3), (90, 0, 0),
                    mat('#fff3c4', 0.3, emit=2.5, emit_color='#ffe7a0'), verts=12, bevel=0.006, seg=1))
    scr = screen('phone_screen', (sw, sh), (0, -0.092, ph / 2), (0, 0, 0), SCREEN_IMG)
    xf(body + [scr], (0, 0, 0.13), (-7, 0, 0))            # lean back like a monolith

    base = [box('phone_plinth', (2.5, 1.5, 0.16), (0, -0.28, 0.08), m=STONE, bevel=0.06),
            sbox('phone_socket', (1.95, 0.42, 0.1), (0, 0.02, 0.19), m=EM_DEEP, bevel=0.04)]
    # the classifier's three heads: 30 item classes, 15 materials, 4 bins
    for i, (num, c, ink) in enumerate((('30', EMERALD, OFF), ('15', CITRON, FOREST), ('4', CLAY, OFF))):
        key = [sbox(f'head_key_{i}', (0.5, 0.42, 0.16), (0, 0, 0), m=c, bevel=0.05),
               text(f'head_num_{i}', num, 0.25, 0.03, (0, -0.005, 0.085), (0, 0, 0), ink, bevel=0)]
        key[1].data.resolution_u = 2
        xf(key, ((i - 1) * 0.68, -0.66, 0.2), (26, 0, 0))
        base += key
    everything = body + base + [scr]
    xf(everything, (px, py, 0), (0, 0, rz))
    group('phone', body + base)
    return scr


def build_tree(tx, ty):
    mh, mr = 0.55, 1.55

    def mz(r):
        return mh * max(0.0, 1 - (r / mr) ** 2) ** 1.3

    prof = [(mr + 0.05, -0.03)] + [(mr * k, mz(mr * k)) for k in (1.0, 0.9, 0.78, 0.64, 0.5, 0.34, 0.18)] + [(0, mh)]
    lathe('tree_mound', prof, (tx, ty, 0), m='#7fca6d', verts=40)
    # 11 stepping stones spiral up the mound: the 11 levels of My Tree
    for i in range(11):
        a = R(100 + i * 27.5)
        r = 1.9 - i * 0.088
        last = i == 10
        cyl(f'level_stone_{i + 1}', 0.215 - i * 0.003, 0.18,
            (tx + r * math.cos(a), ty + r * math.sin(a), mz(r) - 0.02 + i * 0.012), (0, 0, i * 31),
            mat(CITRON, 0.5, emit=0.5) if last else OFF, verts=14, bevel=0.035, seg=2)
    trunk_c = '#8a5f3d'
    lathe('tree_trunk', [(0, 0), (0.46, 0), (0.33, 0.22), (0.25, 0.9), (0.21, 1.7), (0.23, 2.2), (0.3, 2.6), (0, 2.6)],
          (tx, ty, mh - 0.12), m=trunk_c, verts=18)
    for i, (dx, dy, dz, tilt, az) in enumerate(((0.42, -0.2, 2.25, 48, -25), (-0.4, 0.2, 2.3, 50, 155),
                                                (-0.2, -0.42, 2.15, 46, -115))):
        cyl(f'tree_branch_{i}', 0.1, 0.9, (tx + dx, ty + dy, mh + dz), (0, tilt, az), trunk_c, r2=0.07, verts=12,
            bevel=0.01, seg=1)
    cz = mh + 2.95
    crown = [(0.0, 0.0, 0.0, 1.2, EMERALD), (0.85, -0.3, -0.42, 0.74, EM_LIGHT), (-0.8, 0.3, 0.05, 0.72, EMERALD),
             (-0.55, -0.62, -0.45, 0.66, EM_DEEP), (0.3, 0.72, -0.4, 0.74, EM_DEEP), (0.18, -0.22, 0.72, 0.66, EM_LIGHT),
             (-0.2, -0.85, 0.12, 0.5, EM_LIGHT), (0.75, 0.45, 0.25, 0.56, EMERALD)]
    for i, (dx, dy, dz, r, c) in enumerate(crown):
        blob(f'tree_crown_{i}', r, (tx + dx, ty + dy, cz + dz), (1, 1, 0.92), c, seed=40 + i, bumps=0.14,
             seg=4 if (r > 0.73 and c != EM_DEEP) else 3)
    # water drops (rewards) hovering near the crown: six, in two bobbing groups
    wet = mat(DROP, 0.12, coat=0.9)
    spots = [(-150, 1.9, 3.2), (-98, 1.72, 4.25), (-80, 1.85, 2.7), (10, 1.75, 4.4), (62, 1.8, 4.2), (140, 1.85, 3.0)]
    groups = ([], [])
    for i, (a, r, z) in enumerate(spots):
        groups[i % 2].append(teardrop(f'drop_{i}', (tx + r * math.cos(R(a)), ty + r * math.sin(R(a)), z),
                                      1.0 if i % 3 else 1.2, wet))
    for k, g in enumerate(groups):
        d = freeze(group(f'water_drops_{"ab"[k]}', g))
        set_origin(d, (tx, ty, 3.6))
        animate(d, 'bob', amp=0.09, speed=1.1 + 0.35 * k)
    return cz + 1.25


BIN_C = (-2.25, -10.4)
BIN_R = 7.9
BIN_STEP = 7.0


def bin_frame(i):
    phi = R(90 - BIN_STEP * i)
    return BIN_C[0] + BIN_R * math.cos(phi), BIN_C[1] + BIN_R * math.sin(phi), -BIN_STEP * i


def bpos(i, dx, dy, z=0.0):
    """World position of an offset in bin i's own frame (dy < 0 is in front of it)."""
    x, y, rz = bin_frame(i)
    c, s = math.cos(R(rz)), math.sin(R(rz))
    return (x + dx * c - dy * s, y + dx * s + dy * c, z)


def build_bins():
    specs = [('recycle', BLUE, BLUE_DARK), ('compost', EMERALD, EM_DEEP), ('landfill', CHAR, CHAR_DARK),
             ('special', CLAY, CLAY_DARK), ('donate', OFF, EM_LIGHT)]
    lid_ob = None
    for i, (kind, body_c, lid_c) in enumerate(specs):
        n = 'bin_' + kind
        parts = [sbox(n + '_foot', (0.5, 0.42, 0.06), (0, 0, 0.03), m=lid_c, bevel=0.02, seg=1),
                 tbox(n + '_body', (0.64, 0.52, 0.7), (0, 0, 0.39), m=body_c, bevel=0.07),
                 sbox(n + '_rim', (0.69, 0.57, 0.06), (0, 0, 0.74), m=lid_c, bevel=0.025, seg=2)]
        lid = [box(n + '_lid', (0.73, 0.61, 0.08), (0, 0, 0.805), m=lid_c, bevel=0.035),
               sbox(n + '_handle', (0.24, 0.08, 0.06), (0, 0, 0.865), m=body_c if kind != 'donate' else CLAY, bevel=0.025, seg=2)]
        if kind == 'recycle':       # three chasing arrows
            for k in range(3):
                parts.append(sym(f'{n}_arrow_{k}', arc_arrow(98 + 120 * k), OFF))
        elif kind == 'compost':     # a sprout
            parts.append(sym(n + '_stem', [(-0.018, -0.17), (0.018, -0.17), (0.018, -0.02), (-0.018, -0.02)], CITRON))
            parts.append(sym(n + '_leaf_r', tr(leaf_outline(0.23, 0.08), 38, 1, 0.09, 0.045), CITRON))
            parts.append(sym(n + '_leaf_l', tr(leaf_outline(0.2, 0.07), 142, 1, -0.078, 0.035), CITRON))
        elif kind == 'landfill':    # a plain lid
            dome = [(0.15 * math.cos(R(a)), 0.11 * math.sin(R(a))) for a in range(0, 181, 20)]
            parts.append(sym(n + '_glyph_dome', tr(dome, dy=-0.02), OFF))
            parts.append(sym(n + '_glyph_bar', tr(rrect(0.4, 0.05, 0.02, 2), dy=-0.065), OFF))
            parts.append(sym(n + '_glyph_knob', tr(rrect(0.09, 0.05, 0.02, 2), dy=0.11), OFF))
        elif kind == 'special':     # a lightning bolt
            parts.append(sym(n + '_bolt', tr(BOLT, s=0.95), CITRON))
        else:                       # a heart, with a donation slot above it
            parts.append(sym(n + '_heart', tr(heart_outline(0.3), dy=-0.03), CLAY))
            parts.append(sbox(n + '_slot', (0.3, 0.03, 0.04), (0, -0.262, 0.64), m=FOREST, bevel=0.01))
        if kind == 'recycle':
            # hinge at the back edge, resting a little open
            hinge = (Matrix.Translation((0, 0.3, 0.77)) @ Euler((R(-9), 0, 0)).to_matrix().to_4x4()
                     @ Matrix.Translation((0, -0.3, -0.77)))
            for o in lid:
                o.matrix_basis = hinge @ o.matrix_basis
        x, y, rz = bin_frame(i)
        xf(parts + lid, (x, y, 0), (0, 0, rz))
        if kind == 'recycle':
            group(n, parts)
            lid_ob = freeze(group(n + '_lid', lid))
            set_origin(lid_ob, (x, y + 0.3, 0.77))
            animate(lid_ob, 'sway', amp=5, speed=1.3, axis='x')
        else:
            group(n, parts + lid)
    return lid_ob


def soda_can(name, loc, c, rot=(0, 0, 0)):
    parts = [cyl(name, 0.075, 0.2, (0, 0, 0), m=c, verts=12, bevel=0.02, seg=2),
             cyl(name + '_top', 0.06, 0.03, (0, 0, 0.095), m=STEEL, verts=12, bevel=0.008, seg=1),
             cyl(name + '_band', 0.078, 0.06, (0, 0, -0.01), m=OFF, verts=12, bevel=0)]
    xf(parts, loc, rot)
    return parts


def pet_bottle(name, loc, cap=EMERALD, label=EM_LIGHT, rot=(0, 0, 0), s=1.0):
    parts = [lathe(name, [(0, 0), (0.075 * s, 0), (0.085 * s, 0.03 * s), (0.085 * s, 0.25 * s), (0.035 * s, 0.36 * s),
                          (0.035 * s, 0.4 * s), (0, 0.4 * s)], m=mat(GLASS, 0.25, coat=0.4), verts=12),
             cyl(name + '_cap', 0.042 * s, 0.045 * s, (0, 0, 0.415 * s), m=cap, verts=12, bevel=0.008, seg=1),
             lathe(name + '_label', [(0.089 * s, 0.1 * s), (0.089 * s, 0.2 * s)], m=label, verts=12)]
    xf(parts, loc, rot)
    return parts


def build_items():
    out = []
    # recycle: cans, PET bottles, a glass jar, a cardboard box of returns
    out += soda_can('can_a', bpos(0, -0.2, -0.62, 0.1), CLAY, (0, 0, 20))
    out += soda_can('can_b', bpos(0, 0.02, -0.82, 0.075), DROP, (90, 0, 55))
    out += soda_can('can_c', bpos(1, -0.42, -0.6, 0.1), CITRON, (0, 0, 70))
    out += pet_bottle('bottle_a', bpos(0, 0.3, -0.56, 0), EMERALD, EM_LIGHT)
    out += pet_bottle('bottle_b', bpos(1, -0.2, -0.95, 0.085), BLUE, OFF, (90, 0, 115))
    jx, jy, _ = bpos(0, 0.52, -0.8)
    out += [lathe('glass_jar', [(0, 0), (0.1, 0), (0.115, 0.03), (0.115, 0.19), (0.085, 0.225), (0.085, 0.25), (0, 0.25)],
                  (jx, jy, 0), m=mat('#bfe9dc', 0.15, coat=0.7), verts=14),
            cyl('glass_jar_lid', 0.095, 0.045, (jx, jy, 0.265), m=CLAY, verts=14, bevel=0.012, seg=2)]
    cx, cy, _ = bpos(0, -0.72, -0.25)
    cbox = [sbox('cardboard_box', (0.46, 0.4, 0.32), (0, 0, 0.16), m=CARD, bevel=0.03),
            sbox('cardboard_flap_l', (0.22, 0.4, 0.035), (-0.3, 0, 0.36), (0, 38, 0), '#c9965f', bevel=0.012),
            sbox('cardboard_flap_r', (0.22, 0.4, 0.035), (0.3, 0, 0.36), (0, -38, 0), '#c9965f', bevel=0.012),
            sbox('cardboard_tape', (0.08, 0.41, 0.2), (0, 0, 0.215), m='#efe0bf', bevel=0.01),
            sbox('cardboard_dark', (0.4, 0.34, 0.03), (0, 0, 0.315), m='#8d6a45', bevel=0.005)]
    cbox += soda_can('can_in_box', (-0.08, 0.04, 0.36), EM_LIGHT, (12, 8, 0))
    cbox += pet_bottle('bottle_in_box', (0.1, -0.04, 0.2), CLAY, OFF, (-8, 10, 0), 0.9)
    xf(cbox, (cx, cy, 0), (0, 0, 14))
    out += cbox
    # compost: an apple
    ax, ay, _ = bpos(1, 0.2, -0.6)
    out += [sphere('apple', 0.085, (ax, ay, 0.078), (1, 1, 0.92), '#d9533f', 12),
            cyl('apple_stem', 0.015, 0.06, (ax, ay, 0.17), (10, 8, 0), WOOD_DARK, verts=6, bevel=0),
            sphere('apple_leaf', 0.04, (ax + 0.04, ay, 0.185), (1.3, 0.6, 0.3), EM_LIGHT, 8)]
    # landfill: a tied rubbish bag
    gx, gy, _ = bpos(2, 0.05, -0.62)
    out += [blob('rubbish_bag', 0.15, (gx, gy, 0.12), (1.05, 1, 0.85), '#7c8a86', seed=5, bumps=0.2, seg=3),
            cyl('rubbish_knot', 0.035, 0.08, (gx, gy, 0.27), m='#7c8a86', r2=0.05, verts=12, bevel=0.01)]
    # special: two batteries
    for k, (dx, dy, rot) in enumerate(((-0.12, -0.6, (0, 0, 0)), (0.14, -0.72, (90, 0, 35)))):
        p = bpos(3, dx, dy, 0.09 if k == 0 else 0.05)
        batt = [cyl(f'battery_{k}', 0.05, 0.18, (0, 0, 0), m=FOREST, verts=12, bevel=0.012, seg=2),
                cyl(f'battery_{k}_top', 0.051, 0.055, (0, 0, 0.065), m=CITRON, verts=12, bevel=0.012, seg=2),
                cyl(f'battery_{k}_nub', 0.02, 0.03, (0, 0, 0.1), m=STEEL, verts=12, bevel=0.005, seg=1)]
        xf(batt, p, rot)
        out += batt
    # donate: a pair of shoes and a folded shirt
    for k, (dx, dy, rz) in enumerate(((-0.28, -0.62, 20), (-0.06, -0.72, 32))):
        p = bpos(4, dx, dy)
        shoe = [sbox(f'shoe_{k}_sole', (0.15, 0.4, 0.05), (0, 0, 0.025), m=OFF, bevel=0.022),
                sphere(f'shoe_{k}_toe', 0.085, (0, -0.09, 0.075), (0.8, 1.35, 0.62), CLAY, 12),
                sbox(f'shoe_{k}_heel', (0.14, 0.2, 0.15), (0, 0.09, 0.115), m=CLAY, bevel=0.055),
                cyl(f'shoe_{k}_hole', 0.045, 0.03, (0, 0.1, 0.185), m=FOREST, verts=12, bevel=0.008, seg=1),
                sbox(f'shoe_{k}_lace', (0.1, 0.03, 0.03), (0, -0.03, 0.125), (25, 0, 0), OFF, bevel=0.01)]
        xf(shoe, p, (0, 0, rz - 28))
        out += shoe
    sx, sy, _ = bpos(4, 0.42, -0.5)
    shirt = [sbox('shirt_fold_0', (0.44, 0.36, 0.07), (0, 0, 0.035), m=EM_LIGHT, bevel=0.03),
             sbox('shirt_fold_1', (0.42, 0.34, 0.06), (0, 0, 0.095), m=EM_LIGHT, bevel=0.028),
             prism('shirt_collar_l', [(-0.1, 0), (0, 0), (-0.02, -0.1)], 0.035, (0, 0.16, 0.115), m=OFF, bevel=0.008),
             prism('shirt_collar_r', [(0, 0), (0.1, 0), (0.02, -0.1)], 0.035, (0, 0.16, 0.115), m=OFF, bevel=0.008),
             sphere('shirt_button', 0.018, (0, 0.0, 0.13), (1, 1, 0.5), OFF, 8)]
    xf(shirt, (sx, sy, 0), (0, 0, -40))
    out += shirt
    group('sorting_items', out)


def build_graph(gx, gy):
    lathe('graph_base', [(0, 0), (0.6, 0), (0.62, 0.05), (0.52, 0.12), (0.14, 0.18), (0.1, 0.26), (0, 0.26)],
          (gx, gy, 0), m=STONE, verts=28)
    wire = FOREST
    z_item, z_mat, z_bin = 2.42, 1.62, 0.88
    parts = [cyl('graph_pole', 0.04, 2.6, (0, 0, 0.2 + 1.3), m=wire, verts=12, bevel=0.01, seg=1),
             sphere('graph_finial', 0.075, (0, 0, 2.85), m=CITRON, seg=12),
             torus('graph_ring', 0.86, 0.017, (0, 0, z_item), m=wire, seg=36, ring=6)]
    items, mats, bins = [], [], []
    for i in range(12):
        a = TAU * i / 12
        items.append(Vector((0.86 * math.cos(a), 0.86 * math.sin(a), z_item)))
        parts.append(sphere(f'graph_item_{i}', 0.085, items[-1], m=EMERALD if i % 2 else EM_LIGHT, seg=8))
    for j in range(5):
        a = TAU * j / 5 + R(18)
        mats.append(Vector((0.5 * math.cos(a), 0.5 * math.sin(a), z_mat)))
        parts.append(sphere(f'graph_material_{j}', 0.115, mats[-1], m=CITRON, seg=14))
    glow = mat(CLAY, 0.5, emit=1.0)
    for j in range(5):
        a = TAU * j / 5 + R(54)
        bins.append(Vector((0.66 * math.cos(a), 0.66 * math.sin(a), z_bin)))
        parts.append(sphere(f'graph_bin_{j}', 0.15, bins[-1], m=glow, seg=14))
    edges = []
    for i in range(12):
        near = sorted(range(5), key=lambda j: (items[i] - mats[j]).length)
        edges.append((items[i], mats[near[0]]))
        if i % 3 == 0:
            edges.append((items[i], mats[near[1]]))
    for j in range(5):
        edges.append((mats[j], bins[j]))
        edges.append((mats[j], bins[(j - 1) % 5]))
    for k in range(4):                       # hangers from the pole to the top ring
        a = TAU * k / 4 + R(15)
        edges.append((Vector((0, 0, 2.78)), Vector((0.86 * math.cos(a), 0.86 * math.sin(a), z_item))))
    for k, (p, q) in enumerate(edges):
        parts.append(tube(f'graph_edge_{k}', [tuple(p), tuple(q)], 0.016, wire, smooth_curve=False))
    xf(parts, (gx, gy, 0))
    g = freeze(group('knowledge_graph', parts))
    set_origin(g, (gx, gy, 0.2))
    animate(g, 'spin', axis='z', speed=0.22)
    return 2.95


def build_workbench(wx, wy, rz):
    top_c = '#dcae78'
    p = [box('bench_top', (1.7, 0.82, 0.09), (0, 0, 0.665), m=top_c, bevel=0.035),
         sbox('bench_shelf', (1.5, 0.62, 0.06), (0, 0, 0.2), m=WOOD, bevel=0.02),
         box('bench_board', (1.7, 0.07, 0.72), (0, 0.375, 1.1), m=STONE, bevel=0.03)]
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        tall = sy > 0
        p.append(sbox(f'bench_leg_{i}', (0.1, 0.1, 1.5 if tall else 0.64), (sx * 0.76, sy * 0.33, 0.75 if tall else 0.32),
                     m=WOOD_DARK, bevel=0.025))
    # tools on the board: twine, hammer, set square
    p += [torus('bench_twine', 0.1, 0.045, (-0.52, 0.31, 1.2), (90, 0, 0), EMERALD, seg=18, ring=8),
          cyl('bench_peg_0', 0.022, 0.12, (-0.52, 0.3, 1.31), (90, 0, 0), WOOD_DARK, verts=8, bevel=0),
          sbox('bench_hammer_handle', (0.05, 0.045, 0.36), (-0.05, 0.315, 1.03), (0, 12, 0), WOOD, bevel=0.015),
          sbox('bench_hammer_head', (0.22, 0.075, 0.1), (-0.09, 0.31, 1.23), (0, 12, 0), STEEL_DARK, bevel=0.025),
          prism('bench_square', [(0, 0), (0.34, 0), (0, 0.34)], 0.035, (0.3, 0.345, 0.9), (90, 0, 0), CITRON, bevel=0.01),
          sbox('bench_mat', (0.8, 0.58, 0.03), (-0.38, -0.06, 0.722), m=EM_DEEP, bevel=0.012),
          sbox('bench_tray', (0.84, 0.26, 0.05), (0.4, 0.12, 0.732), m=OFF, bevel=0.02)]
    for i, c in enumerate((CLAY, CITRON, DROP)):
        p.append(sphere(f'material_orb_{i}', 0.115, (0.14 + i * 0.26, 0.12, 0.855), m=mat(c, 0.25, coat=0.6), seg=16))
    # half-finished upcycle: a planter cut from a bottle, with its cut-off top and scissors
    pz = 0.737
    p += [lathe('planter_bottle', [(0, 0), (0.12, 0), (0.135, 0.03), (0.135, 0.21), (0.112, 0.21), (0.112, 0.05), (0, 0.05)],
                (-0.55, -0.02, pz), m=mat(GLASS, 0.25, coat=0.4), verts=16),
          cyl('planter_soil', 0.113, 0.1, (-0.55, -0.02, pz + 0.13), m='#6b4a33', verts=16, bevel=0),
          lathe('planter_band', [(0.139, 0.07), (0.139, 0.13)], (-0.55, -0.02, pz), m=CLAY, verts=16),
          cyl('planter_stem', 0.018, 0.2, (-0.55, -0.02, pz + 0.27), m=EM_DEEP, verts=6, bevel=0),
          sphere('planter_leaf_0', 0.085, (-0.625, -0.02, pz + 0.37), (1.25, 0.62, 0.34), EM_LIGHT, 10, (0, 28, 0)),
          sphere('planter_leaf_1', 0.075, (-0.48, -0.02, pz + 0.39), (1.25, 0.62, 0.34), EM_LIGHT, 10, (0, -32, 0)),
          lathe('bottle_top_cut', [(0.13, 0), (0.135, 0.06), (0.045, 0.2), (0.045, 0.25)], (-0.22, -0.22, pz + 0.132),
                (0, 90, 25), mat(GLASS, 0.25, coat=0.4), verts=14),
          sbox('scissor_blade_0', (0.035, 0.26, 0.03), (-0.14, 0.1, pz + 0.015), (0, 0, 14), STEEL, bevel=0.01),
          sbox('scissor_blade_1', (0.035, 0.26, 0.03), (-0.14, 0.1, pz + 0.02), (0, 0, -14), STEEL, bevel=0.01),
          torus('scissor_ring_0', 0.045, 0.017, (-0.185, -0.05, pz + 0.017), m=CLAY, seg=12, ring=6),
          torus('scissor_ring_1', 0.045, 0.017, (-0.095, -0.05, pz + 0.017), m=CLAY, seg=12, ring=6)]
    cap_p = Vector((-0.22, -0.22, pz + 0.132)) + Euler((0, 0, R(25))).to_matrix() @ Vector((0.27, 0, 0))
    p.append(cyl('bottle_top_cap', 0.055, 0.05, tuple(cap_p), (0, 90, 25), EMERALD, verts=12, bevel=0.01, seg=1))
    # shelf stock: a crate of sorted material, flattened card, a jar
    p += [sbox('shelf_crate', (0.46, 0.4, 0.28), (-0.42, 0, 0.37), (0, 0, 6), CARD, bevel=0.03),
          cyl('shelf_can_0', 0.075, 0.2, (-0.52, -0.04, 0.56), (8, 6, 0), CLAY, verts=12, bevel=0.02, seg=1),
          cyl('shelf_can_1', 0.075, 0.2, (-0.33, 0.05, 0.55), (-6, 10, 0), DROP, verts=12, bevel=0.02, seg=1),
          sbox('shelf_crate_dark', (0.4, 0.34, 0.03), (-0.42, 0, 0.5), (0, 0, 6), '#8d6a45', bevel=0.005, seg=1)]
    for i in range(3):
        p.append(sbox(f'shelf_card_{i}', (0.5, 0.4, 0.045), (0.36, 0, 0.255 + i * 0.047), (0, 0, (i - 1) * 5),
                     CARD if i % 2 else '#c9965f', bevel=0.012))
    p.append(lathe('shelf_jar', [(0, 0), (0.08, 0), (0.09, 0.03), (0.09, 0.15), (0.065, 0.18), (0, 0.18)],
                   (0.36, -0.02, 0.395), m=mat('#bfe9dc', 0.15, coat=0.7), verts=12))
    # the orb being dragged into the workspace
    orb = sphere('dragged_orb', 0.13, (-0.2, -0.1, 1.2), m=mat(EM_LIGHT, 0.25, emit=1.6, coat=0.6), seg=18)
    xf(p + [orb], (wx, wy, 0), (0, 0, rz))
    group('workbench', p)
    centre = orb.matrix_basis.translation.copy()
    freeze(orb)
    set_origin(orb, centre)
    animate(orb, 'bob', amp=0.07, speed=1.5)


def build_bicycle(bx, by, rz):
    fr = CLAY
    tyre = '#2b3834'
    p = []

    def bar(name, a, b, r=0.03, m=fr):
        p.append(tube(name, [(a[0], 0, a[1]), (b[0], 0, b[1])], r, m, smooth_curve=False))

    rear, front = (-0.56, 0.38), (0.56, 0.38)
    bb, seat, head, head_b = (-0.08, 0.36), (-0.24, 0.88), (0.36, 0.86), (0.4, 0.72)
    bar('bike_chainstay', rear, bb)
    bar('bike_seat_tube', bb, (-0.27, 0.98))
    bar('bike_top_tube', seat, head)
    bar('bike_down_tube', bb, head_b)
    bar('bike_seat_stay', rear, seat)
    bar('bike_fork', (0.33, 1.0), front)
    for n, (cx, cz) in (('rear', rear), ('front', front)):
        p.append(torus(f'bike_tyre_{n}', 0.335, 0.045, (cx, 0, cz), (90, 0, 0), tyre, seg=24, ring=6))
        p.append(torus(f'bike_rim_{n}', 0.285, 0.02, (cx, 0, cz), (90, 0, 0), OFF, seg=24, ring=4))
        p.append(cyl(f'bike_hub_{n}', 0.05, 0.1, (cx, 0, cz), (90, 0, 0), STEEL, verts=12, bevel=0.01, seg=1))
        for k in range(3):
            p.append(cyl(f'bike_spoke_{n}_{k}', 0.015, 0.58, (cx, 0, cz), (0, 60 * k + 15, 0), STEEL, verts=6, bevel=0))
    p += [tube('bike_handlebar', [(0.33, -0.24, 1.0), (0.33, 0.24, 1.0)], 0.028, tyre, smooth_curve=False),
          sbox('bike_saddle', (0.28, 0.13, 0.06), (-0.29, 0, 1.0), m=FOREST, bevel=0.028),
          cyl('bike_chainring', 0.085, 0.04, (bb[0], -0.05, bb[1]), (90, 0, 0), STEEL_DARK, verts=14, bevel=0.01, seg=1),
          sbox('bike_crank', (0.04, 0.03, 0.3), (bb[0], -0.08, bb[1]), (0, 25, 0), STEEL_DARK, bevel=0.012),
          sbox('bike_pedal_0', (0.12, 0.09, 0.035), (bb[0] + 0.065, -0.13, bb[1] + 0.135), m=tyre, bevel=0.012),
          sbox('bike_pedal_1', (0.12, 0.09, 0.035), (bb[0] - 0.065, 0.1, bb[1] - 0.135), m=tyre, bevel=0.012),
          # front basket with a seedling riding along
          sbox('bike_basket', (0.26, 0.3, 0.2), (0.6, 0, 0.92), m=WOOD, bevel=0.03),
          sbox('bike_basket_in', (0.2, 0.24, 0.03), (0.6, 0, 1.012), m='#6b4a33', bevel=0.005),
          cyl('bike_basket_stem', 0.018, 0.14, (0.6, 0, 1.08), m=EM_DEEP, verts=6, bevel=0),
          sphere('bike_basket_leaf_0', 0.07, (0.545, 0, 1.15), (1.2, 0.6, 0.4), EM_LIGHT, 10, (0, 30, 0)),
          sphere('bike_basket_leaf_1', 0.07, (0.655, 0, 1.16), (1.2, 0.6, 0.4), EMERALD, 10, (0, -30, 0))]
    xf(p, (0, 0, 0), (-12, 0, 0))            # lean onto the post
    py_ = 0.86 * math.sin(R(12)) + 0.03 + 0.075
    p += [cyl('meter_post', 0.07, 1.42, (0.05, py_, 0.71), m=WOOD_DARK, verts=12, bevel=0.02),
          # a round carbon meter: green to clay scale and a needle (kg CO2e)
          cyl('meter_dial', 0.24, 0.1, (0.05, py_, 1.52), (90, 0, 0), FOREST, verts=24, bevel=0.03),
          cyl('meter_face', 0.19, 0.03, (0.05, py_ - 0.045, 1.52), (90, 0, 0), OFF, verts=24, bevel=0.008, seg=1),
          sbox('meter_needle', (0.035, 0.03, 0.16), (0.02, py_ - 0.07, 1.555), (0, -28, 0), CLAY, bevel=0.01),
          cyl('meter_pin', 0.03, 0.04, (0.05, py_ - 0.07, 1.5), (90, 0, 0), FOREST, verts=12, bevel=0.008, seg=1)]
    for k, c in enumerate((EMERALD, EM_LIGHT, CITRON, SUNSHINE, CLAY)):
        a = R(160 - 35 * k)
        p.append(cyl(f'meter_tick_{k}', 0.024, 0.03, (0.05 + 0.145 * math.cos(a), py_ - 0.062, 1.5 + 0.145 * math.sin(a)),
                     (90, 0, 0), c, verts=12, bevel=0.006, seg=1))
    xf(p, (bx, by, 0), (0, 0, rz))
    group('bicycle', p)


def build_transit(x, y, rz):
    """Toy bus and car: the other two passive carbon-tracking modes."""
    tyre = '#2b3834'
    bus = [box('bus_body', (0.74, 0.3, 0.3), (0, 0, 0.23), m=OFF, bevel=0.07),
           sbox('bus_stripe', (0.75, 0.31, 0.07), (0, 0, 0.14), m=EMERALD, bevel=0.02),
           sbox('bus_windows', (0.62, 0.315, 0.1), (-0.03, 0, 0.29), m='#7fc4d6', bevel=0.02),
           sbox('bus_windscreen', (0.04, 0.24, 0.12), (0.36, 0, 0.28), m='#7fc4d6', bevel=0.015),
           sbox('bus_roof', (0.5, 0.2, 0.04), (0, 0, 0.39), m=EM_LIGHT, bevel=0.015)]
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        bus.append(cyl(f'bus_wheel_{i}', 0.075, 0.06, (sx * 0.22, sy * 0.14, 0.075), (90, 0, 0), tyre, verts=12, bevel=0.015, seg=2))
    xf(bus, (x, y, 0), (0, 0, rz))
    car = [sbox('car_body', (0.5, 0.25, 0.14), (0, 0, 0.14), m=CLAY, bevel=0.05),
           sbox('car_cabin', (0.26, 0.22, 0.12), (-0.03, 0, 0.25), m='#7fc4d6', bevel=0.045),
           sbox('car_roof', (0.2, 0.18, 0.035), (-0.03, 0, 0.315), m=CLAY, bevel=0.012)]
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        car.append(cyl(f'car_wheel_{i}', 0.065, 0.06, (sx * 0.15, sy * 0.115, 0.065), (90, 0, 0), tyre, verts=12, bevel=0.015, seg=2))
    a = R(rz)
    xf(car, (x + 0.85 * math.cos(a) - 0.12 * math.sin(a), y + 0.85 * math.sin(a) + 0.12 * math.cos(a), 0), (0, 0, rz + 12))
    group('bus_and_car', bus + car)


FOOT = [(0.0, -0.2), (0.06, -0.17), (0.075, -0.08), (0.068, 0.02), (0.095, 0.1), (0.088, 0.17), (0.035, 0.205),
        (-0.04, 0.185), (-0.078, 0.1), (-0.064, 0.0), (-0.07, -0.09), (-0.055, -0.17)]
TOES = [(-0.058, 0.262, 0.038), (0.0, 0.287, 0.031), (0.048, 0.278, 0.028), (0.088, 0.25, 0.025)]


def build_footprints(points):
    """Footprint-shaped stepping stones (walking), alternating left and right."""
    out = []
    for i, (x, y, heading) in enumerate(points):
        left = i % 2 == 0
        s = 1.2
        side = (-1 if left else 1) * 0.13
        h = R(heading)
        fx, fy = x + side * math.sin(h), y - side * math.cos(h)
        parts = [prism(f'footprint_{i}', tr(FOOT, s=s, mirror=left), 0.06, (0, 0, -0.015), m=OFF, bevel=0.02, seg=1)]
        for k, (tx, ty, r) in enumerate(TOES):
            parts.append(cyl(f'footprint_{i}_toe_{k}', r * s, 0.06, ((-tx if left else tx) * s, ty * s, 0.015), m=OFF,
                             verts=12, bevel=0.012, seg=1))
        xf(parts, (fx, fy, 0), (0, 0, heading - 90))
        out += parts
    group('footprint_path', out)


def build_watering_can(x, y, rz):
    c = EM_LIGHT
    p = [cyl('can_body', 0.17, 0.3, (0, 0, 0.15), m=c, verts=18, bevel=0.03),
         torus('can_rim', 0.165, 0.022, (0, 0, 0.3), m=EM_DEEP, seg=18, ring=6),
         cyl('can_water', 0.15, 0.02, (0, 0, 0.292), m=mat(DROP, 0.15, coat=0.8), verts=18, bevel=0),
         tube('can_spout', [(0.12, 0, 0.09), (0.3, 0, 0.24), (0.43, 0, 0.4)], 0.035, c, res=3),
         cyl('can_rose', 0.035, 0.08, (0.46, 0, 0.435), (0, 40, 0), EM_DEEP, r2=0.075, verts=12, bevel=0.01, seg=1),
         torus('can_handle', 0.12, 0.025, (-0.2, 0, 0.19), (90, 0, 0), EM_DEEP, seg=16, ring=6)]
    xf(p, (x, y, 0), (0, 0, rz))
    return p


def build_pinwheel(x, y):
    cyl('pinwheel_post', 0.04, 1.7, (x, y, 0.85), m=OFF, verts=12, bevel=0.01, seg=1)
    hz = 1.62
    blade = [(0.0, 0.0), (0.46, 0.04), (0.38, 0.21), (0.18, 0.26)]
    parts = [prism(f'pinwheel_blade_{k}', tr(blade, 90 * k), 0.04, (0, -0.04, hz), (90, 0, 0), c, bevel=0.01, seg=2)
             for k, c in enumerate((CLAY, CITRON, EM_LIGHT, DROP))]
    parts.append(cyl('pinwheel_hub', 0.065, 0.06, (0, -0.095, hz), (90, 0, 0), OFF, verts=12, bevel=0.015, seg=2))
    xf(parts, (x, y, 0))
    pw = freeze(group('pinwheel', parts))
    set_origin(pw, (x, y - 0.06, hz))
    animate(pw, 'spin', axis='y', speed=2.4)


# ---------------------------------------------------------------- island
def build_rain_barrel(x, y):
    p = [lathe('rain_barrel', [(0, 0), (0.25, 0), (0.31, 0.2), (0.31, 0.4), (0.26, 0.6), (0.22, 0.6), (0.22, 0.54), (0, 0.54)],
               (x, y, 0), m=WOOD, verts=18),
         torus('rain_barrel_hoop_0', 0.305, 0.022, (x, y, 0.17), m=CHAR_DARK, seg=18, ring=6),
         torus('rain_barrel_hoop_1', 0.3, 0.022, (x, y, 0.45), m=CHAR_DARK, seg=18, ring=6),
         cyl('rain_barrel_water', 0.225, 0.03, (x, y, 0.55), m=mat(DROP, 0.12, coat=0.9), verts=18, bevel=0)]
    return group('rain_barrel', p)


def build(mode='preview'):
    reset()
    setup_world()
    sq = (1.07, 0.98)
    _, radius_at = island_base(R=5.1, seed=202, top='#97dc78', lip=CITRON, soil='#d8b184', soil2='#b58a5f',
                                  rock_c='#97a29f', lobes=((2, 0.06), (3, 0.045), (4, 0.03)), squash=sq)

    def check(tag, x, y, margin=0.1):
        a = math.atan2(y / sq[1], x / sq[0])
        d = math.hypot(x / sq[0], y / sq[1])
        lim = radius_at(a) * 0.92 - margin
        if d > lim:
            print(f'[releaf] OUTSIDE {tag}: {d:.2f} > {lim:.2f}')

    def rim(deg, k=0.93):
        a = R(deg)
        return radius_at(a) * k * sq[0] * math.cos(a), radius_at(a) * k * sq[1] * math.sin(a)

    # paved apron under the sorting line
    mx, my, _ = bpos(2, 0, -0.25)
    apron = lathe('sorting_apron', [(0, 0.014), (0.94, 0.014), (1.0, -0.02)], (mx, my, 0), (0, 0, -14), '#eef0dc', verts=48)
    apron.scale = (2.75, 1.05, 1)

    tx, ty = -2.45, 1.65
    px, py, prz = 0.75, 2.0, -14
    gx, gy = 3.15, 0.95
    wx, wy, wrz = 3.2, -1.55, -24

    tree_top = build_tree(tx, ty)
    build_phone(px, py, prz)
    build_bins()
    build_items()
    graph_top = build_graph(gx, gy)
    build_workbench(wx, wy, wrz)
    # the carbon tracker's four modes: walk (footprints), bicycle, bus, car
    build_bicycle(-3.75, -0.75, -28)
    build_footprints([(-2.75, -1.55, 38), (-2.3, -1.2, 40), (-1.85, -0.8, 44), (-1.42, -0.36, 47),
                      (-1.02, 0.1, 50), (-0.66, 0.58, 54)])
    build_transit(-0.35, -0.62, 24)
    build_pinwheel(1.95, 1.5)
    for tag, x, y in (('bin0', *bpos(0, -0.95, -0.4)[:2]), ('bin0f', *bpos(0, 0, -0.95)[:2]),
                      ('bin4', *bpos(4, 0.65, -0.6)[:2]), ('bin4f', *bpos(4, 0, -0.95)[:2]), ('bike', -4.5, -0.45),
                      ('bench', 4.05, -1.95), ('bench2', 3.7, -2.3), ('graph', 3.8, 0.95), ('mound', tx - 1.85, ty)):
        check(tag, x, y)

    # scan pad: an item under the classifier's eye
    sx, sy = -0.55, 1.05
    cyl('scan_pad', 0.36, 0.1, (sx, sy, 0.05), m=STONE, verts=24, bevel=0.03, seg=2)
    torus('scan_ring', 0.27, 0.03, (sx, sy, 0.105), m=mat(EM_LIGHT, 0.4, emit=1.5), seg=24, ring=6)
    group('scan_item', soda_can('scan_can', (sx, sy, 0.2), CLAY, (0, 0, 30)))

    # ground detail: seedling nursery, watering can, rain barrel, vegetation
    pots = [(1.6, -0.5, 1.0, CLAY, 0), (2.0, -0.28, 0.85, OFF, 40), (2.2, -0.75, 1.1, CLAY, 80), (1.85, -1.05, 0.8, OFF, 15),
            (-1.15, 2.95, 0.9, CLAY, 20), (4.2, -0.3, 0.9, OFF, 60), (-3.8, -2.0, 0.95, CLAY, 10),
            (0.2, 3.75, 0.8, OFF, 50)]
    for i, (x, y, s, c, tw) in enumerate(pots):
        check(f'pot{i}', x, y)
    group('seedling_pots', [seedling(f'seedling_{i}', (x, y, 0), s, c, EM_LIGHT if i % 2 else EMERALD, tw)
                            for i, (x, y, s, c, tw) in enumerate(pots)])
    group('watering_can', build_watering_can(-1.72, 0.02, 112))
    build_rain_barrel(-0.45, 3.3)

    tray = [sbox('seed_tray', (0.72, 0.46, 0.2), (0, 0, 0.1), m=WOOD, bevel=0.03),
            sbox('seed_tray_soil', (0.64, 0.38, 0.04), (0, 0, 0.195), m='#6b4a33', bevel=0.008, seg=1)]
    for k in range(6):
        cx_, cy_ = (k % 3 - 1) * 0.2, (k // 3 - 0.5) * 0.18
        tray += [cyl(f'seed_tray_stem_{k}', 0.016, 0.1 + 0.02 * (k % 2), (cx_, cy_, 0.26), m=EM_DEEP, verts=6, bevel=0),
                 sphere(f'seed_tray_leaf_{k}', 0.05, (cx_, cy_, 0.32 + 0.02 * (k % 2)), (1.3, 0.7, 0.4),
                        EM_LIGHT if k % 2 else EMERALD, 8, (0, 0, 40 * k))]
    xf(tray, (3.2, -3.05, 0), (0, 0, -30))
    check('tray', 3.5, -3.3)
    group('seed_tray', tray)

    bed = [sbox('raised_bed', (1.0, 0.56, 0.24), (0, 0, 0.12), m=WOOD_DARK, bevel=0.035),
           sbox('raised_bed_soil', (0.9, 0.46, 0.04), (0, 0, 0.235), m='#6b4a33', bevel=0.008, seg=1)]
    for k in range(4):
        cx_ = (k - 1.5) * 0.22
        hh = 0.14 + 0.05 * (k % 2)
        bed += [cyl(f'raised_bed_stem_{k}', 0.018, hh, (cx_, 0, 0.25 + hh / 2), m=EM_DEEP, verts=6, bevel=0),
                sphere(f'raised_bed_leaf_{k}a', 0.07, (cx_ - 0.055, 0, 0.27 + hh), (1.25, 0.62, 0.34), EM_LIGHT, 8, (0, 28, 0)),
                sphere(f'raised_bed_leaf_{k}b', 0.065, (cx_ + 0.055, 0, 0.28 + hh), (1.25, 0.62, 0.34), EMERALD, 8, (0, -32, 0))]
    xf(bed, (3.2, 2.45, 0), (0, 0, 50))
    check('bed', 3.55, 2.85)
    group('raised_bed', bed)

    tree('tree_small_a', (1.9, 3.85, 0), 1.5, 0.62, trunk='#8a5f3d', leaf=EM_LIGHT, leaf2=EMERALD, seed=3)
    tree('tree_small_b', (-1.25, 4.0, 0), 1.25, 0.5, trunk='#8a5f3d', leaf=EMERALD, leaf2=EM_DEEP, seed=8)
    check('tree_a', 1.9, 3.85)
    check('tree_b', -1.25, 4.0)
    bushes = [(-2.3, 3.75, 0.34), (0.95, 4.2, 0.3), (4.0, 1.5, 0.28), (-4.4, 0.75, 0.3), (4.3, 0.45, 0.28),
              (-3.1, 3.0, 0.32), (0.5, -1.75, 0.24), (-4.3, -1.6, 0.26), (-3.5, -2.8, 0.24), (3.95, -2.55, 0.3)]
    for i, (x, y, r) in enumerate(bushes):
        check(f'bush{i}', x, y)
        bush(f'bush_{i}', (x, y, 0), r, (EM_LIGHT, LEAF, '#74c07a')[i % 3], seed=i)
    tufts, flowers = [], []
    for i, (x, y) in enumerate([(-0.05, 0.5), (1.2, 0.5), (-0.25, -2.0), (2.6, 2.0), (-1.9, 3.75), (-4.3, 0.2),
                                (4.2, 1.5), (1.0, -0.4), (-3.8, -2.0), (3.6, -3.0), (0.6, 3.5), (-2.0, -0.4),
                                (-2.9, -0.2), (4.3, 1.0), (2.5, -0.1), (-0.6, -4.0), (2.0, -3.9), (-2.6, -3.5)]):
        tufts += grass_tuft(f'tuft_{i}', (x, y, 0), seed=i, m='#63b866')
    group('grass_tufts', tufts)
    for i, (x, y) in enumerate([(0.6, 0.6), (-1.2, -1.4), (1.75, 0.25), (-1.75, -1.75), (2.4, 3.0), (-3.6, 2.6),
                                (4.3, -0.85), (0.9, -2.1), (-0.5, 4.2), (2.7, -3.3), (-4.1, -0.1), (3.75, 2.05),
                                (-1.7, -3.8), (0.7, -4.15), (-3.9, -2.75)]):
        flowers += flower(f'flower_{i}', (x, y, 0), 0.24 + 0.03 * (i % 3), (OFF, CLAY, CITRON)[i % 3], SUNSHINE, EM_DEEP)
    group('flowers', flowers)
    for i, (deg, r) in enumerate([(212, 0.36), (338, 0.4), (22, 0.3), (112, 0.3), (60, 0.26), (158, 0.34), (300, 0.28)]):
        x, y = rim(deg, 0.955)
        rock(f'shore_rock_{i}', r, (x, y, -0.07), ROCK if i % 2 else '#b3b9ba', seed=i + 21)

    bx, by, _ = bin_frame(2)
    hotspot(1, (px, py + 0.4, 3.85))
    hotspot(2, (bx, by, 1.25))
    hotspot(3, (gx, gy, graph_top + 0.25))
    hotspot(4, (tx, ty, min(tree_top + 0.15, 4.95)))
    finish('releaf', mode, cam_loc=(-9.5, -13.5, 8.2), cam_target=(0.0, -0.25, 1.0), lens=50)
