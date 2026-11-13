"""Home harbor: where the voyage starts and ends. Lighthouse, pier, boathouse, mailbox."""
import math
from kit import *


def build(mode='preview'):
    reset()
    setup_world()
    base, radius_at = island_base(R=4.6, seed=7, top='#a9d68a', lip='#8fc77a', soil='#d9b382',
                                  soil2='#b98d60', rock_c='#9aa3a6')
    # sand apron toward the pier
    lathe('beach', [(0.0, 0.012), (1.9, 0.012), (2.25, -0.02), (2.3, -0.08)], (0.6, -2.6, 0), m=SAND, verts=48)

    # --- rocky rise and lighthouse
    for i, (x, y, r) in enumerate([(-1.9, 1.5, 1.25), (-2.7, 0.9, 0.8), (-1.2, 2.3, 0.85), (-2.6, 2.1, 0.6)]):
        rock(f'rise_{i}', r, (x, y, r * 0.28), '#aab1b3' if i % 2 else '#9aa3a6', seed=i + 3, squash=0.62)
    lx, ly, lz = -1.9, 1.55, 0.85
    lathe('lh_plinth', [(0, 0), (0.92, 0), (0.92, 0.22), (0.8, 0.3), (0, 0.3)], (lx, ly, lz), m='#d8d2c4')
    lathe('lh_tower', [(0, 0), (0.7, 0), (0.52, 2.9), (0, 2.9)], (lx, ly, lz + 0.3), m=WHITE, verts=48)
    for k, z in enumerate((0.55, 1.5, 2.4)):
        r0 = 0.7 - 0.18 * (z - 0.21) / 2.9
        r1 = 0.7 - 0.18 * (z + 0.21) / 2.9
        lathe(f'lh_band_{k}', [(r0 + 0.012, z - 0.21), (r1 + 0.012, z + 0.21)], (lx, ly, lz + 0.3), m=CORAL, verts=48)
    cyl('lh_gallery', 0.78, 0.12, (lx, ly, lz + 3.26), m='#3b4a46', verts=40, bevel=0.03)
    torus('lh_rail', 0.74, 0.022, (lx, ly, lz + 3.56), m='#3b4a46')
    for i in range(10):
        a = TAU * i / 10
        cyl(f'lh_post_{i}', 0.018, 0.26, (lx + 0.74 * math.cos(a), ly + 0.74 * math.sin(a), lz + 3.44), m='#3b4a46', verts=8, bevel=0)
    lamp = cyl('lh_lamp', 0.36, 0.56, (lx, ly, lz + 3.62), m=mat('#fff3c4', 0.3, emit=5.0, emit_color='#ffd98a'), verts=32, bevel=0.03)
    animate(lamp, 'pulse', speed=0.9)
    for i in range(6):
        a = TAU * i / 6
        cyl(f'lh_mullion_{i}', 0.022, 0.6, (lx + 0.38 * math.cos(a), ly + 0.38 * math.sin(a), lz + 3.62), m='#3b4a46', verts=8, bevel=0)
    lathe('lh_roof', [(0.52, 0), (0.5, 0.06), (0.08, 0.5), (0, 0.52)], (lx, ly, lz + 3.92), m=CORAL, verts=40)
    sphere('lh_finial', 0.07, (lx, ly, lz + 4.5), m=SUNSHINE, seg=14)
    box('lh_door', (0.34, 0.08, 0.62), (lx + 0.02, ly - 0.69, lz + 0.62), (4, 0, 0), '#4f6a60', bevel=0.05)
    sphere('lh_window', 0.12, (lx + 0.02, ly - 0.6, lz + 1.9), (1, 0.4, 1.3), '#4f6a60', 16)
    # steps up the rise
    for i in range(4):
        box(f'step_{i}', (0.7, 0.34, 0.14), (lx + 0.35 + i * 0.18, ly - 1.1 - i * 0.3, 0.62 - i * 0.16), (0, 0, -22), '#cfc8b8', bevel=0.04)

    # --- boathouse
    hx, hy = 2.1, 1.0
    box('house_floor', (2.3, 1.9, 0.14), (hx, hy, 0.07), m='#d6cab2', bevel=0.04)
    box('house_body', (2.0, 1.6, 1.25), (hx, hy, 0.76), m='#f3ead7', bevel=0.07)
    roof = prism('house_roof', [(-1.2, 0), (1.2, 0), (0, 0.78)], 1.95, (hx, hy + 0.975, 1.36), (90, 0, 0), '#3f7f69', bevel=0.06)
    box('house_door', (0.5, 0.07, 0.86), (hx - 0.45, hy - 0.81, 0.57), m=WOOD, bevel=0.05)
    sphere('house_knob', 0.035, (hx - 0.3, hy - 0.86, 0.56), m=SUNSHINE, seg=10)
    box('house_window', (0.56, 0.07, 0.46), (hx + 0.45, hy - 0.81, 0.86), m=mat('#bfe4ea', 0.25, emit=0.6, emit_color='#ffe7b0'), bevel=0.04)
    box('house_sill', (0.68, 0.14, 0.06), (hx + 0.45, hy - 0.84, 0.6), m=WOOD_DARK, bevel=0.02)
    box('house_chimney', (0.26, 0.26, 0.7), (hx + 0.6, hy + 0.1, 1.85), m='#d9836a', bevel=0.04)
    for i, dx in enumerate((-0.14, 0.0, 0.14)):
        flower(f'sill_flower_{i}', (hx + 0.45 + dx, hy - 0.86, 0.6), 0.16, CORAL if i != 1 else SUNSHINE)
    # flag
    cyl('flag_pole', 0.03, 1.9, (hx + 1.25, hy - 0.6, 0.95), m='#3b4a46', verts=10, bevel=0)
    sphere('flag_ball', 0.055, (hx + 1.25, hy - 0.6, 1.93), m=SUNSHINE, seg=10)
    flag = prism('flag', [(0, 0), (0.78, 0.2), (0, 0.42)], 0.03, (hx + 1.27, hy - 0.585, 1.42), (90, 0, 0), CORAL, bevel=0.01)
    set_origin(flag, (hx + 1.25, hy - 0.6, 1.63))
    animate(flag, 'sway', amp=9, speed=1.6, axis='z')

    # --- pier
    px = 0.75
    for i in range(9):
        y = -2.4 - i * 0.44
        box(f'plank_{i}', (1.25, 0.38, 0.09), (px, y, 0.02 - 0.0 * i), (0, 0, (i % 3 - 1) * 1.2), WOOD if i % 2 else '#d39c66', bevel=0.025)
    for i, y in enumerate((-2.6, -4.0, -5.7)):
        for s in (-1, 1):
            cyl(f'pile_{i}_{s}', 0.1, 1.9, (px + s * 0.6, y, -0.7), m=WOOD_DARK, verts=14, bevel=0.02)
            cyl(f'pile_cap_{i}_{s}', 0.125, 0.07, (px + s * 0.6, y, 0.28), m='#e9dcc3', verts=14, bevel=0.02)
    tube('pier_rope', [(px - 0.6, -2.6, 0.22), (px - 0.62, -3.3, 0.02), (px - 0.6, -4.0, 0.22), (px - 0.62, -4.85, 0.0), (px - 0.6, -5.7, 0.22)], 0.022, '#e9dcc3')
    # lantern at the pier head
    cyl('lantern_post', 0.035, 1.1, (px + 0.6, -5.7, 0.86), m='#3b4a46', verts=10, bevel=0)
    lantern = sphere('lantern', 0.13, (px + 0.6, -5.7, 1.48), (1, 1, 1.15), mat('#ffe9a8', 0.3, emit=6.0, emit_color='#ffcf70'), 16)
    animate(lantern, 'pulse', speed=1.4)
    lathe('lantern_cap', [(0.16, 0), (0.02, 0.12), (0, 0.12)], (px + 0.6, -5.7, 1.6), m='#3b4a46', verts=16)

    # --- mailbox (contact) and crates by the pier
    mx, my = -0.55, -2.25
    cyl('mail_post', 0.05, 0.8, (mx, my, 0.4), m=WOOD_DARK, verts=10, bevel=0.01)
    mb = box('mail_box', (0.36, 0.56, 0.3), (mx, my, 0.9), m='#3f7f69', bevel=0.11, seg=5)
    box('mail_slot', (0.2, 0.03, 0.035), (mx, my - 0.285, 0.94), m='#1f3a31', bevel=0.01)
    mflag = box('mail_flag', (0.03, 0.16, 0.1), (mx + 0.2, my - 0.05, 1.02), m=CORAL, bevel=0.012)
    letter = box('mail_letter', (0.24, 0.02, 0.16), (mx, my - 0.3, 1.02), (18, 0, 6), PAPER, bevel=0.006)
    animate(letter, 'bob', amp=0.03, speed=1.2)
    box('crate_a', (0.5, 0.5, 0.5), (2.1, -1.6, 0.25), (0, 0, 14), '#d7a66f', bevel=0.04)
    box('crate_b', (0.42, 0.42, 0.42), (2.62, -1.42, 0.21), (0, 0, -9), '#c98f5a', bevel=0.04)
    box('crate_c', (0.4, 0.4, 0.4), (2.2, -1.55, 0.7), (0, 0, 31), '#e2b47e', bevel=0.04)
    lathe('barrel', [(0, 0), (0.2, 0), (0.25, 0.25), (0.2, 0.5), (0, 0.5)], (1.55, -2.0, 0.0), m=WOOD_DARK, verts=20)
    torus('barrel_hoop', 0.245, 0.018, (1.55, -2.0, 0.25), m='#3b4a46', seg=20, ring=6)
    # coiled rope
    for i in range(3):
        torus(f'coil_{i}', 0.2 - i * 0.012, 0.035, (-0.1, -3.0, 0.045 + i * 0.062), m='#e9dcc3', seg=24, ring=8)

    # --- path stones from pier to house and lighthouse
    for i, (x, y) in enumerate([(0.7, -1.9), (0.9, -1.3), (1.2, -0.75), (1.5, -0.25), (0.3, -1.2), (-0.3, -0.7), (-0.8, -0.1), (-1.15, 0.45)]):
        cyl(f'stone_{i}', 0.2 + 0.03 * (i % 3), 0.05, (x, y, 0.02), (0, 0, i * 37), '#e6dfcf', verts=9, bevel=0.02)

    # --- vegetation
    tree('tree_a', (3.15, 2.5, 0), 1.9, 0.8, seed=2)
    tree('tree_b', (0.2, 3.3, 0), 1.6, 0.66, leaf='#6bb878', leaf2='#4b9c69', seed=5)
    pine('pine_a', (-3.5, -0.4, 0), 1.7, 0.5)
    pine('pine_b', (-3.0, -1.2, 0), 1.25, 0.4)
    for i, (x, y, r) in enumerate([(3.4, 0.2, 0.36), (2.9, -0.5, 0.26), (-0.6, 2.9, 0.3), (-3.6, 0.9, 0.3), (1.1, 2.6, 0.28), (-1.9, -1.9, 0.3)]):
        bush(f'bush_{i}', (x, y, 0), r, LEAF if i % 2 else '#74c07a', seed=i)
    for i, (x, y) in enumerate([(3.0, -1.0), (0.2, 0.9), (-2.4, -0.6), (0.9, 3.6), (-1.0, -1.5), (2.6, 3.3), (-3.0, -2.0), (3.7, 1.3)]):
        grass_tuft(f'tuft_{i}', (x, y, 0), seed=i)
    for i, (x, y) in enumerate([(0.0, 0.2), (-0.3, 1.5), (2.2, -0.6), (-2.2, -1.3), (1.0, 3.0), (3.4, -0.2)]):
        flower(f'flower_{i}', (x, y, 0), 0.26, (CORAL, SUNSHINE, WHITE)[i % 3])
    for i, (x, y, r) in enumerate([(4.0, -1.6, 0.34), (-3.9, -1.9, 0.42), (3.3, -2.6, 0.24), (-1.9, -3.4, 0.3)]):
        rock(f'shore_rock_{i}', r, (x, y, -0.05), ROCK if i % 2 else '#b3b9ba', seed=i + 11)

    # --- two mooring buoys in the water (separate, they bob)
    for i, (x, y) in enumerate([(3.4, -5.2), (-1.6, -5.6)]):
        b = join([lathe(f'buoy_body_{i}', [(0, -0.22), (0.2, -0.16), (0.26, 0.0), (0.2, 0.2), (0.07, 0.3), (0.07, 0.52), (0, 0.52)], (x, y, WATER_Z + 0.06), m=BUOY, verts=20),
                  torus(f'buoy_band_{i}', 0.262, 0.02, (x, y, WATER_Z + 0.06), m=WHITE, seg=20, ring=6),
                  sphere(f'buoy_light_{i}', 0.055, (x, y, WATER_Z + 0.62), m=mat('#fff3c4', 0.3, emit=4, emit_color='#ffd98a'), seg=10)], f'buoy_{i}')
        set_origin(b, (x, y, WATER_Z))
        animate(b, 'bob', amp=0.05, speed=0.9 + 0.2 * i, tilt=5)


    # --- chart table: the voyage in miniature (eight islands on a coral course)
    tx, ty = 0.15, 0.55
    box('chart_table_top', (1.5, 1.0, 0.08), (tx, ty, 0.62), (0, 0, -14), WOOD, bevel=0.03)
    for i, (dx, dy) in enumerate(((-0.6, -0.36), (0.6, -0.36), (-0.6, 0.36), (0.6, 0.36))):
        a = math.radians(-14)
        cyl(f'chart_leg_{i}', 0.045, 0.6, (tx + dx * math.cos(a) - dy * math.sin(a), ty + dx * math.sin(a) + dy * math.cos(a), 0.3), m=WOOD_DARK, verts=10, bevel=0.01)
    box('chart_paper', (1.2, 0.78, 0.016), (tx, ty, 0.672), (0, 0, -14), PAPER, bevel=0.004)
    stops = [(-0.48, -0.2), (-0.34, 0.14), (-0.2, -0.12), (-0.06, 0.2), (0.08, -0.16), (0.22, 0.12), (0.36, -0.14), (0.5, 0.16)]
    a = math.radians(-14)
    world = [(tx + x * math.cos(a) - y * math.sin(a), ty + x * math.sin(a) + y * math.cos(a)) for x, y in stops]
    for i, (x, y) in enumerate(world):
        cyl(f'chart_isle_{i}', 0.05, 0.03, (x, y, 0.695), m=('#6fb26a', '#f7c65b', '#6366f1', '#59b7b0', '#2f5a55', '#c9744f', '#116d55', '#575540')[i], verts=12, bevel=0.008)
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(world, world[1:])):
        for k in (0.3, 0.5, 0.7):
            box(f'chart_dash_{i}_{int(k * 10)}', (0.04, 0.014, 0.008), (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, 0.686), (0, 0, math.degrees(math.atan2(y1 - y0, x1 - x0))), CORAL, bevel=0)
    lathe('chart_compass', [(0, 0), (0.1, 0), (0.1, 0.035), (0, 0.035)], (tx + 0.5, ty + 0.28, 0.66), m=mat('#e5b85c', 0.35, metallic=0.6), verts=20)
    box('chart_needle', (0.13, 0.018, 0.01), (tx + 0.5, ty + 0.28, 0.705), (0, 0, 35), CORAL, bevel=0)
    for i in range(2):
        cyl(f'chart_roll_{i}', 0.05, 0.62, (tx - 0.52 + i * 0.09, ty + 0.34 - i * 0.03, 0.72 + i * 0.01), (0, 90, 62 + i * 9), PAPER, verts=12, bevel=0.01)

    # --- telescope on the rise, trained on the open sea
    sx, sy, sz = -0.75, 1.55, 0.0
    for i in range(3):
        b = TAU * i / 3 + 0.4
        tube(f'scope_leg_{i}', [(sx, sy, 1.0), (sx + 0.3 * math.cos(b), sy + 0.3 * math.sin(b), 0.0)], 0.022, WOOD_DARK, smooth_curve=False)
    scope = join([cyl('scope_tube', 0.07, 0.8, (sx, sy, 1.08), (0, 72, -38), mat('#e5b85c', 0.35, metallic=0.6), r2=0.1, verts=16, bevel=0.01),
                  cyl('scope_eye', 0.05, 0.22, (sx - 0.36, sy + 0.285, 0.94), (0, 72, -38), '#3b4a46', verts=12, bevel=0.01)], 'telescope')
    set_origin(scope, (sx, sy, 1.02))
    animate(scope, 'sway', amp=10, speed=0.35, axis='z')

    # --- signpost by the pier, three arrows out to sea
    gx, gy = 1.85, -2.75
    cyl('signpost', 0.05, 1.55, (gx, gy, 0.77), m=WOOD_DARK, verts=10, bevel=0.01)
    for i, (rz, col) in enumerate(((-60, CORAL), (-20, '#f7c65b'), (-95, '#7fd0c6'))):
        prism(f'sign_arrow_{i}', [(0, -0.09), (0.5, -0.09), (0.64, 0), (0.5, 0.09), (0, 0.09)], 0.05, (gx, gy + 0.025, 1.38 - i * 0.26), (90, 0, rz), col, bevel=0.012)

    # --- a rowboat tied up beside the pier
    rx, ry = -0.75, -4.35
    hull = [(-0.34, -0.7), (0.34, -0.7), (0.4, 0.1), (0.22, 0.62), (0, 0.84), (-0.22, 0.62), (-0.4, 0.1)]
    inner = [(x * 0.78, y * 0.86 + 0.02) for x, y in hull]
    row = join([prism('row_hull', hull, 0.4, (rx, ry, WATER_Z - 0.1), m='#fbf8f0', bevel=0.05),
                prism('row_inner', inner, 0.06, (rx, ry, WATER_Z + 0.26), m='#c98f5a', bevel=0.01),
                box('row_bench_a', (0.62, 0.14, 0.05), (rx, ry - 0.2, WATER_Z + 0.31), m=WOOD, bevel=0.015),
                box('row_bench_b', (0.5, 0.14, 0.05), (rx, ry + 0.3, WATER_Z + 0.31), m=WOOD, bevel=0.015),
                box('row_stripe', (0.82, 1.52, 0.05), (rx, ry + 0.02, WATER_Z + 0.17), m=CORAL, bevel=0.02),
                cyl('row_oar', 0.022, 1.3, (rx + 0.2, ry + 0.05, WATER_Z + 0.37), (90, 0, 12), WOOD_DARK, verts=8, bevel=0)], 'rowboat')
    set_origin(row, (rx, ry, WATER_Z))
    animate(row, 'bob', amp=0.04, speed=1.0, tilt=3)
    tube('row_line', [(rx + 0.3, ry + 0.7, WATER_Z + 0.2), (rx + 0.6, ry + 0.6, WATER_Z + 0.05), (px - 0.6, -4.0, 0.2)], 0.016, '#e9dcc3')

    # --- lighthouse details: windows, door arch and a slow beam
    for k, (z, ang) in enumerate(((1.2, -70), (2.2, -110))):
        r = 0.7 - 0.18 * z / 2.9
        sphere(f'lh_window_{k}', 0.1, (lx + r * math.cos(math.radians(ang)), ly + r * math.sin(math.radians(ang)), lz + 0.3 + z), (1, 1, 1.35), '#4f6a60', 14)
    torus('lh_door_arch', 0.2, 0.035, (lx + 0.02, ly - 0.69, lz + 0.92), (86, 0, 0), '#d8d2c4', seg=20, ring=8)
    beam = lathe('lh_beam', [(0.05, 0), (0.55, 4.0)], (lx, ly, lz + 3.62), (0, 90, -50), mat('#fff4c9', 0.5, emit=1.2, emit_color='#ffe9a8', alpha=0.09), verts=20)
    set_origin(beam, (lx, ly, lz + 3.62))
    animate(beam, 'spin', speed=0.35, axis='z')

    # --- string of lanterns from the boathouse to the flagpole
    line = [(hx - 0.95, hy - 0.82, 1.42), (hx + 0.2, hy - 1.0, 1.28), (hx + 1.25, hy - 0.6, 1.72)]
    tube('lantern_string', line, 0.012, '#3b4a46')
    for i, t in enumerate((0.12, 0.3, 0.5, 0.7, 0.88)):
        x = (1 - t) ** 2 * line[0][0] + 2 * t * (1 - t) * line[1][0] + t * t * line[2][0]
        y = (1 - t) ** 2 * line[0][1] + 2 * t * (1 - t) * line[1][1] + t * t * line[2][1]
        z = (1 - t) ** 2 * line[0][2] + 2 * t * (1 - t) * line[1][2] + t * t * line[2][2]
        sphere(f'string_lamp_{i}', 0.055, (x, y, z - 0.08), (1, 1, 1.2), mat(('#ffd98a', '#ff9d7a', '#a8e6d8')[i % 3], 0.3, emit=3.5), 10)

    # --- gulls, a bench, an anchor and a fence
    def gull(name, loc, rz=0):
        x, y, z = loc
        return [sphere(name + '_body', 0.11, (x, y, z + 0.1), (1.5, 1, 1), WHITE, 12, (0, 0, rz)),
                sphere(name + '_head', 0.07, (x + 0.14 * math.cos(math.radians(rz)), y + 0.14 * math.sin(math.radians(rz)), z + 0.21), m=WHITE, seg=10),
                cyl(name + '_beak', 0.022, 0.09, (x + 0.24 * math.cos(math.radians(rz)), y + 0.24 * math.sin(math.radians(rz)), z + 0.2), (0, 90, rz), SUNSHINE, r2=0.003, verts=8, bevel=0),
                sphere(name + '_wing', 0.09, (x - 0.03 * math.cos(math.radians(rz)), y - 0.03 * math.sin(math.radians(rz)), z + 0.12), (1.5, 1.08, 0.7), '#c9d2d6', 10, (0, 0, rz))]
    gull('gull_a', (px - 0.6, -5.7, 0.31), -30)
    gull('gull_b', (hx - 0.5, hy + 0.2, 2.1), 200)
    bx, by = -2.3, -2.3
    box('bench_seat', (0.95, 0.3, 0.06), (bx, by, 0.34), (0, 0, 28), WOOD, bevel=0.02)
    box('bench_back', (0.95, 0.05, 0.32), (bx - 0.07, by + 0.13, 0.56), (-8, 0, 28), WOOD, bevel=0.02)
    for s_ in (-1, 1):
        box(f'bench_leg_{s_}', (0.07, 0.26, 0.32), (bx + s_ * 0.36 * math.cos(math.radians(28)), by + s_ * 0.36 * math.sin(math.radians(28)), 0.16), (0, 0, 28), '#3b4a46', bevel=0.015)
    ax, ay = hx - 1.12, hy - 0.5
    cyl('anchor_shank', 0.035, 0.75, (ax, ay, 0.42), (0, 14, 0), '#3b4a46', verts=10, bevel=0.01)
    torus('anchor_ring', 0.08, 0.022, (ax + 0.09, ay, 0.84), (90, 0, 0), '#3b4a46', seg=16, ring=6)
    tube('anchor_arms', [(ax - 0.36, ay, 0.3), (ax - 0.22, ay, 0.1), (ax - 0.08, ay, 0.05), (ax + 0.12, ay, 0.14), (ax + 0.22, ay, 0.36)], 0.035, '#3b4a46')
    box('anchor_stock', (0.4, 0.05, 0.05), (ax + 0.06, ay, 0.7), (0, 14, 0), '#3b4a46', bevel=0.015)
    for i in range(6):
        fa = math.radians(118 + i * 13)
        fr = radius_at(fa) * 0.86
        cyl(f'fence_post_{i}', 0.04, 0.42, (fr * math.cos(fa), fr * math.sin(fa), 0.21), m='#f3ead7', verts=8, bevel=0.01)
        if i:
            pa = math.radians(118 + (i - 1) * 13)
            pr = radius_at(pa) * 0.86
            tube(f'fence_rail_{i}', [(pr * math.cos(pa), pr * math.sin(pa), 0.32), (fr * math.cos(fa), fr * math.sin(fa), 0.32)], 0.02, '#f3ead7', smooth_curve=False)
    for i, (x, y) in enumerate([(1.3, -1.0), (-1.6, -2.6), (3.6, 0.9), (-3.3, 2.6), (2.0, 3.6), (-0.9, 3.5), (0.9, 1.9), (-2.9, -2.9)]):
        flower(f'flower_x_{i}', (x, y, 0), 0.24, (SUNSHINE, CORAL, '#b9a7d6', WHITE)[i % 4])

    hotspot(1, (lx, ly, lz + 3.7))
    hotspot(2, (hx, hy - 0.9, 1.3))
    hotspot(3, (mx, my, 1.25))
    hotspot(4, (px, -5.0, 0.4))
    finish('harbor', mode, cam_loc=(-9.0, -14.5, 8.0), cam_target=(0.1, -0.6, 1.0), lens=50)
