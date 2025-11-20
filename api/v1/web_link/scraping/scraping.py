from __future__ import annotations
import os
import random
import re
import shutil
import stat
import sys
import tempfile
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import uuid

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from api.v1._shared.custom_schemas import HeadingsData, OpenGraphData, PageContent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# User Agents variados para anti-detecção
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

def _get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)

def _create_chrome_driver_headless() -> tuple[webdriver.Chrome, str, str]:
    import subprocess
    
    # LIMPEZA RADICAL: Matar todos os processos Chrome/ChromeDriver
    try:
        # Mata processos Chrome
        subprocess.run(["pkill", "-9", "-f", "chrome"], check=False, timeout=5)
        subprocess.run(["pkill", "-9", "-f", "chromedriver"], check=False, timeout=5)
        subprocess.run(["pkill", "-9", "-f", "google-chrome"], check=False, timeout=5)
        
        # Aguarda um pouco para garantir que os processos foram mortos
        time.sleep(2)
        
        # Limpa diretórios temporários órfãos
        import glob
        for pattern in ["/tmp/chrome*", "/tmp/selenium*", "/tmp/chrome_user_data*"]:
            for path in glob.glob(pattern):
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
                    
    except Exception:
        pass

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-domain-reliability")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--password-store=basic")
    chrome_options.add_argument("--use-mock-keychain")
    chrome_options.add_argument("--accept-language=pt-BR,pt;q=0.9,en;q=0.8")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.page_load_strategy = "none"

    # UA randômico
    chrome_options.add_argument(f"--user-agent={_get_random_user_agent()}")

    # SOLUÇÃO DEFINITIVA: Criar diretório único para cada instância
    import tempfile
    import uuid
    
    # Cria diretórios únicos para cada instância do Chrome
    unique_id = str(uuid.uuid4())[:8]
    user_data_dir = tempfile.mkdtemp(prefix=f"chrome_user_data_{unique_id}_")
    cache_dir = tempfile.mkdtemp(prefix=f"chrome_cache_{unique_id}_")
    
    # Usa diretórios únicos para evitar conflitos
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument(f"--disk-cache-dir={cache_dir}")
    chrome_options.add_argument(f"--homedir={user_data_dir}")
    
    # Configurações para evitar conflitos de sessão
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    # Evita disputa de porta - usa porta aleatória
    import random
    debug_port = random.randint(9222, 9999)
    chrome_options.add_argument(f"--remote-debugging-port={debug_port}")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)

    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR','pt','en']})")
    except Exception:
        pass

    return driver, user_data_dir, cache_dir

def _cleanup_temp_dirs(*paths: str, retries: int = 5, delay: float = 0.5):
    import shutil, time, subprocess
    
    for p in paths:
        if not p or not os.path.exists(p):
            continue
            
        # Remove locks específicos do Chrome
        lock_files = [
            "SingletonLock", "SingletonCookie", "SingletonSocket",
            "lockfile", "LOCK", "chrome_debug.log", "Default/Lock File",
            "Default/SingletonLock", "Default/SingletonCookie", "Default/SingletonSocket"
        ]
        
        for lock in lock_files:
            try:
                lock_path = os.path.join(p, lock)
                if os.path.exists(lock_path):
                    os.remove(lock_path)
            except Exception:
                pass
        
        # Força remoção de arquivos específicos do Chrome que podem estar bloqueados
        try:
            subprocess.run(["find", p, "-name", "*.lock", "-delete"], check=False, timeout=5)
            subprocess.run(["find", p, "-name", "Singleton*", "-delete"], check=False, timeout=5)
        except Exception:
            pass
        
        # Tenta remover o diretório com múltiplas tentativas
        for attempt in range(retries):
            try:
                if os.path.exists(p):
                    shutil.rmtree(p, ignore_errors=False)
                    break
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                    # Tenta matar processos que possam estar usando o diretório
                    try:
                        subprocess.run(["lsof", "+D", p], check=False, timeout=3)
                    except Exception:
                        pass
                else:
                    # Última tentativa: força remoção
                    try:
                        subprocess.run(["rm", "-rf", p], check=False, timeout=10)
                    except Exception:
                        pass

def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _extract_meta(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    def meta(name: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"name": name})
        return tag.get("content") if tag and tag.has_attr("content") else None

    def prop(property_name: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"property": property_name})
        return tag.get("content") if tag and tag.has_attr("content") else None

    metas = {
        "title": (soup.title.string if soup.title else None) or prop("og:title"),
        "description": meta("description") or prop("og:description"),
        "keywords": meta("keywords"),
        "og:type": prop("og:type"),
        "og:image": prop("og:image"),
        "og:url": prop("og:url"),
        "canonical": None,
    }

    link_canonical = soup.find("link", rel=lambda v: v and "canonical" in [x.lower() for x in (v if isinstance(v, list) else [v])])
    if link_canonical and link_canonical.has_attr("href"):
        metas["canonical"] = link_canonical["href"]

    return metas

def _extract_headings(soup: BeautifulSoup) -> Dict[str, List[str]]:
    data: Dict[str, List[str]] = {"h1": [], "h2": [], "h3": []}
    for level in ("h1", "h2", "h3"):
        for tag in soup.find_all(level):
            txt = _clean_text(tag.get_text(" "))
            if txt:
                data[level].append(txt)
    return data

def _extract_main_text(soup: BeautifulSoup, min_len: int = 40) -> str:
    if soup.body:
        text = soup.body.get_text(" ", strip=True)
    else:
        text = soup.get_text(" ", strip=True)
    return text[:20000]

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""

def _poll_until_ready_or_timeout(
    driver: webdriver.Chrome,
    url: str,
    max_seconds: float = 30.0,
    poll_interval: float = 0.25
) -> Tuple[str, bool]:
    """
    Navega e faz polling até existir <body> OU estourar o tempo.
    Retorna (page_source, timed_out).
    """
    start = time.monotonic()
    timed_out = False

    # Tenta navegar (não bloqueante por 'none', mas ainda pode esperar um pouco).
    try:
        driver.get(url)
    except TimeoutException:
        # Se houve timeout do próprio get, seguimos para capturar o que tiver.
        pass
    except WebDriverException:
        # Repassar para o chamador tratar retry
        raise

    # Aguarda presença de <body> ou até estourar o tempo
    body_found = False
    while True:
        elapsed = time.monotonic() - start
        if elapsed >= max_seconds:
            timed_out = True
            break
        try:
            # Aguarda rapidamente pela presença do body (não bloqueante por muito tempo)
            WebDriverWait(driver, poll_interval).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            body_found = True
            break
        except TimeoutException:
            # segue o loop até estourar o tempo
            continue

    # Coleta o que tiver
    try:
        page_source = driver.page_source or ""
    except Exception:
        page_source = ""

    # Se o body apareceu muito cedo, dá um micro-respiro para render dinâmico (sem estourar 30s)
    if body_found and not timed_out:
        while True:
            elapsed = time.monotonic() - start
            if elapsed >= max_seconds:
                timed_out = True
                break
            # Pequeno polling para permitir carregamento incremental
            time.sleep(poll_interval)
            # Heurística simples: se DOM cresce, continua mais um ciclo; senão, para
            try:
                current_len = len(driver.page_source or "")
            except Exception:
                current_len = len(page_source)
            if current_len <= len(page_source):
                break
            page_source = driver.page_source or ""

    return page_source, timed_out

def url_to_json(url: str, timeout: float = 30.0, max_retries: int = 1) -> PageContent:
    """
    Faz o scraping de uma URL usando Selenium headless e retorna um PageContent.
    - Navegação+render por tentativa: máx. 30s (default).
    - Até 2 tentativas (max_retries=1 => 2 tentativas).
    - Se estourar o tempo, retorna conteúdo parcial com timed_out=True.
    - Extração (BeautifulSoup) ocorre fora do limite de 30s.

    Raises:
        WebDriverException em falhas críticas do WebDriver após as tentativas.
        ValueError se nenhum HTML válido for obtido.
    """

    best_html = ""
    best_timed_out = False
    last_exception = None

    for attempt in range(max_retries + 1):
        driver, user_data_dir, cache_dir = None, None, None
        try:
            driver, user_data_dir, cache_dir = _create_chrome_driver_headless()
            html, timed_out = _poll_until_ready_or_timeout(driver, url, max_seconds=timeout, poll_interval=0.25)

            if len(html) > len(best_html):
                best_html = html
                best_timed_out = timed_out

            if html and ("<html" in html.lower() or "<body" in html.lower()):
                break

        except WebDriverException as e:
            last_exception = e
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            _cleanup_temp_dirs(user_data_dir, cache_dir)

    if not best_html:
        # Se nada foi obtido, propaga última exceção ou gera erro claro
        if last_exception:
            raise WebDriverException(f"Falha ao carregar {url}: {last_exception}")
        raise ValueError(f"Nenhum HTML válido obtido em {url}")

    # ===== Extração (fora do limite de 30s) =====
    soup = BeautifulSoup(best_html, "lxml")
    meta = _extract_meta(soup)
    headings_dict = _extract_headings(soup)
    main_text = _extract_main_text(soup)
    
    #print(soup.body.prettify())
    #print(soup.body.get_text(" ", strip=True))

    headings_data = HeadingsData(
        h1=headings_dict.get("h1", []),
        h2=headings_dict.get("h2", []),
        h3=headings_dict.get("h3", [])
    )

    og_data = OpenGraphData(
        type=meta.get("og:type"),
        url=meta.get("og:url"),
        image=meta.get("og:image")
    )

    return PageContent(
        title=meta.get("title"),
        description=meta.get("description"),
        keywords=meta.get("keywords"),
        canonical=meta.get("canonical"),
        headings=headings_data,
        text_full=main_text,
        og=og_data,
        timed_out=best_timed_out 
    )
