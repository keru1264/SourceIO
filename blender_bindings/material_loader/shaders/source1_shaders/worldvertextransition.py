from typing import Any

import bpy

from SourceIO.blender_bindings.material_loader.shader_base import Nodes, ExtraMaterialParameters
from SourceIO.blender_bindings.material_loader.shaders.source1_shader_base import Source1ShaderBase
from SourceIO.blender_bindings.utils.bpy_utils import is_blender_4

from .detail import DetailSupportMixin


class WorldVertexTransition(DetailSupportMixin, Source1ShaderBase):
    SHADER = 'worldvertextransition'

    @property
    def basetexture(self):
        texture_path = self._vmt.get_string('$basetexture', None)
        if texture_path is not None:
            return self.load_texture_or_default(texture_path, (0.3, 0.0, 0.3, 1.0))
        return None

    @property
    def blendmodulatetexture(self):
        texture_path = self._vmt.get_string('$blendmodulatetexture', None)
        if texture_path is not None:
            image = self.load_texture_or_default(texture_path, (0.3, 0.0, 0.3, 1.0))
            image.colorspace_settings.is_data = True
            image.colorspace_settings.name = 'Non-Color'
            return image

        return None

    @property
    def basetexture2(self):
        texture_path = self._vmt.get_string('$basetexture2', None)
        if texture_path is not None:
            return self.load_texture_or_default(texture_path, (0.3, 0.3, 0.0, 1.0))
        return None

    @property
    def bumpmap(self):
        texture_path = self._vmt.get_string('$bumpmap', None)
        if texture_path is not None:
            image = self.load_texture_or_default(texture_path, (0.6, 0.0, 0.6, 1.0))
            image.colorspace_settings.is_data = True
            image.colorspace_settings.name = 'Non-Color'
            if self.ssbump:
                image = self.convert_ssbump(image)
            image = self.convert_normalmap(image)
            return image
        return None

    @property
    def bumpmap2(self):
        texture_path = self._vmt.get_string('$bumpmap2', None)
        if texture_path is not None:
            image = self.load_texture_or_default(texture_path, (0.6, 0.6, 0.0, 1.0))
            image.colorspace_settings.is_data = True
            image.colorspace_settings.name = 'Non-Color'
            if self.ssbump:
                image = self.convert_ssbump(image)
            image = self.convert_normalmap(image)
            return image
        return None

    @property
    def selfillum(self):
        return self._vmt.get_int('$selfillum', 0) == 1

    @property
    def ssbump(self):
        return self._vmt.get_int('$ssbump', 0) == 1

    @property
    def translucent(self):
        return self._vmt.get_int('$translucent', 0) == 1

    @property
    def alpha(self):
        return self._vmt.get_float('alpha', 1.0)

    @property
    def phong(self):
        return self._vmt.get_int('$phong', 0) == 1

    @property
    def phongboost(self):
        return self._vmt.get_float('$phongboost', 1)

    @property
    def seamless_scale(self):
        return self._vmt.get_float('$seamless_scale', 1)

    def create_nodes(self, material: bpy.types.Material, extra_parameters: dict[ExtraMaterialParameters, Any]):
        material_output = self.create_node(Nodes.ShaderNodeOutputMaterial)
        shader = self.create_node(Nodes.ShaderNodeBsdfPrincipled, self.SHADER)
        self.connect_nodes(shader.outputs['BSDF'], material_output.inputs['Surface'])

        uv_node = self.create_node(Nodes.ShaderNodeUVMap)

        uv_out = uv_node.outputs[0]

        # if self.seamless_scale != 1.0:
        #     vector_mult = self.create_node(Nodes.ShaderNodeVectorMath)
        #     vector_mult.operation = 'MULTIPLY'
        #     vector_mult.inputs[1].default_value = (1, 1, 0)
        #     self.connect_nodes(uv_out, vector_mult.inputs[0])
        #     uv_out = vector_mult.outputs[0]

        basetexture = self.basetexture
        basetexture2 = self.basetexture2
        blendmodulatetexture = self.blendmodulatetexture

        if basetexture and basetexture2:
            vertex_color = self.create_node(Nodes.ShaderNodeVertexColor)

            color_mix = self.create_node(Nodes.ShaderNodeMixRGB)

            bs_node = self.create_texture_node(basetexture, name='$basetexture')
            self.connect_nodes(uv_out, bs_node.inputs[0])
            bs_socket = bs_node.outputs[0]

            bs_node2 = self.create_texture_node(basetexture2, name='$basetexture2')
            self.connect_nodes(uv_out, bs_node2.inputs[0])
            bs_socket2 = bs_node2.outputs[0]

            if blendmodulatetexture != None:
                sep_rgb = self.create_node(Nodes.ShaderNodeSeparateColor)
                sep_rgb.mode = "RGB"
                sub = self.create_node(Nodes.ShaderNodeMath)
                sub.operation = 'SUBTRACT'
                sub_bias = self.create_node(Nodes.ShaderNodeMath)
                sub_bias.operation = 'SUBTRACT'
                sub_bias.inputs[1].default_value = 0.001
                add = self.create_node(Nodes.ShaderNodeMath)
                add.operation = 'ADD'
                maprange = self.create_node(Nodes.ShaderNodeMapRange)
                maprange.interpolation_type = 'SMOOTHSTEP'

                self.connect_nodes(sep_rgb.outputs[1], sub.inputs[0])
                self.connect_nodes(sep_rgb.outputs[0], sub.inputs[1])
                self.connect_nodes(sep_rgb.outputs[0], add.inputs[0])
                self.connect_nodes(sep_rgb.outputs[1], add.inputs[1])
                self.connect_nodes(sub.outputs[0], sub_bias.inputs[0])
                self.connect_nodes(sub_bias.outputs[0], maprange.inputs[1])
                self.connect_nodes(add.outputs[0], maprange.inputs[2])
                self.connect_nodes(vertex_color.outputs[0], maprange.inputs[0])
                self.connect_nodes(maprange.outputs[0], color_mix.inputs['Fac'])
                self.create_and_connect_texture_node(blendmodulatetexture, sep_rgb.inputs[0],
                                                     name='$blendmodulatedecal')

            else:
                self.connect_nodes(vertex_color.outputs['Color'], color_mix.inputs['Fac'])
            color_mix.blend_type = 'MIX'

            albedo = color_mix.outputs[0]

            if self.detail:
                if self.detail2:
                    albedo, detail = self.handle_detail(color_mix.inputs[1], bs_socket, uv_node=None)
                    albedo, detail2 = self.handle_detail2(color_mix.inputs[2], bs_socket2, uv_node=None)
                    self.connect_nodes(color_mix.outputs['Color'], shader.inputs['Base Color'])
                else:
                    albedo, detail = self.handle_detail(shader.inputs['Base Color'], albedo, uv_node=None)
                    self.connect_nodes(bs_socket, color_mix.inputs[1])
                    self.connect_nodes(bs_socket2, color_mix.inputs[2])
            else:
                self.connect_nodes(bs_socket, color_mix.inputs[1])
                self.connect_nodes(bs_socket2, color_mix.inputs[2])
                self.connect_nodes(color_mix.outputs['Color'], shader.inputs['Base Color'])
        bumpmap = self.bumpmap
        bumpmap2 = self.bumpmap2

        if bumpmap and bumpmap2:
            color_mix_norm = self.create_node(Nodes.ShaderNodeMixRGB)
            color_mix_norm.blend_type = 'MIX'

            self.create_and_connect_texture_node(bumpmap, color_mix_norm.inputs['Color1'], name='$bumpmap', uv_out=uv_out)
            self.create_and_connect_texture_node(bumpmap2, color_mix_norm.inputs['Color2'], name='$bumpmap2', uv_out=uv_out)

            if blendmodulatetexture != None:
                self.connect_nodes(maprange.outputs[0], color_mix_norm.inputs['Fac'])
            else:
                self.connect_nodes(vertex_color.outputs[0], color_mix_norm.inputs['Fac'])

            norm_map = self.create_node(Nodes.ShaderNodeNormalMap)

            self.connect_nodes(color_mix_norm.outputs[0], norm_map.inputs['Color'])
            self.connect_nodes(norm_map.outputs[0], shader.inputs['Normal'])

        if not self.phong:
            if is_blender_4():
                shader.inputs['Specular IOR Level'].default_value = 0
            else:
                shader.inputs['Specular'].default_value = 0
