# Modulo che contiene l'algoritmo di calcolo delle metriche e la lettura dei file JSON del gold standard.
import re
from typing import Dict
from markdownCleaner import MarkdownCleaner


def _tokenize(text: str) -> list[str]:
    """Tokenizzazione e normalizzazione del testo: rimozione di punteggiatura, conversione a minuscolo e split."""
    clean_text = re.sub(r"[,.:|]|---|```", "", text).lower()
    return clean_text.split()

def calculate_metrics(parsed_text : str, gold_text : str) -> Dict[str, float]:
    tokens_estratti = _tokenize(MarkdownCleaner.clean(parsed_text))
    tokens_gs = _tokenize(gold_text)
    n_correct_words = 0
    for i in range(min(len(tokens_estratti),len(tokens_gs))):
        if tokens_estratti[i] == tokens_gs[i]: n_correct_words += 1
        else: print(f"{tokens_estratti[i]} {tokens_gs[i]} {i}")
    precision = n_correct_words/len(tokens_estratti)
    recall = n_correct_words/len(tokens_gs)
    f1 = 2 * precision * recall / (precision + recall)
    return{
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }






