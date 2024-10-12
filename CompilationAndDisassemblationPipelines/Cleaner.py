import os
import shutil
import subprocess
import matplotlib.pyplot as plt
from CleaningToolManager import ManagerTool
import json
#import pandas as pd
from collections import Counter

if __name__ == "__main__":
    script_path = os.path.dirname(os.path.realpath(__file__))
    directory = script_path  # Replace with the actual path if different
    arm_folder = os.path.join(script_path, "ARM")

    # Generate statistics and print information regarding the files in the folders and in the root folder
    file_stats, folder_file_count = ManagerTool.numero_file_per_cartella(arm_folder)

    """
    # Execute file deletion outside the range
    ManagerTool.elimina_file_fuori_intervallo(arm_folder, soglia_min_kb=5, soglia_max_kb=11)

    # Execute reduction of the number of files for folders with the highest occurrences
    ManagerTool.riduci_numero_file_maggiori_occorrenze(arm_folder, soglia_totale=125)

    # Generate statistics and print information regarding the files in the folders and in the root folder
    file_stats, folder_file_count = ManagerTool.numero_file_per_cartella(arm_folder)
    """