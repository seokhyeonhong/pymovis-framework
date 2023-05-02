from __future__ import annotations

import fbx
from pymovis.motion.data.fbx_parser import TextureInfo

def get_textures(geometry) -> list[TextureInfo]:
    textures = []
    if geometry.GetNode() is None:
        return textures
    
    num_materials = geometry.GetNode().GetSrcObjectCount()
    for material_idx in range(num_materials):
        material = geometry.GetNode().GetSrcObject(material_idx)
        
        # go through all the possible textures
        if not isinstance(material, fbx.FbxSurfaceMaterial):
            continue
        
        for texture_idx in range(fbx.FbxLayerElement.sTypeTextureCount()):
            property = material.FindProperty(fbx.FbxLayerElement.sTextureChannelNames(texture_idx))
            textures.extend(find_and_display_texture_info_by_property(property, material_idx))
    
    return textures

def find_and_display_texture_info_by_property(property, material_idx):
    textures = []

    if not property.IsValid():
        print("Invalid property")
        return textures
    
    texture_count = property.GetSrcObjectCount()
    for j in range(texture_count):
        if not isinstance(property.GetSrcObject(j), fbx.FbxTexture):
            continue

        layered_texture = property.GetSrcObject(j)
        if isinstance(layered_texture, fbx.FbxLayeredTexture):
            for k in range(layered_texture.GetSrcObjectCount()):
                texture = layered_texture.GetSrcObject(k)
                if not isinstance(texture, fbx.FbxTexture):
                    continue
                
                blend_mode = layered_texture.GetTextureBlendMode(k)
                texture_info = get_file_texture(texture, blend_mode)
                texture_info.property = property.GetName()
                texture_info.connected_material = material_idx
                textures.append(texture_info)
        else:
            texture = property.GetSrcObject(j)
            if not isinstance(texture, fbx.FbxTexture):
                continue
            
            texture_info = get_file_texture(texture, -1)
            texture_info.property = property.GetName()
            texture_info.connected_material = material_idx
            textures.append(texture_info)
            
    return textures

def get_file_texture(texture, blend_mode):
    info = TextureInfo()
    info.name = texture.GetName()

    # get texture type
    if isinstance(texture, fbx.FbxFileTexture):
        info.filename = texture.GetFileName()
    elif isinstance(texture, fbx.FbxProceduralTexture):
        return info
    else:
        raise Exception("Unknown texture type")
    
    # get texture properties
    info.scale_u = texture.GetScaleU()
    info.scale_v = texture.GetScaleV()
    info.translation_u = texture.GetTranslationU()
    info.translation_v = texture.GetTranslationV()
    info.swap_uv = texture.GetSwapUV()
    info.rotation_u = texture.GetRotationU()
    info.rotation_v = texture.GetRotationV()
    info.rotation_w = texture.GetRotationW()

    # get texture alpha properties
    alpha_sources = [ "None", "RGB Intensity", "Black" ]
    info.alpha_source = alpha_sources[texture.GetAlphaSource()]
    info.crop_left = texture.GetCroppingLeft()
    info.crop_top = texture.GetCroppingTop()
    info.crop_right = texture.GetCroppingRight()
    info.crop_bottom = texture.GetCroppingBottom()

    # get texture mapping types
    mapping_types = [ "Null", "Planar", "Spherical", "Cylindrical", "Box", "Face", "UV", "Environment" ]
    info.mapping_type = mapping_types[texture.GetMappingType()]
    
    if texture.GetMappingType() == fbx.FbxTexture.ePlanar:
        planar_mapping_normals = [ "X", "Y", "Z" ]
        info.planar_mapping_normal = planar_mapping_normals[texture.GetPlanarMappingNormal()]

    # get blend modes
    blend_modes = [ "Translucent", "Additive", "Modulate", "Modulate2", "Over", "Normal", "Dissolve", "Darken", "ColorBurn", "LinearBurn",
                    "DarkerColor", "Lighten", "Screen", "ColorDodge", "LinearDodge", "LighterColor", "SoftLight", "HardLight", "VividLight",
                    "LinearLight", "PinLight", "HardMix", "Difference", "Exclusion", "Substract", "Divide", "Hue", "Saturation", "Color",
                    "Luminosity", "Overlay" ]
    
    if blend_mode >= 0:
        info.blend_mode = blend_modes[blend_mode]
    
    info.alpha = texture.GetDefaultAlpha()

    # get texture uses
    if isinstance(texture, fbx.FbxFileTexture):
        material_uses = [ "Model Material", "Default Material" ]
        info.material_use = material_uses[texture.GetMaterialUse()]

    texture_uses = [ "Standard", "Shadow Map", "Light Map", "Spherical Reflexion Map", "Sphere Reflexion Map", "Bump Normal Map" ]
    info.texture_use = texture_uses[texture.GetTextureUse()]

    return info