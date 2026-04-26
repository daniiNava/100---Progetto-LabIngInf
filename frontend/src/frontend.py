"""
Modulo Frontend dell'applicazione Minerva.
Implementa un'archittettura BFF (Backend For Frontend) utilizzando FastAPI e Jinja2.
Il modulo non contiene logica di business, ma si occupa esclusivamente di gestire
le chiamate REST verso il backend e di renderizzare dinamicamente l'interfaccia utente.
"""
from fastapi import FastAPI, Request, Form 
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests 
import os

app= FastAPI(title="Minerva Web UI")

# Configurazione del motore di templating Jinja2
templates=Jinja2Templates("templates")

# Risoluzione dinamica dell'URL del backend (utile per l'orchestrazione con Docker)
API_BASE_URL=os.getenv("BACKEND_URL", "http://127.0.0.1:8003")

def get_gs_urls():
    """
    Recupera dinamicamente la lista di tutti gli URL presenti nei Gold Standard.
    Interroga l'endpoint /domains e, per ciascun dominio, l'endpoint /full_gold_standard. 
    
    Returns:
        list: Lista di URL formattati come stringhe
    """
    gs_urls=[]
    try:
        # 1. Recupero dei domini supportati dal backend
        response=requests.get(f"{API_BASE_URL}/domains") 
        if response.status_code==200: 
            lista_domini=response.json().get("domains", []) #prendiamo la risposta del backend (che arriva in formato json) e la convertiamo in un dizionario python ed estraiamo il valore associato alla chiave "domains"
            
            # 2. Recupero degli URL per ciascun dominio interrogando l'endpoint /full_gold_standard
            for dominio in lista_domini:
                res_gs=requests.get(f"{API_BASE_URL}/full_gold_standard", params={"domain":dominio}) 
                if res_gs.status_code==200:
                    new=res_gs.json().get("gold_standard", []) 
                    for i in new:
                        gs_urls.append(i["url"]) #apriamo il pacchetto e guardiamo solamente il valore associato all'etichetta "url", e lo appendiamo a gs_urls
    
    except requests.RequestException as e:
        # Gestione silente degli errori di rete per non bloccare il rendering della UI
        print("errore nella chiamata API per i domini:", e)
    
    return gs_urls


@app.get("/", response_class=HTMLResponse)
async def home(request:Request):
    """
    Endpoint per il rendering della homepage.
    Inietta nel template Jinja2 la lista degli URL presenti nei Gold Standard, per popolare il menu a tendina.
    """
    gs_urls=get_gs_urls()
    return templates.TemplateResponse( #fondiamo il codice python con il codice HTML 
        request=request,
        name="index.html",
        context={"gs_urls": gs_urls}
    )

@app.post("/", response_class=HTMLResponse)
async def analyze(request: Request, url: str=Form(...)):
    """
    Gestisce la sottomissione del form da parte dell'utente.
    Esegue in sequenza le chiamate REST al backend per:
        1. Ottenere il parsing del documento (endpoint /parse)
        2. Ottenere l'eventuale Gold Standard associato (endpoint /gold_standard)
        3. Richiedere il calcolo delle metriche di valutazione (endpoint /evaluate)
    """
    results={}
    evaluation=None
    gold_data=None 
    error_msg=None 

    try:
        # 1. Richiesta di parsing al backend
        richiesta_parser= requests.get(f"{API_BASE_URL}/parse", params={"url": url})
        
        if richiesta_parser.status_code==200:
            results=richiesta_parser.json()
            
            # 2. Richiesta del Gold Standard associato all'URL (se esistente)
            richiesta_gs=requests.get(f"{API_BASE_URL}/gold_standard", params={"url":url})
            if richiesta_gs.status_code==200:
                gold_data=richiesta_gs.json()

                # 3. Costruzione del payload e Richiesta del calcolo delle metriche di valutazione
                eval_payload={
                    "parsed_text": results.get("parsed_text",""),
                    "gold_text":gold_data.get("gold_text","")
                } #trovato il gs e il parsed text, li mettiamo in un pacchetto json (eval_payload)

                eval_res=requests.post(f"{API_BASE_URL}/evaluate", json=eval_payload)
                if eval_res.status_code==200:
                    evaluation=eval_res.json()
    
        else:
            # Propagazione degli errori generati dal backend (es. URL non valido, dominio non supportato)
            dettaglio_errore=richiesta_parser.json().get("detail", "Errore di parsing sconosciuto")
            error_msg=f"Errore dal server: {dettaglio_errore}"
    
    except requests.RequestException as e:
        error_msg=f"Errore di connessione al backend: {e}"

    # Rendering del tamplate con iniezione dei dati elaborati
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request":request,
            "url":url,
            "results": results,
            "gold_data": gold_data,
            "evaluation": evaluation,
            "error_msg": error_msg, 
            "gs_urls": get_gs_urls() # Ricarica gli URL per mantenere popolato il menu a tendina
        } 
    ) 