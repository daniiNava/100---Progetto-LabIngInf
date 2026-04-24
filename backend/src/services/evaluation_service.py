import re
import math
from collections import Counter
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
        "f1": round(f1, 4),
        
    }

def calculate_levenshtein_distance(parsed_text: str, gold_text: str) -> int:
    #calcola quante operazioni (inserimenti, cancellazioni, sostituzioni) servono per trasformare il testo estratto dal parser nel testo perfetto del gs
    #Interessante perche-> ci dice esattamente quanto costa correggere un errore 
    #calcola la distanza di levenshtein a livello di parole.
    #indica il numero minimo di operazioni necassarie per trasformare i token estratti nei token del gs

    tokens_estratti=parsed_text.lower().split()
    tokens_gs=gold_text.lower().split()

    len_est=len(tokens_estratti)
    len_gs=len(tokens_gs)

    #dynamic programming
    dp=[[0 for _ in range(len_gs+1)] for _ in range(len_est+1)]

    for i in range(len_est+1):
        dp[i][0]=i 
    for j in range(len_gs+1):
        dp[0][j]=j 

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
    #valuta l'importanza delle parole se il parser sbaglia una parola corta la penalita è breve 
    #mentre se sbaglia parole lunghela penalita è molto alta, metrica alla base dei motori di ricerca per capire se i documenti parlano dello stesso argomento 
    tokens_estratti = re.findall(r'\b\w+\b', str(parsed_text).lower())
    tokens_gs = re.findall(r'\b\w+\b', str(gold_text).lower())

    vec_est=Counter(tokens_estratti)
    vec_gs=Counter(tokens_gs)
    #costruiamo il nostro vocabolario, trovando tutte le parole uniche 
    words=set(vec_est.keys()).union(set(vec_gs.keys()))
    #calcolo del prodotto scalare
    dot_product= sum(vec_est.get(word,0)*vec_gs.get(word,0) for word in words)

    #calcolo magnitudini (norma euclidea)
    mag_est=math.sqrt(sum(val**2 for val in vec_est.values()))
    mag_gs=math.sqrt(sum(val**2 for val in vec_gs.values()))

    if mag_est==0 or mag_gs==0:
        return 0.0 
    similarity=dot_product/(mag_est*mag_gs)
    return round(similarity,4)

