from manim import *

class Hello(Scene):
    def construct(self):
        t = Text("Hello, Manim!")
        self.play(Write(t))
        self.wait(0.5)
