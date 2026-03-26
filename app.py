from __future__ import annotations

import calendar
import json
import math
import os
import re
import subprocess
import sys
import textwrap
import threading
import importlib
import tkinter as tk
import unicodedata
import webbrowser
import winsound
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tkinter import ttk, font as tkfont, filedialog, messagebox
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import TZPATH, ZoneInfo, available_timezones

APP_TITLE = "World Time Specialist"

try:
    import pystray
    from PIL import Image
    PYSTRAY_AVAILABLE = True
except Exception:
    pystray = None
    Image = None
    PYSTRAY_AVAILABLE = False

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ASSETS_DIR = BASE_DIR / "assets"
SOUNDS_DIR = ASSETS_DIR / "sounds"
MAP_IMAGE_FILE = ASSETS_DIR / "world_map.png"
SOUND_SESSION_START = SOUNDS_DIR / "session_start.wav"
SOUND_SESSION_END = SOUNDS_DIR / "session_end.wav"
SOUND_ALARM = SOUNDS_DIR / "alarm.wav"
SOUND_TIMER = SOUNDS_DIR / "timer_end.wav"
# Use the softest bundled ticking sample to keep active-session ambience subtle.
SOUND_TICKING = SOUNDS_DIR / "clock-ticking-2.wav"
TRAY_ICON_FILE = ASSETS_DIR / "clock.ico"
DEFAULT_ALARM_SOUND_ID = "alarm_clock_01"

ALARM_SOUND_LIBRARY: list[dict[str, str]] = [
    {"id": "alarm_clock_01", "file": "alarm-clock-01.wav", "pl": "Klasyczny alarm 1", "en": "Classic alarm 1", "style_pl": "klasyczny", "style_en": "classic"},
    {"id": "clock_ticking_01", "file": "clock-ticking-1.wav", "pl": "Tikanie zegara 1", "en": "Clock ticking 1", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "clock_ticking_02", "file": "clock-ticking-2.wav", "pl": "Tikanie zegara 2", "en": "Clock ticking 2", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "clock_ticking_04", "file": "clock-ticking-4.wav", "pl": "Tikanie zegara 3", "en": "Clock ticking 3", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "clock_ticking_05", "file": "clock-ticking-5.wav", "pl": "Tikanie zegara 4", "en": "Clock ticking 4", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "bell_ringing_01", "file": "bell-ringing-01.wav", "pl": "Dzwon 1", "en": "Bell 1", "style_pl": "dzwonek", "style_en": "bell"},
    {"id": "bell_ringing_02", "file": "bell-ringing-02.wav", "pl": "Dzwon 2", "en": "Bell 2", "style_pl": "dzwonek", "style_en": "bell"},
    {"id": "bell_ringing_03", "file": "bell-ringing-03.wav", "pl": "Dzwon 3", "en": "Bell 3", "style_pl": "dzwonek", "style_en": "bell"},
    {"id": "bell_ringing_04", "file": "bell-ringing-04.wav", "pl": "Dzwon 4", "en": "Bell 4", "style_pl": "dzwonek", "style_en": "bell"},
    {"id": "bell_ringing_05", "file": "bell-ringing-05.wav", "pl": "Dzwon 5", "en": "Bell 5", "style_pl": "dzwonek", "style_en": "bell"},
    {"id": "bell_ring_01", "file": "bell-ring-01.wav", "pl": "Pojedynczy dzwon", "en": "Single bell", "style_pl": "klasyczny", "style_en": "classic"},
    {"id": "small_bell_ring_01", "file": "small-bell-ring-01a.wav", "pl": "Mały dzwonek 1", "en": "Small bell 1", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "small_bell_ringing_01", "file": "small-bell-ringing-01.wav", "pl": "Mały dzwonek 2", "en": "Small bell 2", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "small_bell_ringing_02", "file": "small-bell-ringing-02.wav", "pl": "Mały dzwonek 3", "en": "Small bell 3", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "magic_chime_01", "file": "magic-chime-01.wav", "pl": "Magiczny dzwonek 1", "en": "Magic chime 1", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "magic_chime_02", "file": "magic-chime-02.wav", "pl": "Magiczny dzwonek 2", "en": "Magic chime 2", "style_pl": "spokojny", "style_en": "calm"},
    {"id": "magic_chime_03", "file": "magic-chime-03.wav", "pl": "Magiczny dzwonek 3", "en": "Magic chime 3", "style_pl": "ambient", "style_en": "ambient"},
    {"id": "magic_chime_04", "file": "magic-chime-04.wav", "pl": "Magiczny dzwonek 4", "en": "Magic chime 4", "style_pl": "ambient", "style_en": "ambient"},
    {"id": "magic_chime_05", "file": "magic-chime-05.wav", "pl": "Magiczny dzwonek 5", "en": "Magic chime 5", "style_pl": "ambient", "style_en": "ambient"},
    {"id": "magic_chime_06", "file": "magic-chime-06.wav", "pl": "Magiczny dzwonek 6", "en": "Magic chime 6", "style_pl": "ambient", "style_en": "ambient"},
    {"id": "magic_chime_07", "file": "magic-chime-07.wav", "pl": "Magiczny dzwonek 7", "en": "Magic chime 7", "style_pl": "ambient", "style_en": "ambient"},
    {"id": "button_01", "file": "button-1.wav", "pl": "Puls 1", "en": "Pulse 1", "style_pl": "pulsacyjny", "style_en": "pulsing"},
    {"id": "button_02", "file": "button-2.wav", "pl": "Puls 2", "en": "Pulse 2", "style_pl": "pulsacyjny", "style_en": "pulsing"},
    {"id": "button_03", "file": "button-3.wav", "pl": "Klik 1", "en": "Click 1", "style_pl": "dynamiczny", "style_en": "dynamic"},
    {"id": "button_04", "file": "button-4.wav", "pl": "Klik 2", "en": "Click 2", "style_pl": "dynamiczny", "style_en": "dynamic"},
    {"id": "button_05", "file": "button-5.wav", "pl": "Klik 3", "en": "Click 3", "style_pl": "dynamiczny", "style_en": "dynamic"},
    {"id": "button_06", "file": "button-6.wav", "pl": "Klik 4", "en": "Click 4", "style_pl": "energetyczny", "style_en": "energetic"},
    {"id": "button_07", "file": "button-7.wav", "pl": "Klik 5", "en": "Click 5", "style_pl": "energetyczny", "style_en": "energetic"},
    {"id": "button_08", "file": "button-8.wav", "pl": "Klik 6", "en": "Click 6", "style_pl": "energetyczny", "style_en": "energetic"},
    {"id": "button_10", "file": "button-10.wav", "pl": "Klik 7", "en": "Click 7", "style_pl": "pulsacyjny", "style_en": "pulsing"},
    {"id": "button_11", "file": "button-11.wav", "pl": "Klik 8", "en": "Click 8", "style_pl": "pulsacyjny", "style_en": "pulsing"},
]

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

CITY_LABELS: dict[str, dict[str, str]] = {
    "Warszawa": {"pl": "Warszawa", "en": "Warsaw"},
    "Londyn": {"pl": "Londyn", "en": "London"},
    "Nowy Jork": {"pl": "Nowy Jork", "en": "New York"},
    "Chicago": {"pl": "Chicago", "en": "Chicago"},
    "Denver": {"pl": "Denver", "en": "Denver"},
    "Los Angeles": {"pl": "Los Angeles", "en": "Los Angeles"},
    "Sao Paulo": {"pl": "Sao Paulo", "en": "Sao Paulo"},
    "Johannesburg": {"pl": "Johannesburg", "en": "Johannesburg"},
    "Dubaj": {"pl": "Dubaj", "en": "Dubai"},
    "Delhi": {"pl": "Delhi", "en": "Delhi"},
    "Singapur": {"pl": "Singapur", "en": "Singapore"},
    "Tokio": {"pl": "Tokio", "en": "Tokyo"},
    "Sydney": {"pl": "Sydney", "en": "Sydney"},
    "Auckland": {"pl": "Auckland", "en": "Auckland"},
}

MAP_CITY_LONGITUDE: dict[str, float] = {
    "Warszawa": 21.01,
    "Londyn": -0.12,
    "Nowy Jork": -74.00,
    "Chicago": -87.62,
    "Denver": -104.99,
    "Los Angeles": -118.24,
    "Sao Paulo": -46.63,
    "Johannesburg": 28.05,
    "Dubaj": 55.27,
    "Delhi": 77.21,
    "Singapur": 103.82,
    "Tokio": 139.69,
    "Sydney": 151.20,
    "Auckland": 174.76,
}

MAP_CITY_LATITUDE: dict[str, float] = {
    "Warszawa": 52.23,
    "Londyn": 51.50,
    "Nowy Jork": 40.71,
    "Chicago": 41.88,
    "Denver": 39.74,
    "Los Angeles": 34.05,
    "Sao Paulo": -23.55,
    "Johannesburg": -26.20,
    "Dubaj": 25.20,
    "Delhi": 28.61,
    "Singapur": 1.35,
    "Tokio": 35.68,
    "Sydney": -33.86,
    "Auckland": -36.85,
}

UNIVERSAL_REFERENCES: list[tuple[str, str, str]] = [
    ("UTC", "Etc/UTC", "Koordynowany czas uniwersalny"),
    ("GMT/BST", "Europe/London", "Greenwich / UK"),
    ("CET/CEST", "Europe/Warsaw", "Europa Środkowa"),
    ("EET/EEST", "Europe/Helsinki", "Europa Wschodnia"),
    ("MSK", "Europe/Moscow", "Moskwa"),
    ("EST/EDT", "America/New_York", "USA Wschód"),
    ("CST/CDT", "America/Chicago", "USA Centrum"),
    ("MST/MDT", "America/Denver", "USA Góry"),
    ("PST/PDT", "America/Los_Angeles", "USA Zachód"),
    ("IST", "Asia/Kolkata", "Indie"),
    ("CST", "Asia/Shanghai", "Chiny"),
    ("JST", "Asia/Tokyo", "Japonia"),
    ("AEST/AEDT", "Australia/Sydney", "Australia Wschód"),
]

FALLBACK_ZONE_RULES: dict[str, dict[str, object]] = {
    "Etc/UTC": {"std": 0, "abbr_std": "UTC"},
    "Europe/Warsaw": {"std": 60, "dst": 120, "abbr_std": "CET", "abbr_dst": "CEST", "rule": "eu"},
    "Europe/Berlin": {"std": 60, "dst": 120, "abbr_std": "CET", "abbr_dst": "CEST", "rule": "eu"},
    "Europe/London": {"std": 0, "dst": 60, "abbr_std": "GMT", "abbr_dst": "BST", "rule": "eu"},
    "Europe/Helsinki": {"std": 120, "dst": 180, "abbr_std": "EET", "abbr_dst": "EEST", "rule": "eu"},
    "Europe/Moscow": {"std": 180, "abbr_std": "MSK"},
    "America/New_York": {"std": -300, "dst": -240, "abbr_std": "EST", "abbr_dst": "EDT", "rule": "us"},
    "America/Chicago": {"std": -360, "dst": -300, "abbr_std": "CST", "abbr_dst": "CDT", "rule": "us"},
    "America/Denver": {"std": -420, "dst": -360, "abbr_std": "MST", "abbr_dst": "MDT", "rule": "us"},
    "America/Los_Angeles": {"std": -480, "dst": -420, "abbr_std": "PST", "abbr_dst": "PDT", "rule": "us"},
    "America/Sao_Paulo": {"std": -180, "abbr_std": "BRT"},
    "Africa/Johannesburg": {"std": 120, "abbr_std": "SAST"},
    "Asia/Dubai": {"std": 240, "abbr_std": "GST"},
    "Asia/Kolkata": {"std": 330, "abbr_std": "IST"},
    "Asia/Singapore": {"std": 480, "abbr_std": "SGT"},
    "Asia/Shanghai": {"std": 480, "abbr_std": "CST"},
    "Asia/Tokyo": {"std": 540, "abbr_std": "JST"},
    "Australia/Sydney": {"std": 600, "dst": 660, "abbr_std": "AEST", "abbr_dst": "AEDT", "rule": "aus"},
    "Pacific/Auckland": {"std": 720, "dst": 780, "abbr_std": "NZST", "abbr_dst": "NZDT", "rule": "nz"},
}

FALLBACK_ZONE_IDS = sorted(
    {
        zone_id
        for _label, zone_id in WORLD_HIGHLIGHTS
    }
    | {zone_id for _name, zone_id, _desc in UNIVERSAL_REFERENCES}
    | set(FALLBACK_ZONE_RULES.keys())
)

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

TZ_ABBREVIATION_MAP: dict[str, str] = {
    "UTC": "Etc/UTC",
    "GMT": "Etc/UTC",
    "CET": "Europe/Warsaw",
    "CEST": "Europe/Warsaw",
    "EET": "Europe/Helsinki",
    "EEST": "Europe/Helsinki",
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "BST": "Europe/London",
    "IST": "Asia/Kolkata",
    "JST": "Asia/Tokyo",
    "KST": "Asia/Seoul",
    "MSK": "Europe/Moscow",
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
}

SESSION_PRESETS: dict[str, dict[str, str] | None] = {
    "Brak sesji": None,
    "NYSE (Nowy Jork 09:30-16:00)": {"zone": "America/New_York", "open": "09:30", "close": "16:00"},
    "NASDAQ (Nowy Jork 09:30-16:00)": {"zone": "America/New_York", "open": "09:30", "close": "16:00"},
    "LSE (Londyn 08:00-16:30)": {"zone": "Europe/London", "open": "08:00", "close": "16:30"},
    "XETRA (Frankfurt 09:00-17:30)": {"zone": "Europe/Berlin", "open": "09:00", "close": "17:30"},
    "JPX (Tokio 09:00-15:00)": {"zone": "Asia/Tokyo", "open": "09:00", "close": "15:00"},
}

SESSION_LABELS: dict[str, dict[str, str]] = {
    "Brak sesji": {"pl": "Brak sesji", "en": "No session"},
    "NYSE (Nowy Jork 09:30-16:00)": {"pl": "NYSE (Nowy Jork 09:30-16:00)", "en": "NYSE (New York 09:30-16:00)"},
    "NASDAQ (Nowy Jork 09:30-16:00)": {"pl": "NASDAQ (Nowy Jork 09:30-16:00)", "en": "NASDAQ (New York 09:30-16:00)"},
    "LSE (Londyn 08:00-16:30)": {"pl": "LSE (Londyn 08:00-16:30)", "en": "LSE (London 08:00-16:30)"},
    "XETRA (Frankfurt 09:00-17:30)": {"pl": "XETRA (Frankfurt 09:00-17:30)", "en": "XETRA (Frankfurt 09:00-17:30)"},
    "JPX (Tokio 09:00-15:00)": {"pl": "JPX (Tokio 09:00-15:00)", "en": "JPX (Tokyo 09:00-15:00)"},
}

SETTINGS_DIR = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "WorldTimeSpecialist"
STARTUP_DIR = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
AUTOSTART_FILE = STARTUP_DIR / "WorldTimeSpecialist.cmd"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
LEGACY_SETTINGS_FILE = Path(__file__).with_name("world_time_settings.json")
DEFAULT_THEME = "Nowoczesny Szklany"
NIGHT_THEME = "Czarny Kontrast"
AUTO_NIGHT_DEFAULT_START = "21:00"
AUTO_NIGHT_DEFAULT_STOP = "06:00"
TILE_MIN_WIDTH = 280
TILE_MIN_HEIGHT = 360
TILE_DEFAULT_WIDTH = 360
TILE_DEFAULT_HEIGHT = 450
TILE_SNAP_THRESHOLD = 18
TILE_MARGIN = 12

THEMES: dict[str, dict[str, object]] = {
    "Nowoczesny Szklany": {
        "app_bg": "#0A1226",
        "card_bg": "#16233F",
        "card_alt_bg": "#1B2B4D",
        "text": "#E9F1FF",
        "muted": "#B7C7E6",
        "heading": "#F7FAFF",
        "accent": "#2D72FF",
        "accent_hover": "#4A8BFF",
        "accent_soft": "#3A6FD6",
        "entry_bg": "#1B2A4A",
        "entry_text": "#F1F6FF",
        "tree_bg": "#162748",
        "tree_head_bg": "#20345E",
        "canvas_top": "#1A294C",
        "canvas_bottom": "#0B142D",
        "phase_bg": {
            "night": "#1B2747",
            "morning": "#1E5D7A",
            "day": "#2262A5",
            "afternoon": "#2F7A5E",
            "evening": "#5B4D8A",
        },
        "session_active": "#1F5E38",
        "session_inactive": "#5C2F2F",
        "clock_session_active": "#215B2D",
        "clock_session_inactive": "#5B2A2A",
        "clock_border": "#A9C9FF",
        "clock_tick": "#DDEBFF",
        "clock_hour": "#F8FAFC",
        "clock_minute": "#D6E7FF",
        "clock_second": "#FF6B6B",
        "clock_pin": "#F8FAFC",
        "clock_arc_active": "#7CFC8A",
        "clock_arc_inactive": "#FF8A8A",
    },
    "Ciemny Klasyczny": {
        "app_bg": "#0B132B",
        "card_bg": "#17223C",
        "card_alt_bg": "#12213F",
        "text": "#F0F4F8",
        "muted": "#C4D8F2",
        "heading": "#F8FAFC",
        "accent": "#1D5FD1",
        "accent_hover": "#2F80ED",
        "accent_soft": "#2463D4",
        "entry_bg": "#17223C",
        "entry_text": "#EAF2FF",
        "tree_bg": "#12213F",
        "tree_head_bg": "#1D3259",
        "canvas_top": "#1B2747",
        "canvas_bottom": "#0E1A33",
        "phase_bg": {
            "night": "#1B2747",
            "morning": "#1E5D7A",
            "day": "#2262A5",
            "afternoon": "#2F7A5E",
            "evening": "#5B4D8A",
        },
        "session_active": "#21603A",
        "session_inactive": "#603030",
        "clock_session_active": "#215B2D",
        "clock_session_inactive": "#5B2A2A",
        "clock_border": "#A9C9FF",
        "clock_tick": "#DDEBFF",
        "clock_hour": "#F8FAFC",
        "clock_minute": "#D6E7FF",
        "clock_second": "#FF6B6B",
        "clock_pin": "#F8FAFC",
        "clock_arc_active": "#7CFC8A",
        "clock_arc_inactive": "#FF8A8A",
    },
    "Czarny Kontrast": {
        "app_bg": "#050505",
        "card_bg": "#101010",
        "card_alt_bg": "#161616",
        "text": "#F5F5F5",
        "muted": "#CBCBCB",
        "heading": "#FFFFFF",
        "accent": "#3D3D3D",
        "accent_hover": "#5A5A5A",
        "accent_soft": "#4A4A4A",
        "entry_bg": "#121212",
        "entry_text": "#FFFFFF",
        "tree_bg": "#141414",
        "tree_head_bg": "#202020",
        "canvas_top": "#1A1A1A",
        "canvas_bottom": "#0A0A0A",
        "phase_bg": {
            "night": "#191919",
            "morning": "#2B2B2B",
            "day": "#353535",
            "afternoon": "#2E2E2E",
            "evening": "#252525",
        },
        "session_active": "#2D5D35",
        "session_inactive": "#5A2C2C",
        "clock_session_active": "#21462A",
        "clock_session_inactive": "#452121",
        "clock_border": "#E2E2E2",
        "clock_tick": "#E8E8E8",
        "clock_hour": "#FFFFFF",
        "clock_minute": "#DDDDDD",
        "clock_second": "#FF7A7A",
        "clock_pin": "#FFFFFF",
        "clock_arc_active": "#9EFFAB",
        "clock_arc_inactive": "#FF9D9D",
    },
    "Jasny Klasyczny": {
        "app_bg": "#E8EDF5",
        "card_bg": "#FFFFFF",
        "card_alt_bg": "#F4F7FB",
        "text": "#1B1F2A",
        "muted": "#334563",
        "heading": "#101829",
        "accent": "#2A5DD8",
        "accent_hover": "#3B75F2",
        "accent_soft": "#5E89F2",
        "entry_bg": "#FFFFFF",
        "entry_text": "#0F172A",
        "tree_bg": "#F6F8FC",
        "tree_head_bg": "#DCE6F7",
        "canvas_top": "#E8EEF8",
        "canvas_bottom": "#D9E3F4",
        "phase_bg": {
            "night": "#D7E0EE",
            "morning": "#CDEAF5",
            "day": "#BED7F2",
            "afternoon": "#CFEAD9",
            "evening": "#E0D6F1",
        },
        "session_active": "#3A8B5A",
        "session_inactive": "#A35252",
        "clock_session_active": "#7CB88E",
        "clock_session_inactive": "#CD8686",
        "clock_border": "#35588E",
        "clock_tick": "#35588E",
        "clock_hour": "#0F172A",
        "clock_minute": "#1E293B",
        "clock_second": "#E85353",
        "clock_pin": "#0F172A",
        "clock_arc_active": "#42B35D",
        "clock_arc_inactive": "#D45D5D",
    },
    "Nocny Cieply": {
        "app_bg": "#1A120D",
        "card_bg": "#2A1A11",
        "card_alt_bg": "#342016",
        "text": "#F6E8D6",
        "muted": "#E4C6A0",
        "heading": "#FFEED8",
        "accent": "#B4672E",
        "accent_hover": "#CB7A37",
        "accent_soft": "#D19057",
        "entry_bg": "#2F1D13",
        "entry_text": "#FFE7CC",
        "tree_bg": "#301F15",
        "tree_head_bg": "#4A2D1E",
        "canvas_top": "#3A2418",
        "canvas_bottom": "#1E130D",
        "phase_bg": {
            "night": "#2A1A11",
            "morning": "#5A3723",
            "day": "#7A4A2D",
            "afternoon": "#8B522F",
            "evening": "#6A3E26",
        },
        "session_active": "#6E7A2A",
        "session_inactive": "#6A3A2A",
        "clock_session_active": "#5F6A1E",
        "clock_session_inactive": "#5C2E20",
        "clock_border": "#E9C9A0",
        "clock_tick": "#F0D6B6",
        "clock_hour": "#FFF1E0",
        "clock_minute": "#F0D5B5",
        "clock_second": "#FFB074",
        "clock_pin": "#FFF1E0",
        "clock_arc_active": "#CED96A",
        "clock_arc_inactive": "#E79072",
    },
    "Ciemny Komfort Oczy": {
        "app_bg": "#0E1214",
        "card_bg": "#161F23",
        "card_alt_bg": "#1B252A",
        "text": "#E7ECEE",
        "muted": "#B2C0C5",
        "heading": "#F5F7F8",
        "accent": "#4E6D66",
        "accent_hover": "#5B8178",
        "accent_soft": "#6A9188",
        "entry_bg": "#1A2529",
        "entry_text": "#ECF2F4",
        "tree_bg": "#1A2529",
        "tree_head_bg": "#25343A",
        "canvas_top": "#223137",
        "canvas_bottom": "#131D21",
        "phase_bg": {
            "night": "#1A2529",
            "morning": "#294049",
            "day": "#35515B",
            "afternoon": "#3D5E53",
            "evening": "#425061",
        },
        "session_active": "#2D6C50",
        "session_inactive": "#6A3D3D",
        "clock_session_active": "#2A5A44",
        "clock_session_inactive": "#5A2E2E",
        "clock_border": "#B8CED6",
        "clock_tick": "#D5E5EA",
        "clock_hour": "#EFF5F7",
        "clock_minute": "#D8E8EE",
        "clock_second": "#FF8E8E",
        "clock_pin": "#EFF5F7",
        "clock_arc_active": "#96DEB5",
        "clock_arc_inactive": "#E7A1A1",
    },
    "Szafirowa Mgła": {
        "app_bg": "#0A1020",
        "card_bg": "#131F3A",
        "card_alt_bg": "#1A2A4B",
        "text": "#E6F0FF",
        "muted": "#B4C5E3",
        "heading": "#F8FBFF",
        "accent": "#3A7BFF",
        "accent_hover": "#5A93FF",
        "accent_soft": "#5B8EE6",
        "entry_bg": "#18264A",
        "entry_text": "#F1F6FF",
        "tree_bg": "#132241",
        "tree_head_bg": "#1D3260",
        "canvas_top": "#1A294F",
        "canvas_bottom": "#0B142B",
        "phase_bg": {
            "night": "#1A2646",
            "morning": "#1E5B78",
            "day": "#2567A7",
            "afternoon": "#2E7B62",
            "evening": "#5C4F8F",
        },
        "session_active": "#1F5E3B",
        "session_inactive": "#5D3131",
        "clock_session_active": "#1E532E",
        "clock_session_inactive": "#582828",
        "clock_border": "#B7D6FF",
        "clock_tick": "#E0EEFF",
        "clock_hour": "#F8FAFC",
        "clock_minute": "#D8E7FF",
        "clock_second": "#FF6F7F",
        "clock_pin": "#F8FAFC",
        "clock_arc_active": "#83F3A1",
        "clock_arc_inactive": "#FF9A9A",
    },
    "Metaliczny Grafit": {
        "app_bg": "#0D0F12",
        "card_bg": "#1A1E24",
        "card_alt_bg": "#20262E",
        "text": "#ECEFF4",
        "muted": "#B5BDC9",
        "heading": "#F8FAFF",
        "accent": "#4A6A8C",
        "accent_hover": "#5C7FA5",
        "accent_soft": "#6C86A6",
        "entry_bg": "#1F242B",
        "entry_text": "#F4F7FB",
        "tree_bg": "#1A1F26",
        "tree_head_bg": "#2A3340",
        "canvas_top": "#242A33",
        "canvas_bottom": "#12161C",
        "phase_bg": {
            "night": "#1A1F26",
            "morning": "#2D3C4D",
            "day": "#3B4E63",
            "afternoon": "#3A5A55",
            "evening": "#3B3F55",
        },
        "session_active": "#2B6C52",
        "session_inactive": "#6A3A3A",
        "clock_session_active": "#2C5846",
        "clock_session_inactive": "#592D2D",
        "clock_border": "#C9D4E2",
        "clock_tick": "#DCE4EF",
        "clock_hour": "#F7FAFF",
        "clock_minute": "#D7E0EC",
        "clock_second": "#FF7C7C",
        "clock_pin": "#F7FAFF",
        "clock_arc_active": "#9DE6BB",
        "clock_arc_inactive": "#E7A1A1",
    },
}

THEME_LABELS: dict[str, dict[str, str]] = {
    "Nowoczesny Szklany": {"pl": "Nowoczesny Szklany", "en": "Modern Glass"},
    "Ciemny Klasyczny": {"pl": "Ciemny Klasyczny", "en": "Dark Classic"},
    "Czarny Kontrast": {"pl": "Czarny Kontrast", "en": "Black Contrast"},
    "Jasny Klasyczny": {"pl": "Jasny Klasyczny", "en": "Light Classic"},
    "Nocny Cieply": {"pl": "Nocny Ciepły", "en": "Warm Night"},
    "Ciemny Komfort Oczy": {"pl": "Ciemny Komfort Oczy", "en": "Eye Comfort Dark"},
    "Szafirowa Mgła": {"pl": "Szafirowa Mgła", "en": "Sapphire Mist"},
    "Metaliczny Grafit": {"pl": "Metaliczny Grafit", "en": "Metallic Graphite"},
}

TIME_PICKER_VALUES = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in (0, 30)]

PHASE_BG = THEMES[DEFAULT_THEME]["phase_bg"]

OFFSET_REPRESENTATIVE_ZONE: dict[int, str] = {
    -480: "America/Los_Angeles",
    -420: "America/Denver",
    -360: "America/Chicago",
    -300: "America/New_York",
    0: "Etc/UTC",
    60: "Europe/Warsaw",
    120: "Europe/Helsinki",
    180: "Europe/Moscow",
    330: "Asia/Kolkata",
    480: "Asia/Shanghai",
    540: "Asia/Tokyo",
    600: "Australia/Sydney",
}

EDUCATION_TOPICS: dict[str, dict[str, object]] = {
    "root": {
        "icon": "🌍",
        "label": {"pl": "Start: mapa czasu", "en": "Start: time map"},
        "title": {
            "pl": "Jak działa czas światowy: od UTC do czasu lokalnego",
            "en": "How world time works: from UTC to local time",
        },
        "body": {
            "pl": (
                "🔹 Wszystkie strefy czasowe odnoszą się do UTC.\n"
                "🔹 Konwersja zawsze oznacza ten sam moment pokazany na innym zegarze lokalnym.\n"
                "🔹 Aplikacja liczy to automatycznie, uwzględniając DST (czas letni/zimowy).\n\n"
                "Praktycznie: wybierasz czas źródłowy, strefę źródła i strefę docelową. "
                "Wynik jest natychmiast porównywany do czasu bazowego."
            ),
            "en": (
                "🔹 All time zones are defined relative to UTC.\n"
                "🔹 Conversion always means the same instant shown on a different local clock.\n"
                "🔹 The app calculates this automatically, including DST rules.\n\n"
                "In practice: choose source time, source zone, and target zone. "
                "The result is instantly compared to your base time."
            ),
        },
    },
    "utc": {
        "icon": "🧭",
        "label": {"pl": "UTC i GMT", "en": "UTC and GMT"},
        "title": {"pl": "UTC: wspólny punkt odniesienia", "en": "UTC: the shared reference baseline"},
        "body": {
            "pl": (
                "UTC (Coordinated Universal Time) to skoordynowany czas uniwersalny.\n"
                "Skrót pochodzi z kompromisu językowego: ang. *Coordinated Universal Time* i fr. *Temps Universel Coordonné*.\n"
                "GMT (Greenwich Mean Time) to historyczny czas południka 0°.\n\n"
                "✅ UTC nie zmienia się sezonowo.\n"
                "✅ Zmiany czasu (DST) wprowadzają strefy lokalne.\n"
                "✅ W praktyce UTC jest bazą dla wszystkich stref i konwersji."
            ),
            "en": (
                "UTC (Coordinated Universal Time) is the global time reference.\n"
                "The acronym is a linguistic compromise: *Coordinated Universal Time* (EN) and *Temps Universel Coordonné* (FR).\n"
                "GMT (Greenwich Mean Time) is the historic time of the prime meridian.\n\n"
                "✅ UTC never changes seasonally.\n"
                "✅ Local zones apply DST rules.\n"
                "✅ In practice, UTC is the baseline for all zones and conversions."
            ),
        },
    },
    "offset": {
        "icon": "➕",
        "label": {"pl": "Offsety UTC", "en": "UTC offsets"},
        "title": {"pl": "UTC+/-: różnica godzin", "en": "UTC+/-: hour difference"},
        "body": {
            "pl": (
                "UTC+01:00 oznacza „godzinę później niż UTC”.\n"
                "UTC-05:00 oznacza „pięć godzin wcześniej niż UTC”.\n\n"
                "⚠️ Ten sam offset może należeć do wielu krajów.\n"
                "Dlatego do dokładności używa się stref IANA (np. Europe/Warsaw)."
            ),
            "en": (
                "UTC+01:00 means one hour ahead of UTC.\n"
                "UTC-05:00 means five hours behind UTC.\n\n"
                "⚠️ The same offset can be shared by multiple countries.\n"
                "For precision, use IANA zones (e.g., Europe/Warsaw)."
            ),
        },
    },
    "abbr": {
        "icon": "🔤",
        "label": {"pl": "Skróty stref", "en": "Zone abbreviations"},
        "title": {"pl": "EST, CET, JST: wygodne, ale nie zawsze jednoznaczne", "en": "EST, CET, JST: convenient but sometimes ambiguous"},
        "body": {
            "pl": (
                "Skróty są krótkie i popularne, ale mogą być wieloznaczne (np. CST).\n"
                "Przykłady rozwinięć:\n"
                "• CET = Central European Time (czas środkowoeuropejski)\n"
                "• EET = Eastern European Time (czas wschodnioeuropejski)\n"
                "• EST = Eastern Standard Time (wschodni standard USA)\n"
                "• JST = Japan Standard Time (standard Japonii)\n\n"
                "W aplikacji zawsze pokazujemy także pełną nazwę IANA.\n"
                "Dla ważnych terminów (giełda, loty, spotkania) wybieraj pełną strefę."
            ),
            "en": (
                "Abbreviations are short and common, but can be ambiguous (e.g., CST).\n"
                "Common expansions:\n"
                "• CET = Central European Time\n"
                "• EET = Eastern European Time\n"
                "• EST = Eastern Standard Time (US East)\n"
                "• JST = Japan Standard Time\n\n"
                "The app always displays the full IANA zone too.\n"
                "For critical timing (trading, flights, meetings), use full zone names."
            ),
        },
    },
    "iana": {
        "icon": "🗺️",
        "label": {"pl": "Strefy IANA", "en": "IANA zones"},
        "title": {"pl": "IANA: najdokładniejszy format stref", "en": "IANA: the most precise zone format"},
        "body": {
            "pl": (
                "IANA to *Internet Assigned Numbers Authority*.\n"
                "Nazwy typu Europe/Warsaw i America/New_York pochodzą z bazy IANA Time Zone Database.\n"
                "To ona definiuje reguły DST i historyczne zmiany czasu.\n\n"
                "Python `zoneinfo` korzysta z tej bazy, dlatego wyniki są spójne z systemem."
            ),
            "en": (
                "IANA stands for *Internet Assigned Numbers Authority*.\n"
                "Names like Europe/Warsaw and America/New_York come from the IANA Time Zone Database.\n"
                "It defines DST rules and historical transitions.\n\n"
                "Python `zoneinfo` uses this database, keeping results system-consistent."
            ),
        },
    },
    "dst": {
        "icon": "🌗",
        "label": {"pl": "DST lato/zima", "en": "DST summer/winter"},
        "title": {"pl": "Dlaczego różnica godzin czasem się zmienia", "en": "Why hour differences sometimes change"},
        "body": {
            "pl": (
                "DST to *Daylight Saving Time* (czas letni/zimowy).\n"
                "Część krajów przesuwa zegar sezonowo, co zmienia różnicę między miastami.\n\n"
                "W aplikacji widzisz to w offsetach, skrócie strefy i profilu sezonowym."
            ),
            "en": (
                "DST stands for *Daylight Saving Time*.\n"
                "Some countries shift clocks seasonally, which changes city-to-city differences.\n\n"
                "You can see it in offsets, abbreviations, and seasonal profiles."
            ),
        },
    },
    "convert": {
        "icon": "🔄",
        "label": {"pl": "Konwersja czasu", "en": "Time conversion"},
        "title": {"pl": "Konwerter krok po kroku", "en": "Converter step by step"},
        "body": {
            "pl": (
                "1) Wpisz godzinę i datę (lub samą godzinę).\n"
                "2) Wybierz strefę źródła (IANA, skrót albo UTC+/-).\n"
                "3) Wybierz strefę docelową albo tryb „do czasu bazowego”.\n\n"
                "Wynik zawsze opisuje ten sam punkt czasu."
            ),
            "en": (
                "1) Enter date/time (or just time).\n"
                "2) Choose source zone (IANA, abbreviation, or UTC+/-).\n"
                "3) Choose target zone or “convert to base time”.\n\n"
                "The output always represents the same instant."
            ),
        },
    },
    "pitfalls": {
        "icon": "⚠️",
        "label": {"pl": "Najczęstsze pułapki", "en": "Common pitfalls"},
        "title": {"pl": "Błędy, które najczęściej psują konwersję", "en": "Mistakes that most often break conversion"},
        "body": {
            "pl": (
                "• Mieszanie skrótów i offsetów bez daty.\n"
                "• Ignorowanie DST.\n"
                "• Używanie samej nazwy miasta przy nazwach wieloznacznych.\n\n"
                "Najbezpieczniej: pełna strefa IANA + data + godzina."
            ),
            "en": (
                "• Mixing abbreviations and offsets without a date.\n"
                "• Ignoring DST.\n"
                "• Using city names alone when names are ambiguous.\n\n"
                "Safest approach: full IANA zone + date + time."
            ),
        },
    },
}

EDUCATION_HISTORY: dict[str, str] = {
    "pl": (
        "📚 Tło historyczne oznaczeń czasu\n\n"
        "🕰️ 1884: Konferencja Międzynarodowego Południka w Waszyngtonie\n"
        "Ustalono południk zerowy w Greenwich i podział świata na strefy.\n\n"
        "🚂 Koniec XIX wieku: koleje i telegraf\n"
        "Szybki transport i komunikacja wymusiły standaryzację czasu.\n\n"
        "📡 1972: narodziny UTC\n"
        "UTC połączył czas atomowy z korektami astronomicznymi (sekundy przestępne).\n\n"
        "💾 Era komputerowa: baza IANA Time Zone Database\n"
        "Pojawiła się potrzeba utrzymywania historycznych i regionalnych zmian w jednym standardzie.\n\n"
        "🔎 Ciekawostki:\n"
        "• Nie wszystkie kraje stosują DST.\n"
        "• Nie wszystkie offsety są pełnymi godzinami (np. UTC+05:30, UTC+05:45).\n"
        "• Decyzje o zmianie czasu bywają polityczne i potrafią zmieniać się szybko."
    ),
    "en": (
        "📚 Historical background of time notation\n\n"
        "🕰️ 1884: International Meridian Conference (Washington)\n"
        "The prime meridian in Greenwich was adopted and global zoning was formalized.\n\n"
        "🚂 Late 19th century: railways and telegraph\n"
        "Fast transport and communication required standardized timekeeping.\n\n"
        "📡 1972: UTC introduced\n"
        "UTC combined atomic time with astronomical corrections (leap seconds).\n\n"
        "💾 Computer era: IANA Time Zone Database\n"
        "A global standard became necessary to track historical and regional rule changes.\n\n"
        "🔎 Fun facts:\n"
        "• Not all countries use DST.\n"
        "• Not all offsets are full hours (e.g., UTC+05:30, UTC+05:45).\n"
        "• Time policies can be political and may change quickly."
    ),
}

EDUCATION_TREE: list[tuple[str, str | None]] = [
    ("root", None),
    ("utc", "root"),
    ("offset", "root"),
    ("abbr", "root"),
    ("iana", "root"),
    ("dst", "root"),
    ("convert", "root"),
    ("pitfalls", "root"),
]

LANGUAGES = {"pl": "Polski", "en": "English"}

I18N: dict[str, dict[str, str]] = {
    "lang_label": {"pl": "Język:", "en": "Language:"},
    "theme_label": {"pl": "Motyw:", "en": "Theme:"},
    "auto_night": {"pl": "Auto nocny", "en": "Auto night"},
    "base_time": {"pl": "Czas bazowy", "en": "Base time"},
    "tab_world": {"pl": "Czasy Świata", "en": "World Times"},
    "tab_search": {"pl": "Szukaj Miasta/Kraju", "en": "Search City/Country"},
    "tab_universal": {"pl": "Uniwersalne Czasy", "en": "Universal Times"},
    "tab_converter": {"pl": "Konwerter", "en": "Converter"},
    "tab_compare": {"pl": "Kalkulator Porównań", "en": "Comparison"},
    "tab_education": {"pl": "Edukacja", "en": "Education"},
    "tab_map": {"pl": "Mapa Świata", "en": "World Map"},
    "tab_tiles": {"pl": "Kafelki Czasu", "en": "Time Tiles"},
    "tab_alarms": {"pl": "Alarmy i Timery", "en": "Alarms & Timers"},
    "tab_links": {"pl": "Źródła Czasu", "en": "Time Sources"},
    "status_search_hint": {
        "pl": "Wpisz kraj, kod ISO (np. PL) albo miasto (np. Warszawa, Tokio). Działa też wyszukiwanie online.",
        "en": "Enter a country, ISO code (e.g., PL) or city (e.g., Warsaw, Tokyo). Online lookup is supported.",
    },
    "search_source_hint": {
        "pl": "Pełny opis źródła dopasowania pojawi się tutaj.",
        "en": "Full match-source description will be shown here.",
    },
    "tile_status_hint": {
        "pl": "Dodaj miasto/strefę, aby utworzyć kafelek czasu.",
        "en": "Add a city/time zone to create a time tile.",
    },
    "compare_hint": {"pl": "Wpisz dwie lokalizacje i kliknij Porównaj.", "en": "Enter two locations and click Compare."},
}

TIME_LINKS: list[dict[str, object]] = [
    {
        "title": {"pl": "NIST time.gov", "en": "NIST time.gov"},
        "url": "https://time.gov",
        "desc": {
            "pl": "Oficjalny czas USA z NIST. Publiczna synchronizacja UTC i odchyłki zegarów.",
            "en": "Official US time from NIST. Public UTC sync and clock offsets.",
        },
    },
    {
        "title": {"pl": "BIPM – UTC/TAI", "en": "BIPM – UTC/TAI"},
        "url": "https://www.bipm.org/en/work-programme/time",
        "desc": {
            "pl": "Międzynarodowe Biuro Miar publikuje definicje UTC/TAI i metrologię czasu.",
            "en": "BIPM publishes UTC/TAI references and time metrology standards.",
        },
    },
    {
        "title": {"pl": "IERS – biuletyny (sekundy przestępne)", "en": "IERS – bulletins (leap seconds)"},
        "url": "https://www.iers.org/IERS/EN/Publications/Bulletins/bulletins.html",
        "desc": {
            "pl": "Biuletyny C i D o sekundach przestępnych i różnicach UT1–UTC.",
            "en": "Bulletins C and D with leap-second decisions and UT1–UTC offsets.",
        },
    },
    {
        "title": {"pl": "USNO – Precise Time", "en": "USNO – Precise Time"},
        "url": "https://www.usno.navy.mil/USNO/time",
        "desc": {
            "pl": "US Naval Observatory: precyzyjne serwisy czasu i odniesienia UTC.",
            "en": "US Naval Observatory time services and UTC references.",
        },
    },
    {
        "title": {"pl": "NPL Time (UK)", "en": "NPL Time (UK)"},
        "url": "https://www.npl.co.uk/npltime",
        "desc": {
            "pl": "Narodowe Laboratorium Fizyczne UK: źródła czasu i synchronizacja.",
            "en": "UK National Physical Laboratory time sources and sync services.",
        },
    },
    {
        "title": {"pl": "PTB Time & Frequency", "en": "PTB Time & Frequency"},
        "url": "https://www.ptb.de/cms/en/ptb/fachabteilungen/abtq/zeit-und-frequenz.html",
        "desc": {
            "pl": "Niemiecki PTB: skale czasu, UTC(PTB) i pomiary częstotliwości.",
            "en": "Germany’s PTB: time scales, UTC(PTB), and frequency standards.",
        },
    },
]

PHASE_LABELS: dict[str, dict[str, str]] = {
    "night": {"pl": "Noc", "en": "Night"},
    "morning": {"pl": "Poranek", "en": "Morning"},
    "day": {"pl": "Dzień", "en": "Day"},
    "afternoon": {"pl": "Popołudnie", "en": "Afternoon"},
    "evening": {"pl": "Wieczór", "en": "Evening"},
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


def parse_utc_offset_minutes(raw: str) -> int | None:
    text = normalize(raw)
    if not text:
        return None

    compact = text.replace(" ", "")
    compact = compact.replace("utcplus", "utc+").replace("gmtplus", "gmt+")
    compact = compact.replace("utcminus", "utc-").replace("gmtminus", "gmt-")
    compact = compact.replace("plus", "+").replace("minus", "-")

    match = re.fullmatch(r"(?:utc|gmt)?([+-])(\d{1,2})(?::?(\d{2}))?", compact)
    if not match:
        return None

    sign = 1 if match.group(1) == "+" else -1
    hours = int(match.group(2))
    minutes = int(match.group(3) or "0")
    if hours > 14 or minutes > 59:
        return None
    if hours == 14 and minutes != 0:
        return None
    return sign * (hours * 60 + minutes)


def compact_source_label(source: str, max_len: int = 34) -> str:
    cleaned = source.strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "..."


def wrap_source_text(source: str, width: int = 78) -> str:
    cleaned = source.strip()
    if not cleaned:
        return "-"
    exploded = cleaned.replace(", ", ",\n")
    wrapped_lines: list[str] = []
    for line in exploded.splitlines():
        chunks = textwrap.wrap(line, width=width, break_long_words=False, break_on_hyphens=False)
        wrapped_lines.extend(chunks or [""])
    return "\n".join(wrapped_lines)


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    raw = color.strip().lstrip("#")
    if len(raw) != 6:
        return 0, 0, 0
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{max(0, min(255, r)):02X}{max(0, min(255, g)):02X}{max(0, min(255, b)):02X}"


def blend_hex(color_a: str, color_b: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, ratio))
    ar, ag, ab = hex_to_rgb(color_a)
    br, bg, bb = hex_to_rgb(color_b)
    mixed = (
        int(ar + (br - ar) * ratio),
        int(ag + (bg - ag) * ratio),
        int(ab + (bb - ab) * ratio),
    )
    return rgb_to_hex(mixed)


def format_diff(delta: timedelta) -> str:
    total_minutes = int(delta.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


def day_phase(hour: int) -> str:
    if 5 <= hour < 10:
        return "morning"
    if 10 <= hour < 14:
        return "day"
    if 14 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 22:
        return "evening"
    return "night"


def phase_label(phase_key: str, language: str = "pl") -> str:
    labels = PHASE_LABELS.get(phase_key, PHASE_LABELS["day"])
    return labels.get(language, labels["pl"])


def is_dst_active(dt: datetime) -> bool:
    dst = dt.dst()
    return bool(dst and dst.total_seconds() != 0)


def _last_weekday(year: int, month: int, weekday: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    if n < 0:
        return _last_weekday(year, month, weekday)
    d = date(year, month, 1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    d += timedelta(days=7 * (n - 1))
    return d


def _local_transition_utc(year: int, month: int, weekday: int, n: int, hour: int, offset_minutes: int) -> datetime:
    transition_date = _nth_weekday(year, month, weekday, n)
    local_dt = datetime(year, month, transition_date.day, hour, 0)
    return (local_dt - timedelta(minutes=offset_minutes)).replace(tzinfo=timezone.utc)


def _is_dst_eu(dt_utc: datetime) -> bool:
    year = dt_utc.year
    start = datetime(year, 3, _last_weekday(year, 3, 6).day, 1, 0, tzinfo=timezone.utc)
    end = datetime(year, 10, _last_weekday(year, 10, 6).day, 1, 0, tzinfo=timezone.utc)
    return start <= dt_utc < end


def _is_dst_us(dt_utc: datetime, std_offset: int, dst_offset: int) -> bool:
    year = dt_utc.year
    start = _local_transition_utc(year, 3, 6, 2, 2, std_offset)
    end = _local_transition_utc(year, 11, 6, 1, 2, dst_offset)
    return start <= dt_utc < end


def _is_dst_southern(
    dt_utc: datetime,
    std_offset: int,
    dst_offset: int,
    start_month: int,
    start_weekday: int,
    start_week: int,
    start_hour: int,
    end_month: int,
    end_weekday: int,
    end_week: int,
    end_hour: int,
) -> bool:
    year = dt_utc.year
    start = _local_transition_utc(year, start_month, start_weekday, start_week, start_hour, std_offset)
    end = _local_transition_utc(year, end_month, end_weekday, end_week, end_hour, dst_offset)
    if start < end:
        return start <= dt_utc < end
    if dt_utc >= start:
        return True
    return dt_utc < end


def fallback_offset(dt_utc: datetime, zone_id: str) -> tuple[int, str]:
    rule = FALLBACK_ZONE_RULES.get(zone_id)
    if not rule:
        return 0, "UTC"
    std_offset = int(rule.get("std", 0))
    dst_offset = int(rule.get("dst", std_offset))
    abbr_std = str(rule.get("abbr_std", "UTC"))
    abbr_dst = str(rule.get("abbr_dst", abbr_std))
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)

    is_dst = False
    rule_key = str(rule.get("rule", ""))
    if dst_offset != std_offset and rule_key:
        if rule_key == "eu":
            is_dst = _is_dst_eu(dt_utc)
        elif rule_key == "us":
            is_dst = _is_dst_us(dt_utc, std_offset, dst_offset)
        elif rule_key == "aus":
            is_dst = _is_dst_southern(dt_utc, std_offset, dst_offset, 10, 6, 1, 2, 4, 6, 1, 3)
        elif rule_key == "nz":
            is_dst = _is_dst_southern(dt_utc, std_offset, dst_offset, 9, 6, -1, 2, 4, 6, 1, 3)

    offset = dst_offset if is_dst else std_offset
    abbr = abbr_dst if is_dst else abbr_std
    return offset, abbr


def seasonal_offset_description(zone_id: str, year: int, language: str = "pl") -> str:
    try:
        zone = ZoneInfo(zone_id)
        january = datetime(year, 1, 15, 12, 0, tzinfo=zone)
        july = datetime(year, 7, 15, 12, 0, tzinfo=zone)
        jan_name = january.tzname() or "-"
        jul_name = july.tzname() or "-"
        jan_off = format_offset(january.utcoffset())
        jul_off = format_offset(july.utcoffset())
    except Exception:
        jan_utc = datetime(year, 1, 15, 12, 0, tzinfo=timezone.utc)
        jul_utc = datetime(year, 7, 15, 12, 0, tzinfo=timezone.utc)
        jan_offset, jan_name = fallback_offset(jan_utc, zone_id)
        jul_offset, jul_name = fallback_offset(jul_utc, zone_id)
        jan_off = format_offset(timedelta(minutes=jan_offset))
        jul_off = format_offset(timedelta(minutes=jul_offset))

    if jan_name == jul_name and jan_off == jul_off:
        return f"{jan_name} ({jan_off})"
    if language == "en":
        return f"winter: {jan_name} {jan_off} | summer: {jul_name} {jul_off}"
    return f"zima: {jan_name} {jan_off} | lato: {jul_name} {jul_off}"


def _read_tab_file(filename: str) -> list[str]:
    try:
        import importlib.resources as resources

        for package, relative_parts in (("tzdata.zoneinfo", [filename]), ("tzdata", ["zoneinfo", filename])):
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
        candidates = [base / filename, base / "tzdata" / filename, base / "zoneinfo" / filename]
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

    normalized_lookup: dict[str, list[str]] = {}
    for key, codes in country_lookup.items():
        normalized_lookup[key] = sorted(set(codes))

    normalized_zone_map: dict[str, list[str]] = {}
    for code, zones in code_to_zones.items():
        normalized_zone_map[code] = sorted(set(zones))

    return normalized_lookup, code_to_country, normalized_zone_map


def parse_time_input(raw: str, now_in_source: datetime) -> datetime | None:
    value = raw.strip()
    if not value:
        return now_in_source.replace(second=0, microsecond=0)

    formats_with_date = [
        "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S",
        "%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %I:%M %p", "%d.%m.%Y %I:%M %p",
    ]
    formats_time_only = ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"]

    for fmt in formats_with_date:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=now_in_source.tzinfo)
        except ValueError:
            continue

    for fmt in formats_time_only:
        try:
            parsed = datetime.strptime(value, fmt)
            return now_in_source.replace(hour=parsed.hour, minute=parsed.minute, second=parsed.second, microsecond=0)
        except ValueError:
            continue

    return None


def format_duration_abs(delta: timedelta) -> str:
    total_minutes = abs(int(delta.total_seconds() // 60))
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h" if minutes == 0 else f"{hours}h {minutes}m"


def comparison_summary(place_a: str, place_b: str, delta_b_minus_a: timedelta) -> str:
    minutes = int(delta_b_minus_a.total_seconds() // 60)
    if minutes == 0:
        return f"W {place_b} i w {place_a} jest ta sama godzina."
    if minutes > 0:
        return f"W {place_b} jest {format_duration_abs(delta_b_minus_a)} później niż w {place_a}."
    return f"W {place_b} jest {format_duration_abs(delta_b_minus_a)} wcześniej niż w {place_a}."


def comparison_summary_en(place_a: str, place_b: str, delta_b_minus_a: timedelta) -> str:
    minutes = int(delta_b_minus_a.total_seconds() // 60)
    if minutes == 0:
        return f"{place_b} and {place_a} have the same time."
    if minutes > 0:
        return f"{place_b} is {format_duration_abs(delta_b_minus_a)} ahead of {place_a}."
    return f"{place_b} is {format_duration_abs(delta_b_minus_a)} behind {place_a}."


def parse_hhmm(value: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", value)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    return None


def parse_alarm_time(value: str) -> tuple[int, int, int] | None:
    raw = value.strip()
    if not raw:
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.hour, parsed.minute, parsed.second
        except ValueError:
            continue
    return None


def normalize_hhmm(value: str, fallback: str) -> str:
    parsed = parse_alarm_time(value.strip())
    if not parsed:
        parsed = parse_alarm_time(fallback)
    if not parsed:
        return fallback
    hour, minute, _second = parsed
    return f"{hour:02d}:{minute:02d}"


def parse_alarm_date(value: str) -> date | None:
    raw = value.strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def format_hhmmss(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_hhmmss_ms(total_seconds: float) -> str:
    total_seconds = max(0.0, float(total_seconds))
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    millis = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


@dataclass
class SearchResult:
    zone_id: str
    score: int
    source: str


@dataclass
class TileCard:
    card_id: int
    frame: ttk.Frame
    canvas: tk.Canvas
    title_label: ttk.Label
    digital_label: ttk.Label
    meta_label: ttk.Label
    phase_label: tk.Label
    session_label: tk.Label
    zone_id: str
    title: str
    session_key: str
    x: int = 0
    y: int = 0
    width: int = 360
    height: int = 440
    window_id: int | None = None
    resize_handle: tk.Label | None = None
    gloss_canvas: tk.Canvas | None = None

class TimeZoneEngine:
    def __init__(self) -> None:
        self.country_lookup, self.code_to_country, self.code_to_zones = load_country_timezone_index()
        all_zones = sorted(available_timezones())
        tab_zones = {zone for zones in self.code_to_zones.values() for zone in zones}
        if tab_zones:
            all_zones = sorted(set(all_zones).union(tab_zones))
        if FALLBACK_ZONE_IDS:
            all_zones = sorted(set(all_zones).union(FALLBACK_ZONE_IDS))
        if not all_zones:
            all_zones = ["Etc/UTC"]
        self.zone_ids = [z for z in all_zones if not z.startswith(("posix/", "right/"))]
        self.zone_set = set(self.zone_ids)
        self.zone_search_tokens = {zone: normalize(zone) for zone in self.zone_ids}
        self.zone_cache: dict[str, ZoneInfo] = {}
        self.zone_to_codes: dict[str, list[str]] = {}
        for code, zones in self.code_to_zones.items():
            for zone_id in zones:
                self.zone_to_codes.setdefault(zone_id, []).append(code)
        self._online_cache: dict[str, list[SearchResult]] = {}

    def zone(self, zone_id: str) -> ZoneInfo | None:
        if zone_id in self.zone_cache:
            return self.zone_cache[zone_id]
        try:
            zone = ZoneInfo(zone_id)
        except Exception:
            return None
        self.zone_cache[zone_id] = zone
        return zone

    def has_fallback(self, zone_id: str) -> bool:
        return zone_id in FALLBACK_ZONE_RULES

    def convert(self, dt: datetime, zone_id: str) -> datetime:
        if dt.tzinfo is None:
            dt_utc = dt.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt.astimezone(timezone.utc)
        zone = self.zone(zone_id)
        if zone is not None:
            return dt_utc.astimezone(zone)
        offset_minutes, abbr = fallback_offset(dt_utc, zone_id)
        tz = timezone(timedelta(minutes=offset_minutes), name=abbr)
        return dt_utc.astimezone(tz)

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
            zone = self.zone(zone_id)
            if zone is None:
                continue
            zoned = now_local.astimezone(zone)
            if zoned.tzname() == local_name and zoned.utcoffset() == local_offset:
                candidates.append(zone_id)
                if len(candidates) > 15:
                    break
        return candidates[0] if len(candidates) == 1 else None

    def country_names_for_zone(self, zone_id: str) -> list[str]:
        codes = self.zone_to_codes.get(zone_id, [])
        names = [self.code_to_country.get(code, code) for code in codes]
        return sorted(set(names))

    def zones_for_offset(self, offset_minutes: int, at_utc: datetime | None = None, limit: int = 60) -> list[str]:
        utc_now = at_utc or datetime.now(timezone.utc)
        matches: list[str] = []
        for zone_id in self.zone_ids:
            zone = self.zone(zone_id)
            if zone is not None:
                zoned = utc_now.astimezone(zone)
                offset = zoned.utcoffset() or timedelta(0)
            else:
                offset_min, _abbr = fallback_offset(utc_now, zone_id)
                offset = timedelta(minutes=offset_min)
            if int(offset.total_seconds() // 60) == offset_minutes:
                matches.append(zone_id)
                if len(matches) >= limit:
                    break
        return matches

    def representative_zone_for_offset(self, offset_minutes: int, at_utc: datetime | None = None) -> str | None:
        matches = self.zones_for_offset(offset_minutes, at_utc=at_utc, limit=120)
        if not matches:
            return None

        preferred = OFFSET_REPRESENTATIVE_ZONE.get(offset_minutes)
        if preferred and preferred in matches:
            return preferred

        for zone_id in matches:
            if not zone_id.startswith("Etc/"):
                return zone_id
        return matches[0]

    def offset_hint_context(self, offset_minutes: int, at_utc: datetime | None = None) -> str:
        offset_text = format_offset(timedelta(minutes=offset_minutes))
        representative = self.representative_zone_for_offset(offset_minutes, at_utc=at_utc)
        if not representative:
            return f"Wpisano offset {offset_text}. Ten offset może być wspólny dla wielu regionów."

        countries = self.country_names_for_zone(representative)
        if countries:
            return (
                f"Wpisano offset {offset_text}. Przykładowa strefa: {representative} "
                f"(kraj: {countries[0]}). Uwaga: offset nie wskazuje jednego kraju."
            )
        return f"Wpisano offset {offset_text}. Przykładowa strefa: {representative}. Uwaga: offset nie wskazuje jednego kraju."

    def resolve_zone_hint(self, query: str, allow_online: bool = True) -> str | None:
        raw = query.strip()
        if not raw:
            return None

        offset_minutes = parse_utc_offset_minutes(raw)
        if offset_minutes is not None:
            zone_id = self.representative_zone_for_offset(offset_minutes)
            if zone_id:
                return zone_id

        upper = raw.upper()
        mapped = TZ_ABBREVIATION_MAP.get(upper)
        if mapped and mapped in self.zone_set:
            return mapped

        if raw in self.zone_set:
            return raw

        for zone_id in self.zone_ids:
            if zone_id.casefold() == raw.casefold():
                return zone_id

        normalized = normalize(raw)
        if not normalized:
            return None

        for zone_id in self.zone_ids:
            city_norm = normalize(zone_id.split("/")[-1])
            if normalized == city_norm:
                return zone_id

        if upper in self.code_to_zones and self.code_to_zones[upper]:
            return self.code_to_zones[upper][0]

        country_codes = self.country_lookup.get(normalized, [])
        for code in country_codes:
            zones = self.code_to_zones.get(code, [])
            if zones:
                return zones[0]

        results = self.search(raw, limit=1, include_online=allow_online)
        return results[0].zone_id if results else None

    def search(self, query: str, limit: int = 80, include_online: bool = True) -> list[SearchResult]:
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

        mapped = TZ_ABBREVIATION_MAP.get(query_upper)
        abbreviation_query = mapped is not None
        if mapped:
            add_result(mapped, 182, f"skrót {query_upper}")

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
                add_result(zone_id, 160, "dokładna nazwa strefy")
                continue

            if zone_id.casefold() == query.strip().casefold():
                if abbreviation_query:
                    continue
                add_result(zone_id, 190, "dokładna nazwa IANA")
                continue

            city = zone_id.split("/")[-1].replace("_", " ")
            city_norm = normalize(city)
            if normalized == city_norm:
                add_result(zone_id, 155, "dokładna nazwa miasta")
                continue

            if city_norm.startswith(normalized):
                add_result(zone_id, 145, "miasto")
                continue

            if normalized in token:
                add_result(zone_id, 120, "dopasowanie strefy")

        if include_online:
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
                if not zone_id or zone_id not in self.zone_set or zone_id in seen:
                    continue

                seen.add(zone_id)
                results.append(SearchResult(zone_id=zone_id, score=118, source=f"online: {display_name}"))
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
        req = Request(url, headers={"User-Agent": "WorldTimeSpecialist/1.1 (desktop-app)", "Accept": "application/json"})
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
        req = Request(url, headers={"User-Agent": "WorldTimeSpecialist/1.1 (desktop-app)", "Accept": "application/json"})
        with urlopen(req, timeout=5) as response:
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        zone_id = data.get("timezone") if isinstance(data, dict) else None
        return zone_id if isinstance(zone_id, str) else None

class TimeSpecialistApp(tk.Tk):
    REFRESH_MS = 1000

    def __init__(self) -> None:
        super().__init__()
        try:
            self.tk.call("tk", "scaling", 1.15)
        except tk.TclError:
            pass
        self._loaded_settings = self._load_settings_file()
        loaded_theme = str(self._loaded_settings.get("theme", DEFAULT_THEME))
        if loaded_theme not in THEMES:
            loaded_theme = DEFAULT_THEME
        loaded_auto_night = bool(self._loaded_settings.get("auto_night", False))
        self.theme_name = loaded_theme
        self.auto_night_enabled = loaded_auto_night
        self.current_theme_name = ""
        self.theme_palette = THEMES[DEFAULT_THEME]
        self.phase_bg = dict(PHASE_BG)

        self.title(APP_TITLE)
        self.geometry("1760x980")
        self.minsize(1280, 800)
        saved_geometry = str(self._loaded_settings.get("window_geometry", "")).strip()
        if saved_geometry:
            try:
                self.geometry(saved_geometry)
            except tk.TclError:
                pass
        self.configure(bg=str(self.theme_palette.get("app_bg", "#0B132B")))

        self.engine = TimeZoneEngine()
        self.system_zone_key = self.engine.detect_local_zone_key() or "Europe/Warsaw"
        if self.system_zone_key not in self.engine.zone_set and self.engine.zone_ids:
            self.system_zone_key = self.engine.zone_ids[0]
        self.iana_zone_values = sorted(self.engine.zone_ids)
        self.city_zone_values, self.city_zone_lookup = self._build_city_zone_values(self.iana_zone_values)

        saved_manual = str(self._loaded_settings.get("manual_zone_resolved", self.system_zone_key))
        self.manual_zone_resolved = saved_manual if saved_manual in self.engine.zone_set else self.system_zone_key
        self.search_results: list[SearchResult] = []
        self.search_source_by_zone: dict[str, str] = {}
        self.selected_zone: str | None = None

        self.tile_cards: list[TileCard] = []
        self.focus_tile_cards: list[TileCard] = []
        self.next_tile_id = 1
        self.fullscreen_enabled = False
        self.tile_focus_window: tk.Toplevel | None = None
        self.focus_tiles_canvas: tk.Canvas | None = None
        self.focus_tiles_inner: ttk.Frame | None = None
        self.focus_tiles_window: int | None = None
        self.focus_tiles_scroll: ttk.Scrollbar | None = None
        self.tile_drag_state: dict[str, int] | None = None
        self.tile_resize_state: dict[str, int] | None = None
        self.focus_auto_layout = True
        self.tiles_grid_layout = False
        self.fullscreen_auto_layout_var = tk.BooleanVar(value=bool(self._loaded_settings.get("fullscreen_auto_layout", True)))

        base_mode_loaded = str(self._loaded_settings.get("base_mode", "auto"))
        if base_mode_loaded not in ("auto", "manual"):
            base_mode_loaded = "auto"
        manual_base_loaded = str(self._loaded_settings.get("manual_base_zone", self.manual_zone_resolved))

        self.base_mode_var = tk.StringVar(value=base_mode_loaded)
        self.manual_base_zone_var = tk.StringVar(value=manual_base_loaded)
        language_loaded = str(self._loaded_settings.get("language", "pl")).strip().lower()
        if language_loaded not in LANGUAGES:
            language_loaded = "pl"
        self.language_var = tk.StringVar(value=language_loaded)
        self.base_notice_var = tk.StringVar(value="Tryb AUTO: bazowa strefa = lokalna strefa systemu.")
        self.theme_var = tk.StringVar(value=loaded_theme)
        self.theme_display_var = tk.StringVar(value="")
        self.auto_night_var = tk.BooleanVar(value=loaded_auto_night)
        loaded_auto_night_start = normalize_hhmm(str(self._loaded_settings.get("auto_night_start", AUTO_NIGHT_DEFAULT_START)), AUTO_NIGHT_DEFAULT_START)
        loaded_auto_night_stop = normalize_hhmm(str(self._loaded_settings.get("auto_night_stop", AUTO_NIGHT_DEFAULT_STOP)), AUTO_NIGHT_DEFAULT_STOP)
        self.auto_night_start_var = tk.StringVar(value=loaded_auto_night_start)
        self.auto_night_stop_var = tk.StringVar(value=loaded_auto_night_stop)

        self.base_time_var = tk.StringVar(value="--:--:--")
        self.base_info_var = tk.StringVar(value="")
        self.system_info_var = tk.StringVar(value="")

        self.status_var = tk.StringVar(value=I18N["status_search_hint"]["pl"])
        self.search_query_var = tk.StringVar(value=str(self._loaded_settings.get("search_query", "")))
        self.detail_header_var = tk.StringVar(value="Wybierz lokalizację z listy wyników.")
        self.detail_body_var = tk.StringVar(value="Tutaj zobaczysz szczegóły strefy i relacje do czasu bazowego.")
        self.search_source_full_var = tk.StringVar(value=I18N["search_source_hint"]["pl"])

        converter_mode_loaded = str(self._loaded_settings.get("converter_target_mode", "base"))
        if converter_mode_loaded not in ("base", "manual"):
            converter_mode_loaded = "base"
        self.converter_input_var = tk.StringVar(value=str(self._loaded_settings.get("converter_input", "10:15")))
        self.converter_source_zone_var = tk.StringVar(value=str(self._loaded_settings.get("converter_source_zone", "EST")))
        self.converter_target_mode_var = tk.StringVar(value=converter_mode_loaded)
        self.converter_target_zone_var = tk.StringVar(value=str(self._loaded_settings.get("converter_target_zone", "Europe/Warsaw")))
        self.converter_live_var = tk.BooleanVar(value=bool(self._loaded_settings.get("converter_live", True)))
        self.converter_result_var = tk.StringVar(value="")
        self.converter_detail_var = tk.StringVar(value="")

        self.compare_a_var = tk.StringVar(value=str(self._loaded_settings.get("compare_a", "Warszawa")))
        self.compare_b_var = tk.StringVar(value=str(self._loaded_settings.get("compare_b", "New York")))
        self.compare_reference_time_var = tk.StringVar(value=str(self._loaded_settings.get("compare_reference_time", "")))
        self.compare_reference_zone_var = tk.StringVar(value=str(self._loaded_settings.get("compare_reference_zone", "")))
        self.compare_status_var = tk.StringVar(value=I18N["compare_hint"]["pl"])
        self.compare_result_var = tk.StringVar(value="")

        self.education_selected_topic = "root"
        self.education_title_var = tk.StringVar(value="")
        self.education_body_var = tk.StringVar(value="")

        self.tile_query_var = tk.StringVar(value=str(self._loaded_settings.get("tile_query", "")))
        loaded_tile_session = self._resolve_session_key(str(self._loaded_settings.get("tile_session", "Brak sesji")))
        if loaded_tile_session not in SESSION_PRESETS:
            loaded_tile_session = "Brak sesji"
        self.tile_session_var = tk.StringVar(value=loaded_tile_session)
        self.tile_status_var = tk.StringVar(value=I18N["tile_status_hint"]["pl"])
        self.session_sound_enabled_var = tk.BooleanVar(value=bool(self._loaded_settings.get("session_sound_enabled", True)))
        self.tile_ticking_var = tk.BooleanVar(value=bool(self._loaded_settings.get("tile_ticking", False)))
        self.session_state_cache: dict[int, bool] = {}
        self.ticking_after_id: str | None = None
        self.ticking_generation = 0
        self.any_session_active = False
        self.sound_muted = bool(self._loaded_settings.get("sound_muted", False))
        self.tray_icon: object | None = None
        self.tray_thread: threading.Thread | None = None
        self.tray_install_in_progress = False
        self.pending_tray_minimize = False
        self.minimize_on_start_var = tk.BooleanVar(value=bool(self._loaded_settings.get("minimize_on_start", True)))

        self.alarms: list[dict[str, object]] = []
        self.alarm_last_fire: dict[int, str] = {}
        self.alarm_selected_id: int | None = None
        self.next_alarm_id = 1
        self.alarm_label_var = tk.StringVar(value=self._t("Alarm", "Alarm"))
        self.alarm_zone_var = tk.StringVar(value=self.system_zone_key)
        self.alarm_time_var = tk.StringVar(value="08:00")
        self.alarm_date_var = tk.StringVar(value="")
        self.alarm_day_var = tk.StringVar(value="")
        self.alarm_month_var = tk.StringVar(value="")
        self.alarm_year_var = tk.StringVar(value="")
        self.alarm_enabled_var = tk.BooleanVar(value=True)
        self.alarms_paused_var = tk.BooleanVar(value=bool(self._loaded_settings.get("alarms_paused", False)))
        self.alarm_duration_var = tk.StringVar(value="20")
        self.alarm_sound_display_var = tk.StringVar(value="")
        self.alarm_sound_id_var = tk.StringVar(value=str(self._loaded_settings.get("alarm_sound_default", DEFAULT_ALARM_SOUND_ID)))
        self.alarm_script_var = tk.StringVar(value="")
        self.alarm_status_var = tk.StringVar(value="")

        self.stopwatch_running = False
        self.stopwatch_start: datetime | None = None
        self.stopwatch_elapsed = timedelta(0)
        self.stopwatch_time_var = tk.StringVar(value="00:00:00.000")
        self.stopwatch_after_id: str | None = None

        self.timer_running = False
        self.timer_end_time: datetime | None = None
        self.timer_remaining_var = tk.StringVar(value="00:00:00")
        self.timer_minutes_var = tk.StringVar(value=str(self._loaded_settings.get("timer_minutes", "5")))
        self.timer_seconds_var = tk.StringVar(value=str(self._loaded_settings.get("timer_seconds", "00")))
        self.timer_repeat_var = tk.BooleanVar(value=bool(self._loaded_settings.get("timer_repeat", False)))
        self.timer_repeat_minutes_var = tk.StringVar(value=str(self._loaded_settings.get("timer_repeat_minutes", "30")))
        self.timer_script_var = tk.StringVar(value=str(self._loaded_settings.get("timer_script", "")))
        self.timer_repeat_interval = 0
        self.timer_remaining_seconds = 0
        self.timer_input_total = 0
        self.timer_pause_start: datetime | None = None
        self.settings_dirty = False
        self.settings_save_after_id: str | None = None
        self._i18n_widgets: list[tuple[tk.Widget, str, str, str]] = []

        self._load_alarms_from_settings()

        self._setup_styles()
        self._build_ui()
        self._apply_theme(force=True)
        self._on_base_mode_change()
        self._run_search()
        self._run_comparison()
        if not self._load_tiles_from_settings():
            self._add_default_tiles()

        self._wire_setting_traces()

        self.bind("<Escape>", self._on_escape)
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)

        self._refresh_loop()
        self.after(800, self._auto_minimize_if_autostart)

    def _setup_styles(self) -> None:
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("Action.TButton", font=("Bahnschrift", 11, "bold"), padding=(12, 8))
        self.style.configure("Search.TEntry", padding=(10, 7))
        self.style.configure("TNotebook.Tab", font=("Bahnschrift", 12, "bold"), padding=(18, 12))
        self.style.configure("Treeview", rowheight=34, borderwidth=0, font=("Bahnschrift", 11))
        self.style.configure("Treeview.Heading", font=("Bahnschrift", 11, "bold"), relief="flat")
        self.style.configure("AlarmStatus.TLabel", font=("Bahnschrift", 11, "bold"), foreground="#FF5A5A")

    def _t(self, pl: str, en: str) -> str:
        return en if self.language_var.get() == "en" else pl

    def _bind_i18n(self, widget: tk.Widget, option: str, pl: str, en: str) -> None:
        self._i18n_widgets.append((widget, option, pl, en))
        try:
            widget.configure(**{option: self._t(pl, en)})
        except tk.TclError:
            pass

    def _build_city_zone_values(self, zone_ids: list[str]) -> tuple[list[str], dict[str, str]]:
        values: list[str] = []
        lookup: dict[str, str] = {}
        for zone_id in zone_ids:
            if not zone_id:
                continue
            city = zone_id.split("/")[-1].replace("_", " ")
            display = f"{city} — {zone_id}"
            values.append(display)
            lookup[display] = zone_id
            if zone_id not in lookup:
                lookup[zone_id] = zone_id
        values.extend(zone_ids)
        values = sorted(set(values), key=lambda v: v.casefold())
        return values, lookup

    def _register_autocomplete(self, combo: ttk.Combobox, values: list[str], limit: int | None = None) -> None:
        if not hasattr(self, "_combo_sources"):
            self._combo_sources: dict[ttk.Combobox, list[str]] = {}
            self._combo_after: dict[ttk.Combobox, str] = {}
            self._combo_limits: dict[ttk.Combobox, int | None] = {}
        self._combo_sources[combo] = values
        self._combo_limits[combo] = limit
        effective_limit = limit if limit is not None else len(values)
        combo.configure(values=values[:effective_limit])
        combo.bind("<KeyRelease>", lambda _event, c=combo: self._schedule_combo_filter(c), add="+")

    def _schedule_combo_filter(self, combo: ttk.Combobox) -> None:
        after_id = self._combo_after.get(combo) if hasattr(self, "_combo_after") else None
        if after_id:
            try:
                self.after_cancel(after_id)
            except tk.TclError:
                pass
        self._combo_after[combo] = self.after(140, lambda c=combo: self._filter_combo_values(c))

    def _filter_combo_values(self, combo: ttk.Combobox) -> None:
        values = self._combo_sources.get(combo, []) if hasattr(self, "_combo_sources") else []
        text = combo.get().strip().casefold()
        limit = self._combo_limits.get(combo) if hasattr(self, "_combo_limits") else None
        effective_limit = len(values) if limit is None else limit
        if not text:
            combo.configure(values=values[:effective_limit])
            return

        starts = [v for v in values if v.casefold().startswith(text)]
        contains = [v for v in values if text in v.casefold() and v not in starts]
        filtered = (starts + contains)[:effective_limit]
        combo.configure(values=filtered)

    def _on_language_change(self, event: tk.Event | None = None) -> None:
        if self.language_var.get() not in LANGUAGES:
            self.language_var.set("pl")
        self._apply_language(force=True)
        self._mark_settings_dirty()

    def _apply_language(self, force: bool = False) -> None:
        self.title(self._t("Specjalista Czasu Świata", "World Time Specialist"))
        for widget, option, pl, en in self._i18n_widgets:
            try:
                widget.configure(**{option: self._t(pl, en)})
            except tk.TclError:
                continue

        self.status_var.set(I18N["status_search_hint"][self.language_var.get()])
        self.search_source_full_var.set(I18N["search_source_hint"][self.language_var.get()])
        self.compare_status_var.set(I18N["compare_hint"][self.language_var.get()])
        self.tile_status_var.set(I18N["tile_status_hint"][self.language_var.get()])
        if self.base_mode_var.get() == "auto":
            self.base_notice_var.set(self._t(f"Tryb AUTO: baza = {self.system_zone_key}", f"AUTO mode: base = {self.system_zone_key}"))
        else:
            self.base_notice_var.set(self._t(f"Tryb MANUAL: baza = {self.manual_zone_resolved}", f"MANUAL mode: base = {self.manual_zone_resolved}"))

        if hasattr(self, "notebook"):
            self.notebook.tab(self.world_tab, text=I18N["tab_world"][self.language_var.get()])
            self.notebook.tab(self.search_tab, text=I18N["tab_search"][self.language_var.get()])
            self.notebook.tab(self.universal_tab, text=I18N["tab_universal"][self.language_var.get()])
            self.notebook.tab(self.converter_tab, text=I18N["tab_converter"][self.language_var.get()])
            self.notebook.tab(self.compare_tab, text=I18N["tab_compare"][self.language_var.get()])
            self.notebook.tab(self.education_tab, text=I18N["tab_education"][self.language_var.get()])
            if hasattr(self, "map_tab"):
                self.notebook.tab(self.map_tab, text=I18N["tab_map"][self.language_var.get()])
            self.notebook.tab(self.tiles_tab, text=I18N["tab_tiles"][self.language_var.get()])
            if hasattr(self, "alarms_tab"):
                self.notebook.tab(self.alarms_tab, text=I18N["tab_alarms"][self.language_var.get()])
            if hasattr(self, "links_tab"):
                self.notebook.tab(self.links_tab, text=I18N["tab_links"][self.language_var.get()])

        self._update_tray_menu()
        self._refresh_tray_support_buttons()
        self._update_all_headings()
        self._refresh_alarm_sound_values()
        self._refresh_theme_combo_values()
        self._refresh_session_combo_values()
        self._configure_alarm_tree_tags()

        if hasattr(self, "education_tree"):
            for topic_id, _ in EDUCATION_TREE:
                topic = EDUCATION_TOPICS.get(topic_id, {})
                label_map = topic.get("label", {})
                if isinstance(label_map, dict):
                    label = str(label_map.get(self.language_var.get(), label_map.get("pl", topic_id)))
                    icon = str(topic.get("icon", "•"))
                    self.education_tree.item(topic_id, text=f"{icon} {label}")
        if hasattr(self, "education_text"):
            self._set_education_topic(self.education_selected_topic)
        if hasattr(self, "selected_zone") and self.selected_zone:
            self._update_detail_panel(self.selected_zone)
        if hasattr(self, "world_map_canvas"):
            self._draw_world_map_tab()
        if hasattr(self, "education_map_canvas"):
            self._draw_education_map()
        self._run_converter(silent=True)
        self._run_comparison()

    def _on_theme_change(self, event: tk.Event | None = None) -> None:
        selected = self.theme_display_var.get().strip() or self.theme_var.get().strip()
        resolved_theme = self._resolve_theme_name(selected)
        if resolved_theme in THEMES:
            self.theme_name = resolved_theme
            self.theme_var.set(resolved_theme)
        self.auto_night_start_var.set(normalize_hhmm(self.auto_night_start_var.get(), AUTO_NIGHT_DEFAULT_START))
        self.auto_night_stop_var.set(normalize_hhmm(self.auto_night_stop_var.get(), AUTO_NIGHT_DEFAULT_STOP))
        self.auto_night_enabled = bool(self.auto_night_var.get())
        self._refresh_theme_combo_values()
        self._apply_theme()
        self._mark_settings_dirty()

    def _effective_theme_name(self) -> str:
        base_theme = self.theme_name if self.theme_name in THEMES else DEFAULT_THEME
        if self.auto_night_enabled:
            start_h, start_m, _ = parse_alarm_time(normalize_hhmm(self.auto_night_start_var.get(), AUTO_NIGHT_DEFAULT_START)) or (21, 0, 0)
            stop_h, stop_m, _ = parse_alarm_time(normalize_hhmm(self.auto_night_stop_var.get(), AUTO_NIGHT_DEFAULT_STOP)) or (6, 0, 0)
            now_dt = datetime.now().astimezone()
            now_minutes = now_dt.hour * 60 + now_dt.minute
            start_minutes = start_h * 60 + start_m
            stop_minutes = stop_h * 60 + stop_m
            if start_minutes == stop_minutes:
                return NIGHT_THEME
            if start_minutes < stop_minutes:
                in_night_window = start_minutes <= now_minutes < stop_minutes
            else:
                in_night_window = now_minutes >= start_minutes or now_minutes < stop_minutes
            if in_night_window:
                return NIGHT_THEME
        return base_theme

    def _theme_display_name(self, theme_name: str) -> str:
        labels = THEME_LABELS.get(theme_name, {"pl": theme_name, "en": theme_name})
        return labels.get(self.language_var.get(), labels.get("pl", theme_name))

    def _city_display_name(self, city_name: str) -> str:
        labels = CITY_LABELS.get(city_name)
        if labels is None:
            for entry in CITY_LABELS.values():
                if city_name == entry.get("pl") or city_name == entry.get("en"):
                    labels = entry
                    break
        if labels is None:
            labels = {"pl": city_name, "en": city_name}
        return labels.get(self.language_var.get(), labels.get("pl", city_name))

    def _session_display_name(self, session_key: str) -> str:
        labels = SESSION_LABELS.get(session_key, {"pl": session_key, "en": session_key})
        return labels.get(self.language_var.get(), labels.get("pl", session_key))

    def _resolve_session_key(self, value: str) -> str:
        raw = value.strip()
        if raw in SESSION_PRESETS:
            return raw
        for session_key, labels in SESSION_LABELS.items():
            if raw == labels.get("pl") or raw == labels.get("en"):
                return session_key
        return raw

    def _resolve_theme_name(self, value: str) -> str | None:
        raw = value.strip()
        if raw in THEMES:
            return raw
        for theme_name, labels in THEME_LABELS.items():
            if raw == labels.get("pl") or raw == labels.get("en"):
                return theme_name
        return None

    def _refresh_theme_combo_values(self) -> None:
        if not hasattr(self, "theme_combo"):
            return
        values = [self._theme_display_name(theme_name) for theme_name in THEMES]
        self._theme_display_lookup = {self._theme_display_name(theme_name): theme_name for theme_name in THEMES}
        self.theme_combo.configure(values=values)
        self.theme_display_var.set(self._theme_display_name(self.theme_name))

    def _refresh_session_combo_values(self) -> None:
        if not hasattr(self, "tile_session_combo"):
            return
        values = [self._session_display_name(session_key) for session_key in SESSION_PRESETS]
        self.tile_session_combo.configure(values=values)
        resolved = self._resolve_session_key(self.tile_session_var.get())
        if resolved not in SESSION_PRESETS:
            resolved = "Brak sesji"
        self.tile_session_var.set(self._session_display_name(resolved))

    def _configure_alarm_tree_tags(self) -> None:
        if not hasattr(self, "alarms_tree"):
            return
        enabled_fg = blend_hex(str(self.theme_palette.get("session_active", "#21603A")), "#FFFFFF", 0.35)
        disabled_fg = blend_hex(str(self.theme_palette.get("session_inactive", "#603030")), "#FFFFFF", 0.25)
        self.alarms_tree.tag_configure("alarm_enabled", foreground=enabled_fg)
        self.alarms_tree.tag_configure("alarm_disabled", foreground=disabled_fg)

    def _tile_display_title(self, card: TileCard) -> str:
        if card.session_key in SESSION_PRESETS and card.session_key != "Brak sesji":
            return self._session_display_name(card.session_key)
        if card.title.startswith("Bazowy:") or card.title.startswith("Base:"):
            return self._t(f"Bazowy: {card.zone_id}", f"Base: {card.zone_id}")
        return self._city_display_name(card.title) if card.title in CITY_LABELS else card.title

    def _refresh_map_side_layout(self, _event: tk.Event | None = None) -> None:
        if not hasattr(self, "map_side_text"):
            return
        if hasattr(self, "map_side_title"):
            wrap = max(120, self.map_side_title.winfo_width() or 180)
            self.map_side_title.configure(wraplength=wrap, justify="left")
        self.map_side_text.update_idletasks()
        top, bottom = self.map_side_text.yview()
        needs_scroll = bottom - top < 0.999
        if hasattr(self, "map_side_scroll"):
            if needs_scroll:
                self.map_side_scroll.grid()
            else:
                self.map_side_scroll.grid_remove()

    def _apply_theme(self, force: bool = False) -> None:
        theme_name = self._effective_theme_name()
        if not force and self.current_theme_name == theme_name:
            return
        self.current_theme_name = theme_name
        palette = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self.theme_palette = palette
        phase_map = palette.get("phase_bg")
        self.phase_bg = dict(phase_map) if isinstance(phase_map, dict) else dict(PHASE_BG)

        app_bg = str(palette.get("app_bg", "#0B132B"))
        card_bg = str(palette.get("card_bg", "#17223C"))
        card_alt_bg = str(palette.get("card_alt_bg", card_bg))
        text = str(palette.get("text", "#F0F4F8"))
        muted = str(palette.get("muted", "#C4D8F2"))
        heading = str(palette.get("heading", "#F8FAFC"))
        accent = str(palette.get("accent", "#1D5FD1"))
        accent_hover = str(palette.get("accent_hover", "#2F80ED"))
        accent_soft = str(palette.get("accent_soft", "#2463D4"))
        entry_bg = str(palette.get("entry_bg", card_bg))
        entry_text = str(palette.get("entry_text", text))
        tree_bg = str(palette.get("tree_bg", card_alt_bg))
        tree_head_bg = str(palette.get("tree_head_bg", card_bg))
        canvas_top = str(palette.get("canvas_top", card_bg))
        canvas_bottom = str(palette.get("canvas_bottom", app_bg))

        self.configure(bg=app_bg)

        self.style.configure(".", background=app_bg, foreground=text, fieldbackground=entry_bg)
        self.style.configure("Root.TFrame", background=app_bg)
        self.style.configure("Card.TFrame", background=card_bg)
        self.style.configure("Card.TFrame", borderwidth=1, relief="solid")
        self.style.configure("Header.TLabel", background=app_bg, foreground=heading, font=("Bahnschrift", 34, "bold"))
        self.style.configure("SubHeader.TLabel", background=app_bg, foreground=muted, font=("Bahnschrift", 14))
        self.style.configure("CardTitle.TLabel", background=card_bg, foreground=heading, font=("Bahnschrift", 18, "bold"))
        self.style.configure("Clock.TLabel", background=card_bg, foreground=heading, font=("Consolas", 36, "bold"))
        self.style.configure("Info.TLabel", background=card_bg, foreground=muted, font=("Bahnschrift", 13))
        self.style.configure("SmallInfo.TLabel", background=card_bg, foreground=muted, font=("Bahnschrift", 12))
        self.style.configure("EduTitle.TLabel", background=card_bg, foreground=heading, font=("Bahnschrift", 22, "bold"))
        self.style.configure("EduMain.TLabel", background=card_bg, foreground=text, font=("Bahnschrift", 14))
        self.style.configure("EduMore.TLabel", background=card_bg, foreground=muted, font=("Bahnschrift", 13))
        self.style.configure("Action.TButton", font=("Bahnschrift", 12, "bold"), padding=(12, 8))
        self.style.map(
            "Action.TButton",
            background=[("active", accent_hover), ("!active", accent)],
            foreground=[("disabled", blend_hex(text, app_bg, 0.55)), ("!disabled", heading)],
        )

        self.style.configure("TNotebook", background=app_bg, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Bahnschrift", 12, "bold"), padding=(18, 12))
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", card_bg), ("!selected", card_alt_bg)],
            foreground=[("selected", heading), ("!selected", muted)],
        )
        self.style.configure("Treeview", background=tree_bg, fieldbackground=tree_bg, foreground=text, rowheight=34, borderwidth=0, font=("Bahnschrift", 11))
        self.style.configure("Treeview.Heading", background=tree_head_bg, foreground=heading, font=("Bahnschrift", 11, "bold"), relief="flat")
        self.style.map("Treeview", background=[("selected", accent_soft)], foreground=[("selected", heading)])
        self._configure_alarm_tree_tags()
        self.style.configure("Search.TEntry", padding=(8, 6), fieldbackground=entry_bg, foreground=entry_text)
        self.style.configure("TScrollbar", gripcount=0, background=blend_hex(accent, app_bg, 0.35), troughcolor=canvas_bottom)
        glass_a = blend_hex(card_bg, "#FFFFFF", 0.10)
        glass_b = blend_hex(card_bg, app_bg, 0.35)
        self.style.configure(
            "Glass.TCombobox",
            foreground=heading,
            fieldbackground=glass_a,
            background=glass_b,
            bordercolor=blend_hex(heading, app_bg, 0.70),
            darkcolor=glass_b,
            lightcolor=glass_b,
            arrowsize=16,
            padding=6,
        )
        self.style.map(
            "Glass.TCombobox",
            fieldbackground=[("readonly", glass_a)],
            foreground=[("readonly", heading)],
            selectbackground=[("readonly", accent)],
            selectforeground=[("readonly", heading)],
            arrowcolor=[("readonly", heading)],
            background=[("readonly", glass_b)],
        )

        if hasattr(self, "education_text"):
            self.education_text.configure(
                bg=entry_bg,
                fg=text,
                insertbackground=heading,
                selectbackground=accent_soft,
                selectforeground=heading,
            )
        if hasattr(self, "map_side_text"):
            self.map_side_text.configure(
                bg=entry_bg,
                fg=text,
                insertbackground=heading,
                selectbackground=accent_soft,
                selectforeground=heading,
            )

        if hasattr(self, "education_map_canvas"):
            self._draw_education_map()

        if hasattr(self, "tiles_canvas"):
            self.tiles_canvas.configure(bg=canvas_bottom)
            self._paint_gradient_background(self.tiles_canvas, canvas_top, canvas_bottom, tag="bg_gradient")
        if self.focus_tiles_canvas is not None:
            self.focus_tiles_canvas.configure(bg=canvas_bottom)
            self._paint_gradient_background(self.focus_tiles_canvas, canvas_top, canvas_bottom, tag="focus_bg")

        self._configure_phase_tags()
        self._layout_tiles()
        if self.fullscreen_enabled and self.focus_tiles_canvas is not None:
            self._layout_focus_tiles()

    def _build_ui(self) -> None:
        self.root_container = ttk.Frame(self, style="Root.TFrame", padding=14)
        self.root_container.pack(fill="both", expand=True)
        self.root_container.columnconfigure(0, weight=1)
        self.root_container.rowconfigure(1, weight=1)

        self.header_frame = ttk.Frame(self.root_container, style="Card.TFrame", padding=14)
        self.header_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        self.header_frame.columnconfigure(0, weight=3)
        self.header_frame.columnconfigure(1, weight=2)

        left = ttk.Frame(self.header_frame, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsew")
        self.header_title_label = ttk.Label(left, text="", style="Header.TLabel")
        self.header_title_label.pack(anchor="w")
        self._bind_i18n(self.header_title_label, "text", "Specjalista Czasu Świata", "World Time Specialist")
        self.header_subtitle_label = ttk.Label(
            left,
            text=(
                "AUTO: strefa systemu | MANUAL: wymuszenie strefy bazowej. "
                "Wszystkie widoki liczą względem czasu bazowego."
            ),
            style="SubHeader.TLabel",
        )
        self.header_subtitle_label.pack(anchor="w", pady=(6, 8))
        self._bind_i18n(
            self.header_subtitle_label,
            "text",
            "AUTO: strefa systemu | MANUAL: wymuszenie strefy bazowej. Wszystkie widoki liczą względem czasu bazowego.",
            "AUTO: system local zone | MANUAL: forced base zone. All views are calculated relative to base time.",
        )

        base_control = ttk.Frame(left, style="Card.TFrame")
        base_control.pack(fill="x")

        self.auto_radio = ttk.Radiobutton(base_control, text="AUTO (lokalna systemowa)", variable=self.base_mode_var, value="auto", command=self._on_base_mode_change)
        self.auto_radio.grid(row=0, column=0, sticky="w")
        self.manual_radio = ttk.Radiobutton(base_control, text="MANUAL", variable=self.base_mode_var, value="manual", command=self._on_base_mode_change)
        self.manual_radio.grid(row=0, column=1, sticky="w", padx=(10, 0))
        self._bind_i18n(self.auto_radio, "text", "AUTO (lokalna systemowa)", "AUTO (system local)")
        self._bind_i18n(self.manual_radio, "text", "MANUAL", "MANUAL")

        self.manual_base_entry = ttk.Combobox(
            base_control,
            textvariable=self.manual_base_zone_var,
            values=self.iana_zone_values,
            width=36,
            style="Glass.TCombobox",
            state="normal",
        )
        self.manual_base_entry.grid(row=0, column=2, sticky="ew", padx=(10, 8))
        self.manual_base_entry.bind("<Return>", self._on_manual_base_enter)
        self._register_autocomplete(self.manual_base_entry, self.iana_zone_values)

        self.manual_base_button = ttk.Button(base_control, text="Zastosuj", style="Action.TButton", command=self._apply_manual_base)
        self.manual_base_button.grid(row=0, column=3, sticky="e")
        self._bind_i18n(self.manual_base_button, "text", "✔ Zastosuj", "✔ Apply")

        self.language_label = ttk.Label(base_control, text="", style="SmallInfo.TLabel")
        self.language_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self._bind_i18n(self.language_label, "text", "Język:", "Language:")
        self.language_combo = ttk.Combobox(
            base_control,
            textvariable=self.language_var,
            values=list(LANGUAGES.keys()),
            state="readonly",
            width=10,
            style="Glass.TCombobox",
        )
        self.language_combo.grid(row=1, column=1, sticky="w", padx=(10, 8), pady=(8, 0))
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        self.theme_frame = ttk.Frame(base_control, style="Card.TFrame")
        self.theme_frame.grid(row=1, column=2, sticky="w", pady=(8, 0), padx=(0, 12))
        self.theme_label = ttk.Label(self.theme_frame, text="", style="SmallInfo.TLabel")
        self.theme_label.pack(side="left")
        self._bind_i18n(self.theme_label, "text", "Motyw:", "Theme:")
        self.theme_combo = ttk.Combobox(self.theme_frame, textvariable=self.theme_display_var, values=[], state="readonly", width=24, style="Glass.TCombobox")
        self.theme_combo.pack(side="left", padx=(8, 0))
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)
        self._refresh_theme_combo_values()

        self.auto_night_frame = ttk.Frame(base_control, style="Card.TFrame")
        self.auto_night_frame.grid(row=1, column=3, columnspan=4, sticky="w", pady=(8, 0))
        self.auto_night_check = ttk.Checkbutton(self.auto_night_frame, text="", variable=self.auto_night_var, command=self._on_theme_change)
        self.auto_night_check.pack(side="left")
        self._bind_i18n(self.auto_night_check, "text", "Auto nocny", "Auto night")
        self.auto_night_start_label = ttk.Label(self.auto_night_frame, text="", style="SmallInfo.TLabel")
        self.auto_night_start_label.pack(side="left", padx=(10, 4))
        self._bind_i18n(self.auto_night_start_label, "text", "Start:", "Start:")
        self.auto_night_start_combo = ttk.Combobox(
            self.auto_night_frame,
            textvariable=self.auto_night_start_var,
            values=TIME_PICKER_VALUES,
            width=6,
            state="normal",
            style="Glass.TCombobox",
        )
        self.auto_night_start_combo.pack(side="left")
        self.auto_night_start_combo.bind("<<ComboboxSelected>>", self._on_theme_change)
        self.auto_night_start_combo.bind("<FocusOut>", self._on_theme_change, add="+")
        self._register_autocomplete(self.auto_night_start_combo, TIME_PICKER_VALUES)
        self.auto_night_stop_label = ttk.Label(self.auto_night_frame, text="", style="SmallInfo.TLabel")
        self.auto_night_stop_label.pack(side="left", padx=(10, 4))
        self._bind_i18n(self.auto_night_stop_label, "text", "Stop:", "Stop:")
        self.auto_night_stop_combo = ttk.Combobox(
            self.auto_night_frame,
            textvariable=self.auto_night_stop_var,
            values=TIME_PICKER_VALUES,
            width=6,
            state="normal",
            style="Glass.TCombobox",
        )
        self.auto_night_stop_combo.pack(side="left")
        self.auto_night_stop_combo.bind("<<ComboboxSelected>>", self._on_theme_change)
        self.auto_night_stop_combo.bind("<FocusOut>", self._on_theme_change, add="+")
        self._register_autocomplete(self.auto_night_stop_combo, TIME_PICKER_VALUES)

        self.session_sound_check = ttk.Checkbutton(base_control, text="", variable=self.session_sound_enabled_var)
        self.session_sound_check.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._bind_i18n(self.session_sound_check, "text", "Dźwięki sesji (start/koniec)", "Session sounds (start/end)")

        self.minimize_on_start_check = ttk.Checkbutton(base_control, text="", variable=self.minimize_on_start_var)
        self.minimize_on_start_check.grid(row=2, column=1, sticky="w", pady=(8, 0))
        self._bind_i18n(self.minimize_on_start_check, "text", "Minimalizuj do tray przy starcie", "Minimize to tray on startup")

        self.autostart_add_btn = ttk.Button(base_control, text="", style="Action.TButton", command=self._add_to_autostart)
        self.autostart_add_btn.grid(row=2, column=2, sticky="w", padx=(16, 8), pady=(8, 0))
        self._bind_i18n(self.autostart_add_btn, "text", "🚀 Dodaj do autostartu", "🚀 Add to autostart")
        self.autostart_remove_btn = ttk.Button(base_control, text="", style="Action.TButton", command=self._remove_from_autostart)
        self.autostart_remove_btn.grid(row=2, column=3, sticky="w", padx=(0, 8), pady=(8, 0))
        self._bind_i18n(self.autostart_remove_btn, "text", "🛑 Usuń z autostartu", "🛑 Remove from autostart")
        self.tray_minimize_btn = ttk.Button(base_control, text="", style="Action.TButton", command=self._minimize_to_tray)
        self.tray_minimize_btn.grid(row=2, column=4, sticky="w", padx=(0, 4), pady=(8, 0))
        self._bind_i18n(self.tray_minimize_btn, "text", "📥 Minimalizuj do tray", "📥 Minimize to tray")
        self.tray_install_btn = ttk.Button(base_control, text="", style="Action.TButton", command=self._install_tray_support)
        self.tray_install_btn.grid(row=2, column=5, sticky="w", padx=(0, 4), pady=(8, 0))
        self._bind_i18n(self.tray_install_btn, "text", "🧩 Zainstaluj tray", "🧩 Install tray")

        base_control.columnconfigure(0, weight=0)
        base_control.columnconfigure(1, weight=0)
        base_control.columnconfigure(2, weight=1)
        base_control.columnconfigure(3, weight=0)
        base_control.columnconfigure(4, weight=0)
        base_control.columnconfigure(5, weight=0)
        base_control.columnconfigure(6, weight=1)
        ttk.Label(left, textvariable=self.base_notice_var, style="SmallInfo.TLabel", wraplength=860).pack(anchor="w", pady=(8, 0))

        right = ttk.Frame(self.header_frame, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        self.base_time_label = ttk.Label(right, text="", style="CardTitle.TLabel")
        self.base_time_label.pack(anchor="e")
        self._bind_i18n(self.base_time_label, "text", "Czas bazowy", "Base time")
        ttk.Label(right, textvariable=self.base_time_var, style="Clock.TLabel").pack(anchor="e", pady=(2, 0))
        ttk.Label(right, textvariable=self.base_info_var, style="Info.TLabel", justify="right", wraplength=560).pack(anchor="e", pady=(4, 0))
        ttk.Label(right, textvariable=self.system_info_var, style="SmallInfo.TLabel", justify="right", wraplength=560).pack(anchor="e", pady=(6, 0))

        self.notebook = ttk.Notebook(self.root_container)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.world_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.search_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.universal_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.converter_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.compare_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.education_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.map_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.tiles_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.alarms_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)
        self.links_tab = ttk.Frame(self.notebook, style="Root.TFrame", padding=12)

        self.notebook.add(self.world_tab, text=I18N["tab_world"][self.language_var.get()])
        self.notebook.add(self.search_tab, text=I18N["tab_search"][self.language_var.get()])
        self.notebook.add(self.universal_tab, text=I18N["tab_universal"][self.language_var.get()])
        self.notebook.add(self.converter_tab, text=I18N["tab_converter"][self.language_var.get()])
        self.notebook.add(self.compare_tab, text=I18N["tab_compare"][self.language_var.get()])
        self.notebook.add(self.education_tab, text=I18N["tab_education"][self.language_var.get()])
        self.notebook.add(self.map_tab, text=I18N["tab_map"][self.language_var.get()])
        self.notebook.add(self.tiles_tab, text=I18N["tab_tiles"][self.language_var.get()])
        self.notebook.add(self.alarms_tab, text=I18N["tab_alarms"][self.language_var.get()])
        self.notebook.add(self.links_tab, text=I18N["tab_links"][self.language_var.get()])

        self._build_world_tab()
        self._build_search_tab()
        self._build_universal_tab()
        self._build_converter_tab()
        self._build_compare_tab()
        self._build_education_tab()
        self._build_map_tab()
        self._build_tiles_tab()
        self._build_alarms_tab()
        self._build_links_tab()
        self._refresh_autostart_buttons()
        self._refresh_tray_support_buttons()
        self._configure_phase_tags()
        self._apply_language(force=True)

    def _update_all_headings(self) -> None:
        if hasattr(self, "world_tree"):
            if self.language_var.get() == "en":
                headings = {
                    "place": "Place",
                    "zone": "IANA Zone",
                    "time": "Local Time",
                    "abbr": "Abbr.",
                    "utc": "UTC Offset",
                    "diff": "To Base",
                    "phase": "Day Phase",
                }
            else:
                headings = {
                    "place": "Miejsce",
                    "zone": "Strefa IANA",
                    "time": "Czas Lokalny",
                    "abbr": "Skrót",
                    "utc": "Offset UTC",
                    "diff": "Do Bazowego",
                    "phase": "Pora Dnia",
                }
            for col, text in headings.items():
                self.world_tree.heading(col, text=text)
        if hasattr(self, "search_tree"):
            if self.language_var.get() == "en":
                headings = {
                    "zone": "Zone",
                    "time": "Current Time",
                    "abbr": "Abbr.",
                    "utc": "UTC",
                    "diff": "To Base",
                    "phase": "Day Phase",
                    "source": "Source",
                }
            else:
                headings = {
                    "zone": "Strefa",
                    "time": "Aktualny Czas",
                    "abbr": "Skrót",
                    "utc": "UTC",
                    "diff": "Do Bazowego",
                    "phase": "Pora Dnia",
                    "source": "Źródło",
                }
            for col, text in headings.items():
                self.search_tree.heading(col, text=text)
        if hasattr(self, "universal_tree"):
            if self.language_var.get() == "en":
                headings = {
                    "name": "Standard",
                    "example": "Reference Location",
                    "time": "Current Time",
                    "abbr": "Current Abbr.",
                    "utc": "UTC Now",
                    "diff": "To Base",
                    "season": "Winter/Summer Profile",
                }
            else:
                headings = {
                    "name": "Standard",
                    "example": "Przykład Lokalizacji",
                    "time": "Aktualny Czas",
                    "abbr": "Skrót Teraz",
                    "utc": "UTC Teraz",
                    "diff": "Do Bazowego",
                    "season": "Zakres Zima/Lato",
                }
            for col, text in headings.items():
                self.universal_tree.heading(col, text=text)
        if hasattr(self, "alarms_tree"):
            if self.language_var.get() == "en":
                headings = {
                    "label": "Label",
                    "zone": "Zone",
                    "time": "Time",
                    "date": "Date",
                    "repeat": "Kind",
                    "duration": "Duration",
                    "sound": "Sound",
                    "enabled": "Status",
                }
            else:
                headings = {
                    "label": "Nazwa",
                    "zone": "Strefa",
                    "time": "Godzina",
                    "date": "Data",
                    "repeat": "Rodzaj",
                    "duration": "Długość",
                    "sound": "Dźwięk",
                    "enabled": "Status",
                }
            for col, text in headings.items():
                self.alarms_tree.heading(col, text=text)
            self._refresh_alarm_tree()

    def _build_world_tab(self) -> None:
        container = ttk.Frame(self.world_tab, style="Card.TFrame", padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        self.world_title_label = ttk.Label(container, text="", style="CardTitle.TLabel")
        self.world_title_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.world_title_label, "text", "Podstawowe miasta świata", "Core world cities")

        columns = ("place", "zone", "time", "abbr", "utc", "diff", "phase")
        self.world_tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="none")
        self.world_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        widths = {"place": 190, "zone": 230, "time": 180, "abbr": 100, "utc": 105, "diff": 120, "phase": 120}

        for col in columns:
            self.world_tree.heading(col, text="")
            self.world_tree.column(col, width=widths[col], anchor="center")
        self.world_tree.column("place", anchor="w")
        self.world_tree.column("zone", anchor="w")
        self._update_all_headings()

        scroll = ttk.Scrollbar(container, orient="vertical", command=self.world_tree.yview)
        scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.world_tree.configure(yscrollcommand=scroll.set)

        self.world_rows: list[tuple[str, str]] = []
        for place_name, zone_id in WORLD_HIGHLIGHTS:
            if self.engine.zone(zone_id) is None and not self.engine.has_fallback(zone_id):
                continue
            self.world_rows.append((place_name, zone_id))
            self.world_tree.insert("", "end", iid=zone_id, values=("", "", "", "", "", "", ""))

        self.world_legend_label = ttk.Label(container, text="", style="SmallInfo.TLabel")
        self.world_legend_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._bind_i18n(
            self.world_legend_label,
            "text",
            "Legenda: Poranek (05:00-09:59), Dzień (10:00-13:59), Popołudnie (14:00-17:59), Wieczór (18:00-21:59), Noc (22:00-04:59)",
            "Legend: Morning (05:00-09:59), Day (10:00-13:59), Afternoon (14:00-17:59), Evening (18:00-21:59), Night (22:00-04:59)",
        )

    def _build_search_tab(self) -> None:
        root = ttk.Frame(self.search_tab, style="Root.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=4)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(1, weight=1)

        search_bar = ttk.Frame(root, style="Card.TFrame", padding=10)
        search_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        search_bar.columnconfigure(1, weight=1)

        self.search_title_label = ttk.Label(search_bar, text="", style="CardTitle.TLabel")
        self.search_title_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(
            self.search_title_label,
            "text",
            "Wpisz kraj, kod ISO (np. PL) albo miasto (np. Tokio):",
            "Type a country, ISO code (e.g., PL) or city (e.g., Tokyo):",
        )
        self.search_entry = ttk.Entry(search_bar, textvariable=self.search_query_var, style="Search.TEntry")
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=10)
        self.search_entry.bind("<Return>", self._on_search_enter)
        self.search_button = ttk.Button(search_bar, text="", style="Action.TButton", command=self._run_search)
        self.search_button.grid(row=0, column=2)
        self._bind_i18n(self.search_button, "text", "🔎 Szukaj", "🔎 Search")

        ttk.Label(search_bar, textvariable=self.status_var, style="SmallInfo.TLabel", wraplength=980).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        left_card = ttk.Frame(root, style="Card.TFrame", padding=10)
        left_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left_card.columnconfigure(0, weight=1)
        left_card.rowconfigure(1, weight=1)

        self.search_results_label = ttk.Label(left_card, text="", style="CardTitle.TLabel")
        self.search_results_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.search_results_label, "text", "Wyniki", "Results")

        columns = ("zone", "time", "abbr", "utc", "diff", "phase", "source")
        self.search_tree = ttk.Treeview(left_card, columns=columns, show="headings", selectmode="browse")
        self.search_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        widths = {"zone": 230, "time": 145, "abbr": 90, "utc": 90, "diff": 110, "phase": 100, "source": 170}

        for col in columns:
            self.search_tree.heading(col, text="")
            self.search_tree.column(col, width=widths[col], anchor="center")
        self.search_tree.column("zone", anchor="w")
        self.search_tree.column("source", anchor="w")
        self._update_all_headings()

        search_scroll = ttk.Scrollbar(left_card, orient="vertical", command=self.search_tree.yview)
        search_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.search_tree.configure(yscrollcommand=search_scroll.set)

        source_card = ttk.Frame(left_card, style="Card.TFrame", padding=(0, 8, 0, 0))
        source_card.grid(row=2, column=0, columnspan=2, sticky="ew")
        source_card.columnconfigure(0, weight=1)
        self.search_source_title_label = ttk.Label(source_card, text="", style="CardTitle.TLabel")
        self.search_source_title_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.search_source_title_label, "text", "Pełne źródło dopasowania", "Full match source")
        ttk.Label(source_card, textvariable=self.search_source_full_var, style="SmallInfo.TLabel", justify="left", wraplength=860).grid(row=1, column=0, sticky="ew", pady=(4, 0))

        self.search_tree.bind("<<TreeviewSelect>>", self._on_search_select)

        detail_card = ttk.Frame(root, style="Card.TFrame", padding=12)
        detail_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        detail_card.columnconfigure(0, weight=1)

        ttk.Label(detail_card, textvariable=self.detail_header_var, style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(detail_card, textvariable=self.detail_body_var, style="Info.TLabel", justify="left", wraplength=440).grid(row=1, column=0, sticky="nw", pady=(8, 0))

        self.search_set_base_btn = ttk.Button(detail_card, text="", style="Action.TButton", command=self._set_selected_as_base_zone)
        self.search_set_base_btn.grid(row=2, column=0, sticky="w", pady=(12, 0))
        self._bind_i18n(self.search_set_base_btn, "text", "📍 Ustaw wynik jako strefę bazową", "📍 Set result as base zone")

        self.search_hints_label = ttk.Label(detail_card, text="", style="SmallInfo.TLabel", justify="left")
        self.search_hints_label.grid(row=3, column=0, sticky="sw", pady=(14, 0))
        self._bind_i18n(
            self.search_hints_label,
            "text",
            "Wskazówki:\n- miasto: Warszawa / Nowy Jork / Tokio\n- kraj: Polska / Stany Zjednoczone / Japonia\n- kod ISO: PL, US, JP\n- wpisz skrót lub offset: EST, CET, JST, UTC+1",
            "Tips:\n- city: Warsaw / New York / Tokyo\n- country: Poland / United States / Japan\n- ISO code: PL, US, JP\n- enter abbreviation or offset: EST, CET, JST, UTC+1",
        )

    def _build_universal_tab(self) -> None:
        root = ttk.Frame(self.universal_tab, style="Card.TFrame", padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        self.universal_title_label = ttk.Label(root, text="", style="CardTitle.TLabel")
        self.universal_title_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.universal_title_label, "text", "Uniwersalne standardy i skróty stref", "Universal zone standards and abbreviations")

        columns = ("name", "example", "time", "abbr", "utc", "diff", "season")
        self.universal_tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="none")
        self.universal_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        widths = {"name": 120, "example": 210, "time": 160, "abbr": 115, "utc": 110, "diff": 120, "season": 390}

        for col in columns:
            self.universal_tree.heading(col, text="")
            self.universal_tree.column(col, width=widths[col], anchor="center")
        self.universal_tree.column("example", anchor="w")
        self.universal_tree.column("season", anchor="w")
        self._update_all_headings()

        scroll = ttk.Scrollbar(root, orient="vertical", command=self.universal_tree.yview)
        scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.universal_tree.configure(yscrollcommand=scroll.set)

        self.universal_rows: list[tuple[str, str, str]] = []
        for name, zone_id, desc in UNIVERSAL_REFERENCES:
            if self.engine.zone(zone_id) is None and not self.engine.has_fallback(zone_id):
                continue
            row_id = f"u::{name}::{zone_id}"
            self.universal_rows.append((name, zone_id, desc))
            self.universal_tree.insert("", "end", iid=row_id, values=(name, zone_id, "", "", "", "", ""))

        self.universal_note_label = ttk.Label(root, text="", style="SmallInfo.TLabel", wraplength=1280, justify="left")
        self.universal_note_label.grid(row=2, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(
            self.universal_note_label,
            "text",
            "Uwaga: te same skróty mogą oznaczać różne regiony (np. CST). W tabeli zawsze pokazujemy też strefę IANA.",
            "Note: the same abbreviations may refer to different regions (e.g., CST). We always show the IANA zone as well.",
        )

    def _build_converter_tab(self) -> None:
        root = ttk.Frame(self.converter_tab, style="Card.TFrame", padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        self.converter_title_label = ttk.Label(root, text="", style="CardTitle.TLabel")
        self.converter_title_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.converter_title_label, "text", "Uniwersalny konwerter czasu", "Universal time converter")

        controls = ttk.Frame(root, style="Card.TFrame", padding=8)
        controls.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        source_box = ttk.Frame(controls, style="Card.TFrame", padding=10)
        source_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        source_box.columnconfigure(1, weight=1)
        self.converter_source_title = ttk.Label(source_box, text="", style="CardTitle.TLabel")
        self.converter_source_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._bind_i18n(self.converter_source_title, "text", "Źródło", "Source")

        self.converter_source_time_label = ttk.Label(source_box, text="", style="SmallInfo.TLabel")
        self.converter_source_time_label.grid(row=1, column=0, sticky="w")
        self._bind_i18n(self.converter_source_time_label, "text", "Czas źródłowy:", "Source time:")
        self.converter_input_entry = ttk.Entry(source_box, textvariable=self.converter_input_var, style="Search.TEntry")
        self.converter_input_entry.grid(row=1, column=1, sticky="ew", padx=(6, 0))
        self.converter_input_entry.bind("<KeyRelease>", self._on_converter_field_change)

        self.converter_source_zone_label = ttk.Label(source_box, text="", style="SmallInfo.TLabel")
        self.converter_source_zone_label.grid(row=2, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(self.converter_source_zone_label, "text", "Strefa źródła:", "Source zone:")
        self.converter_source_entry = ttk.Combobox(
            source_box,
            textvariable=self.converter_source_zone_var,
            values=self.city_zone_values,
            style="Glass.TCombobox",
            state="normal",
        )
        self.converter_source_entry.grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(10, 0))
        self.converter_source_entry.bind("<KeyRelease>", self._on_converter_field_change)
        self._register_autocomplete(self.converter_source_entry, self.city_zone_values)

        target_box = ttk.Frame(controls, style="Card.TFrame", padding=10)
        target_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        target_box.columnconfigure(1, weight=1)
        self.converter_target_title = ttk.Label(target_box, text="", style="CardTitle.TLabel")
        self.converter_target_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._bind_i18n(self.converter_target_title, "text", "Cel", "Target")

        self.converter_base_radio = ttk.Radiobutton(target_box, text="", variable=self.converter_target_mode_var, value="base", command=self._on_converter_mode_change)
        self.converter_base_radio.grid(row=1, column=0, columnspan=2, sticky="w")
        self._bind_i18n(self.converter_base_radio, "text", "Konwertuj do czasu bazowego", "Convert to base time")
        self.converter_manual_radio = ttk.Radiobutton(target_box, text="", variable=self.converter_target_mode_var, value="manual", command=self._on_converter_mode_change)
        self.converter_manual_radio.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self._bind_i18n(self.converter_manual_radio, "text", "Konwertuj do strefy manualnej", "Convert to manual zone")

        self.converter_target_zone_label = ttk.Label(target_box, text="", style="SmallInfo.TLabel")
        self.converter_target_zone_label.grid(row=3, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(self.converter_target_zone_label, "text", "Cel (manualnie):", "Target (manual):")
        self.converter_target_entry = ttk.Combobox(
            target_box,
            textvariable=self.converter_target_zone_var,
            values=self.city_zone_values,
            style="Glass.TCombobox",
            state="normal",
        )
        self.converter_target_entry.grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=(10, 0))
        self.converter_target_entry.bind("<KeyRelease>", self._on_converter_field_change)
        self._register_autocomplete(self.converter_target_entry, self.city_zone_values)

        self.converter_live_check = ttk.Checkbutton(target_box, text="", variable=self.converter_live_var, command=lambda: self._run_converter(silent=True))
        self.converter_live_check.grid(row=4, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(self.converter_live_check, "text", "Auto odświeżanie", "Auto refresh")

        actions = ttk.Frame(controls, style="Card.TFrame")
        actions.grid(row=1, column=0, columnspan=2, sticky="e", pady=(10, 0))
        self.converter_calc_button = ttk.Button(actions, text="", style="Action.TButton", command=lambda: self._run_converter(silent=False))
        self.converter_calc_button.grid(row=0, column=0, sticky="e")
        self._bind_i18n(self.converter_calc_button, "text", "🧮 Przelicz", "🧮 Convert")

        self.converter_hint_label = ttk.Label(
            root,
            text="",
            style="SmallInfo.TLabel",
            wraplength=1280,
            justify="left",
        )
        self.converter_hint_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._bind_i18n(
            self.converter_hint_label,
            "text",
            "Formaty czasu: 10:15, 22:45:30, 2026-03-24 10:15, 24.03.2026 10:15, 10:15 PM. Strefa źródła/docelowa: IANA (Europe/Warsaw), skrót (EST) lub offset (UTC+1).",
            "Time formats: 10:15, 22:45:30, 2026-03-24 10:15, 24.03.2026 10:15, 10:15 PM. Source/target zone: IANA (Europe/Warsaw), abbreviation (EST), or offset (UTC+1).",
        )

        result_card = ttk.Frame(root, style="Card.TFrame", padding=12)
        result_card.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        result_card.columnconfigure(0, weight=1)

        self.converter_result_title = ttk.Label(result_card, text="", style="CardTitle.TLabel")
        self.converter_result_title.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.converter_result_title, "text", "Wynik", "Result")
        ttk.Label(result_card, textvariable=self.converter_result_var, style="Clock.TLabel", font=("Consolas", 26, "bold")).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(result_card, textvariable=self.converter_detail_var, style="Info.TLabel", justify="left", wraplength=1280).grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _build_compare_tab(self) -> None:
        root = ttk.Frame(self.compare_tab, style="Card.TFrame", padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)

        self.compare_title_label = ttk.Label(root, text="", style="CardTitle.TLabel")
        self.compare_title_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.compare_title_label, "text", "Kalkulator porównania miast/stref", "City/time-zone comparison calculator")

        controls = ttk.Frame(root, style="Card.TFrame", padding=8)
        controls.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(3, weight=1)

        self.compare_loc_a_label = ttk.Label(controls, text="", style="SmallInfo.TLabel")
        self.compare_loc_a_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.compare_loc_a_label, "text", "Lokalizacja A:", "Location A:")
        self.compare_a_entry = ttk.Entry(controls, textvariable=self.compare_a_var, style="Search.TEntry")
        self.compare_a_entry.grid(row=0, column=1, sticky="ew", padx=(6, 12))
        self.compare_a_entry.bind("<Return>", self._on_compare_enter)

        self.compare_loc_b_label = ttk.Label(controls, text="", style="SmallInfo.TLabel")
        self.compare_loc_b_label.grid(row=0, column=2, sticky="w")
        self._bind_i18n(self.compare_loc_b_label, "text", "Lokalizacja B:", "Location B:")
        self.compare_b_entry = ttk.Entry(controls, textvariable=self.compare_b_var, style="Search.TEntry")
        self.compare_b_entry.grid(row=0, column=3, sticky="ew", padx=(6, 12))
        self.compare_b_entry.bind("<Return>", self._on_compare_enter)

        self.compare_run_btn = ttk.Button(controls, text="", style="Action.TButton", command=self._run_comparison)
        self.compare_run_btn.grid(row=0, column=4, sticky="e")
        self._bind_i18n(self.compare_run_btn, "text", "⚖ Porównaj", "⚖ Compare")

        self.compare_ref_time_label = ttk.Label(controls, text="", style="SmallInfo.TLabel")
        self.compare_ref_time_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(self.compare_ref_time_label, "text", "Czas referencyjny (opcjonalnie):", "Reference time (optional):")
        self.compare_reference_time_entry = ttk.Entry(controls, textvariable=self.compare_reference_time_var, style="Search.TEntry")
        self.compare_reference_time_entry.grid(row=1, column=1, sticky="ew", padx=(6, 12), pady=(10, 0))
        self.compare_reference_time_entry.bind("<Return>", self._on_compare_enter)

        self.compare_ref_zone_label = ttk.Label(controls, text="", style="SmallInfo.TLabel")
        self.compare_ref_zone_label.grid(row=1, column=2, sticky="w", pady=(10, 0))
        self._bind_i18n(self.compare_ref_zone_label, "text", "Strefa tego czasu (opcjonalnie):", "Reference zone (optional):")
        self.compare_reference_zone_entry = ttk.Combobox(
            controls,
            textvariable=self.compare_reference_zone_var,
            values=self.iana_zone_values,
            style="Glass.TCombobox",
            state="normal",
        )
        self.compare_reference_zone_entry.grid(row=1, column=3, sticky="ew", padx=(6, 12), pady=(10, 0))
        self.compare_reference_zone_entry.bind("<Return>", self._on_compare_enter)
        self._register_autocomplete(self.compare_reference_zone_entry, self.iana_zone_values)
        self.compare_example_label = ttk.Label(
            controls,
            text="",
            style="SmallInfo.TLabel",
        )
        self.compare_example_label.grid(row=1, column=4, sticky="e", pady=(10, 0))
        self._bind_i18n(
            self.compare_example_label,
            "text",
            "Przykład: czas 13:14 + strefa UTC+1 albo Europe/Warsaw",
            "Example: time 13:14 + zone UTC+1 or Europe/Warsaw",
        )

        ttk.Label(root, textvariable=self.compare_status_var, style="SmallInfo.TLabel", wraplength=1280).grid(row=2, column=0, sticky="w", pady=(8, 0))

        result = ttk.Frame(root, style="Card.TFrame", padding=12)
        result.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        result.columnconfigure(0, weight=1)

        self.compare_summary_title = ttk.Label(result, text="", style="CardTitle.TLabel")
        self.compare_summary_title.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.compare_summary_title, "text", "Podsumowanie", "Summary")
        ttk.Label(result, textvariable=self.compare_result_var, style="Info.TLabel", justify="left", wraplength=1280).grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _build_education_tab(self) -> None:
        root = ttk.Frame(self.education_tab, style="Root.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=4)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(2, weight=1)

        header = ttk.Frame(root, style="Card.TFrame", padding=12)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        self.education_header_label = ttk.Label(header, text="", style="CardTitle.TLabel")
        self.education_header_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(
            self.education_header_label,
            "text",
            "📘 Strefy czasowe od zera: mapa myśli + praktyka",
            "📘 Time zones from zero: mind map + practice",
        )
        self.education_intro_label = ttk.Label(
            header,
            text="",
            style="SmallInfo.TLabel",
            justify="left",
            wraplength=1280,
        )
        self.education_intro_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._bind_i18n(
            self.education_intro_label,
            "text",
            "Ta zakładka pokazuje logikę UTC, offsetów, skrótów i IANA oraz praktyczne zasady bez błędów.",
            "This tab explains UTC, offsets, abbreviations and IANA logic with practical, mistake-proof rules.",
        )

        map_card = ttk.Frame(root, style="Card.TFrame", padding=0)
        map_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        map_card.columnconfigure(0, weight=1)
        self.education_hierarchy_label = ttk.Label(map_card, text="", style="CardTitle.TLabel")
        self.education_hierarchy_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.education_hierarchy_label, "text", "🧠 Hierarchia pojęć (widok graficzny)", "🧠 Concepts hierarchy (visual)")
        self.education_map_canvas = tk.Canvas(map_card, bg="#0F1D3A", height=220, highlightthickness=0)
        self.education_map_canvas.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.education_map_canvas.bind("<Configure>", self._draw_education_map)
        self._draw_education_map()

        tree_card = ttk.Frame(root, style="Card.TFrame", padding=10)
        tree_card.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        tree_card.columnconfigure(0, weight=1)
        tree_card.rowconfigure(1, weight=1)
        self.education_tree_label = ttk.Label(tree_card, text="", style="CardTitle.TLabel")
        self.education_tree_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.education_tree_label, "text", "📂 Struktura tematów", "📂 Topic structure")

        self.education_tree = ttk.Treeview(tree_card, show="tree", selectmode="browse")
        self.education_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        tree_scroll = ttk.Scrollbar(tree_card, orient="vertical", command=self.education_tree.yview)
        tree_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.education_tree.configure(yscrollcommand=tree_scroll.set)
        self.education_tree.bind("<<TreeviewSelect>>", self._on_education_select)

        for topic_id, parent_id in EDUCATION_TREE:
            parent = "" if parent_id is None else parent_id
            topic = EDUCATION_TOPICS[topic_id]
            label_map = topic.get("label", {})
            label = str(label_map.get(self.language_var.get(), label_map.get("pl", topic_id))) if isinstance(label_map, dict) else topic_id
            icon = str(topic.get("icon", "•"))
            self.education_tree.insert(parent, "end", iid=topic_id, text=f"{icon} {label}", open=True)

        detail_card = ttk.Frame(root, style="Card.TFrame", padding=14)
        detail_card.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        detail_card.columnconfigure(0, weight=1)
        detail_card.rowconfigure(2, weight=1)

        ttk.Label(detail_card, textvariable=self.education_title_var, style="EduTitle.TLabel", wraplength=520, justify="left").grid(row=0, column=0, sticky="w")
        self.education_history_button = ttk.Button(detail_card, text="", style="Action.TButton", command=self._open_education_history)
        self.education_history_button.grid(row=1, column=0, sticky="w", pady=(8, 8))
        self._bind_i18n(self.education_history_button, "text", "🕰️ Tło historyczne i ciekawostki", "🕰️ Historical background & facts")

        self.education_text = tk.Text(
            detail_card,
            wrap="word",
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=6,
            font=("Bahnschrift", 12),
        )
        self.education_text.grid(row=2, column=0, sticky="nsew")
        edu_scroll = ttk.Scrollbar(detail_card, orient="vertical", command=self.education_text.yview)
        edu_scroll.grid(row=2, column=1, sticky="ns")
        self.education_text.configure(yscrollcommand=edu_scroll.set)
        self.education_text.tag_configure("h", font=("Bahnschrift", 14, "bold"))
        self.education_text.tag_configure("b", font=("Bahnschrift", 12))
        self.education_text.tag_configure("muted", font=("Bahnschrift", 11, "italic"))
        self.education_text.configure(state="disabled")

        self.education_tree.selection_set("root")
        self.education_tree.focus("root")
        self._set_education_topic("root")

    def _draw_education_map(self, event: tk.Event | None = None) -> None:
        canvas = self.education_map_canvas
        canvas.delete("all")

        width = max(canvas.winfo_width(), 980)
        height = max(canvas.winfo_height(), 220)
        top = str(self.theme_palette.get("canvas_top", "#1B2747"))
        bottom = str(self.theme_palette.get("canvas_bottom", "#0E1A33"))
        for idx in range(24):
            y0 = int(height * idx / 24)
            y1 = int(height * (idx + 1) / 24)
            color = blend_hex(top, bottom, idx / 23)
            canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")

        link_color = blend_hex(str(self.theme_palette.get("accent_soft", "#7AAAF0")), str(self.theme_palette.get("heading", "#EAF2FF")), 0.25)
        node_fill = str(self.theme_palette.get("card_bg", "#1E2B4A"))
        node_outline = str(self.theme_palette.get("clock_border", "#8CB9FF"))
        node_text = str(self.theme_palette.get("heading", "#EAF2FF"))

        nodes: dict[str, tuple[float, float]] = {
            "UTC": (110, height * 0.5),
            "offset": (300, height * 0.5),
            "abbr": (500, height * 0.28),
            "iana": (500, height * 0.72),
            "dst": (700, height * 0.28),
            "convert": (700, height * 0.72),
            "result": (890, height * 0.5),
        }
        labels = {
            "UTC": "UTC",
            "offset": self._t("Offset UTC+/-", "UTC+/- offset"),
            "abbr": self._t("Skróty\nEST/CET/JST", "Abbrev.\nEST/CET/JST"),
            "iana": "IANA\nEurope/Warsaw",
            "dst": self._t("DST\nlato/zima", "DST\nsummer/winter"),
            "convert": self._t("Konwersje\nczasu", "Time\nconversions"),
            "result": self._t("Wynik\nlokalny", "Local\nresult"),
        }
        links = [
            ("UTC", "offset"),
            ("offset", "abbr"),
            ("offset", "iana"),
            ("abbr", "dst"),
            ("iana", "convert"),
            ("dst", "result"),
            ("convert", "result"),
        ]

        for source, target in links:
            sx, sy = nodes[source]
            tx, ty = nodes[target]
            canvas.create_line(sx + 70, sy, tx - 70, ty, fill=link_color, width=2, smooth=True)

        for node_id, (x, y) in nodes.items():
            canvas.create_rectangle(x - 74, y - 30, x + 74, y + 30, fill=node_fill, outline=node_outline, width=2)
            canvas.create_text(x, y, text=labels[node_id], fill=node_text, font=("Bahnschrift", 10, "bold"), justify="center")

    def _on_education_select(self, event: tk.Event) -> None:
        selected = self.education_tree.selection()
        if not selected:
            return
        self._set_education_topic(selected[0])

    def _set_education_topic(self, topic_id: str) -> None:
        topic = EDUCATION_TOPICS.get(topic_id, EDUCATION_TOPICS["root"])
        self.education_selected_topic = topic_id
        title_map = topic.get("title", {})
        body_map = topic.get("body", {})
        title_txt = str(title_map.get(self.language_var.get(), title_map.get("pl", ""))) if isinstance(title_map, dict) else ""
        body_txt = str(body_map.get(self.language_var.get(), body_map.get("pl", ""))) if isinstance(body_map, dict) else ""
        icon = str(topic.get("icon", "📘"))
        self.education_title_var.set(f"{icon} {title_txt}")

        if hasattr(self, "education_text"):
            self.education_text.configure(state="normal")
            self.education_text.delete("1.0", "end")
            self.education_text.insert("end", f"{title_txt}\n\n", ("h",))
            self.education_text.insert("end", body_txt + "\n\n", ("b",))
            self.education_text.insert(
                "end",
                self._t("Wskazówka: używaj pełnej strefy IANA przy ważnych wydarzeniach.", "Tip: use full IANA zone names for critical events."),
                ("muted",),
            )
            self.education_text.configure(state="disabled")

    def _open_education_history(self) -> None:
        history_window = tk.Toplevel(self)
        history_window.title(self._t("Historia oznaczeń czasu", "History of time notation"))
        history_window.configure(bg=str(self.theme_palette.get("app_bg", "#0B132B")))

        frame = ttk.Frame(history_window, style="Card.TFrame", padding=14)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(
            frame,
            text=self._t("📚 Historia stref i oznaczeń czasu", "📚 History of zones and time notation"),
            style="EduTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        text = tk.Text(frame, wrap="word", relief="flat", borderwidth=0, padx=10, pady=10, font=("Bahnschrift", 12))
        text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        text.configure(
            bg=str(self.theme_palette.get("entry_bg", "#17223C")),
            fg=str(self.theme_palette.get("text", "#F0F4F8")),
            insertbackground=str(self.theme_palette.get("heading", "#F8FAFC")),
            selectbackground=str(self.theme_palette.get("accent_soft", "#2463D4")),
            selectforeground=str(self.theme_palette.get("heading", "#F8FAFC")),
        )
        scr = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scr.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        text.configure(yscrollcommand=scr.set)
        text.insert("end", EDUCATION_HISTORY[self.language_var.get()])
        text.configure(state="disabled")

        history_window.update_idletasks()
        content = EDUCATION_HISTORY[self.language_var.get()].splitlines()
        font = tkfont.Font(font=text["font"])
        max_line = max((font.measure(line) for line in content), default=600)
        line_height = font.metrics("linespace")
        display_lines = len(content) + 2
        width = max(700, min(1100, int(max_line + 140)))
        height = max(420, min(820, int(display_lines * line_height + 180)))
        history_window.geometry(f"{width}x{height}")

    def _build_map_tab(self) -> None:
        root = ttk.Frame(self.map_tab, style="Root.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=0)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root, style="Card.TFrame", padding=12)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        self.map_title_label = ttk.Label(header, text="", style="CardTitle.TLabel")
        self.map_title_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.map_title_label, "text", "🗺️ Mapa świata i stref czasowych", "🗺️ World map and time zones")
        self.map_subtitle_label = ttk.Label(header, text="", style="SmallInfo.TLabel", wraplength=1280, justify="left")
        self.map_subtitle_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._bind_i18n(
            self.map_subtitle_label,
            "text",
            "Pasma pokazują strefy UTC od -12 do +14. Znaczniki miast aktualizują się na żywo.",
            "Bands show UTC zones from -12 to +14. City markers update live.",
        )

        map_card = ttk.Frame(root, style="Card.TFrame", padding=0)
        map_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        map_card.columnconfigure(0, weight=1)
        map_card.rowconfigure(0, weight=1)

        map_canvas_frame = ttk.Frame(map_card, style="Card.TFrame")
        map_canvas_frame.grid(row=0, column=0, sticky="nsew")
        map_canvas_frame.columnconfigure(0, weight=1)
        map_canvas_frame.rowconfigure(0, weight=1)

        self.world_map_canvas = tk.Canvas(map_canvas_frame, highlightthickness=0)
        self.world_map_canvas.grid(row=0, column=0, sticky="nsew")
        self.world_map_vscroll = ttk.Scrollbar(map_canvas_frame, orient="vertical", command=self.world_map_canvas.yview)
        self.world_map_hscroll = ttk.Scrollbar(map_canvas_frame, orient="horizontal", command=self.world_map_canvas.xview)
        self.world_map_canvas.configure(yscrollcommand=self.world_map_vscroll.set, xscrollcommand=self.world_map_hscroll.set)

        def _on_map_wheel(event: tk.Event) -> None:
            if not hasattr(self, "world_map_canvas"):
                return
            if event.state & 0x1:
                self.world_map_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                self.world_map_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_map_wheel(widget: tk.Widget) -> None:
            widget.bind("<Enter>", lambda _e: self.bind_all("<MouseWheel>", _on_map_wheel))
            widget.bind("<Leave>", lambda _e: self.unbind_all("<MouseWheel>"))

        _bind_map_wheel(self.world_map_canvas)
        _bind_map_wheel(map_canvas_frame)
        self.world_map_canvas.bind("<Configure>", self._draw_world_map_tab)

        side = ttk.Frame(root, style="Card.TFrame", padding=12)
        side.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        side.configure(width=220)
        side.grid_propagate(False)
        side.columnconfigure(0, weight=1)
        side.rowconfigure(1, weight=1)
        self.map_side_title = ttk.Label(side, text="", style="CardTitle.TLabel")
        self.map_side_title.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.map_side_title, "text", "🌐 Podgląd miast świata", "🌐 World city snapshot")
        self.map_side_title.configure(justify="left", wraplength=180)
        self.map_side_text = tk.Text(side, wrap="word", relief="flat", borderwidth=0, padx=8, pady=8, font=("Bahnschrift", 11))
        self.map_side_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.map_side_text.tag_configure("heading", font=("Bahnschrift", 12, "bold"))
        self.map_side_scroll = ttk.Scrollbar(side, orient="vertical", command=self.map_side_text.yview)
        self.map_side_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.map_side_text.configure(yscrollcommand=self.map_side_scroll.set, state="disabled")
        side.bind("<Configure>", self._refresh_map_side_layout)
        self.map_side_text.bind("<Configure>", self._refresh_map_side_layout)
        self._draw_world_map_tab()

    def _get_world_map_image(self, target_width: int, target_height: int) -> tk.PhotoImage | None:
        if not MAP_IMAGE_FILE.is_file():
            return None
        if not hasattr(self, "_world_map_base_image"):
            try:
                self._world_map_base_image = tk.PhotoImage(file=str(MAP_IMAGE_FILE))
            except tk.TclError:
                return None
        base: tk.PhotoImage = self._world_map_base_image
        base_w = max(1, int(base.width()))
        base_h = max(1, int(base.height()))
        scale_w = target_width / base_w
        scale_h = target_height / base_h
        scale = max(scale_w, scale_h)
        scale = max(0.1, min(scale, 6.0))

        def _approx_ratio(value: float, max_den: int = 18) -> tuple[int, int]:
            best_num, best_den = 1, 1
            best_err = abs(value - 1.0)
            for den in range(1, max_den + 1):
                num = max(1, int(round(value * den)))
                err = abs(num / den - value)
                if err < best_err:
                    best_num, best_den, best_err = num, den, err
            return best_num, best_den

        num, den = _approx_ratio(scale)
        scale_key = (num, den, base_w, base_h)
        if getattr(self, "_world_map_scale", None) != scale_key:
            self._world_map_scale = scale_key
            scaled = base.zoom(num, num).subsample(den, den)
            self._world_map_scaled_image = scaled
        return self._world_map_scaled_image

    def _draw_world_map_tab(self, event: tk.Event | None = None) -> None:
        if not hasattr(self, "world_map_canvas"):
            return
        canvas = self.world_map_canvas
        canvas.delete("all")
        view_width = max(canvas.winfo_width(), 320)
        view_height = max(canvas.winfo_height(), 240)
        width = view_width
        height = view_height
        canvas.configure(scrollregion=(0, 0, width, height))

        top = str(self.theme_palette.get("canvas_top", "#1B2747"))
        bottom = str(self.theme_palette.get("canvas_bottom", "#0E1A33"))
        for idx in range(40):
            y0 = int(height * idx / 40)
            y1 = int(height * (idx + 1) / 40)
            color = blend_hex(top, bottom, idx / 39)
            canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")

        left_margin = 0
        right_margin = 0
        map_top = 0
        map_bottom = height
        map_height = max(160, map_bottom - map_top)
        usable_width = max(200, width - left_margin - right_margin)
        map_left = left_margin
        map_right = map_left + usable_width
        draw_left = map_left
        draw_top = map_top
        draw_width = usable_width
        draw_height = map_height
        draw_right = map_right
        draw_bottom = map_bottom

        def lon_to_x(lon: float) -> float:
            return draw_left + ((lon + 180.0) / 360.0) * draw_width

        land_outline = blend_hex(str(self.theme_palette.get("clock_border", "#A9C9FF")), "#FFFFFF", 0.35)
        map_image = self._get_world_map_image(int(usable_width), int(map_height))
        if map_image is not None:
            img_w = max(1, int(map_image.width()))
            img_h = max(1, int(map_image.height()))
            draw_left = map_left + (usable_width - img_w) / 2
            draw_top = map_top + (map_height - img_h) / 2
            draw_width = img_w
            draw_height = img_h
            draw_right = draw_left + draw_width
            draw_bottom = draw_top + draw_height
            canvas.create_image(draw_left + draw_width / 2, draw_top + draw_height / 2, image=map_image)
        else:
            land_fill = blend_hex(str(self.theme_palette.get("card_bg", "#17223C")), "#5F7FB5", 0.35)

            continents = [
                # North America
                [(0.05, 0.18), (0.10, 0.10), (0.20, 0.08), (0.28, 0.12), (0.34, 0.18), (0.38, 0.26),
                 (0.40, 0.34), (0.36, 0.40), (0.30, 0.44), (0.24, 0.48), (0.18, 0.54), (0.12, 0.56),
                 (0.08, 0.50), (0.06, 0.40)],
                # South America
                [(0.27, 0.50), (0.32, 0.56), (0.35, 0.64), (0.34, 0.74), (0.31, 0.84), (0.27, 0.88),
                 (0.24, 0.80), (0.23, 0.68), (0.24, 0.58)],
                # Europe
                [(0.43, 0.20), (0.47, 0.18), (0.52, 0.20), (0.54, 0.24), (0.50, 0.28), (0.46, 0.28)],
                # Africa
                [(0.48, 0.30), (0.56, 0.32), (0.60, 0.40), (0.60, 0.52), (0.56, 0.64), (0.50, 0.70),
                 (0.46, 0.62), (0.45, 0.48)],
                # Asia
                [(0.55, 0.20), (0.62, 0.16), (0.70, 0.18), (0.80, 0.22), (0.90, 0.28), (0.95, 0.38),
                 (0.92, 0.46), (0.84, 0.50), (0.76, 0.48), (0.70, 0.44), (0.64, 0.38), (0.58, 0.34)],
                # Australia
                [(0.78, 0.72), (0.86, 0.70), (0.92, 0.76), (0.90, 0.84), (0.82, 0.86), (0.76, 0.80)],
                # Greenland
                [(0.28, 0.02), (0.32, 0.04), (0.34, 0.08), (0.30, 0.10), (0.26, 0.06)],
            ]

            for poly in continents:
                points: list[float] = []
                for nx, ny in poly:
                    x = draw_left + nx * draw_width
                    y = draw_top + ny * draw_height
                    points.extend([x, y])
                canvas.create_polygon(points, fill=land_fill, outline=land_outline, width=2, smooth=True)

        offsets = list(range(-12, 13))

        def offset_band_bounds(offset: int) -> tuple[float, float]:
            lon_left = (offset - 0.5) * 15.0
            lon_right = (offset + 0.5) * 15.0
            lon_left = max(-180.0, lon_left)
            lon_right = min(180.0, lon_right)
            return lon_left, lon_right

        for i, offset in enumerate(offsets):
            lon_left, lon_right = offset_band_bounds(offset)
            x0 = lon_to_x(lon_left)
            x1 = lon_to_x(lon_right)
            if x1 <= x0:
                continue
            base_band = str(self.theme_palette.get("accent_soft", "#4D7FD4"))
            tone = 0.12 if i % 2 == 0 else 0.26
            band = blend_hex(base_band, str(self.theme_palette.get("canvas_bottom", "#0E1A33")), tone)
            canvas.create_rectangle(x0, draw_top, x1, draw_bottom, fill=band, outline=blend_hex(band, "#FFFFFF", 0.2), width=1, stipple="gray25")

        now_utc = datetime.now(timezone.utc)
        subsolar = (now_utc.hour + now_utc.minute / 60 + now_utc.second / 3600 - 12) * 15.0

        night_overlay = blend_hex(str(self.theme_palette.get("canvas_bottom", "#0E1A33")), "#000000", 0.35)
        canvas.create_rectangle(draw_left, draw_top, draw_right, draw_bottom, fill=night_overlay, outline="", stipple="gray50")

        day_overlay = blend_hex(str(self.theme_palette.get("accent_soft", "#4D7FD4")), "#FFFFFF", 0.65)
        day_start = subsolar - 90
        day_end = subsolar + 90
        if day_start < -180 or day_end > 180:
            if day_start < -180:
                canvas.create_rectangle(lon_to_x(day_start + 360), draw_top, draw_right, draw_bottom, fill=day_overlay, outline="", stipple="gray25")
                canvas.create_rectangle(draw_left, draw_top, lon_to_x(day_end), draw_bottom, fill=day_overlay, outline="", stipple="gray25")
            else:
                canvas.create_rectangle(lon_to_x(day_start), draw_top, draw_right, draw_bottom, fill=day_overlay, outline="", stipple="gray25")
                canvas.create_rectangle(draw_left, draw_top, lon_to_x(day_end - 360), draw_bottom, fill=day_overlay, outline="", stipple="gray25")
        else:
            canvas.create_rectangle(lon_to_x(day_start), draw_top, lon_to_x(day_end), draw_bottom, fill=day_overlay, outline="", stipple="gray25")

        base_now = self._get_base_now(datetime.now().astimezone())
        base_offset = base_now.utcoffset() or timedelta(0)
        base_offset_hours = base_offset.total_seconds() / 3600.0
        base_offset_rounded = int(round(base_offset_hours))
        base_offset_rounded = max(-12, min(12, base_offset_rounded))
        base_lon_left, base_lon_right = offset_band_bounds(base_offset_rounded)
        highlight_x0 = lon_to_x(base_lon_left)
        highlight_x1 = lon_to_x(base_lon_right)
        highlight_color = "#FFD84D"
        highlight_fill = blend_hex(highlight_color, "#FFF7C2", 0.25)
        canvas.create_rectangle(highlight_x0, draw_top, highlight_x1, draw_bottom, fill=highlight_fill, outline=blend_hex(highlight_color, "#FFFFFF", 0.18), width=2, stipple="gray25")

        grid_color = blend_hex(str(self.theme_palette.get("muted", "#C4D8F2")), bottom, 0.55)
        for lon in range(-180, 181, 15):
            x = draw_left + ((lon + 180) / 360) * draw_width
            canvas.create_line(x, draw_top, x, draw_bottom, fill=grid_color, width=1, dash=(2, 6))
        for lat in range(-60, 61, 30):
            y = draw_top + ((90 - lat) / 180) * draw_height
            canvas.create_line(draw_left, y, draw_right, y, fill=grid_color, width=1, dash=(2, 6))

        utc_font_size = max(8, min(11, int(draw_width / 180)))
        label_font = ("Bahnschrift", utc_font_size, "bold")
        label_row_height = max(16, utc_font_size + 8)
        label_y_top = 10
        for i, offset in enumerate(offsets):
            lon_left, lon_right = offset_band_bounds(offset)
            x0 = lon_to_x(lon_left)
            x1 = lon_to_x(lon_right)
            if x1 <= x0:
                continue
            label = f"UTC{offset:+d}"
            label_bg = blend_hex(str(self.theme_palette.get("card_bg", "#17223C")), "#000000", 0.25)
            row = i % 2
            label_y = label_y_top + row * label_row_height
            canvas.create_rectangle(
                x0 + 2,
                label_y - 10,
                x1 - 2,
                label_y + 10,
                fill=label_bg,
                outline=blend_hex(label_bg, "#FFFFFF", 0.2),
                width=1,
            )
            canvas.create_text(
                (x0 + x1) / 2,
                label_y,
                text=label,
                fill=str(self.theme_palette.get("heading", "#F8FAFC")),
                font=label_font,
            )

        city_font_size = max(10, min(16, int(draw_width / 100)))
        font = tkfont.Font(family="Bahnschrift", size=city_font_size, weight="bold")
        placed: list[tuple[float, float, float, float]] = []

        def place_label(cx: float, cy: float, text: str) -> tuple[float, float, float, float]:
            lines = text.splitlines()
            text_width = max(font.measure(line) for line in lines) if lines else 40
            line_h = font.metrics("linespace")
            text_height = max(1, len(lines)) * line_h
            pad_x, pad_y = 6, 4
            box_w = text_width + 2 * pad_x
            box_h = text_height + 2 * pad_y
            offsets = [(0, -28), (0, 28), (28, -16), (-28, -16), (28, 16), (-28, 16), (-44, 0), (44, 0)]
            bounds_left = max(4, draw_left)
            bounds_right = min(width - 4, draw_right)
            bounds_top = max(4, draw_top)
            bounds_bottom = min(height - 4, draw_bottom)
            for ox, oy in offsets:
                x0 = cx + ox - box_w / 2
                y0 = cy + oy - box_h / 2
                x1 = x0 + box_w
                y1 = y0 + box_h
                if x0 < bounds_left or x1 > bounds_right or y0 < bounds_top or y1 > bounds_bottom:
                    continue
                overlap = False
                for bx0, by0, bx1, by1 in placed:
                    if not (x1 < bx0 or x0 > bx1 or y1 < by0 or y0 > by1):
                        overlap = True
                        break
                if not overlap:
                    placed.append((x0, y0, x1, y1))
                    return cx + ox, cy + oy, box_w, box_h
            fallback_x = min(max(cx, bounds_left + box_w / 2), bounds_right - box_w / 2)
            fallback_y = min(max(cy + 24, bounds_top + box_h / 2), bounds_bottom - box_h / 2)
            placed.append((fallback_x - box_w / 2, fallback_y - box_h / 2, fallback_x + box_w / 2, fallback_y + box_h / 2))
            return fallback_x, fallback_y, box_w, box_h

        for city_name, zone_id in WORLD_HIGHLIGHTS:
            lon = MAP_CITY_LONGITUDE.get(city_name)
            lat = MAP_CITY_LATITUDE.get(city_name, 0.0)
            if lon is None:
                continue
            city_now = self.engine.convert(now_utc, zone_id)
            city_label = self._city_display_name(city_name)
            x = draw_left + ((lon + 180.0) / 360.0) * draw_width
            y = draw_top + ((90.0 - lat) / 180.0) * draw_height
            dot_radius = max(4, min(7, int(draw_width / 240)))
            canvas.create_oval(
                x - dot_radius,
                y - dot_radius,
                x + dot_radius,
                y + dot_radius,
                fill=str(self.theme_palette.get("clock_second", "#FF6B6B")),
                outline=blend_hex(str(self.theme_palette.get("clock_border", "#A9C9FF")), "#FFFFFF", 0.35),
                width=1,
            )
            label_x, label_y, box_w, box_h = place_label(x, y, f"{city_label}\n{city_now:%H:%M}")
            box_left = label_x - box_w / 2
            box_top = label_y - box_h / 2
            box_right = box_left + box_w
            box_bottom = box_top + box_h
            label_bg = blend_hex(str(self.theme_palette.get("card_bg", "#17223C")), "#000000", 0.35)
            canvas.create_line(x, y, label_x, label_y, fill=land_outline, width=1)
            canvas.create_rectangle(
                box_left,
                box_top,
                box_right,
                box_bottom,
                fill=label_bg,
                outline=blend_hex(label_bg, "#FFFFFF", 0.2),
                width=1,
                stipple="gray50",
            )
            canvas.create_text(
                label_x,
                label_y,
                text=f"{city_label}\n{city_now:%H:%M}",
                fill=str(self.theme_palette.get("heading", "#F8FAFC")),
                font=font,
                justify="center",
            )

        if hasattr(self, "map_side_text"):
            lines: list[str] = []
            for city_name, zone_id in WORLD_HIGHLIGHTS:
                city_now = self.engine.convert(now_utc, zone_id)
                lines.append(f"• {self._city_display_name(city_name)} — {city_now:%H:%M:%S} ({city_now.tzname()})")
            self.map_side_text.configure(state="normal")
            self.map_side_text.delete("1.0", "end")
            if self.language_var.get() == "en":
                self.map_side_text.insert("end", "Live world clock snapshot\n\n", ("heading",))
            else:
                self.map_side_text.insert("end", "Podgląd światowych czasów na żywo\n\n", ("heading",))
            self.map_side_text.insert("end", "\n".join(lines))
            self.map_side_text.configure(state="disabled")
            self._refresh_map_side_layout()

    def _build_tiles_tab(self) -> None:
        self.tiles_root = ttk.Frame(self.tiles_tab, style="Root.TFrame")
        self.tiles_root.pack(fill="both", expand=True)
        self.tiles_root.columnconfigure(0, weight=1)
        self.tiles_root.rowconfigure(1, weight=1)

        self.tiles_controls = ttk.Frame(self.tiles_root, style="Card.TFrame", padding=10)
        self.tiles_controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.tiles_controls.columnconfigure(1, weight=1)

        self.tiles_city_label = ttk.Label(self.tiles_controls, text="", style="CardTitle.TLabel")
        self.tiles_city_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(self.tiles_city_label, "text", "Miasto/strefa:", "City/zone:")
        self.tile_query_entry = ttk.Combobox(
            self.tiles_controls,
            textvariable=self.tile_query_var,
            values=self.city_zone_values,
            style="Glass.TCombobox",
            state="normal",
        )
        self.tile_query_entry.grid(row=0, column=1, sticky="ew", padx=(8, 10))
        self.tile_query_entry.bind("<Return>", self._on_tile_enter)
        self._register_autocomplete(self.tile_query_entry, self.city_zone_values)

        self.tiles_add_btn = ttk.Button(self.tiles_controls, text="", style="Action.TButton", command=self._add_tile_from_query)
        self.tiles_add_btn.grid(row=0, column=2, sticky="e", padx=(0, 8))
        self._bind_i18n(self.tiles_add_btn, "text", "➕ Dodaj z miasta", "➕ Add from city")

        self.tiles_session_label = ttk.Label(self.tiles_controls, text="", style="SmallInfo.TLabel")
        self.tiles_session_label.grid(row=0, column=3, sticky="w")
        self._bind_i18n(self.tiles_session_label, "text", "Sesja:", "Session:")
        self.tile_session_combo = ttk.Combobox(
            self.tiles_controls,
            textvariable=self.tile_session_var,
            values=[],
            state="readonly",
            width=34,
            style="Glass.TCombobox",
        )
        self.tile_session_combo.grid(row=0, column=4, sticky="w", padx=(8, 10))
        self._refresh_session_combo_values()

        self.tiles_add_session_btn = ttk.Button(self.tiles_controls, text="", style="Action.TButton", command=self._add_tile_from_session)
        self.tiles_add_session_btn.grid(row=0, column=5, sticky="e", padx=(0, 8))
        self._bind_i18n(self.tiles_add_session_btn, "text", "🏛 Dodaj z sesji", "🏛 Add from session")
        self.tiles_add_base_btn = ttk.Button(self.tiles_controls, text="", style="Action.TButton", command=self._add_base_tile)
        self.tiles_add_base_btn.grid(row=0, column=6, sticky="e", padx=(0, 8))
        self._bind_i18n(self.tiles_add_base_btn, "text", "🕒 Dodaj bazowy", "🕒 Add base tile")
        self.tiles_add_defaults_btn = ttk.Button(self.tiles_controls, text="", style="Action.TButton", command=self._add_default_tiles)
        self.tiles_add_defaults_btn.grid(row=0, column=7, sticky="e", padx=(0, 8))
        self._bind_i18n(self.tiles_add_defaults_btn, "text", "📦 Sesje domyślne", "📦 Default sessions")
        self.tiles_clear_btn = ttk.Button(self.tiles_controls, text="", style="Action.TButton", command=self._clear_tiles)
        self.tiles_clear_btn.grid(row=0, column=8, sticky="e", padx=(0, 8))
        self._bind_i18n(self.tiles_clear_btn, "text", "🧹 Wyczyść", "🧹 Clear")
        self.tiles_grid_btn = ttk.Button(self.tiles_controls, text="", style="Action.TButton", command=self._align_tiles_to_grid)
        self.tiles_grid_btn.grid(row=0, column=9, sticky="e", padx=(0, 8))
        self._bind_i18n(self.tiles_grid_btn, "text", "🧲 Wyrównaj do siatki", "🧲 Align to grid")
        self.tiles_fullscreen_btn = ttk.Button(self.tiles_controls, text="", style="Action.TButton", command=self._toggle_fullscreen)
        self.tiles_fullscreen_btn.grid(row=0, column=10, sticky="e")
        self._bind_i18n(self.tiles_fullscreen_btn, "text", "🖥 Pełny ekran kafelków", "🖥 Tile fullscreen")

        ttk.Label(self.tiles_controls, textvariable=self.tile_status_var, style="SmallInfo.TLabel", wraplength=1260).grid(row=1, column=0, columnspan=11, sticky="w", pady=(8, 0))

        self.tiles_ticking_check = ttk.Checkbutton(self.tiles_controls, text="", variable=self.tile_ticking_var, command=self._on_tile_ticking_toggle)
        self.tiles_ticking_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self._bind_i18n(self.tiles_ticking_check, "text", "Tykanie (tylko aktywna sesja)", "Ticking (only active session)")
        self.tiles_session_sound_check = ttk.Checkbutton(self.tiles_controls, text="", variable=self.session_sound_enabled_var)
        self.tiles_session_sound_check.grid(row=2, column=3, columnspan=3, sticky="w", pady=(6, 0))
        self._bind_i18n(self.tiles_session_sound_check, "text", "Powiadomienie startu/zakończenia sesji", "Session start/end notifications")
        self.tiles_fullscreen_layout_check = ttk.Checkbutton(self.tiles_controls, text="", variable=self.fullscreen_auto_layout_var, command=self._on_fullscreen_layout_toggle)
        self.tiles_fullscreen_layout_check.grid(row=2, column=6, columnspan=3, sticky="w", pady=(6, 0))
        self._bind_i18n(self.tiles_fullscreen_layout_check, "text", "Wyrównaj i skaluj w pełnym ekranie", "Align & scale in fullscreen")

        self.tiles_area = ttk.Frame(self.tiles_root, style="Card.TFrame", padding=0)
        self.tiles_area.grid(row=1, column=0, sticky="nsew")
        self.tiles_area.columnconfigure(0, weight=1)
        self.tiles_area.rowconfigure(0, weight=1)

        self.tiles_canvas = tk.Canvas(self.tiles_area, bg=str(self.theme_palette.get("canvas_bottom", "#0E1A33")), highlightthickness=0)
        self.tiles_canvas.grid(row=0, column=0, sticky="nsew")

        self.tiles_scroll = ttk.Scrollbar(self.tiles_area, orient="vertical", command=self.tiles_canvas.yview)
        self.tiles_scroll.grid(row=0, column=1, sticky="ns")
        self.tiles_canvas.configure(yscrollcommand=self.tiles_scroll.set)
        self.tiles_canvas.bind("<Configure>", self._on_tiles_canvas_configure)
        self._bind_mousewheel_to_canvas(self.tiles_canvas, self.tiles_canvas)
        self._bind_mousewheel_to_canvas(self.tiles_area, self.tiles_canvas)

    def _build_alarms_tab(self) -> None:
        root = ttk.Frame(self.alarms_tab, style="Root.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root, style="Card.TFrame", padding=12)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        header_title = ttk.Label(header, text="", style="CardTitle.TLabel")
        header_title.grid(row=0, column=0, sticky="w")
        self._bind_i18n(header_title, "text", "⏰ Alarmy, timery i stoper", "⏰ Alarms, timers, and stopwatch")
        header_subtitle = ttk.Label(header, text="", style="SmallInfo.TLabel", wraplength=1280, justify="left")
        header_subtitle.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._bind_i18n(
            header_subtitle,
            "text",
            "Dodaj kilka alarmów w różnych strefach. Alarm uruchamia się w czasie lokalnym wybranej strefy.",
            "Add multiple alarms in different zones. Each alarm fires in the local time of its zone.",
        )

        alarms_card = ttk.Frame(root, style="Card.TFrame", padding=12)
        alarms_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        alarms_card.columnconfigure(0, weight=1)
        alarms_card.rowconfigure(1, weight=1)

        alarms_title = ttk.Label(alarms_card, text="", style="CardTitle.TLabel")
        alarms_title.grid(row=0, column=0, sticky="w")
        self._bind_i18n(alarms_title, "text", "📌 Lista alarmów", "📌 Alarm list")

        columns = ("label", "zone", "time", "date", "repeat", "duration", "sound", "enabled")
        self.alarms_tree = ttk.Treeview(alarms_card, columns=columns, show="headings", selectmode="browse")
        self.alarms_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.alarms_tree.heading("label", text=self._t("Nazwa", "Label"))
        self.alarms_tree.heading("zone", text=self._t("Strefa", "Zone"))
        self.alarms_tree.heading("time", text=self._t("Godzina", "Time"))
        self.alarms_tree.heading("date", text=self._t("Data", "Date"))
        self.alarms_tree.heading("repeat", text=self._t("Rodzaj", "Kind"))
        self.alarms_tree.heading("duration", text=self._t("Długość", "Duration"))
        self.alarms_tree.heading("sound", text=self._t("Dźwięk", "Sound"))
        self.alarms_tree.heading("enabled", text=self._t("Status", "Status"))
        self.alarms_tree.column("label", width=160, anchor="w")
        self.alarms_tree.column("zone", width=170, anchor="w")
        self.alarms_tree.column("time", width=90, anchor="center")
        self.alarms_tree.column("date", width=110, anchor="center")
        self.alarms_tree.column("repeat", width=150, anchor="center")
        self.alarms_tree.column("duration", width=90, anchor="center")
        self.alarms_tree.column("sound", width=200, anchor="w")
        self.alarms_tree.column("enabled", width=90, anchor="center")
        self.alarms_tree.bind("<<TreeviewSelect>>", self._on_alarm_select)
        self._configure_alarm_tree_tags()

        alarm_scroll = ttk.Scrollbar(alarms_card, orient="vertical", command=self.alarms_tree.yview)
        alarm_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.alarms_tree.configure(yscrollcommand=alarm_scroll.set)

        form = ttk.Frame(alarms_card, style="Card.TFrame", padding=8)
        form.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        for col in range(4):
            form.columnconfigure(col, weight=1)

        alarm_label = ttk.Label(form, text="", style="SmallInfo.TLabel")
        alarm_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(alarm_label, "text", "Nazwa alarmu:", "Alarm label:")
        self.alarm_label_entry = ttk.Entry(form, textvariable=self.alarm_label_var, style="Search.TEntry")
        self.alarm_label_entry.grid(row=0, column=1, sticky="ew", padx=(6, 12))

        alarm_zone = ttk.Label(form, text="", style="SmallInfo.TLabel")
        alarm_zone.grid(row=0, column=2, sticky="w")
        self._bind_i18n(alarm_zone, "text", "Strefa czasowa:", "Time zone:")
        self.alarm_zone_entry = ttk.Combobox(
            form,
            textvariable=self.alarm_zone_var,
            values=self.iana_zone_values,
            style="Glass.TCombobox",
            state="normal",
        )
        self.alarm_zone_entry.grid(row=0, column=3, sticky="ew", padx=(6, 0))
        self._register_autocomplete(self.alarm_zone_entry, self.iana_zone_values)

        alarm_time_label = ttk.Label(form, text="", style="SmallInfo.TLabel")
        alarm_time_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(alarm_time_label, "text", "Godzina (HH:MM):", "Time (HH:MM):")
        self.alarm_time_entry = ttk.Entry(form, textvariable=self.alarm_time_var, style="Search.TEntry")
        self.alarm_time_entry.grid(row=1, column=1, sticky="ew", padx=(6, 12), pady=(10, 0))

        alarm_date_label = ttk.Label(form, text="", style="SmallInfo.TLabel")
        alarm_date_label.grid(row=1, column=2, sticky="w", pady=(10, 0))
        self._bind_i18n(alarm_date_label, "text", "Data (opcjonalnie):", "Date (optional):")
        date_frame = ttk.Frame(form, style="Card.TFrame")
        date_frame.grid(row=1, column=3, sticky="w", padx=(6, 0), pady=(10, 0))
        date_frame.columnconfigure(0, weight=0)
        date_frame.columnconfigure(1, weight=0)
        date_frame.columnconfigure(2, weight=0)
        day_values = [""] + [f"{d:02d}" for d in range(1, 32)]
        month_values = [""] + [f"{m:02d}" for m in range(1, 13)]
        self.alarm_day_combo = ttk.Combobox(date_frame, textvariable=self.alarm_day_var, values=day_values, width=4, state="readonly", style="Glass.TCombobox")
        self.alarm_day_combo.grid(row=0, column=0, padx=(0, 4))
        self.alarm_month_combo = ttk.Combobox(date_frame, textvariable=self.alarm_month_var, values=month_values, width=4, state="readonly", style="Glass.TCombobox")
        self.alarm_month_combo.grid(row=0, column=1, padx=(0, 4))
        self.alarm_year_entry = ttk.Entry(date_frame, textvariable=self.alarm_year_var, width=6, style="Search.TEntry")
        self.alarm_year_entry.grid(row=0, column=2)

        alarm_duration_label = ttk.Label(form, text="", style="SmallInfo.TLabel")
        alarm_duration_label.grid(row=2, column=2, sticky="w", pady=(10, 0))
        self._bind_i18n(alarm_duration_label, "text", "Długość dzwonienia (s):", "Ring duration (s):")
        self.alarm_duration_entry = ttk.Entry(form, textvariable=self.alarm_duration_var, style="Search.TEntry")
        self.alarm_duration_entry.grid(row=2, column=3, sticky="ew", padx=(6, 0), pady=(10, 0))

        alarm_sound_label = ttk.Label(form, text="", style="SmallInfo.TLabel")
        alarm_sound_label.grid(row=3, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(alarm_sound_label, "text", "Dźwięk alarmu:", "Alarm sound:")
        self.alarm_sound_combo = ttk.Combobox(
            form,
            textvariable=self.alarm_sound_display_var,
            values=[],
            state="readonly",
            style="Glass.TCombobox",
        )
        self.alarm_sound_combo.grid(row=3, column=1, columnspan=3, sticky="ew", padx=(6, 0), pady=(10, 0))
        self.alarm_sound_combo.bind("<<ComboboxSelected>>", self._on_alarm_sound_select)

        alarm_script_label = ttk.Label(form, text="", style="SmallInfo.TLabel")
        alarm_script_label.grid(row=4, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(alarm_script_label, "text", "Skrypt (opcjonalnie):", "Script (optional):")
        self.alarm_script_entry = ttk.Entry(form, textvariable=self.alarm_script_var, style="Search.TEntry")
        self.alarm_script_entry.grid(row=4, column=1, columnspan=2, sticky="ew", padx=(6, 8), pady=(10, 0))
        self.alarm_script_browse_btn = ttk.Button(form, text="", style="Action.TButton", command=self._browse_alarm_script)
        self.alarm_script_browse_btn.grid(row=4, column=3, sticky="e", pady=(10, 0))
        self._bind_i18n(self.alarm_script_browse_btn, "text", "📂 Wybierz", "📂 Browse")

        self.alarms_pause_check = ttk.Checkbutton(form, text="", variable=self.alarms_paused_var, command=self._on_alarms_pause_toggle)
        self.alarms_pause_check.grid(row=5, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(self.alarms_pause_check, "text", "Pauza alarmów i timerów", "Pause alarms & timers")

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=5, column=1, columnspan=3, sticky="e", pady=(10, 0))
        self.alarm_add_btn = ttk.Button(buttons, text="", style="Action.TButton", command=self._add_alarm)
        self.alarm_add_btn.grid(row=0, column=0, padx=(0, 6))
        self._bind_i18n(self.alarm_add_btn, "text", "➕ Dodaj", "➕ Add")
        self.alarm_update_btn = ttk.Button(buttons, text="", style="Action.TButton", command=self._update_alarm)
        self.alarm_update_btn.grid(row=0, column=1, padx=(0, 6))
        self._bind_i18n(self.alarm_update_btn, "text", "💾 Aktualizuj", "💾 Update")
        self.alarm_toggle_btn = ttk.Button(buttons, text="", style="Action.TButton", command=self._toggle_alarm)
        self.alarm_toggle_btn.grid(row=0, column=2, padx=(0, 6))
        self._bind_i18n(self.alarm_toggle_btn, "text", "⏻ Włącz/Wyłącz", "⏻ Toggle")
        self.alarm_remove_btn = ttk.Button(buttons, text="", style="Action.TButton", command=self._remove_alarm)
        self.alarm_remove_btn.grid(row=0, column=3, padx=(0, 6))
        self._bind_i18n(self.alarm_remove_btn, "text", "🗑 Usuń", "🗑 Remove")
        self.alarm_test_btn = ttk.Button(buttons, text="", style="Action.TButton", command=self._test_alarm_sound)
        self.alarm_test_btn.grid(row=0, column=4, padx=(0, 6))
        self._bind_i18n(self.alarm_test_btn, "text", "🔔 Test dźwięku", "🔔 Test sound")
        self.alarm_clear_btn = ttk.Button(buttons, text="", style="Action.TButton", command=self._clear_alarm_fields)
        self.alarm_clear_btn.grid(row=0, column=5)
        self._bind_i18n(self.alarm_clear_btn, "text", "🧹 Wyczyść", "🧹 Clear")

        self.alarm_status_label = ttk.Label(alarms_card, textvariable=self.alarm_status_var, style="AlarmStatus.TLabel", wraplength=1100, justify="left")
        self.alarm_status_label.grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.alarm_help_label = ttk.Label(alarms_card, text="", style="SmallInfo.TLabel", wraplength=1100, justify="left")
        self.alarm_help_label.grid(row=4, column=0, sticky="w", pady=(6, 0))
        self._bind_i18n(
            self.alarm_help_label,
            "text",
            "Opis pól: nazwa = etykieta alarmu, strefa = gdzie ma zadzwonić, data opcjonalna (dzień/miesiąc/rok). "
            "Kolumna Rodzaj pokazuje ∞ dla alarmu bez daty, Jednorazowy dla alarmu z datą "
            "oraz dopisek / Skrypt, gdy uruchamiany jest dodatkowy skrypt. "
            "Pauza alarmów i timerów wstrzymuje całą sekcję bez zmiany statusów. Skrypt uruchamia się wraz z dźwiękiem.",
            "Field help: label = alarm name, zone = where it should ring, date optional (day/month/year), "
            "the Kind column shows ∞ for alarms without a date, One-off for alarms with a date, "
            "and adds / Script when an extra script is attached. "
            "Pause alarms & timers stops the whole section without changing statuses. Script runs together with the sound.",
        )
        self._set_alarm_pause_status_text(mark_dirty=False)

        right = ttk.Frame(root, style="Root.TFrame")
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        stopwatch_card = ttk.Frame(right, style="Card.TFrame", padding=12)
        stopwatch_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        stopwatch_card.columnconfigure(0, weight=1)
        stopwatch_title = ttk.Label(stopwatch_card, text="", style="CardTitle.TLabel")
        stopwatch_title.grid(row=0, column=0, sticky="w")
        self._bind_i18n(stopwatch_title, "text", "⏱️ Stoper", "⏱️ Stopwatch")
        ttk.Label(stopwatch_card, textvariable=self.stopwatch_time_var, style="Clock.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        sw_buttons = ttk.Frame(stopwatch_card, style="Card.TFrame")
        sw_buttons.grid(row=2, column=0, sticky="w", pady=(10, 0))
        sw_start = ttk.Button(sw_buttons, text="", style="Action.TButton", command=self._start_stopwatch)
        sw_start.grid(row=0, column=0, padx=(0, 6))
        self._bind_i18n(sw_start, "text", "▶ Start", "▶ Start")
        sw_stop = ttk.Button(sw_buttons, text="", style="Action.TButton", command=self._stop_stopwatch)
        sw_stop.grid(row=0, column=1, padx=(0, 6))
        self._bind_i18n(sw_stop, "text", "■ Stop", "■ Stop")
        sw_reset = ttk.Button(sw_buttons, text="", style="Action.TButton", command=self._reset_stopwatch)
        sw_reset.grid(row=0, column=2)
        self._bind_i18n(sw_reset, "text", "↺ Reset", "↺ Reset")

        timer_card = ttk.Frame(right, style="Card.TFrame", padding=12)
        timer_card.grid(row=1, column=0, sticky="nsew")
        timer_card.columnconfigure(0, weight=1)
        timer_title = ttk.Label(timer_card, text="", style="CardTitle.TLabel")
        timer_title.grid(row=0, column=0, sticky="w")
        self._bind_i18n(timer_title, "text", "⏲️ Timer", "⏲️ Timer")
        ttk.Label(timer_card, textvariable=self.timer_remaining_var, style="Clock.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))

        timer_controls = ttk.Frame(timer_card, style="Card.TFrame")
        timer_controls.grid(row=2, column=0, sticky="w", pady=(10, 0))
        timer_minutes_label = ttk.Label(timer_controls, text="", style="SmallInfo.TLabel")
        timer_minutes_label.grid(row=0, column=0, sticky="w")
        self._bind_i18n(timer_minutes_label, "text", "Minuty:", "Minutes:")
        timer_minutes_entry = ttk.Entry(timer_controls, textvariable=self.timer_minutes_var, width=6, style="Search.TEntry")
        timer_minutes_entry.grid(row=0, column=1, padx=(6, 12))
        timer_seconds_label = ttk.Label(timer_controls, text="", style="SmallInfo.TLabel")
        timer_seconds_label.grid(row=0, column=2, sticky="w")
        self._bind_i18n(timer_seconds_label, "text", "Sekundy:", "Seconds:")
        timer_seconds_entry = ttk.Entry(timer_controls, textvariable=self.timer_seconds_var, width=6, style="Search.TEntry")
        timer_seconds_entry.grid(row=0, column=3, padx=(6, 12))

        timer_script_label = ttk.Label(timer_controls, text="", style="SmallInfo.TLabel")
        timer_script_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(timer_script_label, "text", "Skrypt po czasie:", "Script on finish:")
        self.timer_script_entry = ttk.Entry(timer_controls, textvariable=self.timer_script_var, width=28, style="Search.TEntry")
        self.timer_script_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(6, 12), pady=(10, 0))
        self.timer_script_browse_btn = ttk.Button(timer_controls, text="", style="Action.TButton", command=self._browse_timer_script)
        self.timer_script_browse_btn.grid(row=1, column=3, sticky="e", pady=(10, 0))
        self._bind_i18n(self.timer_script_browse_btn, "text", "📂 Wybierz", "📂 Browse")

        self.timer_repeat_check = ttk.Checkbutton(timer_controls, text="", variable=self.timer_repeat_var)
        self.timer_repeat_check.grid(row=2, column=0, sticky="w", pady=(10, 0))
        self._bind_i18n(self.timer_repeat_check, "text", "Powtarzaj co (min):", "Repeat every (min):")
        self.timer_repeat_entry = ttk.Entry(timer_controls, textvariable=self.timer_repeat_minutes_var, width=6, style="Search.TEntry")
        self.timer_repeat_entry.grid(row=2, column=1, sticky="w", padx=(6, 12), pady=(10, 0))

        timer_buttons = ttk.Frame(timer_card, style="Card.TFrame")
        timer_buttons.grid(row=3, column=0, sticky="w", pady=(8, 0))
        timer_start = ttk.Button(timer_buttons, text="", style="Action.TButton", command=self._start_timer)
        timer_start.grid(row=0, column=0, padx=(0, 6))
        self._bind_i18n(timer_start, "text", "▶ Start", "▶ Start")
        timer_stop = ttk.Button(timer_buttons, text="", style="Action.TButton", command=self._stop_timer)
        timer_stop.grid(row=0, column=1, padx=(0, 6))
        self._bind_i18n(timer_stop, "text", "■ Stop", "■ Stop")
        timer_reset = ttk.Button(timer_buttons, text="", style="Action.TButton", command=self._reset_timer)
        timer_reset.grid(row=0, column=2)
        self._bind_i18n(timer_reset, "text", "↺ Reset", "↺ Reset")

        self.timer_help_label = ttk.Label(timer_card, text="", style="SmallInfo.TLabel", wraplength=520, justify="left")
        self.timer_help_label.grid(row=4, column=0, sticky="w", pady=(6, 0))
        self._bind_i18n(
            self.timer_help_label,
            "text",
            "Opis pól: minuty/sekundy = czas odliczania, skrypt uruchomi się po końcu, "
            "powtarzaj co X min uruchamia skrypt cyklicznie.",
            "Field help: minutes/seconds = countdown, script runs on finish, "
            "repeat every X minutes runs the script cyclically.",
        )

        self._refresh_alarm_tree()
        self._refresh_alarm_sound_values()

    def _build_links_tab(self) -> None:
        root = ttk.Frame(self.links_tab, style="Root.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root, style="Card.TFrame", padding=12)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        title = ttk.Label(header, text="", style="CardTitle.TLabel")
        title.grid(row=0, column=0, sticky="w")
        self._bind_i18n(title, "text", "🔗 Źródła czasu i standardów", "🔗 Time sources and standards")
        subtitle = ttk.Label(header, text="", style="SmallInfo.TLabel", wraplength=1280, justify="left")
        subtitle.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._bind_i18n(
            subtitle,
            "text",
            "Linki do najważniejszych instytucji utrzymujących UTC, TAI i synchronizację czasu.",
            "Links to key institutions maintaining UTC, TAI, and official time services.",
        )

        links_holder = ttk.Frame(root, style="Root.TFrame")
        links_holder.grid(row=1, column=0, sticky="nsew")
        links_holder.columnconfigure(0, weight=1)
        links_holder.rowconfigure(0, weight=1)

        self.links_canvas = tk.Canvas(links_holder, highlightthickness=0, bg=str(self.theme_palette.get("canvas_bottom", "#0E1A33")))
        self.links_canvas.grid(row=0, column=0, sticky="nsew")
        links_scroll = ttk.Scrollbar(links_holder, orient="vertical", command=self.links_canvas.yview)
        links_scroll.grid(row=0, column=1, sticky="ns")
        self.links_canvas.configure(yscrollcommand=links_scroll.set)

        links_frame = ttk.Frame(self.links_canvas, style="Root.TFrame")
        self.links_window_id = self.links_canvas.create_window((0, 0), window=links_frame, anchor="nw")
        links_frame.columnconfigure(0, weight=1)

        def _on_links_configure(_event: tk.Event | None = None) -> None:
            if not hasattr(self, "links_canvas"):
                return
            self.links_canvas.configure(scrollregion=self.links_canvas.bbox("all"))
            canvas_width = self.links_canvas.winfo_width()
            self.links_canvas.itemconfigure(self.links_window_id, width=canvas_width)

        links_frame.bind("<Configure>", _on_links_configure)
        self.links_canvas.bind("<Configure>", _on_links_configure)

        def _on_mousewheel(event: tk.Event) -> None:
            if not hasattr(self, "links_canvas"):
                return
            delta = int(-1 * (event.delta / 120))
            self.links_canvas.yview_scroll(delta, "units")

        def _bind_mousewheel(widget: tk.Widget) -> None:
            widget.bind("<Enter>", lambda _e: self.bind_all("<MouseWheel>", _on_mousewheel))
            widget.bind("<Leave>", lambda _e: self.unbind_all("<MouseWheel>"))

        _bind_mousewheel(self.links_canvas)
        _bind_mousewheel(links_frame)

        for idx, link in enumerate(TIME_LINKS):
            card = ttk.Frame(links_frame, style="Card.TFrame", padding=12)
            card.grid(row=idx, column=0, sticky="ew", pady=(0, 10))
            card.columnconfigure(0, weight=1)
            title_txt_pl = str(link.get("title", {}).get("pl", ""))
            title_txt_en = str(link.get("title", {}).get("en", ""))
            desc_txt_pl = str(link.get("desc", {}).get("pl", ""))
            desc_txt_en = str(link.get("desc", {}).get("en", ""))
            url = str(link.get("url", ""))

            title_label = ttk.Label(card, text="", style="CardTitle.TLabel")
            title_label.grid(row=0, column=0, sticky="w")
            self._bind_i18n(title_label, "text", title_txt_pl, title_txt_en)
            desc_label = ttk.Label(card, text="", style="Info.TLabel", wraplength=1200, justify="left")
            desc_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
            self._bind_i18n(desc_label, "text", desc_txt_pl, desc_txt_en)
            ttk.Label(card, text=url, style="SmallInfo.TLabel").grid(row=2, column=0, sticky="w", pady=(6, 0))
            open_btn = ttk.Button(card, text="", style="Action.TButton", command=lambda u=url: webbrowser.open(u))
            open_btn.grid(row=0, column=1, rowspan=3, sticky="e", padx=(12, 0))
            self._bind_i18n(open_btn, "text", "↗ Otwórz", "↗ Open")
            _bind_mousewheel(card)

    def _on_tiles_canvas_configure(self, event: tk.Event) -> None:
        self._paint_gradient_background(
            self.tiles_canvas,
            str(self.theme_palette.get("canvas_top", "#1B2747")),
            str(self.theme_palette.get("canvas_bottom", "#0E1A33")),
            tag="bg_gradient",
        )
        self._layout_tiles()

    def _refresh_alarm_tree(self) -> None:
        if not hasattr(self, "alarms_tree"):
            return
        for item in self.alarms_tree.get_children():
            self.alarms_tree.delete(item)
        for alarm in self.alarms:
            alarm_id = int(alarm.get("id", 0))
            label = str(alarm.get("label", ""))
            zone = str(alarm.get("zone", ""))
            time_txt = str(alarm.get("time", ""))
            date_txt = str(alarm.get("date", "")).strip()
            enabled = bool(alarm.get("enabled", True))
            status = self._t("● Włączony", "● Enabled") if enabled else self._t("● Wyłączony", "● Disabled")
            duration = str(alarm.get("duration", "20"))
            sound_id = str(alarm.get("sound_id", DEFAULT_ALARM_SOUND_ID))
            sound_label = self._sound_display_for_id(sound_id)
            repeat_display = self._alarm_kind_display(alarm)
            status_tag = "alarm_enabled" if enabled else "alarm_disabled"
            self.alarms_tree.insert(
                "",
                "end",
                iid=str(alarm_id),
                values=(label, zone, time_txt, date_txt or "-", repeat_display, duration, sound_label, status),
                tags=(status_tag,),
            )

    def _alarm_kind_display(self, alarm: dict[str, object]) -> str:
        has_date = bool(str(alarm.get("date", "")).strip())
        has_script = bool(str(alarm.get("script", "")).strip())
        kind_label = self._t("Jednorazowy", "One-off") if has_date else "∞"
        if has_script:
            kind_label = f"{kind_label} / {self._t('Skrypt', 'Script')}"
        return kind_label

    def _get_alarm_by_id(self, alarm_id: int) -> dict[str, object] | None:
        for alarm in self.alarms:
            if int(alarm.get("id", 0)) == alarm_id:
                return alarm
        return None

    def _on_alarm_select(self, _event: tk.Event) -> None:
        selected = self.alarms_tree.selection() if hasattr(self, "alarms_tree") else ()
        if not selected:
            return
        try:
            alarm_id = int(selected[0])
        except (ValueError, TypeError):
            return
        alarm = self._get_alarm_by_id(alarm_id)
        if not alarm:
            return
        self.alarm_selected_id = alarm_id
        self.alarm_label_var.set(str(alarm.get("label", "")))
        self.alarm_zone_var.set(str(alarm.get("zone", "")))
        self.alarm_time_var.set(str(alarm.get("time", "")))
        alarm_date_str = str(alarm.get("date", "")).strip()
        self.alarm_date_var.set(alarm_date_str)
        parsed_alarm_date = parse_alarm_date(alarm_date_str) if alarm_date_str else None
        if parsed_alarm_date:
            self.alarm_day_var.set(f"{parsed_alarm_date.day:02d}")
            self.alarm_month_var.set(f"{parsed_alarm_date.month:02d}")
            self.alarm_year_var.set(str(parsed_alarm_date.year))
        else:
            self.alarm_day_var.set("")
            self.alarm_month_var.set("")
            self.alarm_year_var.set("")
        self.alarm_enabled_var.set(bool(alarm.get("enabled", True)))
        self.alarm_duration_var.set(str(alarm.get("duration", "20")))
        self.alarm_script_var.set(str(alarm.get("script", "")))
        sound_id = str(alarm.get("sound_id", DEFAULT_ALARM_SOUND_ID))
        self.alarm_sound_id_var.set(sound_id)
        self._refresh_alarm_sound_values()

    def _add_alarm(self) -> None:
        label = self.alarm_label_var.get().strip() or self._t("Alarm", "Alarm")
        zone_hint = self.alarm_zone_var.get().strip()
        zone_id = zone_hint if zone_hint in self.engine.zone_set else self.engine.resolve_zone_hint(zone_hint, allow_online=True)
        if not zone_id or zone_id not in self.engine.zone_set:
            self.alarm_status_var.set(self._t("Nie rozpoznano strefy alarmu.", "Alarm zone not recognized."))
            return
        time_raw = self.alarm_time_var.get().strip()
        if parse_alarm_time(time_raw) is None:
            self.alarm_status_var.set(self._t("Niepoprawny format godziny alarmu.", "Invalid alarm time format."))
            return
        day = self.alarm_day_var.get().strip()
        month = self.alarm_month_var.get().strip()
        year = self.alarm_year_var.get().strip()
        date_raw = ""
        if day or month or year:
            if not (day and month and year):
                self.alarm_status_var.set(self._t("Uzupełnij dzień, miesiąc i rok albo zostaw puste.", "Fill day, month, and year or leave empty."))
                return
            date_raw = f"{year}-{month}-{day}"
        if date_raw and parse_alarm_date(date_raw) is None:
            self.alarm_status_var.set(self._t("Niepoprawny format daty alarmu.", "Invalid alarm date format."))
            return
        duration_raw = self.alarm_duration_var.get().strip() or "20"
        try:
            duration = max(1, int(duration_raw))
        except ValueError:
            self.alarm_status_var.set(self._t("Niepoprawna długość alarmu.", "Invalid alarm duration."))
            return
        repeat_daily = not bool(date_raw)
        script_path = self.alarm_script_var.get().strip()
        sound_id = self._resolve_alarm_sound_id()
        alarm_id = self.next_alarm_id
        self.next_alarm_id += 1
        self.alarms.append(
            {
                "id": alarm_id,
                "label": label,
                "zone": zone_id,
                "time": time_raw,
                "date": date_raw,
                "enabled": bool(self.alarm_enabled_var.get()),
                "repeat_daily": repeat_daily,
                "duration": duration,
                "sound_id": sound_id,
                "script": script_path,
            }
        )
        self.alarm_status_var.set(self._t("Dodano alarm.", "Alarm added."))
        self._refresh_alarm_tree()
        self._mark_settings_dirty()

    def _update_alarm(self) -> None:
        if self.alarm_selected_id is None:
            self.alarm_status_var.set(self._t("Wybierz alarm do edycji.", "Select an alarm to update."))
            return
        alarm = self._get_alarm_by_id(self.alarm_selected_id)
        if not alarm:
            return
        label = self.alarm_label_var.get().strip() or self._t("Alarm", "Alarm")
        zone_hint = self.alarm_zone_var.get().strip()
        zone_id = zone_hint if zone_hint in self.engine.zone_set else self.engine.resolve_zone_hint(zone_hint, allow_online=True)
        if not zone_id or zone_id not in self.engine.zone_set:
            self.alarm_status_var.set(self._t("Nie rozpoznano strefy alarmu.", "Alarm zone not recognized."))
            return
        time_raw = self.alarm_time_var.get().strip()
        if parse_alarm_time(time_raw) is None:
            self.alarm_status_var.set(self._t("Niepoprawny format godziny alarmu.", "Invalid alarm time format."))
            return
        day = self.alarm_day_var.get().strip()
        month = self.alarm_month_var.get().strip()
        year = self.alarm_year_var.get().strip()
        date_raw = ""
        if day or month or year:
            if not (day and month and year):
                self.alarm_status_var.set(self._t("Uzupełnij dzień, miesiąc i rok albo zostaw puste.", "Fill day, month, and year or leave empty."))
                return
            date_raw = f"{year}-{month}-{day}"
        if date_raw and parse_alarm_date(date_raw) is None:
            self.alarm_status_var.set(self._t("Niepoprawny format daty alarmu.", "Invalid alarm date format."))
            return
        duration_raw = self.alarm_duration_var.get().strip() or "20"
        try:
            duration = max(1, int(duration_raw))
        except ValueError:
            self.alarm_status_var.set(self._t("Niepoprawna długość alarmu.", "Invalid alarm duration."))
            return
        repeat_daily = not bool(date_raw)
        script_path = self.alarm_script_var.get().strip()
        sound_id = self._resolve_alarm_sound_id()
        alarm.update(
            {
                "label": label,
                "zone": zone_id,
                "time": time_raw,
                "date": date_raw,
                "enabled": bool(self.alarm_enabled_var.get()),
                "repeat_daily": repeat_daily,
                "duration": duration,
                "sound_id": sound_id,
                "script": script_path,
            }
        )
        self.alarm_status_var.set(self._t("Zaktualizowano alarm.", "Alarm updated."))
        self._refresh_alarm_tree()
        self._mark_settings_dirty()

    def _toggle_alarm(self) -> None:
        if self.alarm_selected_id is None:
            self.alarm_status_var.set(self._t("Wybierz alarm do przełączenia.", "Select an alarm to toggle."))
            return
        alarm = self._get_alarm_by_id(self.alarm_selected_id)
        if not alarm:
            return
        alarm["enabled"] = not bool(alarm.get("enabled", True))
        self.alarm_enabled_var.set(bool(alarm.get("enabled", True)))
        self.alarm_status_var.set(self._t("Zmieniono status alarmu.", "Alarm status updated."))
        self._refresh_alarm_tree()
        self._mark_settings_dirty()

    def _remove_alarm(self) -> None:
        if self.alarm_selected_id is None:
            self.alarm_status_var.set(self._t("Wybierz alarm do usunięcia.", "Select an alarm to remove."))
            return
        alarm_id = self.alarm_selected_id
        self.alarms = [alarm for alarm in self.alarms if int(alarm.get("id", 0)) != alarm_id]
        self.alarm_last_fire.pop(alarm_id, None)
        self.alarm_selected_id = None
        self._refresh_alarm_tree()
        self._mark_settings_dirty()
        self.alarm_status_var.set(self._t("Usunięto alarm.", "Alarm removed."))

    def _clear_alarm_fields(self) -> None:
        self.alarm_selected_id = None
        self.alarm_label_var.set(self._t("Alarm", "Alarm"))
        self.alarm_zone_var.set(self.system_zone_key)
        self.alarm_time_var.set("08:00")
        self.alarm_date_var.set("")
        self.alarm_day_var.set("")
        self.alarm_month_var.set("")
        self.alarm_year_var.set("")
        self.alarm_enabled_var.set(True)
        self.alarm_duration_var.set("20")
        self.alarm_sound_id_var.set(DEFAULT_ALARM_SOUND_ID)
        self.alarm_script_var.set("")
        self._refresh_alarm_sound_values()

    def _test_alarm_sound(self) -> None:
        sound_id = self._resolve_alarm_sound_id()
        path = self._sound_path_for_id(sound_id)
        self._play_sound_for_duration(path, 4)
        self.alarm_status_var.set(self._t("Odtworzono dźwięk alarmu.", "Played alarm sound."))

    def _start_stopwatch(self) -> None:
        if self.stopwatch_running:
            return
        self.stopwatch_start = datetime.now().astimezone()
        self.stopwatch_running = True
        self._tick_stopwatch()

    def _stop_stopwatch(self) -> None:
        if not self.stopwatch_running or self.stopwatch_start is None:
            return
        now = datetime.now().astimezone()
        self.stopwatch_elapsed += now - self.stopwatch_start
        self.stopwatch_running = False
        self.stopwatch_start = None
        if self.stopwatch_after_id is not None:
            try:
                self.after_cancel(self.stopwatch_after_id)
            except tk.TclError:
                pass
            self.stopwatch_after_id = None
        self.stopwatch_time_var.set(format_hhmmss_ms(self.stopwatch_elapsed.total_seconds()))

    def _reset_stopwatch(self) -> None:
        self.stopwatch_running = False
        self.stopwatch_start = None
        self.stopwatch_elapsed = timedelta(0)
        if self.stopwatch_after_id is not None:
            try:
                self.after_cancel(self.stopwatch_after_id)
            except tk.TclError:
                pass
            self.stopwatch_after_id = None
        self.stopwatch_time_var.set("00:00:00.000")

    def _tick_stopwatch(self) -> None:
        if not self.stopwatch_running or self.stopwatch_start is None:
            self.stopwatch_after_id = None
            return
        now = datetime.now().astimezone()
        elapsed = self.stopwatch_elapsed + (now - self.stopwatch_start)
        self.stopwatch_time_var.set(format_hhmmss_ms(elapsed.total_seconds()))
        self.stopwatch_after_id = self.after(50, self._tick_stopwatch)

    def _start_timer(self) -> None:
        try:
            minutes = int(self.timer_minutes_var.get().strip() or 0)
            seconds = int(self.timer_seconds_var.get().strip() or 0)
        except ValueError:
            self.alarm_status_var.set(self._t("Niepoprawne minuty/sekundy timera.", "Invalid timer minutes/seconds."))
            return
        total = max(0, minutes * 60 + seconds)
        if self.timer_remaining_seconds > 0 and total == self.timer_input_total:
            total = self.timer_remaining_seconds
        repeat_enabled = bool(self.timer_repeat_var.get())
        repeat_minutes_raw = self.timer_repeat_minutes_var.get().strip()
        repeat_minutes = 0
        if repeat_enabled and repeat_minutes_raw:
            try:
                repeat_minutes = max(1, int(repeat_minutes_raw))
            except ValueError:
                self.alarm_status_var.set(self._t("Niepoprawny interwał powtarzania timera.", "Invalid timer repeat interval."))
                return
        if repeat_enabled and repeat_minutes:
            total = repeat_minutes * 60
        if total <= 0:
            self.alarm_status_var.set(self._t("Ustaw czas timera większy od zera.", "Set timer greater than zero."))
            return
        self.timer_input_total = total
        self.timer_remaining_seconds = total
        self.timer_end_time = datetime.now().astimezone() + timedelta(seconds=total)
        self.timer_running = True
        self.timer_repeat_interval = total if repeat_enabled else 0

    def _stop_timer(self) -> None:
        if not self.timer_running or self.timer_end_time is None:
            return
        now = datetime.now().astimezone()
        remaining = int((self.timer_end_time - now).total_seconds())
        self.timer_remaining_seconds = max(0, remaining)
        self.timer_running = False
        self.timer_end_time = None
        self.timer_repeat_interval = 0
        self.timer_pause_start = None
        self.timer_remaining_var.set(format_hhmmss(self.timer_remaining_seconds))

    def _reset_timer(self) -> None:
        self.timer_running = False
        self.timer_end_time = None
        self.timer_remaining_seconds = 0
        self.timer_input_total = 0
        self.timer_repeat_interval = 0
        self.timer_pause_start = None
        self.timer_remaining_var.set("00:00:00")

    def _refresh_alarms_and_timers(self, now_system: datetime) -> None:
        active = self._handle_alarm_timer_pause(now_system)
        self._update_stopwatch(now_system)
        if not active:
            return
        self._check_alarms(now_system)
        self._update_timer(now_system)

    def _handle_alarm_timer_pause(self, now_system: datetime) -> bool:
        if self.alarms_paused_var.get():
            if self.timer_running and self.timer_pause_start is None:
                self.timer_pause_start = now_system
            return False
        if self.timer_pause_start is not None:
            if self.timer_running and self.timer_end_time is not None:
                self.timer_end_time += (now_system - self.timer_pause_start)
            self.timer_pause_start = None
        return True

    def _check_alarms(self, now_system: datetime) -> None:
        for alarm in list(self.alarms):
            if not bool(alarm.get("enabled", True)):
                continue
            zone_id = str(alarm.get("zone", ""))
            zone = self.engine.zone(zone_id)
            if zone is None and not self.engine.has_fallback(zone_id):
                continue
            now_zone = self.engine.convert(now_system, zone_id)
            time_raw = str(alarm.get("time", ""))
            parsed_time = parse_alarm_time(time_raw)
            if not parsed_time:
                continue
            date_raw = str(alarm.get("date", "")).strip()
            target_date = parse_alarm_date(date_raw) if date_raw else None
            repeat_daily = not bool(target_date)
            if target_date and now_zone.date() != target_date:
                continue
            hour, minute, second = parsed_time
            if now_zone.hour == hour and now_zone.minute == minute and now_zone.second == second:
                alarm_id = int(alarm.get("id", 0))
                key = f"{now_zone.date()} {hour:02d}:{minute:02d}:{second:02d}"
                if self.alarm_last_fire.get(alarm_id) == key:
                    continue
                self.alarm_last_fire[alarm_id] = key
                duration = int(alarm.get("duration", 20) or 20)
                sound_id = str(alarm.get("sound_id", DEFAULT_ALARM_SOUND_ID))
                path = self._sound_path_for_id(sound_id)
                self._play_sound_for_duration(path, duration)
                script_path = str(alarm.get("script", "")).strip()
                if script_path:
                    self._run_alarm_script(script_path)
                self.alarm_status_var.set(self._t(f"Alarm: {alarm.get('label', '')}", f"Alarm: {alarm.get('label', '')}"))
                if target_date and not repeat_daily:
                    alarm["enabled"] = False
                    self._refresh_alarm_tree()
                    self._mark_settings_dirty()

    def _update_stopwatch(self, now_system: datetime) -> None:
        if self.stopwatch_running and self.stopwatch_after_id is not None:
            return
        if self.stopwatch_running and self.stopwatch_start is not None:
            elapsed = self.stopwatch_elapsed + (now_system - self.stopwatch_start)
            self.stopwatch_time_var.set(format_hhmmss_ms(elapsed.total_seconds()))
        else:
            self.stopwatch_time_var.set(format_hhmmss_ms(self.stopwatch_elapsed.total_seconds()))

    def _update_timer(self, now_system: datetime) -> None:
        if not self.timer_running or self.timer_end_time is None:
            if self.timer_remaining_seconds:
                self.timer_remaining_var.set(format_hhmmss(self.timer_remaining_seconds))
            return
        remaining = int((self.timer_end_time - now_system).total_seconds())
        if remaining <= 0:
            self._play_sound_for_duration(SOUND_TIMER, 4)
            script_path = self.timer_script_var.get().strip()
            if script_path:
                self._run_alarm_script(script_path)
            if self.timer_repeat_interval > 0:
                self.timer_end_time = now_system + timedelta(seconds=self.timer_repeat_interval)
                self.timer_remaining_seconds = self.timer_repeat_interval
                self.timer_remaining_var.set(format_hhmmss(self.timer_repeat_interval))
                self.alarm_status_var.set(self._t("Timer powtórzony.", "Timer repeated."))
                return
            self.timer_running = False
            self.timer_end_time = None
            self.timer_remaining_seconds = 0
            self.timer_remaining_var.set("00:00:00")
            self.alarm_status_var.set(self._t("Timer zakończony.", "Timer finished."))
            return
        self.timer_remaining_seconds = remaining
        self.timer_remaining_var.set(format_hhmmss(remaining))

    def _play_sound(self, path: Path | None) -> None:
        if self.sound_muted:
            return
        self._stop_ticking()
        try:
            if path and path.is_file():
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except RuntimeError:
            pass
        if self.tile_ticking_var.get() and self.any_session_active:
            self.after(1200, self._schedule_ticking)

    def _play_sound_for_duration(self, path: Path | None, duration_seconds: int) -> None:
        if self.sound_muted:
            return
        duration_seconds = max(1, int(duration_seconds))
        self._stop_ticking()
        try:
            if path and path.is_file():
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            else:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except RuntimeError:
            return

        self.after(duration_seconds * 1000, self._stop_sound)

    def _stop_sound(self) -> None:
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except RuntimeError:
            pass
        if self.tile_ticking_var.get() and self.any_session_active and not self.sound_muted:
            self._schedule_ticking()

    def _sound_path_for_id(self, sound_id: str) -> Path | None:
        for sound in ALARM_SOUND_LIBRARY:
            if sound.get("id") == sound_id:
                return SOUNDS_DIR / sound.get("file", "")
        return SOUND_ALARM

    def _sound_display_for_id(self, sound_id: str) -> str:
        for sound in ALARM_SOUND_LIBRARY:
            if sound.get("id") == sound_id:
                label = sound.get("en") if self.language_var.get() == "en" else sound.get("pl")
                style = sound.get("style_en") if self.language_var.get() == "en" else sound.get("style_pl")
                return f"{label} · {style}"
        return sound_id

    def _refresh_alarm_sound_values(self) -> None:
        if not hasattr(self, "alarm_sound_combo"):
            return
        values: list[str] = []
        self._alarm_sound_lookup: dict[str, str] = {}
        for sound in ALARM_SOUND_LIBRARY:
            label = sound.get("en") if self.language_var.get() == "en" else sound.get("pl")
            style = sound.get("style_en") if self.language_var.get() == "en" else sound.get("style_pl")
            display = f"{label} · {style}"
            values.append(display)
            self._alarm_sound_lookup[display] = sound.get("id", "")
        self.alarm_sound_combo.configure(values=values)
        current_id = self.alarm_sound_id_var.get() or DEFAULT_ALARM_SOUND_ID
        self.alarm_sound_id_var.set(current_id)
        self.alarm_sound_display_var.set(self._sound_display_for_id(current_id))

    def _resolve_alarm_sound_id(self) -> str:
        display = self.alarm_sound_display_var.get().strip()
        lookup = getattr(self, "_alarm_sound_lookup", {})
        if display in lookup:
            sound_id = lookup[display]
        else:
            sound_id = self.alarm_sound_id_var.get() or DEFAULT_ALARM_SOUND_ID
        if not sound_id:
            sound_id = DEFAULT_ALARM_SOUND_ID
        self.alarm_sound_id_var.set(sound_id)
        return sound_id

    def _on_alarm_sound_select(self, _event: tk.Event | None = None) -> None:
        sound_id = self._resolve_alarm_sound_id()
        self.alarm_sound_id_var.set(sound_id)

    def _browse_alarm_script(self) -> None:
        path = filedialog.askopenfilename(
            title=self._t("Wybierz skrypt alarmu", "Select alarm script"),
            filetypes=[
                ("PowerShell", "*.ps1"),
                ("Shell", "*.sh;*.bash"),
                ("Python", "*.py"),
                ("Batch", "*.bat;*.cmd"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.alarm_script_var.set(path)

    def _browse_timer_script(self) -> None:
        path = filedialog.askopenfilename(
            title=self._t("Wybierz skrypt timera", "Select timer script"),
            filetypes=[
                ("PowerShell", "*.ps1"),
                ("Shell", "*.sh;*.bash"),
                ("Python", "*.py"),
                ("Batch", "*.bat;*.cmd"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.timer_script_var.set(path)

    def _run_alarm_script(self, script_path: str) -> None:
        if not script_path:
            return
        path = Path(script_path).expanduser()
        if not path.is_file():
            self.alarm_status_var.set(self._t(f"Nie znaleziono skryptu: {script_path}", f"Script not found: {script_path}"))
            return
        suffix = path.suffix.lower()
        try:
            if suffix == ".ps1":
                subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(path)])
            elif suffix in (".bat", ".cmd"):
                subprocess.Popen(["cmd", "/c", str(path)])
            elif suffix == ".py":
                subprocess.Popen([sys.executable, str(path)])
            elif suffix in (".sh", ".bash"):
                subprocess.Popen(["bash", str(path)])
            else:
                subprocess.Popen([str(path)], shell=True)
        except OSError:
            self.alarm_status_var.set(self._t("Nie udało się uruchomić skryptu alarmu.", "Failed to run alarm script."))

    def _update_alarm_date_hint(self, _event: tk.Event | None = None) -> None:
        return

    def _handle_session_sound(self, card: TileCard, active: bool, session_open: datetime | None, session_close: datetime | None) -> None:
        if session_open is None or session_close is None:
            self.session_state_cache[card.card_id] = False
            return
        prev = self.session_state_cache.get(card.card_id)
        self.session_state_cache[card.card_id] = active
        if prev is None:
            return
        if not self.session_sound_enabled_var.get():
            return
        if active and not prev:
            self._play_sound(SOUND_SESSION_START)
        elif not active and prev:
            self._play_sound(SOUND_SESSION_END)

    def _update_ticking_state(self, any_active: bool) -> None:
        self.any_session_active = any_active
        if not self.tile_ticking_var.get() or self.sound_muted or not SOUND_TICKING.is_file():
            self._stop_ticking(stop_sound=True)
            return
        if any_active:
            self._schedule_ticking()
        else:
            self._stop_ticking(stop_sound=True)

    def _schedule_ticking(self) -> None:
        if self.ticking_after_id is not None:
            return
        now = datetime.now().astimezone()
        delay = max(5, 1000 - int(now.microsecond / 1000))
        generation = self.ticking_generation
        self.ticking_after_id = self.after(delay, lambda gen=generation: self._tick_once(gen))

    def _tick_once(self, generation: int) -> None:
        if generation != self.ticking_generation:
            return
        self.ticking_after_id = None
        if not self.tile_ticking_var.get() or self.sound_muted or not self.any_session_active:
            return
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
            winsound.PlaySound(str(SOUND_TICKING), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except RuntimeError:
            return
        self._schedule_ticking()

    def _stop_ticking(self, stop_sound: bool = False) -> None:
        self.ticking_generation += 1
        if self.ticking_after_id is not None:
            try:
                self.after_cancel(self.ticking_after_id)
            except tk.TclError:
                pass
            self.ticking_after_id = None
        if stop_sound:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except RuntimeError:
                pass

    def _on_tile_ticking_toggle(self) -> None:
        self._update_ticking_state(self.any_session_active)
        self._mark_settings_dirty()

    def _configure_phase_tags(self) -> None:
        mappings = (
            ("night", str(self.phase_bg.get("night", "#1B2747"))),
            ("morning", str(self.phase_bg.get("morning", "#1E5D7A"))),
            ("day", str(self.phase_bg.get("day", "#2262A5"))),
            ("afternoon", str(self.phase_bg.get("afternoon", "#2F7A5E"))),
            ("evening", str(self.phase_bg.get("evening", "#5B4D8A"))),
        )
        for tree_name in ("world_tree", "search_tree"):
            tree = getattr(self, tree_name, None)
            if tree is None:
                continue
            for tag_name, color in mappings:
                tree.tag_configure(tag_name, background=color)

    def _paint_gradient_background(self, canvas: tk.Canvas, top_color: str, bottom_color: str, tag: str = "bg_gradient") -> None:
        canvas.delete(tag)
        width = max(2, canvas.winfo_width())
        height = max(2, canvas.winfo_height())
        steps = max(20, min(height // 2, 180))
        for idx in range(steps):
            y0 = int(height * idx / steps)
            y1 = int(height * (idx + 1) / steps)
            color = blend_hex(top_color, bottom_color, idx / max(1, steps - 1))
            canvas.create_rectangle(0, y0, width, y1, fill=color, outline="", tags=tag)
        stripe = blend_hex(top_color, "#FFFFFF", 0.15)
        for i in range(-width, width, 120):
            canvas.create_line(i, 0, i + width, height, fill=stripe, width=16, stipple="gray25", tags=tag)
        canvas.tag_lower(tag)

    def _load_settings_file(self) -> dict:
        try:
            if SETTINGS_FILE.is_file():
                payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            if LEGACY_SETTINGS_FILE.is_file():
                payload = json.loads(LEGACY_SETTINGS_FILE.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
                    SETTINGS_FILE.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
                    return payload
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    def _load_alarms_from_settings(self) -> None:
        raw = self._loaded_settings.get("alarms")
        if not isinstance(raw, list):
            return
        for row in raw:
            if not isinstance(row, dict):
                continue
            zone_raw = str(row.get("zone", "")).strip()
            if not zone_raw:
                continue
            zone_id = zone_raw if zone_raw in self.engine.zone_set else self.engine.resolve_zone_hint(zone_raw, allow_online=False)
            if not zone_id or zone_id not in self.engine.zone_set:
                continue
            time_raw = str(row.get("time", "")).strip()
            if parse_alarm_time(time_raw) is None:
                continue
            date_raw = str(row.get("date", "")).strip()
            if date_raw and parse_alarm_date(date_raw) is None:
                date_raw = ""
            duration_raw = row.get("duration", 20)
            try:
                duration = max(1, int(duration_raw))
            except (TypeError, ValueError):
                duration = 20
            sound_id = str(row.get("sound_id", DEFAULT_ALARM_SOUND_ID)).strip() or DEFAULT_ALARM_SOUND_ID
            if not any(sound.get("id") == sound_id for sound in ALARM_SOUND_LIBRARY):
                sound_id = DEFAULT_ALARM_SOUND_ID
            script_path = str(row.get("script", "")).strip()
            repeat_daily = not bool(date_raw)
            label = str(row.get("label", "")).strip() or self._t("Alarm", "Alarm")
            enabled = bool(row.get("enabled", True))
            alarm_id = row.get("id")
            if not isinstance(alarm_id, int) or alarm_id <= 0:
                alarm_id = self.next_alarm_id
                self.next_alarm_id += 1
            else:
                self.next_alarm_id = max(self.next_alarm_id, alarm_id + 1)
            self.alarms.append(
                {
                    "id": int(alarm_id),
                    "label": label,
                    "zone": zone_id,
                    "time": time_raw,
                    "date": date_raw,
                    "enabled": enabled,
                    "repeat_daily": repeat_daily,
                    "duration": duration,
                    "sound_id": sound_id,
                    "script": script_path,
                }
            )

    def _snapshot_tiles(self) -> list[dict[str, str | int]]:
        snapshot: list[dict[str, str | int]] = []
        for card in self.tile_cards:
            snapshot.append(
                {
                    "zone_id": card.zone_id,
                    "title": card.title,
                    "session_key": card.session_key,
                    "x": int(card.x),
                    "y": int(card.y),
                    "width": int(card.width),
                    "height": int(card.height),
                }
            )
        return snapshot

    def _load_tiles_from_settings(self) -> bool:
        raw_tiles = self._loaded_settings.get("tiles")
        if not isinstance(raw_tiles, list):
            return False
        loaded_any = False
        for row in raw_tiles:
            if not isinstance(row, dict):
                continue
            zone_id = str(row.get("zone_id", "")).strip()
            if not zone_id:
                continue
            title = str(row.get("title", zone_id)).strip() or zone_id
            session_key = str(row.get("session_key", "Brak sesji")).strip() or "Brak sesji"
            if session_key not in SESSION_PRESETS:
                session_key = "Brak sesji"
            raw_x = row.get("x")
            raw_y = row.get("y")
            tile_x = int(raw_x) if isinstance(raw_x, int) else None
            tile_y = int(raw_y) if isinstance(raw_y, int) else None
            tile_w = int(row.get("width", TILE_DEFAULT_WIDTH)) if isinstance(row.get("width"), int) else TILE_DEFAULT_WIDTH
            tile_h = int(row.get("height", TILE_DEFAULT_HEIGHT)) if isinstance(row.get("height"), int) else TILE_DEFAULT_HEIGHT
            before_count = len(self.tile_cards)
            self._add_tile(
                zone_id,
                title,
                session_key,
                silent=True,
                tile_x=tile_x,
                tile_y=tile_y,
                tile_w=tile_w,
                tile_h=tile_h,
            )
            if len(self.tile_cards) > before_count:
                loaded_any = True
        return loaded_any

    def _collect_settings_payload(self) -> dict:
        return {
            "base_mode": self.base_mode_var.get(),
            "manual_base_zone": self.manual_base_zone_var.get().strip(),
            "manual_zone_resolved": self.manual_zone_resolved,
            "language": self.language_var.get(),
            "theme": self.theme_name,
            "auto_night": bool(self.auto_night_var.get()),
            "auto_night_start": normalize_hhmm(self.auto_night_start_var.get(), AUTO_NIGHT_DEFAULT_START),
            "auto_night_stop": normalize_hhmm(self.auto_night_stop_var.get(), AUTO_NIGHT_DEFAULT_STOP),
            "search_query": self.search_query_var.get(),
            "converter_input": self.converter_input_var.get(),
            "converter_source_zone": self.converter_source_zone_var.get(),
            "converter_target_mode": self.converter_target_mode_var.get(),
            "converter_target_zone": self.converter_target_zone_var.get(),
            "converter_live": bool(self.converter_live_var.get()),
            "compare_a": self.compare_a_var.get(),
            "compare_b": self.compare_b_var.get(),
            "compare_reference_time": self.compare_reference_time_var.get(),
            "compare_reference_zone": self.compare_reference_zone_var.get(),
            "tile_query": self.tile_query_var.get(),
            "tile_session": self._resolve_session_key(self.tile_session_var.get()),
            "tiles": self._snapshot_tiles(),
            "session_sound_enabled": bool(self.session_sound_enabled_var.get()),
            "tile_ticking": bool(self.tile_ticking_var.get()),
            "sound_muted": bool(self.sound_muted),
            "alarm_sound_default": self.alarm_sound_id_var.get(),
            "alarms": self.alarms,
            "alarms_paused": bool(self.alarms_paused_var.get()),
            "minimize_on_start": bool(self.minimize_on_start_var.get()),
            "fullscreen_auto_layout": bool(self.fullscreen_auto_layout_var.get()),
            "timer_minutes": self.timer_minutes_var.get(),
            "timer_seconds": self.timer_seconds_var.get(),
            "timer_repeat": bool(self.timer_repeat_var.get()),
            "timer_repeat_minutes": self.timer_repeat_minutes_var.get(),
            "timer_script": self.timer_script_var.get(),
            "window_geometry": self.winfo_geometry(),
        }

    def _save_settings_file(self) -> None:
        payload = self._collect_settings_payload()
        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
            self.settings_dirty = False
        except OSError:
            pass

    def _mark_settings_dirty(self, *_: object) -> None:
        self.settings_dirty = True
        if self.settings_save_after_id is not None:
            self.after_cancel(self.settings_save_after_id)
        self.settings_save_after_id = self.after(900, self._flush_settings_save)

    def _flush_settings_save(self) -> None:
        self.settings_save_after_id = None
        if self.settings_dirty:
            self._save_settings_file()

    def _wire_setting_traces(self) -> None:
        tracked_vars: list[tk.Variable] = [
            self.base_mode_var,
            self.manual_base_zone_var,
            self.search_query_var,
            self.converter_input_var,
            self.converter_source_zone_var,
            self.converter_target_mode_var,
            self.converter_target_zone_var,
            self.converter_live_var,
            self.compare_a_var,
            self.compare_b_var,
            self.compare_reference_time_var,
            self.compare_reference_zone_var,
            self.tile_query_var,
            self.tile_session_var,
            self.theme_var,
            self.auto_night_var,
            self.auto_night_start_var,
            self.auto_night_stop_var,
            self.session_sound_enabled_var,
            self.tile_ticking_var,
            self.alarm_sound_id_var,
            self.alarms_paused_var,
            self.minimize_on_start_var,
            self.fullscreen_auto_layout_var,
            self.timer_minutes_var,
            self.timer_seconds_var,
            self.timer_repeat_var,
            self.timer_repeat_minutes_var,
            self.timer_script_var,
            self.language_var,
        ]
        self._trace_tokens: list[tuple[tk.Variable, str]] = []
        for variable in tracked_vars:
            token = variable.trace_add("write", self._mark_settings_dirty)
            self._trace_tokens.append((variable, token))

    def _on_app_close(self) -> None:
        self._flush_settings_save()
        if self.tile_focus_window is not None:
            self.tile_focus_window.destroy()
            self.tile_focus_window = None
        self._stop_ticking()
        self._stop_tray_icon()
        self.destroy()

    def _autostart_command(self) -> str:
        if getattr(sys, "frozen", False):
            return f'start "" "{Path(sys.executable)}"'
        return f'start "" "{Path(sys.executable)}" "{Path(__file__).resolve()}"'

    def _refresh_autostart_buttons(self) -> None:
        if not hasattr(self, "autostart_add_btn") or not hasattr(self, "autostart_remove_btn"):
            return
        enabled = AUTOSTART_FILE.is_file()
        self.autostart_add_btn.configure(state=("disabled" if enabled else "normal"))
        self.autostart_remove_btn.configure(state=("normal" if enabled else "disabled"))

    def _refresh_tray_support_buttons(self) -> None:
        if not hasattr(self, "tray_install_btn"):
            return
        if self.tray_install_in_progress:
            self.tray_install_btn.configure(text=self._t("⏳ Instalacja...", "⏳ Installing..."), state="disabled")
            return
        if PYSTRAY_AVAILABLE:
            self.tray_install_btn.configure(text=self._t("✅ Tray gotowy", "✅ Tray ready"), state="disabled")
        else:
            self.tray_install_btn.configure(text=self._t("🧩 Zainstaluj tray", "🧩 Install tray"), state="normal")

    def _load_tray_modules(self) -> bool:
        global pystray, Image, PYSTRAY_AVAILABLE
        try:
            pystray = importlib.import_module("pystray")
            Image = importlib.import_module("PIL.Image")
            PYSTRAY_AVAILABLE = True
            return True
        except Exception:
            pystray = None
            Image = None
            PYSTRAY_AVAILABLE = False
            return False

    def _install_tray_support(self, pending_minimize: bool = False) -> None:
        if PYSTRAY_AVAILABLE or self.tray_install_in_progress:
            return
        self.tray_install_in_progress = True
        self.pending_tray_minimize = pending_minimize
        self._refresh_tray_support_buttons()

        def _worker() -> None:
            commands = [
                [sys.executable, "-m", "pip", "install", "pystray", "Pillow"],
                ["py", "-m", "pip", "install", "pystray", "Pillow"],
                ["python", "-m", "pip", "install", "pystray", "Pillow"],
            ]
            ok = False
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    ok = result.returncode == 0
                    if ok:
                        break
                except OSError:
                    ok = False

            def _finish() -> None:
                self.tray_install_in_progress = False
                if ok and self._load_tray_modules():
                    messagebox.showinfo(self._t("Tray", "Tray"), self._t("Zainstalowano obsługę traya.", "Tray support installed."))
                else:
                    messagebox.showerror(self._t("Tray", "Tray"), self._t("Nie udało się zainstalować traya.", "Failed to install tray support."))
                self._refresh_tray_support_buttons()
                if self.pending_tray_minimize and PYSTRAY_AVAILABLE:
                    self.pending_tray_minimize = False
                    self._minimize_to_tray()
                else:
                    self.pending_tray_minimize = False

            self.after(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _add_to_autostart(self) -> None:
        try:
            STARTUP_DIR.mkdir(parents=True, exist_ok=True)
            AUTOSTART_FILE.write_text(f"@echo off\n{self._autostart_command()}\n", encoding="utf-8")
            messagebox.showinfo(self._t("Autostart", "Autostart"), self._t("Dodano do autostartu Windows.", "Added to Windows autostart."))
        except OSError:
            messagebox.showerror(self._t("Autostart", "Autostart"), self._t("Nie udało się dodać do autostartu.", "Failed to add to autostart."))
        self._refresh_autostart_buttons()

    def _remove_from_autostart(self) -> None:
        try:
            if AUTOSTART_FILE.is_file():
                AUTOSTART_FILE.unlink()
            messagebox.showinfo(self._t("Autostart", "Autostart"), self._t("Usunięto z autostartu Windows.", "Removed from Windows autostart."))
        except OSError:
            messagebox.showerror(self._t("Autostart", "Autostart"), self._t("Nie udało się usunąć z autostartu.", "Failed to remove from autostart."))
        self._refresh_autostart_buttons()

    def _build_tray_menu(self) -> object | None:
        if not PYSTRAY_AVAILABLE or pystray is None:
            return None
        mute_label = lambda _item=None: self._t("Wycisz", "Mute") if not self.sound_muted else self._t("Włącz dźwięk", "Unmute")
        return pystray.Menu(
            pystray.MenuItem(self._t("Otwórz", "Open"), self._tray_open, default=True),
            pystray.MenuItem(mute_label, self._tray_toggle_mute),
            pystray.MenuItem(self._t("Zamknij", "Close"), self._tray_quit),
        )

    def _update_tray_menu(self) -> None:
        if self.tray_icon is None or not PYSTRAY_AVAILABLE or pystray is None:
            return
        self.tray_icon.menu = self._build_tray_menu()
        try:
            self.tray_icon.update_menu()
        except Exception:
            pass

    def _ensure_tray_icon(self, prompt_install: bool = True) -> bool:
        if self.tray_icon is not None:
            return True
        if not PYSTRAY_AVAILABLE or pystray is None or Image is None:
            if prompt_install:
                should_install = messagebox.askyesno(
                    self._t("Tray", "Tray"),
                    self._t(
                        "Brak biblioteki pystray/Pillow. Zainstalować teraz?",
                        "Missing pystray/Pillow. Install now?",
                    ),
                )
                if should_install:
                    self._install_tray_support(pending_minimize=True)
            else:
                messagebox.showwarning(
                    self._t("Tray", "Tray"),
                    self._t(
                        "Brak biblioteki pystray/Pillow. Zainstaluj pystray i Pillow, aby użyć traya.",
                        "Missing pystray/Pillow. Install pystray and Pillow to enable the tray icon.",
                    ),
                )
            return False
        try:
            if TRAY_ICON_FILE.is_file():
                image = Image.open(TRAY_ICON_FILE)
            else:
                image = Image.new("RGB", (64, 64), "#1B2747")
        except Exception:
            image = Image.new("RGB", (64, 64), "#1B2747")
        menu = self._build_tray_menu()
        self.tray_icon = pystray.Icon("WorldTimeSpecialist", image, APP_TITLE, menu)
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
        return True

    def _stop_tray_icon(self) -> None:
        if self.tray_icon is None:
            return
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.tray_icon = None

    def _tray_open(self, _icon: object | None = None, _item: object | None = None) -> None:
        self.after(0, self._restore_from_tray)

    def _tray_quit(self, _icon: object | None = None, _item: object | None = None) -> None:
        self.after(0, self._on_app_close)

    def _tray_toggle_mute(self, _icon: object | None = None, _item: object | None = None) -> None:
        self.after(0, lambda: self._set_muted(not self.sound_muted))

    def _minimize_to_tray(self) -> None:
        if not self._ensure_tray_icon(prompt_install=True):
            return
        self.withdraw()

    def _restore_from_tray(self) -> None:
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
            self.state("zoomed")
        except tk.TclError:
            pass

    def _set_muted(self, muted: bool) -> None:
        self.sound_muted = bool(muted)
        if self.sound_muted:
            try:
                winsound.PlaySound(None, winsound.SND_ASYNC)
            except RuntimeError:
                pass
            self._stop_ticking(stop_sound=True)
        else:
            if self.tile_ticking_var.get() and self.any_session_active:
                self._schedule_ticking()
        self._update_tray_menu()
        self._mark_settings_dirty()

    def _auto_minimize_if_autostart(self) -> None:
        if not AUTOSTART_FILE.is_file():
            return
        if not self.minimize_on_start_var.get():
            return
        if not PYSTRAY_AVAILABLE:
            return
        self._minimize_to_tray()

    def _on_alarms_pause_toggle(self) -> None:
        self._set_alarm_pause_status_text(mark_dirty=True)

    def _set_alarm_pause_status_text(self, mark_dirty: bool) -> None:
        if self.alarms_paused_var.get():
            self.alarm_status_var.set(self._t("Alarmy i timery wstrzymane.", "Alarms and timers paused."))
        else:
            self.alarm_status_var.set(self._t("Alarmy i timery aktywne.", "Alarms and timers active."))
        if mark_dirty:
            self._mark_settings_dirty()

    def _on_fullscreen_layout_toggle(self) -> None:
        if self.fullscreen_enabled and self.focus_tiles_canvas is not None:
            self.focus_auto_layout = bool(self.fullscreen_auto_layout_var.get())
            self._layout_focus_tiles()
        self._mark_settings_dirty()

    def _on_search_enter(self, event: tk.Event) -> None:
        self._run_search()

    def _on_compare_enter(self, event: tk.Event) -> None:
        self._run_comparison()

    def _on_tile_enter(self, event: tk.Event) -> None:
        self._add_tile_from_query()

    def _on_manual_base_enter(self, event: tk.Event) -> None:
        self._apply_manual_base()

    def _on_escape(self, event: tk.Event) -> None:
        if self.fullscreen_enabled or self.tile_focus_window is not None:
            self._toggle_fullscreen(force_off=True)

    def _get_base_zone_id(self) -> str:
        return self.manual_zone_resolved if self.base_mode_var.get() == "manual" else self.system_zone_key

    def _get_base_now(self, now_system: datetime) -> datetime:
        base_zone_id = self._get_base_zone_id()
        return self.engine.convert(now_system, base_zone_id)

    def _on_base_mode_change(self) -> None:
        mode = self.base_mode_var.get()
        manual_state = "normal" if mode == "manual" else "disabled"
        self.manual_base_entry.configure(state=manual_state)
        self.manual_base_button.configure(state=manual_state)

        if mode == "auto":
            self.base_notice_var.set(self._t(f"Tryb AUTO: baza = {self.system_zone_key}", f"AUTO mode: base = {self.system_zone_key}"))
        else:
            self.base_notice_var.set(self._t(f"Tryb MANUAL: baza = {self.manual_zone_resolved}", f"MANUAL mode: base = {self.manual_zone_resolved}"))

        self._run_converter(silent=True)
        self._mark_settings_dirty()

    def _apply_manual_base(self) -> None:
        query = self.manual_base_zone_var.get().strip()
        resolved = self.engine.resolve_zone_hint(query, allow_online=True)
        if not resolved:
            self.base_notice_var.set(
                self._t(
                    f"Nie znaleziono strefy dla: {query}. Pozostaje: {self.manual_zone_resolved}",
                    f"Could not find zone for: {query}. Keeping: {self.manual_zone_resolved}",
                )
            )
            return

        self.manual_zone_resolved = resolved
        self.manual_base_zone_var.set(resolved)
        self.base_mode_var.set("manual")
        self.base_notice_var.set(self._t(f"Tryb MANUAL: baza ustawiona na {resolved}", f"MANUAL mode: base set to {resolved}"))
        self._on_base_mode_change()
        self._mark_settings_dirty()

    def _set_selected_as_base_zone(self) -> None:
        selected = self.search_tree.selection()
        if not selected:
            self.base_notice_var.set(self._t("Najpierw wybierz wynik w tabeli wyszukiwania.", "Select a row in search results first."))
            return
        zone_id = selected[0]
        self.manual_zone_resolved = zone_id
        self.manual_base_zone_var.set(zone_id)
        self.base_mode_var.set("manual")
        self.base_notice_var.set(self._t(f"Tryb MANUAL: baza ustawiona na {zone_id}", f"MANUAL mode: base set to {zone_id}"))
        self._on_base_mode_change()
        self._mark_settings_dirty()

    def _source_for_zone(self, zone_id: str) -> str:
        return self.search_source_by_zone.get(zone_id, "-")

    def _resolve_zone_input(self, hint: str, allow_online: bool = True) -> tuple[str | None, str | None, timezone | None, str]:
        raw = hint.strip()
        if not raw:
            return None, None, None, ""

        offset_minutes = parse_utc_offset_minutes(raw)
        if offset_minutes is not None:
            offset_delta = timedelta(minutes=offset_minutes)
            offset_name = format_offset(offset_delta)
            fixed_zone = timezone(offset_delta, name=offset_name)
            context = self.engine.offset_hint_context(offset_minutes)
            return offset_name, None, fixed_zone, context

        zone_id = self.city_zone_lookup.get(raw) if hasattr(self, "city_zone_lookup") else None
        if not zone_id and hasattr(self, "city_zone_lookup"):
            raw_cf = raw.casefold()
            for key, value in self.city_zone_lookup.items():
                if key.casefold() == raw_cf:
                    zone_id = value
                    break
        if not zone_id:
            zone_id = self.engine.resolve_zone_hint(raw, allow_online=allow_online)
        if not zone_id:
            return None, None, None, ""
        if self.engine.zone(zone_id) is None and not self.engine.has_fallback(zone_id):
            return None, None, None, ""
        return zone_id, zone_id, None, ""

    def _run_search(self) -> None:
        query = self.search_query_var.get().strip()
        if query:
            self.status_var.set(self._t("Szukanie lokalne + online...", "Searching local + online..."))
            self.update_idletasks()
        self.search_results = self.engine.search(query, include_online=True) if query else []
        self.search_source_by_zone = {result.zone_id: result.source for result in self.search_results}

        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        if not query:
            self.status_var.set(self._t("Wpisz kraj, kod ISO (np. PL) albo miasto (np. Warszawa, Tokio). Możesz wpisać też EST/CET/JST lub UTC+1.", "Enter a country, ISO code (e.g., PL) or city (e.g., Warsaw, Tokyo). You can also type EST/CET/JST or UTC+1."))
            self.detail_header_var.set(self._t("Wybierz lokalizację z listy wyników.", "Select a location from the results list."))
            self.detail_body_var.set(self._t("Tutaj zobaczysz szczegóły strefy i relacje do czasu bazowego.", "Zone details and relation to base time will appear here."))
            self.search_source_full_var.set(self._t("Pełny opis źródła dopasowania pojawi się tutaj.", "Full match-source description will appear here."))
            return

        if not self.search_results:
            self.status_var.set(self._t(f"Brak wyników dla: {query}", f"No results for: {query}"))
            self.detail_header_var.set(self._t("Brak danych", "No data"))
            self.detail_body_var.set(self._t("Spróbuj innej nazwy lub dopisz region, np. Warszawa, Poland.", "Try another name or add a region, e.g., Warsaw, Poland."))
            self.search_source_full_var.set(self._t("Brak źródła do pokazania.", "No source to display."))
            return

        self.status_var.set(self._t(f"Znaleziono {len(self.search_results)} stref (pokazano do limitu 80).", f"Found {len(self.search_results)} zones (up to 80 shown)."))

        for result in self.search_results:
            self.search_tree.insert("", "end", iid=result.zone_id, values=(result.zone_id, "", "", "", "", "", compact_source_label(result.source)))

        first = self.search_results[0].zone_id
        self.search_tree.selection_set(first)
        self.search_tree.focus(first)
        self.selected_zone = first
        self._update_detail_panel(first)
        self._mark_settings_dirty()

    def _on_search_select(self, event: tk.Event) -> None:
        selected = self.search_tree.selection()
        if not selected:
            return
        zone_id = selected[0]
        self.selected_zone = zone_id
        self._update_detail_panel(zone_id)

    def _update_detail_panel(self, zone_id: str, base_now: datetime | None = None) -> None:
        zone = self.engine.zone(zone_id)
        if zone is None and not self.engine.has_fallback(zone_id):
            return

        now_system = datetime.now().astimezone()
        if base_now is None:
            base_now = self._get_base_now(now_system)

        now_target = self.engine.convert(base_now, zone_id)
        target_offset = now_target.utcoffset() or timedelta(0)
        base_offset = base_now.utcoffset() or timedelta(0)
        diff = target_offset - base_offset

        phase_key = day_phase(now_target.hour)
        phase_txt = phase_label(phase_key, self.language_var.get())
        dst_text = self._t("TAK", "YES") if is_dst_active(now_target) else self._t("NIE", "NO")
        full_source = self._source_for_zone(zone_id)
        self.search_source_full_var.set(wrap_source_text(full_source, width=90))

        base_zone_id = self._get_base_zone_id()
        self.detail_header_var.set(self._t(f"Szczegóły: {zone_id}", f"Details: {zone_id}"))
        detail_chunks = [
            self._t("Czas bazowy:\n", "Base time:\n"),
            f"- {base_now:%Y-%m-%d %H:%M:%S} ({base_zone_id}, {base_now.tzname()})\n\n",
            self._t("Czas w wybranej strefie:\n", "Time in selected zone:\n"),
            f"- {now_target:%Y-%m-%d %H:%M:%S}\n",
            self._t(f"- skrót: {now_target.tzname() or '-'}\n", f"- abbreviation: {now_target.tzname() or '-'}\n"),
            f"- offset: {format_offset(now_target.utcoffset())}\n",
            self._t(f"- różnica do bazowego: {format_diff(diff)}\n", f"- difference to base: {format_diff(diff)}\n"),
            self._t(f"- DST aktywne: {dst_text}\n", f"- DST active: {dst_text}\n"),
            self._t(
                f"- profil sezonowy: {seasonal_offset_description(zone_id, now_target.year, language='pl')}\n",
                f"- seasonal profile: {seasonal_offset_description(zone_id, now_target.year, language='en')}\n",
            ),
            self._t(f"- pora dnia: {phase_txt}\n\n", f"- day phase: {phase_txt}\n\n"),
            self._t("Źródło dopasowania:\n", "Match source:\n"),
            f"{wrap_source_text(full_source, width=62)}",
        ]
        self.detail_body_var.set("".join(detail_chunks))

    def _on_converter_mode_change(self) -> None:
        mode = self.converter_target_mode_var.get()
        self.converter_target_entry.configure(state="normal" if mode == "manual" else "disabled")
        self._run_converter(silent=True)

    def _on_converter_field_change(self, event: tk.Event) -> None:
        if self.converter_live_var.get():
            self._run_converter(silent=True)

    def _run_converter(self, silent: bool = False) -> None:
        source_zone_hint = self.converter_source_zone_var.get().strip()
        source_zone_label, source_zone_id, source_fixed_zone, source_context = self._resolve_zone_input(source_zone_hint, allow_online=True)
        if not source_zone_label or (source_zone_id is None and source_fixed_zone is None):
            if not silent:
                self.converter_result_var.set("-")
                self.converter_detail_var.set(self._t(f"Nie znaleziono strefy źródła: {source_zone_hint}", f"Source zone not found: {source_zone_hint}"))
            return

        if source_zone_id and source_zone_hint and source_zone_hint.casefold() != source_zone_id.casefold():
            if source_zone_hint not in TZ_ABBREVIATION_MAP:
                self.converter_source_zone_var.set(source_zone_id)

        if source_zone_id is not None:
            now_source = self.engine.convert(datetime.now().astimezone(), source_zone_id)
        else:
            now_source = datetime.now().astimezone(source_fixed_zone)
        source_dt = parse_time_input(self.converter_input_var.get(), now_source)
        if source_dt is None:
            if not silent:
                self.converter_result_var.set("-")
                self.converter_detail_var.set(self._t("Niepoprawny format czasu. Przykłady: 10:15, 2026-03-24 10:15, 10:15 PM", "Invalid time format. Examples: 10:15, 2026-03-24 10:15, 10:15 PM"))
            return

        target_context = ""
        if self.converter_target_mode_var.get() == "base":
            target_zone_id = self._get_base_zone_id()
            if self.engine.zone(target_zone_id) is None and not self.engine.has_fallback(target_zone_id):
                return
            target_label = target_zone_id
        else:
            target_hint = self.converter_target_zone_var.get().strip()
            target_label, target_zone_id, target_fixed_zone, target_context = self._resolve_zone_input(target_hint, allow_online=True) if target_hint else (None, None, None, "")
            if not target_label or (target_zone_id is None and target_fixed_zone is None):
                if not silent:
                    self.converter_result_var.set("-")
                    self.converter_detail_var.set(self._t(f"Nie znaleziono strefy docelowej: {target_hint}", f"Target zone not found: {target_hint}"))
                return
            target_zone_id = target_zone_id or target_label
            target_label = target_zone_id
            if target_zone_id and target_hint and target_hint.casefold() != target_zone_id.casefold():
                if target_hint not in TZ_ABBREVIATION_MAP:
                    self.converter_target_zone_var.set(target_zone_id)

        if self.converter_target_mode_var.get() == "base":
            target_dt = self.engine.convert(source_dt, target_zone_id)
        else:
            if target_zone_id is not None:
                target_dt = self.engine.convert(source_dt, target_zone_id)
            else:
                target_dt = source_dt.astimezone(target_fixed_zone)

        source_offset = source_dt.utcoffset() or timedelta(0)
        target_offset = target_dt.utcoffset() or timedelta(0)
        diff = target_offset - source_offset

        target_phase_key = day_phase(target_dt.hour)
        target_phase = phase_label(target_phase_key, self.language_var.get())
        self.converter_result_var.set(f"{target_dt:%Y-%m-%d %H:%M:%S}")
        detail = (
            f"{source_dt:%Y-%m-%d %H:%M:%S} ({source_zone_label}, {source_dt.tzname()}) -> "
            f"{target_dt:%Y-%m-%d %H:%M:%S} ({target_label}, {target_dt.tzname()})\n"
            + self._t(
                f"Offsety: {format_offset(source_dt.utcoffset())} -> {format_offset(target_dt.utcoffset())} | różnica: {format_diff(diff)}\n",
                f"Offsets: {format_offset(source_dt.utcoffset())} -> {format_offset(target_dt.utcoffset())} | difference: {format_diff(diff)}\n",
            )
            + self._t(f"Pora dnia docelowo: {target_phase}", f"Target day phase: {target_phase}")
        )
        if source_context:
            detail += f"\n{source_context}"
        if target_context:
            detail += self._t(f"\nCel: {target_context}", f"\nTarget: {target_context}")
        self.converter_detail_var.set(detail)

    def _run_comparison(self) -> None:
        query_a = self.compare_a_var.get().strip()
        query_b = self.compare_b_var.get().strip()

        if not query_a or not query_b:
            self.compare_status_var.set(self._t("Podaj obie lokalizacje.", "Provide both locations."))
            self.compare_result_var.set("")
            return

        zone_a = self.engine.resolve_zone_hint(query_a, allow_online=True)
        zone_b = self.engine.resolve_zone_hint(query_b, allow_online=True)

        if not zone_a or not zone_b:
            self.compare_status_var.set(self._t("Nie udało się rozpoznać jednej z lokalizacji.", "Could not resolve one of the locations."))
            self.compare_result_var.set("")
            return

        reference_time_raw = self.compare_reference_time_var.get().strip()
        reference_zone_raw = self.compare_reference_zone_var.get().strip()

        now_system = datetime.now().astimezone()
        base_now = self._get_base_now(now_system)
        reference_dt = base_now
        reference_desc = f"{base_now:%Y-%m-%d %H:%M:%S} ({self._get_base_zone_id()}, {base_now.tzname()})"
        reference_context = ""

        if reference_time_raw or reference_zone_raw:
            reference_hint = reference_zone_raw or self._get_base_zone_id()
            ref_label, ref_zone_id, ref_fixed_zone, reference_context = self._resolve_zone_input(reference_hint, allow_online=True)
            if not ref_label or (ref_zone_id is None and ref_fixed_zone is None):
                self.compare_status_var.set(self._t(f"Nie znaleziono strefy referencyjnej: {reference_hint}", f"Reference zone not found: {reference_hint}"))
                self.compare_result_var.set("")
                return

            if ref_zone_id is not None:
                now_reference_zone = self.engine.convert(datetime.now().astimezone(), ref_zone_id)
            else:
                now_reference_zone = datetime.now().astimezone(ref_fixed_zone)
            parsed_reference = parse_time_input(reference_time_raw, now_reference_zone) if reference_time_raw else now_reference_zone.replace(second=0, microsecond=0)
            if parsed_reference is None:
                self.compare_status_var.set(self._t("Niepoprawny format czasu referencyjnego.", "Invalid reference time format."))
                self.compare_result_var.set("")
                return
            reference_dt = parsed_reference
            reference_desc = f"{reference_dt:%Y-%m-%d %H:%M:%S} ({ref_label}, {reference_dt.tzname()})"

        if self.engine.zone(zone_a) is None and not self.engine.has_fallback(zone_a):
            self.compare_status_var.set(self._t("Nie udało się załadować jednej z rozpoznanych stref.", "Could not load one of the resolved zones."))
            self.compare_result_var.set("")
            return
        if self.engine.zone(zone_b) is None and not self.engine.has_fallback(zone_b):
            self.compare_status_var.set(self._t("Nie udało się załadować jednej z rozpoznanych stref.", "Could not load one of the resolved zones."))
            self.compare_result_var.set("")
            return

        dt_a = self.engine.convert(reference_dt, zone_a)
        dt_b = self.engine.convert(reference_dt, zone_b)

        phase_a = phase_label(day_phase(dt_a.hour), self.language_var.get())
        phase_b = phase_label(day_phase(dt_b.hour), self.language_var.get())

        offset_a = dt_a.utcoffset() or timedelta(0)
        offset_b = dt_b.utcoffset() or timedelta(0)
        delta_b_minus_a = offset_b - offset_a

        self.compare_status_var.set(self._t(f"Porównanie {zone_a} vs {zone_b}", f"Comparison {zone_a} vs {zone_b}"))
        details = (
            self._t(f"Punkt odniesienia: {reference_desc}\n", f"Reference point: {reference_desc}\n")
            + f"A ({query_a} -> {zone_a}): {dt_a:%Y-%m-%d %H:%M:%S} | {dt_a.tzname()} | {format_offset(dt_a.utcoffset())} | {phase_a}\n"
            + f"B ({query_b} -> {zone_b}): {dt_b:%Y-%m-%d %H:%M:%S} | {dt_b.tzname()} | {format_offset(dt_b.utcoffset())} | {phase_b}\n\n"
            + (
                comparison_summary(query_a, query_b, delta_b_minus_a)
                if self.language_var.get() == "pl"
                else comparison_summary_en(query_a, query_b, delta_b_minus_a)
            )
        )
        if reference_context:
            details += f"\n\n{reference_context}"
        self.compare_result_var.set(details)

    def _add_default_tiles(self) -> None:
        self._clear_tiles(silent=True)
        if hasattr(self, "tiles_canvas"):
            try:
                self.tiles_canvas.update_idletasks()
            except tk.TclError:
                pass
        preferred_order = [
            "JPX (Tokio 09:00-15:00)",
            "XETRA (Frankfurt 09:00-17:30)",
            "LSE (Londyn 08:00-16:30)",
            "NASDAQ (Nowy Jork 09:30-16:00)",
            "NYSE (Nowy Jork 09:30-16:00)",
        ]
        session_keys = [key for key in preferred_order if key in SESSION_PRESETS]
        for key, preset in SESSION_PRESETS.items():
            if not preset:
                continue
            if key not in session_keys:
                session_keys.append(key)
        if not session_keys:
            return

        margin = TILE_MARGIN
        gap = 12
        canvas_width = max(self.tiles_canvas.winfo_width(), 1200)
        available = max(200, canvas_width - margin * 2 - gap * (len(session_keys) - 1))
        tile_w = max(TILE_MIN_WIDTH, min(TILE_DEFAULT_WIDTH, int(available / max(1, len(session_keys)))))
        tile_h = max(TILE_MIN_HEIGHT, int(tile_w * 1.25))
        x = margin
        y = margin
        for session_key in session_keys:
            preset = SESSION_PRESETS.get(session_key)
            if not preset:
                continue
            zone_id = str(preset.get("zone", ""))
            if not zone_id:
                continue
            self._add_tile(zone_id, self._session_display_name(session_key), session_key, silent=True, tile_x=x, tile_y=y, tile_w=tile_w, tile_h=tile_h)
            x += tile_w + gap
        self.tile_status_var.set(self._t("Wczytano domyślne kafelki sesji tradingowych.", "Loaded default trading-session tiles."))
        self._mark_settings_dirty()

    def _add_base_tile(self) -> None:
        zone_id = self._get_base_zone_id()
        session_key = self._resolve_session_key(self.tile_session_var.get())
        self._add_tile(zone_id, self._t(f"Bazowy: {zone_id}", f"Base: {zone_id}"), session_key)

    def _add_tile_from_query(self) -> None:
        query = self.tile_query_var.get().strip()
        if not query:
            self.tile_status_var.set(self._t("Wpisz miasto lub strefę, aby dodać kafelek.", "Type a city or zone to add a tile."))
            return
        zone_id = self.city_zone_lookup.get(query)
        if not zone_id:
            zone_id = self.engine.resolve_zone_hint(query, allow_online=True)
        if not zone_id:
            self.tile_status_var.set(self._t(f"Nie znaleziono strefy dla: {query}", f"Zone not found for: {query}"))
            return
        title = query
        self._add_tile(zone_id, title, "Brak sesji")
        self.tile_query_var.set("")

    def _add_tile_from_session(self) -> None:
        session_key = self._resolve_session_key(self.tile_session_var.get())
        preset = SESSION_PRESETS.get(session_key)
        if not preset:
            self.tile_status_var.set(self._t("Wybierz sesję giełdową do dodania.", "Select a trading session to add."))
            return
        zone_id = str(preset.get("zone", "")).strip()
        if not zone_id:
            self.tile_status_var.set(self._t("Brak strefy dla wybranej sesji.", "Selected session has no zone."))
            return
        self._add_tile(zone_id, self._session_display_name(session_key), session_key)

    def _align_tiles_to_grid(self) -> None:
        if not self.tile_cards:
            return
        self.tiles_grid_layout = True
        self._layout_tiles()
        self._sync_focus_tiles()
        self._mark_settings_dirty()
        self.tile_status_var.set(self._t("Wyrównano kafelki do siatki.", "Aligned tiles to grid."))

    def _next_tile_position(self, width: int, height: int) -> tuple[int, int]:
        margin = TILE_MARGIN
        gap = 12
        canvas_width = max(self.tiles_canvas.winfo_width(), 1200)
        cols = max(1, int((canvas_width - margin * 2 + gap) // (width + gap)))
        idx = len(self.tile_cards)
        row = idx // cols
        col = idx % cols
        return margin + col * (width + gap), margin + row * (height + gap)

    def _add_tile(
        self,
        zone_id: str,
        title: str,
        session_key: str,
        silent: bool = False,
        tile_x: int | None = None,
        tile_y: int | None = None,
        tile_w: int = TILE_DEFAULT_WIDTH,
        tile_h: int = TILE_DEFAULT_HEIGHT,
    ) -> None:
        zone = self.engine.zone(zone_id)
        if zone is None and not self.engine.has_fallback(zone_id):
            self.tile_status_var.set(self._t(f"Brak dostępu do strefy: {zone_id}", f"No access to zone: {zone_id}"))
            return

        card_id = self.next_tile_id
        self.next_tile_id += 1

        frame = ttk.Frame(self.tiles_canvas, style="Card.TFrame", padding=10)
        frame.configure(cursor="fleur")
        frame.grid_propagate(False)
        gloss = tk.Canvas(
            frame,
            highlightthickness=0,
            bd=0,
            bg=str(self.theme_palette.get("card_bg", "#17223C")),
        )
        gloss.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            gloss.tk.call("lower", gloss._w)
        except tk.TclError:
            pass

        title_label = ttk.Label(frame, text=title, style="CardTitle.TLabel")
        title_label.grid(row=0, column=0, sticky="w")
        title_label.configure(cursor="fleur")

        remove_btn = ttk.Button(frame, text=self._t("🗑 Usuń", "🗑 Remove"), style="Action.TButton", command=lambda cid=card_id: self._remove_tile(cid))
        remove_btn.grid(row=0, column=1, sticky="e")

        canvas = tk.Canvas(
            frame,
            width=220,
            height=220,
            bg=str(self.theme_palette.get("card_bg", "#17223C")),
            highlightthickness=0,
        )
        canvas.grid(row=1, column=0, columnspan=2, pady=(8, 8))

        digital_label = ttk.Label(frame, text="--:--:--", style="Clock.TLabel", font=("Consolas", 24, "bold"))
        digital_label.grid(row=2, column=0, columnspan=2, sticky="w")

        meta_label = ttk.Label(frame, text=zone_id, style="SmallInfo.TLabel", wraplength=320, justify="left")
        meta_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        phase_label = tk.Label(
            frame,
            text="",
            bg=str(self.phase_bg.get("night", "#1E2B4A")),
            fg=str(self.theme_palette.get("heading", "#F8FAFC")),
            font=("Bahnschrift", 10, "bold"),
            padx=8,
            pady=3,
        )
        phase_label.grid(row=4, column=0, sticky="w", pady=(8, 0))

        session_label = tk.Label(
            frame,
            text="",
            bg=str(self.theme_palette.get("session_inactive", "#603030")),
            fg=str(self.theme_palette.get("heading", "#F8FAFC")),
            font=("Bahnschrift", 10),
            padx=8,
            pady=3,
        )
        session_label.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        resize_handle = tk.Label(
            frame,
            text="◢",
            bg=str(self.theme_palette.get("card_bg", "#17223C")),
            fg=str(self.theme_palette.get("muted", "#C4D8F2")),
            font=("Bahnschrift", 12, "bold"),
            cursor="size_nw_se",
            padx=4,
            pady=0,
        )
        resize_handle.place(x=0, y=0)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)
        frame.rowconfigure(1, weight=1)

        width = max(TILE_MIN_WIDTH, int(tile_w))
        height = max(TILE_MIN_HEIGHT, int(tile_h))
        if tile_x is None or tile_y is None:
            tile_x, tile_y = self._next_tile_position(width, height)
        window_id = self.tiles_canvas.create_window(
            int(tile_x),
            int(tile_y),
            window=frame,
            anchor="nw",
            width=width,
            height=height,
            tags=("tile_card",),
        )

        card = TileCard(
            card_id=card_id,
            frame=frame,
            canvas=canvas,
            title_label=title_label,
            digital_label=digital_label,
            meta_label=meta_label,
            phase_label=phase_label,
            session_label=session_label,
            zone_id=zone_id,
            title=title,
            session_key=session_key if session_key in SESSION_PRESETS else "Brak sesji",
            x=int(tile_x),
            y=int(tile_y),
            width=width,
            height=height,
            window_id=window_id,
            resize_handle=resize_handle,
            gloss_canvas=gloss,
        )
        self.tile_cards.append(card)

        self._bind_tile_interactions(card)
        self._apply_tile_geometry(card)
        self._layout_tiles()
        if not silent:
            self.tile_status_var.set(self._t(f"Dodano kafelek: {title} ({zone_id})", f"Added tile: {title} ({zone_id})"))
        self._sync_focus_tiles()
        self._mark_settings_dirty()

    def _remove_tile(self, card_id: int) -> None:
        kept: list[TileCard] = []
        for card in self.tile_cards:
            if card.card_id == card_id:
                if card.window_id is not None:
                    self.tiles_canvas.delete(card.window_id)
                card.frame.destroy()
                self.session_state_cache.pop(card.card_id, None)
            else:
                kept.append(card)
        self.tile_cards = kept
        self._layout_tiles()
        self._sync_focus_tiles()
        self._mark_settings_dirty()

    def _clear_tiles(self, silent: bool = False) -> None:
        for card in self.tile_cards:
            if card.window_id is not None:
                self.tiles_canvas.delete(card.window_id)
            card.frame.destroy()
        self.tile_cards = []
        self.session_state_cache.clear()
        if not silent:
            self.tile_status_var.set(self._t("Wyczyszczono wszystkie kafelki.", "Cleared all tiles."))
        self._sync_focus_tiles()
        self._mark_settings_dirty()

    def _apply_tile_geometry(self, card: TileCard, canvas: tk.Canvas | None = None, min_width: int | None = None, min_height: int | None = None) -> None:
        target_canvas = canvas or self.tiles_canvas
        min_w = TILE_MIN_WIDTH if min_width is None else int(min_width)
        min_h = TILE_MIN_HEIGHT if min_height is None else int(min_height)
        card.width = max(min_w, int(card.width))
        card.height = max(min_h, int(card.height))
        card.x = max(TILE_MARGIN, int(card.x))
        card.y = max(TILE_MARGIN, int(card.y))

        available_w = max(90, card.width - 36)
        reserved = 260 if card.height >= 360 else int(card.height * 0.5)
        available_h = max(70, card.height - reserved)
        clock_size = min(available_w, available_h)
        if clock_size < 70:
            clock_size = available_w if available_w < available_h else available_h

        card_bg = str(self.theme_palette.get("card_bg", "#17223C"))
        card.canvas.configure(width=clock_size, height=clock_size, bg=card_bg)
        digital_size = max(12, min(30, int(card.width / 10)))
        card.digital_label.configure(font=("Consolas", digital_size, "bold"))
        title_size = max(10, min(16, int(card.width / 22)))
        card.title_label.configure(font=("Bahnschrift", title_size, "bold"))
        card.meta_label.configure(wraplength=max(120, card.width - 22), justify="left")
        card.title_label.configure(wraplength=max(120, card.width - 150), justify="left")
        card.phase_label.configure(anchor="w", wraplength=max(120, card.width - 22), justify="left")
        card.session_label.configure(anchor="w", wraplength=max(120, card.width - 22), justify="left")
        if card.gloss_canvas is not None:
            card.gloss_canvas.configure(width=card.width, height=card.height)
            self._draw_tile_gloss(card.gloss_canvas, card.width, card.height)
        if card.resize_handle is not None:
            card.resize_handle.configure(bg=card_bg, fg=str(self.theme_palette.get("muted", "#C4D8F2")), text="◢")
            card.resize_handle.place(x=max(0, card.width - 22), y=max(0, card.height - 20))
        if card.window_id is not None and target_canvas is not None:
            target_canvas.coords(card.window_id, card.x, card.y)
            target_canvas.itemconfig(card.window_id, width=card.width, height=card.height)
        card.frame.configure(width=card.width, height=card.height)

    def _draw_tile_gloss(self, canvas: tk.Canvas, width: int, height: int) -> None:
        canvas.delete("all")
        bg = str(self.theme_palette.get("card_bg", "#17223C"))
        dark = blend_hex(bg, "#000000", 0.22)
        light = blend_hex(bg, "#FFFFFF", 0.22)
        border = blend_hex(bg, "#FFFFFF", 0.28)
        canvas.create_rectangle(1, 1, width - 2, height - 2, fill=bg, outline=border, width=2)

        steps = 18
        for i in range(steps):
            ratio = i / max(1, steps - 1)
            color = blend_hex(light, dark, ratio)
            y0 = int((height - 4) * i / steps) + 2
            y1 = int((height - 4) * (i + 1) / steps) + 2
            canvas.create_rectangle(3, y0, width - 3, y1, fill=color, outline="")

        glow_color = blend_hex("#FFFFFF", bg, 0.86)
        canvas.create_oval(
            -width * 0.15,
            -height * 0.35,
            width * 0.85,
            height * 0.65,
            fill=glow_color,
            outline="",
        )

        gloss_height = max(46, int(height * 0.24))
        gloss_steps = 12
        for i in range(gloss_steps):
            ratio = i / max(1, gloss_steps - 1)
            color = blend_hex("#FFFFFF", bg, 0.82 + ratio * 0.12)
            y0 = 5 + int((gloss_height - 8) * i / gloss_steps)
            y1 = 5 + int((gloss_height - 8) * (i + 1) / gloss_steps)
            canvas.create_rectangle(6, y0, width - 6, y1, fill=color, outline="")

        stripe = blend_hex("#FFFFFF", bg, 0.6)
        canvas.create_line(-width * 0.3, height * 0.12, width * 1.25, height * 0.48, fill=stripe, width=10, stipple="gray25")
        shadow = blend_hex(bg, "#000000", 0.35)
        canvas.create_rectangle(6, height - 22, width - 6, height - 6, fill=shadow, outline="")

    def _update_tiles_scrollregion(self) -> None:
        self._update_canvas_scrollregion(self.tiles_canvas, self.tile_cards)

    def _update_canvas_scrollregion(self, canvas: tk.Canvas, cards: list[TileCard]) -> None:
        max_x = canvas.winfo_width()
        max_y = canvas.winfo_height()
        for card in cards:
            max_x = max(max_x, card.x + card.width + 12)
            max_y = max(max_y, card.y + card.height + 12)
        canvas.configure(scrollregion=(0, 0, max_x, max_y))

    def _bind_mousewheel_to_canvas(self, widget: tk.Widget, canvas: tk.Canvas) -> None:
        def _on_mousewheel(event: tk.Event) -> None:
            delta = int(-1 * (event.delta / 120)) if event.delta else 0
            if delta:
                canvas.yview_scroll(delta, "units")

        widget.bind("<Enter>", lambda _e: self.bind_all("<MouseWheel>", _on_mousewheel), add="+")
        widget.bind("<Leave>", lambda _e: self.unbind_all("<MouseWheel>"), add="+")

    def _compute_grid_layout(self, count: int, canvas: tk.Canvas) -> tuple[int, int, int, int]:
        if count <= 0:
            return 1, 1, TILE_DEFAULT_WIDTH, TILE_DEFAULT_HEIGHT
        width = max(320, canvas.winfo_width())
        height = max(320, canvas.winfo_height())
        margin = TILE_MARGIN
        gap = 12
        aspect = 1.25
        best: tuple[tuple[float, int], int, int, float, float] | None = None
        for cols in range(1, count + 1):
            rows = int(math.ceil(count / cols))
            max_w_by_width = (width - margin * 2 - gap * (cols - 1)) / cols
            max_h_by_height = (height - margin * 2 - gap * (rows - 1)) / rows
            if max_w_by_width <= 0 or max_h_by_height <= 0:
                continue
            tile_w = min(max_w_by_width, max_h_by_height / aspect)
            tile_h = tile_w * aspect
            if tile_w <= 0 or tile_h <= 0:
                continue
            empty = rows * cols - count
            score = (tile_w, -empty)
            if best is None or score > best[0]:
                best = (score, cols, rows, tile_w, tile_h)
        if best is None:
            return 1, count, TILE_DEFAULT_WIDTH, TILE_DEFAULT_HEIGHT
        _, cols, rows, tile_w, tile_h = best
        tile_w = max(80, int(tile_w))
        tile_h = max(120, int(tile_h))
        return cols, rows, tile_w, tile_h

    def _apply_grid_layout(self, cards: list[TileCard], canvas: tk.Canvas) -> None:
        if not cards:
            return
        gap = 12
        margin = TILE_MARGIN
        cols, _rows, tile_w, tile_h = self._compute_grid_layout(len(cards), canvas)
        for idx, card in enumerate(cards):
            row = idx // cols
            col = idx % cols
            card.x = margin + col * (tile_w + gap)
            card.y = margin + row * (tile_h + gap)
            card.width = tile_w
            card.height = tile_h
            self._apply_tile_geometry(card, canvas=canvas, min_width=tile_w, min_height=tile_h)
        self._update_canvas_scrollregion(canvas, cards)

    def _layout_tiles(self) -> None:
        if self.tiles_grid_layout:
            self._apply_grid_layout(self.tile_cards, self.tiles_canvas)
        else:
            for card in self.tile_cards:
                self._apply_tile_geometry(card)
            self._update_tiles_scrollregion()

    def _bind_tile_interactions(self, card: TileCard) -> None:
        drag_widgets = [card.frame, card.title_label, card.digital_label]
        for widget in drag_widgets:
            widget.bind("<ButtonPress-1>", lambda event, cid=card.card_id: self._start_tile_drag(cid, event))
            widget.bind("<B1-Motion>", lambda event, cid=card.card_id: self._drag_tile(cid, event))
            widget.bind("<ButtonRelease-1>", lambda event, cid=card.card_id: self._stop_tile_drag(cid, event))
            self._bind_mousewheel_to_canvas(widget, self.tiles_canvas)
        if card.resize_handle is not None:
            card.resize_handle.bind("<ButtonPress-1>", lambda event, cid=card.card_id: self._start_tile_resize(cid, event))
            card.resize_handle.bind("<B1-Motion>", lambda event, cid=card.card_id: self._resize_tile(cid, event))
            card.resize_handle.bind("<ButtonRelease-1>", lambda event, cid=card.card_id: self._stop_tile_resize(cid, event))
            self._bind_mousewheel_to_canvas(card.resize_handle, self.tiles_canvas)

    def _bind_focus_tile_interactions(self, card: TileCard) -> None:
        drag_widgets = [card.frame, card.title_label, card.digital_label]
        for widget in drag_widgets:
            widget.bind("<ButtonPress-1>", lambda event, cid=card.card_id: self._start_focus_tile_drag(cid, event))
            widget.bind("<B1-Motion>", lambda event, cid=card.card_id: self._drag_focus_tile(cid, event))
            widget.bind("<ButtonRelease-1>", lambda event, cid=card.card_id: self._stop_focus_tile_drag(cid, event))
            if self.focus_tiles_canvas is not None:
                self._bind_mousewheel_to_canvas(widget, self.focus_tiles_canvas)
        if card.resize_handle is not None:
            card.resize_handle.bind("<ButtonPress-1>", lambda event, cid=card.card_id: self._start_focus_tile_resize(cid, event))
            card.resize_handle.bind("<B1-Motion>", lambda event, cid=card.card_id: self._resize_focus_tile(cid, event))
            card.resize_handle.bind("<ButtonRelease-1>", lambda event, cid=card.card_id: self._stop_focus_tile_resize(cid, event))
            if self.focus_tiles_canvas is not None:
                self._bind_mousewheel_to_canvas(card.resize_handle, self.focus_tiles_canvas)

    def _get_focus_tile_by_id(self, card_id: int) -> TileCard | None:
        for card in self.focus_tile_cards:
            if card.card_id == card_id:
                return card
        return None

    def _canvas_pointer(self, event: tk.Event, canvas: tk.Canvas | None = None) -> tuple[int, int]:
        target = canvas or self.tiles_canvas
        local_x = event.x_root - target.winfo_rootx()
        local_y = event.y_root - target.winfo_rooty()
        return int(target.canvasx(local_x)), int(target.canvasy(local_y))

    def _get_tile_by_id(self, card_id: int) -> TileCard | None:
        for card in self.tile_cards:
            if card.card_id == card_id:
                return card
        return None

    def _start_tile_drag(self, card_id: int, event: tk.Event) -> None:
        card = self._get_tile_by_id(card_id)
        if card is None:
            return
        self.tiles_grid_layout = False
        pointer_x, pointer_y = self._canvas_pointer(event)
        self.tile_drag_state = {
            "card_id": card.card_id,
            "start_x": pointer_x,
            "start_y": pointer_y,
            "orig_x": card.x,
            "orig_y": card.y,
        }

    def _snap_tile_position(self, card: TileCard, x: int, y: int, canvas: tk.Canvas | None = None, cards: list[TileCard] | None = None) -> tuple[int, int]:
        target_canvas = canvas or self.tiles_canvas
        candidates = cards or self.tile_cards
        snap = TILE_SNAP_THRESHOLD
        target_x = max(TILE_MARGIN, int(x))
        target_y = max(TILE_MARGIN, int(y))
        scroll_values = str(target_canvas.cget("scrollregion")).split()
        scroll_right = int(float(scroll_values[2])) if len(scroll_values) == 4 else 0
        scroll_bottom = int(float(scroll_values[3])) if len(scroll_values) == 4 else 0
        visible_right = int(target_canvas.canvasx(target_canvas.winfo_width()))
        visible_bottom = int(target_canvas.canvasy(target_canvas.winfo_height()))
        canvas_right = max(card.width + TILE_MARGIN, scroll_right, visible_right) - TILE_MARGIN
        canvas_bottom = max(card.height + TILE_MARGIN, scroll_bottom, visible_bottom) - TILE_MARGIN
        if abs(target_x - TILE_MARGIN) <= snap:
            target_x = TILE_MARGIN
        if abs(target_y - TILE_MARGIN) <= snap:
            target_y = TILE_MARGIN
        if abs((target_x + card.width) - canvas_right) <= snap:
            target_x = canvas_right - card.width
        if abs((target_y + card.height) - canvas_bottom) <= snap:
            target_y = canvas_bottom - card.height

        for other in candidates:
            if other.card_id == card.card_id:
                continue
            left, right = other.x, other.x + other.width
            top, bottom = other.y, other.y + other.height
            if abs(target_x - left) <= snap:
                target_x = left
            if abs(target_x - right) <= snap:
                target_x = right
            if abs((target_x + card.width) - left) <= snap:
                target_x = left - card.width
            if abs((target_x + card.width) - right) <= snap:
                target_x = right - card.width
            if abs(target_y - top) <= snap:
                target_y = top
            if abs(target_y - bottom) <= snap:
                target_y = bottom
            if abs((target_y + card.height) - top) <= snap:
                target_y = top - card.height
            if abs((target_y + card.height) - bottom) <= snap:
                target_y = bottom - card.height
        return target_x, target_y

    def _drag_tile(self, card_id: int, event: tk.Event) -> None:
        state = self.tile_drag_state
        if state is None or int(state.get("card_id", -1)) != card_id:
            return
        card = self._get_tile_by_id(card_id)
        if card is None:
            return
        pointer_x, pointer_y = self._canvas_pointer(event)
        raw_x = int(state["orig_x"]) + (pointer_x - int(state["start_x"]))
        raw_y = int(state["orig_y"]) + (pointer_y - int(state["start_y"]))
        card.x, card.y = self._snap_tile_position(card, raw_x, raw_y)
        self._apply_tile_geometry(card)
        self._update_tiles_scrollregion()

    def _stop_tile_drag(self, card_id: int, event: tk.Event) -> None:
        if self.tile_drag_state and int(self.tile_drag_state.get("card_id", -1)) == card_id:
            self.tile_drag_state = None
            self._sync_focus_tiles()
            self._mark_settings_dirty()

    def _start_tile_resize(self, card_id: int, event: tk.Event) -> None:
        card = self._get_tile_by_id(card_id)
        if card is None:
            return
        self.tiles_grid_layout = False
        pointer_x, pointer_y = self._canvas_pointer(event)
        self.tile_resize_state = {
            "card_id": card.card_id,
            "start_x": pointer_x,
            "start_y": pointer_y,
            "orig_w": card.width,
            "orig_h": card.height,
        }

    def _snap_tile_size(self, card: TileCard, width: int, height: int, cards: list[TileCard] | None = None) -> tuple[int, int]:
        candidates = cards or self.tile_cards
        snapped_w = max(TILE_MIN_WIDTH, int(round(width / 10) * 10))
        snapped_h = max(TILE_MIN_HEIGHT, int(round(height / 10) * 10))
        snap = TILE_SNAP_THRESHOLD
        for other in candidates:
            if other.card_id == card.card_id:
                continue
            if abs((card.x + snapped_w) - other.x) <= snap:
                snapped_w = max(TILE_MIN_WIDTH, other.x - card.x)
            if abs((card.x + snapped_w) - (other.x + other.width)) <= snap:
                snapped_w = max(TILE_MIN_WIDTH, (other.x + other.width) - card.x)
            if abs((card.y + snapped_h) - other.y) <= snap:
                snapped_h = max(TILE_MIN_HEIGHT, other.y - card.y)
            if abs((card.y + snapped_h) - (other.y + other.height)) <= snap:
                snapped_h = max(TILE_MIN_HEIGHT, (other.y + other.height) - card.y)
        return snapped_w, snapped_h

    def _resize_tile(self, card_id: int, event: tk.Event) -> None:
        state = self.tile_resize_state
        if state is None or int(state.get("card_id", -1)) != card_id:
            return
        card = self._get_tile_by_id(card_id)
        if card is None:
            return
        pointer_x, pointer_y = self._canvas_pointer(event)
        raw_w = int(state["orig_w"]) + (pointer_x - int(state["start_x"]))
        raw_h = int(state["orig_h"]) + (pointer_y - int(state["start_y"]))
        card.width, card.height = self._snap_tile_size(card, raw_w, raw_h)
        self._apply_tile_geometry(card)
        self._update_tiles_scrollregion()

    def _stop_tile_resize(self, card_id: int, event: tk.Event) -> None:
        if self.tile_resize_state and int(self.tile_resize_state.get("card_id", -1)) == card_id:
            self.tile_resize_state = None
            self._sync_focus_tiles()
            self._mark_settings_dirty()

    def _start_focus_tile_drag(self, card_id: int, event: tk.Event) -> None:
        card = self._get_focus_tile_by_id(card_id)
        if card is None or self.focus_tiles_canvas is None:
            return
        self.focus_auto_layout = False
        pointer_x, pointer_y = self._canvas_pointer(event, canvas=self.focus_tiles_canvas)
        self.tile_drag_state = {
            "card_id": card.card_id,
            "start_x": pointer_x,
            "start_y": pointer_y,
            "orig_x": card.x,
            "orig_y": card.y,
        }

    def _drag_focus_tile(self, card_id: int, event: tk.Event) -> None:
        if self.focus_tiles_canvas is None:
            return
        state = self.tile_drag_state
        if state is None or int(state.get("card_id", -1)) != card_id:
            return
        card = self._get_focus_tile_by_id(card_id)
        if card is None:
            return
        pointer_x, pointer_y = self._canvas_pointer(event, canvas=self.focus_tiles_canvas)
        raw_x = int(state["orig_x"]) + (pointer_x - int(state["start_x"]))
        raw_y = int(state["orig_y"]) + (pointer_y - int(state["start_y"]))
        card.x, card.y = self._snap_tile_position(card, raw_x, raw_y, canvas=self.focus_tiles_canvas, cards=self.focus_tile_cards)
        self._apply_tile_geometry(card, canvas=self.focus_tiles_canvas)
        self._update_canvas_scrollregion(self.focus_tiles_canvas, self.focus_tile_cards)

    def _stop_focus_tile_drag(self, card_id: int, event: tk.Event) -> None:
        if self.tile_drag_state and int(self.tile_drag_state.get("card_id", -1)) == card_id:
            self.tile_drag_state = None
            self._sync_focus_to_main(card_id)
            self._mark_settings_dirty()

    def _start_focus_tile_resize(self, card_id: int, event: tk.Event) -> None:
        card = self._get_focus_tile_by_id(card_id)
        if card is None or self.focus_tiles_canvas is None:
            return
        self.focus_auto_layout = False
        pointer_x, pointer_y = self._canvas_pointer(event, canvas=self.focus_tiles_canvas)
        self.tile_resize_state = {
            "card_id": card.card_id,
            "start_x": pointer_x,
            "start_y": pointer_y,
            "orig_w": card.width,
            "orig_h": card.height,
        }

    def _resize_focus_tile(self, card_id: int, event: tk.Event) -> None:
        if self.focus_tiles_canvas is None:
            return
        state = self.tile_resize_state
        if state is None or int(state.get("card_id", -1)) != card_id:
            return
        card = self._get_focus_tile_by_id(card_id)
        if card is None:
            return
        pointer_x, pointer_y = self._canvas_pointer(event, canvas=self.focus_tiles_canvas)
        raw_w = int(state["orig_w"]) + (pointer_x - int(state["start_x"]))
        raw_h = int(state["orig_h"]) + (pointer_y - int(state["start_y"]))
        card.width, card.height = self._snap_tile_size(card, raw_w, raw_h, cards=self.focus_tile_cards)
        self._apply_tile_geometry(card, canvas=self.focus_tiles_canvas)
        self._update_canvas_scrollregion(self.focus_tiles_canvas, self.focus_tile_cards)

    def _stop_focus_tile_resize(self, card_id: int, event: tk.Event) -> None:
        if self.tile_resize_state and int(self.tile_resize_state.get("card_id", -1)) == card_id:
            self.tile_resize_state = None
            self._sync_focus_to_main(card_id)
            self._mark_settings_dirty()

    def _sync_focus_to_main(self, card_id: int) -> None:
        focus_card = self._get_focus_tile_by_id(card_id)
        if focus_card is None:
            return
        for card in self.tile_cards:
            if card.card_id == focus_card.card_id:
                card.x = focus_card.x
                card.y = focus_card.y
                card.width = focus_card.width
                card.height = focus_card.height
                self._apply_tile_geometry(card)
                self._update_tiles_scrollregion()
                break

    def _toggle_fullscreen(self, force_off: bool = False) -> None:
        if force_off:
            self._close_tile_focus_window()
            return
        if self.fullscreen_enabled:
            self._close_tile_focus_window()
        else:
            self._open_tile_focus_window()

    def _open_tile_focus_window(self) -> None:
        if self.tile_focus_window is not None:
            return
        self.fullscreen_enabled = True
        self.tiles_fullscreen_btn.configure(text=self._t("Zamknij pełny ekran", "Exit fullscreen"))
        self.notebook.select(self.tiles_tab)

        window = tk.Toplevel(self)
        window.title(self._t("Kafelki Czasu - Pełny ekran", "Time Tiles - Fullscreen"))
        window.configure(bg=str(self.theme_palette.get("app_bg", "#0B132B")))
        window.attributes("-fullscreen", True)
        window.bind("<Escape>", lambda _event: self._toggle_fullscreen(force_off=True))
        window.protocol("WM_DELETE_WINDOW", lambda: self._toggle_fullscreen(force_off=True))

        outer = ttk.Frame(window, style="Root.TFrame", padding=10)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        canvas = tk.Canvas(outer, bg=str(self.theme_palette.get("canvas_bottom", "#0E1A33")), highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scroll.set)

        inner = ttk.Frame(canvas, style="Root.TFrame")
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", self._on_focus_inner_configure)
        canvas.bind("<Configure>", self._on_focus_canvas_configure)
        self._bind_mousewheel_to_canvas(canvas, canvas)
        self._bind_mousewheel_to_canvas(inner, canvas)

        self.tile_focus_window = window
        self.focus_tiles_canvas = canvas
        self.focus_tiles_scroll = scroll
        self.focus_tiles_inner = inner
        self.focus_tiles_window = window_id
        self.focus_auto_layout = bool(self.fullscreen_auto_layout_var.get())

        self._build_focus_cards()
        self._layout_focus_tiles()
        self.tile_status_var.set(self._t("Tryb pełnoekranowy kafelków włączony. Wciśnij Esc, aby wyjść.", "Tile fullscreen mode enabled. Press Esc to exit."))

    def _close_tile_focus_window(self) -> None:
        self.fullscreen_enabled = False
        if hasattr(self, "tiles_fullscreen_btn"):
            self.tiles_fullscreen_btn.configure(text=self._t("Pełny ekran kafelków", "Tile fullscreen"))
        if self.tile_focus_window is not None:
            self.tile_focus_window.destroy()
        self.tile_focus_window = None
        self.focus_tiles_canvas = None
        self.focus_tiles_inner = None
        self.focus_tiles_window = None
        self.focus_tiles_scroll = None
        self.focus_tile_cards = []
        self.tile_status_var.set(self._t("Tryb pełnoekranowy kafelków wyłączony.", "Tile fullscreen mode disabled."))

    def _build_focus_cards(self) -> None:
        if self.focus_tiles_canvas is None:
            return
        for card in self.focus_tile_cards:
            if card.window_id is not None:
                self.focus_tiles_canvas.delete(card.window_id)
            card.frame.destroy()
        self.focus_tile_cards = []
        for src in self.tile_cards:
            frame = ttk.Frame(self.focus_tiles_canvas, style="Card.TFrame", padding=12)
            frame.configure(cursor="fleur")
            frame.grid_propagate(False)
            gloss = tk.Canvas(
                frame,
                highlightthickness=0,
                bd=0,
                bg=str(self.theme_palette.get("card_bg", "#17223C")),
            )
            gloss.place(x=0, y=0, relwidth=1, relheight=1)
            try:
                gloss.tk.call("lower", gloss._w)
            except tk.TclError:
                pass

            title_label = ttk.Label(frame, text=src.title, style="CardTitle.TLabel")
            title_label.grid(row=0, column=0, sticky="w")

            canvas = tk.Canvas(
                frame,
                width=300,
                height=300,
                bg=str(self.theme_palette.get("card_bg", "#17223C")),
                highlightthickness=0,
            )
            canvas.grid(row=1, column=0, pady=(8, 8))

            digital_label = ttk.Label(frame, text="--:--:--", style="Clock.TLabel", font=("Consolas", 34, "bold"))
            digital_label.grid(row=2, column=0, sticky="w")

            meta_label = ttk.Label(frame, text=src.zone_id, style="SmallInfo.TLabel", wraplength=520, justify="left")
            meta_label.grid(row=3, column=0, sticky="w", pady=(4, 0))

            phase_label = tk.Label(
                frame,
                text="",
                bg=str(self.phase_bg.get("night", "#1E2B4A")),
                fg=str(self.theme_palette.get("heading", "#F8FAFC")),
                font=("Bahnschrift", 11, "bold"),
                padx=8,
                pady=4,
            )
            phase_label.grid(row=4, column=0, sticky="w", pady=(8, 0))

            session_label = tk.Label(
                frame,
                text="",
                bg=str(self.theme_palette.get("session_inactive", "#603030")),
                fg=str(self.theme_palette.get("heading", "#F8FAFC")),
                font=("Bahnschrift", 11),
                padx=8,
                pady=4,
            )
            session_label.grid(row=5, column=0, sticky="w", pady=(8, 0))

            resize_handle = tk.Label(
                frame,
                text="◢",
                bg=str(self.theme_palette.get("card_bg", "#17223C")),
                fg=str(self.theme_palette.get("muted", "#C4D8F2")),
                font=("Bahnschrift", 12, "bold"),
                cursor="size_nw_se",
                padx=4,
                pady=0,
            )
            resize_handle.place(x=max(0, int(src.width) - 22), y=max(0, int(src.height) - 20))

            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(1, weight=1)

            window_id = self.focus_tiles_canvas.create_window(
                int(src.x),
                int(src.y),
                window=frame,
                anchor="nw",
                width=int(src.width),
                height=int(src.height),
                tags=("focus_tile",),
            )

            focus_card = TileCard(
                card_id=src.card_id,
                frame=frame,
                canvas=canvas,
                title_label=title_label,
                digital_label=digital_label,
                meta_label=meta_label,
                phase_label=phase_label,
                session_label=session_label,
                zone_id=src.zone_id,
                title=src.title,
                session_key=src.session_key,
                x=int(src.x),
                y=int(src.y),
                width=int(src.width),
                height=int(src.height),
                window_id=window_id,
                resize_handle=resize_handle,
                gloss_canvas=gloss,
            )
            self.focus_tile_cards.append(focus_card)
            self._bind_focus_tile_interactions(focus_card)
            self._apply_tile_geometry(focus_card, canvas=self.focus_tiles_canvas)

    def _layout_focus_tiles(self) -> None:
        if self.focus_tiles_canvas is None:
            return
        if self.focus_auto_layout:
            self._apply_grid_layout(self.focus_tile_cards, self.focus_tiles_canvas)
        else:
            for card in self.focus_tile_cards:
                self._apply_tile_geometry(card, canvas=self.focus_tiles_canvas)
            self._update_canvas_scrollregion(self.focus_tiles_canvas, self.focus_tile_cards)

    def _sync_focus_tiles(self) -> None:
        if not self.fullscreen_enabled:
            return
        self._build_focus_cards()
        self._layout_focus_tiles()

    def _on_focus_inner_configure(self, event: tk.Event) -> None:
        if self.focus_tiles_canvas is None:
            return
        self.focus_tiles_canvas.configure(scrollregion=self.focus_tiles_canvas.bbox("all"))

    def _on_focus_canvas_configure(self, event: tk.Event) -> None:
        if self.focus_tiles_canvas is None or self.focus_tiles_window is None:
            return
        self._paint_gradient_background(
            self.focus_tiles_canvas,
            str(self.theme_palette.get("canvas_top", "#1B2747")),
            str(self.theme_palette.get("canvas_bottom", "#0E1A33")),
            tag="focus_bg",
        )
        self.focus_tiles_canvas.itemconfig(self.focus_tiles_window, width=event.width)
        self._layout_focus_tiles()

    def _session_state_for_card(self, card: TileCard, now_tile: datetime) -> tuple[str, bool, datetime | None, datetime | None]:
        preset = SESSION_PRESETS.get(card.session_key)
        if not preset:
            return self._t("Sesja: brak", "Session: none"), False, None, None

        zone_id = preset.get("zone", "")
        open_txt = preset.get("open", "")
        close_txt = preset.get("close", "")
        parsed_open = parse_hhmm(open_txt)
        parsed_close = parse_hhmm(close_txt)
        if not parsed_open or not parsed_close:
            return self._t(f"Sesja: błąd definicji ({card.session_key})", f"Session: invalid definition ({card.session_key})"), False, None, None
        if self.engine.zone(zone_id) is None and not self.engine.has_fallback(zone_id):
            return self._t(f"Sesja: błąd definicji ({card.session_key})", f"Session: invalid definition ({card.session_key})"), False, None, None
        now_session = self.engine.convert(now_tile, zone_id)

        open_h, open_m = parsed_open
        close_h, close_m = parsed_close

        open_dt = now_session.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
        close_dt = now_session.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
        if close_dt <= open_dt:
            close_dt += timedelta(days=1)
            if now_session < open_dt:
                now_session += timedelta(days=1)

        active = open_dt <= now_session < close_dt

        open_tile = open_dt.astimezone(now_tile.tzinfo)
        close_tile = close_dt.astimezone(now_tile.tzinfo)
        status_text = self._t("AKTYWNA", "ACTIVE") if active else self._t("NIEAKTYWNA", "INACTIVE")
        text = f"{self._session_display_name(card.session_key)}: {open_txt}-{close_txt} ({status_text})"
        return text, active, open_tile, close_tile

    def _draw_clock(self, canvas: tk.Canvas, now_dt: datetime, phase_key: str, session_open: datetime | None, session_close: datetime | None, session_active: bool) -> None:
        canvas.delete("all")

        width = int(canvas.cget("width"))
        height = int(canvas.cget("height"))
        cx = width / 2
        cy = height / 2
        radius = min(width, height) / 2 - 10

        phase_face = str(self.phase_bg.get(phase_key, "#1E2B4A"))
        if session_open and session_close:
            face = str(self.theme_palette.get("clock_session_active", "#215B2D")) if session_active else str(self.theme_palette.get("clock_session_inactive", "#5B2A2A"))
        else:
            face = phase_face

        # Gradient tarczy - nowoczesny efekt wizualny.
        for ring in range(16):
            ratio = ring / 15
            ring_radius = radius - ring * 2.0
            if ring_radius <= 2:
                break
            tone = blend_hex(face, str(self.theme_palette.get("canvas_top", "#1B2747")), ratio * 0.65)
            canvas.create_oval(
                cx - ring_radius,
                cy - ring_radius,
                cx + ring_radius,
                cy + ring_radius,
                fill=tone,
                outline="",
            )

        canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill="",
            outline=str(self.theme_palette.get("clock_border", "#A9C9FF")),
            width=2,
        )

        for i in range(12):
            angle = math.radians(i * 30 - 90)
            outer_x = cx + math.cos(angle) * (radius - 4)
            outer_y = cy + math.sin(angle) * (radius - 4)
            inner_x = cx + math.cos(angle) * (radius - (18 if i % 3 == 0 else 12))
            inner_y = cy + math.sin(angle) * (radius - (18 if i % 3 == 0 else 12))
            canvas.create_line(
                inner_x,
                inner_y,
                outer_x,
                outer_y,
                fill=str(self.theme_palette.get("clock_tick", "#DDEBFF")),
                width=2 if i % 3 == 0 else 1,
            )

        if session_open and session_close:
            start_hour = session_open.hour + session_open.minute / 60 + session_open.second / 3600
            end_hour = session_close.hour + session_close.minute / 60 + session_close.second / 3600
            while end_hour <= start_hour:
                end_hour += 24
            duration = min(end_hour - start_hour, 12)
            start_tk = 90 - ((start_hour % 12) * 30)
            extent = -(duration * 30)
            base_arc = str(self.theme_palette.get("clock_arc_active", "#7CFC8A")) if session_active else str(self.theme_palette.get("clock_arc_inactive", "#FF8A8A"))
            if session_active:
                pulse = (math.sin((now_dt.second + now_dt.microsecond / 1e6) * 2 * math.pi / 1.8) + 1) / 2
                arc_color = blend_hex(base_arc, "#FFFFFF", 0.35 * pulse)
            else:
                arc_color = base_arc
            canvas.create_arc(
                cx - radius + 8,
                cy - radius + 8,
                cx + radius - 8,
                cy + radius - 8,
                start=start_tk,
                extent=extent,
                style="arc",
                outline=arc_color,
                width=10,
            )

            start_mark = blend_hex(arc_color, "#FFFFFF", 0.25)
            end_mark = blend_hex(arc_color, "#000000", 0.20)
            for mark_hour, color in ((start_hour, start_mark), (end_hour, end_mark)):
                angle = math.radians((mark_hour % 12) * 30 - 90)
                inner_x = cx + math.cos(angle) * (radius - 30)
                inner_y = cy + math.sin(angle) * (radius - 30)
                outer_x = cx + math.cos(angle) * (radius - 2)
                outer_y = cy + math.sin(angle) * (radius - 2)
                canvas.create_line(inner_x, inner_y, outer_x, outer_y, fill=color, width=3)

        hour = now_dt.hour % 12 + now_dt.minute / 60 + now_dt.second / 3600
        minute = now_dt.minute + now_dt.second / 60
        second = now_dt.second

        self._draw_hand(canvas, cx, cy, radius * 0.52, hour * 30, 5, str(self.theme_palette.get("clock_hour", "#F8FAFC")))
        self._draw_hand(canvas, cx, cy, radius * 0.72, minute * 6, 3, str(self.theme_palette.get("clock_minute", "#D6E7FF")))
        self._draw_hand(canvas, cx, cy, radius * 0.83, second * 6, 1, str(self.theme_palette.get("clock_second", "#FF6B6B")))

        canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=str(self.theme_palette.get("clock_pin", "#F8FAFC")), outline="")

    def _draw_hand(self, canvas: tk.Canvas, cx: float, cy: float, length: float, angle_degrees: float, width: int, color: str) -> None:
        radians = math.radians(angle_degrees - 90)
        x = cx + math.cos(radians) * length
        y = cy + math.sin(radians) * length
        canvas.create_line(cx, cy, x, y, fill=color, width=width)

    def _refresh_header(self, now_system: datetime, base_now: datetime) -> None:
        base_zone_id = self._get_base_zone_id()
        mode_name = "AUTO" if self.base_mode_var.get() == "auto" else "MANUAL"
        dst_label = self._t("TAK", "YES") if is_dst_active(base_now) else self._t("NIE", "NO")

        self.base_time_var.set(base_now.strftime("%Y-%m-%d  %H:%M:%S"))
        self.base_info_var.set(f"{mode_name} | {base_zone_id} | {base_now.tzname()} | {format_offset(base_now.utcoffset())} | DST: {dst_label}")
        self.system_info_var.set(self._t(f"System lokalny: {self.system_zone_key} | {now_system.tzname()} | {format_offset(now_system.utcoffset())}", f"Local system: {self.system_zone_key} | {now_system.tzname()} | {format_offset(now_system.utcoffset())}"))

    def _refresh_world_table(self, base_now: datetime) -> None:
        base_offset = base_now.utcoffset() or timedelta(0)
        for place_name, zone_id in self.world_rows:
            target = self.engine.convert(base_now, zone_id)
            phase_key = day_phase(target.hour)
            phase_txt = phase_label(phase_key, self.language_var.get())
            self.world_tree.item(zone_id, values=(self._city_display_name(place_name), zone_id, target.strftime("%Y-%m-%d %H:%M:%S"), target.tzname() or "-", format_offset(target.utcoffset()), format_diff((target.utcoffset() or timedelta(0)) - base_offset), phase_txt), tags=(phase_key,))

    def _refresh_search_table(self, base_now: datetime) -> None:
        base_offset = base_now.utcoffset() or timedelta(0)
        for result in self.search_results:
            zone_id = result.zone_id
            if not self.search_tree.exists(zone_id):
                continue

            zone = self.engine.zone(zone_id)
            if zone is None and not self.engine.has_fallback(zone_id):
                continue
            target = self.engine.convert(base_now, zone_id)
            phase_key = day_phase(target.hour)
            phase_txt = phase_label(phase_key, self.language_var.get())
            self.search_tree.item(
                zone_id,
                values=(
                    zone_id,
                    target.strftime("%Y-%m-%d %H:%M:%S"),
                    target.tzname() or "-",
                    format_offset(target.utcoffset()),
                    format_diff((target.utcoffset() or timedelta(0)) - base_offset),
                    phase_txt,
                    compact_source_label(result.source),
                ),
                tags=(phase_key,),
            )

        if self.selected_zone and self.search_tree.exists(self.selected_zone):
            self._update_detail_panel(self.selected_zone, base_now=base_now)

    def _refresh_universal_table(self, base_now: datetime) -> None:
        base_offset = base_now.utcoffset() or timedelta(0)
        for name, zone_id, _ in self.universal_rows:
            row_id = f"u::{name}::{zone_id}"
            zone = self.engine.zone(zone_id)
            if zone is None and not self.engine.has_fallback(zone_id):
                continue
            now_target = self.engine.convert(base_now, zone_id)
            self.universal_tree.item(
                row_id,
                values=(
                    name,
                    zone_id,
                    now_target.strftime("%Y-%m-%d %H:%M:%S"),
                    now_target.tzname() or "-",
                    format_offset(now_target.utcoffset()),
                    format_diff((now_target.utcoffset() or timedelta(0)) - base_offset),
                    seasonal_offset_description(zone_id, now_target.year, language=self.language_var.get()),
                ),
            )

    def _refresh_tiles(self, base_now: datetime) -> None:
        base_offset = base_now.utcoffset() or timedelta(0)
        any_active = False
        for card in self.tile_cards:
            zone = self.engine.zone(card.zone_id)
            if zone is None and not self.engine.has_fallback(card.zone_id):
                continue

            now_tile = self.engine.convert(base_now, card.zone_id)
            phase_key = day_phase(now_tile.hour)
            phase_txt = phase_label(phase_key, self.language_var.get())

            session_text, session_active, open_tile, close_tile = self._session_state_for_card(card, now_tile)

            card.title_label.configure(text=self._tile_display_title(card))
            card.digital_label.configure(text=now_tile.strftime("%H:%M:%S"))
            card.meta_label.configure(
                text=(
                    f"{card.zone_id} | {now_tile.tzname()} | {format_offset(now_tile.utcoffset())} | "
                    + self._t("do bazowego ", "to base ")
                    + f"{format_diff((now_tile.utcoffset() or timedelta(0)) - base_offset)}"
                )
            )
            card.phase_label.configure(text=phase_txt, bg=str(self.phase_bg.get(phase_key, "#1E2B4A")))
            card.session_label.configure(
                text=session_text,
                bg=str(self.theme_palette.get("session_active", "#21603A")) if session_active else str(self.theme_palette.get("session_inactive", "#603030")),
            )

            self._draw_clock(card.canvas, now_tile, phase_key, open_tile, close_tile, session_active)
            self._handle_session_sound(card, session_active, open_tile, close_tile)
            if session_active:
                any_active = True

        self._update_ticking_state(any_active)

    def _refresh_focus_tiles(self, base_now: datetime) -> None:
        if not self.fullscreen_enabled or self.tile_focus_window is None:
            return
        base_offset = base_now.utcoffset() or timedelta(0)
        for card in self.focus_tile_cards:
            zone = self.engine.zone(card.zone_id)
            if zone is None and not self.engine.has_fallback(card.zone_id):
                continue

            now_tile = self.engine.convert(base_now, card.zone_id)
            phase_key = day_phase(now_tile.hour)
            phase_txt = phase_label(phase_key, self.language_var.get())
            session_text, session_active, open_tile, close_tile = self._session_state_for_card(card, now_tile)

            card.title_label.configure(text=self._tile_display_title(card))
            card.digital_label.configure(text=now_tile.strftime("%H:%M:%S"))
            card.meta_label.configure(
                text=(
                    f"{card.zone_id} | {now_tile.tzname()} | {format_offset(now_tile.utcoffset())} | "
                    + self._t("do bazowego ", "to base ")
                    + f"{format_diff((now_tile.utcoffset() or timedelta(0)) - base_offset)}"
                )
            )
            card.phase_label.configure(text=phase_txt, bg=str(self.phase_bg.get(phase_key, "#1E2B4A")))
            card.session_label.configure(
                text=session_text,
                bg=str(self.theme_palette.get("session_active", "#21603A")) if session_active else str(self.theme_palette.get("session_inactive", "#603030")),
            )
            self._draw_clock(card.canvas, now_tile, phase_key, open_tile, close_tile, session_active)

    def _refresh_loop(self) -> None:
        self._apply_theme()
        now_system = datetime.now().astimezone()
        base_now = self._get_base_now(now_system)

        self._refresh_header(now_system, base_now)
        self._refresh_world_table(base_now)
        self._refresh_search_table(base_now)
        self._refresh_universal_table(base_now)
        self._refresh_tiles(base_now)
        self._refresh_focus_tiles(base_now)
        self._refresh_alarms_and_timers(now_system)
        if hasattr(self, "world_map_canvas"):
            self._draw_world_map_tab()

        if self.converter_live_var.get():
            self._run_converter(silent=True)

        if self.settings_dirty and self.settings_save_after_id is None:
            self._mark_settings_dirty()

        self.after(self.REFRESH_MS, self._refresh_loop)


def main() -> None:
    app = TimeSpecialistApp()
    app.mainloop()


if __name__ == "__main__":
    main()
