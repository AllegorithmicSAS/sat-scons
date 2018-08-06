import sys
import os
from pysbs import context
from pysbs import substance
from pysbs import batchtools
import os.path
import pathlib


def detect_arnold_installation(arnold_roots):
    for p in arnold_roots:
        script_path = os.path.join(p, 'scripts')
        bin_path = os.path.join(p, 'bin')
        shader_path = os.path.join(p, 'shaders')
        if os.path.isdir(script_path) and os.path.isdir(bin_path) and os.path.isdir(shader_path):
            sys.path.insert(0, script_path)
            os.environ['PATH'] = os.environ['PATH'] + ';' + bin_path
            return (True, shader_path)
    return (False, '')


arnold_roots = ['C:/solidangle/mtoadeploy/2017']

# Configuration globals
ARNOLD_FOUND, ARNOLD_SHADER_PATH = detect_arnold_installation(arnold_roots)
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

print('Found Arnold: %r' % ARNOLD_FOUND)
if ARNOLD_FOUND:
    from arnold_python import render_arnold

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


# Scons render builder
def render(env, target, source):
    dest_filename = str(target[0])
    source = str(source[0])
    map = env['MAP']
    resolution = env['RESOLUTION']
    render_res = batchtools.sbsrender_render(source,
                                             output_path=os.path.dirname(dest_filename),
                                             output_name=strip_directory_and_extension(dest_filename),
                                             input_graph_output=map,
                                             set_value=['$outputsize@%d,%d' % (resolution, resolution)],
                                             engine='d3d10pc',
                                             png_format_compression='none'
                                             ).wait()
    return render_res


# Scons thumbnail renderer using arnold
def render_thumbnail_arnold(env, target, source):
    return render_arnold(target_file=str(target[0]),
                         base_color_tex=str(source[0]),
                         normal_tex=str(source[1]),
                         roughness_tex=str(source[2]),
                         metallic_tex=str(source[3]),
                         resolution=env['RESOLUTION'],
                         shader_path=ARNOLD_SHADER_PATH)


# Scons builder injecting a thumbnail into an sbs file
def inject_thumbnail(env, target, source):
    print('injecting thumbnail')
    source_sbs = str(source[0])
    source_thumbnail = str(source[1])
    sbsDoc = substance.SBSDocument(sbs_context, source_sbs)
    sbsDoc.parseDoc()
    g = sbsDoc.getSBSGraphList()[0]
    g.setIcon(source_thumbnail)
    resource_list = sbsDoc.getSBSResourceList()
    for r in resource_list:
        if r.mSource:
            s = r.mSource.getSource()
            if isinstance(s, substance.resource.SBSSourceExternalCopy):
                r.mSource = None

    sbsDoc.writeDoc(aNewFileAbsPath=str(target[0]), aUpdateRelativePaths=True)
    print('wrote doc %s' % str(target[0]))
    return None


# Scanner identifying dependencies from an sbs file
def sbs_scan(node, env, path, arg=None):
    print('Scanning %s' % str(node))
    sbsDoc = substance.SBSDocument(sbs_context, str(node))
    sbsDoc.parseDoc()
    dependencies = sbsDoc.getDependencyPathList(aRecurseOnPackages=True)
    resources = sbsDoc.getResourcePathList()
    return dependencies + resources

# Set up the sbs_scanner
sbs_scanner = Scanner(function=sbs_scan,
                      skeys=['.sbs'])

# Set up environment with builders
env = Environment(
    BUILDERS={
        # Copy builder
        'cp': Builder(action='copy $SOURCE $TARGET'),
        # Cooking with scanning
        'cook_scan': Builder(action=Action(cook_sbs),
                             source_scanner=sbs_scanner),
        # Cooking without rescanning
        'cook_no_scan': Builder(action=Action(cook_sbs)),
        # Rendering an sbsar to images
        'render': Builder(action=Action(render,
                                        varlist=['RESOLUTION', 'MAP'])),
        # Render a thumbnail
        'render_thumbnail': Builder(action=Action(render_thumbnail_arnold,
                                                  varlist=['RESOLUTION'])),
        # Injecting a thumbnail into an sbs file
        'inject_thumbnail': Builder(action=Action(inject_thumbnail))
    })


# Create targets for rendering all the maps needed to render a thumbnail
def render_maps(env, src_node, maps_to_render, resolution):
    p = pathlib.WindowsPath(str(src_node))
    split_path = list(p.parts)
    res = {}
    for m in maps_to_render:
        local_path = list(split_path)
        local_path[-1] = os.path.splitext(local_path[-1])[0] + '_' + m + '.png'
        new_path = os.path.join(*local_path)
        res[m] = env.render(new_path, src_node, MAP=m, RESOLUTION=resolution)[0]
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

        if ARNOLD_FOUND:
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
        else:
            # Arnold not found, just copy the cooked sbsar to the output directory
            env.cp(output_sbsar, cooked_dest)


# Walk through the source directory and process all sbs files
for root, dirs, files in os.walk(SRC_DIR):
    path = root.split(os.sep)
    for file in files:
        src = os.path.join(root, file)
        if os.path.splitext(src)[1] == '.sbs':
            process_sbs(src)
