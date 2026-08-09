"""Reproducible Blender scene for the bike shed: GLB in, product-shot renders out.

Headless usage (from the repo root):
    blender --background --python blender/build_scene.py            # build shed_scene.blend
    blender --background --python blender/build_scene.py -- --render  # + render all cameras

Pipeline: import blender/scene.glb (121 named parts from cad/build.py, mm
units) -> scale to meters -> one PBR wood material per cut-list name group ->
ground plane, Nishita sky + sun -> four cameras -> save shed_scene.blend.
With --render: Cycles 1920x1080 per camera into blender/renders/.

Material mapping is by part-name substring, checked in GROUPS order below
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
RENDER_DIR = HERE / "renders"

MM_TO_M = 0.001

# group key -> (base color sRGB, roughness, per-board brightness jitter,
#               grain stripe scale, grain mix strength)
# framing lumber / plates / rafters / fascia+rake trim / PT floor framing /
# PT skids / OSB deck — tonal spread so the frame reads part-by-part.
MATERIALS = {
    "framing":      ((0.48, 0.34, 0.19), 0.78, 0.30, 9.0, 0.14),
    "plate":        ((0.56, 0.41, 0.25), 0.76, 0.24, 9.0, 0.12),
    "rafter":       ((0.46, 0.33, 0.18), 0.78, 0.30, 7.0, 0.14),
    "trim":         ((0.58, 0.44, 0.27), 0.70, 0.16, 6.0, 0.10),
    "floor_frame":  ((0.28, 0.22, 0.14), 0.80, 0.24, 8.0, 0.10),
    "skid":         ((0.20, 0.16, 0.11), 0.72, 0.22, 8.0, 0.08),
    "osb":          ((0.42, 0.31, 0.17), 0.88, 0.12, 16.0, 0.18),
}


def group_for(label: str) -> str:
    """Cut-list label -> material group; order matters."""
    if "sub floor osb" in label:
        return "osb"
    if "skid" in label:                       # skid, skid sister
        return "skid"
    if "joist" in label:                      # rim joist, floor joist (PT)
        return "floor_frame"
    if label == "rafter":
        return "rafter"
    if "fascia" in label or "rake board" in label:
        return "trim"
    if "plate" in label:                      # incl. rake wall top plates
        return "plate"
    return "framing"                          # studs, headers, jacks, kings, cripples


def make_material(key: str):
    base, rough, jitter, grain_scale, grain_mix = MATERIALS[key]
    mat = bpy.data.materials.new(f"wood-{key}")
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


def main():
    do_render = "--render" in sys.argv
    bpy.ops.wm.read_factory_settings(use_empty=True)

    bpy.ops.import_scene.gltf(filepath=str(GLB))
    parts = [ob for ob in bpy.data.objects if ob.type == "MESH"]
    assert len(parts) == 121, f"expected 121 parts in scene.glb, got {len(parts)}"
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
    cams = setup_cameras(lo, hi)
    bpy.context.scene.camera = cams[0]
    setup_cycles()

    bpy.ops.wm.save_mainfile(filepath=str(BLEND))
    print(f"saved {BLEND}")

    if do_render:
        RENDER_DIR.mkdir(exist_ok=True)
        scene = bpy.context.scene
        for cam_obj in cams:
            scene.camera = cam_obj
            scene.render.filepath = str(RENDER_DIR / f"{cam_obj.name}.png")
            bpy.ops.render.render(write_still=True)
            print(f"rendered {scene.render.filepath}")


if __name__ == "__main__":
    main()
