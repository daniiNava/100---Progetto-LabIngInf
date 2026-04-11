import asyncio
from parser import ParserWikipediaIT
from markdownCleaner import MarkdownCleaner
async def main():
    #Prova parser Wikipedia
    parser = ParserWikipediaIT()
    ret = await parser.parse("https://it.wikipedia.org/wiki/Minerva")
    print(MarkdownCleaner.clean(ret["parsed_text"]))

if __name__ == "__main__":
    asyncio.run(main())