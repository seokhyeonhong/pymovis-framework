from OpenGL.GL import *

import glfw
from pymovis.vis.camera import Camera
from pymovis.vis.light import DirectionalLight, PointLight

class App:
    def __init__(
        self,
        camera = Camera(),
        light = DirectionalLight(),
        capture=False,
        width=1920,
        height=1080,
        capture_path="capture",
    ):
        self.camera = camera
        self.light = light
        self.capture = capture
        self.capture_path = capture_path
        self.width = width
        self.height = height
        self.io = self.IO()

    class IO:
        def __init__(self):
            self.capture = False
            self.last_mouse_x = 0
            self.last_mouse_y = 0
            self.mouse_middle_down = False
            self.mouse_left_down = False
    
    """
    Override these methods to add custom rendering code.
    """
    def start(self):
        pass

    def update(self):
        pass

    def late_update(self):
        pass

    def render(self):
        pass
    
    def render_xray(self):
        pass
    
    """
    Callback functions for glfw and camera control
    """
    def key_callback(self, window, key, scancode, action, mods):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(window, True)
        # elif key == glfw.KEY_F1 and action == glfw.PRESS:
        #     Render.set_render_mode(RenderMode.PHONG)
        # elif key == glfw.KEY_F2 and action == glfw.PRESS:
        #     Render.set_render_mode(RenderMode.WIREFRAME)
        elif key == glfw.KEY_F5 and action == glfw.PRESS:
            self._capture = True
        elif key == glfw.KEY_F6 and action == glfw.PRESS:
            self._capture = False
        elif key == glfw.KEY_V and action == glfw.PRESS:
            self.camera.is_perspective = not self.camera.is_perspective
        
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

    def scroll_callback(self, window, xoffset, yoffset):
        left_alt_pressed = (glfw.get_key(window, glfw.KEY_LEFT_ALT) == glfw.PRESS)
        if left_alt_pressed:
            self.camera.dolly(yoffset)
        else:
            self.camera.zoom(yoffset)

    def on_error(self, error, description):
        pass

    def on_resize(self, window, width, height):
        glViewport(0, 0, width, height)
        self.width = width
        self.height = height