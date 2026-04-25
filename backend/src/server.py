"""
Modulo principale dell'applicazione FastAPI. Gestisce il routing delle richieste HTTP, 
l'abilitazione del CORS e i servizi di parsing e valutazione.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse
import sys
import asyncio

# Fix per l'esecuzione di Playwright su Windows (Crawl4AI) in ambiente Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from models import (
    DocumentData, EvaluateRequest, EvaluateResponse, DomainsResponse, 
    TokenLevelEval, GoldStandardData, FullGoldStandardResponse, ParseRequest
)
from services.parser_service import run_parser, run_parser_raw
from services.evaluation_service import calculate_metrics
from services.gs_service import get_gold_standard_by_url, get_full_gold_standard

app = FastAPI(title="Minera Web Parser API", version="1.0")

# Configurazione CORS per consentire la comunicazione con il frontend (Web UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista dei domini supportati dal sistema
SUPPORTED_DOMAINS = ["it.wikipedia.org", "people.com", "www.bbc.com", "www.repubblica.it"]

@app.get("/domains", response_model=DomainsResponse)
async def get_domains():
    """Restituisce la lista dei domini web supportati dal sistema."""
    return DomainsResponse(domains=SUPPORTED_DOMAINS)

@app.get("/parse", response_model=DocumentData)
async def parse_url(url: str = Query(..., description="URL ddella pagina web da parsare")):
    """
    Riceve un URL, ne verifica la validità e delega l'estrazione 
    del testo al servizio di parsing asincrono.
    """
    # Estrazione del dominio dall'URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # Chiamata al servizio asincrono di parsing (Crawl4AI)
    result_dict = await run_parser(url, domain)

    #Restituzione dei dati (Serializzazione tramite il modello Pydantic)
    return result_dict

@app.post("/parse", response_model=DocumentData)
async def parse_raw_html(request: ParseRequest):

    """
    Esegue il parsing partendo da un HTML grezzo fornito nel body della richiesta,
    evitando il download della pagina tramite rete.
    """

    parsed_url=urlparse(request.url)
    domain=parsed_url.netloc

    if not domain:
        raise HTTPException(status_code=400, detail="Formato URL non valido")
    
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    result_dict=await run_parser_raw(request.url, domain, request.html_text)
    return DocumentData(**result_dict)

@app.get("/gold_standard", response_model=GoldStandardData)
async def get_gold_standard(url: str = Query(..., description="L'URL del documento richiesto")):
    """Restituisce l'entry del Gold Standard corrispondente all'URL fornito."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if not domain: 
        raise HTTPException(status_code=400, detail="Formato URL non valido")
    
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    # Chiamata al livello di servizio 
    gs_entry = get_gold_standard_by_url(url, domain)

    # Serializzazione tramite Pydantic
    return GoldStandardData(**gs_entry)

@app.get("/full_gold_standard", response_model=FullGoldStandardResponse)
async def get_full_gold_standard_endpoint(domain: str = Query(..., description="Il dominio di cui si richiede l'interno GS")):
    """Restituisce tutte le entry del Gold Standard per un dominio specifico."""
    
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    # Chiamata al livello di servizio 
    gs_data = get_full_gold_standard(domain)

    # Serializzazione tramite Pydantic
    return FullGoldStandardResponse(gold_standard=gs_data)

@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_document(request: EvaluateRequest):
    """
    Calcola le metriche di valutazione (Precision, Recall, F1-Score) 
    confrontando un testo estratto con il relativo Golden Standard.
    """

    # Invocazione del servizio matematico per il calcolo delle metriche
    metrics_dict = calculate_metrics(request.parsed_text, request.gold_text)

    # Instanziazione del modello annidato TokenLevelEval
    # token_eval = metrics_dict
    token_eval = TokenLevelEval(**metrics_dict)
    
    # Restituzione della risposta strutturata
    return EvaluateResponse(token_level_eval=token_eval)

@app.get("/full_gs_eval", response_model=EvaluateResponse)
async def evaluate_full_domain(domain: str = Query(..., description="Il dominio da valutare")):
    """
    Esegue una valutazione completa: recupera il Gold Standard per il dominio,
    effettua il parsing offline (tramite HTML salvato) degli URL e calcola le metriche medie.
    """
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    # Recupero del Gold Standard per il dominio richiesto
    gs_data_list = get_full_gold_standard(domain)

    if not gs_data_list:
        raise HTTPException(status_code=404, detail="Gold Standard vuoto o inesistente per il dominio")
    
    total_precision = 0.0
    total_recall = 0.0
    total_f1 = 0.0
    doc_count = len(gs_data_list)

    # Iterazione sui documenti del Gold Standard
    for gs_entry in gs_data_list:
        url = gs_entry.get("url")
        gold_text = gs_entry.get("gold_text")
        html_text = gs_entry.get("html_text")
        
        if not url or not gold_text:
            continue

        try:
            # Ottimizzazione: parsing dell'HTML locale senza chiamate di rete
            parse_result = await run_parser_raw(url, domain,html_text)
            parsed_text = parse_result.get("parsed_text", "")

            # Calcolo delle metriche per la singola iterazione
            metrics = calculate_metrics(parsed_text, gold_text)

            total_precision += metrics["precision"]
            total_recall += metrics["recall"]
            total_f1 += metrics["f1"]
            

        except HTTPException:
            # Ignora i documenti problematici per non bloccare la valutazione globale
            continue

    if doc_count == 0:
        raise HTTPException(status_code=500, detail=("Impossibile valutare i documenti (errori di parsing)"))
    
    # Calcolo delle metriche aritmetiche
    avg_precision = total_precision / doc_count
    avg_recall = total_recall / doc_count
    avg_f1 = total_f1 / doc_count

    # Creazione dell'oggetto TokenLevelEval con le medie
    avg_token_eval = TokenLevelEval(
        precision=round(avg_precision, 4),
        recall=round(avg_recall, 4),
        f1=round(avg_f1, 4),
    )

    return EvaluateResponse(token_level_eval=avg_token_eval)

if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys

    # Forza windows a usare il gestore di eventi corretto per i sottoprocessi (PlayWright)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Avvio del server per ambiente di sviluppo locale
    uvicorn.run(app, host="127.0.0.1", port=8003)

    # avviare semplicemente scrivendo nel terminale: "python server.py"