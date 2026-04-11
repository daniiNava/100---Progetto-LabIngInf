import asyncio
from parser import ParserWikipediaIT
from markdownCleaner import MarkdownCleaner
from tokenLevelEval import TokenLevelEval
import json

async def main():
    #Prova parser Wikipedia
    parser = ParserWikipediaIT()
    ret = await parser.parse("https://it.wikipedia.org/wiki/Minerva")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])

    with open('GS/WikipediaIT.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[0]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    ret = await parser.parse("https://it.wikipedia.org/wiki/BabelNet")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])

    with open('GS/WikipediaIT.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[1]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")


if __name__ == "__main__":
    asyncio.run(main())