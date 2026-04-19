# Modulo che contiene la logica per chiamare Crawl4AI (estrazione dati)
from fastapi import HTTPException
from typing import Dict
from parser import ParserWikipediaIT, ParserBBC, ParserRepubblica, ParserPeople
import re 
async def run_parser(url: str, domain: str) -> Dict[str, str]:
    """Servizio asincrono per l'estrazione e la pulizia del testo da una pagina Web."""

    parser = 0    

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

#nuova funzione 

async def run_parser_raw(url: str, domain:str, html_text: str) -> Dict[str, str]:
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
    
    
    
    