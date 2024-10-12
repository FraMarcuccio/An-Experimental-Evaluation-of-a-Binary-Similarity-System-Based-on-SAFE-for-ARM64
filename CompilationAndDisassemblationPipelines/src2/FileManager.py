import os
import re
import shutil

class FileManager:
    def __init__(self):
        self.ARM_folder, self.last_folder = self.find_ARM_folder()

    def find_ARM_folder(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        ARM_path = os.path.join(current_directory, "ARM")
        last_folder = os.path.basename(ARM_path)
        if os.path.isdir(ARM_path):
            return ARM_path, last_folder
        else:
            return None, None

    def find_files_in_path(self, path):
        all_files = []
        # Recursively traverse the path
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        return all_files

    def decompose_path(self, file_path):
        # Get the file name
        file_name = os.path.basename(file_path)

        # Decompose the path into a list of folders
        folders = file_path.split(os.path.sep)

        # Index of the desired upper folder (relative to the file name)
        upper_folder_index = -4  # Select the folder 4 positions before the file name
        
        # If the index is valid, get the name of the desired folder
        if abs(upper_folder_index) <= len(folders):
            upper_folder_name = folders[upper_folder_index]
            # Split the library name and version using the "-" separator
            if "-" in upper_folder_name:
                lib_name, lib_version = upper_folder_name.split("-", 1)
            else:
                lib_name = upper_folder_name
                lib_version = None
        else:
            upper_folder_name = None
            lib_name = None
            lib_version = None

        # Index of the upper folder + 1
        upper_folder_plus_one_index = -3
        if abs(upper_folder_plus_one_index) <= len(folders):
            upper_folder_plus_one_name = folders[upper_folder_plus_one_index]
            # Split the compiler name and version using the "-" separator
            if "-" in upper_folder_plus_one_name:
                compiler_name, compiler_version = upper_folder_plus_one_name.split("-", 1)
            else:
                compiler_name = upper_folder_plus_one_name
                compiler_version = None
        else:
            upper_folder_plus_one_name = None
            compiler_name = None
            compiler_version = None

        # Index of the upper folder + 2
        upper_folder_plus_two_index = -2
        if abs(upper_folder_plus_two_index) <= len(folders):
            upper_folder_plus_two_name = folders[upper_folder_plus_two_index]
        else:
            upper_folder_plus_two_name = None

        # Get the number after the word "Optimization"
        optimization_match = re.search(r'Optimization(\d+)', upper_folder_plus_two_name)
        if optimization_match:
            optimization_number = optimization_match.group(1)
        else:
            optimization_number = None

        return {
            "File name": file_name,
            "Library": lib_name,
            "Library version": lib_version,
            "Compiler": compiler_name,
            "Compiler version": compiler_version,
            "Optimization": optimization_number
        }

    def clear_project_folder(self, project):
        # Removes files and folders from the 'project' folder if present
        for item in os.listdir(project):
            item_path = os.path.join(project, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)  # Remove file
                    print("File removed from the project folder")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)  # Remove folder
                    print("Folder removed from the project folder")
            except Exception as e:
                print(f"Error while removing {item_path}: {e}")