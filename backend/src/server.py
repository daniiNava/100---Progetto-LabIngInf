# Questo è il modulo principale del server, definisce l'istanza FastAPI e gli endpoint sulla porta 8004.
# Inoltre, c'è la gestione delle richieste HTTP.

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from urllib.parse import urlparse

import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from models import (
    DocumentData, EvaluateRequest, EvaluateResponse, DomainsResponse, 
    TokenLevelEval, GoldStandardData, FullGoldStandardResponse
)
from services.parser_service import run_parser
from services.evaluation_service import calculate_metrics
from services.gs_service import get_gold_standard_by_url, get_full_gold_standard

app = FastAPI(title="Minera Web Parser API", version="1.0")

# Abilitazione CORS per permettere al frontend (porta 8004) di comunicare con noi (porta 8003)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definizione dei domini supportati
SUPPORTED_DOMAINS = ["it.wikipedia.org", "people.com", "www.bbc.com", "www.repubblica.it"]

@app.get("/domains", response_model=DomainsResponse)
async def get_domains():
    """Restituisce la lista dei domini supportati."""
    return DomainsResponse(domains=SUPPORTED_DOMAINS)

@app.get("/parse", response_model=DocumentData)
async def parse_url(url: str = Query(..., description="URL da parsare")):
    """Esegue il parser per un documento di un dominio supportato."""
    # 1. Estrazione del dominio dall'URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # 2. Verifica se il dominio è valido e supportato
    if not domain:
        raise HTTPException(status_code=400, detail="Formato URL non valido")
    
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    # 3. Chiamata al servizio asincrono di parsing (Crawl4AI)
    # Il costrutto 'await' delega l'esecuzione senza bloccare il thread principale
    result_dict = await run_parser(url, domain)

    # 4. Restituzione dei dati (Serializzazione tramite il modello Pydantic)
    return DocumentData(**result_dict)

@app.get("/gold_standard", response_model=GoldStandardData)
async def get_gold_standard(url: str = Query(..., description="L'URL del documento richiesto")):
    """Restituisce l'entry del Gold Standard corrispondente all'URL fornito"""
    # Analisi sintattica dell'URL per estrarre il dominio 
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
    """Restituisce tutte le entry del Gold Standard per un dominio specifico"""
    
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    # Chiamata al livello di servizio 
    gs_data = get_full_gold_standard(domain)

    # Serializzazione tramite Pydantic
    return FullGoldStandardResponse(gold_standard=gs_data)

@app.post("/evaluate", response_model=EvaluateResponse)     # Valutazione singola
async def evaluate_document(request: EvaluateRequest):
    """
    Calcola le metriche di valutazione (Precision, Recall, F1-Score) 
    confrontando un testo estratto con il relativo Golden Standard
    """

    # Invocazione del servizio matematico per il calcolo delle metriche
    metrics_dict = calculate_metrics(request.parsed_text, request.gold_text)

    # Instanziazione del modello annidato TokenLevelEval
    token_eval = TokenLevelEval(**metrics_dict)

    # Restituzione della risposta strutturata
    return EvaluateResponse(token_level_eval=token_eval)


@app.get("/full_gs_eval", response_model=EvaluateResponse)      # Valutazione generale di un dominio
async def evaluate_full_domain(domain: str = Query(..., description="Il dominio da valutare")):
    """
    Esegue una valutazione completa: recupera il Gold Standard per il dominio,
    effettua il parsing live degli URL e calcola le metriche medie
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
    doc_count = 0

    # Iterazione sui documenti del Gold Standard
    for gs_entry in gs_data_list:
        url = gs_entry.get("url")
        gold_text = gs_entry.get("gold_text")
        
        if not url or not gold_text:
            continue

        try:
            #Esecuzione del parsing live per il documento corrente
            parse_result = await run_parser(url, domain)
            parsed_text = parse_result.get("parsed_text", "")

            # Calcolo delle metriche per la singola iterazione
            metrics = calculate_metrics(parsed_text, gold_text)

            total_precision += metrics["precision"]
            total_recall += metrics["recall"]
            total_f1 += metrics["f1"]
            doc_count += 1

        except HTTPException:
            # Gestione silente o log dell'errore per documenti non raggiungibili durante il test
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

    # Restituzione di EvaluateResponse
    return EvaluateResponse(token_level_eval=avg_token_eval)

if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys

    # Forza windows a usare il gestore di eventi corretto per i sottoprocessi (PlayWright)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    uvicorn.run(app, host="127.0.0.1", port=8003)

    # avviare semplicemente scrviendo nel termile: "python server.py"