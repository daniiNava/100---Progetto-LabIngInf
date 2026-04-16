from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates 
from fastapi.responses import HTMLResponse
import requests 
import os

app = FastAPI(title="Minerva Web UI")
templates = Jinja2Templates(directory="templates")

# URL base dell'API

API_BASE_URL = "http://backend:8003" 

def get_gs_urls():
    """Funzione di supporto per recuperare gli URL del Gold Standard."""
    gs_urls = []
    try:
        response = requests.get(f"{API_BASE_URL}/domains")
        if response.status_code == 200:
            lista_domini = response.json().get("domains", [])
            for dominio in lista_domini:
                res_gs = requests.get(f"{API_BASE_URL}/full_gold_standard", params={"domain": dominio})
                if res_gs.status_code == 200:
                    new = res_gs.json().get("gold_standard", [])
                    for i in new: 
                        gs_urls.append(i["url"])
    except requests.RequestException as e:
        print("Errore nella chiamata API per i domini:", e)
    return gs_urls


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Chiamiamo la funzione di supporto
    gs_urls = get_gs_urls()
    return templates.TemplateResponse("file.html", {"request": request, "gs_urls": gs_urls})


@app.post("/", response_class=HTMLResponse)
async def analyze(request: Request, url: str = Form(...)):
    results = {}
    evaluation = None
    gold_data = None 

    try: 
        # Richiedo il parsing al backend 
        richiesta_parser = requests.get(f"{API_BASE_URL}/parse", params={"url": url})
        
        if richiesta_parser.status_code == 200:
            
            results = richiesta_parser.json()  
            
            richiesta_gs = requests.get(f"{API_BASE_URL}/gold_standard", params={"url": url})
            if richiesta_gs.status_code == 200:
                gold_data = richiesta_gs.json()
                
                eval_payload = {
                    "parsed_text": results.get("parsed_text", ""), 
                    "gold_text": gold_data.get("gold_text", "")
                }
                
                eval_res = requests.post(f"{API_BASE_URL}/evaluate", json=eval_payload)
                if eval_res.status_code == 200:
                    evaluation = eval_res.json()
                    
    except requests.RequestException as e:
        print("Errore durante l'analisi:", e)
    
    return templates.TemplateResponse("file.html", {
        "request": request,
        "url": url,
        "results": results,      
        "gold_data": gold_data,  
        "evaluation": evaluation,
        "gs_urls": get_gs_urls() 
    })