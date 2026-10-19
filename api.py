import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
import logging

# Importiere deine bestehenden Klassen
from user import User
from db_sqlite import Database as DB

# app = FastAPI(
#     title="Telefonbuch API",
#     description="Eine REST-API zur Verwaltung von Kontakten",
#     version="1.0.0"
# )

# Datenbank initialisieren
#db = DB()

# ==========================================
# CORS-MIDDLEWARE HINZUFÜGEN (WICHTIG FÜR FRONTENDS!)
# ==========================================
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Erlaubt Zugriff von jedem anderen Rechner im Netzwerk
#     allow_credentials=True,
#     allow_methods=["*"],  # Erlaubt GET, POST, PUT, DELETE etc.
#     allow_headers=["*"],
# )

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
    phone_prefix: Optional[str] = ""
    phone: Optional[str] = ""
    deleted:int


# ==========================================
# API ENDPUNKTE (ROUTES)
# ==========================================
# 2. Die API als Klasse
class TelefonbuchAPI:
    def __init__(self):
        # Logger initialisieren (nutzt die Konfiguration aus deiner main.py)
        self.logger = logging.getLogger(__name__)
        self.db = DB()
        # FastAPI Instanz erstellen und an self binden
        self.app = FastAPI(title="Telefonbuch-API", version="1.0.0")
        
        # Middleware konfigurieren
        self.setup_middleware()
        
        # Routen registrieren
        self.setup_routes()
        
        self.logger.info("TelefonbuchAPI-Klasse erfolgreich initialisiert.")

    def setup_middleware(self):
        """Konfiguriert CORS-Sicherheitsrichtlinien."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.logger.debug("CORS-Middleware konfiguriert.")

    def setup_routes(self):
        """Verknüpft die internen Methoden mit den FastAPI-Endpunkten."""
        # Wichtig: Wir übergeben die Methoden der Klasse direkt an die HTTP-Dekoratoren
        self.app.get("/")(self.startseite)
        self.app.post("/kontakte/", response_model=KontaktOut, status_code=201)(self.api_kontakt_anlegen)
        self.app.get("/kontakte/", response_model=List[KontaktOut])(self.api_kontakt_suchen)
        self.app.put("/kontakte/{kontakt_id}", response_model=KontaktOut)(self.api_kontakt_bearbeiten)
        self.app.delete("/kontakte/{kontakt_id}", status_code=200)(self.api_kontakt_loeschen)
        self.app.get("/papierkorb/", response_model=List[KontaktOut])(self.api_papierkorb_anzeigen)
        self.app.post("/papierkorb/{kontakt_id}/wiederherstellen", status_code=200)(self.api_kontakt_wiederherstellen)
        self.logger.debug("API-Routen registriert.")





#@app.get("/")
    def startseite(self):
        return {
            "message": "Willkommen zur Telefonbuch-API!",
            "doku": "Gehe zu http://127.0.0 für die interaktive Dokumentation."
        }


#@app.post("/kontakte/", response_model=KontaktOut, status_code=201)
    def api_kontakt_anlegen(self, kontakt: KontaktIn):
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
            neue_person.save_user(neue_person)

            return KontaktOut(
                id=neue_person.id,
                first_name=neue_person.first_name,
                last_name=neue_person.last_name,
                phone_prefix=neue_person.phone_prefix,
                phone=neue_person.phone,
                deleted=neue_person.deleted
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Datenbankfehler: {e}")


#@app.get("/kontakte/", response_model=List[KontaktOut])
    def api_kontakt_suchen(self, q: Optional[str] = Query(None, description="Suchbegriff für ID, Vor- oder Nachname")):
        """2: Kontakt suchen / Alle anzeigen"""
        try:
            if not q or q.strip() == "":
                rows = self.db.select()
                ergebnisse = [User.from_dict(r) for r in rows]
            else:
                ergebnisse = User.search_user(q.strip())
                
            return [
                KontaktOut(
                    id=p.id,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    phone_prefix=p.phone_prefix,
                    phone=p.phone,
                    deleted=p.deleted
                ) for p in ergebnisse
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler bei der Suche: {e}")


#@app.put("/kontakte/{kontakt_id}", response_model=KontaktOut)
    def api_kontakt_bearbeiten(self, kontakt_id: int, kontakt_daten: KontaktIn):
        """3: Kontakt bearbeiten"""
        try:
            db_ergebnis = self.db.select(condition_str="id = ?", condition_values=(kontakt_id,))
            if not db_ergebnis:
                raise HTTPException(status_code=404, detail="Kontakt mit dieser ID nicht gefunden.")
            
            person = User.from_dict(db_ergebnis[0])
            
            person.first_name = kontakt_daten.first_name.strip() or person.first_name
            person.last_name = kontakt_daten.last_name.strip() or person.last_name
            person.phone_prefix = kontakt_daten.phone_prefix.strip() or person.phone_prefix
            person.phone = kontakt_daten.phone.strip() or person.phone
            
            if person.save_user(person):
                return KontaktOut(
                    id=person.id,
                    first_name=person.first_name,
                    last_name=person.last_name,
                    phone_prefix=person.phone_prefix,
                    phone=person.phone,
                    deleted=person.deleted
                )
            else:
                raise HTTPException(status_code=500, detail="Aktualisierung in der Datenbank fehlgeschlagen.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Bearbeiten: {e}")


#@app.delete("/kontakte/{kontakt_id}", status_code=200)
    def api_kontakt_loeschen(self, kontakt_id: int):
        """4: Kontakt löschen (Soft-Delete)"""
        try:
            erfolg = self.db.delete(condition_str="id = ?", condition_values=(kontakt_id,))
            if erfolg:
                return {"status": "success", "message": f"Kontakt ID {kontakt_id} wurde in den Papierkorb verschoben."}
            else:
                raise HTTPException(status_code=404, detail="Kontakt nicht gefunden oder bereits gelöscht.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Löschen: {e}")


#@app.get("/papierkorb/", response_model=List[KontaktOut])
    def api_papierkorb_anzeigen(self):
        """5a: Admin-Papierkorb anzeigen"""
        try:
            rows = self.db.select(condition_str="deleted = 1", include_deleted=True)
            geloeschte = [User.from_dict(r) for r in rows]
            return [
                KontaktOut(
                    id=p.id,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    phone_prefix=p.phone_prefix,
                    phone=p.phone,
                    deleted=p.deleted
                ) for p in geloeschte
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Laden des Papierkorbs: {e}")


#@app.post("/papierkorb/{kontakt_id}/wiederherstellen", status_code=200)
    def api_kontakt_wiederherstellen(self, kontakt_id: int):
        """5b: Kontakt aus dem Papierkorb reaktivieren"""
        try:
            erfolg = self.db.update(            
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

api_instanz = TelefonbuchAPI()
app = api_instanz.app

# def main():
#     import uvicorn
#     #uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
#     uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
#     #uvicorn.run("api:app", host="192.168.178.24", port=8000, reload=True)

# if __name__ == "__main__":
#     main()