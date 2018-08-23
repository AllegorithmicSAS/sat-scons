import os
import subprocess
import threading

mutex = threading.Lock()


def render_appleseed(target_file, base_color_tex, normal_tex, roughness_tex, metallic_tex, resolution, appleseed_path):
    mutex.acquire()

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
        appleseed_cli_path = os.path.join(appleseed_path, "bin", "appleseed.cli.exe" if os.name == "nt" else "appleseed.cli")
        subprocess.check_call([appleseed_cli_path, "--message-verbosity", "error", project_file, "--output", target_file])

    except Exception as e:
        print("Failed to generate {0} with appleseed: {1}".format(target_file, e))
        raise

    finally:
        mutex.release()
