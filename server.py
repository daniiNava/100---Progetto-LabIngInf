import asyncio
from parser import ParserWikipediaIT
async def main():
    #Prova parser Wikipedia
    parser = ParserWikipediaIT()
    ret = await parser.parse("https://it.wikipedia.org/wiki/Minerva")
    print(ret["parsed_text"].replace("## ", "\n").replace("_", "").replace("**", ""))

    

if __name__ == "__main__":
    asyncio.run(main())