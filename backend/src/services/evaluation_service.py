# Modulo che contiene l'algoritmo di calcolo delle metriche e la lettura dei file JSON del gold standard.
import re
from typing import Set, Dict

def _tokenize(text: str) -> Set[str]:
    """Tokenizzazione e normalizzazione del testo: rimozione di punteggiatura, conversione a minuscolo e split."""
    if not text:
        return set()
    clean_text = re.sub(r'[*#_]|\[.*?\]\(.*?\)', '', text)
    return set(re.findall(r'\b\w+\b', clean_text.lower()))

def calculate_metrics(parsed_text: str, gold_text:str) -> Dict[str, float]:
    """Calcola Precision, Recall e F1-score a livello di token"""
    token_estratti = _tokenize(parsed_text)
    token_gs = _tokenize(gold_text)

    intersezione = token_estratti.intersection(token_gs)
    len_int = len(intersezione)
    len_est = len(token_estratti)
    len_gs = len(token_gs)

    precision = (len_int / len_est) if len_est > 0 else 0.0
    recall = (len_int / len_gs) if len_gs > 0 else 0.0

    f1_score = 0.0
    if(precision + recall) > 0:
        f1_score = 2 * (precision*recall) / (precision + recall)

    return{
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1_score, 4)
    }
