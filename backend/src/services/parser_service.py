from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from fastapi import HTTPException
from typing import Dict

async def run_parser(url: str, domain: str) -> Dict[str, str]:
    """Servizio asincrono per l'esteazione e la pulizia del testo da una pagina Web."""
    browser_cfg = BrowserConfig(headless=True) 
    crawler_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        excluded_tags=['nav', 'footer', 'script', 'style', 'aside'],
    )

    try:
        async with AsyncWebCrawler(browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=crawler_cfg)

            if not result.success:
                # Sollevare un'eccezione HTTP che viene gestita automaticamente da FastAPI
                raise HTTPException(
                    status_code=502, 
                    detail=f"Errore del crawler (Bad Gateway): {result.error.message}"
                )
            return {
                "url": url, 
                "domain": domain, 
                "title": result.metadata.get('title', 'Titolo mancante') if result.metadata else 'Titolo mancante',
                "html_text": result.html,
                "parsed_text": result.markdown
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Errore interno del server durante il parsing: {str(e)}"
        )
