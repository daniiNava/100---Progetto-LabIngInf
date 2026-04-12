# Metodo utile per l'obiettivo 2 (Lettura dei GS dal filesystem)
import  json
from    pathlib import Path
from    fastapi import HTTPException
from    typing  import List, Dict

# Costruzione dinamica del percorso di base
# resolve(), ottiene il percorso assoluto, i parent risalgono la gerarchia fino alla root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
GS_DIR = BASE_DIR / "gs_data"

def get_gold_standard_by_url(url: str, domain:str) -> Dict[str, str]:
    """Legge il file JSON relativo a un dominio e restituisce la singola entry corrispondente all'URL richiesto"""
    file_path = GS_DIR / f"{domain}_gs.json"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File Gold Standard per il dominio {domain} non trovato nel percorso: {file_path}"
        )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)    # Il file è una lista di dizionari

            # Ricerca lineare dell'URL all'interno della lista
            for entry in data_list:
                if(entry.get("url")) == url:
                    return entry
                
        # Se il ciclo termina senza ritorni, l'URL non è presente
        raise HTTPException(status_code=404, detail="URL non presente nel Gold Standard")


    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corruzione del file JSON del Gold Standard")
    
def get_full_gold_standard(domain: str) -> List[Dict[str, str]]:
    """Legge e restituisce l'intero contenuto del file Gold Standard per un dato dominio"""
    file_path = GS_DIR / f"{domain}_gs.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File Gold Standard per il dominio {domain} non trovato")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
            return data_list
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corruzione del file JSON del Gold Standard")
        