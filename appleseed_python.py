import os
import platform
import subprocess
import sys
import threading
import urllib

if sys.version_info >= (3, 0):
    from urllib.parse import urlparse
    from urllib.request import urlretrieve
    from urllib.error import URLError
else:
    from urlparse import urlparse
    from urllib import urlretrieve
    URLError = IOError

import zipfile

mutex = threading.Lock()


def render_appleseed(target_file, base_color_tex, normal_tex, roughness_tex, metallic_tex, resolution):
    mutex.acquire()

    try:
        # Download and install appleseed if necessary.
        if not os.path.isdir("appleseed"):
            install_appleseed()

        # Render with appleseed.
        render(target_file, base_color_tex, normal_tex, roughness_tex, metallic_tex, resolution)

    finally:
        mutex.release()


def install_appleseed():
    archive_filename = None

    try:
        # Official appleseed releases can be found at https://github.com/appleseedhq/appleseed/releases.
        download_urls = {
            "win32": "https://github.com/appleseedhq/appleseed/releases/download/1.9.0-beta/appleseed-1.9.0-beta-0-g5693918-win64-vs140.zip",
            "linux": "https://github.com/appleseedhq/appleseed/releases/download/1.9.0-beta/appleseed-1.9.0-beta-0-g5693918-linux64-gcc48.zip",
            "darwin": "https://github.com/appleseedhq/appleseed/releases/download/1.9.0-beta/appleseed-1.9.0-beta-0-g5693918-mac64-clang.zip"
        }

        # Prior to Python 3.3, sys.platform returns "linux2" or "linux3":
        # https://docs.python.org/3/library/sys.html#sys.platform
        platform_name = sys.platform
        if platform_name.startswith("linux"):
            platform_name = "linux"

        # Abort if appleseed is not supported on the current platform.
        if platform_name not in download_urls:
            raise RuntimeError("appleseed is not supported on {0}.".format(platform_name))

        download_url = download_urls[platform_name]
        archive_filename = os.path.basename(urlparse(download_url).path)

        # Download appleseed.
        print("Downloading {0}...".format(download_url))
        urlretrieve(download_url, archive_filename)

        # Unpack archive.
        print("Unpacking {0}...".format(archive_filename))
        zip = zipfile.ZipFile(archive_filename, "r")
        zip.extractall(".")
        zip.close()

        # On Linux/macOS, make sure appleseed.cli is executable.
        if os.name == "posix":
            os.chmod("appleseed/bin/appleseed.cli", 755)

        # Conclude.
        if os.path.isdir("appleseed"):
            print("Successfully installed appleseed in {0}.".format(os.path.abspath("appleseed")))
        else:
            raise RuntimeError("Failed to install appleseed")

    # This handler exists to work around a limitation/bug in SCons.
    except URLError as e:
        e.strerror = "Failed to install appleseed: {0}".format(e)
        print(e.strerror)
        raise

    except Exception as e:
        print("Failed to install appleseed: {0}".format(e))
        raise

    finally:
        if archive_filename and os.path.isfile(archive_filename):
            # Delete archive.
            print("Removing {0}...".format(archive_filename))
            os.remove(archive_filename)

    print("Proceeding...")


def render(target_file, base_color_tex, normal_tex, roughness_tex, metallic_tex, resolution):
    try:
        # Read the template file from disk.
        with open("scene_template.appleseed", "r") as file:
            project_text = file.read()

        # Substitute variables by their values.
        project_text = project_text.replace("$baseColorTexturePath", base_color_tex)
        project_text = project_text.replace("$normalTexturePath", normal_tex)
        project_text = project_text.replace("$roughnessTexturePath", roughness_tex)
        project_text = project_text.replace("$metallicTexturePath", metallic_tex)
        project_text = project_text.replace("$frameWidth", str(resolution[0]))
        project_text = project_text.replace("$frameHeight", str(resolution[1]))

        # Write the new project file to disk.
        project_file = os.path.splitext(target_file)[0] + ".appleseed"
        with open(project_file, "w") as file:
            file.write(project_text)

        # Invoke appleseed to render the project file.
        appleseed_cli_path = r"appleseed\bin\appleseed.cli.exe" if os.name == "nt" else "appleseed/bin/appleseed.cli"
        result = subprocess.check_call([appleseed_cli_path, "--message-verbosity", "error", project_file, "--output", target_file])

    except Exception as e:
        print("Failed to generate {0} with appleseed: {1}".format(target_file, e))
        raise
