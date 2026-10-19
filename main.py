import os
import webbrowser
from time import sleep
import threading
import logging
import logging.config

from pathlib import Path
import gui_tkinter
import konsole_telefonbuch
import uvicorn
from api import TelefonbuchAPI 

def open_browser_delayed(url, delay=4):
    """Wartet kurz und öffnet dann den Browser."""
    sleep(delay)
    webbrowser.open(url, new=2)
    exit()


def main():

    aktuelles_verzeichnis = os.path.dirname(os.path.abspath(__file__))
    os.environ['LOG_DIR'] = aktuelles_verzeichnis
    logging_path = Path(__file__).parent / "logging_config.ini"
    logging.config.fileConfig(logging_path, 
        defaults={'LOG_DIR': aktuelles_verzeichnis.replace('\\', '/')}) 

    logger = logging.getLogger(__name__)

    datei_name = "telefonbuch.html"
    ordner = Path(__file__).parent / datei_name
    url = f"file://{ordner}"

    logger.info("Programm Start")
    print("Was wollen Sie " \
    "starten")
    print("1: Telefonbuch Konsole")
    print("2: Telefonbuch Tkinter GUI")
    print("3: Telefonbuch api + HTML")

    try:
        auswahl = input(": ")
        
    except KeyboardInterrupt:
        logger.error("Modul main KeyboardInterrupt bei Input")
        exit()

    match auswahl:
        case "1":
            logging.info("Start Konsole")
            konsole_telefonbuch.main()
            logging.info("Ende Konsole")
            exit()
        case "2":
            logging.info("Start Tkinter GUI")
            gui_tkinter.main()
            logging.info("Ende Tkinter GUI")
            exit()
        case "3":
            logging.info("Initialisiere API-Klasse...")
            api_instanz = TelefonbuchAPI()

            config = uvicorn.Config(
                app=api_instanz.app, 
                host="0.0.0.0", 
                port=8000, 
                log_level="info"
            )
            server = uvicorn.Server(config)

            logging.info("Start Browser-Thread")
            browser_thread = threading.Thread(
                target=open_browser_delayed, args=(url, 2)
            )
            browser_thread.daemon = True
            browser_thread.start()

            api_thread = threading.Thread(target=server.run)
            api_thread.daemon = True 
            logging.info("Start API-Thread im Hintergrund")
            api_thread.start()

            print("\n" + "="*50)
            print(" API läuft erfolgreich im Hintergrund.")
            print(" Drücke [ENTER] in dieser Konsole, um die API zu stoppen.")
            print("="*50 + "\n")            
            input() 

            logging.info("Stoppe API-Server...")
            server.should_exit = True 

            api_thread.join(timeout=5) 
            logging.info("API-Server wurde erfolgreich beendet.")
            print("\n[✓] Server gestoppt. Zurück zum Hauptmenü...")

        case _:
            logging.info("Auswahl Ende")
            exit()


if __name__ == "__main__":
    main()

