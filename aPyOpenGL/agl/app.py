from enum import Enum
from OpenGL.GL import *

import glfw
import os
import datetime
import cv2
import numpy as np
import glm

from .motion import Motion
from .camera import Camera
from .light  import Light, DirectionalLight, PointLight
from .render import Render
from .model  import Model
from .ui     import UI

""" Base class for all applications """
class App:
    def __init__(
        self,
        camera = Camera(),
        lights = [DirectionalLight(), DirectionalLight(direction=glm.vec3(1, -2, 1), intensity=0.2)],
    ):
        # render settings
        self.camera = camera
        self.lights = lights
        
        # display options
        self.width, self.height = 1920, 1080
        self.io = self.IO()
        self.ui = UI()
        self.capture_path = os.path.join("capture", str(datetime.date.today()))
        self.window = self.init_glfw()

        # play options
        self.fps = 30
        self.frame = 0
        self.prev_frame = -1
        self.playing = True

        # capture
        self.captures = []
        self.record_mode  = App.RecordMode.eNONE

        # auxiliary - render fps
        self.start_time = 0
        self.end_time = 0
        self.frame_count = 0
        self.render_fps = 30

    class IO:
        def __init__(self):
            self.last_mouse_x = 0
            self.last_mouse_y = 0
            self.mouse_middle_down = False
            self.mouse_left_down = False
    
    class RecordMode(Enum):
        eNONE           = 0
        eSECTION_TO_VID = 1
        # eSECTION_TO_IMG = 3

    def init_glfw(self):
        glfw.init()
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.SAMPLES, 4)

        # create window
        window = glfw.create_window(self.width, self.height, "pymovis", None, None)
        glfw.make_context_current(window)

        if not window:
            glfw.terminate()
            raise Exception("Failed to create GLFW window")
        
        glfw.make_context_current(window)
        glfw.swap_interval(1)

        # callbacks
        glfw.set_framebuffer_size_callback(window, self.on_resize)
        glfw.set_key_callback(window, self.key_callback)
        glfw.set_cursor_pos_callback(window, self.mouse_callback)
        glfw.set_mouse_button_callback(window, self.mouse_button_callback)
        glfw.set_scroll_callback(window, self.scroll_callback)
        glfw.set_error_callback(self.on_error)
        
        # global OpenGL state
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LEQUAL)
        glCullFace(GL_BACK)
        # glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        # intialize shaders
        Render.initialize_shaders()
        glViewport(0, 0, self.width, self.height)

        return window

    """ Cotinue on these methods to add custom rendering scripts """
    def start(self):
        # render options
        self.grid = Render.plane(200, 200).albedo(0.15).floor(True)
        self.axis = Render.axis()
        self.render_fps_text = Render.text_on_screen().position([0, 0.95, 0]).scale(0.3)

        # ui
        self.ui.add_menu("App")
        self.ui.add_menu_item("App", "Play / Pause", self.toggle_play, key=glfw.KEY_SPACE)
        self.ui.add_menu_item("App", "Axis", self.axis.switch_visible, key=glfw.KEY_A)
        self.ui.add_menu_item("App", "Grid", self.grid.switch_visible, key=glfw.KEY_G)
        self.ui.add_menu_item("App", "FPS", self.render_fps_text.switch_visible, key=glfw.KEY_F)

    def update(self):
        # time setting
        if self.record_mode == App.RecordMode.eNONE:
            if self.playing:
                self.frame = int(glfw.get_time() * self.fps)
            else:
                glfw.set_time(self.frame / self.fps)
        else:
            self.frame = int(glfw.get_time() * self.fps)
            if self.frame - self.prev_frame > 1:
                self.frame = self.prev_frame + 1
                glfw.set_time(self.frame / self.fps)

    def late_update(self):
        # capture video
        if self.record_mode != App.RecordMode.eNONE:
            if (self.frame - self.prev_frame) == 1:
                self.captures.append(self.capture_screen())
                
        # update previous frame
        self.prev_frame = self.frame

        # render fps
        self.frame_count += 1
        if self.frame_count == 100:
            self.end_time = glfw.get_time()
            self.render_fps = self.frame_count / (self.end_time - self.start_time)
            self.frame_count = 0
            self.start_time = glfw.get_time()

    def render(self):
        self.axis.draw()
        self.grid.draw()

    def render_text(self):
        self.render_fps_text.text(f"Render FPS: {self.render_fps:.2f}").draw()

    def render_xray(self):
        pass
    
    def terminate(self):
        pass

    """ Callback functions for glfw and camera control """
    def key_callback(self, window, key, scancode, action, mods):
        if action != glfw.PRESS:
            return

        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)
            Render.clear()
        elif key == glfw.KEY_F1:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        elif key == glfw.KEY_F2:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # camera control
        elif key == glfw.KEY_V:
            self.camera.switch_projection()

        # capture
        elif key == glfw.KEY_F5:
            self.save_image(self.capture_screen())
        elif key == glfw.KEY_F6:
            if self.record_mode == App.RecordMode.eSECTION_TO_VID:
                self.save_video()
                self.captures = []
                self.record_mode = App.RecordMode.eNONE
            elif self.record_mode == App.RecordMode.eNONE:
                self.record_mode = App.RecordMode.eSECTION_TO_VID

        # frame control
        elif self.record_mode == App.RecordMode.eNONE:
            if key == glfw.KEY_LEFT_BRACKET:
                self.move_frame(-1)
            elif key == glfw.KEY_RIGHT_BRACKET:
                self.move_frame(+1)
            elif key == glfw.KEY_LEFT:
                self.move_frame(-self.fps)
            elif key == glfw.KEY_RIGHT:
                self.move_frame(+self.fps)

        self.ui.key_callback(window, key, scancode, action, mods)
        
    def mouse_callback(self, window, xpos, ypos):
        offset_x = xpos - self.io.last_mouse_x
        offset_y = self.io.last_mouse_y - ypos

        self.io.last_mouse_x = xpos
        self.io.last_mouse_y = ypos

        left_alt_pressed    = (glfw.get_key(window, glfw.KEY_LEFT_ALT) == glfw.PRESS)
        if left_alt_pressed and self.io.mouse_middle_down:
            self.camera.track(offset_x, offset_y)
        elif left_alt_pressed and self.io.mouse_left_down:
            self.camera.tumble(offset_x, offset_y)

    def mouse_button_callback(self, window, button, action, mods):
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self.io.mouse_left_down = True
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
            self.io.mouse_left_down = False
        if button == glfw.MOUSE_BUTTON_MIDDLE and action == glfw.PRESS:
            self.io.mouse_middle_down = True
        if button == glfw.MOUSE_BUTTON_MIDDLE and action == glfw.RELEASE:
            self.io.mouse_middle_down = False

    def scroll_callback(self, window, x_offset, y_offset):
        left_alt_pressed = (glfw.get_key(window, glfw.KEY_LEFT_ALT) == glfw.PRESS)
        if left_alt_pressed:
            self.camera.dolly(y_offset)
        else:
            self.camera.zoom(y_offset)

    def on_error(self, error, desc):
        pass

    def on_resize(self, window, width, height):
        glViewport(0, 0, width, height)
        self.width, self.height = width, height
        self.ui.resize_font(width, height)
    
    """ Capture functions """
    def capture_screen(self):
        viewport = glGetIntegerv(GL_VIEWPORT)
        x, y, *_ = viewport
        
        glReadBuffer(GL_FRONT)
        data = glReadPixels(x, y, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE)
        pixels = np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)
        pixels = np.flip(pixels[:-self.ui.get_menu_height()], axis=0)
        image = cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR)
        return image
    
    def save_image(self, image):
        image_dir = os.path.join(self.capture_path, "images")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        
        image_path = os.path.join(image_dir, datetime.datetime.now().strftime("%H-%M-%S") + ".png")
        cv2.imwrite(image_path, image)
    
    def save_video(self):
        video_dir = os.path.join(self.capture_path, "videos")
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
        
        video_path = os.path.join(video_dir, datetime.datetime.now().strftime("%H-%M-%S") + ".mp4")
        height, width, _ = self.captures[0].shape
        
        video = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"mp4v"), self.fps, (width, height))
        for image in self.captures:
            video.write(image)
        video.release()

        glfw.set_time(self.frame / self.fps)
    
    """ UI functions """
    def process_inputs(self):
        self.ui.process_inputs()

    def initialize_ui(self):
        self.ui.initialize(self.window)
    
    def render_ui(self):
        self.ui.render()
    
    def terminate_ui(self):
        self.ui.terminate()

    """ Auxiliary functions """
    def toggle_play(self):
        self.playing = not self.playing
    
    def move_frame(self, offset):
        self.frame = int(max(0, self.frame + offset))
        glfw.set_time(self.frame / self.fps)