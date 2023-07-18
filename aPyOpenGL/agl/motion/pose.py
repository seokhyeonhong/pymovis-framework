from __future__ import annotations

import numpy as np

from .skeleton import Skeleton
from aPyOpenGL.ops import mathops
import aPyOpenGL.transforms as T

class Pose:
    """
    Represents a pose of a skeleton.
    It contains the local rotation matrices of each joint and the root position.

    global_xforms[i] = global_xforms[parent_idx[i]] @ pre_xform[i] @ local_rots[i]

    Attributes:
        skeleton (Skeleton)     : The skeleton that this pose belongs to.
        local_R  (numpy.ndarray): The local rotation matrices of the joints.
        root_p   (numpy.ndarray): The root position.
    """
    def __init__(
        self,
        skeleton: Skeleton,
        local_quats: np.ndarray or list[np.ndarray] = None,
        root_pos: np.ndarray = None,
    ):
        # set attributes
        self.skeleton = skeleton
        self.local_quats = np.stack([T.n_quat.identity()] * skeleton.num_joints(), axis=0) if local_quats is None else np.array(local_quats)
        self.root_pos = np.zeros(3) if root_pos is None else root_pos
        
        # check shapes
        if self.skeleton.num_joints() == 0:
            raise ValueError("Cannot create a pose for an empty skeleton.")
    
    def pre_xforms(self):
        pre_xforms = self.skeleton.pre_xforms()
        pre_xforms[0, :3, 3] = self.root_pos
        return pre_xforms
    
    def root_pre_xform(self):
        root_pre_xform = self.skeleton.root_pre_xform()
        root_pre_xform[:3, 3] = self.root_pos
        return root_pre_xform

    def local_xforms(self):
        local_Rs = T.n_quat.to_rotmat(self.local_quats)

        local_xforms = np.stack([np.identity(4, dtype=np.float32) for _ in range(self.skeleton.num_joints())], axis=0)
        for i in range(self.skeleton.num_joints()):
            local_xforms[i, :3, :3] = local_Rs[i]
            
        return local_xforms
    
    def root_local_xform(self):
        root_local_xform = np.identity(4, dtype=np.float32)
        root_local_xform[:3, :3] = T.n_quat.to_rotmat(self.local_quats[0])
        return root_local_xform
    
    def global_xforms(self):
        noj = self.skeleton.num_joints()
        pre_xforms = self.pre_xforms()
        local_xforms = self.local_xforms()

        global_xforms = np.stack([np.identity(4, dtype=np.float32) for _ in range(noj)], axis=0)
        global_xforms[0] = pre_xforms[0] @ local_xforms[0]
        for i in range(1, noj):
            global_xforms[i] = global_xforms[self.skeleton.parent_idx[i]] @ pre_xforms[i] @ local_xforms[i]

        return global_xforms
    
    def root_global_xform(self):
        root_pre_xform = self.root_pre_xform()
        root_local_xform = self.root_local_xform()
        return root_pre_xform @ root_local_xform
    
    def skeleton_xforms(self):
        noj = self.skeleton.num_joints()
        global_xforms = self.global_xforms()

        skeleton_xforms = np.stack([np.identity(4, dtype=np.float32) for _ in range(noj - 1)], axis=0)
        for i in range(1, noj):
            parent_pos = global_xforms[self.skeleton.parent_idx[i], :3, 3]
            
            target_dir = mathops.normalize(global_xforms[i, :3, 3] - parent_pos)

            axis = np.cross(np.array([0, 1, 0]), target_dir)
            axis = axis / (np.linalg.norm(axis, axis=-1, keepdims=True) + 1e-8)
            angle = np.arccos(np.dot(np.array([0, 1, 0]), target_dir))

            skeleton_xforms[i-1, :3, :3] = T.n_aaxis.to_rotmat(angle[..., None] * axis)
            skeleton_xforms[i-1, :3,  3] = (parent_pos + global_xforms[i, :3, 3]) / 2
        
        return skeleton_xforms
    
    @classmethod
    def from_numpy(cls, skeleton, local_R, root_p):
        return cls(skeleton, local_R, root_p)

    @classmethod
    def from_torch(cls, skeleton, local_R, root_p):
        return cls(skeleton, local_R.cpu().numpy(), root_p.cpu().numpy())

    # """ IK functions """
    # def two_bone_ik(self, base_idx, effector_idx, target_p, eps=1e-8, facing="forward"):
    #     mid_idx = self.skeleton.parent_idx[effector_idx]
    #     if self.skeleton.parent_idx[mid_idx] != base_idx:
    #         raise ValueError(f"{base_idx} and {effector_idx} are not in a two bone IK hierarchy")

    #     a = self.global_p[base_idx]
    #     b = self.global_p[mid_idx]
    #     c = self.global_p[effector_idx]

    #     global_a_R = self.global_R[base_idx]
    #     global_b_R = self.global_R[mid_idx]

    #     lab = np.linalg.norm(b - a)
    #     lcb = np.linalg.norm(b - c)
    #     lat = np.clip(np.linalg.norm(target_p - a), eps, lab + lcb - eps)

    #     ac_ab_0 = np.arccos(np.clip(np.dot(mathops.normalize(c - a), mathops.normalize(b - a)), -1, 1))
    #     ba_bc_0 = np.arccos(np.clip(np.dot(mathops.normalize(a - b), mathops.normalize(c - b)), -1, 1))
    #     ac_at_0 = np.arccos(np.clip(np.dot(mathops.normalize(c - a), mathops.normalize(target_p - a)), -1, 1))

    #     ac_ab_1 = np.arccos(np.clip((lcb*lcb - lab*lab - lat*lat) / (-2*lab*lat), -1, 1))
    #     ba_bc_1 = np.arccos(np.clip((lat*lat - lab*lab - lcb*lcb) / (-2*lab*lcb), -1, 1))

    #     axis_0 = mathops.normalize(np.cross(c - a, self.forward if facing == "forward" else -self.forward))
    #     axis_1 = mathops.normalize(np.cross(c - a, target_p - a))

    #     r0 = rotation.A_to_R(ac_ab_1 - ac_ab_0, rotation.R_inv(global_a_R) @ axis_0)
    #     r1 = rotation.A_to_R(ba_bc_1 - ba_bc_0, rotation.R_inv(global_b_R) @ axis_0)
    #     r2 = rotation.A_to_R(ac_at_0, rotation.R_inv(global_a_R) @ axis_1)

    #     self.local_R[base_idx] = self.local_R[base_idx] @ r0 @ r2
    #     self.local_R[mid_idx] = self.local_R[mid_idx] @ r1

    #     self.update()