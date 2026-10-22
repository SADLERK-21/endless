# Builds M_Fitted: a projected master material whose layout each actor sets through Custom Primitive Data,
# so wall panels fit a wall from corner to corner and parquet runs along a corridor's axis (GDD 4.1).
# Runs inside unreal-mcp's ProgrammaticToolset.execute_tool_script. Recreates the graph from scratch.
#
# Custom Primitive Data 0..3 ("Fit"): origin along U (cm), tile along U (cm, 0 = TileU param),
# V origin (walls: top of the panel, cm), axes: floors 0 / 1 (1 = pattern runs along world X),
# walls 2 (along Y) / 3 (along X): a wall's 20cm end caps show a slice of mid-panel instead of a squeezed panel.
# Walls: U runs along the wall, V down from the origin. Floors: U = X, V = Y unless swapped.
import json

M = 'editor_toolset.toolsets.material.MaterialTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
O = 'editor_toolset.toolsets.object.ObjectTools.'
FOLDER, NAME = '/Game/Endless/Materials', 'M_Fitted'
MAT = {'refPath': FOLDER + '/' + NAME + '.' + NAME}
PLASTER = '/Game/Fab/Megascans/Surfaces/Fresh_Wall_Plaster_wi0oadulw/High/wi0oadulw_tier_1/Textures/T_wi0oadulw_4K_'

UV_CODE = """float3 a = abs(N);
float2 p;
if (a.z > 0.5) p = D.w > 0.5 ? float2(WP.y, WP.x) : WP.xy;
else p = float2(a.x > a.y ? WP.y : WP.x, -WP.z);
float tu = D.y > 0 ? D.y : TU;
float2 uv = float2((p.x - D.x) / tu, (p.y + D.z) / TV);
if (a.z <= 0.5 && D.w > 1.5 && ((D.w > 2.5) == (a.x > a.y))) uv.x = 0.425 + 0.15 * frac(p.x / 20);
return uv;"""

# The tangent-space normal back to world space with the same axes the UVs used (green = up in the image)
NORMAL_CODE = """float3 a = abs(N);
float3 tu, up, nz;
if (a.z > 0.5) {
    tu = D.w > 0.5 ? float3(0, 1, 0) : float3(1, 0, 0);
    up = D.w > 0.5 ? float3(-1, 0, 0) : float3(0, -1, 0);
    nz = float3(0, 0, sign(N.z));
} else {
    tu = a.x > a.y ? float3(0, 1, 0) : float3(1, 0, 0);
    up = float3(0, 0, 1);
    nz = a.x > a.y ? float3(sign(N.x), 0, 0) : float3(0, sign(N.y), 0);
}
return normalize(tu * T.x + up * T.y + nz * T.z);"""


def tool(name, **args):
    return execute_tool(M + name, json.dumps(args))['returnValue']


def node(cls, x, y, **values):
    e = tool('add_expression', material_or_function=MAT, expression_class={'refPath': '/Script/Engine.MaterialExpression' + cls}, x=x, y=y)
    if values and not execute_tool(O + 'set_properties', json.dumps({'instance': e, 'values': json.dumps(values)}))['returnValue']:
        raise RuntimeError('set_properties failed on %s: %s' % (cls, values))
    return e


def custom(x, y, code, out_type, desc, inputs):
    e = node('Custom', x, y, Code=code, OutputType=out_type, Description=desc)
    # set_properties can't resize an array and rename its elements in one call: copy the default input first
    cur = json.loads(execute_tool(O + 'get_properties', json.dumps({'instance': e, 'properties': ['Inputs']}))['returnValue'])['Inputs']
    for values in ({'Inputs': cur[:1] * len(inputs)}, {'Inputs': [dict(cur[0], InputName=k) for k in inputs]}):
        if not execute_tool(O + 'set_properties', json.dumps({'instance': e, 'values': json.dumps(values)}))['returnValue']:
            raise RuntimeError('set_properties failed on Custom inputs: %s' % values)
    return e


def wire(a, b, pin, out=''):
    tool('connect_expressions', from_expression=a, from_output_name=out, to_expression=b, to_input_name=pin)


def run():
    if execute_tool(AS + 'exists', json.dumps({'path': FOLDER + '/' + NAME}))['returnValue']:
        for e in tool('get_expressions', material_or_function=MAT):
            tool('delete_expression', material_or_function=MAT, expression=e)
    else:
        tool('create_material', folder_path=FOLDER, asset_name=NAME)
    execute_tool(O + 'set_properties', json.dumps({'instance': MAT, 'values': json.dumps({'bTangentSpaceNormal': False})}))

    wp = node('WorldPosition', -1400, 0)
    n = node('VertexNormalWS', -1400, 150)
    fit = node('VectorParameter', -1400, 300, ParameterName='Fit', bUseCustomPrimitiveData=True, PrimitiveDataIndex=0,
               DefaultValue={'R': 0, 'G': 0, 'B': 0, 'A': 0})
    tile_u = node('ScalarParameter', -1400, 500, ParameterName='TileU', DefaultValue=200)
    tile_v = node('ScalarParameter', -1400, 600, ParameterName='TileV', DefaultValue=200)
    uv = custom(-1000, 200, UV_CODE, 'CMOT_Float2', 'FitUV', ('WP', 'N', 'D', 'TU', 'TV'))
    for src, pin in ((wp, 'WP'), (n, 'N'), (tile_u, 'TU'), (tile_v, 'TV')):
        wire(src, uv, pin)
    wire(fit, uv, 'D', 'RGBA')  # the default pin is RGB only

    base_tex = node('TextureObjectParameter', -1000, -300, ParameterName='BaseColor',
                    Texture=PLASTER + 'B.T_wi0oadulw_4K_B')
    normal_tex = node('TextureObjectParameter', -1000, 500, ParameterName='Normal',
                      Texture=PLASTER + 'N.T_wi0oadulw_4K_N', SamplerType='SAMPLERTYPE_Normal')
    base = node('TextureSample', -600, -200)
    wire(base_tex, base, 'Tex')
    wire(uv, base, 'UVs')
    nrm = node('TextureSample', -600, 400, SamplerType='SAMPLERTYPE_Normal')
    wire(normal_tex, nrm, 'Tex')
    wire(uv, nrm, 'UVs')

    tint = node('VectorParameter', -600, -400, ParameterName='Tint', DefaultValue={'R': 1, 'G': 1, 'B': 1, 'A': 1})
    color = node('Multiply', -300, -300)
    wire(base, color, 'A', 'RGB')
    wire(tint, color, 'B', 'RGB')
    world_n = custom(-300, 300, NORMAL_CODE, 'CMOT_Float3', 'FitNormal', ('N', 'D', 'T'))
    wire(n, world_n, 'N')
    wire(fit, world_n, 'D', 'RGBA')
    wire(nrm, world_n, 'T', 'RGB')
    rough = node('ScalarParameter', -300, 100, ParameterName='Roughness', DefaultValue=0.8)

    tool('connect_to_output', expression=color, output_name='', material_property='MP_BaseColor')
    tool('connect_to_output', expression=world_n, output_name='', material_property='MP_Normal')
    tool('connect_to_output', expression=rough, output_name='', material_property='MP_Roughness')
    tool('recompile', material_or_function=MAT)
    execute_tool(AS + 'save_assets', json.dumps({'asset_paths': [MAT['refPath']]}))  # the package path alone can fail
    return {'ok': NAME}
