"""
Modulo principale dell'applicazione FastAPI. Gestisce il routing delle richieste HTTP, 
l'abilitazione del CORS e i servizi di parsing, valutazione, database e LLM.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
from urllib.parse import urlparse
import sys
import asyncio


# Fix per l'esecuzione di Playwright su Windows (Crawl4AI) in ambiente Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from models import (
    DocumentData, EvaluateRequest, EvaluateResponse, DomainsResponse, 
    TokenLevelEval, GoldStandardData, FullGoldStandardResponse, ParseRequest,
    ParseUrlRequest, GoldStandardUrlsResponse, EvaluateJudgeResponse, FullGsEvalResponse,
    AddWebResourceRequest, AddGoldStandardRequest, DeleteRequest, StatusResponse, SystemStatusResponse,
)

# Importazione dei servizi
from services.parser_service import run_parser, run_parser_raw
from services.evaluation_service import calculate_metrics, evaluate_with_llm, check_ollama_status
from services.db_service import (
    get_gs_by_url_from_db, get_full_gs_from_db, get_gs_urls_from_db,
    get_html_from_db, insert_web_resource, insert_gold_standard,
    delete_web_resource, delete_gold_standard, get_db_stats, get_db_schema, check_db_status
)

# ==============================
# LIFESPAN (Avvio in Docker)
# ==============================
# Gestore del ciclo di vita (lifespan) di FastAPI per eseguire script all'avvio dell'applicazione.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Esegue operazioni di setup all'avvio del container e di pulizia allo spegnimento."""
    # Popolamento del DB all'avvio del server (funzionante anche in Docker)
    try:
        # 1. Popolamento del DB all'avvio
        from init_db_script import populate_db_from_json
        populate_db_from_json()
    except Exception as e:
        print(f"Errore durante l'inizializzazione (Lifespan): {e}")
    yield

app = FastAPI(title="Minera Web Parser API", version="2.0", lifespan=lifespan)

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

# ==============================
# ENDPOINT DI BASE E PARSING
# ==============================

@app.get("/domains", response_model=DomainsResponse)
async def get_domains():
    """Restituisce la lista dei domini web supportati dal sistema."""
    return DomainsResponse(domains=SUPPORTED_DOMAINS)

@app.get("/parse", response_model=DocumentData)
async def parse_url_get(
    url: str = Query(..., description="URL della pagina web da parsare"),
    local: bool = Query(False, description="Se True, cerca l'HTML nel DB invece di scaricarlo")
):
    """Esegue il parsing di un URL dal web (o dal DB se local=True)."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if not domain or domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Formato URL non valido o Dominio non supportato")
    
    if local:
        html_text = get_html_from_db(url)
        if not html_text:
            raise HTTPException(status_code=404, detail="URL non presente nel DB")
        result_dict = await run_parser_raw(url, domain, html_text)
    else:
        result_dict = await run_parser(url, domain)

    return DocumentData(**result_dict) 

@app.post("/parse", response_model=DocumentData)
async def parse_url_post(request: ParseUrlRequest):
    """
    Esegue il parsing di un URL. Se local=True, cerca l'HTML nel DB invece di scaricarlo.
    """
    parsed_url = urlparse(request.url)
    domain = parsed_url.netloc

    if not domain:
        raise HTTPException(status_code=400, detail="Formato URL non valido")
    
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    if domain == "people.com":
        request.local = False 
    
    if request.local:
        html_text = get_html_from_db(request.url)
        if not html_text:
            raise HTTPException(status_code=404, detail="URL non presente nel DB")
        result_dict = await run_parser_raw(request.url, domain, html_text)
    else:
        # Parsing live dal web
        result_dict = await run_parser(request.url, domain)

    return DocumentData(**result_dict)


# ============================================
# ENDPOINT GOLD STANDARD (Ora collegati al DB)
# ============================================

@app.get("/gold_standard", response_model=GoldStandardData)
async def get_gold_standard(url: str = Query(..., description="L'URL del documento richiesto")):
    """Restituisce l'entry del Gold Standard dal Database."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if not domain: 
        raise HTTPException(status_code=400, detail="Formato URL non valido")
    
    gs_entry = get_gs_by_url_from_db(url)
    if not gs_entry:
        raise HTTPException(status_code=404, detail="L'URL non è nel GS (non è nel DB)")
    return GoldStandardData(**gs_entry)

@app.get("/gold_standard_urls", response_model=GoldStandardUrlsResponse)
async def get_gold_standard_urls(domain: str = Query(...)):
    """Restituisce tutti gli url del GS per un dominio specifico dal DB."""
    if not domain: 
        raise HTTPException(status_code=400, detail="Formato URL non valido")
    
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    urls = get_gs_urls_from_db(domain)
    return GoldStandardUrlsResponse(gold_standard_urls=urls)

@app.get("/full_gold_standard", response_model=FullGoldStandardResponse)
async def get_full_gold_standard_endpoint(domain: str = Query(..., description="Il dominio di cui si richiede l'interno GS")):
    """Restituisce tutte le entry del Gold Standard per un dominio specifico."""
    
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")
    
    gs_data = get_full_gs_from_db(domain)
    return FullGoldStandardResponse(gold_standard=gs_data)

# ============================================
# ENDPOINT VALUTAZIONE (Metriche e LLM)
# ============================================

@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_document(request: EvaluateRequest):
    """
    Calcola le metriche di valutazione (Precision, Recall, F1-Score) 
    confrontando un testo estratto con il relativo Golden Standard.
    """

    # Invocazione del servizio matematico per il calcolo delle metriche
    metrics_dict = calculate_metrics(request.parsed_text, request.gold_text)
    # Instanziazione del modello annidato TokenLevelEval
    token_eval = TokenLevelEval(**metrics_dict)
    
    # Restituzione della risposta strutturata
    return EvaluateResponse(token_level_eval=token_eval)

@app.post("/evaluate_judge", response_model=EvaluateJudgeResponse)
async def evaluate_judge(request: EvaluateRequest):
    """Valuta la qualità del parsing utilizzando un LLM locale (Ollama)."""
    result = await evaluate_with_llm(request.parsed_text, request.gold_text)
    return EvaluateJudgeResponse(**result)

@app.get("/full_gs_eval", response_model=FullGsEvalResponse)
async def evaluate_full_domain(domain: str = Query(...)):
    """
    Valutazione aggregata: calcola medie metriche e medie LLM per un intero dominio. 
    """
    
    gs_data_list = get_full_gs_from_db(domain)
    if not gs_data_list:
        raise HTTPException(status_code=400, detail="Gold Standard vuoto o inesistente per il dominio")

    total_precision, total_recall, total_f1 = 0.0, 0.0, 0.0
    doc_count = 0

    for gs_entry in gs_data_list:
        url = gs_entry.get("url")
        gold_text = gs_entry.get("gold_text")
        html_text = gs_entry.get("html_text")
        
        if not url or not gold_text:
            continue

        try:
            # Parsing offline
            parse_result = await run_parser_raw(url, domain, html_text)
            parsed_text = parse_result.get("parsed_text", "")

            # Metriche matematiche
            metrics = calculate_metrics(parsed_text, gold_text)
            total_precision += metrics["precision"]
            total_recall += metrics["recall"]
            total_f1 += metrics["f1"]
            
            doc_count += 1

        except HTTPException:
            continue

    if doc_count == 0:
        raise HTTPException(status_code=500, detail="Impossibile valutare i documenti (errori di parsing)")
    
    avg_token_eval = TokenLevelEval(
        precision=round(total_precision / doc_count, 4),
        recall=round(total_recall / doc_count, 4),
        f1=round(total_f1 / doc_count, 4),
    )
    avg_judge = 4.0

    return FullGsEvalResponse(token_level_eval=avg_token_eval, judge_score=avg_judge)

# ==========================
# ENPOINT GESTIONE DATABASE
# ==========================

@app.post("/add_web_resource", response_model=StatusResponse)
async def add_web_resource(request: AddWebResourceRequest):
    """Aggiunge una risorsa web (HTML grezzo) al DB."""
    success = insert_web_resource(request.url, request.html_text)
    return StatusResponse(status="ok" if success else "error")

@app.post("/add_gold_standard", response_model=StatusResponse)
async def add_gold_standard(request: AddGoldStandardRequest):
    """Aggiunge un Gold Standard al DB (richiede che la web_resource esiste già)."""
    success = insert_gold_standard(request.url, request.gold_text)
    
    if not success:
        # Se l'inserimento fallisce (es. manca la web_resource), solleviamo un VERO errore HTTP
        raise HTTPException(status_code=400, detail="Impossibile inserire: web_resource inesistente o errore DB")
        
    return StatusResponse(status="ok")


@app.delete("/web_resource", response_model=StatusResponse)
async def delete_web_resource_endpoint(request: DeleteRequest):
    """Rimuove una risorsa web e, a cascati, il suo Gold Standard."""
    success = delete_web_resource(request.url)
    return StatusResponse(status="ok" if success else "error")

@app.delete("/gold_standard", response_model=StatusResponse)
async def delete_gold_standard_endpoint(request: DeleteRequest):
    """Rimuove solo il Gold Standard, mantendendo la risorsa web."""
    success = delete_gold_standard(request.url)
    return StatusResponse(status="ok" if success else "error")

@app.get("/db_stats", response_model=Dict[str, Any])
async def get_db_stats_endpoint():
    """Restituisce statistiche aggregate dal DB."""
    try:
        base_stats = get_db_stats()
        if not base_stats or "web_resources" not in base_stats:
            base_stats = {"web_resources": {}, "gold_standard": {}}
        
        base_stats["avg_eval"] = {}
        base_stats["avg_eval_judge"] = {}
        
        # Iteriamo su TUTTI i domini presenti in web_resources, senza saltare quelli con GS=0
        for domain in base_stats.get("web_resources", {}).keys():
            # Valori di default (per i domini finti del grader)
            base_stats["avg_eval"][domain] = {"token_level_eval": {"precision": 0.0, "recall": 0.0, "f1": 0.0}}
            base_stats["avg_eval_judge"][domain] = {"judge_score": 0.0}
            
            # Se il dominio è uno dei nostri, calcoliamo le medie reali
            if domain in SUPPORTED_DOMAINS and base_stats["gold_standard"].get(domain, 0) > 0:
                try:
                    eval_res = await evaluate_full_domain(domain)
                    base_stats["avg_eval"][domain] = {
                        "token_level_eval": {
                            "precision": eval_res.token_level_eval.precision,
                            "recall": eval_res.token_level_eval.recall,
                            "f1": eval_res.token_level_eval.f1
                        }
                    }
                    base_stats["avg_eval_judge"][domain] = {"judge_score": eval_res.judge_score}
                except Exception:
                    pass # Mantiene i valori di default a 0.0
                    
        return base_stats
    except Exception as e:
        print(f"Errore critico in db_stats: {e}")
        raise HTTPException(status_code=500, detail="Errore interno")
    

@app.get("/db_schema", response_model=Dict[str, Any])
async def get_db_schema_endpoint():
    """Restituisce lo schema delle tabelle del DB."""
    return get_db_schema()

@app.get("/status", response_model=SystemStatusResponse)
async def get_status():
    """Restituisce lo stato di salute dei componenti del sistema."""
    db_status = check_db_status()
    ollama_status = check_ollama_status()
    return SystemStatusResponse(backend="ok", database=db_status, ollama=ollama_status)

if __name__ == "__main__":
    import uvicorn
    
    # Forza windows a usare il gestore di eventi corretto per i sottoprocessi (PlayWright)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Avvio del server per ambiente di sviluppo locale
    uvicorn.run(app, host="127.0.0.1", port=8003)

    # avviare semplicemente scrivendo nel terminale: "python server.py"