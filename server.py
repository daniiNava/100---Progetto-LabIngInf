import asyncio
from parser import ParserWikipediaIT,ParserBBC,ParserPeople,ParserRepubblica
from markdownCleaner import MarkdownCleaner
from tokenLevelEval import TokenLevelEval
import json
async def testWikipediaIT():
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

async def testBBC():
    parser = ParserBBC()
    ret = await parser.parse("https://www.bbc.com/news/world-us-canada-34317754")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/BBC.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[0]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    ret = await parser.parse("https://www.bbc.com/news/articles/c20q4nv89yzo")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/BBC.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[2]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    ret = await parser.parse("https://www.bbc.com/travel/article/20260410-why-its-impossible-to-measure-englands-coastline")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/BBC.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[3]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    ret = await parser.parse("https://www.bbc.com/culture/article/20260216-10-early-photographic-fakes-that-trick-the-eye")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/BBC.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[4]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

async def testRepubblica():
    parser = ParserRepubblica()
    ret = await parser.parse("https://www.repubblica.it/tecnologia/2023/12/12/news/startup_italiane_10_al_top-421587498/")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/Repubblica.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[0]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    ret = await parser.parse("https://www.repubblica.it/spettacoli/tv-radio/2026/04/10/news/cesaroni_il_ritorno_serie_tv_claudio_amendola_cast-425274728/")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/Repubblica.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[1]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    ret = await parser.parse("https://www.repubblica.it/salute/2024/12/05/news/l_influenza_che_non_passa_casi_in_aumento_cosa_succede_al_nostro_sistema_immunitario-423824877/")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/Repubblica.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[2]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    ret = await parser.parse("https://www.repubblica.it/economia/2024/04/13/news/la_benzina_non_si_ferma_piu_punte_di_28_euro_al_litro_il_governo_prezzo_medio_sotto_2_euro-422520446/")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/Repubblica.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[3]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

    ret = await parser.parse("https://www.repubblica.it/il-gusto/2024/09/14/news/suppli_migliori_a_roma_dove_mangiarli-423499807/")
    parsed_text_cleaned = MarkdownCleaner.clean(ret["parsed_text"])
    
    with open('GS/Repubblica.json', 'r', encoding='utf-8') as gs:
        gs_file = json.load(gs)
    gold_text = gs_file[4]["gold_text"]
    result = TokenLevelEval.eval(parsed_text_cleaned,gold_text)
    print(f"{ret["title"]} : {result:2f}")

async def main():
    #await testWikipediaIT()
    await testBBC()
    #await testRepubblica()


if __name__ == "__main__":
    asyncio.run(main())