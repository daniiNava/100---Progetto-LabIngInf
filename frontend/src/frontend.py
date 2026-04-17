from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates 
from fastapi.responses import HTMLResponse
import requests 
import os

app = FastAPI(title="Minerva Web UI")
templates = Jinja2Templates("templates")

# URL base dell'API (Lascialo così per testare in locale)
#API_BASE_URL = "http://127.0.0.1:8003"
#per testare con docker 
API_BASE_URL = os.getenv("BACKEND_URL","http://127.0.0.1:8003")



def get_gs_urls():
    """Funzione di supporto per recuperare gli URL del Gold Standard."""
    gs_urls = []
    try:
        response = requests.get(f"{API_BASE_URL}/domains") #otteniamo la lista dei domini supportati
        if response.status_code == 200:
            lista_domini = response.json().get("domains", []) #prendiamo la risposta del backend (che arriva in formato json) e la convertiamo in un dizionario python ed estraiamo il valore associato alla chiave "domains" 
            for dominio in lista_domini: 
                res_gs = requests.get(f"{API_BASE_URL}/full_gold_standard", params={"domain": dominio}) #per ogni dominio, chiamiamo l'API /full_gold_standard per ottenere tutti i dati salvati, ma per evitare bloccchi di dati troppo grandi, richiediamo i dati solo per un dominio specificato params={"domain": dominio}
                if res_gs.status_code == 200:
                    new = res_gs.json().get("gold_standard", [])
                    for i in new: #prendiamo ogni pacchetto di dati i 
                        gs_urls.append(i["url"]) #apriamo il pacchetto e guardiamo solamente il valore associato all'etichetta "url", e lo appendiamo a gs_urls
    except requests.RequestException as e:
        print("Errore nella chiamata API per i domini:", e)
    return gs_urls

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    gs_urls = get_gs_urls()
    return templates.TemplateResponse( #fondiamo il codice python con il codice HTML 
        request=request, 
        name="file.html", 
        context={"gs_urls": gs_urls} #context è un dizionario
        #in HTML seguendo la sintassi di Jinja, avremmo un qualcosa del tipo
        # <select name="url">
        #{% for url in gs_urls %}
        #    <option value="{{ url }}">{{ url }}</option>
        #{% endfor %}
        #</select>
    )

@app.post("/", response_class=HTMLResponse)
async def analyze(request: Request, url: str = Form(...)): #url: .. indica che l'utente sta inviando un modulo HTML(form)
    #i ... indicano che è un campo obbligatorio 
    results = {}
    evaluation = None
    gold_data = None 
    error_msg = None

    try: 
        # Richiedo il parsing al backend, per un determinato url
        richiesta_parser = requests.get(f"{API_BASE_URL}/parse", params={"url": url})
        
        if richiesta_parser.status_code == 200:
            results = richiesta_parser.json()  
            #il parsing è andato bene, richiediamo il gold_standard per quel determinato url
            richiesta_gs = requests.get(f"{API_BASE_URL}/gold_standard", params={"url": url})
            if richiesta_gs.status_code == 200:
                gold_data = richiesta_gs.json()
                
                eval_payload = {
                    "parsed_text": results.get("parsed_text", ""), 
                    "gold_text": gold_data.get("gold_text", "")
                } #trovato il gs e il parsed text, li mettiamo in un pacchetto json (eval_payload) 
                
                eval_res = requests.post(f"{API_BASE_URL}/evaluate", json=eval_payload) #richiediamo la valutazione per farli valutare 
                if eval_res.status_code == 200:
                    evaluation = eval_res.json()
            else:
                error_msg= "URL passato con successo, ma non è presente nel gold standard "
        else:
            # Estrazione dinamica dell'errore restituito da FastAPI
            dettaglio_errore = richiesta_parser.json().get("detail", "Errore di parsing sconosciuto")
            error_msg = f"Errore dal server: {dettaglio_errore}"
                    
    except requests.RequestException as e:
        error_msg = f"Errore di connessione al backend: {e}"
    
    
    return templates.TemplateResponse(
        request=request, 
        name="file.html", 
        context={
            "request": request,
            "url": url,
            "results": results,      
            "gold_data": gold_data,  
            "evaluation": evaluation,
            "error_msg": error_msg, #dentro il file html ci sarà una logica del tipo {% if error_msg% }
            "gs_urls": get_gs_urls() #lista dei domini supportati; Quando l'utente clicca "Analizza", la pagina web si ricarica per mostrare i risultati. Ricaricandosi, perderebbe il menu a tendina con i link. Chiamando di nuovo questa funzione, ci assicuriamo che il menu a tendina venga ridisegnato correttamente anche nella pagina dei risultati.
        } #imballiamo tutto cio che è stato fatto, tutto ciò che è nel context diventa 
        #una variabile che il file.html usa per disegnare la pagina
    )

#if __name__ == "__main__":
    import uvicorn 
    uvicorn.run("frontend:app", host="127.0.0.1",port=8004, reload=True)

