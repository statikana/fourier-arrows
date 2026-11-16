from __future__ import annotations
from sympy import sin, cos, tan, latex, Expr, I
from manim import *  # type: ignore
from src.expression import Term, t, Expression

a = 1
kx = 5
ky = 3

# Parametric curve over t in [0, 1]
x = t
y = 2 * t
 
# probably don't change this
f_t = x + I * y
n_terms = 11  # must be odd for symmetric negative/positive frequencies
expr = Expression(f_t=f_t, n_terms=n_terms)

class FourierConstruct(MovingCameraScene):
    """Renders rotating Fourier epicycle arrows approximating f_t."""
    def construct(self):
        font_size = DEFAULT_FONT_SIZE // 1.5
        expr.set_coefs()
        terms = expr.terms
        print(terms)
        print(expr.at(0), expr.at(.5))
        # term 0 always first, then -1, +1, ...
        terms.sort(key=lambda t: (abs(t.n), t.n))

        arrows = self.make_arrows()

        run_time = 10
        loops = 1

        # typing for pyright
        self.camera: MovingCamera

        def update_arrow(mobject: Mobject, dt: float) -> None:
            arrow: ChainedArrow = mobject  # type: ignore
            if arrow.prev is None:
                # the first arrow is constant
                return


            prev_end = arrow.prev.get_end()
            b_start, b_end = arrow.get_start_and_end()
            
            # delta keeps the direction and length of the
            # arrow constant while rotating
            delta = b_end - b_start

            new_start = prev_end
            new_end = prev_end + delta
            arrow.put_start_and_end_on(new_start, new_end)

            arrow.rotate(
                angle=TAU * arrow.rate * dt / run_time,  # moves .rate rotations every second
                about_point=new_start,
            )
            # move the arrow's associated circle as well
            arrow.circle.move_to(new_start)

        def update_time(mobject: Mobject) -> None:
            t = round((self.time / run_time) % 1, 3)
            # Drop leading "0" so values render as ".000" .. ".999"
            string = str(t)[1:].ljust(4, '0')
            new = Text("Time: " + string, font="Cascadia Mono", font_size=font_size)

            new.next_to(function_label, DOWN, aligned_edge=LEFT)

            timer.become(new)
        
        
        # Apply updaters
        circles = []
        for arrow in arrows:
            arrow.add_updater(update_arrow)
            circles.append(arrow.circle)


        # ParametricFunction shape
        function = ParametricFunction(
            function=lambda time: (float(x.subs(t, time)), float(y.subs(t, time)), 0),  # type: ignore
            color=BLUE,
            stroke_width=2,
            stroke_opacity=.2
        )


        main_elements = VGroup(*arrows, *circles, function)


        # X and Y function labels
        x_latex, y_latex = map(self.func_to_latex, [x, y])

        x_label = MathTex("x = " + x_latex, font_size=font_size)
        y_label = MathTex("y = " + y_latex, font_size=font_size)
    
        function_label = VGroup(x_label, y_label).arrange(DOWN, aligned_edge=LEFT)
        function_label.to_corner(UL, buff=.2)

        # Timer
        timer = Text("Time: .000")
        timer.add_updater(update_time)
        

        # Scale function & arrows to fit
        # based on the bounds of the functions
        (xmin, xmax), (ymin, ymax) = get_bounds(f_t)

        width = xmax-xmin
        height = ymax-ymin

        # how much of the width and height of the screen the function takes up
        width_factor = width / self.camera.frame.width
        height_factor = height / self.camera.frame.height

        # conservative scaling, ensure doesn't zoom in too much
        center = np.array([(xmin+xmax)/2, (ymin+ymax)/2, 0])
        shift = center
        main_elements.shift(-shift)
        self.add(Dot((0,0,0), color=GREEN))

        scale = 1 / max(width_factor, height_factor)
        scale *= .9
        main_elements.scale(scale)
        
        # move to center of screen, based on scale

        self.add(main_elements, timer, function_label)
        self.wait(run_time * loops)
    
    def make_arrow(self, start: complex, end: complex, prev: ChainedArrow | None, term: Term):
        """Makes an ChainedArrow from `start` to `end` in the XY plane. Rotates based
        on the end position of `prev`, and a rate equal to `term.n`"""
        return ChainedArrow(
            prev=prev,
            term=term,
            start=(start.real, start.imag, 0),
            end=(end.real, end.imag, 0),
            buff=0,
            stroke_width=1,
            tip_length=2,
            max_tip_length_to_length_ratio=.1
        )
    
    def make_arrows(self) -> list[ChainedArrow]:
        """Makes the initial arrows for each term at t=0"""
        arrows = []
        cursor = 0 + 0j
        terms = expr.terms

        for term in terms:
            change = term.at(0)

            end = cursor + change

            arrow = self.make_arrow(
                start=cursor,
                end=end, 
                prev=arrows[-1] if arrows else None,
                term=term
            )

            arrows.append(arrow)
            cursor = end  # tip-to-tail
        
        return arrows
    
    def func_to_latex(self, func: Expr) -> str:
        """Converts a SymPy expression to LaTeX, restoring symbolic pi/2pi from floats."""
        ltx = latex(func)
        for digit in reversed(range(10, 17)):
            ltx = ltx.replace(str(round(PI, digit)), "\\pi").replace(str(round(TAU, digit)), "2\\pi")
        return ltx


class ChainedArrow(Arrow):
    """Represents a `Manim.Arrow` with an assocated previous `ChainedArrow` and a term in the
    Fourier series being displayed. Also creates a circle which displays the radius of rotation"""
    def __init__(
        self,
        prev: ChainedArrow | None,
        term: Term,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.prev = prev
        
        # term 0 doesn't rotate, term 1 rotates 1x, term -3 rotates 3x in reverse, ...
        self.rate = term.n
        self.term = term

        self.circle = Circle(
            # hide the circle for the constant term
            radius=self.get_length() if self.rate != 0 else 0,
            fill_opacity=0,
            stroke_color=WHITE,
            stroke_opacity=.15,
            stroke_width=self.stroke_width
        )


def get_bounds(f_t: Expr) -> tuple[tuple[float, float], tuple[float, float]]:
    """Gets the maximum and minimum bounds of f_t based on sampling
    the x & y (real & imag parts) of f_t at different intervals."""
    xmin = ymin = float("inf")
    xmax = ymax = -xmin
    n_steps = 100

    # range() can't step in decimal increments because... idk.
    for bigstep in range(0, n_steps):
        time = bigstep / n_steps 

        # get value at t=time, simplify by casting to `complex`
        value = complex(f_t.subs(t, time))  # type: ignore

        # convert to xy
        x, y = value.real, value.imag

        xmin = min(xmin, x)
        xmax = max(xmax, x)
        ymin = min(ymin, y)
        ymax = max(ymax, y)
    print("BOUNDS", (xmin, xmax), (ymin, ymax))
    return (xmin, xmax), (ymin, ymax)