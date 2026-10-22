# Rebuilds the L_Apartment greybox from the floor plan.
# Runs inside unreal-mcp's ProgrammaticToolset.execute_tool_script (sandboxed: only execute_tool + json/math).
# Deletes every actor in the Blockout and Lights outliner folders, builds them again, and moves the Loop actors
# (LoopManager, PlayerStart, LoopDoor, LoopExit) to match. Returns any static blocker found on the route.
import json
import math

H = 270            # wall height, cm
K = 1.5            # cm per pixel of the user's plan
OX, OY = 197, 205  # plan pixel that maps to world (0,0)
DOOR = 100         # clear width of every doorway
CORR_EXTRA = 200   # upper corridor lengthened: everything below plan y=540 moves down
ROOM_EXTRA = 200   # living / hallway / kitchen deeper: their top wall (plan y=205) moves up
VEST_EXTRA = 200   # vestibule to the front door longer: plan y=73 moves up more
BATH_EXTRA = 100   # bathroom wider: lower-block points right of plan x=380 move right
BED_EXTRA = 200    # bedroom and lower corridor wider: lower-block points from plan x=695 move right again
BED_DOOR_FROM_END = 90  # bedroom door center, cm from the right end of the lower corridor

S = 'editor_toolset.toolsets.scene.SceneTools.'
A = 'editor_toolset.toolsets.actor.ActorTools.'
O = 'editor_toolset.toolsets.object.ObjectTools.'
LVL = '/Game/Maps/L_Apartment.L_Apartment:PersistentLevel.'
ROT0 = {'pitch': 0, 'yaw': 0, 'roll': 0}
MANAGER = LVL + 'LoopManager_UAID_50EBF677B6286D0D03_1474282790'
PLAYER_START = LVL + 'PlayerStart_UAID_50EBF677B6286D0D03_1473898789'
FRONT_DOOR = LVL + 'LoopDoor_UAID_50EBF677B6286E0D03_1713365970'
LOOP_EXIT = LVL + 'LoopExit_UAID_50EBF677B6286D0D03_1474577791'
MATS = '/Game/Endless/Materials/'  # finishes from materials_apartment.py (M_WorldAligned over Fab textures, not in git)


def mat(name):
    return MATS + name + '.' + name


PARQUET, PLASTER = mat('MI_Parquet'), mat('MI_Plaster')
# Room -> (walls, floor laid over the old parquet or None, baseboard or None). GDD 4.1: renovated rooms vs old ones.
FINISH = {
    'living': ('MI_Walls_Living', 'MI_Floor_Living', 'MI_Baseboard_New'),
    'bedroom': ('MI_Walls_Bedroom', 'MI_Floor_Bedroom', 'MI_Baseboard_New'),
    'hall': ('MI_Walls_Hall', 'MI_Floor_Tiles', 'MI_Baseboard_New'),
    'kitchen': ('MI_Walls_Kitchen', 'MI_Floor_Tiles', 'MI_Baseboard_New'),
    'bath': ('MI_Walls_Bath', 'MI_Floor_Bath', None),
    'corr1': ('MI_Walls_Corridor', None, 'MI_Baseboard_Old'),
    'corr2': ('MI_Walls_Corridor', None, 'MI_Baseboard_Old'),
    'nook': ('MI_Wallpaper', None, 'MI_Baseboard_Old'),
    'landing': ('MI_Plaster', 'MI_Plaster', None),
    'outside': ('MI_Plaster', None, None),
}
WALLS = []  # (orient, line, start, end, name) of every wall, for the loose-end check
FREE_ENDS = {'W_Nook start'}  # wall ends that stand free on purpose


def X(px):
    return (px - OX) * K


def XL(px):
    # X for the lower block (lower corridor, bathroom, bedroom)
    x = X(px)
    if px >= 380:
        x += BATH_EXTRA
    if px >= 695:
        x += BED_EXTRA
    return x


def Y(py):
    y = (py - OY) * K
    if py >= 540:
        y += CORR_EXTRA
    if py <= 205:
        y -= ROOM_EXTRA
    if py <= 73:
        y -= VEST_EXTRA
    return y


def rooms():
    # Room rectangles on wall center lines; the first match wins (the nook sits inside the living room)
    fy, top = Y(73), Y(205)
    return [
        ('nook', X(197), X(302), Y(287), Y(413)),
        ('living', X(197), X(547), top, Y(413)),
        ('hall', X(547), X(695), top, Y(413)),
        ('hall', X(543), X(642), fy, top),  # vestibule
        ('kitchen', X(695), X(890), top, Y(413)),
        ('corr1', X(385), X(472), Y(413), Y(540)),
        ('corr2', X(197), XL(695), Y(540), Y(628)),
        ('bath', X(197), XL(380), Y(628), Y(888)),
        ('bedroom', XL(380), XL(787), Y(628), Y(888)),
        ('landing', 409, 779, fy - 240, fy),
    ]


ROOMS = rooms()


def room_at(x, y):
    for name, x0, x1, y0, y1 in ROOMS:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return name
    return 'outside'


def in_folder(f):
    # get_actors_in_folder fails on a missing folder, and that error can't be caught in the sandbox
    if f not in execute_tool(S + 'get_folders', '{}')['returnValue']:
        return []
    return execute_tool(S + 'get_actors_in_folder', json.dumps({'folder_path': f, 'recursive': True}))['returnValue']


def props(a, values):
    if not execute_tool(O + 'set_properties', json.dumps({'instance': a, 'values': json.dumps(values)}))['returnValue']:
        raise RuntimeError('set_properties failed on %s: %s' % (a['refPath'], values))


def folder(a, f):
    execute_tool(S + 'set_actor_folder', json.dumps({'actor': a, 'folder_path': f}))


def place(path, x, y, z, yaw):
    execute_tool(A + 'set_actor_transform', json.dumps({'actor': {'refPath': path}, 'xform': {
        'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': 0, 'yaw': yaw, 'roll': 0}}, 'worldspace': True}))


def box(name, x0, x1, y0, y1, z0=0, z1=H, f='Blockout', mat=None):
    a = execute_tool(S + 'add_to_scene_from_asset', json.dumps({
        'asset_path': '/Engine/BasicShapes/Cube', 'name': name,
        'xform': {'location': {'x': (x0 + x1) / 2, 'y': (y0 + y1) / 2, 'z': (z0 + z1) / 2}, 'rotation': ROT0,
                  'scale': {'x': (x1 - x0) / 100, 'y': (y1 - y0) / 100, 'z': (z1 - z0) / 100}}}))['returnValue']
    folder(a, f)
    props(a, {'bIsSpatiallyLoaded': False})  # small level: keep everything loaded in the editor
    if mat:
        props({'refPath': a['refPath'] + '.StaticMeshComponent0'}, {'OverrideMaterials': [mat]})
    return a


def wall_piece(name, orient, line, a, b, t, z0=0, z1=H):
    # One straight piece of wall from a to b along its line. Each side gets the finish of the room it faces:
    # the piece is split lengthwise into two halves, and each half into runs facing one room.
    # Floor-level runs get a baseboard. 'v' = wall along Y at x = line, 'h' = along X at y = line.
    for side in (-1, 1):
        face = line + side * t / 2
        runs, pos = [], a
        while pos < b:
            nxt = min(pos + 5, b)
            mid = (pos + nxt) / 2
            room = room_at(face + side * 5, mid) if orient == 'v' else room_at(mid, face + side * 5)
            if runs and runs[-1][0] == room:
                runs[-1][2] = nxt
            else:
                runs.append([room, pos, nxt])
            pos = nxt
        lo, hi = sorted((line, face))
        b0, b1 = sorted((face, face + side * 1.5))
        for i, (room, s0, s1) in enumerate(runs):
            walls, _, baseboard = FINISH[room]
            n = '%s_%s%d' % (name, 'A' if side < 0 else 'B', i)
            rect = (lo, hi, s0, s1) if orient == 'v' else (s0, s1, lo, hi)
            box(n, *rect, z0, z1, mat=mat(walls))
            if baseboard and z0 == 0:
                rect = (b0, b1, s0, s1) if orient == 'v' else (s0, s1, b0, b1)
                box(n + '_Base', *rect, 0, 8, f='Blockout/Baseboards', mat=mat(baseboard))


def spans(a0, a1, gaps):
    # Solid pieces between a0..a1 with DOOR-wide holes centered at gaps; ends are NOT pushed into the holes.
    cuts, pos = [], a0
    for c in sorted(gaps):
        cuts.append((pos, c - DOOR / 2))
        pos = c + DOOR / 2
    cuts.append((pos, a1))
    return cuts


def vwall(name, px, py0, py1, gaps=(), t=20, xf=X):
    x = xf(px)
    WALLS.append(('v', x, Y(py0) - t / 2, Y(py1) + t / 2, name))
    for i, (a, b) in enumerate(spans(Y(py0) - t / 2, Y(py1) + t / 2, gaps)):
        wall_piece('%s_%d' % (name, i), 'v', x, a, b, t)
    for c in gaps:
        wall_piece(name + '_Lintel', 'v', x, c - DOOR / 2, c + DOOR / 2, t, 210, H)


def hwall(name, py, px0, px1, gaps=(), t=20, xf=X):
    y = Y(py)
    WALLS.append(('h', y, xf(px0) - t / 2, xf(px1) + t / 2, name))
    for i, (a, b) in enumerate(spans(xf(px0) - t / 2, xf(px1) + t / 2, gaps)):
        wall_piece('%s_%d' % (name, i), 'h', y, a, b, t)
    for c in gaps:
        wall_piece(name + '_Lintel', 'h', y, c - DOOR / 2, c + DOOR / 2, t, 210, H)


def blockers(x0, x1, y0, y1):
    r = execute_tool(S + 'find_actors', json.dumps({'name': '', 'tag': '', 'collision_channels': ['ObjectTypeQuery1'],
        'bounds': {'min': {'x': x0, 'y': y0, 'z': 10}, 'max': {'x': x1, 'y': y1, 'z': 200}, 'isValid': True}}))['returnValue']
    return [a['refPath'].split('.')[-1] for a in r]


def loose_ends():
    # Each wall end must overlap some other wall: a lone end means a hole in the apartment
    bad = []
    for orient, line, a0, a1, name in WALLS:
        for end, sign, tag in ((a0, -1, 'start'), (a1, 1, 'end')):
            lo, hi = sorted((end - sign * 5, end + sign * 15))
            zone = (line - 3, line + 3, lo, hi) if orient == 'v' else (lo, hi, line - 3, line + 3)
            label = '%s %s' % (name, tag)
            # The wall's own two halves are always there; a third actor means another wall meets it
            if len(blockers(*zone)) < 3 and label not in FREE_ENDS:
                bad.append(label)
    return bad


def run():
    # Actors can't be spawned during PIE: bail out before deleting anything
    if execute_tool('EditorToolset.EditorAppToolset.IsPIERunning', '{}')['returnValue']:
        return {'error': 'PIE is running, stop the game first'}
    removed = 0
    for f in ('Blockout', 'Lights'):
        for a in in_folder(f):
            execute_tool(S + 'remove_from_scene', json.dumps({'actor': a}))
            removed += 1

    fy, top, bottom = Y(73), Y(205), Y(888)
    right = XL(787)
    box('Floor', -40, right + 40, fy - 260, bottom + 30, -20, 0, mat=PARQUET)  # the old parquet everywhere
    box('Ceiling', -40, right + 40, fy - 260, bottom + 30, H, H + 20, mat=PLASTER)
    # Renovated rooms lay their own floor over the old parquet; in doorways it ends at the wall center like a threshold
    for i, (room, x0, x1, y0, y1) in enumerate(ROOMS):
        floor = FINISH[room][1]
        if floor:
            box('Floor_%s_%d' % (room, i), x0, x1, y0, y1, 0, 0.5, mat=mat(floor))

    # Upper block: living, hallway, kitchen, vestibule
    vwall('W_Left', 197, 205, 888)
    vwall('W_Kitchen_R', 890, 205, 413)
    hwall('W_Top_Living', 205, 197, 543)
    hwall('W_Top_HallKitchen', 205, 642, 890)
    vwall('W_Vest_L', 543, 73, 205)
    vwall('W_Vest_R', 642, 73, 205)
    vwall('W_LivHall', 547, 205, 413, gaps=[(Y(318) + Y(362)) / 2])
    vwall('W_HallKitchen', 695, 205, 413, gaps=[(Y(318) + Y(398)) / 2])
    vwall('W_Nook', 302, 287, 413)
    # Upper corridor
    hwall('W_413_L', 413, 197, 385)
    hwall('W_413_R', 413, 472, 890)
    vwall('W_Corr1_L', 385, 413, 540)
    vwall('W_Corr1_R', 472, 413, 540)
    # Lower block: corridor, bathroom, bedroom
    bath_door = (XL(247) + XL(328)) / 2
    bed_door = XL(695) - BED_DOOR_FROM_END  # far right end of the corridor: longer walk after waking up
    hwall('W_540_L', 540, 197, 385)
    # Starts at the upper corridor (plan x=472), which the lower-block shift must not move
    wall_piece('W_540_R', 'h', Y(540), X(472) - 10, XL(695) + 10, 20)
    WALLS.append(('h', Y(540), X(472) - 10, XL(695) + 10, 'W_540_R'))
    vwall('W_Corr2_R', 695, 540, 628, xf=XL)
    hwall('W_628', 628, 197, 787, gaps=[bath_door, bed_door], xf=XL)
    vwall('W_Bath_Bed', 380, 628, 888, t=25, xf=XL)
    vwall('W_Bedroom_R', 787, 628, 888, xf=XL)
    hwall('W_Bottom', 888, 197, 787, xf=XL)

    # Front door wall (red line), 100cm opening, dark landing outside
    wall_piece('W_Front_a', 'h', fy, 409, 544, 20)
    wall_piece('W_Front_b', 'h', fy, 644, 779, 20)
    wall_piece('W_Front_Lintel', 'h', fy, 544, 644, 20, 205, H)
    wall_piece('Landing_L', 'v', 419, fy - 220, fy, 20)
    wall_piece('Landing_R', 'v', 769, fy - 220, fy, 20)
    wall_piece('Landing_Back', 'h', fy - 230, 409, 779, 20)

    # Furniture is real meshes in stages_week2.py; the kitchen counter stays a box (no kitchen in the furniture pack)
    box('Kitchen_Counter', X(890) - 70, X(890) - 10, top + 10, Y(400), 0, 90, f='Blockout/Props')

    # Movable lights with short radius: no stationary-overlap limit
    cx = (X(385) + X(472)) / 2
    room_y = (top + Y(413)) / 2
    vest_y = (fy + top) / 2
    corr2_y = (Y(540) + Y(628)) / 2
    for name, x, y in [('Light_Bedroom', (XL(380) + XL(787)) / 2, Y(760)), ('Light_Bath', XL(380) / 2, Y(760)),
                       ('Light_Corridor2_a', XL(695) * 0.25, corr2_y), ('Light_Corridor2_b', XL(695) * 0.75, corr2_y),
                       ('Light_Corridor1_a', cx, Y(413) + 120), ('Light_Corridor1_b', cx, Y(540) - 120),
                       ('Light_Living', X(400), room_y), ('Light_Nook', X(250), Y(350)), ('Light_Hall', X(620), room_y),
                       ('Light_Vestibule_a', X(593), vest_y - 100), ('Light_Vestibule_b', X(593), vest_y + 100),
                       ('Light_Kitchen', X(790), room_y)]:
        l = execute_tool(S + 'add_to_scene_from_class', json.dumps({
            'actor_type': {'refPath': '/Script/Engine.PointLight'}, 'name': name,
            'xform': {'location': {'x': x, 'y': y, 'z': 240}, 'rotation': ROT0}}))['returnValue']
        folder(l, 'Lights')
        props(l, {'bIsSpatiallyLoaded': False})
        props({'refPath': l['refPath'] + '.LightComponent0'}, {'Mobility': 'Movable', 'AttenuationRadius': 500})
    # Bedside lamp on the nightstand (stages_week2.py places the lamp mesh): the bed corner was too dark to read as home
    l = execute_tool(S + 'add_to_scene_from_class', json.dumps({
        'actor_type': {'refPath': '/Script/Engine.PointLight'}, 'name': 'Light_Bedside',
        'xform': {'location': {'x': 432, 'y': 925, 'z': 105}, 'rotation': ROT0}}))['returnValue']
    folder(l, 'Lights')
    props(l, {'bIsSpatiallyLoaded': False})
    props({'refPath': l['refPath'] + '.LightComponent0'}, {'Mobility': 'Movable', 'AttenuationRadius': 350, 'Intensity': 4})

    # Loop actors: door hinge on the left jamb (panel along +X), exit trigger on the landing, wake-up by the bed
    place(FRONT_DOOR, 544, fy, 0, -90)
    place(LOOP_EXIT, 594, fy - 90, 0, -90)
    wake_x, wake_y = XL(565) + 40, Y(760)  # beside the double bed (stages_week2.py), not in it
    wake_yaw = math.degrees(math.atan2(Y(628) - wake_y, bed_door - wake_x))  # face the bedroom door
    place(MANAGER, wake_x, wake_y, 0, wake_yaw)
    place(PLAYER_START, wake_x, wake_y, 100, wake_yaw)

    # Passability: a 90cm path (capsule is 80) through every opening on the route must hit nothing static
    lh = (Y(318) + Y(362)) / 2
    hk = (Y(318) + Y(398)) / 2
    zones = {
        'Liv->Hall': (X(547) - 13, X(547) + 13, lh - 45, lh + 45),
        'Hall->Kitchen': (X(695) - 13, X(695) + 13, hk - 45, hk + 45),
        'Corr2->Bath': (bath_door - 45, bath_door + 45, Y(628) - 13, Y(628) + 13),
        'Corr2->Bedroom': (bed_door - 45, bed_door + 45, Y(628) - 13, Y(628) + 13),
        'Corridor2': (20, XL(695) - 20, Y(540) + 15, Y(628) - 15),
        'Corridor1': (X(385) + 20, X(472) - 20, Y(413) - 20, Y(540) + 20),
        'Vestibule': (549, 639, fy + 5, top - 5),
        'FrontDoorFrame': (549, 639, fy - 13, fy + 13),
    }
    blocked = {k: v for k, v in ((k, blockers(*z)) for k, z in zones.items()) if v}
    return {'removed': removed, 'loose_ends': loose_ends(), 'bed_door_x': bed_door, 'wake_yaw': wake_yaw, 'bath_width': XL(380) - X(197), 'bedroom_width': XL(787) - XL(380),
            'corridor2_length': XL(695) - X(197), 'blocked': blocked}
