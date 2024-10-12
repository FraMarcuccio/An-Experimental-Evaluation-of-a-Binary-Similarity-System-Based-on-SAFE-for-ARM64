import os
import shutil
import subprocess
import magic
import re

# Returns a list of folders inside a specific directory takes as input
def elenca_cartelle(directory):
    folders = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    return folders

# Prints all the files in a specific folder taken as input from a list of folders
def stampa_file_in_cartelle(directory, folders):
    for folder in folders:

        # Ignore both "compiled" and "compiled_{compiler_info}" folders
        if folder == "compiled" or folder.startswith("compiled_"):
            continue

        folder_path = os.path.join(directory, folder)
        files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        print(f"Files in folder {folder}: {files_in_folder}")

# Gets compiler information about the system
def get_compiler_info():
    try:
        # Run the command to get compiler information
        result = subprocess.run(['clang', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        # Extract the first line of compiler information
        first_line = result.stdout.decode('utf-8').split('\n')[0]
        # Use regular expressions to extract version numbers
        version_numbers = re.search(r'version\s+(\d+\.\d+\.\d+)', first_line)
        if version_numbers:
            return version_numbers.group(1)  # Return the first group containing the version numbers
        else:
            return None
    except subprocess.CalledProcessError:
        # Handle the case where the command fails
        print("Error while retrieving compiler information.")
        return None

compiler_version = get_compiler_info()
print(compiler_version)  # Output: '12.2.0' (or whatever the actual version is)

# Checks if a file is an ELF or Object file using the 'file' command
def is_elf_or_object_file(file_path):

    # Runs the 'file' command and gets the output
    result = subprocess.run(['file', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(result)
    output = result.stdout.decode('utf-8')

    # Check if the output contains 'ELF' or 'object'
    if 'ELF' in output or 'object' in output:
        # If it's an ELF or object file, check if it has one of the desired extensions
        _, file_extension = os.path.splitext(file_path)
        desired_extensions = ['.o', '.lo', '.obj', '.elf', '.so']  # List of desired extensions
        if file_extension in desired_extensions:
            return True  # Include files with desired extensions
        else:
            return False  
    else:
        return False  # Exclude files that are not ELF or object files

# Executes commands in each folder in sequence only if the previous command was executed successfully
def esegui_comandi_in_cartelle(directory, folders, commands):
    for folder in folders:
        folder_path = os.path.join(directory, folder)

        # Ignore both "compiled" and "compiled_{compiler_info}" folders
        if folder == "compiled" or folder.startswith("compiled_"):
            continue

        print(f"Executing commands in folder {folder}:")

        for command in commands:
            complete_command = f"{command}"
            try:
                subprocess.run(complete_command, shell=True, check=True, cwd=folder_path)
                print(f"Executed command: {complete_command}")
            except subprocess.CalledProcessError as e:
                print(f"Error while executing command '{complete_command}': {e}")
                return False  # Return False if an error occurs
                break
        else:
            return True  # Return True if all commands were executed successfully

def ARM_folder(directory, folders_in_libraries, iteration_value, directory_lib):

    compiler_info = get_compiler_info()
    arm_directory = os.path.join(directory, "ARM")

    if not os.path.exists(arm_directory):
        os.makedirs(arm_directory)
        print(f"Created folder {arm_directory}")
    else:
        print(f"Folder {arm_directory} already exists")

    for folder in folders_in_libraries:

        lib_dir = os.path.join(arm_directory, folder)

        if compiler_info:
            # Use the compiler information as part of the folder name
            compiled_folder = os.path.join(lib_dir, f"CLANG-{compiler_info}")
        else:
            # Use a default name if compiler information is not available
            compiled_folder = os.path.join(lib_dir, "compiled")

        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)
            print(f"Created folder {lib_dir}")
           
            os.makedirs(compiled_folder)
            print(f"Created folder {compiled_folder}")
            print(compiled_folder)
        else:
            print(f"Folder {lib_dir} already exists")
            print(f"Folder {compiled_folder} already exists")

        # Use os.walk to recursively traverse the folder structure
        for root, _, files in os.walk(os.path.join(directory_lib, folder)):
            for file_name in files:
                file_path = os.path.join(root, file_name)

                # Check if the file is ELF or object
                if is_elf_or_object_file(file_path):
                    new_folder = os.path.join(compiled_folder, f"{folder}_Object_and_ELF_Optimization{iteration_value}")

                    # Create the folder if it doesn't exist
                    if not os.path.exists(new_folder):
                        os.makedirs(new_folder)

                    # Copy the file to the new folder
                    destination_path = os.path.join(new_folder, file_name)
                    shutil.copy(file_path, destination_path)
                    print(f"Copied {file_name} to {new_folder}")

    print("Operations successfully completed.")