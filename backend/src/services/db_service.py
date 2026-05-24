"""
Modulo di servizio per l'interazione con il database MariaDB.
Gestisce la connessione, la creazione dello schema e le operazioni CRUD.
"""
import mariadb
import os
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Parametri di connessione presi dalle variabili d'ambiente (impostate nel docker-compose)
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "minerva_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "minerva_pass")
DB_NAME = os.getenv("DB_NAME", "minerva_db")

def get_connection():
    """Crea e restituisce una connessione al database MariaDB."""
    try:
        conn = mariadb.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mariadb.Error as e:
        print(f"Errore di connessione a MariaDB: {e}")
        return None

def init_db():
    """
    Inizializza lo schema del database creando le tabelle obbligatorie
    se non esistono già.
    """
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    
    # Creazione tabella web_resources
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS web_resources (
            url VARCHAR(2048) PRIMARY KEY,
            domain VARCHAR(255) NOT NULL,
            title VARCHAR(2048),
            html_text LONGTEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Creazione tabella gold_standard con Foreign Key e ON DELETE CASCADE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_standard (
            url VARCHAR(2048) PRIMARY KEY,
            gold_text LONGTEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (url) REFERENCES web_resources(url) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Database inizializzato con successo.")

# ==========================================
# FUNZIONI DI LETTURA (SELECT)
# ==========================================

def get_html_from_db(url: str) -> str:
    """Recupera l'HTML grezzo di una risorsa web dal DB."""
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor()
    
    cursor.execute("SELECT html_text FROM web_resources WHERE url = ?", (url,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return result[0] if result else None

def get_gs_by_url_from_db(url: str) -> dict:
    """Recupera una singola entry del Gold Standard unendo le due tabelle."""
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True) # Restituisce i risultati come dizionari
    
    query = """
        SELECT w.url, w.domain, w.title, w.html_text, g.gold_text
        FROM web_resources w
        JOIN gold_standard g ON w.url = g.url
        WHERE w.url = ?
    """
    cursor.execute(query, (url,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return result

def get_gs_urls_from_db(domain: str) -> list:
    """Restituisce la lista degli URL del GS per un dominio specifico."""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    
    query = """
        SELECT w.url 
        FROM web_resources w
        JOIN gold_standard g ON w.url = g.url
        WHERE w.domain = ?
    """
    cursor.execute(query, (domain,))
    results = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return results

def get_full_gs_from_db(domain: str) -> list:
    """Restituisce tutte le entry del GS per un dominio specifico."""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT w.url, w.domain, w.title, w.html_text, g.gold_text
        FROM web_resources w
        JOIN gold_standard g ON w.url = g.url
        WHERE w.domain = ?
    """
    cursor.execute(query, (domain,))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return results

# ==========================================
# FUNZIONI DI SCRITTURA (INSERT / DELETE)
# ==========================================

def insert_web_resource(url: str, html_text: str, title: str = "Titolo non disponibile") -> bool:
    """Inserisce una nuova risorsa web nel DB."""
    domain = urlparse(url).netloc
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO web_resources (url, domain, title, html_text) VALUES (?, ?, ?, ?)",
            (url, domain, title, html_text)
        )
        conn.commit()
        success = True
    except mariadb.Error as e:
        print(f"Errore inserimento web_resource: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def insert_gold_standard(url: str, gold_text: str) -> bool:
    """Inserisce un nuovo Gold Standard nel DB."""
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO gold_standard (url, gold_text) VALUES (?, ?)",
            (url, gold_text)
        )
        conn.commit()
        success = True
    except mariadb.Error as e:
        print(f"Errore inserimento gold_standard: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def delete_web_resource(url: str) -> bool:
    """Cancella una risorsa web (e a cascata il suo GS)."""
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM web_resources WHERE url = ?", (url,))
        conn.commit()
        success = cursor.rowcount > 0
    except mariadb.Error as e:
        print(f"Errore cancellazione web_resource: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def delete_gold_standard(url: str) -> bool:
    """Cancella solo il Gold Standard."""
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM gold_standard WHERE url = ?", (url,))
        conn.commit()
        success = cursor.rowcount > 0
    except mariadb.Error as e:
        print(f"Errore cancellazione gold_standard: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

# ==========================================
# FUNZIONI DI STATO E SCHEMA
# ==========================================

def check_db_status() -> str:
    """Verifica se il DB è raggiungibile."""
    conn = get_connection()
    if conn:
        conn.close()
        return "ok"
    return "error"

def get_db_schema() -> dict:
    """Restituisce lo schema richiesto dalle slide."""
    return {
        "web_resources": {
            "url": "varchar(2048), PK",
            "domain": "varchar(255)",
            "title": "varchar(2048)",
            "html_text": "longtext",
            "created_at": "datetime"
        },
        "gold_standard": {
            "url": "varchar(2048), PK, FK(web_resources.url)",
            "gold_text": "longtext",
            "created_at": "datetime"
        }
    }

def get_db_stats() -> dict:
    """Calcola le statistiche di base (quanti record per dominio)."""
    conn = get_connection()
    if not conn: return {}
    cursor = conn.cursor(dictionary=True)
    
    stats = {"web_resources": {}, "gold_standard": {}}
    
    # Conteggio web_resources per dominio
    cursor.execute("SELECT domain, COUNT(*) as count FROM web_resources GROUP BY domain")
    for row in cursor.fetchall():
        stats["web_resources"][row["domain"]] = row["count"]
        
    # Conteggio gold_standard per dominio
    cursor.execute("""
        SELECT w.domain, COUNT(*) as count 
        FROM gold_standard g 
        JOIN web_resources w ON g.url = w.url 
        GROUP BY w.domain
    """)
    for row in cursor.fetchall():
        stats["gold_standard"][row["domain"]] = row["count"]
        
    cursor.close()
    conn.close()
    return stats