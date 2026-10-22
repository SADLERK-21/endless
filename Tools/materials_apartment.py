# Creates / updates the apartment finish materials (GDD 4.1): one material instance per finish.
# A single tile size tiles by world position (M_WorldAligned); a (U, V) pair makes an M_Fitted instance, whose layout
# each wall or floor sets through Custom Primitive Data (blockout_apartment.py): panels fit, parquet follows the corridor.
# Runs inside unreal-mcp's ProgrammaticToolset.execute_tool_script. Run it again after adding textures from Fab:
# each finish looks for its Fab texture by folder name and falls back to an already present one until then.
import json

AS = 'editor_toolset.toolsets.asset.AssetTools.'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
FOLDER = '/Game/Endless/Materials'
WORLD = {'refPath': FOLDER + '/M_WorldAligned.M_WorldAligned'}
FITTED = {'refPath': FOLDER + '/M_Fitted.M_Fitted'}  # built by material_fitted.py

# Finish: (Fab folder key, fallback key, tile cm or (U, V) cm, roughness, tint RGB). 'color+relief' takes base color and normal from two sources
FINISHES = {
    'MI_Walls_Living':    ('Fresh_Wall_Plaster+Decorative_Wall_Paint', 'Fresh_Wall_Plaster', 200, 0.8, (1.0, 0.88, 0.72)),
    'MI_Walls_Bedroom':   ('Fresh_Wall_Plaster+Decorative_Wall_Paint', 'Fresh_Wall_Plaster', 200, 0.8, (0.72, 0.82, 0.92)),
    'MI_Walls_Hall':      ('Fresh_Wall_Plaster', None, 250, 0.85, (0.82, 0.82, 0.82)),
    'MI_Walls_Kitchen':   ('Fresh_Wall_Plaster', None, 250, 0.85, (1.0, 1.0, 1.0)),
    'MI_Walls_Bath':      ('Tiles_06/', 'Fresh_Wall_Plaster', 60, 0.3, (1.0, 1.0, 1.0)),  # blue-green squares
    # Painted wall panels: the framed wallpaper's relief in flat paint; the scan is 1 x 2 m, one repeat per wall height
    'MI_Walls_Corridor':  ('Fresh_Wall_Plaster+Framed_Wallpaper', 'Old_Wallpaper', (135, 270), 0.6, (0.72, 0.75, 0.8)),
    'MI_Floor_Living':    ('Wooden_Floor', 'Herringbone_Parquet', 200, 0.45, (1.0, 1.0, 1.0)),
    'MI_Floor_Bedroom':   ('Wooden_Floor', 'Herringbone_Parquet', 200, 0.45, (0.7, 0.6, 0.5)),
    'MI_Floor_Tiles':     ('Tiles_04/', 'Fresh_Wall_Plaster', 220, 0.35, (1.0, 1.0, 1.0)),  # grey plank-like tiles
    'MI_Floor_Bath':      ('Seychelles', 'Fresh_Wall_Plaster', 120, 0.3, (1.0, 1.0, 1.0)),
    'MI_Parquet':         ('Herringbone_Parquet', None, 200, 0.55, (1.0, 1.0, 1.0)),  # under everything
    'MI_Parquet_Corridor': ('Herringbone_Parquet', None, (200, 200), 0.55, (1.0, 1.0, 1.0)),  # along each corridor
    'MI_Plaster':         ('Fresh_Wall_Plaster', None, 250, 0.9, (1.0, 1.0, 1.0)),  # ceilings, stairwell
    'MI_Baseboard_New':   ('Fresh_Wall_Plaster', None, 100, 0.4, (1.0, 1.0, 1.0)),
    'MI_Baseboard_Old':   ('Herringbone_Parquet', None, 60, 0.6, (0.55, 0.4, 0.28)),
}


SOURCES = ('/Game/Fab', '/Game/Materials_CeramicTiles')  # Fab downloads land in /Game/Fab or in their own folder


def textures():
    # Every downloaded texture, so finishes can be matched by folder name
    return [t for f in SOURCES for t in execute_tool(AS + 'find_assets', json.dumps({
        'folder_path': f, 'name': '', 'asset_type': {'refPath': '/Script/Engine.Texture2D'}, 'recursive': True}))['returnValue']]


def pick(all_tex, key):
    # (base color, normal) for a Fab folder key; Megascans end in _B/_N, glTF imports in _texture_0/_texture_2, the tiles pack in _Base_Color/_Normal
    if '+' in key:  # the decorative paint is dark olive: keep its relief, take the color from a light base
        color, relief = (pick(all_tex, k) for k in key.split('+'))
        return (color[0], relief[1]) if color and relief else None
    hits = [t for t in all_tex if key.lower() in t.lower()]
    base = [t for t in hits if t.endswith('_B') or t.endswith('_texture_0') or 'basecolor' in t.lower().replace('_', '') or 'albedo' in t.lower()]
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
        parent = FITTED if isinstance(tile, tuple) else WORLD
        if execute_tool(AS + 'exists', json.dumps({'path': path}))['returnValue']:
            mi = ref(path)
            execute_tool(MI + 'set_parent', json.dumps({'instance': mi, 'parent': parent}))
        else:
            mi = execute_tool(MI + 'create', json.dumps({'folder_path': FOLDER, 'asset_name': name, 'parent': parent}))['returnValue']
        execute_tool(MI + 'set_texture_parameter', json.dumps({'instance': mi, 'name': 'BaseColor', 'value': ref(found[0])}))
        execute_tool(MI + 'set_texture_parameter', json.dumps({'instance': mi, 'name': 'Normal', 'value': ref(found[1])}))
        for param, value in (zip(('TileU', 'TileV'), tile) if parent is FITTED else [('TileSize', tile)]):
            execute_tool(MI + 'set_scalar_parameter', json.dumps({'instance': mi, 'name': param, 'value': value}))
        execute_tool(MI + 'set_scalar_parameter', json.dumps({'instance': mi, 'name': 'Roughness', 'value': rough}))
        execute_tool(MI + 'set_vector_parameter', json.dumps({'instance': mi, 'name': 'Tint',
                                                              'value': {'r': tint[0], 'g': tint[1], 'b': tint[2], 'a': 1}}))
        report[name] = used
    execute_tool(AS + 'save_assets', json.dumps({'asset_paths': [FOLDER + '/' + n for n in FINISHES]}))
    return report
