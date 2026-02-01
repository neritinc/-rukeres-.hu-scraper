import os
import csv
import time
import re
import base64
import io
import hashlib
import requests
from urllib.parse import urlparse, quote_plus
from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
import threading
from webdriver_manager.chrome import ChromeDriverManager

# --- BEALLITASOK ---
INPUT_FILE = "New Text Document.txt"
OUTPUT_DIR = "kepek2"
OUTPUT_DIRS = [OUTPUT_DIR, "kepek"]
OUTPUT_LIST_FILE = "kepek2_lista.txt"
BRANDS_FILE = "brands.csv"
IMAGES_PER_PRODUCT = 3
MIN_FILE_SIZE = 1
MIN_PIXELS = 0
MIN_SIDE = 0
REQUEST_TIMEOUT = 25
SLEEP_BETWEEN = 0.1
MAX_URLS_PER_QUERY = 200
LOG_REJECTS = True
SHOW_BROWSER = True
MAX_PRODUCTS_PER_SITE = 3
FAST_MODE = True
USE_GOOGLE_IMAGES = False
USE_SHOPS = False
USE_PCPP = False
ARUKERESO_ONLY = True
FOUND_FILE = "found.txt"
NOT_FOUND_FILE = "not_found.txt"
PRODUCTS_FILE = "products.txt"
PRODUCTS_FILE_ALT = "product.txt"
USE_ARUKERESO_TOP = False
ARUKERESO_TOP_URLS = [
    "https://www.arukereso.hu/videokartya-c3142/?sgst=1",
]
ARUKERESO_TOP_LIMIT = 20
LOCAL_SHOP_DOMAINS = [
    "arukereso.hu",
    "ipon.hu",
    "pcx.hu",
    "aqua.hu",
    "emag.hu",
    "edigital.hu",
]
FOREIGN_SHOP_DOMAINS = [
    "amazon.com",
    "amazon.de",
    "amazon.co.uk",
    "pcpartpicker.com",
    "newegg.com",
    "bhphotovideo.com",
    "bestbuy.com",
    "microcenter.com",
    "scan.co.uk",
    "overclockers.co.uk",
    "caseking.de",
]
ALL_SHOP_DOMAINS = LOCAL_SHOP_DOMAINS + FOREIGN_SHOP_DOMAINS
ONE_IMAGE_DOMAINS = {
    "arukereso.hu",
    "amazon.com",
    "amazon.de",
    "amazon.co.uk",
    "pcpartpicker.com",
    "bestbuy.com",
    "bhphotovideo.com",
}
DEFAULT_BRAND_DOMAIN_MAP = [
    (["amd", "ryzen", "radeon"], ["amd.com"]),
    (["intel", "core", "arc"], ["intel.com"]),
    (["nvidia", "geforce", "rtx", "gtx"], ["nvidia.com"]),
    (["asrock"], ["asrock.com"]),
    (["asus", "rog", "tuf", "prime", "strix"], ["asus.com", "rog.asus.com"]),
    (["msi", "mag", "mpg", "meg"], ["msi.com"]),
    (["gigabyte", "aorus"], ["gigabyte.com", "aorus.com"]),
    (["corsair"], ["corsair.com"]),
    (["kingston", "fury"], ["kingston.com"]),
    (["g.skill", "gskill"], ["gskill.com"]),
    (["crucial"], ["crucial.com"]),
    (["teamgroup", "t-force", "t-create"], ["teamgroupinc.com"]),
    (["patriot"], ["patriotmemory.com"]),
    (["samsung"], ["samsung.com"]),
    (["wd", "western digital", "westerndigital"], ["wd.com", "westerndigital.com"]),
    (["seagate"], ["seagate.com"]),
    (["lexar"], ["lexar.com"]),
    (["sk hynix", "hynix"], ["skhynix.com"]),
    (["seasonic"], ["seasonic.com"]),
    (["be quiet", "be quiet!"], ["bequiet.com"]),
    (["deepcool"], ["deepcool.com"]),
    (["fractal"], ["fractal-design.com"]),
    (["lian li"], ["lian-li.com"]),
    (["phanteks"], ["phanteks.com"]),
    (["cooler master"], ["coolermaster.com"]),
    (["razer"], ["razer.com"]),
    (["logitech"], ["logitech.com"]),
]

BRAND_SYNONYMS = {
    "msi": ["msi"],
    "gigabyte": ["gigabyte", "aorus"],
    "asus": ["asus", "rog", "tuf", "strix", "prime"],
    "asrock": ["asrock"],
    "zotac": ["zotac"],
    "palit": ["palit"],
    "gainward": ["gainward"],
    "sapphire": ["sapphire"],
    "powercolor": ["powercolor"],
    "xfx": ["xfx"],
    "pny": ["pny"],
    "inno3d": ["inno3d"],
    "galax": ["galax", "kfa2"],
    "evga": ["evga"],
    "msi": ["msi"],
    "lenovo": ["lenovo"],
    "dell": ["dell", "alienware"],
    "hp": ["hp", "omen"],
    "acer": ["acer", "predator"],
    "corsair": ["corsair"],
    "kingston": ["kingston", "fury"],
    "g.skill": ["g.skill", "gskill", "trident"],
    "crucial": ["crucial"],
    "teamgroup": ["teamgroup", "t-force", "t-create"],
    "patriot": ["patriot"],
    "samsung": ["samsung"],
    "wd": ["wd", "westerndigital", "western", "digital"],
    "seagate": ["seagate"],
    "lexar": ["lexar"],
    "sk hynix": ["sk", "hynix", "skhynix"],
    "seasonic": ["seasonic"],
    "be quiet": ["be", "quiet", "bequiet"],
    "deepcool": ["deepcool"],
    "fractal": ["fractal"],
    "lian li": ["lian", "li", "lian-li"],
    "phanteks": ["phanteks"],
    "cooler master": ["cooler", "master", "coolermaster"],
}

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)
_ACTIVE_DRIVER = None

def load_brand_domains(path: str) -> dict[str, list[str]]:
    if not os.path.exists(path):
        return {}
    brand_domains: dict[str, list[str]] = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader, None)
        for row in reader:
            if not row:
                continue
            brand = row[0].strip().lower()
            if not brand:
                continue
            domain_field = row[2].strip() if len(row) > 2 else ""
            if not domain_field:
                brand_domains[brand] = []
                continue
            domains = re.split(r"[,\s]+", domain_field)
            clean = [d.strip() for d in domains if d.strip()]
            brand_domains[brand] = clean
    return brand_domains


def clean_filename(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    return "_".join(name.split())


def read_unique_products(path: str) -> list[str]:
    unique_names = []
    seen = set()
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            if not row:
                continue
            name = row[0].strip()
            if name and name.lower() != "product_name" and name not in seen:
                unique_names.append(name)
                seen.add(name)
    return unique_names


def read_product_colors(path: str) -> dict[str, list[str]]:
    colors: dict[str, list[str]] = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            if not row or len(row) < 3:
                continue
            name = row[0].strip()
            if not name or name.lower() == "product_name":
                continue
            param = row[1].strip().lower()
            if param != "color":
                continue
            value = row[2].strip()
            toks = color_tokens_from_value(value)
            if toks:
                if name not in colors:
                    colors[name] = []
                for t in toks:
                    if t not in colors[name]:
                        colors[name].append(t)
    return colors


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    if not SHOW_BROWSER:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={UA}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def snooze(t: float) -> None:
    if FAST_MODE:
        time.sleep(max(0.2, t * 0.4))
    else:
        time.sleep(t)


def maybe_accept_cookies(driver: webdriver.Chrome) -> None:
    labels = [
        "Accept all",
        "Accept",
        "I agree",
        "Elfogadom",
        "Elfogadás",
        "Elfogadás és bezárás",
        "Elfogadom a sütiket",
        "Sütik elfogadása",
        "Mindet elfogadom",
        "Összes elfogadása",
        "Rendben",
        "OK",
        "Összes elfogadása",
        "Accept all cookies",
    ]
    try:
        # Common cookie accept selectors
        selectors = [
            "button#bnp_btn_accept",
            "button#bnp_btn_reject",
            "button#onetrust-accept-btn-handler",
            "button#accept-cookie",
            "button.cookie-accept",
            "button[aria-label*='Accept']",
            "button[aria-label*='Elfogad']",
            "button[title*='Accept']",
            "button[title*='Elfogad']",
        ]
        for sel in selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, sel)
            if buttons:
                try:
                    buttons[0].click()
                    snooze(0.5)
                    return
                except Exception:
                    pass
        # Bing consent can be inside iframe; try all frames
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            try:
                driver.switch_to.frame(frame)
                buttons = driver.find_elements(By.CSS_SELECTOR, "button#bnp_btn_accept, button[title*='Accept']")
                if buttons:
                    buttons[0].click()
                    snooze(0.5)
                    driver.switch_to.default_content()
                    return
                driver.switch_to.default_content()
            except Exception:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass
        for label in labels:
            buttons = driver.find_elements(By.XPATH, f"//button[contains(., '{label}')]")
            if buttons:
                buttons[0].click()
                snooze(0.5)
                return
    except Exception:
        return


def image_search_urls(driver: webdriver.Chrome, query: str) -> list[str]:
    url = f"https://www.bing.com/images/search?q={requests.utils.quote(query)}&form=HDRSC2"
    driver.get(url)
    snooze(1.2)
    maybe_accept_cookies(driver)

    for _ in range(1 if FAST_MODE else 2):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        snooze(0.8)

    # Prefer full-size image URLs embedded in page source ("murl")
    urls: list[str] = []
    page = driver.page_source
    matches = re.findall(r'"murl":"(.*?)"', page)
    for m in matches:
        cleaned = m.replace("\\/", "/")
        if cleaned.startswith("http"):
            urls.append(cleaned)
        if len(urls) >= MAX_URLS_PER_QUERY:
            break

    if len(urls) < 10:
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            src = img.get_attribute("data-src") or img.get_attribute("src")
            if not src:
                continue
            if src.startswith("http") or src.startswith("data:image"):
                urls.append(src)
            if len(urls) >= MAX_URLS_PER_QUERY:
                break

    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def image_search_urls_google(driver: webdriver.Chrome, query: str) -> list[str]:
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}&tbm=isch"
    driver.get(url)
    snooze(1.2)
    maybe_accept_cookies(driver)

    for _ in range(1 if FAST_MODE else 2):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        snooze(0.8)

    urls: list[str] = []
    page = driver.page_source
    matches = re.findall(r'"ou":"(.*?)"', page)
    for m in matches:
        cleaned = m.replace("\\/", "/")
        if cleaned.startswith("http"):
            urls.append(cleaned)
        if len(urls) >= MAX_URLS_PER_QUERY:
            break

    if len(urls) < 10:
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            try:
                src = img.get_attribute("data-src") or img.get_attribute("src")
            except Exception:
                src = None
            if not src:
                continue
            if src.startswith("http") or src.startswith("data:image"):
                urls.append(src)
            if len(urls) >= MAX_URLS_PER_QUERY:
                break

    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def web_search_urls_bing(driver: webdriver.Chrome, query: str) -> list[str]:
    url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
    driver.get(url)
    snooze(1.2)
    maybe_accept_cookies(driver)

    urls: list[str] = []
    try:
        links = driver.find_elements(By.CSS_SELECTOR, "li.b_algo a")
    except Exception:
        links = []
    for a in links:
        try:
            href = a.get_attribute("href")
        except Exception:
            href = None
        if not href:
            continue
        if "bing.com" in href or "microsoft.com" in href:
            continue
        urls.append(href)
        if len(urls) >= MAX_PRODUCTS_PER_SITE:
            break

    # fallback: regex in page source
    if not urls:
        page = driver.page_source
        matches = re.findall(r'href="(https?://[^"]+)"', page)
        for m in matches:
            if "bing.com" in m or "microsoft.com" in m:
                continue
            urls.append(m)
            if len(urls) >= MAX_PRODUCTS_PER_SITE:
                break

    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def normalize_url(src: str, base: str | None = None) -> str:
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/") and base:
        return base.rstrip("/") + src
    return src


def expand_highres_variants(url: str) -> list[str]:
    variants = [url]

    def add(u: str) -> None:
        if u and u not in variants:
            variants.append(u)

    # Common CDN size segments
    if re.search(r"/(small|mid|thumb|thumbnail)/", url):
        add(re.sub(r"/(small|mid|thumb|thumbnail)/", "/full/", url))
    # Arukereso (akcdn) gallery size variants
    if "akcdn.net" in url:
        add(re.sub(r"/gallery/(\\d+)/(?:small|mid|thumb)/", r"/gallery/\\1/full/", url))
        add(re.sub(r"/(small|mid|thumb)/", "/full/", url))
    # ipon-style size buckets
    if "/medium/" in url:
        add(url.replace("/medium/", "/large/"))
        add(url.replace("/medium/", "/big/"))
    if "/small/" in url:
        add(url.replace("/small/", "/large/"))
        add(url.replace("/small/", "/big/"))
    # Strip inline size suffixes like _200x200 or -300x300 before extension
    stripped = re.sub(r"([_-])\\d{2,4}x\\d{2,4}(?=\\.)", "", url)
    if stripped != url:
        add(stripped)

    return variants


def download_image(src: str, referer: str | None = None) -> bytes | None:
    try:
        src = normalize_url(src, None)
        if src.startswith("data:image"):
            _, encoded = src.split(",", 1)
            data = base64.b64decode(encoded)
            return data if len(data) >= MIN_FILE_SIZE else None
        headers = {
            "User-Agent": UA,
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        if referer:
            headers["Referer"] = referer
        for candidate in expand_highres_variants(src):
            for _ in range(2):
                r = requests.get(candidate, timeout=REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
                if r.status_code == 200:
                    return r.content if len(r.content) >= MIN_FILE_SIZE else None
                # Retry once with minimal headers if blocked
                headers = {"User-Agent": UA}
        # Last resort: use browser to fetch base64 via JS (helps with hotlink/CDN)
        try:
            if _ACTIVE_DRIVER is not None and referer:
                _ACTIVE_DRIVER.get(referer)
                snooze(0.8)
                for candidate in expand_highres_variants(src):
                    data_url = _ACTIVE_DRIVER.execute_script(
                        """
                        const url = arguments[0];
                        const cb = arguments[1];
                        fetch(url).then(r => r.blob()).then(b => {
                            const fr = new FileReader();
                            fr.onload = () => cb(fr.result);
                            fr.readAsDataURL(b);
                        }).catch(() => cb(null));
                        """,
                        candidate,
                    )
                    if data_url and isinstance(data_url, str) and data_url.startswith("data:image"):
                        _, encoded = data_url.split(",", 1)
                        data = base64.b64decode(encoded)
                        return data if len(data) >= MIN_FILE_SIZE else None
        except Exception:
            pass
        return None
    except Exception:
        return None


def detect_brand_domains(name: str, brand_domains: dict[str, list[str]]) -> list[str]:
    n = name.lower().strip()
    # Longest brand first to match multi-word brands
    for brand in sorted(brand_domains.keys(), key=len, reverse=True):
        if n.startswith(brand + " ") or n == brand:
            return brand_domains.get(brand, [])
    # Fallback to default map if brands.csv is empty or missing domain
    for aliases, doms in DEFAULT_BRAND_DOMAIN_MAP:
        for a in aliases:
            if a in n:
                return doms
    return []


def detect_primary_brand(name: str) -> str | None:
    n = name.lower()
    # Prefer longest brand keys to match multi-word brands first
    for brand in sorted(BRAND_SYNONYMS.keys(), key=len, reverse=True):
        for alias in BRAND_SYNONYMS[brand]:
            if alias in n:
                return brand
    return None


def default_domains_for_brand(brand: str) -> list[str]:
    for aliases, doms in DEFAULT_BRAND_DOMAIN_MAP:
        if brand in aliases:
            return doms
    return []


def ensure_brands_file(path: str, products: list[str]) -> None:
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return
    except Exception:
        # If we cannot stat the file, just try to write it.
        pass

    detected: dict[str, list[str]] = {}
    for name in products:
        brand = detect_primary_brand(name)
        if not brand:
            continue
        if brand not in detected:
            detected[brand] = default_domains_for_brand(brand)

    if not detected:
        return

    # Write a minimal brands.csv that load_brand_domains() can read.
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["brand", "aliases", "domains"])
        for brand in sorted(detected.keys()):
            aliases = ",".join(BRAND_SYNONYMS.get(brand, [brand]))
            domains = ",".join(detected[brand])
            writer.writerow([brand, aliases, domains])


def build_manufacturer_queries(name: str, domains: list[str]) -> list[str]:
    base_query = (
        f"{name} official retail box packaging white background professional photography "
        f"-cooler -fan -heatsink -tray -die"
    )
    site_queries = [f"{base_query} site:{d}" for d in domains]
    fallback = [
        base_query,
        f"{name} product box white background official photos -cooler -fan -heatsink -tray -die",
        f"{name} retail box photo white background -cooler -fan -heatsink -tray -die",
    ]
    return site_queries + fallback


def build_shop_queries(name: str) -> list[str]:
    site_queries = []
    for domain in ALL_SHOP_DOMAINS:
        # Ne hasznaljunk szigoruan site: szurot, inkabb domain kulcsszo + utoszures
        site_queries.append(f"{name} {domain}")
        site_queries.append(f"{name} doboz csomagolas {domain}")
        site_queries.append(f"{name} termekfoto {domain}")
    return site_queries


def find_search_input(driver: webdriver.Chrome):
    candidates = driver.find_elements(
        By.CSS_SELECTOR,
        "input[type='search'], input[name='q'], input[name='st'], input[name='field-keywords'], input#twotabsearchtextbox, input[name='query'], input[name='search'], input[placeholder*='Keres'], input[placeholder*='Search']"
    )
    for c in candidates:
        try:
            if c.is_displayed() and c.is_enabled():
                return c
        except Exception:
            continue
    return None


def is_product_link(domain: str, href: str) -> bool:
    h = href.lower()
    if domain == "pcx.hu":
        return "pcx.hu/" in h and "--" in h and "kereses" not in h and "kategori" not in h
    if domain == "ipon.hu":
        return "ipon.hu/" in h and ("/termek/" in h or "/shop/termek/" in h)
    if domain == "arukereso.hu":
        return "arukereso.hu/" in h and re.search(r"-p\\d+/?", h) is not None and "kereso" not in h
    if domain in {"amazon.com", "amazon.de", "amazon.co.uk"}:
        return "/dp/" in h or "/gp/product/" in h
    if domain == "pcpartpicker.com":
        return "/product/" in h and "pcpartpicker.com/product/" in h
    if domain == "newegg.com":
        return "/p/" in h or "/product/" in h
    if domain == "bhphotovideo.com":
        return "/c/product/" in h
    if domain == "bestbuy.com":
        return "/site/" in h and "/sku/" in h
    if domain == "microcenter.com":
        return "/product/" in h
    if domain == "scan.co.uk":
        return "/products/" in h
    if domain == "overclockers.co.uk":
        return "/products/" in h
    if domain == "caseking.de":
        return "/en/" in h or "/de/" in h
    # fallback: domain + not obvious non-product paths
    bad = ["kereses", "search", "kategori", "filter", "kosar", "cart", "brand", "gyarto"]
    return domain in h and not any(b in h for b in bad)


def collect_product_links(driver: webdriver.Chrome, domain: str) -> list[str]:
    if domain == "arukereso.hu":
        try:
            # Try to grab product links directly via JS (some are data-href)
            urls = driver.execute_script(
                """
                const nodes = Array.from(document.querySelectorAll('a[href], a[data-href]'));
                return nodes.map(a => a.href || a.getAttribute('data-href')).filter(Boolean);
                """
            )
            if urls:
                # Dedup + limit
                seen = set()
                uniq = []
                for u in urls:
                    if re.search(r"-p\\d+/?", u) is None:
                        continue
                    if u not in seen:
                        uniq.append(u)
                        seen.add(u)
                    if len(uniq) >= MAX_PRODUCTS_PER_SITE:
                        break
                return uniq
        except Exception:
            pass
    if domain == "aqua.hu":
        return []
    if domain == "emag.hu":
        return []
    links = driver.find_elements(By.TAG_NAME, "a")
    urls: list[str] = []
    for a in links:
        href = a.get_attribute("href")
        if not href:
            continue
        if is_product_link(domain, href):
            urls.append(href)
        if len(urls) >= MAX_PRODUCTS_PER_SITE:
            break
    # dedup
    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def search_site_for_products(driver: webdriver.Chrome, domain: str, query: str) -> list[str]:
    # Use site search box only (no URL-based search)
    try:
        driver.get(f"https://{domain}/")
        snooze(1.2)
        maybe_accept_cookies(driver)
        inp = find_search_input(driver)
        if inp:
            inp.clear()
            inp.send_keys(query)
            inp.send_keys(Keys.ENTER)
            snooze(1.6)
            # If the page has a visible search/submit button, click it as well
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button[aria-label*='Keres'], button[title*='Keres']")
                if btns:
                    btns[0].click()
                    snooze(1.2)
            except Exception:
                pass
            # Arukereso: click first product result if present
            if domain == "arukereso.hu":
                try:
                    link = driver.execute_script(
                        """
                        const links = Array.from(document.querySelectorAll('a[href]'));
                        const hit = links.find(a => /-p\\d+\\/?/i.test(a.href));
                        return hit ? hit.href : null;
                        """
                    )
                    if link:
                        driver.get(link)
                        snooze(1.2)
                        return [link]
                except Exception:
                    pass
            return collect_product_links(driver, domain)
    except Exception:
        pass
    return []


BOX_KEYWORDS = [
    "box",
    "boxed",
    "package",
    "packaging",
    "doboz",
    "csomag",
    "csomagolas",
    "retail",
]

COLOR_SYNONYMS = {
    "black": ["black", "fekete", "charcoal", "carbon", "dark", "midnight", "noir"],
    "white": ["white", "feher", "fehér", "snow", "arctic", "ivory", "moonlight"],
    "silver": ["silver", "ezust", "ezüst", "platinum", "titanium", "steel", "chrome"],
    "gold": ["gold", "arany"],
    "red": ["red", "piros", "crimson", "scarlet", "ruby"],
    "blue": ["blue", "kek", "kék", "navy", "azure"],
    "green": ["green", "zold", "zöld", "emerald"],
    "purple": ["purple", "lilac", "violet"],
    "grey": ["grey", "gray", "szurke", "szürke", "graphite"],
    "brown": ["brown", "walnut", "wood"],
    "pink": ["pink", "rose"],
    "orange": ["orange"],
    "yellow": ["yellow", "sarga", "sárga"],
    "beige": ["beige", "cream"],
    "multicolor": ["rgb", "colorful", "multi", "rainbow"],
}


def color_tokens_from_value(value: str) -> list[str]:
    v = value.lower()
    tokens: list[str] = []
    for _, syns in COLOR_SYNONYMS.items():
        for s in syns:
            if s in v:
                for add in syns:
                    if add not in tokens:
                        tokens.append(add)
                break
    if not tokens:
        parts = re.findall(r"[a-z0-9]+", v)
        tokens = [p for p in parts if len(p) >= 3]
    return tokens

def name_tokens(name: str) -> list[str]:
    parts = re.findall(r"[a-z0-9]+", name.lower())
    return [p for p in parts if len(p) >= 3]


def detect_brand_tokens(name: str) -> list[str]:
    n = name.lower()
    found: list[str] = []
    for _, syns in BRAND_SYNONYMS.items():
        for s in syns:
            if s in n:
                for add in syns:
                    if add not in found:
                        found.append(add)
                break
    return found


def name_match_score(name_toks: list[str], text: str) -> int:
    t = text.lower()
    score = 0
    for tok in name_toks:
        if tok in t:
            score += 2
    return score


def score_image_candidate(url: str, alt: str, title: str, name_toks: list[str], color_toks: list[str]) -> int:
    text = f"{alt} {title} {url}".lower()
    score = 0
    for k in BOX_KEYWORDS:
        if k in text:
            score += 5
    if "box" in text or "doboz" in text:
        score += 3
    if any(x in text for x in ["tray", "die", "cooler", "fan", "heatsink"]):
        score -= 5
    score += name_match_score(name_toks, text)
    if color_toks:
        score += 3 if any(c in text for c in color_toks) else -3
    return score


def should_accept_image(text: str, name_toks: list[str], color_toks: list[str], brand_toks: list[str], relaxed: bool = False) -> bool:
    if not relaxed and name_match_score(name_toks, text) < 1:
        return False
    if color_toks and not any(c in text for c in color_toks):
        return False
    if brand_toks and not any(b in text for b in brand_toks):
        return False
    return True


def extract_image_urls(driver: webdriver.Chrome, product_url: str, name_toks: list[str], color_toks: list[str], domain: str) -> list[tuple[str, str]]:
    try:
        driver.get(product_url)
        snooze(1.6)
        maybe_accept_cookies(driver)
        for _ in range(1 if FAST_MODE else 2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            snooze(0.8)
    except Exception:
        return []

    try:
        images = driver.find_elements(By.TAG_NAME, "img")
    except Exception:
        images = []
    candidates: list[tuple[int, str, str]] = []

    # og:image / twitter:image
    try:
        metas = driver.find_elements(By.CSS_SELECTOR, "meta[property='og:image'], meta[name='twitter:image']")
        for m in metas:
            content = m.get_attribute("content")
            if content and content.startswith("http"):
                content = normalize_url(content, product_url)
                candidates.append((score_image_candidate(content, "", "", name_toks, color_toks), content, content.lower()))
    except Exception:
        pass

    # Arukereso specific carousel images
    if domain == "arukereso.hu":
        try:
            ars = driver.find_elements(By.CSS_SELECTOR, "#carousel-gallery img")
            for img in ars:
                src = img.get_attribute("data-src") or img.get_attribute("src")
                if src and (src.startswith("http") or src.startswith("data:image")):
                    src = normalize_url(src, product_url)
                    candidates.append((score_image_candidate(src, "", "", name_toks, color_toks), src, src.lower()))
        except Exception:
            pass

    def pick_from_srcset(srcset: str) -> str | None:
        opts = []
        for part in srcset.split(","):
            p = part.strip().split(" ")
            if not p:
                continue
            url = p[0].strip()
            w = 0
            if len(p) > 1 and p[1].endswith("w"):
                try:
                    w = int(p[1][:-1])
                except Exception:
                    w = 0
            opts.append((w, url))
        if not opts:
            return None
        opts.sort(reverse=True)
        return opts[0][1]

    attrs = ["data-zoom-image", "data-large", "data-full", "data-original", "data-image"]

    for img in images:
        try:
            src = img.get_attribute("data-src") or img.get_attribute("src")
            srcset = img.get_attribute("data-srcset") or img.get_attribute("srcset")
            alt = img.get_attribute("alt") or ""
            title = img.get_attribute("title") or ""
        except Exception:
            continue
        for a in attrs:
            try:
                val = img.get_attribute(a)
            except Exception:
                val = None
            if val and (val.startswith("http") or val.startswith("data:image")):
                val = normalize_url(val, product_url)
                candidates.append((score_image_candidate(val, alt, title, name_toks, color_toks), val, f"{alt} {title} {val}".lower()))
        if srcset:
            best = pick_from_srcset(srcset)
            if best:
                best = normalize_url(best, product_url)
                candidates.append((score_image_candidate(best, alt, title, name_toks, color_toks), best, f"{alt} {title} {best}".lower()))
        if src and (src.startswith("http") or src.startswith("data:image")):
            src = normalize_url(src, product_url)
            candidates.append((score_image_candidate(src, alt, title, name_toks, color_toks), src, f"{alt} {title} {src}".lower()))
        if len(candidates) >= MAX_URLS_PER_QUERY:
            break

    # Ipon/PCX gyakran scriptben tarol nagy kepeket
    page = driver.page_source
    extra = re.findall(r"https?://[^\"'\\s>]+\\.(?:jpg|jpeg|png|webp)", page, flags=re.IGNORECASE)
    for u in extra:
        low = u.lower()
        if any(x in low for x in ["logo", "icon", "sprite", "avatar", "thumb"]):
            continue
        u = normalize_url(u, product_url)
        candidates.append((score_image_candidate(u, "", "", name_toks, color_toks), u, u.lower()))
        if len(candidates) >= MAX_URLS_PER_QUERY:
            break

    # sort by score (box-related first), then dedup
    candidates.sort(key=lambda x: x[0], reverse=True)
    urls: list[tuple[str, str]] = []
    seen = set()
    min_score = 2
    for score, u, text in candidates:
        if score < min_score:
            continue
        if u not in seen:
            urls.append((u, text))
            seen.add(u)
        if len(urls) >= MAX_URLS_PER_QUERY:
            break
    # dedup
    seen = set()
    uniq: list[tuple[str, str]] = []
    for u, text in urls:
        if u not in seen:
            uniq.append((u, text))
            seen.add(u)
    return uniq


def fetch_top_products_from_category(driver: webdriver.Chrome, url: str, limit: int = 20) -> list[str]:
    try:
        driver.get(url)
        snooze(1.2)
        maybe_accept_cookies(driver)
        for _ in range(2 if FAST_MODE else 3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            snooze(0.6)
    except Exception:
        return []

    results: dict[int, str] = {}
    try:
        boxes = driver.find_elements(By.CSS_SELECTOR, "div.product-box")
    except Exception:
        boxes = []

    for box in boxes:
        try:
            badge = box.find_elements(By.CSS_SELECTOR, ".badge-top-item-wrapper .place")
            if not badge:
                continue
            place_text = badge[0].text.strip()
            if not place_text.isdigit():
                continue
            place = int(place_text)
            if place < 1 or place > limit:
                continue
            name_el = box.find_elements(By.CSS_SELECTOR, ".name h2 a")
            if not name_el:
                continue
            name = name_el[0].get_attribute("title") or name_el[0].text
            name = name.strip()
            if name:
                results[place] = name
        except Exception:
            continue

    top = [results[p] for p in sorted(results.keys()) if p <= limit]
    return top[:limit]


def trim_white_borders(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    bg = Image.new("RGB", rgb.size, "white")
    diff = ImageChops.difference(rgb, bg)
    bbox = diff.getbbox()
    if bbox:
        return rgb.crop(bbox)
    return rgb


def resize_and_letterbox(img: Image.Image, size: int = 800) -> Image.Image:
    img = img.convert("RGB")
    img.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def check_image_size(data: bytes) -> tuple[bool, int, int]:
    try:
        with Image.open(io.BytesIO(data)) as img:
            w, h = img.size
            if MIN_PIXELS <= 0 and MIN_SIDE <= 0:
                return (True, w, h)
            return (w * h >= MIN_PIXELS and w >= MIN_SIDE and h >= MIN_SIDE, w, h)
    except Exception:
        return (False, 0, 0)


def process_image(data: bytes) -> bytes | None:
    try:
        with Image.open(io.BytesIO(data)) as img:
            cropped = trim_white_borders(img)
            final_img = resize_and_letterbox(cropped, size=800)
            out = io.BytesIO()
            final_img.save(out, format="JPEG", quality=92, optimize=True)
            return out.getvalue()
    except Exception:
        return None


def save_processed_image(data: bytes, path: str) -> tuple[bool, str | None]:
    ok, w, h = check_image_size(data)
    if not ok:
        if LOG_REJECTS:
            print(f"    x kicsi kep: {w}x{h}")
        return False, None
    processed = process_image(data)
    if not processed:
        return False, None
    if len(processed) < MIN_FILE_SIZE:
        return False, None
    processed_hash = hashlib.sha1(processed).hexdigest()
    with open(path, "wb") as f:
        f.write(processed)
    return True, processed_hash


def list_existing_images(base: str) -> list[str]:
    matches: list[tuple[int, str]] = []
    prefix = f"{base}_"
    for out_dir in OUTPUT_DIRS:
        try:
            for entry in os.listdir(out_dir):
                if not entry.startswith(prefix) or not entry.lower().endswith(".jpg"):
                    continue
                suffix = entry[len(prefix):-4]
                try:
                    idx = int(suffix)
                except Exception:
                    continue
                matches.append((idx, entry))
        except Exception:
            continue
    matches.sort(key=lambda x: x[0])
    seen = set()
    ordered = []
    for _, name in matches:
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
        if len(ordered) >= IMAGES_PER_PRODUCT:
            break
    return ordered


def write_output_dir_list(out_dir: str, out_file: str) -> None:
    try:
        entries = [
            e
            for e in os.listdir(out_dir)
            if e.lower().endswith(".jpg") and os.path.isfile(os.path.join(out_dir, e))
        ]
    except Exception:
        entries = []
    entries.sort()
    with open(out_file, "w", encoding="utf-8") as f:
        for idx, name in enumerate(entries, start=1):
            f.write(f"{idx};{name}\n")


def format_found_lines(files: list[str], start_index: int) -> tuple[list[str], int]:
    lines = []
    idx = start_index
    for fname in files:
        lines.append(f"{idx};{fname}")
        idx += 1
    return lines, idx


def strip_paren_suffix(name: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()


def main() -> None:
    products = read_unique_products(INPUT_FILE)
    product_colors = read_product_colors(INPUT_FILE)
    ensure_brands_file(BRANDS_FILE, products)
    brand_domains = load_brand_domains(BRANDS_FILE)
    driver = setup_driver()
    global _ACTIVE_DRIVER
    _ACTIVE_DRIVER = driver
    def ensure_driver() -> None:
        nonlocal driver
        try:
            _ = driver.title
        except Exception:
            try:
                driver.quit()
            except Exception:
                pass
            driver = setup_driver()
            globals()["_ACTIVE_DRIVER"] = driver
    if USE_ARUKERESO_TOP and ARUKERESO_TOP_URLS:
        top_products: list[str] = []
        seen_top = set()
        for url in ARUKERESO_TOP_URLS:
            tops = fetch_top_products_from_category(driver, url, ARUKERESO_TOP_LIMIT)
            for name in tops:
                if name not in seen_top:
                    top_products.append(name)
                    seen_top.add(name)
        if top_products:
            products = top_products
    found_lines: list[str] = []
    not_found: list[str] = []
    found_seen = set()
    not_found_seen = set()
    product_seen = set()
    found_counter = 1

    # Friss mappalista kulon fajlba
    write_output_dir_list(OUTPUT_DIR, OUTPUT_LIST_FILE)

    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        pass
    with open(PRODUCTS_FILE_ALT, "w", encoding="utf-8") as f:
        pass
    with open(FOUND_FILE, "w", encoding="utf-8") as f:
        pass
    with open(NOT_FOUND_FILE, "w", encoding="utf-8") as f:
        pass

    for index, name in enumerate(products, start=1):
        ensure_driver()
        if name not in product_seen:
            with open(PRODUCTS_FILE, "a", encoding="utf-8") as f:
                f.write(name + "\n")
            with open(PRODUCTS_FILE_ALT, "a", encoding="utf-8") as f:
                f.write(name + "\n")
            product_seen.add(name)
        base = clean_filename(name)
        existing = list_existing_images(base)
        if existing:
            lines, found_counter = format_found_lines(existing, found_counter)
            for line in lines:
                found_lines.append(line)
                if line not in found_seen:
                    with open(FOUND_FILE, "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                    found_seen.add(line)
            print(f"[{index}/{len(products)}] {name} -> mar letezik, kihagyva")
            continue

        print(f"[{index}/{len(products)}] {name} letoltes...", end=" ", flush=True)

        count = 0
        rejected_small = 0
        rejected_dl = 0
        rejected_dup = 0
        seen_urls = set()
        seen_hashes = set()
        saved_files: list[str] = []

        # Arukereso eloszor
        if ARUKERESO_ONLY and count < IMAGES_PER_PRODUCT:
            toks = name_tokens(name)
            color_toks = []  # arukereso: ne szurnk szinre
            brand_toks = detect_brand_tokens(name)
            ensure_driver()
            product_links = search_site_for_products(driver, "arukereso.hu", name)
            for page_url in product_links:
                if count >= IMAGES_PER_PRODUCT:
                    break
                try:
                    img_urls = extract_image_urls(driver, page_url, toks, color_toks, "arukereso.hu")
                except (WebDriverException, NoSuchWindowException):
                    ensure_driver()
                    try:
                        img_urls = extract_image_urls(driver, page_url, toks, color_toks, "arukereso.hu")
                    except Exception:
                        img_urls = []
                if LOG_REJECTS:
                    print(f"  -> arukereso.hu termekoldal: {page_url} | kepek: {len(img_urls)}")
                for src, text in img_urls:
                    if count >= IMAGES_PER_PRODUCT:
                        break
                    if src in seen_urls:
                        continue
                    seen_urls.add(src)
                    if not should_accept_image(text, toks, color_toks, brand_toks, relaxed=True):
                        continue
                    data = download_image(src, referer=page_url)
                    if not data:
                        rejected_dl += 1
                        continue
                    data_hash = hashlib.sha1(data).hexdigest()
                    if data_hash in seen_hashes:
                        rejected_dup += 1
                        continue
                    out_path = os.path.join(OUTPUT_DIR, f"{base}_{count + 1}.jpg")
                    saved, processed_hash = save_processed_image(data, out_path)
                    if saved:
                        seen_hashes.add(data_hash)
                        if processed_hash:
                            seen_hashes.add(processed_hash)
                        count += 1
                        saved_files.append(os.path.basename(out_path))
                        snooze(SLEEP_BETWEEN)
                    else:
                        rejected_small += 1

        # Ha Arukereso nem talalt, nezzuk meg IPON-t is
        if count < IMAGES_PER_PRODUCT and count > 0:
            ipon_name = strip_paren_suffix(name)
            toks = name_tokens(ipon_name)
            color_toks = product_colors.get(name, [])
            brand_toks = detect_brand_tokens(ipon_name)
            ensure_driver()
            try:
                product_links = search_site_for_products(driver, "ipon.hu", ipon_name)
            except Exception:
                product_links = []
            try:
                for page_url in product_links:
                    if count >= IMAGES_PER_PRODUCT:
                        break
                    try:
                        img_urls = extract_image_urls(driver, page_url, toks, color_toks, "ipon.hu")
                    except (WebDriverException, NoSuchWindowException):
                        ensure_driver()
                        try:
                            img_urls = extract_image_urls(driver, page_url, toks, color_toks, "ipon.hu")
                        except Exception:
                            img_urls = []
                    if LOG_REJECTS:
                        print(f"  -> ipon.hu termekoldal: {page_url} | kepek: {len(img_urls)}")
                    for src, text in img_urls:
                        if count >= IMAGES_PER_PRODUCT:
                            break
                        if src in seen_urls:
                            continue
                        seen_urls.add(src)
                        if not should_accept_image(text, toks, color_toks, brand_toks, relaxed=True):
                            continue
                        data = download_image(src, referer=page_url)
                        if not data:
                            rejected_dl += 1
                            continue
                        data_hash = hashlib.sha1(data).hexdigest()
                        if data_hash in seen_hashes:
                            rejected_dup += 1
                            continue
                        out_path = os.path.join(OUTPUT_DIR, f"{base}_{count + 1}.jpg")
                        saved, processed_hash = save_processed_image(data, out_path)
                        if saved:
                            seen_hashes.add(data_hash)
                            if processed_hash:
                                seen_hashes.add(processed_hash)
                            count += 1
                            saved_files.append(os.path.basename(out_path))
                            snooze(SLEEP_BETWEEN)
                        else:
                            rejected_small += 1
            except Exception:
                if LOG_REJECTS:
                    print("  -> ipon.hu hiba, tovabb")

        if LOG_REJECTS:
            print(f"OK ({count} kep) | elutasitva: kicsi={rejected_small} letoltes={rejected_dl} duplikalt={rejected_dup}")
        else:
            print(f"OK ({count} kep)")

        if saved_files:
            lines, found_counter = format_found_lines(saved_files, found_counter)
            for line in lines:
                found_lines.append(line)
                if line not in found_seen:
                    with open(FOUND_FILE, "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                    found_seen.add(line)
        else:
            not_found.append(name)
            if name not in not_found_seen:
                with open(NOT_FOUND_FILE, "a", encoding="utf-8") as f:
                    f.write(name + "\n")
                not_found_seen.add(name)

    def _quit_driver(drv: webdriver.Chrome) -> None:
        try:
            drv.quit()
        except Exception:
            pass

    t = threading.Thread(target=_quit_driver, args=(driver,), daemon=True)
    t.start()
    t.join(timeout=5.0)

    with open(FOUND_FILE, "a", encoding="utf-8") as f:
        for line in found_lines:
            if line not in found_seen:
                f.write(line + "\n")
                found_seen.add(line)
    with open(NOT_FOUND_FILE, "a", encoding="utf-8") as f:
        for name in not_found:
            if name not in not_found_seen:
                f.write(name + "\n")
                not_found_seen.add(name)

    print("KESZ", flush=True)


if __name__ == "__main__":
    main()
