import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging

from user import User as Us
from db_sqlite import Database as DB

class PhonebookApp:
    def __init__(self, root):
         
        self.root = root
        self.root.title("Telefonbuch - Tkinter Frontend")
        self.root.geometry("650x500")

        # Parameter als Instanzvariablen speichern
        self.db_helper =  DB()  # Ihre DB-Instanz
        self.user_control = Us()  # Die Instanz der User-Klasse für Logik
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Start __init__") 
        skript_ordner = os.path.dirname(os.path.abspath(__file__))
        png_pfad = os.path.join(skript_ordner, "tele.png")
        self.icon_image = tk.PhotoImage(file=png_pfad)
        self.root.wm_iconphoto(True, self.icon_image)

        search_frame = tk.LabelFrame(
            root, text="Kontakte durchsuchen", padx=10, pady=10
        )
        search_frame.pack(fill="x", padx=10, pady=5)

        self.entry_search = tk.Entry(search_frame, width=30)
        self.entry_search.pack(side="left", padx=5)

        btn_search = tk.Button(
            search_frame, text="Suchen", command=self.search_user
        )
        btn_search.pack(side="left", padx=5)

        # WICHTIG: Ändert das Verhalten zurück zur Standardansicht
        btn_refresh = tk.Button(
            search_frame, text="Alle anzeigen", command=self.standard_ansicht_aktivieren
        )
        btn_refresh.pack(side="left", padx=5)

        # WICHTIG: Schaltet jetzt auch die Button-Sichtbarkeit um
        btn_papierkorb = tk.Button(
            search_frame,
            text="🗑️ Admin-Papierkorb",
            command=self.papierkorb_ansicht_aktivieren
        )
        btn_papierkorb.pack(side="left", padx=5)

        table_frame = tk.Frame(root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("id", "first_name", "last_name", "phone")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.tree.heading("id", text="ID", anchor="center")
        self.tree.heading("first_name", text="Vorname", anchor="center")
        self.tree.heading("last_name", text="Nachname", anchor="center")
        self.tree.heading("phone", text="Telefonnummer", anchor="center")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("first_name", width=150, anchor="center")
        self.tree.column("last_name", width=150, anchor="center")
        self.tree.column("phone", width=200, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- UNTERER BEREICH: Neuen Kontakt hinzufügen ---
        form_frame = tk.LabelFrame(
            root, text="Neuen Kontakt anlegen", padx=10, pady=10
        )
        form_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(form_frame, text="Vorname:").grid(row=0, column=0, sticky="w")
        self.entry_first_name = tk.Entry(form_frame)
        self.entry_first_name.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form_frame, text="Nachname:").grid(row=0, column=2, sticky="w")
        self.entry_last_name = tk.Entry(form_frame)
        self.entry_last_name.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(form_frame, text="Vorwahl:").grid(row=1, column=0, sticky="w")
        self.entry_prefix = tk.Entry(form_frame, width=10)
        self.entry_prefix.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        tk.Label(form_frame, text="Nummer:").grid(row=1, column=2, sticky="w")
        self.entry_phone = tk.Entry(form_frame)
        self.entry_phone.grid(row=1, column=3, padx=5, pady=2)

        btn_save = tk.Button(
            form_frame,
            text="Speichern",
            bg="#4CAF50",
            fg="white",
            command=self.kontakt_anlegen,
        )
        btn_save.grid(row=2, column=0, columnspan=4, pady=10, sticky="ew")

        # --- UNTERE STEUERUNGSBUTTONS (Als Instanzvariablen mit self.) ---
        # Löschen-Button
        self.btn_delete = tk.Button(
            root,
            text="Ausgewählten Kontakt löschen",
            bg="#f44336",
            fg="white",
            command=self.kontakt_loeschen,
        )
        self.btn_delete.pack(side="left", padx=5, pady=5)

        # Bearbeiten-Button
        self.btn_edit = tk.Button(
            root,
            text="✏️ Ausgewählten Kontakt bearbeiten",
            bg="#2196F3",
            fg="white",
            command=self.kontakt_laden_zum_bearbeiten,
        )
        self.btn_edit.pack(side="left", padx=5, pady=5)

        # NEU: Der Wiederherstellen-Button (wird erst im Papierkorb sichtbar gemappt)
        self.btn_restore = tk.Button(
            root,
            text="🔄 Ausgewählten Kontakt wiederherstellen",
            bg="#ff9800",
            fg="white",
            command=self.kontakt_wiederherstellen, # Diese Funktion musst du noch in der Logik erstellen
        )

        # Beim Start direkt alle Kontakte laden
        self.load_contacts()

        self.editing_user_id = None  # Speichert die ID, wenn wir gerade editieren
        self.logger.debug("Ende __init__") 


    def kontakt_wiederherstellen(self):
        self.logger.debug("Start kontakt_wiederherstellen") 
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showwarning(
                "Fehler", "Bitte wählen Sie zuerst einen Kontakt aus!"
            )
            return

        item_data = self.tree.item(selected_item)["values"]
        id_wiederherstellen = item_data[0]

        if messagebox.askyesno(
                "Wiederherstellen bestätigen",
                "Möchten Sie diesen Kontakt wirklich Wiederherstellen?",
        ):

            erfolg = self.db_helper.update(
                data_dict={"deleted": 0},
                condition_str="id = ?",
                condition_values=(id_wiederherstellen,)
            )
        self.logger.debug("Start kontakt wurde wiederherstellt") 
        self.oeffne_admin_papierkorb()


    # --- METHODEN ---
    def papierkorb_ansicht_aktivieren(self):
        # 1. Bestehende DB-Logik aufrufen (Inhalt des Papierkorbs laden)
        self.oeffne_admin_papierkorb()
        self.logger.debug("papierkorb_ansicht_aktivieren") 
        # 2. Bearbeiten und Löschen verstecken
        self.btn_edit.pack_forget()
        self.btn_delete.pack_forget()

        # 3. Wiederherstellen anzeigen
        self.btn_restore.pack(side="left", padx=5, pady=5)


    def standard_ansicht_aktivieren(self):
        # 1. Alle regulären Kontakte wieder in das Treeview laden
        self.load_contacts()
        self.logger.debug("standard_ansicht_aktivieren") 
        # 2. Wiederherstellen-Button verstecken
        self.btn_restore.pack_forget()

        # 3. Bearbeiten und Löschen wieder anzeigen
        self.btn_delete.pack(side="left", padx=5, pady=5)
        self.btn_edit.pack(side="left", padx=5, pady=5)

#-----------
    def oeffne_admin_papierkorb(self):
        """
        Lädt alle gelöschten Kontakte (deleted = 1) aus der Datenbank
        und zeigt sie direkt im bestehenden Haupt-Treeview an.
        """
        self.logger.debug("oeffne_admin_papierkorb") 
        try:
            # 1. Alle Einträge mit deleted = 1 aus der DB holen
            rows_dict = self.db_helper.select(
                condition_str="deleted = 1",
                include_deleted=True
                    # Hier filtern wir explizit nach den gelöschten
            )
            self.logger.debug(f"einträge geholt ") 
            # 2. Dicts in User-Objekte umwandeln via from_dict der User-Klasse
            UserClass = self.user_control.__class__
            geloeschte_users = [UserClass.from_dict(row) for row in rows_dict]
            self.logger.debug(f"einträge in User gewandelt") 
            # 3. Das bestehende Treeview leeren
            self.clear_treeview()
            
            # 4. Treeview mit den gelöschten Usern befüllen
            # (Da fill_treeview standardmäßig deleted == 0 prüft, bauen wir das Befüllen hier direkt ein)
            for u in geloeschte_users:
                if u:
                    full_phone = f"{u.phone_prefix} {u.phone}".strip()
                    self.tree.insert(
                        "",
                        "end",
                        values=(u.id, u.first_name, u.last_name, full_phone)
                    )
            self.logger.debug(f"gelöschte User an Treeview gebunden")         
            # Optional: Titel kurz anpassen, damit der Admin weiß, wo er sich befindet
            self.root.title("Telefonbuch - Admin-Papierkorb Ansicht")
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Fehler", f"Papierkorb konnte nicht geladen werden: {e}")
            self.logger.error(f"Papierkorb konnte nicht geladen werden: {e}") 


    def clear_treeview(self):        
        """Hilfsmethode, um alle Einträge aus der Tabelle zu löschen."""
        self.logger.debug(f"treeview wird geleert") 
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.logger.debug(f"treeview wurde geleert") 


    def fill_treeview(self, users_list):
        """Hilfsmethode, um die Tabelle mit einer Liste von User-Objekten zu füllen."""
        self.logger.debug(f"Start fill_treeview") 
        self.clear_treeview()
        for u in users_list:
            if u and getattr(u, "deleted", 0) == 0:  # Nur nicht-gelöschte anzeigen
                full_phone = (
                    f"{u.phone_prefix} {u.phone}".strip()
                )
                self.tree.insert(
                    "",
                    "end",
                    values=(u.id, u.first_name, u.last_name, full_phone),
                )


    def load_contacts(self):
        """Lädt absolut alle aktiven Kontakte aus der Datenbank."""
        self.logger.debug(f"Start load contacts") 
        rows_dict = self.db_helper.select(condition_str="deleted = 0",  # Nur aktive Kontakte holen
        )

        # Dicts in User-Objekte umwandeln (Nutzt den Code aus Ihrer User-Klasse)
        self.logger.debug(f"alle Kontakte wurden geladen") 
        users = [self.user_control.__class__.from_dict(row) for row in rows_dict]
        self.logger.debug(f"alle Kontakte wurden in User gewandelt") 
        self.fill_treeview(users)
        self.logger.debug(f"alle Kontakte an treeview gebunden") 
        self.root.title("Telefonbuch - Alle Kontakte Ansicht")

    def search_user(self):
        self.logger.debug(f"Start search_user") 
        """Nutzt die Suchfunktion Ihrer User-Klasse."""
        search_term = self.entry_search.get()

        if not search_term.strip():
            self.load_contacts()
            self.logger.debug(f"kein suchbegriff") 
            return

        result = self.user_control.search_user(search_term)
        self.logger.debug(f"user mit suchbegriff geholt") 
        if isinstance(result, tuple):
            users = result[0]
        else:
            users = result

        self.fill_treeview(users)


    def kontakt_anlegen(self):
        """Erstellt ein neues User-Objekt und speichert es über die User-Klasse."""
        self.logger.debug(f"Start kontakt_anlegen") 
        vorname = self.entry_first_name.get().strip()
        nachname = self.entry_last_name.get().strip()
        prefix = self.entry_prefix.get().strip()
        phone = self.entry_phone.get().strip()

        if not vorname or not nachname:
            messagebox.showwarning(
                "Fehler", "Vorname und Nachname dürfen nicht leer sein!"
            )
            return

        aktueller_user = Us(
            id=self.editing_user_id,  # Ist None bei neuem User, oder die echte ID beim Bearbeiten
            first_name=vorname,
            last_name=nachname,
            phone_prefix=prefix,
            phone=phone,
            deleted=0
        )
        # Nutzen der integrierten save_user-Methode
        self.user_control.save_user(aktueller_user)
        self.logger.debug(f"Start kontakt wird gespeichert") 
        # Formularfelder leeren
        self.editing_user_id = None
        self.entry_first_name.delete(0, tk.END)
        self.entry_last_name.delete(0, tk.END)
        self.entry_prefix.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.logger.debug(f"Start felder wurden geleert") 

        # Anzeige aktualisieren
        self.load_contacts()
        self.logger.info(f"Kontakt wurde erfolgreich gespeichert!") 
        messagebox.showinfo("Erfolg", "Kontakt wurde erfolgreich gespeichert!")


    def kontakt_loeschen(self):
        """Markiert einen ausgewählten Kontakt über ein Soft-Delete (deleted=1) als gelöscht."""
        self.logger.debug(f"Start kontakt_loeschen") 
        selected_item = self.tree.selection()
        
        if not selected_item:
            messagebox.showwarning(
                "Fehler", "Bitte wählen Sie zuerst einen Kontakt aus!"
            )
            return

        # ID aus der ausgewählten Tabellenzeile auslesen
        item_data = self.tree.item(selected_item)["values"]
        kontakt_id = item_data[0]  # Die ID steht in der ersten Spalte

        # Bestätigungsfenster abfragen
        if messagebox.askyesno(
            "Löschen bestätigen",
            "Möchten Sie diesen Kontakt wirklich löschen?",
        ):
            self.db_helper.delete(condition_str="id = ?", condition_values=(kontakt_id,))
            self.logger.debug(f"Start kontakt wurde gelöscht")
            # Liste neu laden
            self.load_contacts()


    def kontakt_laden_zum_bearbeiten(self):
        """Liest die markierte Zeile aus und schreibt die Daten in die Eingabefelder."""
        self.logger.debug(f"Start kontakt_laden_zum_bearbeiten") 
        selected_item = self.tree.selection()
        
        if not selected_item:
            from tkinter import messagebox
            messagebox.showwarning("Fehler", "Bitte wählen Sie zuerst einen Kontakt aus der Tabelle aus!")
            return

        # Daten aus der markierten Zeile holen
        item_data = self.tree.item(selected_item)["values"]
        self.logger.debug(f"Selektierten Kontakt sichern")         
        # ID zwischenspeichern, damit wir wissen, dass wir updaten müssen
        self.editing_user_id = item_data[0]
        vorname = item_data[1]
        nachname = item_data[2]
        vollstaendige_nummer = str(item_data[3])

        # Vorwahl und Telefonnummer trennen (sucht nach dem ersten Leerzeichen)
        if " " in vollstaendige_nummer:
            prefix, phone = vollstaendige_nummer.split(" ", 1)
        else:
            prefix = ""
            phone = vollstaendige_nummer

        # Eingabefelder zuerst leeren
        self.entry_first_name.delete(0, tk.END)
        self.entry_last_name.delete(0, tk.END)
        self.entry_prefix.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)

        self.logger.debug(f"Eingabefelder werden gefüllt mit Kontakt") 
        # Gefundene Daten in die Eingabefelder schreiben
        self.entry_first_name.insert(0, vorname)
        self.entry_last_name.insert(0, nachname)
        self.entry_prefix.insert(0, prefix)
        self.entry_phone.insert(0, phone)
        
        # Optional: Dem Admin visuelles Feedback geben
        self.root.title(f"Telefonbuch - Bearbeite Kontakt ID: {self.editing_user_id}")


def main():
    logging.info("Start main Methode")  
    root = tk.Tk()

    root.lift()  # Bringt das Fenster über alle anderen Fenster
    root.attributes("-topmost", True)  # Zwingt es ganz nach vorne
    root.after(
        1, lambda: root.attributes("-topmost", False)
    )  # Löst die Sperre sofort wieder, damit es nicht permanent oben blockiert
    root.focus_force()

    app = PhonebookApp(root)

    root.mainloop()
if __name__ == "__main__":
    main()
