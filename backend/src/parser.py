"""
Modulo core per l'estrazione e la pulizia dei contenuti web.
Implementa il Design Pattern Strategy per gestire l'eterogeneità dei domini:
una classe astratta base definisce il contratto di parsing, mentre le sottoclassi
applicano regole specifiche (CSS Selector, inizioni JS) per ogni dominio supportato.
"""
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator
from abc import ABC, abstractmethod
#https://people.com	https://www.bbc.com	https://www.repubblica.it
class Parser(ABC):
    """
    Classe astratta base (Strategy) per i parser di dominio.
    Gestisce il ciclo di vita del crawler asincrono e definisce i metodi comuni
    per il parsing live (da URL) e offline (da Gold Standard JSON, HTML grezzo).
    """

    async def parse_by_url(self, url : str) -> dict:
        """
        Esegue il crawling live della pagina web, estrae i metadati e applica
        le regole di pulizia specifiche del dominio per restituire un output strutturato.
        """
        html_text = ""
        title = ""
        markdown_text=""

        # Configurazione headless per l'esecuzione in background (compatibile con Docker) 
        browser_cfg = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # 1. Fetch iniziale con magic_mode per bypassare eventuali blocchi anti-bot e ottenere l'HTML completo
            result = await crawler.arun(
                url = url, magic_mode=True
            )

            if not result.success:
                raise RuntimeError(result.error_message)
            
            html_text = result.html
            title = result.metadata.get('og:title')
            
            # 2. Applicazione delle regole di pulizia specifiche (CSS/JS)
            result = await crawler.arun(
                url = f"raw:{html_text}",
                config = self.crawler_cfg_parsed
            )
        
        if not result.success:
            raise RuntimeError(result.error_message)
        
        # 3. Post-processing del Markdown per eventuali pulizie finali
        markdown_text = self.clean_markdown(result.markdown)
        return{
            "url":url,
            "domain":self.domain,
            "title":title,
            "html_text":html_text,
            "parsed_text":markdown_text
        }
    

    async def parse_by_gs(self, gs_json : dict) -> dict:
        """
        Esegue il parsing offline partendo dall'HTML grezzo salvato nel Gold Standard.
        Ottimizza le prestazini azzerando il carico di rete.
        """
        html_text = gs_json["html_text"]
        browser_cfg = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(
                url = f"raw:{html_text}",
                config = self.crawler_cfg_parsed
            )

        if not result.success:
            raise RuntimeError(result.error_message)
        
        markdown_text = self.clean_markdown(result.markdown) 
        return{
            "url":gs_json["url"],
            "domain":self.domain,
            "title":gs_json["title"],
            "html_text":html_text,
            "parsed_text":markdown_text
        }
    
    def clean_markdown(self, markdown : str) -> str:
        """
        Metodo di hook per il post-processing testuale.
        Può essere sovrascritto dalle sottoclassi per pulizie specifiche.
        """
        return markdown

class ParserWikipediaIT(Parser):
    """Implementazione della strategia di parsing per il dominio it.wikipedia.org"""
    def __init__(self):
        self.domain = "it.wikipedia.org"
        self.crawler_cfg_parsed = CrawlerRunConfig(
            # Iniezione JS per rimuovere i numerini dele note a piè di pagina prima del parsing
            js_code = """document.querySelectorAll('sup.reference').forEach(el => el.remove());""",
            cache_mode=CacheMode.BYPASS,
            css_selector=".mw-body-content",
            excluded_selector=".toccolours,.hatnote,[aria-labelledby='Note'],[aria-labelledby='Note'] ~ *,.mw-editsection,.infobox,.avviso",
            excluded_tags=["form", "header", "footer", "nav", "script", "style", "figure", "img","button"],
            exclude_external_images=True,
            exclude_social_media_links=True,
            exclude_external_links=True,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True})
            )

    def clean_markdown(self, markdown : str) -> str:
        """Rimuove eventuali blocchi di testo residui a fine pagina."""
        return markdown.rsplit("\n",2)[0] 

class ParserBBC(Parser):
    """Implementazione della strategia di parsing per il dominio www.bbc.com"""
    def __init__(self):
        self.domain = "www.bbc.com"
        self.crawler_cfg_parsed = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            css_selector="#main-content,.HooNV,.fWTqWp,.faEbjU",
            excluded_tags=["form","header", "footer", "nav", "script", "style", "figure", "sup", "img","button"],
            excluded_selector="#additional-reporting-by-grace-eliza-goodwin,[id='top-picture-credits:-reuters-and-getty-images'],[id='is-the-home-on-the-website-and-app-for-the-best-analysis,-with-fresh-perspectives-that-challenge-assumptions-and-deep-reporting-on-the-biggest-issues-of-the-day.-emma-barnett-and-john-simpson-bring-their-pick-of-the-most-thought-provoking-deep-reads-and-analysis,-every-saturday.'],[id='sign-up-for-the-newsletter-here'],[id='bbc-indepth']",
            exclude_external_images=True,
            exclude_social_media_links=True,
            exclude_external_links=True,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True})
            )
    def clean_markdown(self, markdown : str) -> str:
        """Rimuove i blocchi 'Read more' o footer testuali separati da '--'."""
        return markdown.rsplit("--",2)[0]

class ParserPeople(Parser):
    """Implementazione della strategia di parsing per il dominio people.com"""
    def __init__(self):
        self.domain = "people.com"
        self.crawler_cfg_parsed = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            css_selector=".article-subheading,#article-content_1-0",
            excluded_tags=["form", "footer","header", "nav", "script", "style", "figure", "img","button","strong"],
            excluded_selector=".people-sc-block-spotlight,.people-sc-block-featuredlink,.people-sc-block-callout,.people-sc-block-spotlight--mid-circ,.people-sc-block-featuredlink--people-app-promo",
            exclude_external_images=True,
            exclude_social_media_links=True,
            exclude_external_links=True,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True})
            )

class ParserRepubblica(Parser):
    """Implementazione della strategia di parsing per il dominio www.repubblica.it"""
    def __init__(self):
        self.domain = "www.repubblica.it"
        self.crawler_cfg_parsed = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            css_selector=".story__text,.story__summary",
            excluded_tags=["form", "footer", "nav", "script", "style", "figure", "img","button"],
            excluded_selector=".inline-article,.inline-embed,.inline-video",
            exclude_external_images=True,
            exclude_social_media_links=True,
            exclude_external_links=True,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True})
            )