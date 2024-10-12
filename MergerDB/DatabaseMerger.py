import os
import sqlite3

class DatabaseMerger:
    """Class to merge all .db databases from a specified directory into a single database."""

    def __init__(self, db_folder_path, merged_db_path):
        self.db_folder_path = db_folder_path
        self.merged_db_path = merged_db_path

    def merge_databases(self):
        # Remove the merged database if it already exists
        if os.path.exists(self.merged_db_path):
            os.remove(self.merged_db_path)

        # Connect to the new merged database
        merged_conn = sqlite3.connect(self.merged_db_path)
        merged_cur = merged_conn.cursor()

        # Create tables in the new database
        merged_cur.execute('''
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

        merged_cur.execute('''
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

        merged_conn.commit()

        # Function to copy data from the info table and map IDs
        def copy_info_data(cur_source, cur_dest):
            id_map = {}
            cur_source.execute("SELECT id, filename, namef, libreria, versione_libreria, compilatore, versione_compilatore, architettura, filetype, call_graph FROM info")
            rows = cur_source.fetchall()

            for row in rows:
                cur_dest.execute('''
                    INSERT INTO info (filename, namef, libreria, versione_libreria, compilatore, versione_compilatore, architettura, filetype, call_graph)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row[1:])  # Exclude ID since it will be generated automatically
                new_id = cur_dest.lastrowid
                id_map[row[0]] = new_id

            return id_map


        # Function to copy data from the function_info table with mapped IDs
        def copy_function_info_data(cur_source, cur_dest, id_map):
            cur_source.execute("SELECT function_id, filename_id, function_name, entry_point, address, assembly_code, bytecodes, bfs_result, dfs_result FROM function_info")
            rows = cur_source.fetchall()

            for row in rows:
                new_filename_id = id_map.get(row[1])
                cur_dest.execute('''
                    INSERT INTO function_info (filename_id, function_name, entry_point, address, assembly_code, bytecodes, bfs_result, dfs_result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (new_filename_id, row[2], row[3], row[4], row[5], row[6], row[7], row[8]))

        # Iterate through all .db files in the specified folder
        for db_file in os.listdir(self.db_folder_path):
            if db_file.endswith('.db'):
                db_file_path = os.path.join(self.db_folder_path, db_file)

                # Connect to the current database
                conn = sqlite3.connect(db_file_path)
                cur = conn.cursor()

                try:
                    # Copy data from the info and function_info tables of the current database
                    id_map = copy_info_data(cur, merged_cur)
                    copy_function_info_data(cur, merged_cur, id_map)

                    # Commit changes
                    merged_conn.commit()
                    print(f"Merged {db_file} into the database {self.merged_db_path}")
                except sqlite3.Error as e:
                    print(f"SQLite error during merging of {db_file}: {e}")
                finally:
                    # Close the connection to the current database
                    conn.close()

        # Close the connection to the merged database
        merged_conn.close()

"""
# Example usage:
if __name__ == "__main__":
    db_folder = "path/to/db/folder"  # Replace with your database folder path
    merged_db = "merged_database.db"  # Replace with your desired merged database path
    merger = DatabaseMerger(db_folder, merged_db)
    merger.merge_databases()
"""