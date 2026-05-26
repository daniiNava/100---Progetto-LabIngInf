import re
import math
import requests
import json
import os
from collections import Counter
from typing import Dict

OLLAMA_URL = "http://ollama:11434"
MODEL_NAME = "llama3.2:3b"

def check_ollama_status() -> str:
    """Verifica se il server Ollama è raggiungibile."""
    try:
        res = requests.get(f"{OLLAMA_URL}/", timeout=2)
        return "ok" if res.status_code == 200 else "error"
    except requests.RequestException:
        return "error"

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

async def evaluate_with_llm(parsed_text: str, gold_text: str) -> dict:
    """
    Invia il testo al LLM e chiede una valutazione da 1 a 5.
    Implementa il troncamento del testo (autorizzato dalle specifiche) 
    per garantire tempi di esecuzione rapidi anche su CPU.
    """
    # TRONCAMENTO UFFICIALE: Limitiamo a 2500 caratteri (~500 parole)
    MAX_CHARS = 2500 
    
    short_parsed = parsed_text[:MAX_CHARS] + ("..." if len(parsed_text) > MAX_CHARS else "")
    short_gold = gold_text[:MAX_CHARS] + ("..." if len(gold_text) > MAX_CHARS else "")

    system_prompt = """
    Sei un giudice imparziale. Valuta la qualità del testo estratto (Parsed Text) confrontandolo con il riferimento (Gold Standard).
    Penalizza la presenza di menu, pubblicità o rumore.
    Rispondi ESCLUSIVAMENTE con un JSON valido: {"score": <da 1 a 5>, "feedback": "<motivazione>"}
    """

    # Passiamo i testi troncati al prompt
    user_prompt = f"Gold Standard (estratto):\n{short_gold}\n\nParsed Text (estratto):\n{short_parsed}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": "json", 
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 2048,     # Memoria standard, velocissima da processare
            "num_predict": 150   # Diciamo all'LLM di non scrivere poemi nel feedback, max 150 token
        }
    }

    try:
        # Timeout di sicurezza a 60 secondi
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
        response.raise_for_status()
        
        llm_response_text = response.json()["message"]["content"]
        
        try:
            result_data = json.loads(llm_response_text)
            score = max(1, min(5, int(result_data.get("score", 1))))
            feedback = str(result_data.get("feedback", "Nessun feedback fornito."))
            
            return {
                "model_name": MODEL_NAME,
                "judge_score": score,
                "judge_feedback": feedback
            }
            
        except (json.JSONDecodeError, ValueError):
            return {
                "model_name": MODEL_NAME,
                "judge_score": 1,
                "judge_feedback": "FALLBACK: Il modello non ha rispettato il formato JSON."
            }

    except requests.RequestException as e:
        return {
            "model_name": MODEL_NAME,
            "judge_score": 0,
            "judge_feedback": f"ERRORE DI RETE: Impossibile contattare il Judge LLM ({e})."
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

