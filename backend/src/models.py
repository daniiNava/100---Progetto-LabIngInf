"""
Modulo per la definizione degli schemi dei dati tramite Pydantic.
Garantisce la validazione statica e a runtime degli input/output delle API REST,
oltre a generare automaticamente la documentazione Swagger UI.
"""

from pydantic import BaseModel
from typing import List, Dict

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

class ParseRequest(BaseModel):
    """Modello di input per l'esecuzione del parsing offline (senza richeste di rete)"""
    url: str
    html_text: str 