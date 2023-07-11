from __future__ import annotations

import numpy as np

from .skeleton import Skeleton
from pymovis.utils import npconst
from pymovis.ops import mathops, rotation

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
        local_Qs: np.ndarray or list[np.ndarray] = None,
        root_p  : np.ndarray = None,
    ):
        self.skeleton = skeleton
        self.local_Qs = np.array(local_Qs, dtype=np.float32) if local_Qs is not None else np.stack([npconst.Q_IDENTITY() for _ in range(skeleton.num_joints())], axis=0)
        self.root_p   = np.array(root_p, dtype=np.float32) if root_p is not None else self.skeleton.joints[0].local_p

        # check shapes
        if self.skeleton.num_joints() == 0:
            raise ValueError("Cannot create a pose for an empty skeleton.")
        if self.local_Qs.shape != (self.skeleton.num_joints(), 4):
            raise ValueError(f"local_R.shape must be ({skeleton.num_joints()}, 4), but got {local_Qs.shape}")
        if self.root_p.shape != (3,):
            raise ValueError(f"root_p.shape must be (3,), but got {root_p.shape}")
    
    def pre_xforms(self):
        pre_xforms = self.skeleton.pre_xforms()
        pre_xforms[0, :3, 3] = self.root_p
        return pre_xforms
    
    def root_pre_xform(self):
        root_pre_xform = self.skeleton.root_pre_xform()
        root_pre_xform[:3, 3] = self.root_p
        return root_pre_xform

    def local_xforms(self):
        local_Rs = rotation.Q_to_R(self.local_Qs)

        local_xforms = np.stack([np.identity(4, dtype=np.float32) for _ in range(self.skeleton.num_joints())], axis=0)
        for i in range(self.skeleton.num_joints()):
            local_xforms[i, :3, :3] = local_Rs[i]
            
        return local_xforms
    
    def root_local_xform(self):
        root_local_xform = np.identity(4, dtype=np.float32)
        root_local_xform[:3, :3] = rotation.Q_to_R(self.local_Qs[0])
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
            axis = mathops.normalize(np.cross(npconst.UP(), target_dir))
            angle = mathops.signed_angle(npconst.UP(), target_dir, axis)

            skeleton_xforms[i-1, :3, :3] = rotation.A_to_R(angle, axis)
            skeleton_xforms[i-1, :3,  3] = (parent_pos + global_xforms[i, :3, 3]) / 2
        
        return skeleton_xforms
    
    @classmethod
    def from_bvh(cls, skeleton, local_E, order, root_p):
        local_Qs = rotation.E_to_Q(local_E, order, radians=False)
        return cls(skeleton, local_Qs, root_p)
    
    @classmethod
    def from_numpy(cls, skeleton, local_R, root_p):
        return cls(skeleton, local_R, root_p)

    @classmethod
    def from_torch(cls, skeleton, local_R, root_p):
        return cls(skeleton, local_R.cpu().numpy(), root_p.cpu().numpy())

    # """ Base position and directions (on xz plane, equivalent to horizontal plane) """
    # @property
    # def base(self):
    #     return self.root_p * npconst.XZ()
    
    # @property
    # def forward(self):
    #     return mathops.normalize((self.local_R[0] @ self.skeleton.v_forward) * npconst.XZ())
    
    # @property
    # def up(self):
    #     return npconst.UP()
    
    # @property
    # def left(self):
    #     return mathops.normalize(np.cross(self.up, self.forward))

    # """ Manipulation functions """
    # def set_root_p(self, root_p):
    #     delta = root_p - self.root_p
    #     self.translate_root_p(delta)

    # def translate_root_p(self, delta):
    #     self.root_p += delta
    #     self.global_p += delta
    
    # def rotate_root(self, delta):
    #     self.local_R[0] = np.matmul(delta, self.local_R[0])
    #     self.global_R, self.global_p = motionops.R_fk(self.local_R, self.root_p, self.skeleton)
    
    # def update(self):
    #     """ Called whenever the pose is modified """
    #     self.global_R, self.global_p = motionops.R_fk(self.local_R, self.root_p, self.skeleton)

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