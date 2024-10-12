import os
import re
import subprocess
from AutomaticCompilingCLANGver import *

def main():

    # Takes the paths of the folder where running file is in
    cartella_libraries = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libraries")
    print("The path of the libraries folder:", cartella_libraries)

    cartella_script = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    print("The path of the script folder:", cartella_script)

    # Functions input, actual folder
    found_folders = elenca_cartelle(cartella_libraries)

    print("Folders in directory {}: {}".format(cartella_libraries, found_folders))

    for value in range(4):
        errors = []
        for folder in found_folders:
            commands_to_execute = []
            match_found = False
            
            # Execute specific commands for the zlib folder
            if re.match(r'zlib', folder):
                commands_to_execute.extend([
                    f"sed -i \"s/\(CFLAGS='\)[^']*'/\\1-O{value}'/\" ./configure",
                    f"CC=clang CFLAGS='-O{value} -g -mcpu=cortex-a53 --target=aarch64-linux-gnu -fPIC' LDFLAGS='-g' ./configure",
                    "make"
                ])
                success = esegui_comandi_in_cartelle(cartella_libraries, [folder], commands_to_execute)
                if not success:
                    errors.append(folder)
                match_found = True

            # Execute specific commands for the boost folder
            elif re.match(r'boost', folder):
                commands_to_execute.extend([
                    f"./bootstrap.sh --with-toolset=clang",
                    f"sed -i '/^project/ a using gcc : arm : clang ; project : default-build <toolset>gcc-arm ; project : requirements <cflags>\"--target=aarch64-linux-gnu --gcc-toolchain=/usr -g -O{value} -mcpu=cortex-a53\" ;' project-config.jam",
                    f"./b2"
                ])
                success = esegui_comandi_in_cartelle(cartella_libraries, [folder], commands_to_execute)
                #if not success:
                #    errors.append(folder)
                match_found = True
                
            # Execute specific commands for the curl folder
            elif re.match(r'curl', folder):
                commands_to_execute.extend([
                    f"sed -i \"s/\(CFLAGS='\)[^']*'/\\1-O{value}'/\" ./configure",
                    f"./configure --without-ssl --without-zlib --without-brotli --without-zstd --host=aarch64-linux-gnu CC=clang CFLAGS='-O{value} -g --target=aarch64-linux-gnu -static' LDFLAGS='-g' CROSS_FLAGS='-mcpu=cortex-a53'",
                    "make"
                ])
                success = esegui_comandi_in_cartelle(cartella_libraries, [folder], commands_to_execute)
                if not success:
                    errors.append(folder)
                match_found = True

            if not match_found:
                print(f"Folder {folder} did not match any condition, removed.")
                errors.append(folder)

        # Remove folders with errors
        for folder in errors:
            found_folders.remove(folder)

        ARM_folder(cartella_script, found_folders, value, cartella_libraries)

if __name__ == "__main__":
    main()