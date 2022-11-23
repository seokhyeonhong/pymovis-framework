import glm

from pymovis.vis.primitives import *
from pymovis.vis.material import Material
from pymovis.vis.primitives import Cube

class RenderOptions:
    def __init__(
        self,
        mesh,
        shader,
        draw_func
    ):
        self._mesh        = mesh
        self._shader      = shader
        self._position    = glm.vec3(0)
        self._orientation = glm.mat3(1)
        self._scale       = glm.vec3(1)
        self._material    = Material()
        self._uv_repeat   = glm.vec2(1)
        self._draw_func   = draw_func
    
    def get_vao(self):
        return self._mesh.vao

    def get_vao_id(self):
        return self._mesh.vao.vao_id
    
    def draw(self):
        self._draw_func(self, self._shader)

    def get_position(self):
        return self._position

    def get_orientation(self):
        return self._orientation

    def get_scale(self):
        return self._scale
    
    def get_texture_id(self):
        return self._material.get_albedo_map().get_texture_id()
    
    def get_uv_repeat(self):
        return self._uv_repeat

    def set_position(self, x, y=None, z=None):
        if y != None and z != None:
            self._position = glm.vec3(x, y, z)
        else:
            self._position = glm.vec3(x)
        return self

    def set_orientation(self, orientation):
        self._orientation = glm.mat3(orientation)
        return self
    
    def set_scale(self, x, y=None, z=None):
        if y is None and z is None:
            self._scale = glm.vec3(x)
        else:
            self._scale = glm.vec3(x, y, z)
        return self

    def set_material(self, albedo=None, diffuse=None, specular=None):
        if albedo != None:
            self._material.set_albedo(albedo)
        if diffuse != None:
            self._material.set_diffuse(diffuse)
        if specular != None:
            self._material.set_specular(specular)
        return self

    def set_texture(self, filename):
        self._material.set_texture(filename)
        return self
    
    def set_uv_repeat(self, x, y=None):
        if y is None:
            self._uv_repeat = glm.vec2(x)
        else:
            self._uv_repeat = glm.vec2(x, y)
        return self