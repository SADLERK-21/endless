# Creates / updates the apartment finish materials (GDD 4.1): one M_WorldAligned instance per finish.
# Runs inside unreal-mcp's ProgrammaticToolset.execute_tool_script. Run it again after adding textures from Fab:
# each finish looks for its Fab texture by folder name and falls back to an already present one until then.
import json

AS = 'editor_toolset.toolsets.asset.AssetTools.'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
FOLDER = '/Game/Endless/Materials'
PARENT = {'refPath': FOLDER + '/M_WorldAligned.M_WorldAligned'}

# Finish: (Fab folder key, fallback key, tile cm, roughness, tint RGB)
FINISHES = {
    'MI_Walls_Living':    ('Decorative_Wall_Paint', 'Fresh_Wall_Plaster', 200, 0.8, (1.0, 0.88, 0.72)),
    'MI_Walls_Bedroom':   ('Decorative_Wall_Paint', 'Fresh_Wall_Plaster', 200, 0.8, (0.72, 0.82, 0.92)),
    'MI_Walls_Hall':      ('Fresh_Wall_Plaster', None, 250, 0.85, (0.82, 0.82, 0.82)),
    'MI_Walls_Kitchen':   ('Fresh_Wall_Plaster', None, 250, 0.85, (1.0, 1.0, 1.0)),
    'MI_Walls_Bath':      ('Ceramic_Tiles', 'Fresh_Wall_Plaster', 120, 0.3, (1.0, 1.0, 1.0)),
    'MI_Walls_Corridor':  ('Framed_Wallpaper', 'Old_Wallpaper', 150, 0.8, (1.0, 0.92, 0.75)),
    'MI_Wallpaper':       ('Old_Wallpaper', None, 150, 0.8, (1.0, 1.0, 1.0)),  # nook: the old green wallpaper
    'MI_Floor_Living':    ('Wooden_Floor', 'Herringbone_Parquet', 200, 0.45, (1.0, 1.0, 1.0)),
    'MI_Floor_Bedroom':   ('Wooden_Floor', 'Herringbone_Parquet', 200, 0.45, (0.7, 0.6, 0.5)),
    'MI_Floor_Tiles':     ('Ceramic_Tiles', 'Fresh_Wall_Plaster', 120, 0.35, (0.9, 0.9, 0.9)),
    'MI_Floor_Bath':      ('Seychelles', 'Fresh_Wall_Plaster', 120, 0.3, (1.0, 1.0, 1.0)),
    'MI_Parquet':         ('Herringbone_Parquet', None, 200, 0.55, (1.0, 1.0, 1.0)),  # corridors, nook
    'MI_Plaster':         ('Fresh_Wall_Plaster', None, 250, 0.9, (1.0, 1.0, 1.0)),  # ceilings, stairwell
    'MI_Baseboard_New':   ('Fresh_Wall_Plaster', None, 100, 0.4, (1.0, 1.0, 1.0)),
    'MI_Baseboard_Old':   ('Herringbone_Parquet', None, 60, 0.6, (0.55, 0.4, 0.28)),
}


def textures():
    # Every Fab texture, so finishes can be matched by folder name
    return execute_tool(AS + 'find_assets', json.dumps({
        'folder_path': '/Game/Fab', 'name': '', 'asset_type': {'refPath': '/Script/Engine.Texture2D'}, 'recursive': True}))['returnValue']


def pick(all_tex, key):
    # (base color, normal) for a Fab folder key; Megascans end in _B/_N, glTF imports in _texture_0/_texture_2
    hits = [t for t in all_tex if key.lower() in t.lower()]
    base = [t for t in hits if t.endswith('_B') or t.endswith('_texture_0') or 'basecolor' in t.lower() or 'albedo' in t.lower()]
    normal = [t for t in hits if t.endswith('_N') or t.endswith('_texture_2') or 'normal' in t.lower()]
    if base and normal:
        return base[0], normal[0]
    return None


def ref(path):
    return {'refPath': path + '.' + path.split('/')[-1]}


def run():
    all_tex = textures()
    report = {}
    for name, (key, fallback, tile, rough, tint) in FINISHES.items():
        found = pick(all_tex, key)
        used = key
        if not found and fallback:
            found, used = pick(all_tex, fallback), fallback + ' (placeholder)'
        if not found:
            report[name] = 'NO TEXTURES for %s' % key
            continue
        path = FOLDER + '/' + name
        if execute_tool(AS + 'exists', json.dumps({'path': path}))['returnValue']:
            mi = ref(path)
        else:
            mi = execute_tool(MI + 'create', json.dumps({'folder_path': FOLDER, 'asset_name': name, 'parent': PARENT}))['returnValue']
        execute_tool(MI + 'set_texture_parameter', json.dumps({'instance': mi, 'name': 'BaseColor', 'value': ref(found[0])}))
        execute_tool(MI + 'set_texture_parameter', json.dumps({'instance': mi, 'name': 'Normal', 'value': ref(found[1])}))
        execute_tool(MI + 'set_scalar_parameter', json.dumps({'instance': mi, 'name': 'TileSize', 'value': tile}))
        execute_tool(MI + 'set_scalar_parameter', json.dumps({'instance': mi, 'name': 'Roughness', 'value': rough}))
        execute_tool(MI + 'set_vector_parameter', json.dumps({'instance': mi, 'name': 'Tint',
                                                              'value': {'r': tint[0], 'g': tint[1], 'b': tint[2], 'a': 1}}))
        report[name] = used
    execute_tool(AS + 'save_assets', json.dumps({'asset_paths': [FOLDER + '/' + n for n in FINISHES]}))
    return report
