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
    precision = 0
    recall = 0
    f1 = 0
    len_token_estratti = len(tokens_estratti)
    len_token_gs = len(tokens_gs)
    if len_token_estratti != 0 and len_token_gs != 0:
        for i in range(len_token_estratti):
            token = tokens_estratti[0]
            if token in tokens_gs:
                tokens_gs.remove(token) 
                n_correct_words += 1
            else: 
                print(f"{tokens_estratti[0]} {i}")
            tokens_estratti.remove(token)
        precision = n_correct_words/len_token_estratti
        recall = n_correct_words/len_token_gs
        f1 = 2 * precision * recall / (precision + recall)
    return{
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }






