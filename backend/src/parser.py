from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator
from abc import ABC,abstractmethod
#https://people.com	https://www.bbc.com	https://www.repubblica.it
class Parser(ABC):
    async def parse_by_url(self, url : str) -> dict:
        html_text = ""
        title = ""
        markdown_text=""

        browser_cfg = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(
                url = url, magic_mode=True
            )
            if not result.success:
                raise RuntimeError(result.error_message)
            html_text = result.html
            title = result.metadata.get('og:title')
            result = await crawler.arun(
                url = f"raw:{html_text}",
                config = self.crawler_cfg_parsed
            )
        if not result.success:
            raise RuntimeError(result.error_message)
        
        markdown_text = self.clean_markdown(result.markdown)
        return{
            "url":url,
            "domain":self.domain,
            "title":title,
            "html_text":html_text,
            "parsed_text":markdown_text
        }
    async def parse_by_gs(self, gs_json : dict) -> dict:
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
        return markdown

class ParserWikipediaIT(Parser):
    def __init__(self):
        self.domain = "it.wikipedia.org"
        self.crawler_cfg_parsed = CrawlerRunConfig(
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
        return markdown.rsplit("\n",2)[0] 

class ParserBBC(Parser):
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
        return markdown.rsplit("--",2)[0]

class ParserPeople(Parser):
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