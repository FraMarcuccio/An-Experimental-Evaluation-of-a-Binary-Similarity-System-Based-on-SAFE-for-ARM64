import os
import subprocess

def list_and_build_dockerfiles(folder):
    # List of Dockerfiles in the specified folder
    dockerfiles = [f for f in os.listdir(folder) if f.startswith("DF")]
    print(dockerfiles)

    if not dockerfiles:
        print("No Dockerfile found in the folder.")
        return

    for dockerfile in dockerfiles:
        # Convert the Dockerfile name to lowercase
        dockerfile_lowercase = dockerfile.lower()

        print("Building Dockerfile: {}".format(dockerfile))
        # Command to build the Docker container
        build_command = "docker build --rm -t {} -f {} .".format(dockerfile_lowercase, os.path.join(folder, dockerfile))
        subprocess.call(build_command, shell=True)

        # Command to run the Docker container
        run_command = "docker run {}".format(dockerfile_lowercase)
        print("Running the container for {}".format(dockerfile))
        subprocess.call(run_command, shell=True)

# Folder containing the Dockerfiles
folder_path = os.getcwd()

list_and_build_dockerfiles(folder_path)



