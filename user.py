class User:
    def __init__(self, first_name, last_name, phone_prefix="", phone="", deleted=0, id=None):
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
