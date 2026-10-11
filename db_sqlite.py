import sqlite3
from pathlib import Path
import os
from user import User

class Database():
    def __init__(self):
        self.name = "Database"
        
    def create_db(self, name):
        conn, c = self._verbindung_herstellen(name)
        conn.commit()
        conn.close()
        print("db erstellt")

    def create_table(self, db_name, table_name, **parms):
        """
        Erstellt eine Tabelle dynamisch basierend auf den übergebenen Parametern.
        Beispiel: db.create_table("meine_db.db", "users", id="INTEGER PRIMARY KEY", name="TEXT")
        """
        conn, c = self._verbindung_herstellen(db_name)
        if not conn or not c:
            return  

        try:
            column_definitions = [f"{column_name} {column_type}" for column_name, column_type in parms.items()]
            columns_str = ", ".join(column_definitions)
            sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str});"

            c.execute(sql_query)
            conn.commit()
            print(f"Tabelle '{table_name}' erfolgreich erstellt oder existiert bereits.")
            
        except sqlite3.Error as e:
            print(f"Fehler beim Erstellen der Tabelle: {e}")
            
        finally:
            conn.close()

    def _verbindung_herstellen(self, db_name):
        try:
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            return conn, c
        except sqlite3.Error as e:
            print(f"Fehler beim Verbinden: {e}")
            return None, None

    def insert_user(self, db_name, table_name, person_object):
        """
        Fügt ein Person-Objekt in die Datenbank ein und speichert 
        die generierte ID direkt im Objekt ab.
        """
        conn, c = self._verbindung_herstellen(db_name)
        if not conn or not c:
            return False

        try:
            data_dict = person_object.to_dict(include_id=False)

            columns = ", ".join(data_dict.keys())
            placeholder = ", ".join(["?"] * len(data_dict))
            sql_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholder})"
            
            c.execute(sql_query, tuple(data_dict.values()))
            conn.commit()
            
            person_object.id = c.lastrowid
            
            print(f"Erfolgreich gespeichert! Neue Personen-ID ist: {person_object.id}")
            return True

        except sqlite3.Error as e:
            print(f"Fehler beim Einfügen eines Users: {e}")
            return False
        finally:
            conn.close()

    def fetch_data(self, db_name, table_name, columns=None, condition_str=None, condition_values=None, include_deleted=False):
        """
        Liest Daten aus einer Tabelle und gibt sie als Liste von Dictionaries zurück.
        
        :param include_deleted: Wenn True, werden auch Einträge mit deleted = 1 geladen.
                                Standard ist False (nur aktive Einträge).
        """
        conn, c = self._verbindung_herstellen(db_name)
        if not conn or not c:
            return []

        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        try:
            if columns:
                spalten_str = columns if isinstance(columns, str) else ", ".join(columns)
            else:
                spalten_str = "*"

            sql_query = f"SELECT {spalten_str} FROM {table_name}"

            if include_deleted:
                if condition_str:
                    sql_query += f" WHERE {condition_str}"
            else:
                if condition_str:
                    sql_query += f" WHERE ({condition_str}) AND deleted = 0"
                else:
                    sql_query += " WHERE deleted = 0"

            c.execute(sql_query, condition_values or ())

            rows = c.fetchall()
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            print(f"Fehler beim Abrufen der Daten: {e}")
            return []
        finally:
            conn.close()

    def delete_data(self, db_name, table_name, condition_str, condition_values):
        """
        Markiert Datensätze als gelöscht (Soft Delete), indem 'deleted = 1' gesetzt wird.
        Voraussetzung: condition_str MUSS angegeben werden (Sicherheitsfeature).
        """
        if not condition_str:
            print("Fehler: Eine WHERE-Bedingung ist für das Löschen zwingend erforderlich!")
            return False

        conn, c = self._verbindung_herstellen(db_name)
        if not conn or not c:
            return False

        try:

            sql_query = f"UPDATE {table_name} SET deleted = 1 WHERE {condition_str}"
            
            c.execute(sql_query, condition_values)
            conn.commit()
            
            print(f"Erfolgreich {c.rowcount} Datensatz/Datensätze als gelöscht markiert.")
            return True

        except sqlite3.Error as e:
            print(f"Fehler beim Soft-Delete der Daten: {e}")
            return False
        finally:
            conn.close()

        def update_data(self, db_name, table_name, data_dict, condition_str, condition_values):
            """
            Aktualisiert bestehende Datensätze dynamisch mithilfe eines Dictionaries.
            Voraussetzung: condition_str MUSS angegeben werden (Sicherheitsfeature).
            
            :param data_dict: Ein Dictionary mit den Spalten und neuen Werten, z.B. {"phone": "123"}
            """
            if not data_dict:
                print("Fehler: Keine Daten zum Aktualisieren übergeben.")
                return False
                
            if not condition_str:
                print("Fehler: Eine WHERE-Bedingung ist für das Update zwingend erforderlich!")
                return False

            conn, c = self._verbindung_herstellen(db_name)
            if not conn or not c:
                return False

            try:
                set_parts = [f"{spalte} = ?" for spalte in data_dict.keys()]
                set_str = ", ".join(set_parts)
                sql_query = f"UPDATE {table_name} SET {set_str} WHERE {condition_str}"  
                query_values = tuple(data_dict.values()) + tuple(condition_values)

                c.execute(sql_query, query_values)
                conn.commit()
                
                print(f"Erfolgreich {c.rowcount} Datensatz/Datensätze aktualisiert.")
                return True

            except sqlite3.Error as e:
                print(f"Fehler beim Aktualisieren der Daten: {e}")
                return False
            finally:
                conn.close()

    def save_user(self, db_name, table_name, person_object):
        """
        Speichert eine Person ab. 
        Erstellt sie neu (INSERT), wenn sie noch keine ID hat.
        Aktualisiert sie (UPDATE), wenn bereits eine ID vorhanden ist.
        """
        if person_object.id is None:
            return self.insert_user(db_name, table_name, person_object)
        else:            

            data_dict = person_object.to_dict(include_id=False)
        
            return self.update_data(
                db_name=db_name,
                table_name=table_name,
                data_dict=data_dict,
                condition_str="id = ?",
                condition_values=(person_object.id,)
            )

    def search_persons(self, db_name, table_name, search_term):
        """
        Durchsucht die Spalten 'id', 'first_name' und 'last_name' nach dem Suchbegriff.
        Berücksichtigt automatisch 'deleted = 0' und gibt eine Liste von User-Objekten zurück.
        """
        if not search_term or not search_term.strip():
            return []

        such_text = search_term.strip()
        like_value = f"%{such_text}%"

        if such_text.isdigit():
            condition_str = "id = ? OR first_name LIKE ? OR last_name LIKE ?"
            condition_values = (int(such_text), like_value, like_value)
        else:
            condition_str = "first_name LIKE ? OR last_name LIKE ?"
            condition_values = (like_value, like_value)

        rows_dict = self.fetch_data(
            db_name=db_name,
            table_name=table_name,
            condition_str=condition_str,
            condition_values=condition_values
        )

        return [User.from_dict(row) for row in rows_dict]

    def update_data(self, db_name, table_name, data_dict, condition_str, condition_values):
        """
        Aktualisiert bestehende Datensätze dynamisch mithilfe eines Dictionaries.
        Voraussetzung: condition_str MUSS angegeben werden (Sicherheitsfeature).
        
        :param data_dict: Ein Dictionary mit den Spalten und neuen Werten, z.B. {"phone_number": "123"}
        """
        if not data_dict:
            print("Fehler: Keine Daten zum Aktualisieren übergeben.")
            return False
            
        if not condition_str:
            print("Fehler: Eine WHERE-Bedingung ist für das Update zwingend erforderlich!")
            return False

        conn, c = self._verbindung_herstellen(db_name)
        if not conn or not c:
            return False

        try:
            set_parts = [f"{spalte} = ?" for spalte in data_dict.keys()]
            set_str = ", ".join(set_parts)
            sql_query = f"UPDATE {table_name} SET {set_str} WHERE {condition_str}"
            query_values = tuple(data_dict.values()) + tuple(condition_values)

            c.execute(sql_query, query_values)
            conn.commit()
            
            print(f"Erfolgreich {c.rowcount} Datensatz/Datensätze aktualisiert.")
            return True

        except sqlite3.Error as e:
            print(f"Fehler beim Aktualisieren der Daten: {e}")
            return False
        finally:
            conn.close()


def main():
    """
    db_name = "phonebook.db"  
    table_name = "users"
    """
    db_name = "phonebook.db"  
    table_name = "users"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, db_name)
    
    db = Database()
    results = db.fetch_data(
        db_path,
        table_name)

    for user in results:
        print(f"ID: {user['id']}. Name: {user['first_name']} {user['last_name']}, Telefon: {user['phone_prefix']} {user['phone']}")

if __name__ == "__main__":
    main()
