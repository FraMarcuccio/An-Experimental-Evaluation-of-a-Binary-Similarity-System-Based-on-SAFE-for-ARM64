import os
import shutil
import subprocess
import random
import matplotlib.pyplot as plt
from tabulate import tabulate
import json
import pandas as pd
from collections import Counter

class ManagerTool:
    
    # Calculate and print all files, their number, name, and size per folder
    def numero_file_per_cartella(directory):
        if not isinstance(directory, str) or not os.path.exists(directory):
            print(f"Invalid directory: {directory}")
            return {}, {}

        file_stats = {}
        cartella_file_count = {}

        total_files = 0

        print("\nFile count per folder:")
        for root, dirs, files in os.walk(directory):
            if not files:
                continue  # Skip empty folders

            relative_root = os.path.relpath(root, directory)
            cartella_file_count[relative_root] = len(files)
            total_files += len(files)

            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_size_kb = os.path.getsize(file_path) / 1024
                relative_path = os.path.relpath(file_path, directory)  # Relative path for better identification
                file_stats[relative_path] = file_size_kb
                print(f" - {relative_path}: {file_size_kb:.2f} KB")

        # Output of the number of files per folder
        print("\nNumber of files per folder:")
        for cartella, count in cartella_file_count.items():
            print(f" - {cartella}: {count} files")

        # Print the total number of files
        print(f"\nTotal number of files in the directory '{directory}': {total_files} files")

        return file_stats, cartella_file_count

    def crea_grafico_statistiche(file_stats):
        if not file_stats:
            print("No files found. Skipping chart creation.")
            return

        # Sort files by size (X) in ascending order
        sorted_file_stats = dict(sorted(file_stats.items(), key=lambda item: item[1]))

        # Sort files by size (X)
        file_names = list(sorted_file_stats.keys())
        file_sizes = list(sorted_file_stats.values())

        # Create the chart
        plt.figure(figsize=(12, 8))
        plt.bar(file_names, file_sizes, color='skyblue')
        plt.ylabel('Size (KB)')
        plt.xlabel('File')
        plt.title('File sizes in the ARM folder')
        plt.xticks(rotation=90)  # Rotate X-axis labels for visibility
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.show()

    def crea_grafico_statistiche_testuale(file_stats):
        if not file_stats:
            print("No files found. Skipping textual chart creation.")
            return

        # Sort files by size (X) in ascending order
        sorted_file_stats = dict(sorted(file_stats.items(), key=lambda item: item[1]))

        # Sort files by size (X)
        file_names = list(sorted_file_stats.keys())
        file_sizes = list(sorted_file_stats.values())

        # Find the maximum size to scale the height of the chart
        max_size = max(file_sizes)
        scale_factor = 50  # Number of characters to represent the maximum size

        # Print the chart
        print("\nFile size statistics (textual chart):")
        print(f"{'File':<50} {'Size (KB)'}")
        print("-" * 60)
        
        for name, size in zip(file_names, file_sizes):
            bar_length = int((size / max_size) * scale_factor)  # Calculate bar length
            bar = '*' * bar_length
            print(f"{name:<50} {size:.2f} KB | {bar}")

        # Add a line to separate labels from data
        print(f"{'':<50} {'-' * scale_factor}")
        print(f"{'':<50} {'<-- Size (in KB)'}")

    def calcola_media_dimensioni(file_stats):
        if not file_stats:
            print("No files found. Unable to calculate the average.")
            return 0

        # Calculate the total size and the total number of files
        somma_dimensioni = sum(file_stats.values())
        numero_file = len(file_stats)

        # Calculate the average
        media_dimensioni = somma_dimensioni / numero_file

        print(f"Average file size: {media_dimensioni:.2f} KB, for {numero_file} files")
        
        # Reduce the average by 20%
        soglia_kb = media_dimensioni * 0.9

        print(f"Threshold based on 20% reduced average: {soglia_kb:.2f} KB")
        return soglia_kb

    def riduci_numero_file(directory, soglia_totale=300):
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            return

        # Step 1: Count the total number of files and files per folder
        file_paths_per_cartella = {}
        total_files = 0

        for root, dirs, files in os.walk(directory):
            if files:
                relative_root = os.path.relpath(root, directory)
                file_paths_per_cartella[relative_root] = [os.path.join(root, file) for file in files]
                total_files += len(files)

        # If there are fewer files than the threshold, do nothing
        if total_files <= soglia_totale:
            print(f"The total number of files ({total_files}) is already less than or equal to the threshold ({soglia_totale}). No action needed.")
            return

        # Step 2: Calculate the target number of files per folder
        num_cartelle = len(file_paths_per_cartella)
        target_files_per_cartella = soglia_totale // num_cartelle
        extra_files = soglia_totale % num_cartelle

        # Step 3: Reduce files per folder in a semi-random way
        files_to_remove = []

        for cartella, file_paths in file_paths_per_cartella.items():
            num_files_in_cartella = len(file_paths)
            if num_files_in_cartella > target_files_per_cartella:
                num_files_to_remove = num_files_in_cartella - target_files_per_cartella
                if extra_files > 0:
                    num_files_to_remove -= 1  # Subtract one to account for the extra we will add later
                    extra_files -= 1
                if num_files_to_remove > 0:
                    files_to_remove.extend(random.sample(file_paths, num_files_to_remove))

        # Remove files
        print(f"Removing {len(files_to_remove)} files to reach the threshold of {soglia_totale} total files.")
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f" - File '{file_path}' removed.")
            except Exception as e:
                print(f"Error removing file '{file_path}': {e}")

        # Final verification
        _, cartella_file_count = ManagerTool.numero_file_per_cartella(directory)
        total_remaining_files = sum(cartella_file_count.values())
        print(f"Total remaining files after reduction: {total_remaining_files} (Threshold: {soglia_totale})")

    def riduci_numero_file_maggiori_occorrenze(directory, soglia_totale=300):
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            return

        # Step 1: Count the total number of files and files per folder
        file_paths_per_cartella = {}
        total_files = 0

        for root, dirs, files in os.walk(directory):
            if files:
                relative_root = os.path.relpath(root, directory)
                file_paths_per_cartella[relative_root] = [os.path.join(root, file) for file in files]
                total_files += len(files)

        # If there are fewer files than the threshold, do nothing
        if total_files <= soglia_totale:
            print(f"The total number of files ({total_files}) is already less than or equal to the threshold ({soglia_totale}). No action needed.")
            return

        # Step 2: Calculate the target number of files per folder
        num_cartelle = len(file_paths_per_cartella)
        target_files_per_cartella = soglia_totale // num_cartelle
        extra_files = soglia_totale % num_cartelle

        # Step 3: Count file occurrences
        file_counter = Counter()
        file_to_paths = {}
        
        for file_paths in file_paths_per_cartella.values():
            file_names = [os.path.basename(file_path) for file_path in file_paths]
            file_counter.update(file_names)
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                if file_name not in file_to_paths:
                    file_to_paths[file_name] = []
                file_to_paths[file_name].append(file_path)

        # Step 4: Select files with the most occurrences
        sorted_files_by_occurrences = [file for file, count in file_counter.most_common()]
        selected_files = sorted_files_by_occurrences[:soglia_totale]

        # Step 5: Distribute the selected files
        selected_file_paths = {file: file_to_paths[file] for file in selected_files}

        files_to_remove = []

        for cartella, file_paths in file_paths_per_cartella.items():
            num_files_in_cartella = len(file_paths)
            if num_files_in_cartella > target_files_per_cartella:
                num_files_to_remove = num_files_in_cartella - target_files_per_cartella
                if extra_files > 0:
                    num_files_to_remove -= 1  # Subtract one to account for the extra we will add later
                    extra_files -= 1
                if num_files_to_remove > 0:
                    files_to_remove.extend(random.sample(file_paths, num_files_to_remove))

        # Remove files
        print(f"Removing {len(files_to_remove)} files to reach the threshold of {soglia_totale} total files.")
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f" - File '{file_path}' removed.")
            except Exception as e:
                print(f"Error removing file '{file_path}': {e}")

        # Final verification
        _, cartella_file_count = ManagerTool.numero_file_per_cartella(directory)
        total_remaining_files = sum(cartella_file_count.values())
        print(f"Total remaining files after reduction: {total_remaining_files} (Threshold: {soglia_totale})")

    # Delete all files larger than a set threshold in KB
    def elimina_file_grandi(directory, soglia_kb=10):
        print(f"\nDeleting files larger than {soglia_kb}KB...")
        for root, dirs, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_size_kb = os.path.getsize(file_path) / 1024
                if file_size_kb > soglia_kb:
                    os.remove(file_path)
                    print(f" - File '{file_name}' deleted (Size: {file_size_kb:.2f} KB)")

    # Delete all files that do not fall within a specified size range in KB
    def elimina_file_fuori_intervallo(directory, soglia_min_kb=5, soglia_max_kb=11):
        print(f"\nDeleting files not between {soglia_min_kb}KB and {soglia_max_kb}KB...")
        for root, dirs, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_size_kb = os.path.getsize(file_path) / 1024
                if file_size_kb < soglia_min_kb or file_size_kb > soglia_max_kb:
                    os.remove(file_path)
                    print(f" - File '{file_name}' deleted (Size: {file_size_kb:.2f} KB)")


    # Total Statistics
    @staticmethod
    def analizza_struttura_cartelle(directory):
        if not os.path.isdir(directory):
            print(f"Invalid directory: {directory}")
            return None

        # Structured data
        struttura = {
            'totale': {'file_count': 0, 'total_size_kb': 0},
            'sottocartelle': {}
        }

        # Function to calculate the number of files and total size per folder
        def calcola_dati_per_cartella(dir_path):
            file_count = 0
            total_size_kb = 0

            for root, dirs, files in os.walk(dir_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    file_size_kb = os.path.getsize(file_path) / 1024
                    file_count += 1
                    total_size_kb += file_size_kb

            return file_count, total_size_kb

        # 1) Total number of files and total file size in the main folder
        struttura['totale']['file_count'], struttura['totale']['total_size_kb'] = calcola_dati_per_cartella(directory)

        # 2) Number of files and total size of files for each subfolder of ARM
        for root, dirs, files in os.walk(directory):
            for dir_name in dirs:
                sub_dir_path = os.path.join(root, dir_name)
                file_count, total_size_kb = calcola_dati_per_cartella(sub_dir_path)
                struttura['sottocartelle'][dir_name] = {
                    'file_count': file_count,
                    'total_size_kb': total_size_kb,
                    'sottocartelle': {}
                }

                # 3) Number of files and total file size for each subfolder of each subfolder
                for sub_root, sub_dirs, sub_files in os.walk(sub_dir_path):
                    for sub_dir_name in sub_dirs:
                        sub_sub_dir_path = os.path.join(sub_root, sub_dir_name)
                        sub_file_count, sub_total_size_kb = calcola_dati_per_cartella(sub_sub_dir_path)
                        struttura['sottocartelle'][dir_name]['sottocartelle'][sub_dir_name] = {
                            'file_count': sub_file_count,
                            'total_size_kb': sub_total_size_kb
                        }

        return struttura

    @staticmethod
    def analizza_struttura_cartelle_ridotte(directory):
        if not os.path.isdir(directory):
            print(f"Invalid directory: {directory}")
            return None

        # Structured data
        struttura = {
            'totale': {'file_count': 0, 'total_size_kb': 0},
            'sottocartelle': {}
        }

        # Function to calculate the number of files and total size per folder
        def calcola_dati_per_cartella(dir_path):
            file_count = 0
            total_size_kb = 0

            for root, _, files in os.walk(dir_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    file_size_kb = os.path.getsize(file_path) / 1024
                    file_count += 1
                    total_size_kb += file_size_kb

            return file_count, total_size_kb

        # 1) Total number of files and total file size in the main folder
        struttura['totale']['file_count'], struttura['totale']['total_size_kb'] = calcola_dati_per_cartella(directory)

        # 2) Number of files and total file size for each immediate subfolder of ARM
        for root, dirs, _ in os.walk(directory):
            if root == directory:
                for dir_name in dirs:
                    sub_dir_path = os.path.join(root, dir_name)
                    file_count, total_size_kb = calcola_dati_per_cartella(sub_dir_path)
                    struttura['sottocartelle'][dir_name] = {
                        'file_count': file_count,
                        'total_size_kb': total_size_kb
                    }
                break  # Exit the loop to avoid descending into deeper levels

        return struttura

    @staticmethod
    def analizza_numero_file(directory):
        if not os.path.isdir(directory):
            print(f"Invalid directory: {directory}")
            return None

        # Structured data
        struttura = {
            'totale': {'file_count': 0},
            'sottocartelle': {}
        }

        # Function to calculate the number of files per folder
        def calcola_file_per_cartella(dir_path):
            file_count = 0

            for root, _, files in os.walk(dir_path):
                file_count += len(files)

            return file_count

        # 1) Total number of files in the main folder
        struttura['totale']['file_count'] = calcola_file_per_cartella(directory)

        # 2) Number of files for each immediate subfolder of ARM
        for root, dirs, _ in os.walk(directory):
            if root == directory:
                for dir_name in dirs:
                    sub_dir_path = os.path.join(root, dir_name)
                    file_count = calcola_file_per_cartella(sub_dir_path)
                    struttura['sottocartelle'][dir_name] = {
                        'file_count': file_count
                    }
                break  # Exit the loop to avoid descending into deeper levels

        return struttura

    @staticmethod
    def salva_risultati_in_file(directory, file_name='results.json'):
        # Find the folder where the script is executed
        execution_folder = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(execution_folder, file_name)

        # Analyze the folder structure and save the results
        risultati = ManagerTool.analizza_struttura_cartelle(directory)
        with open(file_path, 'w') as file:
            json.dump(risultati, file, indent=4)
        print(f"Results saved to file: {file_path}")

    @staticmethod
    def salva_risultati_in_file_ridotte(directory, file_name='results.json'):
        # Find the folder where the script is executed
        execution_folder = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(execution_folder, file_name)

        # Analyze the folder structure and save the results
        risultati = ManagerTool.analizza_struttura_cartelle_ridotte(directory)
        with open(file_path, 'w') as file:
            json.dump(risultati, file, indent=4)
        print(f"Results saved to file: {file_path}")

    @staticmethod
    def salva_risultati_in_file_numero(directory, file_name='results.json'):
        # Find the folder where the script is executed
        execution_folder = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(execution_folder, file_name)

        # Analyze the folder structure and save the results
        risultati = ManagerTool.analizza_numero_file(directory)
        with open(file_path, 'w') as file:
            json.dump(risultati, file, indent=4)
        print(f"Results saved to file: {file_path}")

    @staticmethod
    def visualizza_statistiche(file_name):
        # Find the folder where the script is executed
        execution_folder = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(execution_folder, file_name)

        # Read data from the JSON file
        with open(file_path, 'r') as file:
            dati = json.load(file)

        # Create DataFrame for visualization
        dati_totale = dati.get('totale', {})
        sottocartelle = dati.get('sottocartelle', {})

        # Data for table and chart
        rows = []
        for cartella, info in sottocartelle.items():
            rows.append({'Folder': cartella, 'File Count': info['file_count'], 'Total Size (KB)': info['total_size_kb']})
            for sub_cartella, sub_info in info.get('sottocartelle', {}).items():
                rows.append({'Folder': f"{cartella} -> {sub_cartella}", 'File Count': sub_info['file_count'], 'Total Size (KB)': sub_info['total_size_kb']})

        df = pd.DataFrame(rows)

        # Create the chart
        plt.figure(figsize=(12, 8))
        for label, df_group in df.groupby('Folder'):
            plt.bar(df_group['Folder'], df_group['Total Size (KB)'], label=label)

        plt.xlabel('Folder')
        plt.ylabel('Total Size (KB)')
        plt.title('Total File Sizes per Folder')
        plt.xticks(rotation=90)
        plt.legend()
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.show()

        # Display the table
        print("\nStatistics Table:")
        print(df.to_string(index=False))

    @staticmethod
    def visualizza_statistiche_ridotte(file_name):
        # Find the folder where the script is executed
        execution_folder = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(execution_folder, file_name)
        
        # Read data from the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Initialize data structure for ARM and its subfolders
        data_arm = {
            'totale': data.get('totale', {}),
            'sottocartelle': {}
        }
        
        # Add only the immediate subfolders of the main ARM folder
        subfolders = data.get('sottocartelle', {})
        for folder, info in subfolders.items():
            data_arm['sottocartelle'][folder] = {
                'file_count': info['file_count'],
                'total_size_kb': info['total_size_kb']
            }

        # Create DataFrame for visualization
        rows = []
        # Add the information for the main ARM folder
        rows.append({
            'Cartella': 'ARM',
            'File Count': data_arm['totale']['file_count'],
            'Total Size (KB)': data_arm['totale']['total_size_kb']
        })
        # Add the information for the subfolders
        for folder, info in data_arm['sottocartelle'].items():
            rows.append({'Cartella': folder, 'File Count': info['file_count'], 'Total Size (KB)': info['total_size_kb']})

        df = pd.DataFrame(rows)
        
        # Create the chart
        plt.figure(figsize=(12, 8))
        plt.bar(df['Cartella'], df['Total Size (KB)'], color='skyblue')
        plt.xlabel('Folder')
        plt.ylabel('Total Size (KB)')
        plt.title('Total File Sizes per Folder (ARM and Subfolders)')
        plt.xticks(rotation=90)
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.show()

        # Create the table
        print("\nStatistics Table for ARM and Subfolders:")
        print(df.to_string(index=False))

    @staticmethod
    def visualizza_statistiche_numero(file_name):
        # Find the folder where the script is executed
        execution_folder = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(execution_folder, file_name)
        
        # Read data from the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Initialize data structure for ARM and its subfolders
        data_arm = {
            'totale': data.get('totale', {}),
            'sottocartelle': {}
        }
        
        # Add only the immediate subfolders of the main ARM folder
        subfolders = data.get('sottocartelle', {})
        for folder, info in subfolders.items():
            data_arm['sottocartelle'][folder] = {
                'file_count': info['file_count']
            }

        # Create DataFrame for visualization
        rows = []
        # Add the information for the main ARM folder
        rows.append({
            'Cartella': 'ARM',
            'File Count': data_arm['totale']['file_count']
        })
        # Add the information for the subfolders
        for folder, info in data_arm['sottocartelle'].items():
            rows.append({'Cartella': folder, 'File Count': info['file_count']})

        df = pd.DataFrame(rows)
        
        # Create the chart
        plt.figure(figsize=(12, 8))
        plt.bar(df['Cartella'], df['File Count'], color='skyblue')
        plt.xlabel('Folder')
        plt.ylabel('Number of Files')
        plt.title('Total Number of Files per Folder (ARM and Subfolders)')
        plt.xticks(rotation=90)
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.show()

        # Create the table
        print("\nStatistics Table for ARM and Subfolders:")
        print(df.to_string(index=False))