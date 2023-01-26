import torch
import glfw
import glm
import copy

import numpy as np

from pymovis.motion.data import bvh, fbx
from pymovis.motion.core import Motion

from pymovis.vis.render import Render
from pymovis.vis.app import App, MotionApp
from pymovis.vis.appmanager import AppManager
from pymovis.vis.model import Model
from pymovis.vis.heightmap import Heightmap

class SimpleApp(App):
    def __init__(self):
        super().__init__()
        self.m = Render.plane()
    
    def render(self):
        self.m.draw()

class MyApp(MotionApp):
    def __init__(self, motion: Motion, model, vel_factor):
        super().__init__(motion, model)
        self.vel_factor = vel_factor

        self.left_leg_idx   = self.motion.skeleton.idx_by_name["LeftUpLeg"]
        self.left_foot_idx  = self.motion.skeleton.idx_by_name["LeftFoot"]
        self.right_leg_idx  = self.motion.skeleton.idx_by_name["RightUpLeg"]
        self.right_foot_idx = self.motion.skeleton.idx_by_name["RightFoot"]

        # heightmap
        # self.heightmap = Heightmap.load_from_file("./data/heightmaps/hmap_010_smooth.txt")
        # self.heightmap_mesh = Render.mesh(self.heightmap.vao)#.set_albedo([1, 0, 0]).set_scale(0.000001)#.set_texture("grid.png").set_uv_repeat(0.1)

        # grid for environment map
        grid_x = np.linspace(-1, 1, 11)
        grid_z = np.linspace(-1, 1, 11)
        grid_x, grid_z = np.meshgrid(grid_x, grid_z)
        grid_y = np.zeros_like(grid_x)
        self.env_map = np.stack([grid_x, grid_y, grid_z], axis=-1)
        self.sphere = Render.sphere(0.05).set_albedo([0, 1, 0])
        # self.cubemap = Render.cubemap("skybox")

        # velocity-based locomotion scaling
        self.scale_motion()
    
    def scale_motion(self):
        self.dupl_motions = []
        for vi, vf in enumerate(self.vel_factor):
            dupl_motion = copy.deepcopy(self.motion)

            for i, pose in enumerate(self.motion.poses[1:], start=1):
                base_v = vf * (self.motion.poses[i].base - self.motion.poses[i-1].base)
                root_p = dupl_motion.poses[i-1].root_p + base_v
                root_p[1] = self.motion.poses[i].root_p[1]
                dupl_motion.poses[i].set_root_p(root_p)

                root_to_left_foot  = pose.global_p[self.left_foot_idx] - pose.root_p
                root_to_right_foot = pose.global_p[self.right_foot_idx] - pose.root_p

                root_to_left_foot  = root_to_left_foot * np.array([0, 1, 0])  + (root_to_left_foot * np.array([1, 0, 1])) * vf
                root_to_right_foot = root_to_right_foot * np.array([0, 1, 0]) + (root_to_right_foot * np.array([1, 0, 1])) * vf

                dupl_motion.poses[i].two_bone_ik(self.left_leg_idx, self.left_foot_idx,   root_to_left_foot + dupl_motion.poses[i].root_p)
                dupl_motion.poses[i].two_bone_ik(self.right_leg_idx, self.right_foot_idx, root_to_right_foot + dupl_motion.poses[i].root_p)

            self.dupl_motions.append(dupl_motion)

        self.motions = [*self.dupl_motions[:1], self.motion, *self.dupl_motions[1:]]
        for i, motion in enumerate(self.motions):
            for pose in motion.poses:
                pose.translate_root_p(np.array([2*i-2, 0, 0]))

    def render(self):
        super().render()
        # self.heightmap_mesh.draw()
        # r = np.stack([self.motion.poses[self.frame].left, self.motion.poses[self.frame].up, self.motion.poses[self.frame].forward], axis=-1)
        # env_map = np.einsum("ij,abj->abi", r, self.env_map) + self.motion.poses[self.frame].base
        # env_map = np.reshape(env_map, [-1, 3])
        # env_map[..., 1] = self.heightmap.sample_height(env_map[..., 0], env_map[..., 2])
        # for e in env_map:
        #     self.sphere.set_position(e).draw()
        
        for i, motion in enumerate(self.motions):
            self.model.set_pose_by_source(motion.poses[self.frame])
            Render.model(self.model).draw()
            if i == 0:
                albedo = [1, 0.2, 0.2]
            elif i == 1:
                albedo = [0.2, 1, 0.2]
            else:
                albedo = [0.2, 0.2, 1]
            self.render_xray(motion.poses[self.frame], albedo)


if __name__ == "__main__":
    app_manager = AppManager()

    motion = bvh.load("./data/animations/jumpy/PFNN_NewCaptures03_000_mirror.bvh", v_forward=[0, 1, 0], v_up=[1, 0, 0], to_meter=0.01)
    model = fbx.FBX("./data/models/model_skeleton.fbx").model()
    motion.align_by_frame(0)
    app = MyApp(motion, model, [0.8, 1.2])
    # app = MyApp(motion, model, [0.8, 0.9, 1.1, 1.2])
    app_manager.run(app)