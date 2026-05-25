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
#templates=Jinja2Templates("templates")


current_dir = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_path)




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
            
            # 2. Recupero degli URL per ciascun dominio interrogando l'endpoint /gold_standard_urls
            for dominio in lista_domini:
                res_gs=requests.get(f"{API_BASE_URL}/gold_standard_urls", params={"domain":dominio}) 
                if res_gs.status_code==200:
                    urls=res_gs.json().get("gold_standard_urls", []) 
                    gs_urls.extend(urls)
    except requests.RequestException as e:
        # Gestione silente degli errori di rete per non bloccare il rendering della UI
        print("errore nella chiamata API per i domini:", e)
    
    return gs_urls

def get_supported_domains(): 
    """recuperiamo i domini per l'homepage"""
    try: 
        res=requests.get(f"{API_BASE_URL}/domains")
        if res.status_code==200:
            return res.json().get("domains", [])
    except: 
        pass
    return []

def check_status(): 
    """controlliamo lo stato dei servizi"""
    status={"backend": False, "db": False, "ollama": False}
    try: 
        res=requests.get(f"{API_BASE_URL}/status", timeout=2)
        if res.status_code==200:
            data=res.json()
            status["backend"]= data.get("backend")=="ok"
            status["db"]= data.get("database")=="ok"
            status["ollama"]= data.get("ollama")=="ok"
    except: 
        pass
    return status
   

@app.get("/", response_class=HTMLResponse)
async def home(request:Request):
    """
    Endpoint per il rendering della homepage.
    Inietta nel template Jinja2 la lista degli URL presenti nei Gold Standard, per popolare il menu a tendina.
    """
    
    return templates.TemplateResponse( #fondiamo il codice python con il codice HTML 
        request=request,
        name="index.html",
        context={
            "domini": get_supported_domains(),
            "status": check_status(),
            "studenti": [
                {"nome": "Daniele Navangioni", "matricola": "2217934"},
                {"nome": "Vittorio Rizzo", "matricola": "2138427"},
                {"nome": "Cosimo Raimondo", "matricola": "2109148"}
            ]
        }
    )

@app.get("/evaluation", response_class=HTMLResponse)
async def evaluation_get(request: Request):
    """pagina di valutazione"""
    return templates.TemplateResponse(
        request=request,
        name="evaluation.html",
        context={"gs_urls": get_gs_urls()}
    )



@app.post("/evaluation", response_class=HTMLResponse)
async def evaluation_post(request: Request, url: str = Form(...), use_local: bool= Form(False)):
    """PAGINA VALUTAZIONE (POST): Esegue l'analisi (La tua logica originale!)"""
    results = {}
    evaluation = None
    judge_data=None
    gold_data = None 
    error_msg = None 

    try:
        parse_payload= {"url": url, "local": use_local}
        richiesta_parser = requests.post(f"{API_BASE_URL}/parse", json=parse_payload)
        if richiesta_parser.status_code == 200:
            results = richiesta_parser.json()
            
            richiesta_gs = requests.get(f"{API_BASE_URL}/gold_standard", params={"url":url})
            if richiesta_gs.status_code == 200:
                gold_data = richiesta_gs.json()
                eval_payload = {
                    "parsed_text": results.get("parsed_text",""),
                    "gold_text": gold_data.get("gold_text","")
                }

                eval_res = requests.post(f"{API_BASE_URL}/evaluate", json=eval_payload)
                if eval_res.status_code == 200:
                    evaluation = eval_res.json()
                
                #valutazione LLM
                judge_res=requests.post(f"{API_BASE_URL}/evaluate_judge", json=eval_payload)
                if judge_res.status_code==200:
                    judge_data=judge_res.json()
        else:
            dettaglio_errore = richiesta_parser.json().get("detail", "Errore di parsing sconosciuto")
            error_msg = f"Errore dal server: {dettaglio_errore}"
    except requests.RequestException as e:
        error_msg = f"Errore di connessione al backend: {e}"

    return templates.TemplateResponse(
        request=request,
        name="evaluation.html",
        context={
            "url": url,
            "results": results,
            "gold_data": gold_data,
            "evaluation": evaluation,
            "judge_data": judge_data,
            "error_msg": error_msg, 
            "gs_urls": get_gs_urls()
        } 
    )

@app.get("/gs_manager", response_class=HTMLResponse)
async def gs_manager_page( request: Request): 
    """pagina per la gestione del gold standard """
    return templates.TemplateResponse(
        request=request, 
        name="gs_manager.html", 
        context={
            "domini": get_supported_domains(),
            "gs_urls": get_gs_urls(),
            "message": None,
            "error": None
        })

@app.post("/gs_manager/add", response_class=HTMLResponse) 
async def gs_manager_add(request: Request, url: str=Form(...), html_text: str=Form(...), gold_text: str= Form(...)):
    message=None 
    error=None 
    try: 
        res_web=requests.post(f"{API_BASE_URL}/add_web_resource", json= {"url": url, "html_text": html_text})
        if res_web.status_code==200:
            res_gs=requests.post(f"{API_BASE_URL}/add_gold_standard", json= {"url": url, "gold_text": gold_text})
            if res_gs.status_code==200:
                message="Risorsa e gold standard raggiunti con successo"
            else: 
                error="Errore durante l'aggiunta del gold standard"
        else: 
            error= "Errore durante l'aggiunta della risorsa web"
    except Exception as e: 
        error=f"Errore di connessione al backend: {e}"
    return templates.TemplateResponse(
        request=request,
        name="gs_manager.html",
        context={
            "domini": get_supported_domains(),
            "gs_urls": get_gs_urls(),
            "message": message, 
            "error": error
        }
    )

@app.post("/gs_manager/delete", response_class=HTMLResponse) 
async def gs_manager_delete(request: Request, url: str=Form(...)):
    """gestiamo la cancellazione di una risorsa dal database"""
    message=None
    error=None 
    try: 
        res=requests.delete(f"{API_BASE_URL}/web_resource", json={"url": url})
        if res.status_code==200:
            message= f"Risorsa {url} eliminata con successo"
        else: 
            error="Errore durante l'eliminazione della risorsa"
    except Exception as e: 
        error=f"Errore di connessione al backend {e}"
    
    return templates.TemplateResponse(
        request=request,
        name="gs_manager.html",
        context={
            "domini": get_supported_domains(),
            "gs_urls": get_gs_urls(),
            "message": message, 
            "error": error
        }
    )
    

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    stats_data={}
    error_msg=None 
    try: 
        res=requests.get(f"{API_BASE_URL}/db_stats")
        if res.status_code==200: 
            stats_data=res.json() 
        else: 
            error_msg="Impossibile recuperare le statistiche dal server"
    except Exception as e:
        error_msg=f"Errore di connessione al backend: {e}"

    return templates.TemplateResponse(
        request=request, 
        name="stats.html", 
        context={
            "stats": stats_data, 
            "error_msg": error_msg
        }) 