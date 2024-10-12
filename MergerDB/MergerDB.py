import random
import sqlite3
import os
import re
from DatabaseCount import DatabaseAnalyzer
from DatabaseFileSelecter import DatabaseFileSelector
from DatabaseMerger import DatabaseMerger

def main():
    # Path to the folder containing the original SQLite databases and the new merged database
    db_folder_path = 'MergingMachine'
    merged_db_path = 'Merged.db'
    decomposed_db = 'bzoc500.db'
    decomposed_db_opt = 'bzoc500.db'

    # Merge all databases from the specified folder
    merger = DatabaseMerger(db_folder_path, merged_db_path)
    merger.merge_databases()

    analyzer = DatabaseAnalyzer(merged_db_path)

    # Count the files in the merged database
    total_files = analyzer.count_files_in_database()
    print(f"Total number of files in the database: {total_files}")

    # Count files by library and version
    analyzer.count_files_by_library_and_version()

    # Count files by library only
    analyzer.count_files_by_library()


    selector = DatabaseFileSelector(decomposed_db_opt)

    # Execute the function to create 50 databases from 1 database
    output_folder = 'selected_files_databases'
    selector.create_databases_from_selection(output_folder)
    print(f"Created 50 databases in the folder '{output_folder}'")

    # Execute the function to create different databases based on the specified distribution, divided by optimization levels
    output_folder = 'optimization_division_databases'
    selector.create_databases_from_selection_optimization_level(output_folder)
    print(f"Created databases divided by optimization level in '{output_folder}'")

if __name__ == "__main__":
    main()
