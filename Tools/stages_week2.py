# Week 2 "story skeleton": placeholder changes of the apartment per loop stage (GDD section 3).
# Runs inside unreal-mcp's ProgrammaticToolset.execute_tool_script, after blockout_apartment.py.
# Rebuilds everything in the Stages outliner folder: props that anomalies swap (bed, wardrobe, phone),
# Anomaly actors, story items, hints, wall signs of the higher power and the per-stage light script.
# World coordinates match blockout_apartment.py (bedroom X 375..1285 / Y 835..1225, hallway X 525..747 / Y -200..312...).
import json

S = 'editor_toolset.toolsets.scene.SceneTools.'
O = 'editor_toolset.toolsets.object.ObjectTools.'
LVL = '/Game/Maps/L_Apartment.L_Apartment:PersistentLevel.'
MANAGER = {'refPath': LVL + 'LoopManager_UAID_50EBF677B6286D0D03_1474282790'}
BLACK = '/Engine/EngineDebugMaterials/BlackUnlitMaterial.BlackUnlitMaterial'
# Linear colors (0..1). WorldText glows, so it reads at any stage darkness (playtest 1: grey text was invisible)
SIGN, CLOCK, LABEL = (0.45, 0.0, 0.0), (1.0, 0.05, 0.03), (1.0, 0.75, 0.15)
# shortcut: engine/editor sounds stand in for the ring and the hint until real audio (MVP week 5); editor-only content won't cook
RING = '/Engine/EngineSounds/1kSineTonePing.1kSineTonePing'
HINT_SOUND = '/Engine/VREditor/Sounds/VR_shep_scale_down_01_Cue.VR_shep_scale_down_01_Cue'

STAGES = [
    ('0_Home', 'Дом. Норма, игрок запоминает квартиру. Часы у кровати стоят на 23:59.', False),
    ('1_Trifle', 'Мелочь. Заброшенные хобби: гитара, модель. Первая еле заметная надпись. (Звонок с писком монитора: неделя 5)', False),
    ('2_Guilt', 'Вина. Подарок маме, пропущенные звонки. Деталь: фото с мамой на кухне. Надпись ведёт на кухню.', True),
    ('3_ICU', 'Реанимация. Капельница у кровати, вода у уборной. Надписи ведут к двери. Свет мигает. (Звонок врачей: неделя 5)', False),
    ('4_Forgiveness', 'Прощение. Мебель сдвинута, фигура в глубине гостиной. Деталь: ответить на звонок мамы. Почти темно.', True),
    ('5_Acceptance', 'Принятие. Часы 00:00, фигура у входной двери. Выбор: уйти или остаться (неделя 6).', False),
]

EXPOSURE_BIAS = -2.0  # EV of the manual exposure volume (-3 before materials: dark wallpaper and wood need +1)
TEXT_GLOW = 2 ** -EXPOSURE_BIAS  # WorldText emissive boost that cancels the exposure: x8 at -3 EV

LIGHT_ROWS = [  # intensity multiplier, Kelvin, flicker share
    (1.0, 2700, 0.0),
    (0.9, 3200, 0.0),
    (0.7, 4000, 0.0),
    (0.5, 5000, 0.4),
    (0.12, 6500, 0.2),
    (2.0, 9000, 0.0),
]


def props(a, values):
    if not execute_tool(O + 'set_properties', json.dumps({'instance': a, 'values': json.dumps(values)}))['returnValue']:
        raise RuntimeError('set_properties failed on %s: %s' % (a['refPath'], values))


def folder(a, f):
    execute_tool(S + 'set_actor_folder', json.dumps({'actor': a, 'folder_path': f}))
    props(a, {'bIsSpatiallyLoaded': False})  # small level: keep everything loaded in the editor
    return a


def spawn(cls, name, x, y, z, f, yaw=0):
    a = execute_tool(S + 'add_to_scene_from_class', json.dumps({
        'actor_type': {'refPath': cls}, 'name': name,
        'xform': {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': 0, 'yaw': yaw, 'roll': 0}}}))['returnValue']
    return folder(a, f)


def box(name, x0, x1, y0, y1, z0, z1, f, black=False, mat=None):
    a = execute_tool(S + 'add_to_scene_from_asset', json.dumps({
        'asset_path': '/Engine/BasicShapes/Cube', 'name': name,
        'xform': {'location': {'x': (x0 + x1) / 2, 'y': (y0 + y1) / 2, 'z': (z0 + z1) / 2},
                  'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0},
                  'scale': {'x': (x1 - x0) / 100, 'y': (y1 - y0) / 100, 'z': (z1 - z0) / 100}}}))['returnValue']
    if black or mat:
        props({'refPath': a['refPath'] + '.StaticMeshComponent0'}, {'OverrideMaterials': [BLACK if black else MATS + mat + '.' + mat]})
    return folder(a, f)


MATS = '/Game/Endless/Materials/'
ZD = '/Game/ZD_Kitchen_Collection01/Meshs/'  # Tableware / Appliances Collection (ZenDen-Digital, Fab)
FF = '/Game/FreeFurniturePack/Meshes/'  # Free Furniture Pack (Next Level 3D, Fab); pivots sit bottom-center
BP = '/Game/FreeFurniturePack/Blueprints/'  # the pack's assembled furniture: doors and drawers on their meshes
# Pack fronts face local +Y: yaw 90 faces -X (right walls), -90 faces +X (left walls), 180 faces -Y


def mesh(name, asset, x, y, yaw, f, z=0, scale=(1, 1, 1)):
    a = execute_tool(S + 'add_to_scene_from_asset', json.dumps({
        'asset_path': asset if asset.startswith('/') else FF + asset, 'name': name,
        'xform': {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': 0, 'yaw': yaw, 'roll': 0},
                  'scale': dict(zip('xyz', scale))}}))['returnValue']
    return folder(a, f)


def text(name, s, x, y, z, yaw, size, color, f):
    # WorldText, not TextRender: TextRender's fonts have no Cyrillic. Reads from the actor's +X side.
    a = spawn('/Script/Endless.WorldText', name, x, y, z, f, yaw)
    props(a, {'Text': s, 'Size': size, 'Color': {'R': color[0], 'G': color[1], 'B': color[2], 'A': 1.0}})
    props({'refPath': a['refPath'] + '.Widget'}, {'TintColorAndOpacity': {'R': TEXT_GLOW, 'G': TEXT_GLOW, 'B': TEXT_GLOW, 'A': 1.0}})
    return a


def rim_light(name, x, y, z, f):
    # The figure is unlit black: it only reads as a silhouette against a lit wall behind it
    l = spawn('/Script/Engine.PointLight', name, x, y, z, f)
    props({'refPath': l['refPath'] + '.LightComponent0'}, {'Mobility': 'Movable', 'Intensity': 6, 'AttenuationRadius': 300})
    return l


def anomaly(name, first, last, f, show=(), hide=()):
    a = spawn('/Script/Endless.Anomaly', name, 0, 0, 0, f)
    props(a, {'FirstStage': first, 'LastStage': last,
              'ShowWhenActive': [x['refPath'] for x in show], 'HideWhenActive': [x['refPath'] for x in hide]})
    return a


def kitchen_set(f):
    # Along the right wall (inner face x=1030), from the top wall: fridge, cabinet, sink, dishwasher, hob, cabinet
    x0, x1, top, bottom = 970, 1030, -190, 292
    mesh('Fridge', ZD + 'Fridge/BP_Fridge', x1 - 38, top + 58, 180, f, z=102)
    run0 = top + 117
    box('Kitchen_Plinth', x0 + 5, x1, run0, bottom, 0, 10, f, mat='MI_Kitchen_Dark')
    box('Kitchen_Cabinets_a', x0, x1, run0, 67, 10, 87, f, mat='MI_Kitchen_Facade')
    mesh('Dishwasher', ZD + 'Dishwasher/BP_DishWasher', x1 - 30, 99, 90, f)
    box('Kitchen_Cabinets_b', x0, x1, 131, bottom, 10, 87, f, mat='MI_Kitchen_Facade')
    box('Countertop', x0 - 2, x1, run0, bottom, 87, 91, f, mat='MI_Countertop')
    box('Sink', x0 + 10, x1 - 12, 0, 50, 91, 92, f, mat='MI_Kitchen_Dark')
    box('Hob', x0 + 8, x1 - 8, 136, 186, 91, 91.5, f, mat='MI_Kitchen_Dark')
    box('Kitchen_Upper', x1 - 35, x1, run0, bottom, 150, 220, f, mat='MI_Kitchen_Facade')
    mesh('Microwave', ZD + 'Microwave/BP_Microwave', x1 - 28, 240, 90, f, z=91)
    mesh('Toaster', ZD + 'Toaster/BP_Toaster', x1 - 20, 280, 90, f, z=91)
    mesh('KnifeBlock', ZD + 'KnifeBlock/BP_KnifeBlock', x1 - 15, -50, 90, f, z=91)


def remove_folder(f):
    if f not in execute_tool(S + 'get_folders', '{}')['returnValue']:
        return 0
    actors = execute_tool(S + 'get_actors_in_folder', json.dumps({'folder_path': f, 'recursive': True}))['returnValue']
    for a in actors:
        execute_tool(S + 'remove_from_scene', json.dumps({'actor': a}))
    return len(actors)


def run():
    if execute_tool('EditorToolset.EditorAppToolset.IsPIERunning', '{}')['returnValue']:
        return {'error': 'PIE is running, stop the game first'}
    # Only ever delete by folder: find_actors' name filter is a substring match ('Bed' hits 'W_Bedroom_R')
    removed = remove_folder('Stages')

    # Normal apartment (stage 0): props that later stages hide or move
    n = 'Stages/0_Normal'
    # Bedroom: double bed headboard to the bathroom wall, nightstand with lamp and the stopped clock
    bed = mesh('Bed', 'SM_Modern_Bed_2', 517, 1080, 0, n)
    mesh('Nightstand', 'SM_Bed_Table', 412, 925, 0, n)
    mesh('Bedside_Lamp', 'SM_Table_Lamp', 422, 912, 0, n, z=61)  # the pack's Bed_Lamp meshes are wall lamps
    box('Clock_Body', 400, 414, 928, 952, 61, 76, n)
    clock = text('Clock_2359', '23:59', 415, 940, 68, 0, 7, CLOCK, n)
    mesh('Bedroom_Wardrobe', BP + 'BP_Modern_Cupboard', 1137, 1029, 90, n)  # built-in along the right wall
    mesh('Picture_Bed', 'SM_Classic_Picture', 389, 1080, 0, n, z=150)
    # Renovated rooms get the pack's modern furniture (GDD 4.1); old pieces stay only in the corridors
    # Hallway: wardrobe and the phone on a commode, both on the right wall
    # shortcut: the 2.8 m sliding wardrobe squeezed to 1.7 x 2.3 m to fit beside the phone commode; a narrower model later
    mesh('Wardrobe', BP + 'BP_Modern_Cupboard', 700, -100, 90, n, scale=(0.6, 1, 0.9))
    mesh('PhoneTable', BP + 'BP_Classic_Commode', 715, 30, 90, n)
    phone = box('Phone', 705, 725, 20, 40, 100, 110, n)
    mesh('Picture_Hall', 'SM_Classic_Picture', 536, -60, 0, n, z=160)
    # Living room: sofa back to the top wall, coffee table, TV on a commode by the left wall; the armchair stays right of the corridor's line of sight to the stage 4 figure
    sofa = mesh('Sofa', 'SM_Modern_Sofa_2', 176, -93, 90, n)
    armchair = mesh('Armchair', 'SM_Modern_Armchair', 445, -10, 90, n)
    mesh('Coffee_Table', 'SM_Coffee_Table', 176, -10, 0, n)
    mesh('TV_Stand', 'SM_Commode', 40, 13, -90, n)
    mesh('TV', 'SM_TV', 40, 13, -90, n, z=88)
    # Computer nook: desk and office chair
    mesh('Desk', 'SM_Modern_Table', 55, 219, -90, n)
    mesh('Desk_Chair', 'SM_Modern_Office_chair', 125, 219, 90, n)
    # Kitchen: table along the narrow room, the kitchen set along the right wall
    mesh('Dining_Table', 'SM_Modern_Table', 830, 40, 90, n)
    mesh('Dining_Chair_1', 'SM_Modern_Chair_1', 830, -90, 0, n)
    mesh('Dining_Chair_2', 'SM_Modern_Chair_1', 830, 170, 180, n)
    kitchen_set(n)
    # Bathroom and lower corridor
    mesh('Toilet', 'SM_Toilet', 40, 1175, -90, n)
    mesh('Bathtub', 'SM_Bathtub', 250, 1160, 180, n)
    mesh('Picture_Corridor', 'SM_Classic_Picture', 700, 714, 90, n, z=150)

    # 1: abandoned hobbies, first faint sign
    f = 'Stages/1_Trifle'
    s1 = [box('Guitar', 380, 420, -190, -175, 0, 110, f), text('Guitar_Label', 'гитара (пыльная)', 400, -170, 130, 90, 16, LABEL, f),
          box('ModelKit', 20, 60, 180, 230, 75, 95, f), text('ModelKit_Label', 'недособранная модель', 75, 205, 115, 0, 14, LABEL, f)]
    anomaly('A1_Hobbies', 1, -1, f, show=s1)
    anomaly('A1_Sign', 1, -1, f, show=[text('Sign1', 'ты не спишь', 600, 714, 160, 90, 20, SIGN, f)])

    # 2: guilt about mom; story item = photo in the kitchen, the sign points there
    f = 'Stages/2_Guilt'
    anomaly('A2_Gift', 2, -1, f, show=[box('Gift', 545, 585, 262, 298, 0, 30, f),
                                         text('Gift_Label', 'подарок маме', 586, 280, 50, 0, 16, LABEL, f)])
    anomaly('A2_MissedCalls', 2, 3, f, show=[text('MissedCalls', 'Мама: 12 пропущенных', 735, 30, 135, 180, 14, LABEL, f)])
    photo = spawn('/Script/Endless.StoryItem', 'Photo', 1000, 100, 102, f, yaw=90)
    props({'refPath': photo['refPath'] + '.Mesh'}, {'StaticMesh': FF + 'SM_Picture.SM_Picture',
                                                     'RelativeScale3D': {'X': 0.4, 'Y': 0.4, 'Z': 0.4}})
    props(photo, {'UseMessage': 'Фото: мама и я, лет десять назад. На обороте её почерком: «Приезжай, когда сможешь».'})
    anomaly('A2_Photo', 2, 2, f, show=[photo, text('Photo_Label', 'фото с мамой [E]', 990, 100, 130, 180, 14, LABEL, f)])
    hint2 = spawn('/Script/Endless.StageHint', 'Hint_Kitchen', 900, 60, 150, f)
    props(hint2, {'Stage': 2, 'MinRepeat': 2, 'Sound': HINT_SOUND})
    anomaly('A2_Sign', 2, 2, f, show=[text('Sign2', 'загляни на кухню', 736, 120, 170, 180, 24, SIGN, f)])

    # 3: the hospital leaks in; signs lead to the front door
    f = 'Stages/3_ICU'
    anomaly('A3_IV', 3, -1, f, show=[box('IV_Pole', 630, 640, 930, 940, 0, 180, f), box('IV_Bag', 622, 648, 925, 945, 160, 190, f),
                                       text('IV_Label', 'капельница', 635, 950, 210, 0, 16, LABEL, f)])
    anomaly('A3_Water', 3, 4, f, show=[box('Puddle', 95, 180, 760, 830, 0, 0.5, f)])
    anomaly('A3_Sign', 3, -1, f, show=[text('Sign3', 'иди к двери', 293, 500, 170, 0, 30, SIGN, f)])

    # 4: the apartment breaks; story item = answer mom's call; the figure shows up for the first time
    f = 'Stages/4_Forgiveness'
    phone_item = spawn('/Script/Endless.StoryItem', 'Phone_Ringing', 715, 30, 110, f)
    props(phone_item, {'bHideOnUse': False,
                       'UseMessage': 'Мама: «Сынок? Ты меня слышишь? Я здесь, рядом…»  [заглушка: озвученный разговор — неделя 5]'})
    anomaly('A4_Call', 4, 4, f, hide=[phone], show=[phone_item, text('Sign4', 'ОТВЕТЬ', 736, 30, 195, 180, 30, SIGN, f),
                                                      text('Phone_Label', 'звонит: Мама [E]', 735, 30, 140, 180, 14, LABEL, f)])
    hint4 = spawn('/Script/Endless.StageHint', 'Hint_Phone', 715, 30, 150, f)
    props(hint4, {'Stage': 4, 'MinRepeat': 0, 'Sound': RING, 'Interval': 2.5})  # the phone rings from the stage start
    anomaly('A4_Moved', 4, 4, f, hide=[bed, sofa, armchair], show=[mesh('Bed_Moved', 'SM_Modern_Bed_2', 520, 1080, 90, f),
                                                                   mesh('Sofa_Moved', 'SM_Modern_Sofa_2', 420, -60, 180, f)])
    # Deep in the living room, in line with the upper corridor: seen while walking it toward the living room
    anomaly('A4_Figure', 4, 4, f, show=[box('Figure_Living', 327, 367, -120, -80, 0, 220, f, black=True),
                                        rim_light('Figure_Living_Rim', 347, -175, 200, f)])

    # 5: acceptance; the clock moves to 00:00, the figure waits on the landing right behind the front door
    f = 'Stages/5_Acceptance'
    anomaly('A5_Clock', 5, -1, f, hide=[clock], show=[text('Clock_0000', '00:00', 415, 940, 68, 0, 7, CLOCK, f)])
    anomaly('A5_Figure', 5, -1, f, show=[box('Figure_Door', 574, 614, -790, -760, 0, 230, f, black=True),
                                         rim_light('Figure_Door_Rim', 594, -808, 200, f),
                                         text('Sign5', 'ПОРА', 594, -586, 237, 90, 30, SIGN, f)])

    # Fixed exposure: auto exposure would brighten the dark stages back up. -3 EV keeps stage 0 readable
    # and stage 4 (lamps x0.12) dark: there is no flashlight, the player wanders in the dark.
    pp = spawn('/Script/Engine.PostProcessVolume', 'PP_ManualExposure', 600, 300, 300, 'Stages')
    props(pp, {'bUnbound': True, 'Settings': {
        'bOverride_AutoExposureMethod': True, 'AutoExposureMethod': 'AEM_Manual',
        'bOverride_AutoExposureApplyPhysicalCameraExposure': True, 'AutoExposureApplyPhysicalCameraExposure': False,
        'bOverride_AutoExposureBias': True, 'AutoExposureBias': EXPOSURE_BIAS}})

    # Rough light script over the apartment lamps only: the figures' rim lights must not dim with the stage
    lamps = execute_tool(S + 'get_actors_in_folder', json.dumps({'folder_path': 'Lights', 'recursive': True}))['returnValue']
    lighting = spawn('/Script/Endless.StageLighting', 'StageLighting', 600, 300, 250, 'Stages')
    props(lighting, {'Stages': [{'Intensity': i, 'Temperature': t, 'Flicker': fl} for i, t, fl in LIGHT_ROWS],
                     'Lights': [l['refPath'] for l in lamps]})

    props(MANAGER, {'Stages': [{'Name': n, 'DesignNote': d, 'bRequiresObjective': r} for n, d, r in STAGES]})
    return {'removed': removed, 'lamps': len(lamps)}
