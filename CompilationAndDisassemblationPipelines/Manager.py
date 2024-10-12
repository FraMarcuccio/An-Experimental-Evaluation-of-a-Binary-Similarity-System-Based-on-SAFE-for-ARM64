import os
import shutil
import subprocess
import matplotlib.pyplot as plt
from CleaningToolManager import ManagerTool
import json
import pandas as pd

def run_runner():
    print("Running runner.py...")
    subprocess.run(["python", "Runner.py"])
    print("runner.py has finished execution.")

def run_copier():
    print("Running copier.py...")
    subprocess.run(["python", "Copier.py"])
    print("copier.py has finished execution.")

def sposta_cartella(origine, destinazione):
    try:
        shutil.move(origine, destinazione)
        print("Folder '{}' successfully moved to '{}'.".format(origine, destinazione))
    except FileNotFoundError:
        print("The source folder does not exist.")
    except PermissionError:
        print("Permission denied to move the folder.")
    except shutil.Error as e:
        print("Error while moving the folder: {}".format(e))

def builda_ed_avvia_container_docker():
    print("Building and starting the Docker container...")
    build_command = "docker build -t dockerfinale -f Dockerfile ."
    subprocess.run(build_command, shell=True)

    run_command = "docker run -it dockerfinale"
    print("Running the container for Dockerfile")
    subprocess.run(run_command, shell=True)

def copia_file_da_container():
    print("Starting and copying the file disassembly_info.db from the Docker container...")

    # Start a new temporary container
    run_command = "docker run -d --name temp_container dockerfinale"
    result = subprocess.run(run_command, shell=True)
    if result.returncode != 0:
        print("Error while starting the temporary container.")
        return

    # Ensure that the temp_container is running
    check_container_command = "docker ps -q -f name=temp_container"
    result = subprocess.run(check_container_command, shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("The temp_container is not running.")
        return

    # Copy the file from the container to the current script path
    percorso_script = os.getcwd()
    copy_command = f"docker cp temp_container:/app/disassembly_info.db {percorso_script}"
    result = subprocess.run(copy_command, shell=True)
    if result.returncode != 0:
        print("Error while copying the file from the container.")
        return

    # Remove the temporary container
    subprocess.run("docker rm -f temp_container", shell=True)

    file_destinazione = os.path.join(percorso_script, "disassembly_info.db")
    if os.path.exists(file_destinazione):
        print("File 'disassembly_info.db' successfully copied.")
    else:
        print("Error: the file does not exist in the destination.")

def genera_nome_univoco(nome_originale):
    base, ext = os.path.splitext(nome_originale)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"

percorso_script = os.path.dirname(os.path.realpath(__file__))

run_runner()
run_copier()

# Generate the chart for all files found in ARM
cartella_arm = os.path.join(percorso_script, "ARM")
"""
if os.path.exists(cartella_arm):
    file_stats, cartella_file_count = ManagerTool.numero_file_per_cartella(cartella_arm)
    #ManagerTool.crea_grafico_statistiche(file_stats)
    #ManagerTool.crea_grafico_statistiche_testuale(file_stats)

#ManagerTool.salva_risultati_in_file(cartella_arm, 'risultati.json')
#ManagerTool.salva_risultati_in_file_ridotte(cartella_arm, 'risultatiridotti.json')
#ManagerTool.salva_risultati_in_file_ridotte(cartella_arm, 'risultatinumero.json')
#print(risultatinumero.json)

#ManagerTool.visualizza_statistiche('risultati.json')
#ManagerTool.visualizza_statistiche_ridotte('risultatiridotti.json')
#ManagerTool.visualizza_statistiche_numero('risultatinumero.json')

# Calculate and print the average file size
soglia_kb = ManagerTool.calcola_media_dimensioni(file_stats)

# Delete files larger than 10KB
#ManagerTool.elimina_file_grandi(cartella_arm, soglia_kb)

# Given a threshold, proportionally reduce all files until the threshold is reached
#ManagerTool.riduci_numero_file(cartella_arm, soglia_totale=300)

# Generate the chart for all files found in ARM
cartella_arm = os.path.join(percorso_script, "ARM")
if os.path.exists(cartella_arm):
    file_stats, cartella_file_count = ManagerTool.numero_file_per_cartella(cartella_arm)
    ManagerTool.crea_grafico_statistiche(file_stats)
    #ManagerTool.crea_grafico_statistiche_testuale(file_stats)

# Calculate and print the average file size
#soglia_kb = ManagerTool.calcola_media_dimensioni(file_stats)
"""
cartella_origine = cartella_arm
cartella_destinazione = os.path.join(percorso_script, "src2")
sposta_cartella(cartella_origine, cartella_destinazione)

builda_ed_avvia_container_docker()
#copia_file_da_container()