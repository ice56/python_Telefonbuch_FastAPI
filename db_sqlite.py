import sqlite3
from pathlib import Path
import os
import logging

class Database():
    def __init__(self):
        self.name = "Database"
        self.db_name = "phonebook.db"
        self.db_pfad = Path(__file__).parent / self.db_name
        self.ist_neu = not os.path.exists(self.db_pfad)
        self.table_name = "users"
        self.logger = logging.getLogger(__name__)
        self.conn, self.c = self._verbindung_herstellen()        

    def _verbindung_herstellen(self):
        self.logger.debug("start _verbindung_herstellen") 
        try:            
            if self.ist_neu:
                conn, c = self.create_db(self.db_pfad)
                self.ist_neu = False
            else:
                conn = sqlite3.connect(self.db_pfad)
                c = conn.cursor()
                
            return conn, c
        except sqlite3.Error as e:
            print(f"Fehler beim Verbinden: {e}")
            self.logger.error(f"Fehler beim Verbinden: {e}")
            return None, None


    def create_db(self, name):
        conn = sqlite3.connect(name)
        c = conn.cursor()

        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "first_name": "TEXT NOT NULL",
            "last_name": "TEXT",
            "phone_prefix": "TEXT",
            "phone": "TEXT",
            "deleted": "INTEGER",
        }
        self.conn = conn
        self.c = c

        self.create_table(**columns)
        conn.commit()

        print("db und tabelle erstellt")
        self.logger.info("db und tabelle erstellt")
        
        return conn, c

    def create_table(self, **parms):
        """Erstellt eine Tabelle dynamisch basierend auf den übergebenen Parametern."""
        self.logger.debug(f"Start create_table parms:{parms}") 
        
        if not self.conn or not self.c:
            self.logger.error("Keine offene Verbindung für die Tabellenerstellung gefunden.")
            return
    
        try:
            column_definitions = [f"{column_name} {column_type}" for column_name, column_type in parms.items()]
            columns_str = ", ".join(column_definitions)
            sql_query = f"CREATE TABLE IF NOT EXISTS {self.table_name} ({columns_str});"
            
            self.logger.debug(f"sql_query:{sql_query}") 
            
            self.c.execute(sql_query)
            self.conn.commit()
            
            self.logger.info(f"Tabelle '{self.table_name}' erfolgreich erstellt oder existiert bereits.")
            print(f"Tabelle '{self.table_name}' erfolgreich erstellt.")
    
        except sqlite3.Error as e:
            self.logger.error(f"Fehler beim Erstellen der Tabelle: {e}")
            print(f"Fehler beim Erstellen der Tabelle: {e}")            


    def select(self, columns=None, condition_str=None, condition_values=None, include_deleted=False):
        """
        Liest Daten aus einer Tabelle und gibt sie als Liste von Dictionaries zurück.
        
        :param columns:
        :param condition_str:
        :param condition_values:
        :param include_deleted: Wenn True, werden auch Einträge mit deleted = 1 geladen.
                                Standard ist False (nur aktive Einträge).                                
        """
        self.logger.debug(f"Start Select columns:{columns} condition_str:{condition_str} condition_values:{condition_values}") 
        conn, c = self._verbindung_herstellen()
        if not conn or not c:
            return []

        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        try:
            if columns:
                spalten_str = columns if isinstance(columns, str) else ", ".join(columns)
            else:
                spalten_str = "*"

            sql_query = f"SELECT {spalten_str} FROM {self.table_name}"
            self.logger.debug(f"SELECT: {sql_query}") 
            if include_deleted:
                if condition_str:
                    sql_query += f" WHERE {condition_str}"
            else:
                if condition_str:
                    sql_query += f" WHERE ({condition_str}) AND deleted = 0"
                else:
                    sql_query += " WHERE deleted = 0"

            self.logger.debug(f"condition_values: {condition_values}") 
            c.execute(sql_query, condition_values or ())

            rows = c.fetchall()
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            print(f"Fehler beim Abrufen der Daten: {e}")
            self.logger.error(f"Fehler beim Abrufen der Daten: {e}") 
            return []
        finally:
            conn.close()

    def insert(self, object):
        """
        Fügt ein Person-Objekt in die Datenbank ein und speichert 
        die generierte ID direkt im Objekt ab.
        object: erwartet ein User objekt
        """
        self.logger.debug("start insert") 
        #conn, c = self._verbindung_herstellen(db_name)
        conn, c = self._verbindung_herstellen()
        if not conn or not c:
            return False

        try:
            data_dict = object.to_dict(include_id=False)

            columns = ", ".join(data_dict.keys())
            placeholder = ", ".join(["?"] * len(data_dict))
            sql_query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholder})"
            self.logger.debug(f"INSERT str: {sql_query}") 
            c.execute(sql_query, tuple(data_dict.values()))
            conn.commit()
            self.logger.debug(f"lastrowid: {c.lastrowid}") 
            object.id = c.lastrowid
            
            print(f"Erfolgreich gespeichert! Neue Personen-ID ist: {object.id}")
            self.logger.info(f"Erfolgreich gespeichert! Neue Personen-ID ist: {object.id}") 
            return True, object

        except sqlite3.Error as e:
            print(f"Fehler beim Einfügen eines Users: {e}")
            self.logger.error(f"Fehler beim Einfügen eines Users: {e}") 
            return False, object
        finally:
            conn.close()

    def update(self, data_dict, condition_str, condition_values):
        """
        Aktualisiert bestehende Datensätze dynamisch mithilfe eines Dictionaries.
        Voraussetzung: condition_str MUSS angegeben werden (Sicherheitsfeature).
        
        :param data_dict: Ein Dictionary mit den Spalten und neuen Werten, z.B. {"phone_number": "123"}
        :condition_str
        condition_values
        """
        self.logger.debug(f"start update data_dict:{data_dict} condition_str:{condition_str} condition_values:{condition_values}") 
        if not data_dict:
            print("Fehler: Keine Daten zum Aktualisieren übergeben.")
            return False
            
        if not condition_str:
            print("Fehler: Eine WHERE-Bedingung ist für das Update zwingend erforderlich!")
            return False

        conn, c = self._verbindung_herstellen()
        if not conn or not c:
            return False

        try:
            set_parts = [f"{spalte} = ?" for spalte in data_dict.keys()]
            set_str = ", ".join(set_parts)
            sql_query = f"UPDATE {self.table_name} SET {set_str} WHERE {condition_str}"
            self.logger.debug(f"sql_query: {sql_query}") 
            query_values = tuple(data_dict.values()) + tuple(condition_values)
            self.logger.debug(f"query_values: {query_values}") 
            c.execute(sql_query, query_values)
            conn.commit()
            
            print(f"Erfolgreich {c.rowcount} Datensatz/Datensätze aktualisiert.")
            return True

        except sqlite3.Error as e:
            print(f"Fehler beim Aktualisieren der Daten: {e}")
            self.logger.error(f"Fehler beim Aktualisieren der Daten: {e}") 
            return False
        finally:
            conn.close()

    def delete(self, condition_str, condition_values):
        """
        Markiert Datensätze als gelöscht (Soft Delete), indem 'deleted = 1' gesetzt wird.
        Voraussetzung: condition_str MUSS angegeben werden (Sicherheitsfeature).
        """
        self.logger.debug(f"start delete condition_str:{condition_str} condition_values:{condition_values}") 
        if not condition_str:
            print("Fehler: Eine WHERE-Bedingung ist für das Löschen zwingend erforderlich!")
            return False

        conn, c = self._verbindung_herstellen()
        if not conn or not c:
            return False

        try:

            sql_query = f"UPDATE {self.table_name} SET deleted = 1 WHERE {condition_str}"
            self.logger.debug(f"Update str: {sql_query}") 
            c.execute(sql_query, condition_values)
            conn.commit()
            
            print(f"Erfolgreich {c.rowcount} Datensatz/Datensätze als gelöscht markiert.")
            return True

        except sqlite3.Error as e:
            print(f"Fehler beim Soft-Delete der Daten: {e}")
            self.logger.error(f"Fehler beim Soft-Delete der Daten: {e}") 
            return False
        finally:
            conn.close()
