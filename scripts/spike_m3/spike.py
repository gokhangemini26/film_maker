"""M3 step-0 feasibility spike. Run: blender -b --factory-startup --python spike.py -- <outdir> <engine>
Engines tried by caller: BLENDER_EEVEE, CYCLES, BLENDER_WORKBENCH. Writes report_<engine>.json + png."""
import bpy, sys, time, json, os, math
argv = sys.argv[sys.argv.index("--") + 1:]
out, engine = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
rep = {"blender": bpy.app.version_string, "engine": engine, "steps": {}}

def step(name):
    def deco(fn):
        t = time.time()
        try:
            r = fn(); rep["steps"][name] = {"ok": True, "s": round(time.time() - t, 2), "info": r}
        except Exception as e:
            rep["steps"][name] = {"ok": False, "error": repr(e)}
    return deco

def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_lin(h):
    h = h.lstrip("#"); return [srgb_to_lin(int(h[i:i+2], 16) / 255) for i in (0, 2, 4)]

sc = bpy.context.scene
@step("engine")
def _():
    sc.render.engine = engine
    return sc.render.engine
@step("scene")
def _():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global sc
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    # world: flat pastel sky
    w = bpy.data.worlds.new("w"); w.use_nodes = True; sc.world = w
    w.node_tree.nodes["Background"].inputs[0].default_value = (*hex_lin("#F2C9A0"), 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    # floor
    bpy.ops.mesh.primitive_plane_add(size=20); fl = bpy.context.object
    m = bpy.data.materials.new("floor"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (*hex_lin("#C9B8A8"), 1)
    fl.data.materials.append(m)
    # 'jacket' sphere with cel shader: Diffuse -> ShaderToRGB -> ColorRamp(constant) -> emission
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1), segments=64, ring_count=32)
    sp = bpy.context.object; bpy.ops.object.shade_smooth()
    mt = bpy.data.materials.new("cel"); mt.use_nodes = True; nt = mt.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (*hex_lin("#5F7C9E"), 1)   # shadow tone
    ramp.color_ramp.elements[1].position = 0.35
    ramp.color_ramp.elements[1].color = (*hex_lin("#7C9CC4"), 1)   # jacket hex
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    em = nt.nodes.new("ShaderNodeEmission"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(d.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs[0], bw.inputs[0])
    nt.links.new(bw.outputs[0], ramp.inputs[0]); nt.links.new(ramp.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], outn.inputs[0])
    sp.data.materials.append(mt)
    # inverted-hull outline
    ol = sp.copy(); ol.data = sp.data.copy(); bpy.context.collection.objects.link(ol)
    ol.data.materials.clear()
    om = bpy.data.materials.new("ol"); om.use_nodes = True; om.use_backface_culling = True
    ot = om.node_tree
    for n in list(ot.nodes): ot.nodes.remove(n)
    e2 = ot.nodes.new("ShaderNodeEmission"); e2.inputs[0].default_value = (*hex_lin("#3A4A63"), 1)
    o2 = ot.nodes.new("ShaderNodeOutputMaterial"); ot.links.new(e2.outputs[0], o2.inputs[0])
    ol.data.materials.append(om)
    mod = ol.modifiers.new("sol", "SOLIDIFY"); mod.thickness = -0.03; mod.use_flip_normals = True
    mod.offset = 1; om.use_backface_culling = True
    # light + camera
    bpy.ops.object.light_add(type="SUN", location=(3, -3, 5)); sun = bpy.context.object
    sun.rotation_euler = (math.radians(50), 0, math.radians(35)); sun.data.energy = 3
    bpy.ops.object.camera_add(location=(0, -6, 1.6)); cam = bpy.context.object
    cam.rotation_euler = (math.radians(88), 0, 0); cam.data.lens = 50; sc.camera = cam
    return "built"
@step("render")
def _():
    sc.render.filepath = os.path.join(out, f"spike_{engine}.png")
    if engine == "CYCLES":
        sc.cycles.samples = 16; sc.cycles.device = "CPU"
    if engine == "BLENDER_EEVEE" and hasattr(sc.eevee, "taa_render_samples"):
        sc.eevee.taa_render_samples = 16
    t = time.time(); bpy.ops.render.render(write_still=True)
    return {"render_s": round(time.time() - t, 2), "file": sc.render.filepath}
@step("pixels")
def _():
    img = bpy.data.images.load(os.path.join(out, f"spike_{engine}.png"))
    w, h = img.size; px = list(img.pixels)
    def at(x, y):
        i = (y * w + x) * 4; return [round(px[i + k] * 255) for k in range(3)]  # png loads as sRGB-encoded? report raw
    return {"size": [w, h], "center": at(w // 2, h // 2), "sky_corner": at(10, h - 10), "colorspace": img.colorspace_settings.name}
json.dump(rep, open(os.path.join(out, f"report_{engine}.json"), "w"), indent=2)
print("SPIKE_DONE", json.dumps(rep))
