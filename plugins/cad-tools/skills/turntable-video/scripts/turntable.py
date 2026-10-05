# /// script
# requires-python = ">=3.10"
# dependencies = ["pyvista>=0.44", "numpy", "pillow"]
# ///
"""Render a looping 360-degree turntable MP4 (and optional stills) of one or more mesh parts.

Run with uv, which installs the dependencies on first use:
    uv run --python 3.12 turntable.py base.stl=#2b5c9e lid.stl=#dcddd8 --lift lid -o out.mp4

Rendering is offscreen (VTK), so it works without a visible window. ffmpeg must be on PATH.
"""

import argparse
import math
import os
import shutil
import subprocess
import sys

import numpy as np
import pyvista as pv

PALETTE = ["#2b5c9e", "#dcddd8", "#1f6b3a", "#b8bcc2", "#2a2a2a", "#b0682a", "#7a4a9a"]
UP = {"z": (0, 0, 1), "y": (0, 1, 0)}


def parse_args():
    ap = argparse.ArgumentParser(description="Render a looping 360-degree turntable MP4 of mesh parts.")
    ap.add_argument("parts", nargs="+", help="mesh files (STL/OBJ/PLY/GLB/VTK), each optionally FILE=#rrggbb")
    ap.add_argument("-o", "--out", required=True, help="output .mp4")
    ap.add_argument("--lift", action="append", default=[], help="part name (file stem) that lifts off mid-clip; repeatable")
    ap.add_argument("--lift-mm", type=float, default=None, help="how far lifted parts rise, in model units; default 1.4x the model height")
    ap.add_argument("--turn-seconds", type=float, default=5.0, help="seconds per full turn")
    ap.add_argument("--turns", type=int, default=None, help="full turns; default 1, or 3 with --lift (closed, open, closed)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", type=int, default=1080, help="square frame size in pixels")
    ap.add_argument("--elev", type=float, default=28.0, help="camera elevation in degrees")
    ap.add_argument("--start-azimuth", type=float, default=-35.0)
    ap.add_argument("--up", choices=UP, default="z", help="model up axis: z for CAD/STL, y for GLB")
    ap.add_argument("--no-edges", action="store_true", help="skip the dark feature-edge outlines")
    ap.add_argument("--stills", metavar="DIR", help="also write PNG stills from fixed angles into DIR")
    ap.add_argument("--bg", default="#f4f5f2", help="background colour (fades to white at the top)")
    return ap.parse_args()


def load_parts(specs):
    parts = []
    for i, spec in enumerate(specs):
        path, _, color = spec.partition("=")
        mesh = pv.read(path)
        if isinstance(mesh, pv.MultiBlock):
            mesh = mesh.combine().extract_surface()
        name = os.path.splitext(os.path.basename(path))[0]
        parts.append(dict(name=name, mesh=mesh, color=color or PALETTE[i % len(PALETTE)]))
    return parts


class Scene:
    def __init__(self, parts, args):
        self.args = args
        self.up = np.array(UP[args.up], dtype=float)
        bounds = np.array([p["mesh"].bounds for p in parts])
        lo, hi = bounds[:, 0::2].min(axis=0), bounds[:, 1::2].max(axis=0)
        self.center = (lo + hi) / 2
        self.radius = float(np.linalg.norm(hi - lo) / 2)
        height = float(np.dot(hi - lo, self.up))
        self.lift_mm = args.lift_mm if args.lift_mm is not None else max(height * 1.4, self.radius * 0.35)

        p = pv.Plotter(off_screen=True, window_size=(args.size, args.size), lighting="none")
        p.set_background(args.bg, top="#ffffff")
        key = self.center + self.radius * (1.6 * self._side(-0.6, 0.8) + 2.5 * self.up)
        fill = self.center + self.radius * (1.6 * self._side(0.8, -0.5) + 1.5 * self.up)
        p.add_light(pv.Light(position=key, focal_point=self.center, intensity=0.85, light_type="scene light"))
        p.add_light(pv.Light(position=fill, focal_point=self.center, intensity=0.35, light_type="scene light"))
        p.add_light(pv.Light(light_type="headlight", intensity=0.25))
        self.lifted = []
        for part in parts:
            actors = [p.add_mesh(part["mesh"], color=part["color"], smooth_shading=False, specular=0.25,
                                 specular_power=20, ambient=0.18, diffuse=0.8)]
            if not args.no_edges:
                edges = part["mesh"].extract_feature_edges(feature_angle=35, boundary_edges=False,
                                                           non_manifold_edges=False)
                if edges.n_points:
                    actors.append(p.add_mesh(edges, color="#3a3d42", line_width=1.2))
            if part["name"] in args.lift:
                self.lifted += actors
        self.p = p

    def _side(self, a, b):
        """A horizontal direction for light placement, independent of the up axis."""
        h = np.array([1.0, 0, 0]) if self.up[0] == 0 else np.array([0, 0, 1.0])
        h2 = np.cross(self.up, h)
        return a * h + b * h2

    def render(self, azimuth_deg, lift, elev_deg=None):
        for actor in self.lifted:
            actor.SetPosition(*(self.up * lift))
        elev = math.radians(self.args.elev if elev_deg is None else elev_deg)
        az = math.radians(azimuth_deg)
        focus = self.center + self.up * lift * 0.45
        dist = self.radius * 3.8 + lift * 1.3
        h1 = np.array([1.0, 0, 0]) if self.up[0] == 0 else np.array([0, 0, 1.0])
        h2 = np.cross(self.up, h1)
        horiz = math.sin(az) * h1 - math.cos(az) * h2
        pos = focus + dist * (math.cos(elev) * horiz + math.sin(elev) * self.up)
        cam = self.p.camera
        cam.position, cam.focal_point, cam.up = pos, focus, tuple(self.up)
        cam.view_angle = 30
        self.p.renderer.ResetCameraClippingRange()
        self.p.render()  # without this, screenshot() can return the previous frame
        return self.p.screenshot(return_img=True)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lift_at(t, turn, lift, enabled):
    """Closed for a turn, lift over 1.5 s, open for a turn, lower over 1.5 s, closed again."""
    if not enabled:
        return 0.0
    move = min(1.5, turn * 0.3)
    up0, up1 = turn, turn + move
    down0 = 2 * turn
    down1 = down0 + move
    if t < up0:
        return 0.0
    if t < up1:
        return lift * ease((t - up0) / move)
    if t < down0:
        return lift
    if t < down1:
        return lift * (1 - ease((t - down0) / move))
    return 0.0


def write_video(scene, args):
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is not on PATH; install it (apt install ffmpeg / brew install ffmpeg) and rerun.")
    lifting = bool(scene.lifted)
    turns = args.turns or (3 if lifting else 1)
    seconds = turns * args.turn_seconds  # whole turns, so the clip loops without a jump
    n = int(round(seconds * args.fps))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{args.size}x{args.size}", "-r", str(args.fps), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", args.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert ff.stdin is not None
    deg_per_s = 360.0 / args.turn_seconds
    for i in range(n):
        t = i / args.fps
        img = scene.render(args.start_azimuth + deg_per_s * t, lift_at(t, args.turn_seconds, scene.lift_mm, lifting))
        ff.stdin.write(np.ascontiguousarray(img[:, :, :3]).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("ffmpeg failed")
    print(f"{args.out}: {n} frames, {seconds:.1f} s, {os.path.getsize(args.out) / 1e6:.1f} MB")


def write_stills(scene, args):
    from PIL import Image

    os.makedirs(args.stills, exist_ok=True)
    a0 = args.start_azimuth
    shots = [("01-closed", a0, 0, None), ("03-front", 0, 0, 12), ("04-back", 180, 0, 18),
             ("05-right", 90, 0, 15), ("06-left", 270, 0, 15), ("07-top", 0, 0, 80)]
    if scene.lifted:
        shots.insert(1, ("02-open", a0, scene.lift_mm, None))
    for name, az, lift, el in shots:
        Image.fromarray(scene.render(az, lift, el)).save(os.path.join(args.stills, f"{name}.png"))
    print(f"{args.stills}: {len(shots)} stills")


def main():
    args = parse_args()
    parts = load_parts(args.parts)
    unknown = set(args.lift) - {p["name"] for p in parts}
    if unknown:
        sys.exit(f"--lift names no loaded part: {', '.join(sorted(unknown))} (use the file stem)")
    scene = Scene(parts, args)
    write_video(scene, args)
    if args.stills:
        write_stills(scene, args)


if __name__ == "__main__":
    main()
