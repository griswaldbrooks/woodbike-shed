"""Reproducible Blender scene for the bike shed: GLB in, product-shot renders out.

Headless usage (from the repo root):
    blender --background --python blender/build_scene.py            # build shed_scene.blend
    blender --background --python blender/build_scene.py -- --render  # + render all cameras

    # dressed "finished shed" variant (render dressing, not modeled lumber):
    blender --background --python blender/build_scene.py -- --skin
    blender --background --python blender/build_scene.py -- --skin --render

Pipeline: import blender/scene.glb (293 named parts from cad/build.py -
117 framing + 176 finish, mm units; the finish parts are dropped again,
see main()) -> scale to meters -> one PBR wood material per cut-list name
group -> ground plane, Nishita sky + sun -> four cameras -> save
shed_scene.blend.
With --render: Cycles 1920x1080 per camera into blender/renders/.

--skin layers siding / trim / doors / a roof deck over the framing (aligned
to the framed openings read off the part bboxes) and saves shed_skin.blend;
renders go to blender/renders/skin/. See blender/README.md.

Material mapping is by part-name substring via group_colors.group_for
(names are CUT_LIST.md labels prefixed "NNN "). No hand-placed anything:
cameras and lights derive from the imported bounding box, so the script
survives model geometry changes.
"""
from math import radians
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
GLB = HERE / "scene.glb"
BLEND = HERE / "shed_scene.blend"
BLEND_SKIN = HERE / "shed_skin.blend"
RENDER_DIR = HERE / "renders"
SKIN_RENDER_DIR = RENDER_DIR / "skin"

MM_TO_M = 0.001

# Annotated-product-shot palette + label->group map live in group_colors.py,
# shared with view.py so the CAD viewer and the renders show the same group
# hues (legend in blender/README.md).
sys.path.insert(0, str(HERE))  # script dir, for plain `blender --python` runs
from group_colors import MATERIALS, group_for


def make_material(key: str):
    return _wood(f"wood-{key}", *MATERIALS[key])


def _wood(name, base, rough, jitter, grain_scale, grain_mix):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = rough
    # subtle grain: Wave on object coords mixed into the base color
    texco = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.inputs["Scale"].default_value = grain_scale
    wave.inputs["Distortion"].default_value = 1.8
    wave.inputs["Detail"].default_value = 0.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.65
    grain = nt.nodes.new("ShaderNodeMix")
    grain.data_type = "RGBA"
    grain.inputs["Factor"].default_value = grain_mix
    grain.inputs[6].default_value = base + (1.0,)  # A: flat base
    # per-board tint: Object Info Random -> [-jitter/2, +jitter/2], mixed
    # toward white (positive) or black (negative extrapolation) per board
    oinfo = nt.nodes.new("ShaderNodeObjectInfo")
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value = 0.0
    rng.inputs["From Max"].default_value = 1.0
    rng.inputs["To Min"].default_value = -jitter / 2
    rng.inputs["To Max"].default_value = jitter / 2
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.clamp_factor = False
    tint.inputs[7].default_value = (1.0, 1.0, 1.0, 1.0)  # B: white
    l = nt.links.new
    l(texco.outputs["Object"], wave.inputs["Vector"])
    l(wave.outputs["Color"], ramp.inputs["Fac"])
    l(ramp.outputs["Color"], grain.inputs[7])   # B: grain stripes
    l(oinfo.outputs["Random"], rng.inputs["Value"])
    l(rng.outputs["Result"], tint.inputs["Factor"])
    l(grain.outputs[2], tint.inputs[6])         # A: grained base
    l(tint.outputs[2], bsdf.inputs["Base Color"])
    l(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def scene_bbox():
    lo = Vector((float("inf"),) * 3)
    hi = Vector((float("-inf"),) * 3)
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            lo = Vector(min(a, b) for a, b in zip(lo, w))
            hi = Vector(max(a, b) for a, b in zip(hi, w))
    return lo, hi


def setup_cameras(lo, hi):
    c = (lo + hi) / 2

    def cam(name, pos, aim, lens=None, ortho=None):
        data = bpy.data.cameras.new(name)
        if ortho:
            data.type = "ORTHO"
            data.ortho_scale = ortho
        else:
            data.lens = lens
        ob = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(ob)
        ob.location = pos
        d = (aim - pos).normalized()
        # default rotation_mode is XYZ; a quaternion assignment would be ignored
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return ob

    target = Vector((c.x, c.y, 1.6))
    cams = [
        cam("cam_front_left", Vector((lo.x - 3.8, lo.y - 5.6, 1.70)), target, lens=40),
        cam("cam_back_right", Vector((hi.x + 4.4, hi.y + 5.6, 2.50)), target, lens=40),
        # axial view down the bay from the right-end door opening
        cam("cam_interior", Vector((hi.x - 0.35, 0.7, 1.55)),
            Vector((lo.x + 0.8, 0.7, 1.05)), lens=24),
        cam("cam_elevation", Vector((c.x, lo.y - 7.0, 1.50)),
            Vector((c.x, lo.y - 6.0, 1.50)), ortho=(hi.x - lo.x) + 2.4),
    ]
    return cams


def setup_environment(lo, hi):
    # ground plane at the lowest board, big enough to catch shadows + horizon
    plane = bpy.data.meshes.new("ground")
    plane.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)],
                      [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("ground", plane)
    bpy.context.collection.objects.link(ground)
    ground.location.z = lo.z
    gmat = bpy.data.materials.new("ground")
    gmat.use_nodes = True
    g = gmat.node_tree.nodes["Principled BSDF"]
    g.inputs["Base Color"].default_value = (0.09, 0.13, 0.06, 1.0)
    g.inputs["Roughness"].default_value = 1.0
    ground.data.materials.append(gmat)

    # sky: Nishita; sun elevation/azimuth kept consistent with the SUN lamp
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()
    wout = wnt.nodes.new("ShaderNodeOutputWorld")
    sky = wnt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = 0.93      # ~53.3 deg, matches lamp below
    sky.sun_rotation = 3.97       # sun toward front-left, matches lamp
    sky.altitude = 50.0
    sky.dust_density = 0.4        # clearer air, bluer sky
    sky.ozone_density = 2.0
    sky.sun_disc = False          # lighting comes from the SUN lamp below;
    bg = wnt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.05  # sky as ambient only
    wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    wnt.links.new(bg.outputs["Background"], wout.inputs["Surface"])

    # sun lamp: travels from front-left-high toward back-right-low
    sun_data = bpy.data.lights.new("sun", "SUN")
    sun_data.energy = 3.0
    sun_data.color = (1.0, 0.96, 0.88)
    sun = bpy.data.objects.new("sun", sun_data)
    bpy.context.collection.objects.link(sun)
    travel = Vector((0.5, 0.55, -1.0)).normalized()
    sun.rotation_euler = travel.to_track_quat("-Z", "Y").to_euler()


def setup_cycles():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    cyc = scene.cycles
    cyc.samples = 256
    cyc.use_denoising = True
    cyc.use_adaptive_sampling = True
    cyc.max_bounces = 8
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        scene.view_settings.look = "None"
    # GPU if available (RTX box), CPU fallback otherwise
    prefs = bpy.context.preferences.addons["cycles"].preferences
    device_ok = False
    for api in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = api
        except Exception:
            continue
        prefs.refresh_devices()
        gpus = [d for d in prefs.devices if d.type in ("OPTIX", "CUDA")]
        if gpus:
            for d in prefs.devices:
                d.use = d.type in ("OPTIX", "CUDA")
            cyc.device = "GPU"
            device_ok = True
            print(f"cycles device: {api} -> {[d.name for d in gpus]}")
            break
    if not device_ok:
        cyc.device = "CPU"
        print("cycles device: CPU fallback")


# ---------------------------------------------------------------------------
# Skin mode (--skin): render dressing, NOT modeled lumber.
#
# Layers blue-gray lap siding, white trim, barn-red doors and a roof deck
# over the framing as plain procedural boxes. Everything is aligned to wall
# planes and framed openings read off the imported parts' world bboxes, so
# like the cameras it re-derives from scene.glb. The framing underneath is
# untouched and stays the source of truth (blender/README.md).
# ---------------------------------------------------------------------------

JACK_T = 0.038        # 2x4 width; header span minus two jacks = clear opening
RAFTER_D = 0.14       # 2x6 depth; siding tops tuck under rafter bottoms
SIDING_T = 0.020      # siding board thickness
TRIM_T = 0.032        # trim proud-of-wall thickness
FRIEZE_H = 0.22       # frieze board height
SKIRT_Z = (-0.17, 0.02)   # water table band over the rim joist
CAS_W = 0.14          # door casing width


def part_bboxes(parts):
    """label -> list of world (lo, hi) Vector pairs, one per part."""
    out = {}
    for ob in parts:
        label = ob.name.split(" ", 1)[1]
        ws = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector((min(w[i] for w in ws) for i in range(3)))
        hi = Vector((max(w[i] for w in ws) for i in range(3)))
        out.setdefault(label, []).append((lo, hi))
    return out


def merged(bounds):
    lo = Vector((min(b[0][i] for b in bounds) for i in range(3)))
    hi = Vector((max(b[1][i] for b in bounds) for i in range(3)))
    return lo, hi


def skin_layout(parts):
    """Wall planes, roof plane and clear door openings from the framing."""
    bb = part_bboxes(parts)
    f = bb["front wall bottom plate"][0][0].y       # front outer face (-Y)
    b = bb["back wall bottom plate"][0][1].y        # back outer face
    l = bb["left wall top plate"][0][0].x           # left outer face
    r = bb["right wall top plate"][0][1].x          # right outer face
    front_top = merged(bb["front wall double top plate"])[1].z
    back_top = merged(bb["back wall double top plate short"])[1].z
    # roof top plane through the two fascia tops (front high, back low)
    ff = merged(bb["front fascia"])[1]
    bf = merged(bb["back fascia"])[1]
    slope = (bf.z - ff.z) / (bf.y - ff.y)

    def roof_top(y):
        return ff.z + slope * (y - ff.y)

    def openings(key, axis):
        """header bboxes -> clear openings [(lo, hi) on wall axis, head z]."""
        spans = {}
        for lo, hi in bb[key]:
            k = round(lo[axis], 3)                  # the two plies share a span
            s = spans.setdefault(k, [lo[axis], hi[axis], min(lo.z, hi.z), hi.z])
            s[1] = max(s[1], hi[axis])
            s[2] = min(s[2], lo.z)
        return [(s[0] + JACK_T, s[1] - JACK_T, s[2])
                for s in sorted(spans.values())]

    return {
        "f": f, "b": b, "l": l, "r": r,
        "front_top": front_top, "back_top": back_top,
        "roof_top": roof_top,
        "deck_x": (merged(bb["front fascia"])[0].x, ff.x),
        "front_open": openings("front wall headers", 0),
        "right_open": openings("right wall headers", 1),
    }


def box(name, x0, x1, y0, y1, z0, z1, mat):
    mesh = bpy.data.meshes.new(name)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    mesh.from_pydata(v, [], [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def prism_x(name, x0, x1, yz_pts, mat):
    """Extrude a convex YZ polygon (list of (y, z)) along X."""
    mesh = bpy.data.meshes.new(name)
    n = len(yz_pts)
    v = [(x0, y, z) for y, z in yz_pts] + [(x1, y, z) for y, z in yz_pts]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mesh.from_pydata(v, [], faces)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def lap_material(name, base, rough, exposure, vertical=False,
                 bump_strength=0.5, jit=(0.93, 1.06)):
    """Painted lap siding / plank doors: sawtooth bump + per-board tint.

    Lap lines key on world Z (horizontal siding) or world X+Y (vertical door
    planks: the idle coordinate is constant on each door face)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = rough
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    if vertical:
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        nt.links.new(sep.outputs["X"], add.inputs[0])
        nt.links.new(sep.outputs["Y"], add.inputs[1])
        coord = add.outputs[0]
    else:
        coord = sep.outputs["Z"]
    scale = nt.nodes.new("ShaderNodeMath")
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = 1.0 / exposure
    nt.links.new(coord, scale.inputs[0])
    saw = nt.nodes.new("ShaderNodeMath")
    saw.operation = "FRACT"
    nt.links.new(scale.outputs[0], saw.inputs[0])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    nt.links.new(saw.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # per-board tint: floor(coord/exposure) -> white noise -> brightness
    flr = nt.nodes.new("ShaderNodeMath")
    flr.operation = "FLOOR"
    nt.links.new(scale.outputs[0], flr.inputs[0])
    noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    noise.noise_dimensions = "1D"
    nt.links.new(flr.outputs[0], noise.inputs["W"])
    jr = nt.nodes.new("ShaderNodeMapRange")
    jr.inputs["To Min"].default_value = jit[0]
    jr.inputs["To Max"].default_value = jit[1]
    nt.links.new(noise.outputs["Value"], jr.inputs["Value"])
    comb = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(jr.outputs[0], comb.inputs[i])
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    tint.inputs[6].default_value = base + (1.0,)
    nt.links.new(comb.outputs[0], tint.inputs[7])
    nt.links.new(tint.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def plain_material(name, base, rough, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = base + (1.0,)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return mat


def build_skin(parts, lo, hi):
    """Add siding/trim/doors/roof-deck dressing; return the skin cameras."""
    L = skin_layout(parts)
    f, b, l, r = L["f"], L["b"], L["l"], L["r"]
    roof_top = L["roof_top"]
    rake_top = lambda y: roof_top(y) - RAFTER_D + 0.02   # noqa: E731

    siding = lap_material("skin-siding", (0.150, 0.200, 0.280), 0.55, 0.18)
    door_m = lap_material("skin-door", (0.280, 0.045, 0.035), 0.55, 0.10,
                          vertical=True, bump_strength=0.3)
    trim = plain_material("skin-trim", (0.780, 0.770, 0.730), 0.5)
    black = plain_material("skin-hardware", (0.02, 0.02, 0.02), 0.45, 0.4)
    roofwood = _wood("skin-roofwood", (0.430, 0.300, 0.170), 0.7, 0.15, 1.5, 0.10)

    # grass-green ground + brighter daylight for the dressed backyard look
    g = bpy.data.materials["ground"].node_tree.nodes["Principled BSDF"]
    g.inputs["Base Color"].default_value = (0.075, 0.180, 0.045, 1.0)
    for n in bpy.context.scene.world.node_tree.nodes:
        if n.type == "BACKGROUND":
            n.inputs["Strength"].default_value = 0.25
        elif n.type == "TEX_SKY":
            n.dust_density = 0.15
    bpy.data.lights["sun"].energy = 4.0

    # roof lumber reads as natural wood in the dressed shots
    for ob in parts:
        if ob.name.split(" ", 1)[1] in ("rafter", "front fascia", "back fascia",
                                        "left rake board", "right rake board"):
            ob.data.materials.clear()
            ob.data.materials.append(roofwood)

    front_fz_top = L["front_top"]
    front_fz_bot = front_fz_top - FRIEZE_H
    back_fz_top = roof_top(b) - RAFTER_D
    back_fz_bot = back_fz_top - FRIEZE_H

    # --- front wall: siding piers + header bands, casings, frieze, skirt ---
    fo = L["front_open"]
    xs = [l] + [c for o in fo for c in o[:2]] + [r]
    for x0, x1 in zip(xs[::2], xs[1::2]):
        box(f"siding-f {x0:.2f}", x0, x1, f - SIDING_T, f, 0.0, front_fz_bot, siding)
    box("skirt-f", l, r, f - TRIM_T, f, SKIRT_Z[0], SKIRT_Z[1], trim)
    for o0, o1, hz in fo:
        box(f"siding-f head {o0:.2f}", o0, o1, f - SIDING_T, f, hz, front_fz_bot, siding)
        box(f"casing-f j0 {o0:.2f}", o0 - CAS_W, o0, f - TRIM_T, f, SKIRT_Z[0], hz + CAS_W, trim)
        box(f"casing-f j1 {o0:.2f}", o1, o1 + CAS_W, f - TRIM_T, f, SKIRT_Z[0], hz + CAS_W, trim)
        box(f"casing-f head {o0:.2f}", o0 - CAS_W, o1 + CAS_W, f - TRIM_T, f, hz, hz + CAS_W, trim)
    box("frieze-f", l, r, f - TRIM_T, f, front_fz_bot, front_fz_top, trim)

    # --- back wall: solid ---
    box("siding-b", l, r, b, b + SIDING_T, 0.0, back_fz_bot, siding)
    box("frieze-b", l, r, b, b + TRIM_T, back_fz_bot, back_fz_top, trim)
    box("skirt-b", l, r, b, b + TRIM_T, SKIRT_Z[0], SKIRT_Z[1], trim)

    # --- side walls: raked siding tops; right wall carries an opening ---
    def rake_siding(tag, x0, x1, opens):
        ys = [f] + [c for o in opens for c in o[:2]] + [b]
        for y0, y1 in zip(ys[::2], ys[1::2]):
            prism_x(f"siding-{tag} {y0:.2f}", x0, x1,
                    [(y0, 0.0), (y1, 0.0),
                     (y1, rake_top(y1)), (y0, rake_top(y0))], siding)
        for o0, o1, hz in opens:
            prism_x(f"siding-{tag} head {o0:.2f}", x0, x1,
                    [(o0, hz), (o1, hz),
                     (o1, rake_top(o1)), (o0, rake_top(o0))], siding)
    rake_siding("l", l - SIDING_T, l, [])
    rake_siding("r", r, r + SIDING_T, L["right_open"])
    box("skirt-l", l - TRIM_T, l, f, b, SKIRT_Z[0], SKIRT_Z[1], trim)
    box("skirt-r", r, r + TRIM_T, f, b, SKIRT_Z[0], SKIRT_Z[1], trim)
    for o0, o1, hz in L["right_open"]:
        box("casing-r j0", r, r + TRIM_T, o0 - CAS_W, o0, SKIRT_Z[0], hz + CAS_W, trim)
        box("casing-r j1", r, r + TRIM_T, o1, o1 + CAS_W, SKIRT_Z[0], hz + CAS_W, trim)
        box("casing-r head", r, r + TRIM_T, o0 - CAS_W, o1 + CAS_W, hz, hz + CAS_W, trim)
    for tag, x0, x1 in (("l", l - TRIM_T, l), ("r", r, r + TRIM_T)):
        prism_x(f"frieze-{tag}", x0, x1,
                [(f, rake_top(f) - FRIEZE_H), (b, rake_top(b) - FRIEZE_H),
                 (b, rake_top(b) + 0.02), (f, rake_top(f) + 0.02)], trim)

    # --- corner boards: two flat boards per corner, one on each wall face ---
    for cx, cy, tag in ((l, f, "lf"), (r, f, "rf"), (l, b, "lb"), (r, b, "rb")):
        top = rake_top(cy)
        ex0, ex1 = (cx, cx + CAS_W) if cx == l else (cx - CAS_W, cx)
        ey0, ey1 = (cy, cy + CAS_W) if cy == f else (cy - CAS_W, cy)
        wy0, wy1 = (cy - TRIM_T, cy) if cy == f else (cy, cy + TRIM_T)
        wx0, wx1 = (cx - TRIM_T, cx) if cx == l else (cx, cx + TRIM_T)
        box(f"corner-{tag} f", ex0, ex1, wy0, wy1, SKIRT_Z[0], top, trim)
        box(f"corner-{tag} s", wx0, wx1, ey0, ey1, SKIRT_Z[0], top, trim)

    # --- roof deck slab on the rafter tops ---
    dx0, dx1 = L["deck_x"]
    y0, y1 = f - 0.65, b + 0.35
    prism_x("roof-deck", dx0, dx1,
            [(y0, roof_top(y0)), (y1, roof_top(y1)),
             (y1, roof_top(y1) + 0.035), (y0, roof_top(y0) + 0.035)], roofwood)

    # --- doors: slab + proud perimeter frame + strap hinges + latch ---
    dz0, dz1 = -0.02, 2.194
    W = 0.12

    # slab just proud of the wall face so it hides the bottom plate edge;
    # casing (TRIM_T proud) still stands in front of it
    def front_door(name, x0, x1, hinge, latch):
        box(name, x0, x1, f - 0.020, f + 0.025, dz0, dz1, door_m)
        fy0, fy1 = f - 0.028, f - 0.020
        box(name + " fr-l", x0, x0 + W, fy0, fy1, dz0, dz1, door_m)
        box(name + " fr-r", x1 - W, x1, fy0, fy1, dz0, dz1, door_m)
        box(name + " fr-b", x0, x1, fy0, fy1, dz0, dz0 + W, door_m)
        box(name + " fr-t", x0, x1, fy0, fy1, dz1 - W, dz1, door_m)
        for hz in (0.30, 1.80):
            h0, h1 = ((hinge, hinge + 0.38) if hinge < (x0 + x1) / 2
                      else (hinge - 0.38, hinge))
            box(name + f" hinge{hz}", h0, h1, f - 0.036, f - 0.028,
                hz - 0.03, hz + 0.03, black)
        box(name + " latch", latch - 0.07, latch + 0.07, f - 0.036, f - 0.028,
            1.02, 1.10, black)

    def right_door(name, y0, y1, hinge, latch):
        box(name, r - 0.025, r + 0.020, y0, y1, dz0, dz1, door_m)
        fx0, fx1 = r + 0.020, r + 0.028
        box(name + " fr-l", fx0, fx1, y0, y0 + W, dz0, dz1, door_m)
        box(name + " fr-r", fx0, fx1, y1 - W, y1, dz0, dz1, door_m)
        box(name + " fr-b", fx0, fx1, y0, y1, dz0, dz0 + W, door_m)
        box(name + " fr-t", fx0, fx1, y0, y1, dz1 - W, dz1, door_m)
        for hz in (0.30, 1.80):
            h0, h1 = ((hinge, hinge + 0.38) if hinge < (y0 + y1) / 2
                      else (hinge - 0.38, hinge))
            box(name + f" hinge{hz}", r + 0.028, r + 0.036, h0, h1,
                hz - 0.03, hz + 0.03, black)
        box(name + " latch", r + 0.028, r + 0.036, latch - 0.07, latch + 0.07,
            1.02, 1.10, black)

    for o0, o1, hz in fo:
        if o1 - o0 > 1.2:                      # double door: two leaves
            mid = (o0 + o1) / 2
            front_door("doorB-l", o0 - 0.06, mid, o0, mid)
            front_door("doorB-r", mid, o1 + 0.06, o1, mid)
        else:
            front_door("doorA", o0 - 0.06, o1 + 0.06, o0, o1 - 0.10)
    for o0, o1, hz in L["right_open"]:
        right_door("doorR", o0 - 0.06, o1 + 0.06, o0, o1 - 0.10)

    return setup_skin_cameras(lo, hi)


def setup_skin_cameras(lo, hi):
    c = (lo + hi) / 2

    def cam(name, pos, aim, lens):
        data = bpy.data.cameras.new(name)
        data.lens = lens
        ob = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(ob)
        ob.location = pos
        d = (aim - pos).normalized()
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return ob

    target = Vector((c.x, c.y, 1.5))
    return [
        # 3/4 from front-left, close to the reference photo's angle
        cam("skin_front_left", Vector((lo.x - 4.6, lo.y - 6.6, 1.75)), target, 40),
        cam("skin_back_right", Vector((hi.x + 4.8, hi.y + 6.4, 2.40)), target, 40),
        cam("skin_front", Vector((c.x, lo.y - 9.5, 1.50)),
            Vector((c.x, lo.y, 1.50)), 45),
        cam("skin_door", Vector((1.7, lo.y - 4.2, 1.50)),
            Vector((3.43, lo.y, 1.15)), 40),
    ]


def main():
    do_render = "--render" in sys.argv
    do_skin = "--skin" in sys.argv
    bpy.ops.wm.read_factory_settings(use_empty=True)

    bpy.ops.import_scene.gltf(filepath=str(GLB))
    mesh_obs = [ob for ob in bpy.data.objects if ob.type == "MESH"]
    # scene.glb also carries the modeled finish parts (cad/siding.py etc.);
    # the Blender scenes stay framing-only presentations (the --skin dressing
    # or the group tints), so drop them here - view.py shows them in the CAD
    # viewer. Keep the framing count assertion as the pipeline contract.
    for ob in [o for o in mesh_obs
               if o.name.split(" ", 1)[1].startswith("finish")]:
        bpy.data.objects.remove(ob, do_unlink=True)
    parts = [ob for ob in bpy.data.objects if ob.type == "MESH"]
    assert len(parts) == 117, f"expected 117 parts in scene.glb, got {len(parts)}"
    # glTF import assumes Y-up and hands our Z-up data over rolled onto its
    # side; bake the undo rotation + mm->m scale straight into mesh data
    # (object transforms in --background mode proved unreliable)
    xform = Matrix.Scale(MM_TO_M, 4) @ Matrix.Rotation(radians(-90), 4, "X")
    for ob in parts:
        ob.data.transform(xform)
        ob.data.update()
    bpy.context.view_layer.update()

    mats = {k: make_material(k) for k in MATERIALS}
    counts = dict.fromkeys(MATERIALS, 0)
    for ob in parts:
        label = ob.name.split(" ", 1)[1]  # strip "NNN " instance prefix
        key = group_for(label)
        counts[key] += 1
        ob.data.materials.clear()
        ob.data.materials.append(mats[key])
    print("material groups:", counts)

    lo, hi = scene_bbox()
    print(f"bbox meters: {[round(v, 2) for v in lo]} .. {[round(v, 2) for v in hi]}")
    setup_environment(lo, hi)
    if do_skin:
        cams = build_skin(parts, lo, hi)
    else:
        cams = setup_cameras(lo, hi)
    bpy.context.scene.camera = cams[0]
    setup_cycles()

    bpy.ops.wm.save_mainfile(filepath=str(BLEND_SKIN if do_skin else BLEND))
    print(f"saved {BLEND_SKIN if do_skin else BLEND}")

    if do_render:
        rdir = SKIN_RENDER_DIR if do_skin else RENDER_DIR
        rdir.mkdir(parents=True, exist_ok=True)
        scene = bpy.context.scene
        for cam_obj in cams:
            scene.camera = cam_obj
            scene.render.filepath = str(rdir / f"{cam_obj.name}.png")
            bpy.ops.render.render(write_still=True)
            print(f"rendered {scene.render.filepath}")


if __name__ == "__main__":
    main()
