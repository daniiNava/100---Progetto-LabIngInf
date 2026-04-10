import asyncio
from parser import ParserWikipediaIT
async def main():
    parser = ParserWikipediaIT()
    ret = await parser.parse("https://it.wikipedia.org/wiki/Jo%C3%A3o_Fonseca_(tennista)")
    print(ret["parsed_text"].replace("## ", "\n").replace("_", "").replace("**", ""))
if __name__ == "__main__":
    asyncio.run(main())