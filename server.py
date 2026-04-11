import asyncio
from parser import ParserWikipediaIT,ParserBBC,ParserPeople,ParserRepubblica
from markdownCleaner import MarkdownCleaner
from tokenLevelEval import TokenLevelEval
import json

async def main():
#region Prova parser Wikipedia
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
#endregion
#region Prova parser BBC
    parser = ParserBBC()
    ret = await parser.parse("https://www.bbc.com/news/world-us-canada-34317754")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/BBC.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[0]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    parser = ParserBBC()
    ret = await parser.parse("https://www.bbc.com/news/articles/c1d9z1q2997o")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/BBC.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[1]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")
#endregion


if __name__ == "__main__":
    asyncio.run(main())