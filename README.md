# fourier-anim

A small [Manim](https://www.manim.community/) + [SymPy](https://www.sympy.org/) script that computes complex Fourier series coefficients for a 2D parametric curve $f(t) = x(t) + i\,y(t)$ over $t \in [0, 1]$ and animates the resulting rotating epicycle arrows.

## Project Structure

- `fourier/main.py`  Defines the curve (`x`, `y`, `n_terms`), the `FourierConstruct` Manim scene, `ChainedArrow` epicycles, and bounding-box scaling (`get_bounds`).
- `fourier/src/expression.py`  Symbolic Fourier series solver (`Expression`, `Term`, `i_circle`, and SymPy symbol `t`).
- `fourier/manim.cfg`  Default Manim settings (`1920x1080`, `60` fps, black background).
- `fourier/shell.nix`  Nix shell environment with Python and `manim`.  

## Usage

Run Manim from inside the `fourier/` directory so `manim.cfg` and `./src/cache.json` resolve properly. `cd fourier && manim main.py`

## Customizing the Animation

Open `fourier/main.py` and edit:

- `x` and `y` — SymPy expressions in terms of `t` (sampled over $t \in [0, 1]$).
- `n_terms` — Number of Fourier terms. Must be an **odd** integer so terms are symmetric around $n = 0$ (e.g., `11` uses $n \in [-5, 5]$).
- `run_time` and `loops` (inside `FourierConstruct.construct`) — Duration in seconds per cycle and number of cycles to render.

## How It Works

1. **Coefficient Calculation (`fourier/src/expression.py`)**
   `Expression` combines `x` and `y` into $f(t) = x(t) + i\,y(t)$ and solves each Fourier coefficient by integrating over one period:
   $$c_n = \int_0^1 f(t)\,e^{-2\pi i n t}\,dt$$
   Computed coefficients are written to `fourier/src/cache.json`.

2. **Epicycle Rendering (`fourier/main.py`)**
   - Terms are sorted by frequency magnitude (`0, -1, 1, -2, 2, ...`).
   - Each term becomes a `ChainedArrow` whose tail stays attached to the previous arrow's tip and whose rotation rate is `term.n` revolutions per `run_time` seconds, accompanied by a faint orbit `Circle`.
   - The scene plots the target `ParametricFunction` in the background, scales everything to fit the camera frame using `get_bounds`, and displays `x`, `y`, and a normalized `Time` readout over `[0, 1)`.
