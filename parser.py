from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator
from abc import ABC,abstractmethod
#https://people.com	https://www.bbc.com	https://www.repubblica.it
class Parser(ABC):
    def __init__(self):
        pass
    async def parse(self, url : str) -> dict:
        pass

class ParserWikipediaIT(Parser):
    def __init__(self):
        self.domain = "it.wikipedia.org"
        
    async def parse(self, url : str) -> dict:
        #TODO: Rimozione link riferimento alla fine
        html_text = ""
        clean_sup_script = """document.querySelectorAll('sup').forEach(el => el.remove());"""

        browser_cfg = BrowserConfig(headless=False)
        crawler_cfg_html = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        crawler_cfg_parsed = CrawlerRunConfig(
            js_code=clean_sup_script,
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True,"with_metadata": False}),
            css_selector=".firstHeading,.mw-body-content",
            excluded_selector=".hatnote,[aria-labelledby='Note'],[aria-labelledby='Note'] ~ *,.mw-editsection,.infobox",
            excluded_tags=["form", "header", "footer", "nav", "script", "style", "figure", "sup", "img"],
            exclude_external_links=True,    
            exclude_social_media_links=True,
            exclude_external_images=True
            )

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(
                url = url,
                config = crawler_cfg_html
            )
            html_text = result.html
            result = await crawler.arun(
                url = f"raw:{html_text}",
                config = crawler_cfg_parsed
            )
        if not result.success:
            raise RuntimeError(result.error_message)
        return{
            "url":url,
            "domain":self.domain,
            "title":result.markdown.split("\n",1)[0].replace("#","").strip(),
            "html_text":html_text,
            "parsed_text":result.markdown.split("\n",1)[1]
        }

class ParserBBC(Parser):
    def __init__(self):
        self.domain = "https://www.bbc.com"
    async def parse(self, url : str) -> dict:
        pass

class ParserPeople(Parser):
    def __init__(self):
        self.domain = "https://people.com"
    async def parse(self, url : str) -> dict:
        pass

class ParserRepubblica(Parser):
    def __init__(self):
        self.domain = "https://www.repubblica.it"
    async def parse(self, url : str) -> dict:
        pass