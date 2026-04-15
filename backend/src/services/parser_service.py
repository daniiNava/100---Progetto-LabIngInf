# Modulo che contiene la logica per chiamare Crawl4AI (estrazione dati)
from fastapi import HTTPException
from typing import Dict
from parser import ParserWikipediaIT, ParserBBC, ParserRepubblica, ParserPeople

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
    
    
    
    # browser_cfg = BrowserConfig(headless=True) 
    
    # # Definizione di selettori specifici per migliorare la qualità dell'output per LLM
    # # Se il dominio è uno di quelli assegnati successivamente (ovvero è una testata giornalistica), 
    # # si escludono utleriori elementi di disturbo
    # excluded = ['nav', 'footer', 'script', 'style', 'aside', '.ads', '.social.share']

    # crawler_cfg = CrawlerRunConfig(
    #     cache_mode=CacheMode.BYPASS,
    #     excluded_tags=excluded,
    #     magic_mode=True  # Opzione di Crawl4AI per bypassare i blocchi anti-bot tipici dei siti di news
    # )
    
    # try:
    #     async with AsyncWebCrawler(config=browser_cfg) as crawler:
    #         result = await crawler.arun(url=url, config=crawler_cfg)

    #         if not result.success:
    #             # Sollevare un'eccezione HTTP che viene gestita automaticamente da FastAPI
    #             raise HTTPException(
    #                 status_code=502, 
    #                 detail=f"Errore del crawler su {domain}: {result.error.message}"
    #             )
    #         return {
    #             "url": url, 
    #             "domain": domain, 
    #             "title": result.metadata.get('title', 'Titolo mancante') if result.metadata else 'Titolo mancante',
    #             "html_text": result.html,
    #             "parsed_text": result.markdown
    #         }
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500, 
    #         detail=f"Errore interno del server durante il parsing: {str(e)}"
    #     )
