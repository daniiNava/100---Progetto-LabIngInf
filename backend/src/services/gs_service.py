"""
Modulo di servizio per la gestione dell'I/O sui file del Gold Standard.
Utilizza la libreria 'pathlib  per una risoluzione robusta dei percorsi assoluti, 
garantendo la portabilità del codice tra ambienti di sviluppo e container Docker.
"""

import  json
from    pathlib import Path
from    fastapi import HTTPException
from    typing  import List, Dict

# Risoluzione dinamica della directory root del progetto
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
GS_DIR = BASE_DIR / "GS"

# Mapping statico tra domini supportati e i rispettivi file JSON
FILE_DOMAINS = {
    "it.wikipedia.org":"WikipediaIT.json", 
    "people.com":"People.json", 
    "www.bbc.com":"BBC.json", 
    "www.repubblica.it":"Repubblica.json"
}

def get_gold_standard_by_url(url: str, domain:str) -> Dict[str, str]:
    """
    Legge il file JSON relativo a un dominio e restituisce la singola entry 
    corrispondente all'URL richiesto tramite ricerca lineare
    
    Args:
        url (str): L'URL specifico da cercare.
        domain (str): Il dominio di appartenenza dell'URL.

    Returns:
        Dict[str, str]: Dizionario contenente i dati del Gold Standard per l'URL richiesto.
    """
    file_path = GS_DIR / FILE_DOMAINS[domain]
    
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
    """
    Legge e restituisce l'intero contenuto del file Gold Standard per un dato dominio
    
    Args:
        domain (str): Il dominio di cui recuperare il dataset.

    Returns:
        List[Dict[str, str]]: Lista di tutte le entry presenti nel file JSON.
    """
    file_path = GS_DIR / FILE_DOMAINS[domain]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File Gold Standard per il dominio {domain} non trovato")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
            return data_list
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corruzione del file JSON del Gold Standard")
        