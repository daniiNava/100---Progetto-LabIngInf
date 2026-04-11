# Questo è il modulo principale del server, definisce l'istanza FastAPI e gli endpoint sulla porta 8004.
# Inoltre, c'è la gestione delle richieste HTTP.

from fastapi import FastAPI, HTTPException, Query
from .models import (
    DocumentData, 
    DomainsResponse, 
    GoldStandardData, 
    FullGoldStandardResponse, 
    EvalueateRequest,
    EvalueateResponse
)

app = FastAPI(title="Pipeline NLP - Esonero 1", version="1.0")
# Definizione dei domini supportati
SUPPORTED_DOMAINS = ["it.wikipedia.org", "en.wikipedia.org"]

@app.get("/domains", response_model=DomainsResponse)
async def get_domains():
    """Restituisce la lista dei domini supportati."""
    return DomainsResponse(domains=SUPPORTED_DOMAINS)

@app.get("/parse", response_model=DocumentData)
async def parse_url(url: str = Query(..., description="URL da parsare")):
    """Esegue il parser per un documento di un dominio supportato."""
    # 1. Estrazione del dominio dall'URL
    domain = url.split("/")[2]  # Estrae il dominio dall'URL
    # 2. Verifica se il dominio è supportato
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    # 3. Chiamata al servizio asincrono di parsing (Crawl4AI)
    # document_data = await crawl4ai.parse(url)

    # 4. Restituzione dei dati
    return document_data

    pass # Da implementare integrando la logica del parser

@app.post("/evaluate", response_model=EvalueateResponse)
async def evaluate_document(request: EvalueateRequest):
    """Calcola le metriche di valutazione per un documento parsato (Precision, Recall, F1)."""
    # 1. Passare request.parsed_text e request.gold_text alla funzione di valutazione
    # 2. Costruire e restituire l'EvaluateResponse
    pass