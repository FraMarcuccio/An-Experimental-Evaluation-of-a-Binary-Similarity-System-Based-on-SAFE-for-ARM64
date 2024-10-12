import os
import re
import subprocess
from AutomaticCompilingGCCver import *

def main():

    # Takes the paths of the folder where running file is in
    cartella_libraries = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libraries")
    print("The path of the libraries folder is:", cartella_libraries)

    cartella_script = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    print("The path of the script folder is:", cartella_script)

    # Functions input, actual folder
    cartelle_trovate = elenca_cartelle(cartella_libraries)

    print("Folders in the directory {}: {}".format(cartella_libraries, cartelle_trovate))

    for valore in range(4):
        errori = []
        for cartella in cartelle_trovate:
            comandi_da_eseguire = []
            match_trovato = False

            # Execute specific commands for the zlib folder
            if re.match(r'zlib', cartella):
                comandi_da_eseguire.extend([
                    f"sed -i \"s/\(CFLAGS='\)[^']*'/\\1-O{valore}'/\" ./configure",
                    f"CC=aarch64-linux-gnu-gcc CFLAGS='-O{valore} -g -mtune=cortex-a53 -fPIC' LDFLAGS='-g' ./configure",
                    "make"
                ])
                successo = esegui_comandi_in_cartelle(cartella_libraries, [cartella], comandi_da_eseguire)
                if not successo:
                    errori.append(cartella)
                match_trovato = True

            # Execute specific commands for the openssl folder
            elif re.match(r'openssl', cartella):
                comandi_da_eseguire.extend([
                    f"./Configure linux-generic64 --cross-compile-prefix=/usr/bin/aarch64-linux-gnu- -static -g -O{valore} -gdwarf-4 -mcpu=cortex-a53",                    
                    "make"
                ])
                successo = esegui_comandi_in_cartelle(cartella_libraries, [cartella], comandi_da_eseguire)
                if not successo:
                    errori.append(cartella)
                match_trovato = True

            # Execute specific commands for the boost folder
            elif re.match(r'boost', cartella):
                comandi_da_eseguire.extend([
                    f"./bootstrap.sh",
                    f"sed -i '/^project/ a using gcc : arm : aarch64-linux-gnu-gcc ; project : default-build <toolset>gcc-arm ; project : requirements <cflags>\"-g -O{valore} -mcpu=cortex-a53\" ;' project-config.jam",
                    f"./b2 toolset=gcc-arm target-os=linux"
                ])
                successo = esegui_comandi_in_cartelle(cartella_libraries, [cartella], comandi_da_eseguire)
                #if not successo:
                #    errori.append(cartella)
                match_trovato = True

            # Execute specific commands for the curl folder
            elif re.match(r'curl', cartella):
                comandi_da_eseguire.extend([
                    f"sed -i \"s/\(CFLAGS='\)[^']*'/\\1-O{valore}'/\" ./configure",
                    f"./configure --without-ssl --without-zlib --without-brotli --without-zstd --host=aarch64-linux-gnu CC=aarch64-linux-gnu-gcc CFLAGS='-O{valore} -g -static' LDFLAGS='-g' CROSS_FLAGS='-mcpu=cortex-a53'",
                    "make"
                ])
                successo = esegui_comandi_in_cartelle(cartella_libraries, [cartella], comandi_da_eseguire)
                if not successo:
                    errori.append(cartella)
                match_trovato = True

            if not match_trovato:
                print(f"Folder {cartella} not matched in any condition, removed.")
                errori.append(cartella)
        
        for cartella in errori:
            cartelle_trovate.remove(cartella)

        ARM_folder(cartella_script, cartelle_trovate, valore, cartella_libraries)

if __name__ == "__main__":
    main()