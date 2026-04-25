import asyncio
from parser import ParserWikipediaIT,ParserBBC,ParserPeople,ParserRepubblica,Parser
from markdownCleaner import MarkdownCleaner
from tokenLevelEval import calculate_metrics
import json
def scrivi_json(dati : dict):
    with open('risultato.json', 'w', encoding='utf-8') as f:
        json.dump(dati["html_text"], f)

async def testWikipediaIT():
    parser = ParserWikipediaIT()
    with open('GS/WikipediaIT.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    await validate_gs(gs_file,parser)

async def testBBC():
    parser = ParserBBC()
    with open('GS/BBC.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    await validate_gs(gs_file,parser)

async def testRepubblica():
    parser = ParserRepubblica()
    with open('GS/Repubblica.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    await validate_gs(gs_file,parser)


async def testPeople():
    parser = ParserPeople()
    with open('GS/People.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    await validate_gs(gs_file,parser)
    
async def validate_gs(gs_file : dict, parser : Parser):
    for gs_json in gs_file:
        gold_text = gs_json["gold_text"]
        
        ret = await parser.parse_by_gs(gs_json)
        parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])

        result = calculate_metrics(parsed_text_cleaned,gold_text)
        print(f"{ret["title"]} : {result["f1"]:2f}")
        
async def validate_url(gs_file : dict, parser : Parser): 
    for gs_json in gs_file:
        gold_text = gs_json["gold_text"]
        url = gs_json["url"]

        ret = await parser.parse_by_url(url)
        parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])

        result = calculate_metrics(parsed_text_cleaned,gold_text)
        print(f"{ret["title"]} : {result["f1"]:2f}")
        scrivi_json(ret)

async def main():
    #await testWikipediaIT()
    #await testBBC()
    #await testRepubblica()
    await testPeople()


if __name__ == "__main__":
    asyncio.run(main())