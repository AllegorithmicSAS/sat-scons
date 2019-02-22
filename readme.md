# Library updates using the Substance Automation Toolkit

In this example we set up a build system that builds sbsar files from a library of sbs materials. It will also render 
thumbnails for the materials and injecting them into the sbsar files automatically.

## Prerequisites

In order to run this sample you need:
* Substance Automation Toolkit. Either pro or indie works
* Python 2.7, 3.5 or 3.6.
    * [Scons](https://scons.org/) 
    * [pathlib](https://docs.python.org/3/library/pathlib.html)

The sample uses a renderer for thumbnails. It supports two external renderers:
* [Arnold for Maya](http://solidangle.com/arnold/download/)
* [appleseed](https://appleseedhq.net/)

It will look for Arnold first, then appleseed. If neither is found it will use a Substance node
to render the thumbnails.

The sample should work on Windows, Linux and macOS.

### Install Python

If you don't already have a working Python installation, go here
[https://www.python.org/about/gettingstarted/] to learn how to download and install it.

### Install Substance Automation Toolkit

In order to get access to the Substance Automation toolkit you need a valid subscription
of Substance Designer Indie or a valid Pro license for Substance Automation Toolkit.

The installation instructions for the SAT is available here:
[https://support.allegorithmic.com/documentation/display/SAT/Setup+and+Getting+Started]


### Install Python requirements

Before starting you need to install SCons and pathlib for your Python installation. This
will only need to be done once.
The easiest way to install the packages is using the Python package manager pip.

If Python is properly in path and installed with pip it is as easy as opening a command prompt and run:
```
pip install scons
pip install pathlib
```

If pip is not in path you will need to run something along the lines of:
```
python -m pip install scons
python -m pip install pathlib
```

Depending on how your installation is set up it might need to be run from an administrator 
command prompt

For more help on getting pip setup look here:
[https://pip.pypa.io/en/stable/installing/]

### Install Arnold

The sample can use Arnold as a renderer. It will search paths in `ARNOLD_ROOTS` for a valid
installation. It's set up to look for installations in the default locations for windows. 
Arnold can be found on its [download page](http://solidangle.com/arnold/download/).

### Install appleseed

Appleseed is an open source renderer available under the MIT license. If available it will be used for rendering
thumbnails. The installation steps for this sample are:
* Download appleseed from its [download page](https://appleseedhq.net/download.html). 
* Unpack it in the sample directory. The `appleseed` directory in the zip should be in put in the sample's root 
directory.
* If you want to change the locations to look for appleseed, update the `APPLESEED_ROOTS` variable in SConstruct script.

### Verifying the setup

When done installing the dependencies, the final thing you need to know is how to run SCons.
If your Python environment is set up so scripts directory is in your path you can run SCons directly
from the console like this:
```
PS C:\code> scons

scons: *** No SConstruct file found.
File "c:\python27\lib\site-packages\scons-3.0.1\SCons\Script\Main.py", line 924, in _main
```

If the scripts directory is not in path you can either add it to the path. Look here
for help: https://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/

Don't forget to restart your command prompt window after you changed the path.

If you prefer to not update your path you can also run SCons directly from the scripts directory.
In the event you use Python 2.7 on Windows the command would look something like this assuming Python is installed in the directory `C:\Python27`:
```
PS C:\work\Allegorithmic\code> C:\Python27\Scripts\scons.bat

scons: *** No SConstruct file found.
File "c:\python27\lib\site-packages\scons-3.0.1\SCons\Script\Main.py", line 924, in _main
```

In the examples below we will assume SCons is in your system path.

## The sample directory

When you get hold of the sample directory looks something like:
```
.
│   SConstruct
│   arnold_python.py
│   readme.md
│
└───data
    │   bark.sbs
    │   opus.sbs
    │   wood_planks_age_02.sbs
    │
    └───dependencies
            EnvironmentToolkit.sbs
            metal_floor.sbs
            opus_pattern3.png
            rust.sbs
            substance_logo.png
```
* The data directory contains 3 different Substance materials. The dependencies contains
various substance files and images used by the materials. 
* `arnold_python.py` contains code for rendering a thumbnail using Arnold's Python API.
* `appleseed_python.py` contains code for rendering a thumbnail using the appleseed command line renderer.
* `SConstruct` is a Python file containing the build process for cooking and rendering 
described below.

The Python code is not described in detail in this document, refer to the comments in the code for help understanding it.

## Process

The process the sample goes through looks like this:
* For each file in the data directory
* Cook the sbs file to an sbsar file
* Render out base color, normals, roughness and metallic images to the temp directory
* Render a sphere in a simple environment textured with the textures rendered
* Inject the rendered image as a thumbnail into a copy of the original material
* Cook the copy of the material to a sbsar (now with a thumbnail) and store it in the output directory
* Copy the thumbnail image to the output folder

## Dependency Tracking

On the surface this process looks pretty straightforward but there is a challenge related to making sure we do this 
in a smart way. If we write an ordinary Python script processing everything we will reprocess all materials every time 
we change a single material.

A smarter way of approaching this would be to keep track of what files have changed. This is pretty easy to do by 
storing away a time stamp for when a material was rendered and make sure we only update the ones that was changed after 
its last rendering time. The problem now are the files in the dependency directory. When updating a file there every 
material that uses that dependency is going to have to be re-rendered and suddenly we need to deal with a more complex
challenge. Fortunately there are off-the-shelf solutions for this called build systems. These are typically used for 
making incremental builds of programming projects but it works great for other similar problems too. In this example we 
are using SCons which is a Python-based build system. The other benefit with using a build system is that it can help 
you multithread your builds. Since the build system knows all the dependencies between the different files and tasks
it can also see which ones of them need to be run in a specific order allowing it to run independent tasks
in parallel.

## Scons

Scons is a Python-based build system that keeps track of all files used in a build so we 
can incrementally update the the sbsars and thumbnails as we make changes to the material
library.

A full walk-through of SCons is out of the scope in this sample but for in-depth 
information go [here](https://scons.org/). Here we'll just cover some basic concepts.

### SConstruct

The file called `SConstruct` in the sample directory is a Python file which is used by
SCons as a recipe for how a build should be done. Writing a `SConstruct` file requires
a little bit different thinking than ordinary Python since you are actually not
executing your operations but just telling SCons what needs to be done and then it will
figure out what has changed since last time and run the operations to make sure everything
is up-to-date. In a correctly configured SCons project if you run it twice it will update
everything needed the first time and do nothing the second time since nothing has changed
since the last time.

### Builders

In SCons a builder is a function for processing a set of input files to a set of output 
files. Examples from this sample would be cooking an sbs to an sbsar, rendering a map from
an sbsar or rendering a thumbnail from a set of pbr maps. A build operation is typically 
implemented as calling a command line tool or a Python function
Note that builders never do 
operations in-place meaning it never changes the input files. As an example, if we look at for instance injecting 
a thumbnail into an sbs file it will take an sbs file and a png and create a new sbs file. This might seem
wasteful but the important thing to remember here is any of these intermediate files can
be time stamped in order to avoid reprocessing meaning they can be reused in case 
something for a future build. If we overwrote the input file next time we would run SCons it would see a change from 
last time triggering a rebuild. At any time you can clean these intermediate files but it 
means they will have to be rebuilt next time we run SCons.

### Scanners

A scanner is a function that looks at a file and tells SCons what files it depends on. Since SCons knows nothing about
Substance sbs files we need to help it figure out what dependencies a file has using the pysbs, the Substance
Python API.
In the limited case we have here the only scanning we do is related to looking at sbs 
files and telling SCons what other sbs files it depends on and what resources it is 
referencing. This means that if any file referenced changes between a build it will 
trigger a reprocessing.

### Build environment

In order to keep track of all operations and dependencies between files all build operations are recorded in the build
environment. This environment is initialized with all builders and scanners and when calling them as methods on the 
environment object they will go into the database of operations. When done executing the SConscript file it will look
at what has changed since last time and rebuild everything for you.

## Thumbnail rendering using Arnold

By default the thumbnail rendering is done using Arnold.

The function in the sample essentially takes a set of PBR maps and sets up a scene with:
* A Sphere textured with the PBR maps
* A ground plane
* A physical sky as a light source
* A camera for rendering the image

Note that there is a lock around the Arnold code meaning there will only be one thumbnail
being rendered at once. This is done for two reasons:
* The Arnold code is not written in a way where we can have two Arnold instances running at the same time meaning there 
will be issues in case we do parallel builds
* Arnold is already multithreaded meaning most of the CPU power in the machine will be used by Arnold when rendering 
anyway.

## Thumbnail rendering using appleseed

As part of this sample, thumbnails can be rendered using appleseed. Note that the default choice is Arnold but if it's 
not found it will look for appleseed and use it if found. The code doing the rendering is found in the file 
`appleseed_python.py`. The sample comes with an OSL implementation of the PBR Metallic/Roughness shader used in 
Designer/Painter.

The setup is based on a pre-authored scene containing:
* A sphere textured with PBR maps
* A ground plane
* A physical sky as a light source
* A camera for rendering the image

Process:
* Reads the template scene and replaces the filenames for the textures with the ones for the current material
* Writes out the updated appleseed scene file to the temp directory
* Invokes the appleseed command line renderer on updated appleseed scene to render the image

## Thumbnail rendering using sbsrender

If neither appleseed nor Arnold is found it will use the the Substance Designer PBR rendering
node to create a thumbnail.

This uses an environment map to render a sphere using a Substance Designer rendering. Refer to the graph
in designer to learn more about this feature.

## Running the sample

With all this background information and all the prerequisites installed we are finally ready to run the sample.
Go to the sample directory in a command line window and run (the -j4 flag to the command tells SCons it's allowed 
to run up to four commands in parallel)
```
scons -j4
```
If everything is correctly set up it should start spitting out text related to what is going on
```
scons: Reading SConscript files ...
Found Arnold: True
[INFO][pysbs.context] SAT Install path: C:\Program Files\Allegorithmic\Substance Automation Toolkit
[INFO][pysbs.context] Default package: C:\Program Files\Allegorithmic\Substance Automation Toolkit\resources\packages
[INFO][pysbs.context] SD Install path: C:\Program Files\Allegorithmic\Substance Designer
scons: done reading SConscript files.
scons: Building targets ...
Scanning data\bark.sbs
cook_sbs(["temp\bark.sbsar"], ["data\bark.sbs"])
render(["temp\bark_basecolor.png"], ["temp\bark.sbsar"])
render(["temp\bark_normal.png"], ["temp\bark.sbsar"])
render(["temp\bark_roughness.png"], ["temp\bark.sbsar"])
render(["temp\bark_metallic.png"], ["temp\bark.sbsar"])
render_thumbnail_arnold(["temp\bark.png"], ["temp\bark_basecolor.png", "temp\bark_normal.png", "temp\bark_roughness.png", "temp\bark_metallic.png"])
00:00:00   224MB         | log started Wed Jul  4 17:45:56 2018
...
```
In order to show the benefit of a setup like this we can now run SCons again
```
scons -j4
```
It will respond with:
```
scons: Reading SConscript files ...
Found Arnold: True
[INFO][pysbs.context] SAT Install path: C:\Program Files\Allegorithmic\Substance Automation Toolkit
[INFO][pysbs.context] Default package: C:\Program Files\Allegorithmic\Substance Automation Toolkit\resources\packages
[INFO][pysbs.context] SD Install path: C:\Program Files\Allegorithmic\Substance Designer
scons: done reading SConscript files.
scons: Building targets ...
scons: `.' is up to date.
scons: done building targets.
```

After a full run the directory will look like this:
```
.
│   .sconsign.dblite
│   arnold_python.py
│   arnold_python.pyc
│   readme.md
│   SConstruct
│
├───data
│   │   bark.sbs
│   │   opus.sbs
│   │   wood_planks_age_02.sbs
│   │
│   └───dependencies
│           EnvironmentToolkit.sbs
│           metal_floor.sbs
│           opus_pattern3.png
│           rust.sbs
│           substance_logo.png
│
├───output
│   ├───sbsar
│   │       bark.sbsar
│   │       opus.sbsar
│   │       wood_planks_age_02.sbsar
│   │
│   └───thumbnails
│           bark.png
│           opus.png
│           wood_planks_age_02.png
│
└───temp
        bark.png
        bark.sbs
        bark.sbsar
        bark_basecolor.png
        bark_metallic.png
        bark_normal.png
        bark_roughness.png
        opus.png
        opus.sbs
        opus.sbsar
        opus_basecolor.png
        opus_metallic.png
        opus_normal.png
        opus_roughness.png
        wood_planks_age_02.png
        wood_planks_age_02.sbs
        wood_planks_age_02.sbsar
        wood_planks_age_02_basecolor.png
        wood_planks_age_02_metallic.png
        wood_planks_age_02_normal.png
        wood_planks_age_02_roughness.png
```
As you can see there are now two new directories:
* `output` which contains an sbsar directory for cooked versions of the materials in your library. In case Arnold is found
there will also be a thumbnails directory which contains the thumbnail images for the materials.
* `temp` which contains intermediate files created during the processing. This directory is completely derived from the 
input files and can be deleted at any time but you should keep it around to avoid unnecessary rebuilds. It
should never be checked in to a source control system or live anywhere outside the build machine.

Now you can try changing files in the data or dependencies directory and re-run the sample and see how the build system
figures out what has changed since last time you ran it.

## Known issues

### Python 3 on Windows

When running older versions of scons on Python 3 on Windows there seems to be a problem related to the module 
[pywin32](https://pypi.org/project/pywin32/) and its interaction with SCons. 

Scons version 3.0.4 doesn't have this issue so please upgrade and it should go away.

When the error happens it looks something like this:
```
inject_thumbnail(["temp\bark.sbs"], ["data\bark.sbs", "temp\bark.png"])
Injecting thumbnail into temp\bark.sbs...
[ERROR][pysbs.api_decorators] Exception of kind UnsupportedOperation in pysbs.sbswriter, line 35: SBSWriter.writeOnDisk()
[ERROR][pysbs.api_decorators] Exception of kind UnsupportedOperation in pysbs.substance.substance, line 279: SBSDocument.writeDoc()
scons: *** [temp\bark.sbs] TypeError : decoding to str: need a bytes-like object, NoneType found
Traceback (most recent call last):
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Taskmaster.py", line 255, in execute
    self.targets[0].build()
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Node\__init__.py", line 750, in build
    self.get_executor()(self, **kw)
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Executor.py", line 396, in __call__
    return _do_execute_map[self._do_execute](self, target, kw)
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Executor.py", line 127, in execute_action_list
    status = act(*args, **kw)
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Action.py", line 709, in __call__
    stat = self.execute(target, source, env, executor=executor)
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Action.py", line 1207, in execute
    result = SCons.Errors.convert_to_BuildError(result, exc_info)
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Errors.py", line 203, in convert_to_BuildError
    exc_info=exc_info)
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Errors.py", line 98, in __init__
    self.errstr = SCons.Util.to_str(errstr)
  File "c:\python36\lib\site-packages\scons-3.0.1\SCons\Util.py", line 1620, in to_str
    return str (s, 'utf-8')
TypeError: decoding to str: need a bytes-like object, NoneType found
scons: building terminated because of errors.
```
