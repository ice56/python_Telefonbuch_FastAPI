import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware

# Importiere deine bestehenden Klassen
from user import User
from db_sqlite import Database as DB

app = FastAPI(
    title="Telefonbuch API",
    description="Eine REST-API zur Verwaltung von Kontakten",
    version="1.0.0"
)

# Datenbank initialisieren
db = DB()
DB_NAME = "phonebook.db"
TABLE_NAME = "users"

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, DB_NAME)

# ==========================================
# CORS-MIDDLEWARE HINZUFÜGEN (WICHTIG FÜR FRONTENDS!)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Erlaubt Zugriff von jedem anderen Rechner im Netzwerk
    allow_credentials=True,
    allow_methods=["*"],  # Erlaubt GET, POST, PUT, DELETE etc.
    allow_headers=["*"],
)

# ==========================================
# PYDANTIC-MODELLE (FÜR VALIDIERUNG & JSON)
# ==========================================

class KontaktIn(BaseModel):
    """Eingabe-Schema für das Erstellen/Bearbeiten eines Kontakts."""
    first_name: str
    last_name: str
    phone_prefix: Optional[str] = ""
    phone: Optional[str] = ""

class KontaktOut(BaseModel):
    """Ausgabe-Schema für die API-Antworten."""
    id: Optional[int] = None
    first_name: str
    last_name: str
    phonenumber_prefix: Optional[str] = ""
    phonenumber: Optional[str] = ""


# ==========================================
# API ENDPUNKTE (ROUTES)
# ==========================================

@app.get("/")
def startseite():
    return {
        "message": "Willkommen zur Telefonbuch-API!",
        "doku": "Gehe zu http://127.0.0 für die interaktive Dokumentation."
    }


@app.post("/kontakte/", response_model=KontaktOut, status_code=201)
def api_kontakt_anlegen(kontakt: KontaktIn):
    """1: Neuen Kontakt anlegen"""
    if not kontakt.first_name.strip() or not kontakt.last_name.strip():
        raise HTTPException(status_code=400, detail="Vor- und Nachname dürfen nicht leer sein.")
    
    try:
        neue_person = User(
            first_name=kontakt.first_name.strip(),
            last_name=kontakt.last_name.strip(),
            phone_prefix=kontakt.phone_prefix.strip(),
            phone=kontakt.phone.strip()
        )
        db.save_user(db_path, TABLE_NAME, neue_person)

        return KontaktOut(
            id=neue_person.id,
            first_name=neue_person.first_name,
            last_name=neue_person.last_name,
            phonenumber_prefix=neue_person.phonenumber_prefix,
            phonenumber=neue_person.phonenumber
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {e}")


@app.get("/kontakte/", response_model=List[KontaktOut])
def api_kontakt_suchen(q: Optional[str] = Query(None, description="Suchbegriff für ID, Vor- oder Nachname")):
    """2: Kontakt suchen / Alle anzeigen"""
    try:
        if not q or q.strip() == "":
            rows = db.fetch_data(db_path, TABLE_NAME)
            ergebnisse = [User.from_dict(r) for r in rows]
        else:
            ergebnisse = db.search_persons(db_path, TABLE_NAME, q.strip())
            
        return [
            KontaktOut(
                id=p.id,
                first_name=p.first_name,
                last_name=p.last_name,
                phonenumber_prefix=p.phonenumber_prefix,
                phonenumber=p.phonenumber
            ) for p in ergebnisse
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Suche: {e}")


@app.put("/kontakte/{kontakt_id}", response_model=KontaktOut)
def api_kontakt_bearbeiten(kontakt_id: int, kontakt_daten: KontaktIn):
    """3: Kontakt bearbeiten"""
    try:
        db_ergebnis = db.fetch_data(db_path, TABLE_NAME, condition_str="id = ?", condition_values=(kontakt_id,))
        if not db_ergebnis:
            raise HTTPException(status_code=404, detail="Kontakt mit dieser ID nicht gefunden.")
        
        person = User.from_dict(db_ergebnis[0])
        
        person.first_name = kontakt_daten.first_name.strip() or person.first_name
        person.last_name = kontakt_daten.last_name.strip() or person.last_name
        person.phonenumber_prefix = kontakt_daten.phone_prefix.strip() or person.phonenumber_prefix
        person.phonenumber = kontakt_daten.phone.strip() or person.phonenumber
        
        if db.save_user(db_path, TABLE_NAME, person):
            return KontaktOut(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                phonenumber_prefix=person.phonenumber_prefix,
                phonenumber=person.phonenumber
            )
        else:
            raise HTTPException(status_code=500, detail="Aktualisierung in der Datenbank fehlgeschlagen.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Bearbeiten: {e}")


@app.delete("/kontakte/{kontakt_id}", status_code=200)
def api_kontakt_loeschen(kontakt_id: int):
    """4: Kontakt löschen (Soft-Delete)"""
    try:
        erfolg = db.delete_data(db_path, TABLE_NAME, condition_str="id = ?", condition_values=(kontakt_id,))
        if erfolg:
            return {"status": "success", "message": f"Kontakt ID {kontakt_id} wurde in den Papierkorb verschoben."}
        else:
            raise HTTPException(status_code=404, detail="Kontakt nicht gefunden oder bereits gelöscht.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Löschen: {e}")


@app.get("/papierkorb/", response_model=List[KontaktOut])
def api_papierkorb_anzeigen():
    """5a: Admin-Papierkorb anzeigen"""
    try:
        rows = db.fetch_data(db_path, TABLE_NAME, condition_str="deleted = 1", include_deleted=True)
        geloeschte = [User.from_dict(r) for r in rows]
        return [
            KontaktOut(
                id=p.id,
                first_name=p.first_name,
                last_name=p.last_name,
                phonenumber_prefix=p.phonenumber_prefix,
                phonenumber=p.phonenumber
            ) for p in geloeschte
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden des Papierkorbs: {e}")


@app.post("/papierkorb/{kontakt_id}/wiederherstellen", status_code=200)
def api_kontakt_wiederherstellen(kontakt_id: int):
    """5b: Kontakt aus dem Papierkorb reaktivieren"""
    try:
        erfolg = db.update_data(
            db_name=db_path,
            table_name=TABLE_NAME,
            data_dict={"deleted": 0},
            condition_str="id = ?",
            condition_values=(kontakt_id,)
        )
        if erfolg:
            return {"status": "success", "message": f"Kontakt ID {kontakt_id} wurde erfolgreich reaktiviert."}
        else:
            raise HTTPException(status_code=404, detail="Kontakt konnte nicht reaktiviert werden (ID evtl. nicht im Papierkorb).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Wiederherstellung: {e}")


if __name__ == "__main__":
    import uvicorn
    #uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
    #uvicorn.run("api:app", host="192.168.178.24", port=8000, reload=True)