# Modulo che fa da punto di ingresso dell'applicazione FastApi.

from pydantic import BaseModel
from typing import List, Dict

# Modello per l'output di /parse e per le singole entry del GS
class DocumentData(BaseModel):
    url: str
    domain: str
    title: str
    html_text: str
    parsed_text: str

class GoldStandardData(BaseModel):
    url: str
    domain: str
    title: str
    html_text: str
    gold_text: str

class DomainsResponse(BaseModel):
    domains: List[str]

class FullGoldStandardResponse(BaseModel):
    gold_standard: List[GoldStandardData]

# Modelli per /evalueate
class EvaluateRequest(BaseModel):
    parsed_text: str
    gold_text: str
    
class TokenLevelEval(BaseModel):
    precision: float
    recall: float
    f1: float

class EvaluateResponse(BaseModel):
    token_level_eval: TokenLevelEval
    x_eval: Dict = {} # Placeholder per eventuali metriche extra

class ParseRequest(BaseModel):
    url: str
    html_text: str 