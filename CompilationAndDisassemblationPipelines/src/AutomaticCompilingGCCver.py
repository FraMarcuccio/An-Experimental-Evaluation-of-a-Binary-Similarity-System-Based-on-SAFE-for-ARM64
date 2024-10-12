import os
import shutil
import subprocess
import magic
import re

# Returns a list of folders inside a specific directory takes as input
def elenca_cartelle(directory):
    cartelle = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    return cartelle

# Prints all the files in specific folder takes as input from list of folders
def stampa_file_in_cartelle(directory, cartelle):
    for cartella in cartelle:

        # Ignore both "compiled" and "compiled_{compiler_info}" folders
        if cartella == "compiled" or cartella.startswith("compiled_"):
            continue

        percorso_cartella = os.path.join(directory, cartella)
        files_in_cartella = [f for f in os.listdir(percorso_cartella) if os.path.isfile(os.path.join(percorso_cartella, f))]
        
        print(f"Files in folder {cartella}: {files_in_cartella}")

# Gets compiler information about the system
def get_compiler_info():
    try:
        # Execute the command to get compiler information
        result = subprocess.run(['gcc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        # Extract the first line of the compiler information
        first_line = result.stdout.decode('utf-8').split('\n')[0]
        # Use regular expressions to extract the version numbers after parentheses on the first line
        version_numbers = re.search(r'\((.*?)\)\s*(\d+\.\d+\.\d+)', first_line)
        if version_numbers:
            return version_numbers.group(2)  # Return the second group containing the version numbers
        else:
            return None
    except subprocess.CalledProcessError:
        # Handle the case where the command fails
        print("Error while retrieving compiler information.")
        return None

compiler_version = get_compiler_info()
print(compiler_version)  # Output: '12.2.0' (or whatever the actual version is)

# Checks if a file is ELF or Object file using the 'file' command
def is_elf_or_object_file(file_path):

    # Runs the 'file' command and get the output
    result = subprocess.run(['file', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(result)
    output = result.stdout.decode('utf-8')

    # Check if the output contains 'ELF' or 'object'
    if 'ELF' in output or 'object' in output:
        # If it's ELF or object file, check if it has one of the desired extensions
        _, file_extension = os.path.splitext(file_path)
        desired_extensions = ['.o', '.lo', '.obj', '.elf', '.so']  # List of desired extensions
        if file_extension in desired_extensions:
            return True  # Include files with desired extensions
        else:
            return False  
    else:
        return False  # Exclude files that are not ELF or object files

# Executes commands in each folder sequentially only if the previous command executed successfully
def esegui_comandi_in_cartelle(directory, cartelle, comandi):
    for cartella in cartelle:
        percorso_cartella = os.path.join(directory, cartella)

        # Ignore both "compiled" and "compiled_{compiler_info}" folders
        if cartella == "compiled" or cartella.startswith("compiled_"):
            continue

        print(f"Executing commands in folder {cartella}:")

        for comando in comandi:
            comando_completo = f"{comando}"
            try:
                subprocess.run(comando_completo, shell=True, check=True, cwd=percorso_cartella)
                print(f"Executed command: {comando_completo}")
            except subprocess.CalledProcessError as e:
                print(f"Error executing command '{comando_completo}': {e}")
                return False  # Return False if an error occurs
                break
        else:
            return True  # Return True if all commands were executed successfully

def ARM_folder(directory, cartelle_in_libraries, valore_iterazione, directory_lib):

    compiler_info = get_compiler_info()
    arm_directory = os.path.join(directory, "ARM")

    if not os.path.exists(arm_directory):
        os.makedirs(arm_directory)
        print(f"Created folder {arm_directory}")
    else:
        print(f"The folder {arm_directory} already exists")

    for cartella in cartelle_in_libraries:

        lib_dir = os.path.join(arm_directory, cartella)

        if compiler_info:
            # Use the compiler information as part of the folder name
            cartella_compiled = os.path.join(lib_dir, f"GCC-{compiler_info}")
        else:
            # Use a default name if compiler information is not available
            cartella_compiled = os.path.join(lib_dir, "compiled")

        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)
            print(f"Created folder {lib_dir}")
           
            os.makedirs(cartella_compiled)
            print(f"Created folder {cartella_compiled}")
            print(cartella_compiled)
        else:
            print(f"The folder {lib_dir} already exists")
            print(f"The folder {cartella_compiled} already exists")

        # Use os.walk to recursively traverse the folder structure
        for root, _, files in os.walk(os.path.join(directory_lib, cartella)):
            for file_name in files:
                file_path = os.path.join(root, file_name)

                # Check if the file is ELF or object
                if is_elf_or_object_file(file_path):
                    nuova_cartella = os.path.join(cartella_compiled, f"{cartella}_Object_and_ELF_Optimization{valore_iterazione}")

                    # Create the folder if it doesn't exist
                    if not os.path.exists(nuova_cartella):
                        os.makedirs(nuova_cartella)

                    # Copy the file to the new folder
                    percorso_destinazione = os.path.join(nuova_cartella, file_name)
                    shutil.copy(file_path, percorso_destinazione)
                    print(f"Copied {file_name} to {nuova_cartella}")

    print("Operations completed successfully.")