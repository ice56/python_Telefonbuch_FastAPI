import logging
from db_sqlite import Database as DB

class User:
    def __init__(self, first_name="", last_name="", phone_prefix="", phone="", deleted=0, id=None):
        self.id = id  
        self.first_name = first_name
        self.last_name = last_name
        self.phone_prefix = phone_prefix
        self.phone = phone
        self.deleted = deleted
        self.logger = logging.getLogger(__name__)
        self.db = DB()
        
    def __del__(self):              #Dekonstrukter
        pass



    @classmethod    #Dekoratoren
    def from_dict(cls, db_dict):
        """
        Erstellt ein Person-Objekt aus einem Datenbank-Dictionary.
        """
        if not db_dict:
            return None
            
        return cls(
            id=db_dict.get("id"), 
            first_name=db_dict.get("first_name", ""),
            last_name=db_dict.get("last_name", ""),
            phone_prefix=db_dict.get("phone_prefix", ""),
            phone=db_dict.get("phone", ""),
            deleted=db_dict.get("deleted", 0)
        )

    def to_dict(self, include_id=False):
        """
        Wandelt das Objekt in ein Dict um.
        :param include_id: True für Updates (WHERE id = ?), False für Inserts (da die DB die ID generiert)
        """
        daten = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_prefix": self.phone_prefix,
            "phone": self.phone,
            "deleted": self.deleted
        }
        if include_id:
            daten["id"] = self.id
        return daten
    
    def insert_user(self, user_object):
            """
            Fügt einen Kontakt in die DB ein
            user_object: User Objekt
            """
            self.logger.debug(f"start insert_user user_object:{user_object}") 
            try:                
                insert, user_object = self.db.insert("user", user_object)
                return True

            except Exception as e:
                self.logger.error(f"Fehler beim Einfügen eines Users: {e}") 
                print(f"Fehler beim Einfügen eines Users: {e}")
                return False
            finally:
                pass

    def save_user(self, person_object):
            """
            Speichert eine Person ab. 
            Erstellt sie neu (INSERT), wenn sie noch keine ID hat.
            Aktualisiert sie (UPDATE), wenn bereits eine ID vorhanden ist.
            """
            try:
                self.logger.debug(f"start save_user person_object:{person_object}") 
                if person_object.id is None:
                    self.logger.debug(f"person_object.id ist None:{person_object}")
                    return self.db.insert(person_object)
                else:            
        
                    data_dict = person_object.to_dict(include_id=False)
                    self.logger.debug(f"data_dict:{data_dict}")
                    return self.db.update(data_dict=data_dict,
                        condition_str="id = ?",
                        condition_values=(person_object.id,)
                    )                    
            except Exception as e:
                self.logger.error(f"Fehler beim Speichern eines Users: {e}") 

    def search_user(self, search_term):
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

        rows_dict = self.db .select(
            condition_str=condition_str,
            condition_values=condition_values
        )

        return [User.from_dict(row) for row in rows_dict]