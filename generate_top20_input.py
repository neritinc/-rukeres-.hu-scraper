import re
import sys
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
OUTPUT_PRODUCTS_FILE = "products.txt"
UNITS_FILE = "units.csv"
USE_SELENIUM_FALLBACK = True
SELENIUM_WAIT_SECONDS = 12.0

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
    "Processor": "Type",
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
        "Type",
        "Core Count",
        "Thread Count",
        "Socket",
        "Clock Speed",
        "Turbo Clock Speed",
        "Manufacturing Process",
        "Integrated Graphics",
        "L2 Cache Size",
        "L3 Cache Size",
        "Thermal Design Power (TDP)",
        "Package",
    ],
    "Memory Module": [
        "Capacity",
        "Package",
        "Memory Type",
        "Speed",
        "Multi-channel Package",
        "Memory Latency",
        "LED Lighting",
    ],
    "Motherboard": [
        "Socket",
        "Chipset",
        "CPU Manufacturer",
        "Memory Type",
        "Memory Slots",
        "SATA 3 Ports",
        "M.2 Slots",
        "USB Ports",
        "Form Factor",
    ],
    "Graphics Card": [
        "PCIe Generation",
        "Cooling Fans",
        "Core Clock",
        "Memory Clock",
        "VRAM",
        "Memory Type",
        "Memory Bus",
        "Recommended PSU",
        "Max Resolution",
        "HDMI Ports",
        "DisplayPort Ports",
    ],
    "Storage": [
        "Capacity",
        "Cache",
        "Maximum Read Speed",
        "Maximum Write Speed",
        "Connectivity Technology",
    ],
    "Power Supply": [
        "PSU Type",
        "Wattage",
        "Efficiency Rating",
        "Fan Size",
        "SATA Connectors",
        "PCIe Connectors",
    ],
    "Cooling": [
        "Type",
        "Fan Diameter",
        "Fan RPM",
        "LED Lighting",
        "Dimensions",
        "Weight",
    ],
    "Monitor": [
        "Type",
        "Screen Size",
        "Aspect Ratio",
        "Resolution",
        "Response Time",
        "Refresh Rate",
        "Speakers",
        "AMD FreeSync",
        "Nvidia G-Sync",
    ],
    "Mouse": [
        "Signal",
        "Connectivity Technology",
        "DPI",
        "Key Amounts",
        "Color",
        "Weight",
    ],
    "Case": [
        "Type",
        "Width",
        "Height",
        "Depth",
        "Weight",
        "2.5\" Bays",
        "3.5\" Bays",
        "USB Ports",
        "Transparent Side Panel",
        "Color",
        "ATX Support",
        "Micro ATX Support",
        "Extended ATX Support",
        "Mini ITX Support",
    ],
    "Case Fan": [
        "Fan Diameter",
        "Fan RPM",
        "Noise Level",
        "Airflow",
        "PWM",
        "Connector",
        "LED Lighting",
        "Dimensions",
        "Weight",
    ],
    "Keyboard": [
        "Color",
        "Weight",
        "Backlight",
        "Key Amounts",
        "Compatible",
    ],
    "Webcam": [
        "Microphone",
        "Max FPS",
        "Video Resolution",
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
    "Type": "Type",
    "Clock Speed": "MHz",
    "Turbo Clock Speed": "MHz",
    "Core Count": "Pcs",
    "Thread Count": "Pcs",
    "L2 Cache Size": "MB",
    "L3 Cache Size": "MB",
    "Socket": "N/A",
    "Manufacturing Process": "nm",
    "Integrated Graphics": "Type",
    "Package": "Type",
    "Thermal Design Power (TDP)": "W",
    "Architecture": "N/A",
    # Memory Module
    "Capacity": "GB",
    "Package": "Type",
    "Memory Type": "N/A",
    "Speed": "MHz",
    "Multi-channel Package": "Type",
    "Memory Latency": "CL",
    "LED Lighting": "Yes/No",
    # Motherboard
    "Socket": "N/A",
    "Chipset": "N/A",
    "CPU Manufacturer": "N/A",
    "Memory Type": "N/A",
    "Memory Slots": "Pcs",
    "SATA 3 Ports": "Pcs",
    "M.2 Slots": "Pcs",
    "USB Ports": "Pcs",
    "Form Factor": "N/A",
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
    "PSU Type": "Type",
    "Wattage": "W",
    "Efficiency Rating": "N/A",
    "Fan Size": "mm",
    "SATA Connectors": "Pcs",
    "PCIe Connectors": "Pcs",
    # Cooling
    "Type": "N/A",
    "Fan Diameter": "mm",
    "Fan RPM": "RPM",
    "LED Lighting": "Yes/No",
    "Dimensions": "mm",
    "Weight": "g",
    # Monitor
    "Type": "N/A",
    "Screen Size": "inch",
    "Aspect Ratio": "N/A",
    "Resolution": "N/A",
    "Response Time": "ms",
    "Refresh Rate": "Hz",
    "Speakers": "Yes/No",
    "AMD FreeSync": "Yes/No",
    "Nvidia G-Sync": "Yes/No",
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


def convert_value(category: str, param_name: str, raw_value: str, unit_set: set[str]) -> str:
    unit = resolve_unit(param_name, unit_set)
    v = raw_value.replace("\xa0", " ").strip()
    v_norm = norm_text(v)

    if unit in {"Yes/No"}:
        return yes_no_from_text(v)

    if param_name in {"CAS Latency", "Memory Latency"}:
        v_norm = v_norm.replace("cl", "")
        num = first_number(v_norm)
        return num or v.strip()

    if param_name == "Capacity":
        num = first_number(v_norm)
        if not num:
            return v.strip()
        val = float(num)
        # Storage uses TB; memory modules should keep GB.
        if category == "Storage":
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
        # Keep only parameters explicitly requested for this category.
        if param not in CATEGORY_PARAMS.get(category, []):
            continue
        value = translate_value(raw_val)
        value = convert_value(category, param, value, unit_set)
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
        "tipus": "Type",
        "magok szama": "Core Count",
        "szalak szama": "Thread Count",
        "processzor foglalat": "Socket",
        "orajel": "Clock Speed",
        "alap orajel": "Clock Speed",
        "processzor orajel": "Clock Speed",
        "turbo orajel": "Turbo Clock Speed",
        "max orajel": "Turbo Clock Speed",
        "processzor turbo orajel": "Turbo Clock Speed",
        "gyartasi technologia": "Manufacturing Process",
        "integralt grafikai processzor": "Integrated Graphics",
        "l2 cache": "L2 Cache Size",
        "l2 gyorsito": "L2 Cache Size",
        "l3 cache": "L3 Cache Size",
        "l3 gyorsito": "L3 Cache Size",
        "tdp": "Thermal Design Power (TDP)",
        "kiszereles": "Package",
    },
    "Memory Module": {
        "kapacitas": "Capacity",
        "kiszereles": "Package",
        "memoria tipusa": "Memory Type",
        "sebesseg": "Speed",
        "orajel": "Speed",
        "tobbcsatornas kiszereles": "Multi-channel Package",
        "memoriakesleltetes": "Memory Latency",
        "led megvilagitas": "LED Lighting",
    },

    "Motherboard": {
        "cpu foglalat": "Socket",
        "foglalat": "Socket",
        "chipset": "Chipset",
        "processzor gyarto": "CPU Manufacturer",
        "memoria tipusa": "Memory Type",
        "memoria foglalatok szama": "Memory Slots",
        "sata 3 csatlakozok szama": "SATA 3 Ports",
        "m.2 csatlakozok szama": "M.2 Slots",
        "usb portok szama": "USB Ports",
        "meret szabvany": "Form Factor",
    },

    "Graphics Card": {
        "pci-e generacio": "PCIe Generation",
        "pcie generacio": "PCIe Generation",
        "ventilatorok szama": "Cooling Fans",
        "grafikus chip sebessege": "Core Clock",
        "grafikus mem?ria sebessege": "Memory Clock",
        "grafikus memoria sebessege": "Memory Clock",
        "memoria merete": "VRAM",
        "memoria tipusa": "Memory Type",
        "memoria savszelesseg": "Memory Bus",
        "ajanlott tapegyseg": "Recommended PSU",
        "maximalis felbontas": "Max Resolution",
        "hdmi csatlakozok szama": "HDMI Ports",
        "displayport csatlakozok szama": "DisplayPort Ports",
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
        "tapegyseg tipusa": "PSU Type",
        "tapegyseg teljesitmenye": "Wattage",
        "hatasfok": "Efficiency Rating",
        "ventilator merete": "Fan Size",
        "sata csatlakozo": "SATA Connectors",
        "sata csatlakozo szama": "SATA Connectors",
        "pci-express csatlakozo": "PCIe Connectors",
        "pci-express csatlakozo szama": "PCIe Connectors",
    },

    "Cooling": {
        "tipus": "Type",
        "ventilator atmeroje": "Fan Diameter",
        "ventilator fordulatszama": "Fan RPM",
        "led megvilagitas": "LED Lighting",
        "meretek": "Dimensions",
        "tomeg": "Weight",
    },

    "Monitor": {
        "tipus": "Type",
        "kepatlo": "Screen Size",
        "k?patlo": "Screen Size",
        "keparany": "Aspect Ratio",
        "k?parany": "Aspect Ratio",
        "felbontas": "Resolution",
        "felbont?s": "Resolution",
        "valaszido": "Response Time",
        "v?laszid?": "Response Time",
        "kepfrissitesi frekvencia": "Refresh Rate",
        "k?pfriss?t?si frekvencia": "Refresh Rate",
        "hangszoro": "Speakers",
        "hangsz?r?": "Speakers",
        "amd freesync tamogatas": "AMD FreeSync",
        "amd freesync t?mogat?s": "AMD FreeSync",
        "nvidia g-sync tamogatas": "Nvidia G-Sync",
        "nvidia g-sync t?mogat?s": "Nvidia G-Sync",
    },

    "Mouse": {
        "jelatvitel": "Signal",
        "jel?tvitel": "Signal",
        "eger csatlakoztatasa": "Connectivity Technology",
        "eg?r csatlakoztat?sa": "Connectivity Technology",
        "erzekenyseg": "DPI",
        "?rz?kenys?g": "DPI",
        "gombok szama": "Key Amounts",
        "gombok sz?ma": "Key Amounts",
        "szin": "Color",
        "sz?n": "Color",
        "tomeg": "Weight",
        "t?meg": "Weight",
    },

    "Case": {
        "tipus": "Type",
        "szelesseg": "Width",
        "magassag": "Height",
        "melyseg": "Depth",
        "tomeg": "Weight",
        "2.5\" belso bovitohely": "2.5\" Bays",
        "3.5\" belso bovitohely": "3.5\" Bays",
        "usb csatlakozok szama": "USB Ports",
        "atlatszo oldalfal": "Transparent Side Panel",
        "szin": "Color",
        "atx": "ATX Support",
        "micro atx": "Micro ATX Support",
        "extended atx": "Extended ATX Support",
        "mini itx": "Mini ITX Support",
    },

    "Case Fan": {
        "ventilator atmeroje": "Fan Diameter",
        "ventil?tor ?tm?r?je": "Fan Diameter",
        "ventilator fordulatszama": "Fan RPM",
        "ventil?tor fordulatsz?ma": "Fan RPM",
        "maximalis zajszint": "Noise Level",
        "maxim?lis zajszint": "Noise Level",
        "leveg??raml?s": "Airflow",
        "legaramlas": "Airflow",
        "pwm": "PWM",
        "csatlakozo": "Connector",
        "csatlakoz?": "Connector",
        "led megvilagitas": "LED Lighting",
        "led megvil?g?t?s": "LED Lighting",
        "meretek": "Dimensions",
        "m?retek": "Dimensions",
        "tomeg": "Weight",
        "t?meg": "Weight",
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
        "mikrofon": "Microphone",
        "maximalis kepfrissites": "Max FPS",
        "maxim?lis k?pfriss?t?s": "Max FPS",
        "videofelbontas": "Video Resolution",
        "vide?felbont?s": "Video Resolution",
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
        html = fetch_html(session, url + "#termek-leiras")
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

    # Generic property rows (some pages render these without a table class)
    for name_el in soup.select("td.property-name"):
        row = name_el.parent
        if not row:
            continue
        val_el = row.select_one("td.property-value")
        if not val_el:
            continue
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
        found_property_rows = False

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

        for name_el in soup.select("td.property-name"):
            row = name_el.parent
            if not row:
                continue
            val_el = row.select_one("td.property-value")
            if not val_el:
                continue
            label = name_el.get_text(" ", strip=True)
            value = val_el.get_text(" ", strip=True)
            label = re.sub(r"\s+", " ", label).strip()
            value = re.sub(r"\s+", " ", value).strip()
            if label and value and label not in specs:
                specs[label] = value
                found_property_rows = True

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
        if found_property_rows:
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

    # Stream output so the txt updates while running
    # Track unique products for products.txt
    products_seen = set()
    products_f = open(OUTPUT_PRODUCTS_FILE, "w", encoding="utf-8")
    out_f = open(OUTPUT_FILE, "w", encoding="utf-8")
    out_f.write("product_name;parameter_name;value\n")
    out_f.flush()
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
            if product_name not in products_seen:
                products_seen.add(product_name)
                products_f.write(product_name + "\n")
                products_f.flush()
            if not mapped:
                # Ensure each product appears at least once with a fallback parameter if possible
                fallback = FALLBACK_PARAM.get(category, "Material")
                out_f.write(f"{product_name};{fallback};N/A\n")
                out_f.flush()
                continue
            for param_name, value in mapped:
                out_f.write(f"{product_name};{param_name};{value}\n")
                out_f.flush()

    if driver is not None:
        driver.quit()

    products_f.close()
    out_f.close()


if __name__ == "__main__":
    main()
