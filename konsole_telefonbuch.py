import os
from user import User as Us
from db_sqlite import Database as DB
import logging

class TelefonbuchKonsole:
    def __init__(self):
        self.laeuft = True
        self.db = DB()
        self.user = Us()
        self.logger = logging.getLogger(__name__)


    def kontakt_suchen(self):        
        """Option 2: Sucht nach Kontakten oder zeigt alle aktiven an."""
        self.logger.info("Start Kontakt suchen") 
        print("\n--- Kontakt suchen ---")
        suchbegriff = input("ID oder Vor- bzw. Nachnamen eingeben (Leerlassen für alle aktiven Kontakte): ").strip()
        if suchbegriff == "":
            self.logger.debug("suchbegriff leer") 
            rows = self.db.select()
            ergebnisse = [self.user.from_dict(r) for r in rows]
            self.logger.info("erfolgreich gesucht") 
        else:
            self.logger.debug("suchbegriff: ", suchbegriff) 
            ergebnisse = self.user.search_user(suchbegriff)
            self.logger.info("erfolgreich gesucht") 

        if not ergebnisse:
            print("ℹ️ Keine passenden Personen gefunden.")
            return

        print(f"\n🔍 Gefundene Kontakte ({len(ergebnisse)}):")
        print("-" * 50)
        for p in ergebnisse:
            print(f"[{p.id}] {p.first_name} {p.last_name} | Tel: {p.phone_prefix} {p.phone}")
        print("-" * 50)


    def kontakt_anlegen(self):
        """Option 1: Erstellt einen neuen Kontakt mit Validierung."""
        self.logger.info("Start Kontakt anlegen") 
        print("\n--- Neuen Kontakt anlegen ---")
        vorname = input("Vorname: ").strip()
        nachname = input("Nachname: ").strip()
        vorwahl = input("Vorwahl (Optional): ").strip()
        telefon = input("Telefonnummer (Optional): ").strip()


        # Validierung: Pflichtfelder prüfen
        if not vorname or not nachname:
            print("❌ Fehler: Vor- und Nachname dürfen nicht leer sein!")
            return

        try:
            neue_person = Us(first_name=vorname, last_name=nachname, phone_prefix=vorwahl, phone=telefon)
            neue_person.save_user(neue_person)
            self.logger.info("Kontakt angelegt") 
            print(f"✅ {neue_person.first_name} {neue_person.last_name} wurde erfolgreich gespeichert.")
        except Exception as e:
            print(f"❌ Datenbankfehler beim Anlegen des Kontakts: {e}")
            self.logger.error(" Datenbankfehler beim Anlegen des Kontakts: ", e) 


    def kontakt_bearbeiten(self):
        """Option 3: Bearbeitet einen bestehenden Kontakt anhand seiner ID."""
        self.logger.info("Start Kontakt bearbeiten") 
        print("\n--- Kontakt bearbeiten ---")
        id_input = input("Geben Sie die ID des zu bearbeitenden Kontakts ein: ").strip()
        
        # Validierung: Ist die ID eine Zahl?
        if not id_input.isdigit():
            self.logger.debug("Fehler: Die ID muss eine gültige Zahl sein!") 
            print("❌ Fehler: Die ID muss eine gültige Zahl sein!")
            return

        try:
            db_ergebnis = self.db.select(condition_str="id = ?", condition_values=(id_input,))
            if not db_ergebnis:
                self.logger.debug("Fehler: Keine aktive Person mit dieser ID gefunden") 
                print("❌ Fehler: Keine aktive Person mit dieser ID gefunden.")
                return
            
            # Ersten Eintrag aus der Ergebnisliste holen
            einziger_user_dict = db_ergebnis[0]
            self.logger.debug("Ersten Eintrag aus der Ergebnisliste holen")
            person = self.user.from_dict(einziger_user_dict)
            
            print(f"\nBearbeite aktuell: {person.first_name} {person.last_name}")
            print("--- Drücken Sie ENTER, um den alten Wert zu behalten ---")
            
            person.first_name = input(f"Vorname [{person.first_name}]: ").strip() or person.first_name
            person.last_name = input(f"Nachname [{person.last_name}]: ").strip() or person.last_name
            person.phone_prefix = input(f"Vorwahl [{person.phone_prefix}]: ").strip() or person.phone_prefix
            person.phone = input(f"Telefon [{person.phone}]: ").strip() or person.phone
            
            if person.save_user(person):
                self.logger.info("Kontakt erfolgreich aktualisiert!") 
                print("✅ Kontakt erfolgreich aktualisiert!")
        except Exception as e:
            print(f"❌ Fehler beim Bearbeiten des Kontakts: {e}")
            self.logger.error("Fehler beim Bearbeiten des Kontakts: ", e)


    def kontakt_loeschen(self):
        """Option 4: Führt ein Soft-Delete für einen Kontakt aus."""
        self.logger.info("Start Kontakt löschen")  
        print("\n--- Kontakt löschen ---")
        id_input = input("Geben Sie die ID des zu löschenden Kontakts ein: ").strip()
        self.logger.debug("ID des zu löschenden Kontakts: ", id_input)  
        if not id_input.isdigit():
            self.logger.info("Fehler: Die ID muss eine gültige Zahl sein!") 
            print("❌ Fehler: Die ID muss eine gültige Zahl sein!")
            return

        bestaetigung = input(f"Sind Sie sicher, dass Sie ID {id_input} löschen möchten? (ja/nein): ").strip().lower()
        
        if bestaetigung in ("ja", "j"):
            try:
                if self.db.delete(condition_str="id = ?", condition_values=(id_input,)):
                    print(f"✅ Kontakt ID {id_input} wurde in den Papierkorb verschoben.")
                    self.logger.info(f"Kontakt {id_input} wurde gelöscht")
                else:
                    self.logger.info("Löschvorgang in der Datenbank fehlgeschlagen (ID evtl. nicht vorhanden)")  
                    print("❌ Löschvorgang in der Datenbank fehlgeschlagen (ID evtl. nicht vorhanden).")
            except Exception as e:
                print(f"❌ Fehler beim Löschen des Kontakts: {e}")
                self.logger.error(f"Kontakt löschen fehler {e}")  
        else:
            print("❌ Löschvorgang abgebrochen.")


    def admin_papierkorb(self):
        """Option 5: Zeigt gelöschte Kontakte und erlaubt deren Reaktivierung."""
        print("\n--- 🗑️ Admin-Papierkorb ---")
        self.logger.info("Start admin_papierkorb")
        try:            
            rows = self.db.select(condition_str="deleted = 1", include_deleted=True)
            geloeschte = [Us.from_dict(r) for r in rows]
            
            if not geloeschte:
                print("ℹ️ Der Papierkorb ist leer.")
                return
            self.logger.info("Papierkorb anzeigen")
            print(f"\nFolgende Kontakte befinden sich im Papierkorb ({len(geloeschte)}):")
            print("-" * 50)
            for p in geloeschte:
                print(f"[{p.id}] {p.first_name} {p.last_name}")
            print("-" * 50)
            
            aktion = input("Möchten Sie einen Kontakt wiederherstellen? (ja/nein): ").strip().lower()
            if aktion in ("ja", "j"):
                id_wiederherstellen = input("Geben Sie die ID des Kontakts ein: ").strip()
                
                # Validierung: Ist die ID eine Zahl?
                if not id_wiederherstellen.isdigit():
                    print("❌ Fehler: Die ID muss eine gültige Zahl sein!")
                    self.logger.info("Papierkorb keine Zahl eingeben")
                    return
                    
                erfolg = self.db.update(
                    data_dict={"deleted": 0},
                    condition_str="id = ?",
                    condition_values=(id_wiederherstellen,)
                )            
                if erfolg:
                    print(f"🎉 Kontakt ID {id_wiederherstellen} wurde erfolgreich reaktiviert!")
                    self.logger.info("erfolgreich Kontakt wiederherstellen")  
                else:
                    print("❌ Wiederherstellung fehlgeschlagen (ID evtl. nicht im Papierkorb).")
        except Exception as e:
            print(f"❌ Fehler im Admin-Papierkorb: {e}")
            self.logger.error(f"Fehler bei Admin Papierkorb: {e}")


    # ==========================================
    def zeige_menue_text(self):
        """Gibt das Menü-Layout auf der Konsole aus."""
        print("\n" + "=" * 30)
        print("📞 TELEFONBUCH MENÜ")
        print("=" * 30)
        print("➕ 1: Neuen Kontakt anlegen")
        print("🔍 2: Kontakt suchen / Alle anzeigen")
        print("✏️ 3: Kontakt bearbeiten")
        print("❌ 4: Kontakt löschen (Soft-Delete)")
        print("🗑️ 5: Admin-Papierkorb (Gelöschte reaktivieren)")
        print("🚪 6: Programm beenden")
        print("=" * 30)


    def main_menu(self):
        self.logger.info("Start Menu")  
        """Steuert die Hauptschleife des Programms."""
        while True:
            self.zeige_menue_text()

            try:
                auswahl = input("Bitte wählen Sie eine Option (1-6): ").strip()
            except KeyboardInterrupt:
                self.logger.error("Modul konsole_telefonbuch KeyboardInterrupt")
            
            if auswahl == "1":
                self.logger.debug("Kontakt_anlegen")  
                self.kontakt_anlegen()
            elif auswahl == "2":
                self.logger.debug("Kontakt suchen")  
                self.kontakt_suchen()
            elif auswahl == "3":
                self.logger.debug("Kontakt bearbeiten")  
                self.kontakt_bearbeiten()
            elif auswahl == "4":
                self.logger.debug("Kontakt löschen")  
                self.kontakt_loeschen()
            elif auswahl == "5":
                self.logger.debug("Admin Papierkorb")  
                self.admin_papierkorb()
            elif auswahl == "6":
                self.logger.debug("Programm beendet")  
                print("\n👋 Programm beendet. Auf Wiedersehen!")
                break
            else:
                print("❌ Ungültige Eingabe! Bitte wählen Sie eine Zahl von 1 bis 6.")


def main():
    logging.info("main Module konsole_telefonbuch")  
    app = TelefonbuchKonsole()
    app.main_menu()


if __name__ == "__main__":
    main()

