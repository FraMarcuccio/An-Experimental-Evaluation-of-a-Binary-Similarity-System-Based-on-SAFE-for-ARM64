# -*- coding: utf-8 -*-

import subprocess
import os

#Gets the IDs of all Docker containers on the system.
def get_all_container_ids():
    try:
        # Run the 'docker ps -aq' command to get the IDs of all containers
        result = subprocess.Popen(["docker", "ps", "-aq"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.communicate()
        # Split the result to get a list of IDs
        container_ids = stdout.strip().decode('utf-8').split('\n')
        return container_ids
    except subprocess.CalledProcessError as e:
        print("Error while retrieving container IDs:", e)
        return []

#Checks if a Docker container is running.
def is_container_running(container_id):
    try:
        # Run the 'docker inspect' command to get information about the container
        result = subprocess.Popen(["docker", "inspect", "-f", "{{.State.Running}}", container_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.communicate()
        # Convert the result into a boolean
        is_running = stdout.strip().decode('utf-8') == "true"
        return is_running
    except subprocess.CalledProcessError:
        # If an error occurs, assume the container is not running
        return False

#Gets the name of a Docker container's image.
def get_container_image_name(container_id):
    try:
        result = subprocess.Popen(["docker", "inspect", "-f", "{{.Config.Image}}", container_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.communicate()
        image_name = stdout.strip().decode('utf-8')
        return image_name
    except subprocess.CalledProcessError:
        return ""

def list_folders_in_container(container_id):
    command = "docker exec {} ls -l".format(container_id)
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.communicate()
    print(stdout.decode('utf-8'))

#Gets the list of folders inside a specific folder in a container.
def list_folders_in_ARM(container_id, source_folder):
    try:
        # Run the 'docker exec' command to list the contents of the folder in the container
        result = subprocess.Popen(["docker", "exec", container_id, "ls", source_folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.communicate()
        # Check if the ls command succeeded (exit code 0)
        if result.returncode == 0:
            # Split the result to get a list of folder names
            folders = stdout.strip().decode('utf-8').split('\n')
            return folders
        else:
            print("Error while accessing '{}' in container {}. The folder may not exist.".format(source_folder, container_id))
            return []
    except subprocess.CalledProcessError as e:
        print("Error while listing folders inside '{}' of container {}:".format(source_folder, container_id), e)
        return []

#Copies the folders inside a specific folder from a Docker container to the local machine.
def copy_folders_from_container(container_id, source_folder, destination_folder):
    try:
        # Run the 'docker exec' command to list the contents of the folder in the container
        result = subprocess.Popen(["docker", "exec", container_id, "ls", source_folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.communicate()
        
        # Check if the ls command succeeded (exit code 0)
        if result.returncode == 0:
            # Split the result to get a list of folder names
            folders = stdout.strip().decode('utf-8').split('\n')
            
            # Loop through each folder and copy it to the destination folder
            for folder in folders:
                source_path = "{}:{}/{}".format(container_id, source_folder, folder)
                destination_path = "{}/{}".format(destination_folder, folder)
                
                # Check if the destination folder already exists
                if os.path.exists(destination_path):
                    # If it exists, copy only the contents of the folder
                    subprocess.call(["docker", "cp", "{}/.".format(source_path), destination_path])
                    print("Contents of folder '{}' successfully copied to existing folder '{}'".format(folder, destination_path))
                else:
                    # Otherwise, copy the entire folder
                    subprocess.call(["docker", "cp", source_path, destination_path])
                    print("Folder '{}' successfully copied to folder '{}'".format(folder, destination_path))
            
            print("Folders inside '{}' successfully copied from container {}".format(source_folder, container_id))
        else:
            print("Error while accessing '{}' in container {}. The folder may not exist.".format(source_folder, container_id))

    except subprocess.CalledProcessError as e:
        print("Error while copying folders inside '{}' from container {}:".format(source_folder, container_id), e)

#Stops a Docker container.
def stop_container(container_id):
    try:
        # Run the 'docker stop' command to stop the container
        subprocess.call(["docker", "stop", container_id])
        print("Container {} successfully stopped.".format(container_id))
    except subprocess.CalledProcessError as e:
        print("Error while stopping container {}:".format(container_id), e)

#Removes a Docker container.
def remove_container(container_id):
    try:
        # Run the 'docker rm' command to remove the container
        subprocess.call(["docker", "rm", container_id])
        print("Container {} successfully removed.".format(container_id))
    except subprocess.CalledProcessError as e:
        print("Error while removing container {}:".format(container_id), e)

#Removes a Docker image.
def remove_image(image_name):
    try:
        # Run the 'docker rmi' command to remove the image
        subprocess.call(["docker", "rmi", image_name])
        print("Image {} successfully removed.".format(image_name))
    except subprocess.CalledProcessError as e:
        print("Error while removing image {}:".format(image_name), e)

def main():
    # Specify the folder to copy (path inside the container)
    source_folder = "/app/ARM"
    # Specify the destination folder on the local machine
    current_directory = os.path.dirname(os.path.abspath(__file__))
    destination_folder = os.path.join(current_directory, "ARM")

    # Get the IDs of all containers
    container_ids = get_all_container_ids()
    
    # Filter containers created from images that start with "DF"
    df_containers = [cid for cid in container_ids if get_container_image_name(cid).lower().startswith("df")]

    # Loop through each filtered container and call list_folders_in_container for each container ID
    for container_id in df_containers:
        if is_container_running(container_id):
            print("Listing folders in container {}:".format(container_id))
            list_folders_in_container(container_id)
            print("\n")
        else:
            print("Container {} is not running. Starting it.".format(container_id))

            # Start the container
            subprocess.call(["docker", "start", container_id])
            
            print("Listing folders in container {}:".format(container_id))
            list_folders_in_container(container_id)
            print("\n")

            # List folders to be copied to local
            print("Listing folders in ARM of container {}:".format(container_id))
            folders = list_folders_in_ARM(container_id, source_folder)
            if folders:
                print("\n".join(folders))
            print("\n")
            
            # Copy the folders inside the container just started
            copy_folders_from_container(container_id, source_folder, destination_folder)

            # Stop the container after copying the folders
            stop_container(container_id)

            # Remove the container
            remove_container(container_id)

            # Remove the associated Docker image
            image_name = get_container_image_name(container_id)
            #remove_image(image_name)

if __name__ == "__main__":
    main()