# Library updates using the Substance Automation Toolkit

In this example we set up a build system that builds sbsar files from a library of sbs materials. It will also render 
thumbnails for the materials and injecting them into the sbsar files automatically.

## Prerequisites
In order to run this sample you need:
* Substance Automation Toolkit. Either pro or indie works
* Python 2.7, 3.5 or 3.6.
    * Scons 
    * pathlib
* Optionally Arnold for Maya [http://solidangle.com/arnold/download/] to enable thumbnail 
rendering

This sample has only been tested under Microsoft Windows but it should be possible to run 
on linux or mac with no or few modifications.

### Install python
If you don't already have a working python installation, go here
[https://www.python.org/about/gettingstarted/] to learn how to download and install it.

### Install python requirements
Before starting you need to install scons and pathlib for your python installation. This
will only need to be done once.
The easiest way to install the packages is using the python package manager pip.

If python is properly in path and installed with pip it is as easy as opening a command prompt and run:
```
pip install scons
pip install pathlib
```

If pip is not in path you will need to run something along the lines of:
```
python -m pip install scons
python -m pip install scons
```

Depending on how your installation is set up it might need to be run from an administrator 
command prompt

For more help on getting pip setup look here:
[https://pip.pypa.io/en/stable/installing/]

When done installing the dependencies, the last thing you need to know is how to run scons.
If your python environment is set up so scripts directory is in your path you can run scons directly
from the console like this:
```
PS C:\code> scons

scons: *** No SConstruct file found.
File "c:\python27\lib\site-packages\scons-3.0.1\SCons\Script\Main.py", line 924, in _main
```

If the scripts directory is not in path you can either add it to the path. Look here
for help [https://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/]

Don't forget to restart your command prompt window after you changed the path.

If you prefer to not update your path you can also run scons directly from the scripts directory.
In the event you use Python2.7 on windows the command would look something like this assuming python is installed in the directory
```C:\Python27
PS C:\work\Allegorithmic\code> C:\Python27\Scripts\scons.bat

scons: *** No SConstruct file found.
File "c:\python27\lib\site-packages\scons-3.0.1\SCons\Script\Main.py", line 924, in _main
```

In the examples below we will assume scons is in your system path.
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
* The data directory contains 3 different substance materials. The dependencies contains
various subgraphs and images used by the materials. 
* arnold_python.py contains code for rendering a thumbnail using arnolds python API
* SConstruct is a python file containing the build process for cooking and rendering 
described below

The python code is not described in detail in this document, refer to the comments in the code for help understanding it

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
in a smart way. If we write an ordinary python script processing everything we will reprocess all materials every time 
we change a single material.

A smarter way of approaching this would be to keep track of what files have changed. This is pretty easy to do by 
storing away a time stamp for when a material was rendered and make sure we only update the ones that was changed after 
its last rendering time. The problem now are the files in the dependency directory. When updating a file there every 
material that uses that dependency is going to have to be re-rendered and suddenly we need to deal with a more complex
challenge. Fortunately there are off the shelf solutions for this called build system. These are typically used for 
making incremental builds of programming projects but it works great for other similar problems too. In this example we 
are using scons which is python based build system. The other benefit with using a build system is that it can help you
multithread your builds. Since the build system knows all the dependencies between the different files and task
it can also see which ones of them need to be run in a specific order allowing it to run independent tasks
in parallel.

## Scons
Scons is a python based build system that keeps track of all files used in a build so we 
can incrementally update the the sbsars and thumbnails as we make changes to the material
library.

A full walk-through of scons is out of the scope in this sample but for in-depth 
information go here [https://scons.org/]. Here we'll just cover some basic concepts.

### SConstruct
The file called SConstruct in the sample directory is a python file which is used by
scons as a recipe for how a build should be done. Writing a SConstruct file requires
a little bit different thinking than ordinary python since you are actually not
executing your operations but just telling scons what needs to be done and then it will
figure out what has changed since last time and run the operations to make sure everything
is up-to-date. In a correctly configured scons project if you run it twice it will update
everything needed the first time and do nothing the second time since nothing has changed
since the last time.

### Builders
In scons a builder is a function for processing a set of input files to a set of output 
files. Examples from this sample would be cooking an sbs to an sbsar, rendering a map from
an sbsar or rendering a thumbnail from a set of pbr maps. A build operation is typically 
implemented as calling a command line tool or a python function
Note that builders never do 
operations in-place meaning it never changes the input files. As an example, if we look at for instance injecting 
a thumbnail into an sbs file it will take an sbs file and a png and create a new sbs file. This might seem
wasteful but the important thing to remember here is any of these intermediate files can
be time stamped in order to avoid reprocessing meaning they can be reused in case 
something for a future build. If we overwrote the input file next time we would run scons it would see a change from 
last time triggering a rebuild. At any time you can clean these intermediate files but it 
means they will have to be rebuilt next time we run scons.

### Scanners
A scanner is a function that looks at a file and tells scons what files it depends on. Since scons knows nothing about
substance sbs files we need to help it how to figure out what dependencies a file has using the pysbs, the substance
python API.
In the limited case we have here the only scanning we do is related to looking at sbs 
files and telling scons what other sbs files it depends on and what resources it is 
referencing. This means that if any file referenced changes between a build it will 
trigger a reprocessing.

### Build environment
In order to keep track of all operations and dependencies between files all build operations are recorded in the build
environment. This environment is initialized with all builders and scanners and when calling them as methods on the 
environment object they will go into the database of operations. When done executing the SConscript file it will look
at what has changed since last time and rebuild everything for you.

## Thumbnail Rendering using Arnold
As part of this sample thumbnails are rendered using Arnold if it's available. If it's not detected the build will just
keep. You can learn more about Arnold and its python api here [https://www.solidangle.com/].
The function in the sample essentially takes a set of pbr maps and sets up a scene with:
* Sphere textured with the pbr maps
* A ground plane
* A physical sky as a light source
* A camera for rendering the image

A thing to note here is that there is a lock around the arnold code meaning there will only be one thumbnails
being rendered at once. This is done for two reasons
* The Arnold code is not written in a way where we can have two arnold instances running at the same time meaning there 
be issues in case we do parallell builds
* Arnold is already multithreaded meaning most of the CPU power in the machine will be used by Arnold when rendering 
anyway.

## Running the sample
With all this background information and all the prerequisites installed we are finally ready to run the sample
Go to the sample directory in a command line window and run (the -j4 flag to the command tells scons it's allowed 
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
In order to show the benefit of a setup like this we can now run scons again
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
* output which contains an sbsar directory for cooked versions of the materials in your library. In case Arnold is found
there will also be a thumbnails directory which contains the thumbnail images for the materials.
* temp which contains intermediate files created during the processing. This directory is completely derived from the 
input files and can be deleted at any time but you should keep around to avoid unnecessary rebuilds but it
shound never be checked in to a source control system or live anywhere outside the build machine.

Now you can try changing files in the data or dependencies directory and re-run the sample and see how the build system
can figure out what has changed since last time you ran it.
