import re
import unicodedata
from typing import Dict, List, Tuple, Optional

import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


OUTPUT_FILE = "New Text Document.txt"
UNITS_FILE = "units.csv"
USE_SELENIUM_FALLBACK = False
SELENIUM_WAIT_SECONDS = 6.0

CATEGORY_URLS: Dict[str, str] = {
    "Processor": "https://www.arukereso.hu/processzor-c3139/?sgst=1",
    "Memory Module": "https://www.arukereso.hu/memoria-modul-c3577/?sgst=1",
    "Motherboard": "https://www.arukereso.hu/alaplap-c3128/?sgst=1",
    "Graphics Card": "https://www.arukereso.hu/videokartya-c3142/?sgst=1",
    "Storage": "https://belso-ssd-meghajto.arukereso.hu/?sgst=1",
    "Power Supply": "https://www.arukereso.hu/tapegyseg-c3158/?sgst=1",
    "Cooling": "https://www.arukereso.hu/szamitogep-huto-c3094/?sgst=1",
    "Monitor": "https://www.arukereso.hu/monitor-c3126/?sgst=1",
    "Mouse": "https://eger.arukereso.hu/?sgst=1",
    "Case": "https://www.arukereso.hu/szamitogep-haz-c3085/?sgst=1",
    "Case Fan": "https://szamitogep-huto-ventilator.arukereso.hu/?sgst=1",
    "Keyboard": "https://www.arukereso.hu/billentyuzet-c3111/?sgst=1",
    "Webcam": "https://www.arukereso.hu/webkamera-c3113/?sgst=1",
    "Headset": "https://www.arukereso.hu/fulhallgato-fejhallgato-c3109/?sgst=1",
    "Speaker": "https://www.arukereso.hu/hangfal-c3161/?sgst=1",
    "Accessory": "https://egyeb-szamitogep-kiegeszito.arukereso.hu/?sgst=1",
}

FALLBACK_PARAM: Dict[str, str] = {
    "Processor": "Architecture",
    "Memory Module": "Memory Type",
    "Motherboard": "Socket",
    "Graphics Card": "DirectX Version",
    "Storage": "Connectivity Technology",
    "Power Supply": "Efficiency Rating",
    "Cooling": "Cooling",
    "Monitor": "Resolution",
    "Mouse": "Connectivity Technology",
    "Case": "Type",
    "Case Fan": "Fan Size",
    "Keyboard": "Switch Type",
    "Webcam": "Resolution",
    "Headset": "Microphone",
    "Speaker": "Wattage",
    "Accessory": "Material",
}

# parameter -> unit, from ParameterSeeder.php
CATEGORY_PARAMS: Dict[str, List[str]] = {
    "Processor": [
        "Clock Speed",
        "Turbo Clock Speed",
        "Core Count",
        "Thread Count",
        "L2 Cache Size",
        "L3 Cache Size",
        "Thermal Design Power (TDP)",
        "Integrated Graphics",
    ],
    "Memory Module": [
        "Memory Capacity",
        "Memory Type",
        "Bus Speed",
        "CAS Latency",
    ],
    "Motherboard": [
        "Socket",
        "Chipset",
        "Form Factor",
        "Memory Slots",
        "M.2 Slots",
        "Max Memory",
        "Memory Type",
        "PCIe Slots",
        "Wireless Networking",
        "RAID Support",
    ],
    "Graphics Card": [
        "VRAM",
        "Core Clock",
        "Boost Clock",
        "Memory Clock",
        "CUDA Cores",
        "DirectX Version",
        "Thermal Design Power (TDP)",
        "Cooling Fans",
        "Length",
        "Memory Type",
        "Video Chipset Family",
    ],
    "Storage": [
        "Capacity",
        "Cache",
        "Maximum Read Speed",
        "Maximum Write Speed",
        "Connectivity Technology",
    ],
    "Power Supply": [
        "Wattage",
        "Efficiency Rating",
        "Modular",
        "Wattage",
        "Color",
    ],
    "Cooling": [
        "Color",
        "Lighting",
        "Cooling",
        "Radiator Size",
        "Fan RPM",
        "Noise Level",
        "CPU Socket",
    ],
    "Monitor": [
        "Screen Size",
        "Resolution",
        "Refresh Rate",
        "Panel Type",
    ],
    "Mouse": [
        "Color",
        "Connectivity Technology",
        "DPI",
        "Wireless",
        "Battery Life",
    ],
    "Case": [
        "Type",
        "Dimensions",
        "Color",
        "Side Panel",
        "Max GPU Length",
        "Drive Bays",
        "Radiator Support",
        "Motherboard Form Factor",
        "Warranty",
    ],
    "Case Fan": [
        "Color",
        "Fan Size",
        "Fan height",
        "Fan RPM",
        "Noise Level",
        "Fan Connectors",
        "Warranty",
    ],
    "Keyboard": [
        "Color",
        "Weight",
        "Backlight",
        "Key Amounts",
        "Compatible",
    ],
    "Webcam": [
        "Resolution",
        "Connectivity Technology",
        "Focus Type",
        "FOV Angle",
    ],
    "Headset": [
        "Coldor",
        "Data transfer",
        "Connection",
        "Min. Frequency",
        "Max. Frequency",
        "Sensitivity",
        "Microphone",
        "Active Noise Cancelling",
        "Impedance",
    ],
    "Speaker": [
        "Color",
        "Frequency Range",
        "Tweeter",
        "Wattage",
        "Crossover Frequency",
        "Woofer Size",
        "Power Output",
        "Bass Reflex System",
    ],
    "Accessory": [
        "Length",
        "Material",
        "Max Load",
        "Thermal Conductivity",
        "Ports",
        "Torque",
        "Connection Type",
        "Dimensions",
    ],
}

PARAM_UNITS: Dict[str, str] = {
    # Processor
    "Clock Speed": "MHz",
    "Turbo Clock Speed": "MHz",
    "Core Count": "Pcs",
    "Thread Count": "Pcs",
    "L2 Cache Size": "MB",
    "L3 Cache Size": "MB",
    "Thermal Design Power (TDP)": "W",
    "Architecture": "N/A",
    "Integrated Graphics": "Type",
    # Memory Module
    "Memory Capacity": "GB",
    "Memory Type": "N/A",
    "Bus Speed": "MHz",
    "CAS Latency": "CL",
    # Motherboard
    "Socket": "N/A",
    "Chipset": "N/A",
    "Form Factor": "N/A",
    "Memory Slots": "Pcs",
    "M.2 Slots": "Pcs",
    "Max Memory": "GB",
    "PCIe Slots": "Pcs",
    "Wireless Networking": "N/A",
    "RAID Support": "Yes/No",
    # Graphics Card
    "VRAM": "GB",
    "Core Clock": "MHz",
    "Boost Clock": "MHz",
    "Memory Clock": "MHz",
    "CUDA Cores": "Pcs",
    "DirectX Version": "N/A",
    "Cooling Fans": "Pcs",
    "Length": "mm",
    "Memory Type": "Type",
    "Video Chipset Family": "Type",
    # Storage
    "Capacity": "TB",
    "Cache": "MB",
    "Maximum Read Speed": "MB/s",
    "Maximum Write Speed": "MB/s",
    "Connectivity Technology": "N/A",
    # Power Supply
    "Wattage": "W",
    "Efficiency Rating": "N/A",
    "Modular": "Full",
    "Color": "Color",
    # Cooling
    "Lighting": "Color",
    "Cooling": "Cooled",
    "Radiator Size": "mm",
    "Fan RPM": "RPM",
    "Noise Level": "dB",
    "CPU Socket": "-",
    # Monitor
    "Screen Size": "inch",
    "Resolution": "N/A",
    "Refresh Rate": "Hz",
    "Panel Type": "N/A",
    # Mouse
    "DPI": "DPI",
    "Wireless": "Yes/No",
    "Battery Life": "Hour",
    # Case
    "Type": "Tower",
    "Dimensions": "mm",
    "Side Panel": "Material",
    "Max GPU Length": "mm",
    "Drive Bays": "Pcs",
    "Radiator Support": "mm",
    "Motherboard Form Factor": "-",
    "Warranty": "Year",
    # Case Fan
    "Fan Size": "mm",
    "Fan height": "mm",
    "Fan Connectors": "4 pin",
    # Keyboard
    "Switch Type": "-",
    "Mounting Type": "-",
    "Weight": "g",
    "Battery Capacity": "mAh",
    "Backlight": "-",
    "Key Amounts": "Pcs",
    "Compatible": "-",
    "Layout": "-",
    "Mechanical": "Yes/No",
    # Webcam
    "Focus Type": "-",
    "FOV Angle": "°",
    # Headset
    "Coldor": "-",
    "Frequency Range": "kHz",
    "Microphone": "Yes/No",
    "Active Noise Cancelling": "Yes/No",
    "Impedance": "Ω",
    # Speaker
    "Tweeter": "Teszt",
    "Crossover Frequency": "kHz",
    "Woofer Size": "Teszt",
    "Power Output": "W",
    "Bass Reflex System": "Yes/No",
    # Accessory
    "Length": "m",
    "Material": "-",
    "Max Load": "kg",
    "Thermal Conductivity": "W/mK",
    "Ports": "Pcs",
    "Torque": "nm",
    "Connection Type": "-",
}


def norm_text(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"\s+", " ", t).strip()
    return t


def first_number(text: str) -> str | None:
    m = re.search(r"[-+]?\d+(?:[.,]\d+)?", text)
    if not m:
        return None
    num = m.group(0).replace(",", ".")
    return num


def yes_no_from_text(text: str) -> str:
    t = norm_text(text)
    if any(x in t for x in ["igen", "van", "tamagat", "supported", "yes"]):
        return "Yes"
    if any(x in t for x in ["nem", "nincs", "not", "no", "unsupported"]):
        return "No"
    return text.strip()


def load_units(path: str) -> set[str]:
    units = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.lower().startswith("id;"):
                    continue
                parts = line.split(";")
                if len(parts) < 2:
                    continue
                unit = parts[1].strip()
                if unit:
                    units.add(unit)
    except Exception:
        return set()
    return units


def resolve_unit(param_name: str, unit_set: set[str]) -> str:
    unit = PARAM_UNITS.get(param_name, "N/A")
    if not unit_set:
        return unit
    if unit not in unit_set:
        return "N/A"
    return unit


def convert_value(param_name: str, raw_value: str, unit_set: set[str]) -> str:
    unit = resolve_unit(param_name, unit_set)
    v = raw_value.replace("\xa0", " ").strip()
    v_norm = norm_text(v)

    if unit in {"Yes/No"}:
        return yes_no_from_text(v)

    if param_name == "CAS Latency":
        v_norm = v_norm.replace("cl", "")
        num = first_number(v_norm)
        return num or v.strip()

    if param_name == "Capacity":
        num = first_number(v_norm)
        if not num:
            return v.strip()
        val = float(num)
        if "gb" in v_norm and "tb" not in v_norm:
            val = val / 1000.0
        if abs(val - round(val)) < 1e-6:
            return str(int(round(val)))
        return f"{val:.2f}".rstrip("0").rstrip(".")

    if unit in {"MHz", "GB", "MB", "W", "mm", "dB", "Hz", "RPM", "g", "mAh", "TB", "kHz", "Ω", "Year", "Pcs", "Hour", "nm", "m", "kg", "W/mK", "DPI"}:
        num = first_number(v_norm)
        return num or v.strip()

    return v.strip()


def map_specs(category: str, specs: Dict[str, str], unit_set: set[str]) -> List[Tuple[str, str]]:
    mapped: List[Tuple[str, str]] = []
    present = set()

    for hu_label, raw_val in specs.items():
        param = map_label_to_param(category, hu_label)
        if not param:
            continue
        value = translate_value(raw_val)
        value = convert_value(param, value, unit_set)
        mapped.append((param, value))
        present.add(param)

    # Ensure required params exist; use N/A for missing values
    for req in CATEGORY_PARAMS.get(category, []):
        if req not in present:
            mapped.append((req, "N/A"))

    return [(p, v) for p, v in mapped if v]


def fetch_html(session: requests.Session, url: str) -> str:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def parse_top20_from_category(html: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    items: Dict[int, Tuple[str, str]] = {}
    for box in soup.select("div.product-box"):
        place_el = box.select_one(".badge-top-item-wrapper .place")
        if not place_el:
            continue
        place_txt = place_el.get_text(strip=True)
        if not place_txt.isdigit():
            continue
        place = int(place_txt)
        if place < 1 or place > 20:
            continue
        name_el = box.select_one(".name h2 a")
        if not name_el:
            continue
        name = name_el.get("title") or name_el.get_text(strip=True)
        name = name.strip()
        if not name:
            continue
        url = name_el.get("href") or ""
        if url and url.startswith("/"):
            url = "https://www.arukereso.hu" + url
        if url and "arukereso.hu" not in url:
            # Try to find an arukereso product page link in the box
            url = ""
            for a in box.find_all("a", href=True):
                href = a["href"]
                if "arukereso.hu" in href:
                    url = href
                    break
        items[place] = (name, url)

    return [items[p] for p in sorted(items.keys()) if p <= 20]


def clean_product_name(name: str) -> str:
    # Drop trailing Hungarian category words for cleaner English name.
    suffixes = [
        "processzor",
        "videokartya",
        "videókártya",
        "alaplap",
        "memoria",
        "memória",
        "tapegyseg",
        "tápegység",
        "haz",
        "ház",
        "billentyuzet",
        "billentyűzet",
        "eger",
        "egér",
        "monitor",
        "hangfal",
        "fejhallgato",
        "fejhallgató",
        "webkamera",
        "hutoventilator",
        "hűtőventilátor",
        "huto",
        "hűtő",
        "ssd",
    ]
    n = name.strip()
    n_low = norm_text(n)
    for suf in suffixes:
        if n_low.endswith(" " + suf) or n_low.endswith("-" + suf):
            return n[: -(len(suf) + 1)].strip()
    return n


HU_VALUE_MAP = {
    "igen": "Yes",
    "nem": "No",
    "nincs": "No",
    "van": "Yes",
    "fekete": "Black",
    "feher": "White",
    "fehér": "White",
    "piros": "Red",
    "kek": "Blue",
    "kék": "Blue",
    "zold": "Green",
    "zöld": "Green",
    "szurke": "Gray",
    "szürke": "Gray",
    "ezust": "Silver",
    "ezüst": "Silver",
    "arany": "Gold",
    "barna": "Brown",
    "sarga": "Yellow",
    "sárga": "Yellow",
    "narancs": "Orange",
    "lila": "Purple",
    "rozsaszin": "Pink",
    "rózsaszín": "Pink",
    "magyar": "Hungarian",
}

VALUE_PART_MAP = {
    "radiofrekvencias": "Radio Frequency",
    "rádiófrekvenciás": "Radio Frequency",
    "vezetek nelkuli": "Wireless",
    "vezeték nélküli": "Wireless",
    "bluetooth": "Bluetooth",
    "usb": "USB",
}


def translate_value(v: str) -> str:
    t = v.strip()
    if "/" in t:
        parts = [p.strip() for p in t.split("/")]
        mapped = []
        for p in parts:
            key = norm_text(p)
            mapped.append(VALUE_PART_MAP.get(key, p))
        t = "/".join(mapped)
    low = norm_text(t)
    if low in HU_VALUE_MAP:
        return HU_VALUE_MAP[low]
    return t


LABEL_MAP_COMMON = {
    "szin": "Color",
    "szín": "Color",
    "színváltozat": "Color",
    "csatlakozok": "Connectivity Technology",
    "csatlakozók": "Connectivity Technology",
    "csatlakozo": "Connectivity Technology",
    "csatlakozó": "Connectivity Technology",
    "vezeték nélküli": "Wireless",
    "vezetek nelkuli": "Wireless",
    "felbontas": "Resolution",
    "felbontás": "Resolution",
    "frissitesi frekvencia": "Refresh Rate",
    "frissítési frekvencia": "Refresh Rate",
    "panel": "Panel Type",
    "dpi": "DPI",
    "suly": "Weight",
    "súly": "Weight",
    "gombok szama": "Key Amounts",
    "gombok száma": "Key Amounts",
    "garancia": "Warranty",
}


LABEL_MAP_BY_CATEGORY: Dict[str, Dict[str, str]] = {
    "Processor": {
        "orajel": "Clock Speed",
        "alap orajel": "Clock Speed",
        "turbo orajel": "Turbo Clock Speed",
        "max orajel": "Turbo Clock Speed",
        "processzor orajel": "Clock Speed",
        "processzor órajel": "Clock Speed",
        "processzor turbo orajel": "Turbo Clock Speed",
        "processzor turbo órajel": "Turbo Clock Speed",
        "magok szama": "Core Count",
        "szalak szama": "Thread Count",
        "l2 gyorsito": "L2 Cache Size",
        "l2 gyorsító": "L2 Cache Size",
        "l2 cache": "L2 Cache Size",
        "l3 gyorsito": "L3 Cache Size",
        "l3 gyorsító": "L3 Cache Size",
        "l3 cache": "L3 Cache Size",
        "tdp": "Thermal Design Power (TDP)",
        "architektura": "Architecture",
        "architektúra": "Architecture",
        "integralt grafikai processzor": "Integrated Graphics",
        "integrált grafikai processzor": "Integrated Graphics",
    },
    "Memory Module": {
        "kapacitas": "Memory Capacity",
        "kapacitás": "Memory Capacity",
        "memoria tipusa": "Memory Type",
        "memória típusa": "Memory Type",
        "orajel": "Bus Speed",
        "cas latency": "CAS Latency",
        "cas kesleltetes": "CAS Latency",
        "cas késleltetés": "CAS Latency",
    },
    "Motherboard": {
        "foglalat": "Socket",
        "chipset": "Chipset",
        "formatum": "Form Factor",
        "memoria foglalatok": "Memory Slots",
        "memória foglalatok": "Memory Slots",
        "m.2": "M.2 Slots",
        "max memoria": "Max Memory",
        "memoria tipusa": "Memory Type",
        "pci-e": "PCIe Slots",
        "pcie": "PCIe Slots",
        "vezetek nelkuli halozat": "Wireless Networking",
        "vezeték nélküli hálózat": "Wireless Networking",
        "raid": "RAID Support",
    },
    "Graphics Card": {
        "memoria merete": "VRAM",
        "memória mérete": "VRAM",
        "gpu orajel": "Core Clock",
        "gpu órajel": "Core Clock",
        "boost orajel": "Boost Clock",
        "boost órajel": "Boost Clock",
        "memoria orajel": "Memory Clock",
        "memória órajel": "Memory Clock",
        "cuda magok": "CUDA Cores",
        "directx": "DirectX Version",
        "tdp": "Thermal Design Power (TDP)",
        "ventilatorok szama": "Cooling Fans",
        "ventilátorok száma": "Cooling Fans",
        "hosszusag": "Length",
        "hosszúság": "Length",
        "memoria tipusa": "Memory Type",
        "memória típusa": "Memory Type",
        "video chipset termekcsalad": "Video Chipset Family",
        "videó chipset termékcsalád": "Video Chipset Family",
        "video chipset": "Video Chipset Family",
    },
    "Storage": {
        "kapacitas": "Capacity",
        "kapacitás": "Capacity",
        "cache": "Cache",
        "maximalis ssd olvasasi sebesseg": "Maximum Read Speed",
        "maximális ssd olvasási sebesség": "Maximum Read Speed",
        "maximalis ssd irasi sebesseg": "Maximum Write Speed",
        "maximális ssd írási sebesség": "Maximum Write Speed",
        "csatlakozok": "Connectivity Technology",
        "csatlakozók": "Connectivity Technology",
        "interfesz": "Connectivity Technology",
        "interfész": "Connectivity Technology",
    },
    "Power Supply": {
        "teljesitmeny": "Wattage",
        "teljesítmény": "Wattage",
        "hatasfok": "Efficiency Rating",
        "hatásfok": "Efficiency Rating",
        "modularis": "Modular",
        "moduláris": "Modular",
        "szin": "Color",
        "szín": "Color",
    },
    "Cooling": {
        "szin": "Color",
        "szín": "Color",
        "vilagitas": "Lighting",
        "világítás": "Lighting",
        "hutes tipusa": "Cooling",
        "hűtés típusa": "Cooling",
        "radiator meret": "Radiator Size",
        "radiátor méret": "Radiator Size",
        "fordulatszam": "Fan RPM",
        "fordulatszám": "Fan RPM",
        "zajszint": "Noise Level",
        "cpu foglalat": "CPU Socket",
    },
    "Monitor": {
        "kepernyo meret": "Screen Size",
        "képernyő méret": "Screen Size",
        "felbontas": "Resolution",
        "felbontás": "Resolution",
        "frissitesi frekvencia": "Refresh Rate",
        "frissítési frekvencia": "Refresh Rate",
        "panel tipus": "Panel Type",
        "panel típus": "Panel Type",
    },
    "Mouse": {
        "szin": "Color",
        "szín": "Color",
        "csatlakozas": "Connectivity Technology",
        "csatlakozás": "Connectivity Technology",
        "billentyuzet csatlakoztatasa": "Connectivity Technology",
        "billentyűzet csatlakoztatása": "Connectivity Technology",
        "kiosztas": "Layout",
        "kiosztás": "Layout",
        "mechanikus": "Mechanical",
        "dpi": "DPI",
        "vezetek nelkuli": "Wireless",
        "vezeték nélküli": "Wireless",
        "akkumulator uzemido": "Battery Life",
        "akkumulátor üzemidő": "Battery Life",
    },
    "Case": {
        "tipus": "Type",
        "típus": "Type",
        "meret": "Dimensions",
        "méret": "Dimensions",
        "szin": "Color",
        "szín": "Color",
        "oldallap": "Side Panel",
        "max vga hossz": "Max GPU Length",
        "max gpu hossz": "Max GPU Length",
        "meghajtohelyek": "Drive Bays",
        "meghajtóhelyek": "Drive Bays",
        "radiator tamogatas": "Radiator Support",
        "radiátor támogatás": "Radiator Support",
        "alaplap formatum": "Motherboard Form Factor",
        "alaplap formátum": "Motherboard Form Factor",
        "garancia": "Warranty",
    },
    "Case Fan": {
        "szin": "Color",
        "szín": "Color",
        "meret": "Fan Size",
        "méret": "Fan Size",
        "magassag": "Fan height",
        "magasság": "Fan height",
        "fordulatszam": "Fan RPM",
        "fordulatszám": "Fan RPM",
        "zajszint": "Noise Level",
        "csatlakozo": "Fan Connectors",
        "csatlakozó": "Fan Connectors",
        "garancia": "Warranty",
    },
    "Keyboard": {
        "szin": "Color",
        "szín": "Color",
        "kapcsolo": "Switch Type",
        "kapcsoló": "Switch Type",
        "rogzites": "Mounting Type",
        "rögzítés": "Mounting Type",
        "suly": "Weight",
        "súly": "Weight",
        "akku": "Battery Capacity",
        "hattervilagitas": "Backlight",
        "háttérvilágítás": "Backlight",
        "gombok szama": "Key Amounts",
        "gombok száma": "Key Amounts",
        "kompatibilis": "Compatible",
        "csatlakozas": "Connectivity Technology",
        "csatlakozás": "Connectivity Technology",
    },
    "Webcam": {
        "felbontas": "Resolution",
        "felbontás": "Resolution",
        "csatlakozas": "Connectivity Technology",
        "csatlakozás": "Connectivity Technology",
        "fokusz": "Focus Type",
        "latozog": "FOV Angle",
        "látószög": "FOV Angle",
    },
    "Headset": {
        "szin": "Coldor",
        "szín": "Coldor",
        "frekvencia": "Frequency Range",
        "mikrofon": "Microphone",
        "aktiv zajszures": "Active Noise Cancelling",
        "aktív zajszűrés": "Active Noise Cancelling",
        "impedancia": "Impedance",
    },
    "Speaker": {
        "szin": "Color",
        "szín": "Color",
        "frekvencia": "Frequency Range",
        "tweeter": "Tweeter",
        "teljesitmeny": "Wattage",
        "teljesítmény": "Wattage",
        "valtofrekvencia": "Crossover Frequency",
        "váltófrekvencia": "Crossover Frequency",
        "woofer": "Woofer Size",
        "kimeneti teljesitmeny": "Power Output",
        "kimeneti teljesítmény": "Power Output",
        "bass reflex": "Bass Reflex System",
    },
    "Accessory": {
        "hossz": "Length",
        "anyag": "Material",
        "max terheles": "Max Load",
        "max terhelés": "Max Load",
        "hoszallitas": "Thermal Conductivity",
        "hőszállítás": "Thermal Conductivity",
        "portok": "Ports",
        "nyomatek": "Torque",
        "nyomaték": "Torque",
        "csatlakozas": "Connection Type",
        "csatlakozás": "Connection Type",
        "meret": "Dimensions",
        "méret": "Dimensions",
    },
}


def normalize_label(label: str) -> str:
    return norm_text(label)


def map_label_to_param(category: str, label: str) -> Optional[str]:
    n = normalize_label(label)
    cat_map = LABEL_MAP_BY_CATEGORY.get(category, {})
    if n in cat_map:
        return cat_map[n]
    if n in LABEL_MAP_COMMON:
        return LABEL_MAP_COMMON[n]
    # Fuzzy: find a key contained in label
    for k, v in cat_map.items():
        if k in n:
            return v
    for k, v in LABEL_MAP_COMMON.items():
        if k in n:
            return v
    return None


def fetch_detail_specs(session: requests.Session, url: str) -> Dict[str, str]:
    if not url:
        return {}
    try:
        html = fetch_html(session, url)
    except Exception:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    specs: Dict[str, str] = {}
    # Product properties (often present in description tab)
    for row in soup.select("table.product-properties tr"):
        name_el = row.select_one("td.prop-name")
        tds = row.select("td")
        if not name_el or not tds:
            continue
        val_el = tds[-1]
        label = name_el.get_text(" ", strip=True)
        value = val_el.get_text(" ", strip=True)
        label = re.sub(r"\s+", " ", label).strip()
        value = re.sub(r"\s+", " ", value).strip()
        if label and value and label not in specs:
            specs[label] = value

    # Detailed property sheet (if present)
    for table in soup.select("table.property-sheet"):
        for row in table.select("tr"):
            name_el = row.select_one("td.property-name")
            val_el = row.select_one("td.property-value")
            if not name_el or not val_el:
                continue
            label = name_el.get_text(" ", strip=True)
            value = val_el.get_text(" ", strip=True)
            label = re.sub(r"\s+", " ", label).strip()
            value = re.sub(r"\s+", " ", value).strip()
            if label and value and label not in specs:
                specs[label] = value
        if specs:
            break
    return specs


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


def fetch_detail_specs_selenium(driver: webdriver.Chrome, url: str) -> Dict[str, str]:
    if not url:
        return {}
    try:
        driver.get(url + "#termek-leiras")
    except Exception:
        return {}
    specs: Dict[str, str] = {}
    end_time = time.time() + SELENIUM_WAIT_SECONDS
    while time.time() < end_time:
        try:
            # Try to switch to description tab if present
            tab = driver.find_elements(
                "css selector",
                "a[data-tab='description'], a[data-tab-name='termek-leiras'], a[href*='termek-leiras']",
            )
            if tab:
                tab[0].click()
        except Exception:
            pass

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for row in soup.select("table.product-properties tr"):
            name_el = row.select_one("td.prop-name")
            tds = row.select("td")
            if not name_el or not tds:
                continue
            val_el = tds[-1]
            label = name_el.get_text(" ", strip=True)
            value = val_el.get_text(" ", strip=True)
            label = re.sub(r"\s+", " ", label).strip()
            value = re.sub(r"\s+", " ", value).strip()
            if label and value and label not in specs:
                specs[label] = value

        for table in soup.select("table.property-sheet"):
            for row in table.select("tr"):
                name_el = row.select_one("td.property-name")
                val_el = row.select_one("td.property-value")
                if not name_el or not val_el:
                    continue
                label = name_el.get_text(" ", strip=True)
                value = val_el.get_text(" ", strip=True)
                label = re.sub(r"\s+", " ", label).strip()
                value = re.sub(r"\s+", " ", value).strip()
                if label and value and label not in specs:
                    specs[label] = value
            if specs:
                return specs
        time.sleep(0.6)
    return specs


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    )

    lines: List[str] = ["product_name;parameter_name;value"]
    unit_set = load_units(UNITS_FILE)

    driver = setup_driver() if USE_SELENIUM_FALLBACK else None

    for category, url in CATEGORY_URLS.items():
        print(f"[category] {category} -> {url}", flush=True)
        html = fetch_html(session, url)
        top_items = parse_top20_from_category(html)
        print(f"  top items: {len(top_items)}", flush=True)
        for name, url in top_items:
            print(f"  - {name}", flush=True)
            specs = fetch_detail_specs(session, url)
            if not specs and USE_SELENIUM_FALLBACK and driver is not None:
                specs = fetch_detail_specs_selenium(driver, url)
            mapped = map_specs(category, specs, unit_set)
            product_name = clean_product_name(name)
            if not mapped:
                # Ensure each product appears at least once with a fallback parameter if possible
                fallback = FALLBACK_PARAM.get(category, "Material")
                lines.append(f"{product_name};{fallback};N/A")
                continue
            for param_name, value in mapped:
                lines.append(f"{product_name};{param_name};{value}")

    if driver is not None:
        driver.quit()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
