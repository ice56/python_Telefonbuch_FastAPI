import os
from user import User as Us
from db_sqlite import Database as DB


def kontakt_suchen(db_helper, db_name, table_name):
    """Option 2: Sucht nach Kontakten oder zeigt alle aktiven an."""
    print("\n--- Kontakt suchen ---")
    suchbegriff = input("ID oder Vor- bzw. Nachnamen eingeben (Leerlassen für alle aktiven Kontakte): ").strip()
    _user = Us()
    #_db = DB()
    if suchbegriff == "":
        rows = db_helper.select(db_name, table_name)
        ergebnisse = [_user.from_dict(r) for r in rows]
    else:
        ergebnisse = _user.search_user(db_name, table_name, suchbegriff)
        
    if not ergebnisse:
        print("ℹ️ Keine passenden Personen gefunden.")
        return

    print(f"\n🔍 Gefundene Kontakte ({len(ergebnisse)}):")
    print("-" * 50)
    for p in ergebnisse:
        print(f"[{p.id}] {p.first_name} {p.last_name} | Tel: {p.phonenumber_prefix} {p.phonenumber}")
    print("-" * 50)

def kontakt_anlegen(db_helper, db_name, table_name):
    """Option 1: Erstellt einen neuen Kontakt mit Validierung."""
    print("\n--- Neuen Kontakt anlegen ---")
    vorname = input("Vorname: ").strip()
    nachname = input("Nachname: ").strip()
    vorwahl = input("Vorwahl (Optional): ").strip()
    telefon = input("Telefonnummer (Optional): ").strip()

    _user = Us()
    # Validierung: Pflichtfelder prüfen
    if not vorname or not nachname:
        print("❌ Fehler: Vor- und Nachname dürfen nicht leer sein!")
        return

    try:
        neue_person = Us(first_name=vorname, last_name=nachname, phone_prefix=vorwahl, phone=telefon)
        neue_person.save_user(db_name, table_name, neue_person)
        print(f"✅ {neue_person.first_name} {neue_person.last_name} wurde erfolgreich gespeichert.")
    except Exception as e:
        print(f"❌ Datenbankfehler beim Anlegen des Kontakts: {e}")

def kontakt_bearbeiten(db_helper, db_name, table_name):
    """Option 3: Bearbeitet einen bestehenden Kontakt anhand seiner ID."""
    print("\n--- Kontakt bearbeiten ---")
    id_input = input("Geben Sie die ID des zu bearbeitenden Kontakts ein: ").strip()
    
    # Validierung: Ist die ID eine Zahl?
    if not id_input.isdigit():
        print("❌ Fehler: Die ID muss eine gültige Zahl sein!")
        return

    try:
        db_ergebnis = db_helper.select(db_name, table_name, condition_str="id = ?", condition_values=(id_input,))
        if not db_ergebnis:
            print("❌ Fehler: Keine aktive Person mit dieser ID gefunden.")
            return

        # Ersten Eintrag aus der Ergebnisliste holen
        einziger_user_dict = db_ergebnis[0]
        person = Us.from_dict(einziger_user_dict)
        
        print(f"\nBearbeite aktuell: {person.first_name} {person.last_name}")
        print("--- Drücken Sie ENTER, um den alten Wert zu behalten ---")
        
        person.first_name = input(f"Vorname [{person.first_name}]: ").strip() or person.first_name
        person.last_name = input(f"Nachname [{person.last_name}]: ").strip() or person.last_name
        person.phonenumber_prefix = input(f"Vorwahl [{person.phonenumber_prefix}]: ").strip() or person.phonenumber_prefix
        person.phonenumber = input(f"Telefon [{person.phonenumber}]: ").strip() or person.phonenumber
        
        if person.save_user(db_name, table_name, person):
            print("✅ Kontakt erfolgreich aktualisiert!")
    except Exception as e:
        print(f"❌ Fehler beim Bearbeiten des Kontakts: {e}")

def kontakt_loeschen(db_helper, db_name, table_name):
    """Option 4: Führt ein Soft-Delete für einen Kontakt aus."""
    print("\n--- Kontakt löschen ---")
    id_input = input("Geben Sie die ID des zu löschenden Kontakts ein: ").strip()

    if not id_input.isdigit():
        print("❌ Fehler: Die ID muss eine gültige Zahl sein!")
        return

    bestaetigung = input(f"Sind Sie sicher, dass Sie ID {id_input} löschen möchten? (ja/nein): ").strip().lower()
    
    if bestaetigung in ("ja", "j"):
        try:
            if db_helper.delete(db_name, table_name, condition_str="id = ?", condition_values=(id_input,)):
                print(f"✅ Kontakt ID {id_input} wurde in den Papierkorb verschoben.")
            else:
                print("❌ Löschvorgang in der Datenbank fehlgeschlagen (ID evtl. nicht vorhanden).")
        except Exception as e:
            print(f"❌ Fehler beim Löschen des Kontakts: {e}")
    else:
        print("❌ Löschvorgang abgebrochen.")

def admin_papierkorb(db_helper, db_name, table_name):
    """Option 5: Zeigt gelöschte Kontakte und erlaubt deren Reaktivierung."""
    print("\n--- 🗑️ Admin-Papierkorb ---")
    
    try:
        rows = db_helper.select(db_name, table_name, condition_str="deleted = 1", include_deleted=True)
        geloeschte = [Us.from_dict(r) for r in rows]
        
        if not geloeschte:
            print("ℹ️ Der Papierkorb ist leer.")
            return

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
                return
                
            erfolg = db_helper.update(
                db_name=db_name,
                table_name=table_name,
                data_dict={"deleted": 0},
                condition_str="id = ?",
                condition_values=(id_wiederherstellen,)
            )
            if erfolg:
                print(f"🎉 Kontakt ID {id_wiederherstellen} wurde erfolgreich reaktiviert!")
            else:
                print("❌ Wiederherstellung fehlgeschlagen (ID evtl. nicht im Papierkorb).")
    except Exception as e:
        print(f"❌ Fehler im Admin-Papierkorb: {e}")

# ==========================================
def zeige_menue_text():
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

def main_menu(db_helper, db_name, table_name):
    """Steuert die Hauptschleife des Programms."""
    while True:
        zeige_menue_text()

        try:
            auswahl = input("Bitte wählen Sie eine Option (1-6): ").strip()
        except KeyboardInterrupt:
            pass
        
        if auswahl == "1":
            kontakt_anlegen(db_helper, db_name, table_name)
        elif auswahl == "2":
            kontakt_suchen(db_helper, db_name, table_name)
        elif auswahl == "3":
            kontakt_bearbeiten(db_helper, db_name, table_name)
        elif auswahl == "4":
            kontakt_loeschen(db_helper, db_name, table_name)
        elif auswahl == "5":
            admin_papierkorb(db_helper, db_name, table_name)
        elif auswahl == "6":
            print("\n👋 Programm beendet. Auf Wiedersehen!")
            break
        else:
            print("❌ Ungültige Eingabe! Bitte wählen Sie eine Zahl von 1 bis 6.")

if __name__ == "__main__":
    db = DB()
    db_name = "phonebook.db"
    table_name = "users"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, db_name)
    
    main_menu(db_helper=db, db_name=db_path, table_name=table_name)
