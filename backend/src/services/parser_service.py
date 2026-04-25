"""
Modulo di servizio per la gestione dei parser.
Implementa il Design Pattern 'Factory/Strategy' per istanziare dinamicamente
il parser corretto in base al dominio richiesto.
"""
import re
from fastapi import HTTPException
from typing import Dict
from parser import ParserWikipediaIT, ParserBBC, ParserRepubblica, ParserPeople
 
async def run_parser(url: str, domain: str) -> Dict[str, str]:
    """
    Servizio asincrono per l'estrazione e la pulizia del testo da una pagina Web live.
    Istanzia il parser specifico per il dominio e avvia il crawling.
    """

    parser = None

    match domain:
        case "it.wikipedia.org":
            parser = ParserWikipediaIT()
        case "people.com": 
            parser = ParserPeople()
        case "www.bbc.com":
            parser = ParserBBC()
        case "www.repubblica.it":
            parser = ParserRepubblica()
        case _: 
            raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    try:
        return await parser.parse_by_url(url)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Errore interno del server durante il parsing: {str(e)}"
        )

async def run_parser_raw(url: str, domain:str, html_text: str) -> Dict[str, str]:
    """
    Esegue il parsing offline partendo da una stringa HTML grezza. 
    Utile per ottimizzare le valutazioni massive evitando richieste di rete ridondanti.
    """
    parser=None

    match domain:
        case "it.wikipedia.org":
            parser = ParserWikipediaIT()
        case "people.com": 
            parser = ParserPeople()
        case "www.bbc.com":
            parser = ParserBBC()
        case "www.repubblica.it":
            parser = ParserRepubblica()
        case _: 
            raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    try: 
        # Estrazione del titolo tramite espressione regolare
        match_title = re.search(r'<title>(.*?)</title>', html_text, re.IGNORECASE)
        extracted_title = match_title.group(1) if match_title else "Titolo non disponibile"

        mock_gs_data= {
            "url":url,
            "title":extracted_title,
            "html_text": html_text 
        }
        return await parser.parse_by_gs(mock_gs_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore interno del server durante il parsing raw. {str(e)}"
        )
    
    
    
    