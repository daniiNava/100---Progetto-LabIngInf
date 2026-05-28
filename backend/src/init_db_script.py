import json
import time
from pathlib import Path
from services.db_service import init_db, insert_web_resource, insert_gold_standard, get_connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GS_DIR = BASE_DIR / "GS"

def wait_for_db(max_retries=10, delay=3):
    """Aspetta che il database sia pronto ad accettare connessioni."""
    print("Attesa del database MariaDB...")
    for i in range(max_retries):
        conn = get_connection()
        if conn:
            conn.close()
            print("Database pronto!")
            return True
        print(f"Database non ancora pronto. Riprovo in {delay} secondi... ({i+1}/{max_retries})")
        time.sleep(delay)
    return False

def populate_db_from_json():
    """Legge i file JSON nella cartella GS e li inserisce nel database."""
    
    # 1. Aspetta che il DB sia acceso
    if not wait_for_db():
        print("ERRORE CRITICO: Impossibile connettersi al database dopo vari tentativi. Popolamento fallito.")
        return

    print("Inizio popolamento del database dai file JSON...")
    
    # 2. Inizializza le tabelle
    init_db()
    
    if not GS_DIR.exists():
        print(f"Cartella {GS_DIR} non trovata. Popolamento saltato.")
        return

    # 3. Inserisce i dati
    for json_file in GS_DIR.glob("*.json"):
        print(f"Elaborazione file: {json_file.name}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
                
                for entry in data_list:
                    url = entry.get("url")
                    title = entry.get("title", "Titolo non disponibile")
                    html_text = entry.get("html_text", "")
                    gold_text = entry.get("gold_text", "")
                    
                    if url and html_text:
                        insert_web_resource(url, html_text, title)
                        if gold_text:
                            insert_gold_standard(url, gold_text)
                            
        except Exception as e:
            print(f"Errore durante la lettura di {json_file.name}: {e}")
            
    print("Popolamento completato.")

if __name__ == "__main__":
    populate_db_from_json()