"""
Modulo per la definizione degli schemi dei dati tramite Pydantic.
Garantisce la validazione statica e a runtime degli input/output delle API REST,
oltre a generare automaticamente la documentazione Swagger UI.
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any

# --- MODELLI BASE ---

class DocumentData(BaseModel):
    """Modello di output dell'endpoint /parse e struttura base dei documenti."""
    url: str
    domain: str
    title: str
    html_text: str
    parsed_text: str

class GoldStandardData(BaseModel):
    """Modello rappresentativo di una singola entry all'interno del Gold Standard."""
    url: str
    domain: str
    title: str
    html_text: str
    gold_text: str

class DomainsResponse(BaseModel):
    """Modello di risposta per l'endpoint /domains, che restituisce la lista dei domini supportati."""
    domains: List[str]

class FullGoldStandardResponse(BaseModel):
    """Modello di risposta per l'endpoint /full-gold-standard, che restituisce l'intero Gold Standard di un dominio."""
    gold_standard: List[GoldStandardData]

class GoldStandardUrlsResponse(BaseModel):
    """Modello di risposta per l'endpoint /gold_standard_urls."""
    gold_standard_urls: List[str]


# --- MODELLI PER IL PARSING ---

class ParseRequest(BaseModel):
    """Modello di input per l'esecuzione del parsing offline (senza richeste di rete)"""
    url: str
    html_text: str 

class ParseUrlRequest(BaseModel):
    url: str
    local: Optional[bool] = False

# --- MODELLI PER LA VALUTAZIONE (Metriche e LLM)

class EvaluateRequest(BaseModel):
    """Modello di input per l'endpoint /evaluate, per la richiesta di valutazione di un singolo documento."""
    parsed_text: str
    gold_text: str
    
class TokenLevelEval(BaseModel):
    """Modello contenente le metriche di valutazione calcolate a livello di token."""
    precision: float
    recall: float
    f1: float

class EvaluateResponse(BaseModel):
    """Modello di risposta standardizzato, per gli endpoint di valutazione (/evaluate e /full_gs_eval)."""
    token_level_eval: TokenLevelEval
    x_eval: Dict = {} # Placeholder estensibile per eventuali metriche aggiuntive future

class EvaluateJudgeResponse(BaseModel):
    """Modello di risposta per la valutazione qualitativa tramite LLM."""
    model_name: str
    judge_score: int
    judge_feedback: str
    altre_info: Dict = {}

class FullGsEvalResponse(BaseModel):
    """Modello di risposta per la valutazione aggregata (Metriche + LLM)."""
    token_level_eval: TokenLevelEval
    judge_score: float
    x_eval: Dict = {}


# --- MODELLI PER IL DATABASE (DML E DDL) ---

class AddWebResourceRequest(BaseModel):
    """Modello di input per l'aggiunta di una risorsa web al DB."""
    url: str
    html_text: str

class AddGoldStandardRequest(BaseModel):
    """Modello di input per l'aggiunta di un Gold Standard al DB."""
    url: str
    gold_text: str

class DeleteRequest(BaseModel):
    """Modello di input per la cancellazione di record dal DB."""
    url: str

class StatusResponse(BaseModel):
    """Modello di risposta per le operazioni di modifica DB (INSERT/DELETE)."""
    status: str

# --- MODELLI DI MONITORAGGIO E STATISTICHE

class SystemStatusResponse(BaseModel):
    """Modello di risposta per l'endpoint /status (Healt Check)."""
    backend: str
    database: str
    ollama: str

# class DbStatsResponse(BaseModel):
#     """Modello di formattazione per le statistiche aggregate del database."""
#     stats: Dict[str, Any]

# class DbSchemasResponse(BaseModel):
#     """Modello di formattazione per la struttura tabellare del database."""
#     schema_info: Dict[str, Any]


# NOTA: Per /db_stats e /db_schema usiamo direttamente Dict[str, Any] nel server.py 
# per rispettare esattamente la struttura JSON richiesta dal grader del professore.