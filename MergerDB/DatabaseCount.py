import sqlite3

class DatabaseAnalyzer:
    """Class to analyze a SQLite database and count files based on different criteria."""

    def __init__(self, db_path):
        self.db_path = db_path

    def count_files_in_database(self):
        """Return the total number of files (rows in the 'info' table) in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM info")
            count = cur.fetchone()[0]

            return count
        except sqlite3.Error as e:
            print(f"Errore SQLite: {e}")
            return None
        finally:
            conn.close()

    def count_files_by_library_and_version(self):
        """Count files for each combination of library and version."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # Query to count files for each combination of library and version
            cur.execute('''
                SELECT libreria, versione_libreria, COUNT(*) as file_count
                FROM info
                GROUP BY libreria, versione_libreria
                ORDER BY libreria, versione_libreria
            ''')

            rows = cur.fetchall()

            # Print results: library + version and number of files
            print("Library + Version | Number of files")
            print("-------------------------------------")
            for row in rows:
                print(f"{row[0]} {row[1]} | {row[2]}")

        except sqlite3.Error as e:
            print(f"Errore SQLite: {e}")
        finally:
            conn.close()

    def count_files_by_library(self):
        """Count files for each library, ignoring the version."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # Query to count files for each library without considering the version
            cur.execute('''
                SELECT libreria, COUNT(*) as file_count
                FROM info
                GROUP BY libreria
                ORDER BY libreria
            ''')

            rows = cur.fetchall()

            # Print results: library and number of files
            print("Library | Number of files")
            print("------------------------")
            for row in rows:
                print(f"{row[0]} | {row[1]}")

        except sqlite3.Error as e:
            print(f"Errore SQLite: {e}")
        finally:
            conn.close()


"""
# Example usage:
if __name__ == "__main__":
    db_path = "path/to/your/database.db"  # Replace with your database path
    analyzer = DatabaseAnalyzer(db_path)

    total_files = analyzer.count_files_in_database()
    print(f"Total number of files in the database: {total_files}")

    analyzer.count_files_by_library_and_version()
    analyzer.count_files_by_library()
"""