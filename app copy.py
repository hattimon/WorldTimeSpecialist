from __future__ import annotations

import os
import re
import tkinter as tk
import unicodedata
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError
from zoneinfo import TZPATH, ZoneInfo, available_timezones


APP_TITLE = "World Time Specialist"

# Popularne, czytelne strefy pokazywane od razu po uruchomieniu.
WORLD_HIGHLIGHTS: list[tuple[str, str]] = [
    ("Warszawa", "Europe/Warsaw"),
    ("Londyn", "Europe/London"),
    ("Nowy Jork", "America/New_York"),
    ("Chicago", "America/Chicago"),
    ("Denver", "America/Denver"),
    ("Los Angeles", "America/Los_Angeles"),
    ("Sao Paulo", "America/Sao_Paulo"),
    ("Johannesburg", "Africa/Johannesburg"),
    ("Dubaj", "Asia/Dubai"),
    ("Delhi", "Asia/Kolkata"),
    ("Singapur", "Asia/Singapore"),
    ("Tokio", "Asia/Tokyo"),
    ("Sydney", "Australia/Sydney"),
    ("Auckland", "Pacific/Auckland"),
]

# Uniwersalne punkty odniesienia czasu.
UNIVERSAL_REFERENCES: list[tuple[str, str, str]] = [
    ("UTC", "Etc/UTC", "Koordynowany czas uniwersalny"),
    ("GMT/BST", "Europe/London", "Greenwich / UK"),
    ("CET/CEST", "Europe/Warsaw", "Europa Srodkowa"),
    ("EET/EEST", "Europe/Helsinki", "Europa Wschodnia"),
    ("MSK", "Europe/Moscow", "Moskwa"),
    ("EST/EDT", "America/New_York", "USA Wschod"),
    ("CST/CDT", "America/Chicago", "USA Centrum"),
    ("MST/MDT", "America/Denver", "USA Gory"),
    ("PST/PDT", "America/Los_Angeles", "USA Zachod"),
    ("IST", "Asia/Kolkata", "Indie"),
    ("CST", "Asia/Shanghai", "Chiny"),
    ("JST", "Asia/Tokyo", "Japonia"),
    ("AEST/AEDT", "Australia/Sydney", "Australia Wschod"),
]

# Dodatkowe aliasy krajow (PL/EN), aby wyszukiwanie bylo wygodne.
COUNTRY_ALIASES = {
    "polska": "PL",
    "niemcy": "DE",
    "francja": "FR",
    "hiszpania": "ES",
    "wlochy": "IT",
    "szwajcaria": "CH",
    "austria": "AT",
    "czechy": "CZ",
    "slowacja": "SK",
    "wegry": "HU",
    "ukraina": "UA",
    "litwa": "LT",
    "lotwa": "LV",
    "estonia": "EE",
    "rumunia": "RO",
    "bulgaria": "BG",
    "grecja": "GR",
    "turcja": "TR",
    "portugalia": "PT",
    "norwegia": "NO",
    "szwecja": "SE",
    "finlandia": "FI",
    "dania": "DK",
    "islandia": "IS",
    "irlandia": "IE",
    "wielka brytania": "GB",
    "anglia": "GB",
    "uk": "GB",
    "usa": "US",
    "stany zjednoczone": "US",
    "kanada": "CA",
    "meksyk": "MX",
    "brazylia": "BR",
    "argentyna": "AR",
    "chile": "CL",
    "kolumbia": "CO",
    "peru": "PE",
    "rpa": "ZA",
    "republika poludniowej afryki": "ZA",
    "egipt": "EG",
    "maroko": "MA",
    "kenia": "KE",
    "nigeria": "NG",
    "izrael": "IL",
    "arabia saudyjska": "SA",
    "zjednoczone emiraty arabskie": "AE",
    "indie": "IN",
    "chiny": "CN",
    "japonia": "JP",
    "korea poludniowa": "KR",
    "indonezja": "ID",
    "tajlandia": "TH",
    "wietnam": "VN",
    "singapur": "SG",
    "australia": "AU",
    "nowa zelandia": "NZ",
}


def normalize(text: str) -> str:
    lowered = text.casefold().strip()
    decomposed = unicodedata.normalize("NFKD", lowered)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    without_marks = without_marks.replace("_", " ").replace("/", " ")
    without_marks = re.sub(r"[^a-z0-9+\- ]+", " ", without_marks)
    return re.sub(r"\s+", " ", without_marks).strip()


def format_offset(delta: timedelta | None) -> str:
    if delta is None:
        return "UTC+00:00"
    total_minutes = int(delta.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def format_diff(delta: timedelta) -> str:
    total_minutes = int(delta.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


def day_period_label(hour: int) -> str:
    if 5 <= hour < 10:
        return "Rano"
    if 10 <= hour < 18:
        return "Dzien"
    if 18 <= hour < 22:
        return "Wieczor"
    return "Noc"


def is_dst_active(dt: datetime) -> bool:
    dst = dt.dst()
    return bool(dst and dst.total_seconds() != 0)


def seasonal_offset_description(zone_id: str, year: int) -> str:
    zone = ZoneInfo(zone_id)
    january = datetime(year, 1, 15, 12, 0, tzinfo=zone)
    july = datetime(year, 7, 15, 12, 0, tzinfo=zone)

    jan_name = january.tzname() or "-"
    jul_name = july.tzname() or "-"
    jan_off = format_offset(january.utcoffset())
    jul_off = format_offset(july.utcoffset())

    if jan_name == jul_name and jan_off == jul_off:
        return f"{jan_name} ({jan_off})"
    return f"zima: {jan_name} {jan_off} | lato: {jul_name} {jul_off}"


def _read_tab_file(filename: str) -> list[str]:
    try:
        import importlib.resources as resources

        for package, relative_parts in (
            ("tzdata.zoneinfo", [filename]),
            ("tzdata", ["zoneinfo", filename]),
        ):
            try:
                handle = resources.files(package)
                for part in relative_parts:
                    handle = handle.joinpath(part)
                if handle.is_file():
                    return handle.read_text(encoding="utf-8").splitlines()
            except (FileNotFoundError, ModuleNotFoundError, OSError):
                continue
    except (ImportError, ModuleNotFoundError):
        pass

    for tz_root in TZPATH:
        base = Path(tz_root)
        candidates = [
            base / filename,
            base / "tzdata" / filename,
            base / "zoneinfo" / filename,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8").splitlines()
    return []


def load_country_timezone_index() -> tuple[dict[str, list[str]], dict[str, str], dict[str, list[str]]]:
    code_to_country: dict[str, str] = {}
    code_to_zones: dict[str, list[str]] = {}
    country_lookup: dict[str, list[str]] = {}

    for line in _read_tab_file("iso3166.tab"):
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        code = parts[0].strip().upper()
        country_name = parts[1].strip()
        if code and country_name:
            code_to_country[code] = country_name
            country_lookup.setdefault(normalize(country_name), []).append(code)

    for line in _read_tab_file("zone1970.tab"):
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        country_codes = [segment.strip().upper() for segment in parts[0].split(",") if segment.strip()]
        zone_id = parts[2].strip()
        if not zone_id:
            continue
        for code in country_codes:
            code_to_zones.setdefault(code, []).append(zone_id)

    for alias, code in COUNTRY_ALIASES.items():
        norm_alias = normalize(alias)
        upper_code = code.upper()
        country_lookup.setdefault(norm_alias, []).append(upper_code)

    # Usuwanie duplikatow i porzadkowanie.
    normalized_lookup: dict[str, list[str]] = {}
    for key, codes in country_lookup.items():
        normalized_lookup[key] = sorted(set(codes))

    normalized_zone_map: dict[str, list[str]] = {}
    for code, zones in code_to_zones.items():
        normalized_zone_map[code] = sorted(set(zones))

    return normalized_lookup, code_to_country, normalized_zone_map


@dataclass
class SearchResult:
    zone_id: str
    score: int
    source: str


class TimeZoneEngine:
    def __init__(self) -> None:
        all_zones = sorted(available_timezones())
        self.zone_ids = [z for z in all_zones if not z.startswith(("posix/", "right/"))]
        self.zone_set = set(self.zone_ids)
        self.zone_search_tokens = {zone: normalize(zone) for zone in self.zone_ids}
        self.country_lookup, self.code_to_country, self.code_to_zones = load_country_timezone_index()
        self._online_cache: dict[str, list[SearchResult]] = {}

    def detect_local_zone_key(self) -> str | None:
        now_local = datetime.now().astimezone()
        tzinfo = now_local.tzinfo
        key = getattr(tzinfo, "key", None)
        if isinstance(key, str) and key in self.zone_set:
            return key

        env_tz = os.environ.get("TZ", "")
        if env_tz in self.zone_set:
            return env_tz

        local_name = now_local.tzname()
        local_offset = now_local.utcoffset()
        candidates: list[str] = []
        for zone_id in self.zone_ids:
            tz = ZoneInfo(zone_id)
            zoned = now_local.astimezone(tz)
            if zoned.tzname() == local_name and zoned.utcoffset() == local_offset:
                candidates.append(zone_id)
                if len(candidates) > 15:
                    break
        return candidates[0] if len(candidates) == 1 else None

    def search(self, query: str, limit: int = 80) -> list[SearchResult]:
        normalized = normalize(query)
        if not normalized:
            return []

        results: dict[str, SearchResult] = {}

        def add_result(zone_id: str, score: int, source: str) -> None:
            if zone_id not in self.zone_set:
                return
            existing = results.get(zone_id)
            if not existing or score > existing.score:
                results[zone_id] = SearchResult(zone_id=zone_id, score=score, source=source)

        query_upper = query.strip().upper()
        if query_upper in self.code_to_zones:
            for zone in self.code_to_zones[query_upper]:
                add_result(zone, 180, f"kraj ISO {query_upper}")

        for country_key, country_codes in self.country_lookup.items():
            if normalized == country_key:
                for code in country_codes:
                    for zone_id in self.code_to_zones.get(code, []):
                        source_name = self.code_to_country.get(code, code)
                        add_result(zone_id, 170, f"kraj: {source_name}")
            elif normalized and normalized in country_key and len(normalized) >= 3:
                for code in country_codes:
                    for zone_id in self.code_to_zones.get(code, []):
                        source_name = self.code_to_country.get(code, code)
                        add_result(zone_id, 130, f"kraj: {source_name}")

        for zone_id in self.zone_ids:
            token = self.zone_search_tokens[zone_id]
            if normalized == token:
                add_result(zone_id, 160, "dokladna nazwa strefy")
                continue

            if zone_id.casefold() == query.strip().casefold():
                add_result(zone_id, 190, "dokladna nazwa IANA")
                continue

            city = zone_id.split("/")[-1].replace("_", " ")
            city_norm = normalize(city)
            if normalized == city_norm:
                add_result(zone_id, 155, "dokladna nazwa miasta")
                continue

            if city_norm.startswith(normalized):
                add_result(zone_id, 145, "miasto")
                continue

            if normalized in token:
                add_result(zone_id, 120, "dopasowanie strefy")

        # Dodatkowe wyszukiwanie online po dowolnym miescie (np. mniejsze miasta).
        for online_result in self._search_online_city(query):
            add_result(online_result.zone_id, online_result.score, online_result.source)

        ordered = sorted(results.values(), key=lambda item: (-item.score, item.zone_id))
        return ordered[:limit]

    def _search_online_city(self, query: str, limit: int = 5) -> list[SearchResult]:
        normalized = normalize(query)
        raw = query.strip()
        if len(normalized) < 3:
            return []
        if len(raw) <= 2 and raw.isalpha() and raw.upper() == raw:
            return []

        if normalized in self._online_cache:
            return self._online_cache[normalized]

        results: list[SearchResult] = []
        seen: set[str] = set()

        try:
            geocode_rows = self._online_geocode(query, limit=limit)
            for row in geocode_rows:
                lat = row.get("lat")
                lon = row.get("lon")
                display_name = row.get("display_name", "online")
                if lat is None or lon is None:
                    continue

                zone_id = self._timezone_from_coords(lat, lon)
                if not zone_id:
                    continue
                if zone_id not in self.zone_set:
                    continue
                if zone_id in seen:
                    continue

                seen.add(zone_id)
                results.append(
                    SearchResult(
                        zone_id=zone_id,
                        score=118,
                        source=f"online: {display_name}",
                    )
                )
        except (URLError, OSError, ValueError, json.JSONDecodeError):
            results = []

        self._online_cache[normalized] = results
        return results

    def _online_geocode(self, query: str, limit: int = 5) -> list[dict]:
        params = {
            "q": query,
            "format": "jsonv2",
            "limit": str(limit),
            "addressdetails": "0",
            "accept-language": "pl,en",
        }
        url = "https://nominatim.openstreetmap.org/search?" + urlencode(params)
        req = Request(
            url,
            headers={
                "User-Agent": "WorldTimeSpecialist/1.0 (desktop-app)",
                "Accept": "application/json",
            },
        )
        with urlopen(req, timeout=5) as response:
            payload = response.read().decode("utf-8")
        rows = json.loads(payload)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
        return []

    def _timezone_from_coords(self, lat: str | float, lon: str | float) -> str | None:
        params = {
            "latitude": str(lat),
            "longitude": str(lon),
            "current": "temperature_2m",
            "timezone": "auto",
            "forecast_days": "1",
        }
        url = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
        req = Request(
            url,
            headers={
                "User-Agent": "WorldTimeSpecialist/1.0 (desktop-app)",
                "Accept": "application/json",
            },
        )
        with urlopen(req, timeout=5) as response:
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        zone_id = data.get("timezone") if isinstance(data, dict) else None
        return zone_id if isinstance(zone_id, str) else None


class TimeSpecialistApp(tk.Tk):
    REFRESH_MS = 1000

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1320x820")
        self.minsize(1080, 700)
        self.configure(bg="#0B132B")

        self.engine = TimeZoneEngine()
        self.local_zone_key = self.engine.detect_local_zone_key()
        self.search_results: list[SearchResult] = []
        self.selected_zone: str | None = None

        self.local_time_var = tk.StringVar(value="--:--:--")
        self.local_info_var = tk.StringVar(value="Ladowanie danych lokalnej strefy...")
        self.status_var = tk.StringVar(
            value="Wpisz kraj, kod ISO (np. PL) albo miasto (np. Tokyo, Sycow). "
            "Dla mniejszych miast aplikacja korzysta tez z wyszukiwania online."
        )
        self.search_query_var = tk.StringVar()
        self.detail_header_var = tk.StringVar(value="Wybierz lokalizacje z listy wynikow.")
        self.detail_body_var = tk.StringVar(value="Tutaj zobaczysz szczegoly strefy i relacje do Twojego czasu.")

        self._setup_styles()
        self._build_ui()
        self._run_search()
        self._refresh_loop()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background="#0B132B", foreground="#F0F4F8", fieldbackground="#17223C")
        style.configure("Root.TFrame", background="#0B132B")
        style.configure("Card.TFrame", background="#17223C")
        style.configure("Header.TLabel", background="#0B132B", foreground="#F8FAFC", font=("Bahnschrift", 26, "bold"))
        style.configure("SubHeader.TLabel", background="#0B132B", foreground="#9CC9FF", font=("Bahnschrift", 11))
        style.configure("CardTitle.TLabel", background="#17223C", foreground="#D6E7FF", font=("Bahnschrift", 13, "bold"))
        style.configure("Clock.TLabel", background="#17223C", foreground="#F8FAFC", font=("Consolas", 34, "bold"))
        style.configure("Info.TLabel", background="#17223C", foreground="#C4D8F2", font=("Bahnschrift", 11))
        style.configure("SmallInfo.TLabel", background="#17223C", foreground="#C4D8F2", font=("Bahnschrift", 10))
        style.configure("Action.TButton", font=("Bahnschrift", 10, "bold"), padding=(10, 6))
        style.map(
            "Action.TButton",
            background=[("active", "#2F80ED"), ("!active", "#1D5FD1")],
            foreground=[("disabled", "#9DB4D3"), ("!disabled", "#F8FAFC")],
        )
        style.configure("TNotebook", background="#0B132B", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Bahnschrift", 10, "bold"), padding=(14, 8))
        style.map("TNotebook.Tab", background=[("selected", "#1E2B4A"), ("!selected", "#101B33")], foreground=[("selected", "#F8FAFC"), ("!selected", "#9FB7D8")])
        style.configure("Treeview", background="#12213F", fieldbackground="#12213F", foreground="#E8F1FF", rowheight=28, borderwidth=0, font=("Bahnschrift", 10))
        style.configure("Treeview.Heading", background="#1D3259", foreground="#DDEBFF", font=("Bahnschrift", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#2463D4")], foreground=[("selected", "#FFFFFF")])
        style.configure("Search.TEntry", padding=(8, 6))
        style.configure("TScrollbar", gripcount=0, background="#20345D", troughcolor="#0E1A33")

    def _build_ui(self) -> None:
        root = ttk.Frame(self, style="Root.TFrame", padding=14)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root, style="Card.TFrame", padding=14)
        header.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        header.columnconfigure(0, weight=3)
        header.columnconfigure(1, weight=2)

        left = ttk.Frame(header, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsew")
        ttk.Label(left, text="World Time Specialist", style="Header.TLabel").pack(anchor="w")
        ttk.Label(left, text="Lokalna strefa jest wykrywana automatycznie wraz ze zmiana czasu (DST).", style="SubHeader.TLabel").pack(anchor="w", pady=(6, 0))

        right = ttk.Frame(header, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        ttk.Label(right, text="Twoj czas lokalny", style="CardTitle.TLabel").pack(anchor="e")
        ttk.Label(right, textvariable=self.local_time_var, style="Clock.TLabel").pack(anchor="e", pady=(2, 0))
        ttk.Label(right, textvariable=self.local_info_var, style="Info.TLabel", justify="right").pack(anchor="e", pady=(4, 0))

        notebook = ttk.Notebook(root)
        notebook.grid(row=1, column=0, sticky="nsew")

        self.world_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)
        self.search_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)
        self.universal_tab = ttk.Frame(notebook, style="Root.TFrame", padding=12)

        notebook.add(self.world_tab, text="Czasy Swiata")
        notebook.add(self.search_tab, text="Szukaj Miasta/Kraju")
        notebook.add(self.universal_tab, text="Uniwersalne Czasy")

        self._build_world_tab()
        self._build_search_tab()
        self._build_universal_tab()

    def _build_world_tab(self) -> None:
        container = ttk.Frame(self.world_tab, style="Card.TFrame", padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        ttk.Label(container, text="Podstawowe miasta swiata", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        columns = ("place", "zone", "time", "abbr", "utc", "diff", "phase")
        self.world_tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")
        self.world_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        headings = {
            "place": "Miejsce",
            "zone": "Strefa IANA",
            "time": "Lokalny Czas",
            "abbr": "Skrot",
            "utc": "Offset UTC",
            "diff": "Wzgledem Ciebie",
            "phase": "Pora Dnia",
        }
        widths = {
            "place": 180,
            "zone": 220,
            "time": 170,
            "abbr": 90,
            "utc": 100,
            "diff": 130,
            "phase": 100,
        }

        for col in columns:
            self.world_tree.heading(col, text=headings[col])
            self.world_tree.column(col, width=widths[col], anchor="center")
        self.world_tree.column("place", anchor="w")
        self.world_tree.column("zone", anchor="w")

        scroll = ttk.Scrollbar(container, orient="vertical", command=self.world_tree.yview)
        scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.world_tree.configure(yscrollcommand=scroll.set)

        self.world_tree.tag_configure("day", background="#18335E")
        self.world_tree.tag_configure("morning", background="#215A7A")
        self.world_tree.tag_configure("night", background="#0F1D3A")
        self.world_tree.tag_configure("evening", background="#213D66")

        for _, zone_id in WORLD_HIGHLIGHTS:
            self.world_tree.insert("", "end", iid=zone_id, values=("", "", "", "", "", "", ""))

        legend = ttk.Label(
            container,
            text="Legenda: Rano (05:00-09:59), Dzien (10:00-17:59), Wieczor (18:00-21:59), Noc (22:00-04:59).",
            style="SmallInfo.TLabel",
        )
        legend.grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _build_search_tab(self) -> None:
        root = ttk.Frame(self.search_tab, style="Root.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(1, weight=1)

        search_bar = ttk.Frame(root, style="Card.TFrame", padding=10)
        search_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        search_bar.columnconfigure(1, weight=1)

        ttk.Label(search_bar, text="Wpisz kraj, kod ISO albo miasto:", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        search_entry = ttk.Entry(search_bar, textvariable=self.search_query_var, style="Search.TEntry")
        search_entry.grid(row=0, column=1, sticky="ew", padx=10)
        search_entry.bind("<Return>", self._on_search_enter)
        ttk.Button(search_bar, text="Szukaj", style="Action.TButton", command=self._run_search).grid(row=0, column=2)

        ttk.Label(search_bar, textvariable=self.status_var, style="SmallInfo.TLabel", wraplength=980).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        left_card = ttk.Frame(root, style="Card.TFrame", padding=10)
        left_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left_card.columnconfigure(0, weight=1)
        left_card.rowconfigure(1, weight=1)

        ttk.Label(left_card, text="Wyniki", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        columns = ("zone", "time", "abbr", "utc", "diff", "phase", "source")
        self.search_tree = ttk.Treeview(left_card, columns=columns, show="headings", selectmode="browse")
        self.search_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        headings = {
            "zone": "Strefa",
            "time": "Aktualny Czas",
            "abbr": "Skrot",
            "utc": "UTC",
            "diff": "Do Lokalnego",
            "phase": "Pora Dnia",
            "source": "Zrodlo",
        }
        widths = {
            "zone": 230,
            "time": 145,
            "abbr": 90,
            "utc": 90,
            "diff": 110,
            "phase": 90,
            "source": 150,
        }
        for col in columns:
            self.search_tree.heading(col, text=headings[col])
            self.search_tree.column(col, width=widths[col], anchor="center")
        self.search_tree.column("zone", anchor="w")
        self.search_tree.column("source", anchor="w")

        search_scroll = ttk.Scrollbar(left_card, orient="vertical", command=self.search_tree.yview)
        search_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.search_tree.configure(yscrollcommand=search_scroll.set)
        self.search_tree.tag_configure("day", background="#18335E")
        self.search_tree.tag_configure("morning", background="#215A7A")
        self.search_tree.tag_configure("night", background="#0F1D3A")
        self.search_tree.tag_configure("evening", background="#213D66")
        self.search_tree.bind("<<TreeviewSelect>>", self._on_search_select)

        detail_card = ttk.Frame(root, style="Card.TFrame", padding=12)
        detail_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        detail_card.columnconfigure(0, weight=1)

        ttk.Label(detail_card, textvariable=self.detail_header_var, style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(detail_card, textvariable=self.detail_body_var, style="Info.TLabel", justify="left", wraplength=420).grid(row=1, column=0, sticky="nw", pady=(8, 0))

        hints = (
            "Wskazowki:\n"
            "- miasto: Warszawa / New York / Tokyo / Sycow\n"
            "- kraj: Poland / Polska / United States\n"
            "- kod ISO: PL, US, JP\n"
            "- online: dla mniejszych miast aplikacja probuje geokodowania internetowego"
        )
        ttk.Label(detail_card, text=hints, style="SmallInfo.TLabel", justify="left").grid(row=2, column=0, sticky="sw", pady=(14, 0))

    def _build_universal_tab(self) -> None:
        root = ttk.Frame(self.universal_tab, style="Card.TFrame", padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        ttk.Label(root, text="Uniwersalne standardy i skroty stref", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        columns = ("name", "example", "time", "abbr", "utc", "season")
        self.universal_tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="none")
        self.universal_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        headings = {
            "name": "Standard",
            "example": "Przyklad Lokalizacji",
            "time": "Aktualny Czas",
            "abbr": "Skrot Teraz",
            "utc": "UTC Teraz",
            "season": "Zakres Zima/Lato",
        }
        widths = {
            "name": 120,
            "example": 210,
            "time": 160,
            "abbr": 120,
            "utc": 110,
            "season": 460,
        }
        for col in columns:
            self.universal_tree.heading(col, text=headings[col])
            self.universal_tree.column(col, width=widths[col], anchor="center")
        self.universal_tree.column("example", anchor="w")
        self.universal_tree.column("season", anchor="w")

        scroll = ttk.Scrollbar(root, orient="vertical", command=self.universal_tree.yview)
        scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.universal_tree.configure(yscrollcommand=scroll.set)

        for name, zone_id, _ in UNIVERSAL_REFERENCES:
            row_id = f"u::{name}::{zone_id}"
            self.universal_tree.insert("", "end", iid=row_id, values=(name, zone_id, "", "", "", ""))

        footnote = (
            "Uwaga: ten sam skrot moze byc niejednoznaczny (np. CST w USA i Chinach). "
            "Dlatego aplikacja pokazuje tez identyfikator IANA, ktory jest jednoznaczny."
        )
        ttk.Label(root, text=footnote, style="SmallInfo.TLabel", wraplength=1180, justify="left").grid(row=2, column=0, sticky="w", pady=(10, 0))

    def _on_search_enter(self, event: tk.Event) -> None:
        self._run_search()

    def _run_search(self) -> None:
        query = self.search_query_var.get().strip()
        if query:
            self.status_var.set("Szukanie lokalne + online...")
            self.update_idletasks()
        self.search_results = self.engine.search(query) if query else []

        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        if not query:
            self.status_var.set(
                "Wpisz kraj, kod ISO (np. PL) albo miasto (np. Tokyo, Sycow). "
                "Dla mniejszych miast aplikacja korzysta tez z wyszukiwania online."
            )
            self.detail_header_var.set("Wybierz lokalizacje z listy wynikow.")
            self.detail_body_var.set("Tutaj zobaczysz szczegoly strefy i relacje do Twojego czasu.")
            return

        if not self.search_results:
            self.status_var.set(f"Brak wynikow dla: {query}")
            self.detail_header_var.set("Brak danych")
            self.detail_body_var.set(
                "Sprobuj innej nazwy miasta, kraju albo kodu ISO, np. US, JP, PL. "
                "Jesli to bardzo mala miejscowosc, sprawdz pelna nazwe z regionem."
            )
            return

        self.status_var.set(f"Znaleziono {len(self.search_results)} stref (pokazano do limitu 80).")

        for result in self.search_results:
            self.search_tree.insert(
                "",
                "end",
                iid=result.zone_id,
                values=(result.zone_id, "", "", "", "", "", result.source),
            )

        first = self.search_results[0].zone_id
        self.search_tree.selection_set(first)
        self.search_tree.focus(first)
        self.selected_zone = first
        self._update_detail_panel(first)

    def _on_search_select(self, event: tk.Event) -> None:
        selected = self.search_tree.selection()
        if not selected:
            return
        zone_id = selected[0]
        self.selected_zone = zone_id
        self._update_detail_panel(zone_id)

    def _update_detail_panel(self, zone_id: str) -> None:
        now_local = datetime.now().astimezone()
        now_target = now_local.astimezone(ZoneInfo(zone_id))

        tz_name = now_target.tzname() or "-"
        utc_offset = format_offset(now_target.utcoffset())
        diff = now_target.utcoffset() - now_local.utcoffset()
        dst_text = "TAK" if is_dst_active(now_target) else "NIE"
        season = seasonal_offset_description(zone_id, now_target.year)

        local_zone = self.local_zone_key or (now_local.tzname() or "lokalna")

        self.detail_header_var.set(f"Szczegoly: {zone_id}")
        self.detail_body_var.set(
            "Twoj czas lokalny:\n"
            f"- {now_local:%Y-%m-%d %H:%M:%S} ({local_zone}, {now_local.tzname()})\n\n"
            "Czas w wybranej strefie:\n"
            f"- {now_target:%Y-%m-%d %H:%M:%S}\n"
            f"- skrot: {tz_name}\n"
            f"- offset: {utc_offset}\n"
            f"- roznica do Ciebie: {format_diff(diff)}\n"
            f"- DST aktywne: {dst_text}\n"
            f"- profil sezonowy: {season}\n"
            f"- pora dnia: {day_period_label(now_target.hour)}"
        )

    def _refresh_local_header(self, now_local: datetime) -> None:
        local_zone = self.local_zone_key or (now_local.tzname() or "lokalna strefa")
        offset = format_offset(now_local.utcoffset())
        short = now_local.tzname() or "-"
        dst_text = "DST: TAK" if is_dst_active(now_local) else "DST: NIE"

        self.local_time_var.set(now_local.strftime("%Y-%m-%d  %H:%M:%S"))
        self.local_info_var.set(f"{local_zone} | {short} | {offset} | {dst_text}")

    def _refresh_world_table(self, now_local: datetime) -> None:
        local_offset = now_local.utcoffset() or timedelta(0)
        for place_name, zone_id in WORLD_HIGHLIGHTS:
            target = now_local.astimezone(ZoneInfo(zone_id))
            phase = day_period_label(target.hour)
            if phase == "Rano":
                tag = "morning"
            elif phase == "Dzien":
                tag = "day"
            elif phase == "Wieczor":
                tag = "evening"
            else:
                tag = "night"
            self.world_tree.item(
                zone_id,
                values=(
                    place_name,
                    zone_id,
                    target.strftime("%Y-%m-%d %H:%M:%S"),
                    target.tzname() or "-",
                    format_offset(target.utcoffset()),
                    format_diff((target.utcoffset() or timedelta(0)) - local_offset),
                    phase,
                ),
                tags=(tag,),
            )

    def _refresh_search_table(self, now_local: datetime) -> None:
        local_offset = now_local.utcoffset() or timedelta(0)
        for result in self.search_results:
            zone_id = result.zone_id
            if not self.search_tree.exists(zone_id):
                continue

            target = now_local.astimezone(ZoneInfo(zone_id))
            phase = day_period_label(target.hour)
            if phase == "Rano":
                tag = "morning"
            elif phase == "Dzien":
                tag = "day"
            elif phase == "Wieczor":
                tag = "evening"
            else:
                tag = "night"
            self.search_tree.item(
                zone_id,
                values=(
                    zone_id,
                    target.strftime("%Y-%m-%d %H:%M:%S"),
                    target.tzname() or "-",
                    format_offset(target.utcoffset()),
                    format_diff((target.utcoffset() or timedelta(0)) - local_offset),
                    phase,
                    result.source,
                ),
                tags=(tag,),
            )

        if self.selected_zone and self.search_tree.exists(self.selected_zone):
            self._update_detail_panel(self.selected_zone)

    def _refresh_universal_table(self, now_local: datetime) -> None:
        for name, zone_id, _ in UNIVERSAL_REFERENCES:
            row_id = f"u::{name}::{zone_id}"
            now_target = now_local.astimezone(ZoneInfo(zone_id))
            season = seasonal_offset_description(zone_id, now_target.year)
            self.universal_tree.item(
                row_id,
                values=(
                    name,
                    zone_id,
                    now_target.strftime("%Y-%m-%d %H:%M:%S"),
                    now_target.tzname() or "-",
                    format_offset(now_target.utcoffset()),
                    season,
                ),
            )

    def _refresh_loop(self) -> None:
        now_local = datetime.now().astimezone()
        self._refresh_local_header(now_local)
        self._refresh_world_table(now_local)
        self._refresh_search_table(now_local)
        self._refresh_universal_table(now_local)
        self.after(self.REFRESH_MS, self._refresh_loop)


def main() -> None:
    app = TimeSpecialistApp()
    app.mainloop()


if __name__ == "__main__":
    main()
