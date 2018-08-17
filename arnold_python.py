import os

from arnold import *
from ctypes import *
from threading import Lock

mutex = Lock()


# Bind a texture image to a channel name of a shader
def _bind_texture(shader, filename, channel_name, tiling, color_space=None):
    image = AiNode("image")
    AiNodeSetStr(image, "name", channel_name)
    AiNodeSetStr(image, "filename", filename)
    AiNodeSetFlt(image, "sscale", tiling)
    AiNodeSetFlt(image, "tscale", tiling)
    if color_space:
        AiNodeSetStr(image, "color_space", color_space)
    AiNodeLink(image, channel_name, shader)


# Bind a normal texture to a channel of a shader
def _bind_texture_normal(shader, filename, channel_name, tiling, color_space=None):
    image = AiNode("image")
    AiNodeSetStr(image, "name", channel_name)
    AiNodeSetStr(image, "filename", filename)
    AiNodeSetFlt(image, "sscale", tiling);
    AiNodeSetFlt(image, "tscale", tiling)
    if color_space:
        AiNodeSetStr(image, "color_space", color_space)

    normal_node = AiNode('MayaBump2D')
    AiNodeSetStr(normal_node, 'name', 'bump')
    AiNodeLink(image, 'bump_map', normal_node)
    AiNodeLink(image, 'normal_map', normal_node)
    AiNodeSetBool(normal_node, 'flip_r', True)
    AiNodeSetBool(normal_node, 'flip_g', True)
    AiNodeSetBool(normal_node, 'swap_tangents', False)
    AiNodeSetBool(normal_node, 'use_derivatives', True)
    AiNodeSetStr(normal_node, 'use_as', 'tangent_normal')
    AiNodeLink(normal_node, channel_name, shader);


def render_arnold(target_file, base_color_tex, normal_tex, roughness_tex, metallic_tex, resolution, shader_path):
    mutex.acquire()
    try:
        AiBegin()
        AiLoadPlugins(shader_path)

        # Geometry
        # Sphere
        sph = AiNode("sphere")
        AiNodeSetStr(sph, "name", "mysphere")
        AiNodeSetVec(sph, "center", 0.0, 4.0, 0.0)
        AiNodeSetFlt(sph, "radius", 4.0)

        # Plane
        mesh = AiNode("polymesh")
        AiNodeSetStr(mesh, "name", "mymesh")
        nsides_array = AiArray(1, 1, AI_TYPE_UINT, 4)
        AiNodeSetArray(mesh, "nsides", nsides_array)

        vla = [-100.0,
               0.0,
               100.0,
               100.0,
               0.0,
               100.0,
               -100.0,
               0.0,
               -100.0,
               100.0,
               0.0,
               -100.0]
        vlist_array = AiArrayConvert(len(vla),
                                     1,
                                     AI_TYPE_FLOAT,
                                     (c_float * len(vla))(*vla))
        AiNodeSetArray(mesh, "vlist", vlist_array)

        idxa = [0, 1, 3, 2]
        vidxs_array = AiArrayConvert(len(idxa), 1, AI_TYPE_UINT, (c_uint * len(idxa))(*idxa))
        AiNodeSetArray(mesh, "vidxs", vidxs_array)

        uva = [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
        uvlist_array = AiArrayConvert(len(uva), 1, AI_TYPE_FLOAT, (c_float * len(uva))(*uva))
        AiNodeSetArray(mesh, "uvlist", uvlist_array)

        idxuv = [0, 1, 2, 3]
        uvidxs_array = AiArrayConvert(len(idxuv), 1, AI_TYPE_UINT, (c_uint * len(idxuv))(*idxuv))
        AiNodeSetArray(mesh, "uvidxs", uvidxs_array)

        # Sphere shader
        shader1 = AiNode("standard_surface")
        AiNodeSetStr(shader1, "name", "material_sample")
        _bind_texture(shader1, base_color_tex, 'base_color', 4.0)
        _bind_texture(shader1, roughness_tex, 'specular_roughness', 4.0, 'linear')
        _bind_texture(shader1, metallic_tex, 'metalness', 4.0, 'linear')
        _bind_texture_normal(shader1, normal_tex, 'normal', 4.0, 'linear')
        AiNodeSetPtr(sph, "shader", shader1)

        # Ground shader
        shader2 = AiNode("standard_surface")
        AiNodeSetStr(shader2, "name", "ground")
        AiNodeSetRGB(shader2, "base_color", 0.3, 0.3, 0.3)
        AiNodeSetFlt(shader2, "specular", 0.0)
        AiNodeSetPtr(mesh, "shader", shader2)

        # Camera
        camera = AiNode("persp_camera")
        AiNodeSetStr(camera, "name", "mycamera")

        AiNodeSetVec(camera, "position", 0.0, 4.0, 12)
        AiNodeSetVec(camera, "look_at", 0.0, 4.0, 0.0)
        AiNodeSetFlt(camera, "fov", 45.0)

        # Physical Sky
        sky_tex = AiNode("physical_sky")
        AiNodeSetStr(sky_tex, "name", "mylight")
        AiNodeSetBool(sky_tex, 'use_degrees', True)
        AiNodeSetFlt(sky_tex, 'elevation', 45.0)
        AiNodeSetFlt(sky_tex, 'azimuth', 45.0)

        sky_light = AiNode('skydome_light')
        AiNodeSetFlt(sky_light, 'intensity', 3.0)
        AiNodeLink(sky_tex, 'color', sky_light)

        # Options
        options = AiUniverseGetOptions()
        AiNodeSetInt(options, "AA_samples", 8)
        AiNodeSetInt(options, "xres", resolution[0])
        AiNodeSetInt(options, "yres", resolution[1])
        AiNodeSetInt(options, "GI_diffuse_depth", 4)

        AiNodeSetPtr(options, "camera", camera)

        # Driver
        driver = AiNode("driver_png")
        AiNodeSetStr(driver, "name", "mydriver")
        AiNodeSetStr(driver, "filename", target_file)

        # Filter
        filter = AiNode("gaussian_filter")
        AiNodeSetStr(filter, "name", "myfilter")

        # Assign the driver and filter to the main(beauty) AOV,
        # which is called "RGBA" and is of type RGBA
        outputs_array = AiArrayAllocate(1, 1, AI_TYPE_STRING)
        AiArraySetStr(outputs_array, 0, "RGBA RGBA myfilter mydriver")
        AiNodeSetArray(options, "outputs", outputs_array)

        AiRender()
    finally:
        AiEnd()
        mutex.release()
