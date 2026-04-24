import re
from typing import Dict

def _tokenize(text: str) -> set[str]:
    """
    Tokenizzazione a prova di Grader:
    1. Salva il testo dei link ed elimina gli URL
    2. Trasforma TUTTA la punteggiatura e il Markdown in spazi
    """
    if not text:
        return set()
    
    text = str(text)
    
    # 1. Rimuove gli URL dai link Markdown, tenendo SOLO il testo
    # Es: [Minerva](https://...) diventa -> Minerva
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 2. Rimuove eventuali URL "nudi" rimasti
    text = re.sub(r'http\S+', '', text)
    
    # 3. IL SEGRETO: \W+ sostituisce TUTTO ciò che non è una lettera o un numero con uno spazio.
    # Questo elimina in un colpo solo virgole, punti, asterischi, cancelletti, ecc.
    text = re.sub(r'\W+', ' ', text)
    text = re.sub(r"_", "", text)
    # 4. Lowercase, split per spazio e conversione in SET
    tokens = text.lower().split()
    
    return set(tokens)

def calculate_metrics(parsed_text: str, gold_text: str) -> Dict[str, float]:
    tokens_estratti = _tokenize(parsed_text)
    tokens_gs = _tokenize(gold_text)
    
    # Intersezione standard tra insiemi
    intersezione = tokens_estratti.intersection(tokens_gs)
    n_correct_words = len(intersezione)
    
    len_est = len(tokens_estratti)
    len_gs = len(tokens_gs)
    
    # Prevenzione divisione per zero
    precision = (n_correct_words / len_est) if len_est > 0 else 0.0
    recall = (n_correct_words / len_gs) if len_gs > 0 else 0.0
    
    f1 = 0.0
    if (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }