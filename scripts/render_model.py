#!/usr/bin/env python3
"""Software 3D renderer for the woodbike-shed model (no Blender needed).

Every part is an X-prism over a YZ profile (exact profiles for the sloped
members, bbox rectangles for the rest — same representation as
audit_overlaps.py). Faces are projected with a yaw/pitch orthographic
camera and drawn back-to-front (painter's algorithm) with flat Lambert
shading. Output: PNGs you can actually look at.

Usage: python3 render_model.py [out_dir]   (default: renders/)
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import audit_overlaps as ao
from build_cut_list import section_for

HERE = Path(__file__).parent
M = 39.3700787

COLOR = {
    "Skids": (125, 107, 63), "Floor": (157, 179, 138),
    "Back wall": (227, 198, 146), "Front wall": (227, 198, 146),
    "Left wall": (170, 200, 170), "Right wall": (200, 180, 150),
    "Left rake wall": (176, 137, 84), "Right rake wall": (176, 137, 84),
    "Roof": (127, 168, 201), "Reference": (200, 200, 200),
    "Other": (150, 150, 150),
}

LIGHT = (0.45, -0.5, 0.74)  # ~normalized


def norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def solids():
    """Yield (name, section, [(x, y, z), ...] faces) for every part."""
    bboxes = json.loads((HERE / "bboxes.json").read_text())
    prof = {
        "rafter": ao.RAFTER,
        "left rake board": ao.RAKE_BOARD,
        "right rake board": ao.RAKE_BOARD,
        "left rake wall top plate": ao.LEFT_RAKE_PLATE,
        "right rake wall top plate": ao.RIGHT_RAKE_PLATE,
        "front fascia": ao.FASCIA_FRONT,
        "back fascia": ao.FASCIA_BACK,
    }
    stud_profiles = {round(yc, 2): q for yc, q in
                     zip((0.75, 16.25, 32.25, 48.25), ao.RAKE_STUDS)}
    for r in bboxes:
        name = r["name"]
        bb = r["bbox_m"]
        x0, x1 = bb["lowX"] * M, bb["highX"] * M
        if name in prof:
            poly = prof[name]
        elif name in ("left rake wall studs", "right rake wall studs"):
            yc = round((bb["lowY"] + bb["highY"]) / 2 * M, 2)
            poly = stud_profiles[yc]
        else:
            y0, y1 = bb["lowY"] * M, bb["highY"] * M
            z0, z1 = bb["lowZ"] * M, bb["highZ"] * M
            poly = [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]
        yield name, section_for(name), prism_faces(x0, x1, poly)


def prism_faces(x0, x1, poly):
    n = len(poly)
    faces = []
    caps = [[(x0, y, z) for y, z in poly], [(x1, y, z) for y, z in poly]]
    faces += caps
    for i in range(n):
        y1, z1 = poly[i]
        y2, z2 = poly[(i + 1) % n]
        faces.append([(x0, y1, z1), (x1, y1, z1), (x1, y2, z2), (x0, y2, z2)])
    return faces


def face_normal(pts):
    ax, ay, az = pts[0]
    bx, by, bz = pts[1]
    cx, cy, cz = pts[2]
    u = (bx - ax, by - ay, bz - az)
    v = (cx - ax, cy - ay, cz - az)
    return norm((u[1] * v[2] - u[2] * v[1],
                 u[2] * v[0] - u[0] * v[2],
                 u[0] * v[1] - u[1] * v[0]))


def render(faces, yaw_deg, pitch_deg, w=1600, h=1100, bg=(246, 244, 239)):
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    def proj(p):
        x, y, z = p
        x1 = x * cy - y * sy
        y1 = x * sy + y * cy
        y2 = y1 * cp - z * sp
        z2 = y1 * sp + z * cp
        return (x1, z2, y2)  # screen x, screen y(up), depth

    allp = [proj(p) for f in faces for p in f[0]]
    xs = [p[0] for p in allp]
    zs = [p[1] for p in allp]
    pad = 40
    s = min((w - 2 * pad) / (max(xs) - min(xs)), (h - 2 * pad) / (max(zs) - min(zs)))
    mx, mz = (max(xs) + min(xs)) / 2, (max(zs) + min(zs)) / 2

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    projected = []
    for pts, color in faces:
        pp = [proj(p) for p in pts]
        depth = sum(p[2] for p in pp) / len(pp)
        projected.append((depth, pp, pts, color))
    for depth, pp, pts, color in sorted(projected, key=lambda t: t[0]):
        n = face_normal(pts)
        lam = max(0.0, n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2])
        b = 0.45 + 0.55 * lam
        col = tuple(int(c * b) for c in color)
        scr = [(w / 2 + (p[0] - mx) * s, h / 2 - (p[1] - mz) * s) for p in pp]
        draw.polygon(scr, fill=col, outline=(40, 36, 28))
    return img


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    faces = []
    for name, section, fs in solids():
        if not section:  # inner volume reference body
            continue
        col = COLOR.get(section, (150, 150, 150))
        faces += [(f, col) for f in fs]
    views = [("iso-front", 35, 18), ("iso-back", 215, 18), ("roof-top", 35, 55)]
    for label, yaw, pitch in views:
        img = render(faces, yaw, pitch)
        img.save(out_dir / f"shed-{label}.png")
        print(f"wrote {out_dir / f'shed-{label}.png'}")


if __name__ == "__main__":
    main()
