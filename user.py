from db_sqlite import Database as DB

class User:
    def __init__(self, first_name="", last_name="", phone_prefix="", phone="", deleted=0, id=None):
        self.id = id  
        self.first_name = first_name
        self.last_name = last_name
        self.phonenumber_prefix = phone_prefix
        self.phonenumber = phone
        self.deleted = deleted

    @classmethod
    def from_dict(cls, db_dict):
        """
        Erstellt ein Person-Objekt aus einem Datenbank-Dictionary.
        Liest jetzt auch die 'id' mit aus.
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
            "phone_prefix": self.phonenumber_prefix,
            "phone": self.phonenumber,
            "deleted": self.deleted
        }
        if include_id:
            daten["id"] = self.id
        return daten
    
    def insert_user(self, person_object):    
            try:
                db = DB()

                insert, person_object = db.insert("user", person_object)        
                return True

            except Exception as e:
                print(f"Fehler beim Einfügen eines Users: {e}")
                return False
            finally:
                pass

    def save_user(self, db_name, table_name, person_object):
            """
            Speichert eine Person ab. 
            Erstellt sie neu (INSERT), wenn sie noch keine ID hat.
            Aktualisiert sie (UPDATE), wenn bereits eine ID vorhanden ist.
            """
            try:
                db = DB()
                if person_object.id is None:
                    return db.insert(db_name, table_name, person_object)
                else:            
        
                    data_dict = person_object.to_dict(include_id=False)
                
                    return db.update(
                        db_name=db_name,
                        table_name=table_name,
                        data_dict=data_dict,
                        condition_str="id = ?",
                        condition_values=(person_object.id,)
                    )
            except:
                pass

    def search_user(self, db_name, table_name, search_term):
        """
        Durchsucht die Spalten 'id', 'first_name' und 'last_name' nach dem Suchbegriff.
        Berücksichtigt automatisch 'deleted = 0' und gibt eine Liste von User-Objekten zurück.
        """
        db = DB()
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

        rows_dict = db.select(
            db_name=db_name,
            table_name=table_name,
            condition_str=condition_str,
            condition_values=condition_values
        )

        return [User.from_dict(row) for row in rows_dict]