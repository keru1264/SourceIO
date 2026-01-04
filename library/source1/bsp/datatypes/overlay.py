from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from SourceIO.library.shared.types import Vector2, Vector3
from SourceIO.library.source1.bsp.bsp_file import VBSPFile
from SourceIO.library.utils.file_utils import Buffer


@dataclass(slots=True)
class Overlay:
    id: int
    tex_info: int
    face_count_and_render_order: int
    ofaces: tuple[int, ...]
    u: Vector2[float]
    v: Vector2[float]
    uv_points: npt.NDArray[np.float32]
    origin: Vector3[float]
    normal: Vector3[float]

    @property
    def face_count(self):
        return self.face_count_and_render_order & 0x3FFF

    @property
    def render_order(self):
        return self.face_count_and_render_order >> 14

    @property
    def face_ids(self):
        return self.ofaces[:self.face_count]

    @property
    def basis(self):
        # Basis U is encoded in z components of uv_points 0, 1, 2
        basis_u = np.array([
            self.uv_points[0, 2],  # uv_points[0].z
            self.uv_points[1, 2],  # uv_points[1].z
            self.uv_points[2, 2],  # uv_points[2].z
        ], dtype=np.float32)
        
        # Basis V = cross(normal, basis_u), then normalize
        normal = np.array(self.normal, dtype=np.float32)
        basis_v = np.cross(normal, basis_u)
        basis_v_len = np.linalg.norm(basis_v)
        if basis_v_len > 1e-6:
            basis_v /= basis_v_len
        
        # Check flip flag in uv_points[3].z
        if self.uv_points[3, 2] == 1.0:
            basis_v = -basis_v
        
        return np.array([basis_u, basis_v], dtype=np.float32)

    @property
    def plane_points(self):
        # UV points with z cleared (z was used for basis encoding)
        points = np.zeros((4, 2), dtype=np.float32)
        points[0] = self.uv_points[0, :2]  # x, y only
        points[1] = self.uv_points[1, :2]
        points[2] = self.uv_points[2, :2]
        points[3] = self.uv_points[3, :2]
        return points

    @property
    def plane(self):
        # UV coordinates for texture mapping
        dst_uv = np.zeros((4, 2), dtype=np.float32)
        dst_uv[0] = self.u[0], self.v[0]
        dst_uv[1] = self.u[0], self.v[1]
        dst_uv[2] = self.u[1], self.v[1]
        dst_uv[3] = self.u[1], self.v[0]
        
        # World positions: origin + uv_point.x * basis_u + uv_point.y * basis_v
        origin = np.array(self.origin, dtype=np.float32)
        basis = self.basis
        plane_pts = self.plane_points
        
        dst_pos = np.zeros((4, 3), dtype=np.float32)
        for n in range(4):
            dst_pos[n] = origin + basis[0] * plane_pts[n, 0] + basis[1] * plane_pts[n, 1]
        
        return dst_pos, dst_uv

    @classmethod
    def from_buffer(cls, buffer: Buffer, version: int, bsp: VBSPFile):
        id = buffer.read_int32()
        tex_info = buffer.read_int16()
        face_count_and_render_order = buffer.read_uint16()
        ofaces = buffer.read_fmt('64i')
        u = buffer.read_fmt('ff')
        v = buffer.read_fmt('ff')
        uv_points = np.array(buffer.read_fmt('12f'), dtype=np.float32).reshape((4, 3))
        origin = buffer.read_fmt('fff')
        normal = buffer.read_fmt('fff')
        return cls(id, tex_info, face_count_and_render_order, ofaces, u, v, uv_points, origin, normal)

class VOverlay(Overlay):
    @classmethod
    def from_buffer(cls, buffer: Buffer, version: int, bsp: VBSPFile):
        id = buffer.read_int32()
        tex_info = buffer.read_int32()
        face_count_and_render_order = buffer.read_uint32()
        ofaces = buffer.read_fmt('64i')
        u = buffer.read_fmt('ff')
        v = buffer.read_fmt('ff')
        uv_points = np.array(buffer.read_fmt('12f'), dtype=np.float32).reshape((4, 3))
        origin = buffer.read_fmt('fff')
        normal = buffer.read_fmt('fff')

        return cls(id, tex_info, face_count_and_render_order, ofaces, u, v, uv_points, origin, normal)
