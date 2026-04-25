"""
Modulo di servizio per il caoclolo dellem mtriche di valitazione NLP.
Implementa algoritmi di normalizzazione testuale e calcola metriche standard
(Precision Recall F1-Score) e metriche avanzate (Levenshtein Distance, Cosine Similarity).
"""

import re
import math
from collections import Counter
from typing import Dict

def _tokenize(text: str) -> set[str]:
    """
    Pipeline di tokenizzazione e normalizzazione del testo.
    Estrae il testo utile dai link Markdown e rimuove la punteggiatura tramite regex.
    """
    if not text:
        return set()
    
    text = str(text)
    
    # 1. Estrazione del testo visibile dai link Markdown (es. [Testo](URL) -> "Testo")
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 2. Rimozione di eventuali URL residui nel testo
    text = re.sub(r'http\S+', '', text)
    
    # 3. Sostituzione di tutti i caratteri non alfanumerici (punteggiautea, markdown) con spazi
    text = re.sub(r'\W+', ' ', text)
    text = re.sub(r"_", "", text)
    
    # Conversione del testo in minuscolo, split per parole e cast a Set per l'intersezione
    tokens = text.lower().split()
    return set(tokens)

def calculate_metrics(parsed_text: str, gold_text: str) -> Dict[str, float]:
    """
    Calcola le metriche di valutazione confrontando i token estratti con il Gold Standard.

    Returns: 
        Dict[str, float]: Dizionario contenente Precision, Recall e F1-Score arrotondati a 4 decimali.
    """
    tokens_estratti = _tokenize(parsed_text)
    tokens_gs = _tokenize(gold_text)
    
    # Calcolo dei True Positives tramite intersezione standard tra insiemi
    intersezione = tokens_estratti.intersection(tokens_gs)
    n_correct_words = len(intersezione)
    
    len_est = len(tokens_estratti)
    len_gs = len(tokens_gs)
    
    # Calcolo metriche con prevenzione della divisione per zero
    precision = (n_correct_words / len_est) if len_est > 0 else 0.0
    recall = (n_correct_words / len_gs) if len_gs > 0 else 0.0
    
    f1 = 0.0
    if (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        
    }

def calculate_levenshtein_distance(parsed_text: str, gold_text: str) -> int:
    """
    Calcola la distanza di Leveshtein (Edit Distance) a livello di token.
    Indica il numero minimo di operazioni (inserimenti, cancellazioni, sostituzioni) 
    necessarie per trasformare il testo estratto nel Gold Standard.
    Implementazione basata su Programmazione Dinamica (Dynamic Programming).
    """

    tokens_estratti=parsed_text.lower().split()
    tokens_gs=gold_text.lower().split()

    len_est=len(tokens_estratti)
    len_gs=len(tokens_gs)

    # Inizializzazione della matrice per la Programmazione Dinamica
    dp=[[0 for _ in range(len_gs+1)] for _ in range(len_est+1)]

    for i in range(len_est+1):
        dp[i][0]=i 
    for j in range(len_gs+1):
        dp[0][j]=j 

    # Popolamento della matrice
    for i in range(1, len_est+1):
        for j in range(1, len_gs+1):
            if tokens_estratti[i-1]==tokens_gs[j-1]:
                cost=0
            else:
                cost=1
            dp[i][j]= min(
                dp[i-1][j]+1,
                dp[i][j-1]+1,
                dp[i-1][j-1]+cost 

            )
    return dp[len_est][len_gs]

def calculate_cosine_similarity(parsed_text: str, gold_text: str) -> float:
    """
    Calcola la Cosine Similarity tra i due testi basandosi su un approccio Bag-of-Words.
    Valuta l'importanza delle parole: penalizza maggiormente gli errori su parole
    frequenti rispetto a parole rare. 
    """
    
    tokens_estratti = re.findall(r'\b\w+\b', str(parsed_text).lower())
    tokens_gs = re.findall(r'\b\w+\b', str(gold_text).lower())

    # Creazione dei vettori di frequenza (Term Frequency)
    vec_est=Counter(tokens_estratti)
    vec_gs=Counter(tokens_gs)
    
    # Costruzione del vocabolario unificato  
    words=set(vec_est.keys()).union(set(vec_gs.keys()))
    
    # Calcolo del prodotto scalare
    dot_product= sum(vec_est.get(word,0)*vec_gs.get(word,0) for word in words)

    # Calcolo delle magnitudini (Norma Euclidea)
    mag_est=math.sqrt(sum(val**2 for val in vec_est.values()))
    mag_gs=math.sqrt(sum(val**2 for val in vec_gs.values()))

    if mag_est==0 or mag_gs==0:
        return 0.0 
    
    similarity=dot_product/(mag_est*mag_gs)
    return round(similarity,4)

