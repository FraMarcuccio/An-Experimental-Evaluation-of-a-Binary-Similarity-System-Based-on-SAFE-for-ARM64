import os
import sqlite3

class DatabaseFileSelector:
    """Class to select random files from a SQLite database and create new databases."""

    def __init__(self, db_path):
        self.db_path = db_path

    def select_random_files_for_library(self, cur, library_name, file_count):
        """Select a specific number of random files for a given library."""
        cur.execute('''
            SELECT id, filename
            FROM info
            WHERE libreria = ?
            ORDER BY RANDOM()
            LIMIT ?
        ''', (library_name, file_count))
        
        return cur.fetchall()   # Returns a list of tuples (id, filename)

    def create_single_file_database(self, original_conn, file_id, new_db_path):
        """Copy data of a selected file into a new database."""
        new_conn = sqlite3.connect(new_db_path)
        cur_original = original_conn.cursor()
        cur_new = new_conn.cursor()

        # Create tables in the new database
        cur_new.execute('''
            CREATE TABLE IF NOT EXISTS info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                namef TEXT,
                libreria TEXT,
                versione_libreria TEXT,
                compilatore TEXT,
                versione_compilatore TEXT,
                architettura TEXT,
                filetype TEXT,
                call_graph TEXT
            )
        ''')

        cur_new.execute('''
            CREATE TABLE IF NOT EXISTS function_info (
                function_id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename_id INTEGER,
                function_name TEXT,
                entry_point TEXT,
                address TEXT,
                assembly_code TEXT,
                bytecodes TEXT,
                bfs_result TEXT,
                dfs_result TEXT,
                FOREIGN KEY (filename_id) REFERENCES info (id)
            )
        ''')

        # Copy data from the 'info' table
        cur_original.execute("SELECT * FROM info WHERE id = ?", (file_id,))
        row = cur_original.fetchone()

        cur_new.execute('''
            INSERT INTO info (filename, namef, libreria, versione_libreria, compilatore, versione_compilatore, architettura, filetype, call_graph)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row[1:]) # Exclude ID since it will be generated automatically

        # Get the generated ID for the 'info' table in the new database
        new_file_id = cur_new.lastrowid

        # Copy data from the 'function_info' table related to the selected file
        cur_original.execute("SELECT * FROM function_info WHERE filename_id = ?", (file_id,))
        function_info_rows = cur_original.fetchall()

        for function_row in function_info_rows:
            cur_new.execute('''
                INSERT INTO function_info (filename_id, function_name, entry_point, address, assembly_code, bytecodes, bfs_result, dfs_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (new_file_id, function_row[2], function_row[3], function_row[4], function_row[5], function_row[6], function_row[7], function_row[8]))

        # Commit changes and close the connection
        new_conn.commit()
        new_conn.close()

    def create_databases_from_selection(self, output_folder):
        """Select random files and create new databases for each selected file."""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Connect to the unified database
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Requested distribution
        distribution = {
            'boost': 10,
            'openssl': 10,
            'zlib': 15,
            'curl': 15
        }

        selected_files = []

        # Select random files for each library
        for library, count in distribution.items():
            selected_files += self.select_random_files_for_library(cur, library, count)

        # Create a new database for each selected file
        for i, (file_id, filename) in enumerate(selected_files):
            new_db_path = os.path.join(output_folder, f"file_{i + 1}.db")
            self.create_single_file_database(conn, file_id, new_db_path)

        conn.close()

    def select_random_files_for_library_and_optimization(self, cur, library_name, file_count, optimization_level):
        """Select a specific number of random files for a given library and optimization level."""
        optimization_str = f"Optimization{optimization_level}"
        
        cur.execute('''
            SELECT id, filename
            FROM info
            WHERE libreria = ? AND filename LIKE ?
            ORDER BY RANDOM()
            LIMIT ?
        ''', (library_name, f"%{optimization_str}%", file_count))
        
        return cur.fetchall()  # Returns a list of tuples (id, filename)

    def create_databases_from_selection_optimization_level(self, output_folder):
        """Select random files based on optimization level and create new databases."""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Connect to the unified database
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Requested distribution
        distribution = {
            'zlib': 40
        }

        # Optimization level selection
        optimization_levels = [0, 1, 2, 3]

        # Create directories for each optimization level
        for level in optimization_levels:
            optimization_folder = os.path.join(output_folder, f"Optimization{level}")
            if not os.path.exists(optimization_folder):
                os.makedirs(optimization_folder)

        # Select random files for each library and optimization level
        file_counter = 1  # Counter for file names
        for library, count in distribution.items():
            files_per_optimization = count // len(optimization_levels)  # Divide total by number of optimizations

            for level in optimization_levels:
                selected_files = self.select_random_files_for_library_and_optimization(cur, library, files_per_optimization, level)

                # Create databases for selected files
                for file_id, filename in selected_files:
                    new_db_path = os.path.join(output_folder, f"Optimization{level}", f"file_{file_counter}.db")
                    self.create_single_file_database(conn, file_id, new_db_path)
                    file_counter += 1

        conn.close()


"""
# Example usage:
if __name__ == "__main__":
    db_path = "path/to/your/database.db"  # Replace with your database path
    output_folder = "path/to/output/folder"  # Replace with your output folder path
    selector = DatabaseFileSelector(db_path)

    # Create databases from selection
    selector.create_databases_from_selection(output_folder)

    # Create databases from selection based on optimization level
    selector.create_databases_from_selection_optimization_level(output_folder)
"""