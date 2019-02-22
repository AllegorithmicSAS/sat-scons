import sys
import os
from pysbs import context
from pysbs import substance
from pysbs import batchtools
import os.path
import pathlib
import shutil
import platform
import math

#
# Configuration globals
#

# Where to look for Arnold
ARNOLD_ROOTS = ['C:/solidangle/mtoadeploy/2017',
                'C:/solidangle/mtoadeploy/2018']

# Where to look for appleseed
APPLESEED_ROOTS = ['appleseed']


# Directories to ignore to avoid errors
IGNORE_LIST = {'common_dependencies',
               'dependencies',
               '.autosave'}

TEMP_DIR = 'temp'
OUTPUT_DIR = 'output/sbsar'
THUMBNAIL_DUMP = 'output/thumbnails'
THUMBNAIL_RESOLUTION = [256, 256]
MAP_RESOLUTION = 10
SRC_DIR = "data"

GPU_ENGINE = 'd3d10pc' if platform.system() == 'Windows' else 'ogl3'

#
# Renderer detection
#

def detect_arnold_installation(arnold_roots, min_arnold_version):
    for p in arnold_roots:
        script_path = os.path.join(p, 'scripts')
        bin_path = os.path.join(p, 'bin')
        shader_path = os.path.join(p, 'shaders')
        if os.path.isdir(script_path) and os.path.isdir(bin_path) and os.path.isdir(shader_path):
            sys.path.insert(0, script_path)
            os.environ['PATH'] += ';' + bin_path
            from arnold import AiGetVersion
            major_arnold_version = int(AiGetVersion()[0])
            if major_arnold_version < min_arnold_version:
                print('WARNING: Found Arnold version %d. This sample requires %d' % (
                major_arnold_version, min_arnold_version))
                return (False, '')
            return (True, shader_path)
    return (False, '')


def detect_appleseed_installation(appleseed_roots):
    for p in appleseed_roots:
        if os.path.isdir(p) and os.path.isdir(os.path.join(p, 'bin')):
            return (True, p)
    return (False, '')


# Look for Arnold

try:
    MINIMUM_ARNOLD_VERSION = 5
    ARNOLD_FOUND, ARNOLD_SHADER_PATH = detect_arnold_installation(ARNOLD_ROOTS, MINIMUM_ARNOLD_VERSION)
except:
    ARNOLD_FOUND = False

if ARNOLD_FOUND:
    print('Found Arnold in %s.' % os.path.dirname(ARNOLD_SHADER_PATH))
    import arnold_python
else:
    print('WARNING: No Arnold installation found. If this is unexpected, '
          'make sure the ARNOLD_ROOTS variable points to the right location.')

# Look for appleseed

if not ARNOLD_FOUND:
    try:
        APPLESEED_FOUND, APPLESEED_PATH = detect_appleseed_installation(APPLESEED_ROOTS)
    except:
        APPLESEED_FOUND = False

    if APPLESEED_FOUND:
        print('Found appleseed in %s.' % APPLESEED_PATH)
        import appleseed_python
    else:
        print('WARNING: No appleseed installation found. If this is unexpected, '
              'make sure the APPLESEED_ROOTS variable points to the right location.')

# Report detection results

if ARNOLD_FOUND:
    print('Using Arnold for thumbnail rendering.')
elif APPLESEED_FOUND:
    print('Using appleseed for thumbnail rendering.')
else:
    print('WARNING: Neither Arnold nor appleseed were found; PBR Node Designer will be use.')

# Configure scons for faster dependency scanning (makes a difference on large libraries)

# enabling implicit_cache makes sure the dependency tracking is cached between runs meaning we don't
# have to rescan the entire library every time we run it
SetOption('implicit_cache', 1)

# Set the decider to use timestamps rather than hashing. This is faster but also less conservative since changes
# to the file date without updating the content triggers rebuilds
Decider('timestamp-newer')

sbs_context = context.Context()


# Turns a filename with directory and extension into just the filename without extension
def strip_directory_and_extension(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]


# Scons builder that copies a source file to a target only if source file exists.
def copy_file_if_exists(target, source, env):
    target_path = str(target[0])
    source_path = str(source[0])
    if os.path.isfile(source_path):
        shutil.copyfile(source_path, target_path)


# Scons cook builder
def cook_sbs(env, target, source):
    dest_filename = str(target[0])
    source = str(source[0])
    cook_res = batchtools.sbscooker(source,
                                    output_path=os.path.dirname(str(dest_filename)),
                                    output_name=strip_directory_and_extension(dest_filename),
                                    includes=context.Context.getDefaultPackagePath(),
                                    quiet=True,
                                    enable_icons=True).wait()
    return cook_res


# Scons map rendering builder
def render_map(env, target, source):
    dest_filename = str(target[0])
    source = str(source[0])
    map = env['MAP']
    resolution = env['RESOLUTION']
    render_res = batchtools.sbsrender_render(source,
                                             output_path=os.path.dirname(dest_filename),
                                             output_name=strip_directory_and_extension(dest_filename),
                                             input_graph_output=map,
                                             set_value=['$outputsize@%d,%d' % (resolution, resolution)],
                                             png_format_compression='none',
                                             engine=GPU_ENGINE).wait()
    return render_res


# Scons thumbnail rendering builder
def render_thumbnail(env, target, source):
    if ARNOLD_FOUND:
        return arnold_python.render_arnold(target_file=str(target[0]),
                                           base_color_tex=str(source[0]),
                                           normal_tex=str(source[1]),
                                           roughness_tex=str(source[2]),
                                           metallic_tex=str(source[3]),
                                           resolution=env['RESOLUTION'],
                                           shader_path=ARNOLD_SHADER_PATH)

    elif APPLESEED_FOUND:
        return appleseed_python.render_appleseed(target_file=str(target[0]),
                                                 base_color_tex=os.path.basename(str(source[0])),
                                                 normal_tex=os.path.basename(str(source[1])),
                                                 roughness_tex=os.path.basename(str(source[2])),
                                                 metallic_tex=os.path.basename(str(source[3])),
                                                 resolution=env['RESOLUTION'],
                                                 appleseed_path=APPLESEED_PATH)

    else:
        process = batchtools.sbsrender_render(
            os.path.abspath("./data/dependencies/pbr_render.sbsar"),
            output_name=os.path.splitext(os.path.basename(str(target[0])))[0],
            output_path=os.path.dirname(str(target[0])),
            engine=GPU_ENGINE,
            set_entry=["basecolor@{}".format(str(source[0])),
                       "metallic@{}".format(str(source[3])),
                       "normal@{}".format(str(source[1])),
                       "roughness@{}".format(str(source[2]))],
            set_value=["$outputsize@{rx},{ry}".format(rx=int(math.log(int(env['RESOLUTION'][0]), 2)),
                                                      ry=int(math.log(int(env['RESOLUTION'][1]), 2)))])
        process.wait()


# Scons builder injecting a thumbnail into an sbs file
def inject_thumbnail(env, target, source):
    print('Injecting thumbnail into %s...' % str(target[0]))
    source_sbs = str(source[0])
    source_thumbnail = str(source[1])
    sbsDoc = substance.SBSDocument(sbs_context, source_sbs)
    sbsDoc.parseDoc()
    g = sbsDoc.getSBSGraphList()[0]
    if os.path.isfile(source_thumbnail):
        g.setIcon(source_thumbnail)
    else:
        print("Thumbnail not found, skipping setting the thumbnail.")
    resource_list = sbsDoc.getSBSResourceList()
    for r in resource_list:
        if r.mSource:
            s = r.mSource.getSource()
            if isinstance(s, substance.resource.SBSSourceExternalCopy):
                r.mSource = None

    sbsDoc.writeDoc(aNewFileAbsPath=str(target[0]), aUpdateRelativePaths=True)
    print('Wrote %s.' % str(target[0]))
    return None


_dependencies = {}


# Find all dependencies recursively storing results recursively to
# _dependencies to avoid rescanning the same file multiple times when dealing with
# multiple targets sharing dependencies
def _scan_recursive(filename):
    ext = os.path.splitext(filename)[1]
    merged_dep = set()
    # Only scan sbs dependencies, assume everything else is self contained
    if ext.lower() == '.sbs':
        print('Scanning %s...' % str(filename))
        sbsDoc = substance.SBSDocument(sbs_context, str(filename))
        sbsDoc.parseDoc()
        # Get resources and dependencies this file depends on
        dependencies = sbsDoc.getDependencyPathList(aRecurseOnPackages=False)
        resources = sbsDoc.getResourcePathList()
        all_dep = dependencies + resources
        merged_dep = set(all_dep)
        # Recursively add all dependencies for dependencies
        for dep in all_dep:
            if dep not in _dependencies:
                _scan_recursive(dep)
            merged_dep = merged_dep.union(_dependencies[dep])
    _dependencies[filename] = merged_dep


# Scanner identifying dependencies from an sbs file
def sbs_scan(node, env, path, arg=None):
    filename = str(node)
    # Scan dependencies if we haven't seen this file
    if filename not in _dependencies:
        _scan_recursive(filename)
    return list(_dependencies[filename])


# Set up the sbs_scanner
sbs_scanner = Scanner(function=sbs_scan,
                      skeys=['.sbs'])

# Set up environment with builders
env = Environment(
    BUILDERS={
        # Copy builder
        'cp': Builder(action=copy_file_if_exists),

        # Cooking with scanning
        'cook_scan': Builder(action=Action(cook_sbs), source_scanner=sbs_scanner),

        # Cooking without rescanning
        'cook_no_scan': Builder(action=Action(cook_sbs)),

        # Rendering an sbsar to images
        'render_map': Builder(action=Action(render_map, varlist=['RESOLUTION', 'MAP'])),

        # Render a thumbnail
        'render_thumbnail': Builder(action=Action(render_thumbnail, varlist=['RESOLUTION'])),

        # Injecting a thumbnail into an sbs file
        'inject_thumbnail': Builder(action=Action(inject_thumbnail))
    })


# Create targets for rendering all the maps needed to render a thumbnail
def render_maps(env, src_node, maps_to_render, resolution):
    p = pathlib.PurePath(str(src_node))
    split_path = list(p.parts)
    res = {}
    for m in maps_to_render:
        local_path = list(split_path)
        local_path[-1] = os.path.splitext(local_path[-1])[0] + '_' + m + '.png'
        new_path = os.path.join(*local_path)
        res[m] = env.render_map(new_path, src_node, MAP=m, RESOLUTION=resolution)[0]
    return res


# Generate targets for SBS file cooking, map rendering, thumbnail rendering and thumbnail injection
def process_sbs(src):
    dir_name = pathlib.Path(src).parts[-2]
    # Only cook materials, not their dependencies
    if dir_name not in IGNORE_LIST:
        # Filename for intermediate sbsar file with for rendering maps
        cooked_dest = str(pathlib.Path(TEMP_DIR, *pathlib.Path(src).parts[1:])) + 'ar'

        # Filename for the resulting sbsar with thumbnail embedded
        output_sbsar = str(pathlib.Path(OUTPUT_DIR, *pathlib.Path(src).parts[1:])) + 'ar'

        # Filename for sbs file with thumbnail embedded
        temp_sbs = str(pathlib.Path(TEMP_DIR, *pathlib.Path(src).parts[1:]))

        # Generate filename for the thumbnail file
        thumbnail_file = strip_directory_and_extension(src) + '.png'
        thumbnail_path = str(pathlib.Path(TEMP_DIR, *pathlib.Path(src).parts[1:-1]))
        thumbnail_path = os.path.join(thumbnail_path, thumbnail_file)

        # Cooks sbs to sbsar for for rendering maps
        cooked_sbsar = env.cook_scan(cooked_dest, src)

        # Render out all maps needed for thumbnail rendering
        all_maps = render_maps(env,
                               cooked_sbsar[0],
                               ['basecolor', 'normal', 'roughness', 'metallic'],
                               MAP_RESOLUTION)

        # Render thumbnails
        thumbnail_node = env.render_thumbnail(thumbnail_path,
                                              [all_maps['basecolor'],
                                               all_maps['normal'],
                                               all_maps['roughness'],
                                               all_maps['metallic']],
                                              RESOLUTION=THUMBNAIL_RESOLUTION)

        # Dump the thumbnail to the thumbnail directory
        env.cp(os.path.join(THUMBNAIL_DUMP, os.path.basename(str(thumbnail_node[0]))), thumbnail_node)

        # Now embed the thumbnail file as a thumbnail in the updated sbs and store it
        # as the target sbs
        # Note that the updated dependencies are copied directly since they have no
        # thumbnail
        thumb_sbs = env.inject_thumbnail(temp_sbs, [src, thumbnail_node[0]])

        # Cook the sbs to an sbsar with the thumbnail in the destination node
        env.cook_no_scan(output_sbsar, thumb_sbs)


# Walk through the source directory and process all sbs files
for root, dirs, files in os.walk(SRC_DIR):
    path = root.split(os.sep)
    for file in files:
        src = os.path.join(root, file)
        if os.path.splitext(src)[1] == '.sbs':
            process_sbs(src)
