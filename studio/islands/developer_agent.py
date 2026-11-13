"""A better test for an agent: a careful workshop yard where a coding agent is tested.

Front, left to right: task conveyor -> sealed test chamber (network unplugged) -> patch
chute -> verdict cabinet with its signal tower. Behind: the quarantine pen, the lane
through four admission gates, the admitted stock of 51 crates on three pallets, the
nine-tool pegboard, two agreeing balance scales, a server rack and the hourglass.
"""
import math
from kit import *

SAND_C = '#d9d0b6'
PAPER_C = '#efe9db'
PAD = '#e9e2d1'
OLIVE = '#575540'
OLIVE_LT = '#77745a'
GRAPH = '#2a2f2b'
GRAPH_LT = '#3d4540'
GREEN = '#47c98b'
RED = '#e2574c'
AMBER = '#f2b03b'
BLUE = '#8aa1ad'
BLUE_LT = '#b4c5cc'
CRATES = ('#d7a66f', '#c98f5a', '#e2b47e')
CRATE_DK = '#a8743f'
DRY = '#cfc594'
DRY_DK = '#a9a166'


_kit_box = box


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=WHITE, bevel=0.06, seg=2):
    """Kit box with two bevel segments by default: this island has many small boxes."""
    return _kit_box(name, size, loc, rot, m, bevel, seg)


def pebble(name, r, loc, m, rz=0):
    return sphere(name, r, loc, (1.25, 1.0, 0.55), m, 8, (0, 0, rz))


def cone(name, x, y):
    box(name + '_base', (0.27, 0.27, 0.05), (x, y, 0.025), (0, 0, 12), GRAPH, bevel=0.015, seg=1)
    lathe(name, [(0, 0.05), (0.105, 0.05), (0.03, 0.38), (0, 0.39)], (x, y, 0), m=AMBER, verts=12)
    lathe(name + '_band', [(0.086, 0.15), (0.062, 0.25)], (x, y, 0.0), m=PAPER_C, verts=12).scale = (1.05, 1.05, 1)


def rot2(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def crate(name, s, x, y, z, rz=0, tone=0, tag=None, seg=2, band=False):
    """Toy crate standing on z. Total height is exactly s. Returns its parts."""
    parts = [box(name, (s, s, s * 0.86), (x, y, z + s * 0.43), (0, 0, rz), CRATES[tone % 3],
                 bevel=s * 0.08, seg=seg),
             box(name + '_lid', (s * 1.07, s * 1.07, s * 0.15), (x, y, z + s * 0.925), (0, 0, rz),
                 CRATE_DK, bevel=s * 0.04, seg=1)]
    if band:
        parts.append(box(name + '_foot', (s * 1.07, s * 1.07, s * 0.13), (x, y, z + s * 0.065),
                         (0, 0, rz), CRATE_DK, bevel=s * 0.04, seg=1))
    if tag:
        dx, dy = rot2(0, -s * 0.5 - 0.004, rz)
        parts.append(box(name + '_tag', (s * 0.42, 0.024, s * 0.26), (x + dx, y + dy, z + s * 0.47),
                         (0, 0, rz), tag, bevel=0.006, seg=1))
    return parts


def drum(name, x, y, color, rz=0):
    lathe(name, [(0, 0), (0.2, 0), (0.225, 0.03), (0.225, 0.6), (0.2, 0.63), (0, 0.63)], (x, y, 0),
          m=color, verts=14)
    for k, z in enumerate((0.21, 0.42)):
        torus(f'{name}_rib{k}', 0.226, 0.016, (x, y, z), m=color, seg=14, ring=5)
    cyl(name + '_top', 0.19, 0.03, (x, y, 0.625), m=GRAPH_LT, verts=14, bevel=0.008, seg=1)
    bx, by = rot2(0.1, 0, rz)
    cyl(name + '_bung', 0.035, 0.04, (x + bx, y + by, 0.655), m=PAPER_C, verts=8, bevel=0.008, seg=1)


def clipboard(name, loc, rot, sheet=WHITE):
    """Small clipboard; built flat (board in XY, clip toward +Y) then rotated."""
    b = box(name, (0.27, 0.36, 0.035), (0, 0, 0), m=WOOD_DARK, bevel=0.012, seg=1)
    p = box(name + '_sheet', (0.22, 0.28, 0.02), (0, -0.02, 0.022), m=sheet, bevel=0.004, seg=1)
    c = box(name + '_clip', (0.12, 0.05, 0.035), (0, 0.15, 0.03), m=BLUE, bevel=0.01, seg=1)
    ls = [box(f'{name}_l{i}', (0.15, 0.022, 0.012), (0.0, 0.05 - i * 0.065, 0.034), m=GRAPH_LT, bevel=0, seg=1)
          for i in range(3)]
    ob = join([b, p, c] + ls, name)
    place(ob, loc, rot)
    return ob


def build(mode='preview'):
    reset()
    setup_world()
    base, radius_at = island_base(R=5.3, seed=23, top=SAND_C, lip='#cdc6b2', soil='#cdb38c',
                                  soil2='#ab906c', rock_c='#96988f',
                                  lobes=((2, 0.02), (3, 0.03), (5, 0.018)), squash=(1.08, 0.94))

    glass = mat('#b7d2dc', rough=0.12, alpha=0.24, coat=0.25, name='glass')
    glint = mat('#f4fbfd', rough=0.2, name='glint')
    lit_green = mat(GREEN, 0.3, emit=1.25, emit_color='#2fc07c')
    soft_green = mat(GREEN, 0.35, emit=0.9, emit_color='#2fc07c')
    soft_red = mat(RED, 0.35, emit=0.8)
    soft_amber = mat(AMBER, 0.35, emit=1.2)

    # ------------------------------------------------------------ ground
    y0 = -2.15                                  # centre line of the test line
    box('line_pad', (8.15, 1.3, 0.06), (-0.175, y0, 0.015), m='#d6cfbc', bevel=0.02, seg=2)
    cx, cy = -0.45, y0                          # sealed chamber
    box('chamber_apron', (2.5, 2.1, 0.07), (cx, cy - 0.02, 0.018), m='#c9c2ae', bevel=0.02, seg=2)
    for i, (x, y, r, sy) in enumerate([(-1.3, 0.25, 0.85, 0.7), (0.5, 0.5, 0.6, 0.8), (3.1, -0.75, 0.55, 0.7),
                                       (-4.45, 0.0, 0.5, 1.2), (1.2, 3.0, 0.75, 0.7), (-2.2, 3.6, 0.6, 0.5),
                                       (2.2, -3.75, 0.6, 0.5), (-2.6, -3.7, 0.7, 0.45), (4.6, 2.2, 0.4, 1.3)]):
        p = lathe(f'dry_patch_{i}', [(0, 0.014), (r * 0.8, 0.014), (r, 0.002)], (x, y, 0), m=DRY, verts=20)
        p.scale = (1, sy, 1)
        p.rotation_euler[2] = i * 0.7

    for i, (x, y, r, sy) in enumerate([(-0.4, 1.7, 1.5, 0.45), (2.9, 0.1, 0.9, 0.6), (-0.5, 2.9, 1.1, 0.4), (-0.6, -0.6, 0.9, 0.5)]):
        p = lathe(f'worn_patch_{i}', [(0, 0.008), (r * 0.85, 0.008), (r, 0.001)], (x, y, 0), m='#cdc5ae', verts=20)
        p.scale = (1, sy, 1)

    # ------------------------------------------------------------ 1a. conveyor with three task crates
    c0, c1 = -4.15, -1.35
    cm, cl = (c0 + c1) / 2, c1 - c0
    box('conv_bed', (cl - 0.06, 0.68, 0.07), (cm, y0, 0.455), m=GRAPH, bevel=0.02, seg=2)
    for s in (-1, 1):
        box(f'conv_rail_{s}', (cl, 0.1, 0.24), (cm, y0 + s * 0.4, 0.55), m=BLUE, bevel=0.035)
        box(f'conv_guard_{s}', (cl - 0.3, 0.04, 0.05), (cm, y0 + s * 0.4, 0.73), m=GRAPH_LT, bevel=0.015, seg=2)
        for k, x in enumerate((c0 + 0.2, cm - 0.45, cm + 0.45, c1 - 0.2)):
            cyl(f'conv_guard_post_{s}_{k}', 0.02, 0.1, (x, y0 + s * 0.4, 0.69), m=GRAPH_LT, verts=6, bevel=0)
        for k, x in enumerate((c0 + 0.18, cm, c1 - 0.18)):
            box(f'conv_leg_{s}_{k}', (0.11, 0.11, 0.44), (x, y0 + s * 0.36, 0.25), m=GRAPH_LT, bevel=0.025, seg=2)
            box(f'conv_foot_{s}_{k}', (0.2, 0.2, 0.05), (x, y0 + s * 0.36, 0.065), m=GRAPH, bevel=0.015, seg=1)
    for k, x in enumerate((c0 + 0.18, cm, c1 - 0.18)):
        box(f'conv_brace_{k}', (0.06, 0.66, 0.06), (x, y0, 0.2), m=GRAPH_LT, bevel=0.015, seg=1)
    n_roll = 13
    for i in range(n_roll):
        x = c0 + 0.13 + i * (cl - 0.26) / (n_roll - 1)
        cyl(f'conv_roller_{i}', 0.072, 0.7, (x, y0, 0.548), (90, 0, 0), '#cdd5d6', verts=8, bevel=0.015, seg=1)
    box('conv_stop', (0.08, 0.86, 0.34), (c0 - 0.02, y0, 0.6), m=OLIVE, bevel=0.03)
    # control post at the infeed
    cyl('ctl_post', 0.04, 0.8, (c0 + 0.25, y0 + 0.75, 0.42), m=GRAPH_LT, verts=8, bevel=0.01, seg=1)
    box('ctl_box', (0.3, 0.16, 0.26), (c0 + 0.25, y0 + 0.75, 0.9), (-18, 0, 0), OLIVE, bevel=0.04)
    sphere('ctl_btn_go', 0.045, (c0 + 0.18, y0 + 0.665, 0.95), m=soft_green, seg=10)
    sphere('ctl_btn_stop', 0.045, (c0 + 0.32, y0 + 0.665, 0.95), m=RED, seg=10)

    roller_top = 0.62
    card_cols = (RED, AMBER, BLUE)
    for i, x in enumerate((-3.72, -2.82, -1.92)):
        rz = (4, -5, 3)[i]
        parts = crate(f'task_crate_{i}', 0.46, x, y0, roller_top, rz, tone=i, seg=3, band=True)
        top = roller_top + 0.46
        parts.append(box(f'issue_card_{i}', (0.24, 0.035, 0.2), (x + 0.02, y0 - 0.05, top + 0.1), (-24, 0, rz + 6),
                         card_cols[i], bevel=0.012, seg=2))
        parts.append(box(f'issue_clip_{i}', (0.09, 0.07, 0.07), (x + 0.02, y0 - 0.01, top + 0.03), (-24, 0, rz + 6),
                         GRAPH, bevel=0.015, seg=1))
        parts.append(box(f'issue_line_{i}', (0.14, 0.02, 0.03), (x + 0.02, y0 - 0.085, top + 0.13), (-24, 0, rz + 6),
                         PAPER_C, bevel=0.005, seg=1))
        if i == 1:
            mover = join(parts, 'task_crate_moving')
            set_origin(mover, (x, y0, roller_top))
            animate(mover, 'bob', amp=0.012, speed=1.5)

    # ------------------------------------------------------------ 1b. sealed test chamber
    cw, cd, ch = 1.6, 1.5, 2.1
    box('chamber_plinth', (cw + 0.12, cd + 0.12, 0.24), (cx, cy, 0.15), m=GRAPH, bevel=0.05)
    box('chamber_floor', (cw - 0.2, cd - 0.2, 0.04), (cx, cy, 0.285), m=PAPER_C, bevel=0.01, seg=1)
    px, py = cw / 2 - 0.08, cd / 2 - 0.08
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        box(f'chamber_post_{i}', (0.18, 0.18, 1.62), (cx + sx * px, cy + sy * py, 1.07), m=OLIVE, bevel=0.04)
    for s in (-1, 1):
        box(f'chamber_sill_x{s}', (cw - 0.3, 0.12, 0.1), (cx, cy + s * py, 0.32), m=OLIVE, bevel=0.025, seg=2)
        box(f'chamber_sill_y{s}', (0.12, cd - 0.3, 0.1), (cx + s * px, cy, 0.32), m=OLIVE, bevel=0.025, seg=2)
    box('chamber_roof', (cw + 0.2, cd + 0.2, 0.22), (cx, cy, 1.98), m=OLIVE, bevel=0.06, seg=3)
    box('chamber_roof_cap', (cw - 0.3, cd - 0.3, 0.08), (cx, cy, 2.12), m=OLIVE_LT, bevel=0.03)
    box('chamber_vent', (0.5, 0.42, 0.2), (cx + 0.3, cy + 0.25, 2.24), m=GRAPH_LT, bevel=0.05)
    for k in range(3):
        box(f'chamber_vent_slat_{k}', (0.4, 0.03, 0.03), (cx + 0.3, cy + 0.035, 2.19 + k * 0.05), m=BLUE, bevel=0.008, seg=1)
    cyl('chamber_beacon_base', 0.09, 0.06, (cx - 0.45, cy - 0.4, 2.18), m=GRAPH, verts=12, bevel=0.015, seg=1)
    sphere('chamber_beacon', 0.085, (cx - 0.45, cy - 0.4, 2.25), (1, 1, 1.1), soft_amber, 12)
    # glass walls (front, back, right, upper left)
    fy, bky = cy - py, cy + py
    box('glass_front', (cw - 0.3, 0.04, 1.5), (cx, fy, 1.12), m=glass, bevel=0.01, seg=1)
    box('glass_back', (cw - 0.3, 0.04, 1.5), (cx, bky, 1.12), m=glass, bevel=0.01, seg=1)
    box('glass_right_top', (0.04, cd - 0.3, 0.72), (cx + px, cy, 1.51), m=glass, bevel=0.01, seg=1)
    box('glass_left_top', (0.04, cd - 0.3, 0.5), (cx - px, cy, 1.62), m=glass, bevel=0.01, seg=1)
    for k, (dx, ln) in enumerate(((-0.34, 0.62), (-0.2, 0.34))):
        box(f'glass_glint_{k}', (0.05, 0.016, ln), (cx + dx, fy - 0.026, 1.42 - k * 0.1), (0, 32, 0), glint, bevel=0.006, seg=1)
    box('glass_front_bar', (cw - 0.3, 0.07, 0.07), (cx, fy, 0.92), m=OLIVE, bevel=0.02, seg=2)
    # closed hatch on the left wall, where the conveyor arrives
    hx = cx - px
    box('hatch_frame', (0.1, cd - 0.3, 1.02), (hx, cy, 0.86), m=GRAPH, bevel=0.03)
    box('hatch_door', (0.1, 0.9, 0.82), (hx - 0.05, cy, 0.84), m='#6b7f89', bevel=0.05, seg=3)
    for k, z in enumerate((0.58, 1.1)):
        box(f'hatch_hinge_{k}', (0.07, 0.12, 0.14), (hx - 0.08, cy + 0.47, z), m=GRAPH, bevel=0.02, seg=1)
    torus('hatch_wheel', 0.17, 0.03, (hx - 0.17, cy, 0.86), (0, 90, 0), AMBER, seg=18, ring=8)
    for k in range(3):
        cyl(f'hatch_spoke_{k}', 0.02, 0.34, (hx - 0.17, cy, 0.86), (k * 60, 0, 0), AMBER, verts=6, bevel=0)
    cyl('hatch_hub', 0.05, 0.12, (hx - 0.14, cy, 0.86), (0, 90, 0), GRAPH, verts=10, bevel=0.015, seg=1)
    for k, z in enumerate((0.6, 1.08)):
        box(f'hatch_latch_{k}', (0.06, 0.2, 0.08), (hx - 0.1, cy - 0.42, z), m=GRAPH, bevel=0.02, seg=1)
    # right wall: lower panel with the outlet flap
    box('outlet_panel', (0.1, cd - 0.3, 0.8), (cx + px, cy, 0.75), m=GRAPH, bevel=0.03)
    box('outlet_flap', (0.06, 0.6, 0.3), (cx + px + 0.06, cy, 0.98), m='#6b7f89', bevel=0.03)
    # inside: the task under test on a stand, under an inspection lamp
    cyl('test_stand', 0.36, 0.2, (cx, cy, 0.4), m=BLUE, verts=20, bevel=0.03, seg=2)
    cyl('test_stand_top', 0.3, 0.05, (cx, cy, 0.52), m=GRAPH_LT, verts=20, bevel=0.012, seg=1)
    crate('test_crate', 0.46, cx, cy, 0.545, 14, tone=2, seg=3, band=True)
    cyl('test_lamp_stem', 0.025, 0.3, (cx, cy, 1.72), m=GRAPH, verts=6, bevel=0)
    lathe('test_lamp_shade', [(0.05, 0.14), (0.2, 0.0), (0.22, 0.0), (0.07, 0.17), (0.0, 0.17)], (cx, cy, 1.42), m=GRAPH, verts=14)
    sphere('test_lamp', 0.1, (cx, cy, 1.45), (1, 1, 0.7), mat('#fff3c4', 0.3, emit=5.0, emit_color='#ffd98a'), 12)
    for k, (dx, dy) in enumerate(((-0.52, 0.42), (0.52, 0.42))):
        cyl(f'probe_post_{k}', 0.03, 0.8, (cx + dx, cy + dy, 0.7), m=GRAPH_LT, verts=6, bevel=0)
        sphere(f'probe_tip_{k}', 0.05, (cx + dx, cy + dy, 1.12), m=soft_green if k else soft_amber, seg=8)

    # warning-striped floor edging around the chamber apron
    n = 0
    for run_y in (cy - 1.0, cy + 0.96):
        for i in range(11):
            x = cx - 1.1 + i * 0.22
            if run_y > cy and abs(x - 0.0) < 0.3:
                continue                         # leave room for the cable tray
            box(f'warn_block_{n}', (0.2, 0.15, 0.08), (x, run_y, 0.085), m=AMBER if i % 2 == 0 else GRAPH,
                bevel=0.025, seg=1)
            n += 1
    for sx in (-1, 1):
        for j in range(2):
            box(f'warn_block_{n}', (0.15, 0.2, 0.08), (cx + sx * 1.1, cy - 0.98 + 0.22 * (j + 1) * 1.0, 0.085),
                m=GRAPH if j % 2 == 0 else AMBER, bevel=0.025, seg=1)
            n += 1

    # network-off cue: the chamber's data cable lies unplugged in front of a network post
    nx, ny = 0.98, cy - 1.4
    box('net_post', (0.26, 0.26, 0.62), (nx, ny, 0.31), m=OLIVE, bevel=0.05)
    box('net_socket_plate', (0.03, 0.18, 0.18), (nx - 0.135, ny, 0.3), m=PAPER_C, bevel=0.01, seg=1)
    box('net_socket_hole', (0.03, 0.09, 0.07), (nx - 0.143, ny, 0.3), m=GRAPH, bevel=0.008, seg=1)
    sphere('net_globe', 0.15, (nx, ny, 0.8), m=BLUE, seg=14)
    torus('net_globe_eq', 0.153, 0.014, (nx, ny, 0.8), m=PAPER_C, seg=14, ring=4)
    torus('net_globe_mer', 0.153, 0.014, (nx, ny, 0.8), (90, 0, 25), PAPER_C, seg=14, ring=4)
    torus('net_globe_mer2', 0.153, 0.014, (nx, ny, 0.8), (90, 0, 115), PAPER_C, seg=14, ring=4)
    cyl('net_globe_neck', 0.05, 0.08, (nx, ny, 0.65), m=GRAPH, verts=8, bevel=0.01, seg=1)
    tube('net_cable', [(cx + 0.35, cy - 0.78, 0.2), (cx + 0.36, cy - 0.95, 0.12), (cx + 0.34, cy - 1.14, 0.045),
                       (cx + 0.1, cy - 1.36, 0.045), (cx + 0.3, cy - 1.56, 0.045), (cx + 0.62, cy - 1.42, 0.045),
                       (cx + 0.78, cy - 1.4, 0.045)], 0.035, GRAPH, res=4)
    box('net_cable_gland', (0.16, 0.08, 0.14), (cx + 0.35, cy - 0.8, 0.2), m=BLUE, bevel=0.025, seg=1)
    pgx, pgy = cx + 0.88, cy - 1.4
    cyl('net_plug', 0.065, 0.2, (pgx, pgy, 0.068), (0, 90, 0), AMBER, verts=10, bevel=0.02, seg=2)
    cyl('net_plug_collar', 0.075, 0.05, (pgx - 0.09, pgy, 0.075), (0, 90, 0), GRAPH, verts=10, bevel=0.01, seg=1)
    for k, dy in enumerate((-0.025, 0.025)):
        cyl(f'net_plug_pin_{k}', 0.016, 0.08, (pgx + 0.13, pgy + dy, 0.068), (0, 90, 0), '#d6dcdc', verts=6, bevel=0)

    # ------------------------------------------------------------ 1c. output chute with the single patch slip
    ax, bx = cx + px + 0.05, cx + px + 1.05
    az, bz = 0.92, 0.5
    ang = math.degrees(math.atan2(az - bz, bx - ax))
    ln = math.hypot(bx - ax, az - bz)
    mx, mz = (ax + bx) / 2, (az + bz) / 2
    box('chute_slide', (ln, 0.5, 0.05), (mx, y0, mz), (0, ang, 0), BLUE_LT, bevel=0.015, seg=2)
    for s in (-1, 1):
        box(f'chute_lip_{s}', (ln, 0.05, 0.14), (mx, y0 + s * 0.27, mz + 0.045), (0, ang, 0), BLUE, bevel=0.02, seg=2)
    box('chute_leg', (0.09, 0.44, 0.62), (mx + 0.05, y0, 0.36), m=GRAPH_LT, bevel=0.025, seg=2)
    tx = bx + 0.24
    box('tray_stand', (0.32, 0.4, 0.4), (tx, y0, 0.24), m=GRAPH_LT, bevel=0.04)
    box('tray', (0.56, 0.62, 0.06), (tx, y0, 0.46), m=BLUE_LT, bevel=0.02, seg=2)
    box('tray_end', (0.05, 0.62, 0.15), (tx + 0.27, y0, 0.52), m=BLUE, bevel=0.02, seg=2)
    for s in (-1, 1):
        box(f'tray_side_{s}', (0.56, 0.05, 0.15), (tx, y0 + s * 0.29, 0.52), m=BLUE, bevel=0.02, seg=2)
    slip = [box('patch_slip', (0.34, 0.26, 0.03), (tx - 0.02, y0, 0.505), m=WHITE, bevel=0.008, seg=1)]
    for k, (col, w, dx) in enumerate(((GREEN, 0.2, -0.03), (RED, 0.16, -0.05), (GREEN, 0.22, -0.02))):
        slip.append(box(f'patch_line_{k}', (w, 0.035, 0.014), (tx - 0.02 + dx, y0 + 0.07 - k * 0.07, 0.522), m=col,
                        bevel=0.004, seg=1))
    slip = join(slip, 'patch_slip')
    set_origin(slip, (tx - 0.02, y0, 0.49))
    slip.rotation_euler[2] = math.radians(9)

    # ------------------------------------------------------------ 2. verdict cabinet with signal tower
    vx, vy = 2.82, y0 + 0.03
    vw, vd, vh = 1.8, 0.86, 1.2
    box('verdict_plinth', (vw + 0.08, vd + 0.08, 0.14), (vx, vy, 0.1), m=GRAPH, bevel=0.03)
    box('verdict_body', (vw, vd, vh), (vx, vy, 0.17 + vh / 2), m=PAPER_C, bevel=0.07, seg=3)
    box('verdict_top', (vw + 0.1, vd + 0.1, 0.09), (vx, vy, 0.17 + vh + 0.035), m=OLIVE, bevel=0.03)
    ffy = vy - vd / 2
    for i, dx in enumerate((-0.44, 0.44)):
        dxc = vx + dx
        box(f'drawer_{i}', (0.74, 0.08, 0.42), (dxc, ffy - 0.02, 0.5), m='#d8d0bc', bevel=0.035)
        box(f'drawer_handle_{i}', (0.34, 0.06, 0.06), (dxc, ffy - 0.08, 0.56), m=GRAPH, bevel=0.02, seg=2)
        box(f'drawer_slot_{i}', (0.2, 0.03, 0.09), (dxc, ffy - 0.055, 0.4), m=WHITE, bevel=0.01, seg=1)
        box(f'lamp_plate_{i}', (0.74, 0.06, 0.36), (dxc, ffy - 0.015, 1.03), m=GRAPH, bevel=0.035)
        left_mat = soft_red if i == 0 else soft_green
        sphere(f'lamp_{i}_a', 0.095, (dxc - 0.23, ffy - 0.05, 1.03), (1, 0.7, 1), left_mat, 12)
        sphere(f'lamp_{i}_b', 0.095, (dxc + 0.23, ffy - 0.05, 1.03), (1, 0.7, 1), soft_green, 12)
        for k, sx in enumerate((-0.23, 0.23)):
            torus(f'lamp_bezel_{i}_{k}', 0.1, 0.018, (dxc + sx, ffy - 0.05, 1.03), (90, 0, 0), '#cdd5d6', seg=12, ring=5)
        if i == 0:   # failing -> passing: an arrow from the red lamp to the green one
            prism('verdict_arrow', [(-0.1, -0.022), (0.02, -0.022), (0.02, -0.065), (0.1, 0.0), (0.02, 0.065),
                                    (0.02, 0.022), (-0.1, 0.022)], 0.04, (dxc, ffy - 0.04, 1.03), (90, 0, 0), PAPER_C,
                  bevel=0.008, seg=1)
        else:        # passing stays passing: a plain link
            box('verdict_link', (0.16, 0.04, 0.04), (dxc, ffy - 0.055, 1.03), m=PAPER_C, bevel=0.01, seg=1)
    # signal tower, green lit
    sx_, sy_ = vx + 0.5, vy + 0.05
    zt = 0.17 + vh + 0.08
    cyl('tower_base', 0.17, 0.1, (sx_, sy_, zt + 0.05), m=GRAPH, verts=16, bevel=0.025, seg=2)
    cyl('tower_pole', 0.045, 0.82, (sx_, sy_, zt + 0.5), m='#cdd5d6', verts=10, bevel=0.01, seg=1)
    zs = zt + 0.9
    cyl('tower_collar', 0.15, 0.06, (sx_, sy_, zs + 0.03), m=GRAPH, verts=16, bevel=0.015, seg=1)
    cyl('tower_red', 0.13, 0.25, (sx_, sy_, zs + 0.185), m=mat('#a8443c', 0.35), verts=16, bevel=0.03, seg=2)
    cyl('tower_sep_0', 0.145, 0.035, (sx_, sy_, zs + 0.325), m=GRAPH, verts=16, bevel=0.01, seg=1)
    cyl('tower_amber', 0.13, 0.25, (sx_, sy_, zs + 0.465), m=mat('#b98a34', 0.35), verts=16, bevel=0.03, seg=2)
    cyl('tower_sep_1', 0.145, 0.035, (sx_, sy_, zs + 0.605), m=GRAPH, verts=16, bevel=0.01, seg=1)
    tower = cyl('signal_tower_lamp', 0.135, 0.27, (sx_, sy_, zs + 0.755), m=lit_green, verts=16, bevel=0.03, seg=2)
    animate(tower, 'pulse', speed=1.1)
    lathe('tower_cap', [(0.15, 0), (0.15, 0.03), (0.08, 0.1), (0, 0.11)], (sx_, sy_, zs + 0.89), m=GRAPH, verts=16)
    clipboard('clipboard_verdict', (vx - 0.4, vy + 0.02, zt + 0.02), (0, 0, 22))

    # ------------------------------------------------------------ cable tray: chamber -> server rack
    ty = -0.85
    rx, ry = 2.62, 3.2                          # server rack
    tray_c = '#9aa7a6'
    cable_cols = (GRAPH, AMBER, BLUE)

    def tray_run(name, a, b):
        (x0_, y0_), (x1_, y1_) = a, b
        horiz = abs(x1_ - x0_) > abs(y1_ - y0_)
        ln_ = abs(x1_ - x0_) if horiz else abs(y1_ - y0_)
        mx_, my_ = (x0_ + x1_) / 2, (y0_ + y1_) / 2
        sz = (lambda l, w, h: (l, w, h)) if horiz else (lambda l, w, h: (w, l, h))
        box(name, sz(ln_, 0.34, 0.045), (mx_, my_, 0.02), m=tray_c, bevel=0.012, seg=1)
        for s in (-1, 1):
            off = (0, s * 0.165) if horiz else (s * 0.165, 0)
            box(f'{name}_lip{s}', sz(ln_, 0.035, 0.1), (mx_ + off[0], my_ + off[1], 0.05), m=tray_c, bevel=0.012, seg=1)
        for k, col in enumerate(cable_cols):
            d = (k - 1) * 0.085
            off = (0, d) if horiz else (d, 0)
            box(f'{name}_cable{k}', sz(ln_ + 0.1, 0.055, 0.055), (mx_ + off[0], my_ + off[1], 0.068), m=col,
                bevel=0.022, seg=1)
        n_r = max(1, int(ln_ / 0.7))
        for k in range(n_r):
            t = (k + 0.5) / n_r
            px_, py_ = x0_ + (x1_ - x0_) * t, y0_ + (y1_ - y0_) * t
            box(f'{name}_strap{k}', sz(0.06, 0.38, 0.05), (px_, py_, 0.095), m=GRAPH_LT, bevel=0.012, seg=1)

    tcx = 1.5
    tray_run('tray_a', (0.0, cy + 0.8), (0.0, ty - 0.1))
    tray_run('tray_b', (0.2, ty), (tcx - 0.2, ty))
    tray_run('tray_c', (tcx, ty + 0.2), (tcx, ry - 0.2))
    tray_run('tray_d', (tcx + 0.2, ry), (rx - 0.44, ry))
    for k, (x, y) in enumerate(((0.0, ty), (tcx, ty), (tcx, ry))):
        box(f'tray_junction_{k}', (0.46, 0.46, 0.16), (x, y, 0.08), m=OLIVE, bevel=0.04)
        box(f'tray_junction_lid_{k}', (0.3, 0.3, 0.04), (x, y, 0.17), m=OLIVE_LT, bevel=0.012, seg=1)

    # ------------------------------------------------------------ 7a. server rack with indicator rows
    rw, rd, rh = 0.84, 0.68, 1.45
    box('rack_plinth', (rw + 0.06, rd + 0.06, 0.1), (rx, ry, 0.06), m=GRAPH_LT, bevel=0.025)
    box('rack_body', (rw, rd, rh), (rx, ry, 0.1 + rh / 2), m=GRAPH, bevel=0.06, seg=3)
    box('rack_cap', (rw + 0.06, rd + 0.06, 0.07), (rx, ry, 0.1 + rh + 0.02), m=BLUE, bevel=0.025)
    rfy = ry - rd / 2
    leds = []
    led_cols = [[GREEN, GREEN, AMBER, GREEN, GREEN], [GREEN, GREEN, GREEN, GREEN, AMBER],
                [GREEN, AMBER, GREEN, GREEN, GREEN], [GREEN, GREEN, GREEN, AMBER, GREEN]]
    for r in range(4):
        z = 0.36 + r * 0.32
        box(f'rack_unit_{r}', (rw - 0.14, 0.05, 0.25), (rx, rfy - 0.012, z), m=GRAPH_LT, bevel=0.025, seg=2)
        box(f'rack_unit_grip_{r}', (0.2, 0.04, 0.035), (rx + 0.2, rfy - 0.045, z - 0.05), m=BLUE, bevel=0.01, seg=1)
        for c in range(5):
            col = led_cols[r][c]
            leds.append(box(f'rack_led_{r}_{c}', (0.05, 0.035, 0.05), (rx - 0.27 + c * 0.075, rfy - 0.045, z + 0.045),
                            m=mat(col, 0.3, emit=1.8, emit_color='#2fc07c' if col == GREEN else col), bevel=0.012, seg=1))
    lights = join(leds, 'server_lights')
    animate(lights, 'pulse', speed=2.2)
    for k in range(5):
        box(f'rack_vent_{k}', (0.03, rd - 0.22, 0.045), (rx - rw / 2 - 0.004, ry, 0.45 + k * 0.2), m=GRAPH_LT,
            bevel=0.01, seg=1)
    box('rack_inlet', (0.14, 0.4, 0.2), (rx - rw / 2 - 0.03, ry, 0.16), m=OLIVE, bevel=0.03, seg=2)

    # ------------------------------------------------------------ 7b. hourglass on a pedestal (the time budget)
    gx, gy, gz = 4.2, -0.3, 0.66
    lathe('hourglass_pedestal', [(0, 0), (0.44, 0), (0.44, 0.1), (0.32, 0.17), (0.29, 0.52), (0.4, 0.58), (0.4, 0.66),
                                 (0, 0.66)], (gx, gy, 0), m='#d8d1c0', verts=24)
    hg = [cyl('hg_base', 0.36, 0.08, (gx, gy, gz + 0.04), m=WOOD_DARK, verts=24, bevel=0.025, seg=2),
          cyl('hg_top', 0.36, 0.08, (gx, gy, gz + 1.16), m=WOOD_DARK, verts=24, bevel=0.025, seg=2)]
    for k in range(3):
        a = TAU * k / 3 + 0.5
        hg.append(cyl(f'hg_post_{k}', 0.032, 1.06, (gx + 0.31 * math.cos(a), gy + 0.31 * math.sin(a), gz + 0.6),
                      m=WOOD, verts=8, bevel=0.008, seg=1))
    hg.append(lathe('hg_glass', [(0.0, 0.08), (0.24, 0.08), (0.26, 0.2), (0.22, 0.4), (0.05, 0.6), (0.22, 0.8),
                                 (0.26, 1.0), (0.24, 1.12), (0.0, 1.12)], (gx, gy, gz), m=glass, verts=20))
    hg.append(lathe('hg_sand_low', [(0.0, 0.085), (0.225, 0.085), (0.235, 0.17), (0.12, 0.24), (0.0, 0.34)],
                    (gx, gy, gz), m=AMBER, verts=16))
    hg.append(lathe('hg_sand_top', [(0.0, 0.63), (0.04, 0.63), (0.2, 0.8), (0.2, 0.85), (0.0, 0.83)],
                    (gx, gy, gz), m=AMBER, verts=16))
    hg.append(cyl('hg_stream', 0.016, 0.32, (gx, gy, gz + 0.48), m=AMBER, verts=6, bevel=0))
    hourglass = join(hg, 'hourglass')
    set_origin(hourglass, (gx, gy, gz))
    animate(hourglass, 'spin', axis='z', speed=0.12)

    # ------------------------------------------------------------ 5. two balance scales that agree
    bxc, byc = -2.7, -0.5
    box('dais_base', (2.7, 0.8, 0.16), (bxc, byc, 0.08), m=OLIVE_LT, bevel=0.03)
    box('dais_top', (2.84, 0.94, 0.09), (bxc, byc, 0.2), m=WOOD, bevel=0.03)
    bt = 0.245
    for i, (dx, col) in enumerate(((-0.76, BLUE), (0.76, OLIVE_LT))):
        sxp = bxc + dx
        box(f'scale_base_{i}', (0.6, 0.36, 0.1), (sxp, byc, bt + 0.05), m=col, bevel=0.035)
        cyl(f'scale_column_{i}', 0.05, 0.9, (sxp, byc, bt + 0.54), m=col, verts=10, bevel=0.01, seg=1)
        box(f'scale_beam_{i}', (1.04, 0.07, 0.07), (sxp, byc, bt + 0.98), m=col, bevel=0.025)
        sphere(f'scale_pivot_{i}', 0.08, (sxp, byc, bt + 0.98), m=GRAPH, seg=12)
        # dial with a pointer standing exactly upright: both scales read level
        prism(f'scale_dial_{i}', [(-0.2, 0.0), (0.2, 0.0), (0.14, 0.2), (0.0, 0.26), (-0.14, 0.2)], 0.05,
              (sxp, byc - 0.03, bt + 1.03), (90, 0, 0), PAPER_C, bevel=0.012, seg=1)
        box(f'scale_mark_{i}', (0.045, 0.03, 0.06), (sxp, byc - 0.085, bt + 1.245), m=GREEN, bevel=0.008, seg=1)
        prism(f'scale_pointer_{i}', [(-0.034, 0.0), (0.034, 0.0), (0.0, 0.2)], 0.03, (sxp, byc - 0.08, bt + 1.03),
              (90, 0, 0), RED, bevel=0.006, seg=1)
        for s in (-1, 1):
            ex = sxp + s * 0.46
            pz = bt + 0.46
            for k, (ox, oy) in enumerate(((0.0, -0.14), (0.0, 0.14))):
                tube(f'scale_cord_{i}_{s}_{k}', [(ex, byc, bt + 0.96), (ex + ox, byc + oy, pz + 0.035)], 0.016, GRAPH_LT,
                     smooth_curve=False, res=1)
            lathe(f'scale_pan_{i}_{s}', [(0, 0), (0.14, 0), (0.21, 0.055), (0.22, 0.055), (0.15, -0.025), (0, -0.025)],
                  (ex, byc, pz), m='#cdd5d6', verts=16)
            cyl(f'scale_pan_rest_{i}_{s}', 0.035, pz - bt - 0.02, (ex, byc, bt + (pz - bt - 0.02) / 2), m=col, verts=8,
                bevel=0.008, seg=1)
            if s < 0:
                box(f'scale_load_{i}', (0.17, 0.17, 0.17), (ex, byc, pz + 0.085), (0, 0, 20), CRATES[0], bevel=0.02)
            else:
                cyl(f'scale_weight_{i}_0', 0.08, 0.11, (ex, byc, pz + 0.055), m=AMBER, verts=10, bevel=0.015, seg=1)
                cyl(f'scale_weight_{i}_1', 0.04, 0.06, (ex, byc, pz + 0.135), m=AMBER, verts=8, bevel=0.01, seg=1)
    # the equals sign between them
    cyl('equals_post', 0.035, 0.84, (bxc, byc, bt + 0.42), m=GRAPH_LT, verts=8, bevel=0.008, seg=1)
    box('equals_plate', (0.4, 0.07, 0.34), (bxc, byc, bt + 0.98), m=GRAPH, bevel=0.045)
    for k, dz in enumerate((-0.065, 0.065)):
        box(f'equals_bar_{k}', (0.24, 0.04, 0.06), (bxc, byc - 0.04, bt + 0.98 + dz), m=soft_green, bevel=0.012, seg=1)
        box(f'equals_bar_back_{k}', (0.24, 0.04, 0.06), (bxc, byc + 0.04, bt + 0.98 + dz), m=soft_green, bevel=0.012, seg=1)
    clipboard('clipboard_bench', (bxc + 0.02, byc - 0.3, bt + 0.02), (0, 0, -12))

    # ------------------------------------------------------------ 3. quarantine pen and the four gates
    qx, qy, qs = -3.3, 1.7, 1.6
    h = qs / 2
    box('pen_floor', (qs + 0.16, qs + 0.16, 0.07), (qx, qy, 0.02), m='#d3ccb8', bevel=0.02, seg=2)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        box(f'pen_post_{i}', (0.13, 0.13, 1.34), (qx + sx * h, qy + sy * h, 0.69), m=GRAPH, bevel=0.03)
    for s in (-1, 1):
        box(f'pen_top_x{s}', (qs, 0.09, 0.09), (qx, qy + s * h, 1.27), m=GRAPH, bevel=0.02, seg=2)
        box(f'pen_low_x{s}', (qs, 0.08, 0.08), (qx, qy + s * h, 0.14), m=GRAPH, bevel=0.02, seg=2)
    box('pen_top_y-1', (0.09, qs, 0.09), (qx - h, qy, 1.27), m=GRAPH, bevel=0.02, seg=2)
    box('pen_low_y-1', (0.08, qs, 0.08), (qx - h, qy, 0.14), m=GRAPH, bevel=0.02, seg=2)
    box('pen_top_y1', (0.09, qs, 0.09), (qx + h, qy, 1.27), m=GRAPH, bevel=0.02, seg=2)
    for k, dy in enumerate((-0.585, 0.585)):
        box(f'pen_low_y1_{k}', (0.08, 0.43, 0.08), (qx + h, qy + dy, 0.14), m=GRAPH, bevel=0.02, seg=2)
        box(f'pen_door_post_{k}', (0.1, 0.1, 1.2), (qx + h, qy + (-0.4 if k == 0 else 0.4), 0.66), m=AMBER, bevel=0.025, seg=2)
    nb = 0
    for i in range(7):
        d = -0.6 + i * 0.2
        for (x, y) in ((qx + d, qy - h), (qx + d, qy + h), (qx - h, qy + d)):
            cyl(f'pen_bar_{nb}', 0.028, 1.1, (x, y, 0.7), m=GRAPH_LT, verts=8, bevel=0)
            nb += 1
    for dy in (-0.6, 0.6):
        cyl(f'pen_bar_{nb}', 0.028, 1.1, (qx + h, qy + dy, 0.7), m=GRAPH_LT, verts=8, bevel=0)
        nb += 1
    # quarantine warning diamond on the front bars
    box('pen_sign', (0.36, 0.045, 0.36), (qx - 0.25, qy - h - 0.052, 0.82), (0, 45, 0), AMBER, bevel=0.03)
    box('pen_sign_bar', (0.055, 0.03, 0.17), (qx - 0.25, qy - h - 0.08, 0.86), m=GRAPH, bevel=0.01, seg=1)
    box('pen_sign_dot', (0.055, 0.03, 0.055), (qx - 0.25, qy - h - 0.08, 0.71), m=GRAPH, bevel=0.01, seg=1)
    # held crates: a 3-2-1 stack and two loose ones
    qs_ = 0.42
    qz = 0.055
    stack = [(-0.46, 0.38, 0), (0.0, 0.38, 0), (0.46, 0.38, 0), (-0.23, 0.38, 1), (0.23, 0.38, 1), (0.0, 0.38, 2)]
    for i, (dx, dy, lv) in enumerate(stack):
        crate(f'held_crate_{i}', qs_, qx + dx, qy + dy, qz + lv * qs_, (i * 7) % 5 - 2, tone=i, tag=AMBER, band=True)
    crate('held_crate_6', qs_, qx - 0.42, qy - 0.36, qz, 16, tone=1, tag=AMBER, band=True)
    crate('held_crate_7', qs_, qx + 0.1, qy - 0.3, qz, -9, tone=2, tag=AMBER, band=True)

    # exit lane through exactly four gates
    lx0, lx1 = qx + h + 0.02, 1.28
    ly = qy
    box('lane_floor', (lx1 - lx0, 0.66, 0.05), ((lx0 + lx1) / 2, ly, 0.012), m=PAPER_C, bevel=0.015, seg=1)
    for s in (-1, 1):
        box(f'lane_kerb_{s}', (lx1 - lx0, 0.05, 0.08), ((lx0 + lx1) / 2, ly + s * 0.35, 0.03), m=OLIVE_LT, bevel=0.02, seg=2)
    gate_x = (-1.78, -0.88, 0.02, 0.92)
    gate_col = (BLUE, AMBER, RED, GREEN)
    for i, (gxp, col) in enumerate(zip(gate_x, gate_col)):
        opened = i < 2
        fy_, by_ = ly - 0.5, ly + 0.5
        for k, yy in enumerate((fy_, by_)):
            box(f'gate_{i}_post_{k}', (0.16, 0.14, 1.12), (gxp, yy, 0.56), m=OLIVE, bevel=0.035)
            box(f'gate_{i}_foot_{k}', (0.26, 0.24, 0.07), (gxp, yy, 0.035), m=GRAPH, bevel=0.02, seg=1)
        box(f'gate_{i}_lintel', (0.18, 1.2, 0.16), (gxp, ly, 1.18), m=OLIVE, bevel=0.04)
        box(f'gate_{i}_plate', (0.34, 0.05, 0.34), (gxp, fy_ - 0.09, 0.98), m=col, bevel=0.04)
        num = text(f'gate_{i}_num', str(i + 1), 0.25, 0.03, (gxp, fy_ - 0.118, 0.975), (90, 0, 0), GRAPH)
        num.data.resolution_u = 2
        num.data.bevel_depth = 0.0
        box(f'gate_{i}_cap', (0.2, 0.3, 0.06), (gxp, ly, 1.285), m=col, bevel=0.02, seg=1)
        box(f'gate_{i}_pivot', (0.12, 0.1, 0.16), (gxp - 0.1, fy_ + 0.02, 0.52), m=GRAPH, bevel=0.025, seg=1)
        if opened:      # barrier raised, padlock hangs open on the post
            t = math.radians(12)
            cz_, cy_ = 0.52 + 0.4 * math.cos(t), fy_ + 0.02 + 0.4 * math.sin(t)
            box(f'gate_{i}_arm', (0.075, 0.075, 0.9), (gxp - 0.19, cy_, cz_), (-12, 0, 0), col, bevel=0.025, seg=2)
            box(f'gate_{i}_arm_tip', (0.09, 0.09, 0.12), (gxp - 0.19, fy_ + 0.02 + 0.82 * math.sin(t), 0.52 + 0.82 * math.cos(t)),
                (-12, 0, 0), PAPER_C, bevel=0.02, seg=1)
            box(f'gate_{i}_lock', (0.15, 0.06, 0.13), (gxp, fy_ - 0.1, 0.6), m=col, bevel=0.025, seg=1)
            torus(f'gate_{i}_shackle', 0.045, 0.016, (gxp + 0.045, fy_ - 0.1, 0.71), (90, 0, 0), '#cdd5d6', seg=10, ring=5)
        else:           # barrier down across the lane, padlock closed on it
            box(f'gate_{i}_arm', (0.075, 0.9, 0.075), (gxp - 0.13, ly - 0.02, 0.52), m=col, bevel=0.025, seg=2)
            box(f'gate_{i}_arm_tip', (0.09, 0.12, 0.09), (gxp - 0.13, ly + 0.4, 0.52), m=PAPER_C, bevel=0.02, seg=1)
            box(f'gate_{i}_rest', (0.1, 0.1, 0.12), (gxp - 0.11, by_ - 0.06, 0.44), m=GRAPH, bevel=0.02, seg=1)
            box(f'gate_{i}_lock', (0.07, 0.17, 0.15), (gxp - 0.19, ly, 0.47), m=col, bevel=0.025, seg=1)
            torus(f'gate_{i}_shackle', 0.05, 0.017, (gxp - 0.19, ly, 0.555), (0, 90, 0), '#cdd5d6', seg=10, ring=5)
            box(f'gate_{i}_keyhole', (0.02, 0.035, 0.05), (gxp - 0.228, ly, 0.46), m=GRAPH, bevel=0.006, seg=1)
    # one crate midway (past gates 1 and 2, waiting at 3), on a small dolly
    mxc = (gate_x[1] + gate_x[2]) / 2
    box('dolly', (0.5, 0.5, 0.05), (mxc, ly, 0.095), m=BLUE, bevel=0.015, seg=1)
    for k, (dx, dy) in enumerate(((-0.18, -0.2), (0.18, -0.2), (0.18, 0.2), (-0.18, 0.2))):
        cyl(f'dolly_wheel_{k}', 0.04, 0.04, (mxc + dx, ly + dy, 0.075), (90, 0, 0), GRAPH, verts=8, bevel=0.008, seg=1)
    crate('gate_crate', qs_, mxc, ly, 0.12, 4, tone=0, tag=AMBER, band=True)
    for k, x in enumerate((-2.2, -1.33, 0.47, 1.16)):
        prism(f'lane_chevron_{k}', [(-0.09, -0.14), (-0.01, -0.14), (0.09, 0.0), (-0.01, 0.14), (-0.09, 0.14), (0.01, 0.0)],
              0.03, (x, ly, 0.03), m=OLIVE_LT, bevel=0.006, seg=1)

    # ------------------------------------------------------------ 6. admitted stock: 3 pallets x 17 = 51 crates
    cs, pitch = 0.28, 0.3
    layout = [(i, j, 0) for i in range(3) for j in range(3)] + \
             [(i, j, 1) for i in range(3) for j in (1, 2)] + [(0, 2, 2), (1, 2, 2)]
    assert len(layout) == 17
    total = 0
    for p, (pxc, pyc, prz, flip) in enumerate(((2.25, 1.72, 2, False), (3.42, 1.98, -4, True), (4.02, 0.82, 7, False))):
        parts = []
        for k in range(3):
            dx, dy = rot2(0, (k - 1) * 0.4, prz)
            parts.append(box(f'pallet_{p}_runner_{k}', (1.0, 0.11, 0.09), (pxc + dx, pyc + dy, 0.045), (0, 0, prz), WOOD_DARK,
                             bevel=0.015, seg=1))
        for k in range(5):
            dx, dy = rot2((k - 2) * 0.205, 0, prz)
            parts.append(box(f'pallet_{p}_plank_{k}', (0.18, 1.02, 0.045), (pxc + dx, pyc + dy, 0.11), (0, 0, prz), WOOD,
                             bevel=0.012, seg=1))
        for n_, (i, j, lv) in enumerate(layout):
            ii = 2 - i if flip else i
            dx, dy = rot2((ii - 1) * pitch, (j - 1) * pitch, prz)
            parts += crate(f'stock_{p}_{n_}', cs, pxc + dx, pyc + dy, 0.133 + lv * cs, prz + ((n_ * 5 + p) % 3 - 1) * 1.5,
                           tone=n_ + p + lv, tag=GREEN, seg=1)
            total += 1
        join(parts, f'admitted_pallet_{p}')
    assert total == 51, total
    print('[island] admitted crates:', total)

    # hand truck parked in front of the conveyor
    hx_, hy_, hrz = -3.1, -3.3, 8

    def ht(dx, dy):
        x, y = rot2(dx, dy, hrz)
        return hx_ + x, hy_ + y
    x, y = ht(0, -0.17)
    box('truck_toe', (0.44, 0.28, 0.04), (x, y, 0.03), (0, 0, hrz), BLUE, bevel=0.012, seg=1)
    lean = math.tan(math.radians(9))
    for s in (-1, 1):
        x, y = ht(s * 0.18, (0.62 - 0.03) * lean)
        cyl(f'truck_upright_{s}', 0.028, 1.2, (x, y, 0.62), (-9, 0, hrz), BLUE, verts=8, bevel=0.008, seg=1)
        x, y = ht(s * 0.26, 0.06)
        cyl(f'truck_wheel_{s}', 0.13, 0.08, (x, y, 0.13), (0, 90, hrz), GRAPH, verts=14, bevel=0.03, seg=2)
        cyl(f'truck_hub_{s}', 0.05, 0.1, (x, y, 0.13), (0, 90, hrz), '#cdd5d6', verts=8, bevel=0.01, seg=1)
    x, y = ht(0, 0.06)
    cyl('truck_axle', 0.022, 0.5, (x, y, 0.13), (0, 90, hrz), GRAPH_LT, verts=6, bevel=0)
    for k, z in enumerate((0.34, 0.68, 1.0)):
        x, y = ht(0, (z - 0.03) * lean)
        box(f'truck_bar_{k}', (0.38, 0.04, 0.06), (x, y, z), (-9, 0, hrz), BLUE, bevel=0.015, seg=1)
    x, y = ht(0, (1.2 - 0.03) * lean)
    box('truck_grip', (0.46, 0.06, 0.06), (x, y, 1.21), (-9, 0, hrz), GRAPH, bevel=0.025, seg=2)

    # ------------------------------------------------------------ 4. the tool wall: exactly nine tools, 3 x 3
    wx, wy = -0.5, 3.78
    bw, bh, bz0 = 2.5, 2.3, 0.62
    bzc = bz0 + bh / 2
    box('wall_board', (bw, 0.1, bh), (wx, wy, bzc), m=PAPER_C, bevel=0.03)
    for s in (-1, 1):
        box(f'wall_leg_{s}', (0.14, 0.14, bz0 + bh + 0.1), (wx + s * (bw / 2 + 0.07), wy, (bz0 + bh + 0.1) / 2), m=OLIVE, bevel=0.035)
        box(f'wall_foot_{s}', (0.2, 1.0, 0.1), (wx + s * (bw / 2 + 0.07), wy, 0.05), m=OLIVE, bevel=0.03)
        box(f'wall_brace_{s}', (0.07, 0.07, 0.72), (wx + s * (bw / 2 + 0.07), wy + 0.27, 0.33), (38, 0, 0), OLIVE_LT, bevel=0.02, seg=1)
        box(f'wall_brace_f_{s}', (0.07, 0.07, 0.72), (wx + s * (bw / 2 + 0.07), wy - 0.27, 0.33), (-38, 0, 0), OLIVE_LT, bevel=0.02, seg=1)
    box('wall_header', (bw + 0.28, 0.16, 0.14), (wx, wy, bz0 + bh + 0.06), m=OLIVE, bevel=0.04)
    box('wall_sill', (bw + 0.02, 0.26, 0.07), (wx, wy - 0.06, bz0 - 0.03), m=OLIVE, bevel=0.02, seg=2)
    by = wy - 0.05                               # front face of the board
    hole = '#cfc7b2'
    for i in range(10):
        for j in range(9):
            cyl(f'peg_hole_{i}_{j}', 0.022, 0.02, (wx - 1.08 + i * 0.24, by - 0.002, bz0 + 0.19 + j * 0.24), (90, 0, 0), hole,
                verts=5, bevel=0)

    def P(c, u, v, d=0.0):
        return (wx + c[0] + u, by - d, bzc + c[1] + v)

    def bar(name, c, a, b, width, depth, m, bevel=0.012, off=0.0):
        du, dv = b[0] - a[0], b[1] - a[1]
        return box(name, (math.hypot(du, dv), depth, width), P(c, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, depth / 2 + off),
                   (0, -math.degrees(math.atan2(dv, du)), 0), m, bevel=bevel, seg=1)

    def disc(name, c, uv, r, depth, m, verts=14, off=0.0):
        return cyl(name, r, depth, P(c, uv[0], uv[1], depth / 2 + off), (90, 0, 0), m, verts=verts, bevel=0.01, seg=1)

    def ring(name, c, uv, R, r, m, d=0.04):
        return torus(name, R, r, P(c, uv[0], uv[1], d), (90, 0, 0), m, seg=20, ring=8)

    def flat(name, c, outline, depth, m, uv=(0, 0), bevel=0.012, off=0.0):
        return prism(name, outline, depth, P(c, uv[0], uv[1], off), (90, 0, 0), m, bevel=bevel, seg=1)

    def peg(name, c, uv):
        return cyl(name, 0.022, 0.14, P(c, uv[0], uv[1], 0.07), (90, 0, 0), GRAPH, verts=6, bevel=0)

    cells = [(dx, dz) for dz in (0.74, 0.0, -0.74) for dx in (-0.8, 0.0, 0.8)]
    steel = '#9fb0b8'
    tools = 0

    # 1 wrench
    c = cells[0]
    wr = [(-0.05, -0.27), (0.05, -0.27), (0.09, -0.22), (0.09, -0.16), (0.04, -0.11), (0.04, 0.07), (0.125, 0.13),
          (0.125, 0.25), (0.06, 0.28), (0.06, 0.17), (-0.06, 0.17), (-0.06, 0.28), (-0.125, 0.25), (-0.125, 0.13),
          (-0.04, 0.07), (-0.04, -0.11), (-0.09, -0.16), (-0.09, -0.22)]
    wr = [rot2(x, y, -38) for x, y in wr]
    flat('tool_wrench', c, wr, 0.07, steel)
    hu, hv = rot2(0, -0.2, -38)
    disc('tool_wrench_eye', c, (hu, hv), 0.035, 0.012, PAPER_C, verts=10, off=0.066)
    peg('tool_wrench_peg', c, (hu, hv))
    tools += 1
    # 2 magnifier
    c = cells[1]
    bar('tool_magnifier_handle', c, (-0.03, -0.05), (-0.2, -0.24), 0.075, 0.07, WOOD_DARK, bevel=0.025)
    disc('tool_magnifier_lens', c, (0.06, 0.07), 0.15, 0.04, mat('#cfe5ee', 0.12, coat=0.6), verts=20)
    ring('tool_magnifier', c, (0.06, 0.07), 0.155, 0.036, GRAPH)
    bar('tool_magnifier_glint', c, (0.0, 0.1), (0.07, 0.17), 0.03, 0.012, WHITE, bevel=0.004, off=0.04)
    peg('tool_magnifier_peg', c, (0.06, 0.27))
    tools += 1
    # 3 pencil
    c = cells[2]
    k45 = math.sqrt(0.5)
    cyl('tool_pencil', 0.052, 0.36, P(c, 0.04, 0.04, 0.055), (0, 45, 0), AMBER, verts=6, bevel=0.006, seg=1)
    cyl('tool_pencil_tip', 0.006, 0.13, P(c, 0.04 - 0.245 * k45, 0.04 - 0.245 * k45, 0.055), (0, 45, 0), '#e6c79c',
        r2=0.052, verts=8, bevel=0)
    cyl('tool_pencil_lead', 0.003, 0.05, P(c, 0.04 - 0.29 * k45, 0.04 - 0.29 * k45, 0.055), (0, 45, 0), GRAPH,
        r2=0.022, verts=8, bevel=0)
    cyl('tool_pencil_ferrule', 0.056, 0.05, P(c, 0.04 + 0.2 * k45, 0.04 + 0.2 * k45, 0.055), (0, 45, 0), '#cdd5d6', verts=8, bevel=0.006, seg=1)
    cyl('tool_pencil_eraser', 0.052, 0.07, P(c, 0.04 + 0.26 * k45, 0.04 + 0.26 * k45, 0.055), (0, 45, 0), RED, verts=8, bevel=0.015, seg=2)
    peg('tool_pencil_peg', c, (-0.02, 0.17))
    peg('tool_pencil_peg2', c, (0.17, -0.02))
    tools += 1
    # 4 document
    c = cells[3]
    flat('tool_document', c, [(-0.18, -0.24), (0.18, -0.24), (0.18, 0.13), (0.07, 0.24), (-0.18, 0.24)], 0.05, BLUE_LT)
    flat('tool_document_fold', c, [(0.07, 0.13), (0.18, 0.13), (0.07, 0.24)], 0.062, BLUE, bevel=0.004)
    for k, (v, w) in enumerate(((0.07, 0.2), (-0.01, 0.26), (-0.09, 0.26), (-0.17, 0.16))):
        bar(f'tool_document_line_{k}', c, (-0.13, v), (-0.13 + w, v), 0.03, 0.012, GRAPH_LT, bevel=0.004, off=0.05)
    peg('tool_document_peg', c, (-0.05, 0.19))
    tools += 1
    # 5 terminal prompt
    c = cells[4]
    box('tool_terminal', (0.52, 0.08, 0.4), P(c, 0, 0, 0.04), m=GRAPH, bevel=0.035)
    bar('tool_terminal_bar', c, (-0.22, 0.14), (0.22, 0.14), 0.07, 0.012, GRAPH_LT, bevel=0.004, off=0.08)
    for k, col in enumerate((RED, AMBER, GREEN)):
        disc(f'tool_terminal_dot_{k}', c, (-0.19 + k * 0.06, 0.14), 0.018, 0.012, col, verts=8, off=0.088)
    term_green = mat(GREEN, 0.3, emit=1.2, emit_color='#2fc07c')
    bar('tool_terminal_chev_a', c, (-0.17, 0.05), (-0.07, -0.03), 0.04, 0.025, term_green, bevel=0.008, off=0.075)
    bar('tool_terminal_chev_b', c, (-0.07, -0.03), (-0.17, -0.11), 0.04, 0.025, term_green, bevel=0.008, off=0.075)
    bar('tool_terminal_cursor', c, (0.0, -0.11), (0.14, -0.11), 0.04, 0.025, term_green, bevel=0.008, off=0.075)
    peg('tool_terminal_peg', c, (0.0, 0.2))
    tools += 1
    # 6 branch fork
    c = cells[5]
    bar('tool_branch_trunk', c, (-0.08, -0.22), (-0.08, 0.22), 0.045, 0.045, OLIVE, bevel=0.015)
    bar('tool_branch_fork_a', c, (-0.08, -0.06), (0.14, 0.05), 0.045, 0.045, OLIVE, bevel=0.015)
    bar('tool_branch_fork_b', c, (0.14, 0.03), (0.14, 0.16), 0.045, 0.045, OLIVE, bevel=0.015)
    for k, (uv, col) in enumerate((((-0.08, -0.22), OLIVE), ((-0.08, 0.0), OLIVE), ((-0.08, 0.22), OLIVE),
                                   ((0.14, 0.16), GREEN))):
        disc(f'tool_branch_node_{k}', c, uv, 0.068, 0.07, col, verts=12)
        disc(f'tool_branch_core_{k}', c, uv, 0.03, 0.012, PAPER_C, verts=8, off=0.066)
    peg('tool_branch_peg', c, (-0.08, 0.11))
    tools += 1
    # 7 checklist
    c = cells[6]
    box('tool_checklist', (0.4, 0.045, 0.5), P(c, 0, 0, 0.0225), m=WOOD, bevel=0.02, seg=2)
    box('tool_checklist_sheet', (0.33, 0.02, 0.4), P(c, 0, -0.025, 0.05), m=WHITE, bevel=0.006, seg=1)
    box('tool_checklist_clip', (0.18, 0.05, 0.08), P(c, 0, 0.22, 0.055), m=GRAPH_LT, bevel=0.02, seg=1)
    for k, v in enumerate((0.09, -0.03, -0.15)):
        if k < 2:
            bar(f'tool_checklist_tick_a{k}', c, (-0.13, v + 0.0), (-0.1, v - 0.035), 0.028, 0.014, GREEN, bevel=0.004, off=0.058)
            bar(f'tool_checklist_tick_b{k}', c, (-0.1, v - 0.035), (-0.04, v + 0.04), 0.028, 0.014, GREEN, bevel=0.004, off=0.058)
        else:
            box(f'tool_checklist_box{k}', (0.06, 0.014, 0.06), P(c, -0.09, v, 0.065), m=GRAPH_LT, bevel=0.006, seg=1)
        bar(f'tool_checklist_line{k}', c, (0.0, v), (0.13, v), 0.03, 0.014, GRAPH_LT, bevel=0.004, off=0.058)
    peg('tool_checklist_peg', c, (0.0, 0.27))
    tools += 1
    # 8 scissors
    c = cells[7]
    bar('tool_scissors_blade_a', c, (0.09, -0.1), (-0.09, 0.27), 0.055, 0.035, steel)
    bar('tool_scissors_blade_b', c, (-0.09, -0.1), (0.09, 0.27), 0.055, 0.035, '#cdd5d6', off=0.03)
    ring('tool_scissors_loop_a', c, (0.13, -0.18), 0.075, 0.026, RED, d=0.03)
    ring('tool_scissors_loop_b', c, (-0.13, -0.18), 0.075, 0.026, RED, d=0.045)
    disc('tool_scissors_pivot', c, (0.0, 0.085), 0.03, 0.02, GRAPH, verts=8, off=0.062)
    peg('tool_scissors_peg', c, (0.13, -0.085))
    peg('tool_scissors_peg2', c, (-0.13, -0.085))
    tools += 1
    # 9 compass (dividers)
    c = cells[8]
    bar('tool_compass_leg_a', c, (0.0, 0.14), (-0.15, -0.22), 0.045, 0.04, steel)
    bar('tool_compass_leg_b', c, (0.0, 0.14), (0.15, -0.22), 0.045, 0.04, steel)
    bar('tool_compass_arc', c, (-0.09, -0.06), (0.09, -0.06), 0.03, 0.03, GRAPH_LT, off=0.02)
    bar('tool_compass_handle', c, (0.0, 0.14), (0.0, 0.28), 0.05, 0.05, GRAPH)
    disc('tool_compass_hinge', c, (0.0, 0.14), 0.065, 0.07, AMBER, verts=14)
    flat('tool_compass_needle', c, [(-0.022, 0.0), (0.022, 0.0), (-0.012, -0.07)], 0.03, GRAPH, uv=(-0.15, -0.21), bevel=0.004)
    flat('tool_compass_lead', c, [(-0.022, 0.0), (0.022, 0.0), (0.012, -0.07)], 0.03, RED, uv=(0.15, -0.21), bevel=0.004)
    peg('tool_compass_peg', c, (0.0, 0.03))
    tools += 1
    assert tools == 9
    print('[island] tools:', tools)

    # the back of the wall: bracing, a parts shelf and a spare cable coil (no tools here)
    bk = wy + 0.05
    box('wall_back', (bw - 0.08, 0.03, bh - 0.08), (wx, bk + 0.005, bzc), m='#d9cfb6', bevel=0.01, seg=1)
    for k, z in enumerate((bz0 + 0.45, bz0 + 1.85)):
        box(f'wall_batten_{k}', (bw, 0.07, 0.11), (wx, bk + 0.045, z), m=OLIVE_LT, bevel=0.02)
    box('wall_diagonal', (math.hypot(2.2, 1.4), 0.05, 0.1), (wx, bk + 0.04, bz0 + 1.15), (0, -math.degrees(math.atan2(1.4, 2.2)), 0),
        OLIVE_LT, bevel=0.02)
    box('wall_shelf', (0.9, 0.26, 0.05), (wx - 0.62, bk + 0.16, bz0 + 0.82), m=WOOD, bevel=0.015)
    for k, dx in enumerate((-0.36, 0.36)):
        box(f'wall_shelf_bracket_{k}', (0.05, 0.2, 0.16), (wx - 0.62 + dx, bk + 0.13, bz0 + 0.73), m=GRAPH_LT, bevel=0.015, seg=1)
    for k, (dx, col, hh) in enumerate(((-0.27, BLUE, 0.2), (0.0, AMBER, 0.16), (0.27, OLIVE, 0.22))):
        box(f'wall_bin_{k}', (0.22, 0.2, hh), (wx - 0.62 + dx, bk + 0.17, bz0 + 0.845 + hh / 2), m=col, bevel=0.03)
    cyl('wall_hook', 0.025, 0.16, (wx + 0.7, bk + 0.1, bz0 + 1.52), (90, 0, 0), GRAPH, verts=6, bevel=0)
    for k in range(2):
        torus(f'wall_coil_{k}', 0.2 - k * 0.02, 0.035, (wx + 0.7, bk + 0.085 + k * 0.05, bz0 + 1.33 - k * 0.01), (90, 0, 0), GRAPH_LT if k else GRAPH,
              seg=16, ring=5)
    # backs of the cabinet and the rack
    box('verdict_back', (vw - 0.5, 0.04, vh - 0.5), (vx, vy + vd / 2 + 0.008, 0.17 + vh / 2), m='#d8d0bc', bevel=0.015, seg=1)
    for k in range(3):
        box(f'verdict_back_slot_{k}', (0.5, 0.03, 0.04), (vx + 0.25, vy + vd / 2 + 0.02, 0.95 - k * 0.09), m=GRAPH_LT, bevel=0.008, seg=1)
    box('verdict_back_inlet', (0.2, 0.08, 0.16), (vx - 0.6, vy + vd / 2 + 0.03, 0.42), m=BLUE, bevel=0.025, seg=1)
    tube('verdict_cable', [(vx - 0.6, vy + vd / 2 + 0.05, 0.4), (vx - 0.6, vy + vd / 2 + 0.2, 0.2), (vx - 0.62, vy + vd / 2 + 0.34, 0.04),
                           (vx - 0.9, ty - 0.3, 0.04), (tcx + 0.3, ty - 0.08, 0.04), (tcx + 0.18, ty - 0.02, 0.08)], 0.03, GRAPH, res=3)
    box('rack_back', (rw - 0.16, 0.04, rh - 0.2), (rx, ry + rd / 2 + 0.008, 0.1 + rh / 2), m=GRAPH_LT, bevel=0.015, seg=1)
    for k in range(6):
        box(f'rack_back_slot_{k}', (rw - 0.34, 0.03, 0.05), (rx, ry + rd / 2 + 0.03, 0.5 + k * 0.17), m=BLUE, bevel=0.01, seg=1)

    # step stool in front of the wall
    stx, sty = 0.95, 3.05
    box('stool_step_low', (0.52, 0.3, 0.06), (stx, sty - 0.14, 0.24), (0, 0, -14), WOOD, bevel=0.02, seg=2)
    box('stool_step_top', (0.52, 0.3, 0.06), (stx + 0.035, sty + 0.14, 0.48), (0, 0, -14), WOOD, bevel=0.02, seg=2)
    for k, s in enumerate((-1, 1)):
        dx, dy = rot2(s * 0.22, 0.14, -14)
        box(f'stool_side_hi_{k}', (0.05, 0.28, 0.46), (stx + dx, sty + dy, 0.23), (0, 0, -14), OLIVE_LT, bevel=0.015, seg=1)
        dx, dy = rot2(s * 0.22, -0.14, -14)
        box(f'stool_side_lo_{k}', (0.05, 0.28, 0.22), (stx + dx, sty + dy, 0.11), (0, 0, -14), OLIVE_LT, bevel=0.015, seg=1)

    # ------------------------------------------------------------ ground detail
    drum('drum_a', -3.3, 3.2, OLIVE_LT, 40)
    drum('drum_b', -2.72, 3.45, BLUE, 140)
    drum('drum_c', -2.05, -3.58, AMBER, 200)
    cone('cone_a', 2.05, -3.3)
    cone('cone_b', 1.65, -3.72)
    clipboard('clipboard_pen', (qx - h - 0.02, qy - h - 0.2, 0.2), (62, 0, 20))
    clipboard('clipboard_wall', (wx - 1.05, wy - 0.42, 0.19), (60, 0, -8))
    tufts = [(-1.6, 0.5), (-0.9, -0.2), (0.6, 0.75), (0.4, -0.4), (3.3, -0.55), (2.6, -0.95), (-4.6, 0.3), (-4.3, -0.35),
             (2.0, 0.35), (0.7, 2.75), (-2.5, 3.2), (-3.0, 3.6), (2.3, -3.7), (1.9, -3.9), (-1.3, -3.75), (-3.6, -3.3),
             (4.7, 2.0), (4.5, 2.5), (-1.2, 2.8), (4.9, -1.0), (-4.9, 1.2), (3.6, 3.05)]
    for i, (x, y) in enumerate(tufts):
        grass_tuft(f'dry_tuft_{i}', (x, y, 0), h=0.2 + 0.07 * (i % 3), n=4, m=(DRY_DK, '#b9b074', OLIVE_LT)[i % 3], seed=i + 40)
    for i, (x, y, r) in enumerate([(-0.4, 0.9, 0.1), (0.9, 0.2, 0.08), (-1.9, -1.2, 0.09), (3.6, -3.3, 0.12), (-4.0, 3.3, 0.13),
                                   (1.6, 4.25, 0.1), (4.9, 0.1, 0.1), (-1.5, -3.9, 0.11), (-4.9, -0.4, 0.09)]):
        pebble(f'pebble_{i}', r, (x, y, r * 0.3), '#c9c3b3' if i % 2 else '#b5b0a2', i * 47)
    for i, (a, r) in enumerate([(0.55, 0.36), (2.5, 0.44), (3.6, 0.3), (5.05, 0.4)]):
        d = radius_at(a) * 0.965
        rock(f'rim_rock_{i}', r, (d * 1.08 * math.cos(a), d * 0.94 * math.sin(a), -0.02), '#a9aaa0' if i % 2 else '#b9b8ab',
             seed=i + 21, squash=0.62)

    hotspot(1, (cx, cy, 2.55))
    hotspot(2, (vx - 0.2, vy - 0.2, 1.75))
    hotspot(3, (mxc + 0.45, ly, 1.6))
    hotspot(4, (wx, wy - 0.1, 3.3))
    finish('developer-agent', mode, cam_loc=(-9.4, -14.1, 9.3), cam_target=(-0.05, -0.25, 0.45), lens=50)
