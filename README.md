<p align="center">
  <a href="#english">English</a> • <a href="#polski">Polski</a>
</p>

# 🕒 World Time Specialist

## 📑 Table of Contents

**Quick**
- [Languages](#languages)
- [Download](#download)

**English**
- [Key Features](#en-features)
- [Requirements](#en-requirements)
- [Run](#en-run)
- [Build (Portable EXE)](#en-build-portable)
- [Build (Installer EXE)](#en-build-installer)
- [Credits](#en-credits)

**Polski**
- [Najważniejsze funkcje](#pl-features)
- [Wymagania](#pl-requirements)
- [Uruchomienie](#pl-run)
- [Budowanie (Portable EXE)](#pl-build-portable)
- [Budowanie (Installer EXE)](#pl-build-installer)
- [Credits](#pl-credits)

<a id="languages"></a>

## 🌐 Languages

- 🇬🇧 English (default)
- 🇵🇱 Polski → [Przejdź do sekcji polskiej](#polski)

<a id="download"></a>

## ⬇️ Download

[![Download Installer](https://img.shields.io/badge/Download-Installer-blue?style=for-the-badge&logo=windows)](https://github.com/hattimon/WorldTimeSpecialist/releases/download/v1.0.0/WorldTimeSpecialist-Setup.exe)
[![Download Portable](https://img.shields.io/badge/Download-Portable%20EXE-3b82f6?style=for-the-badge&logo=windows)](https://github.com/hattimon/WorldTimeSpecialist/releases/download/v1.0.0/WorldTimeSpecialist-Portable.exe)
[![All Releases](https://img.shields.io/badge/All%20Releases-GitHub-111827?style=for-the-badge&logo=github)](https://github.com/hattimon/WorldTimeSpecialist/releases)

<a id="english"></a>

## 🇬🇧 English

World Time Specialist is a desktop **Python (tkinter)** application for working with time zones, world clocks, market sessions, alarms and advanced time conversions. It is designed to be **clear, visual and accurate**, with full DST handling and fast search.

<a id="en-features"></a>

### ✨ Key Features

- **Base time** modes: `AUTO` (system time zone) or `MANUAL` (forced base zone). All views show offsets relative to the base.
- **Two UI languages**: Polish and English (instant switch).
- **IANA time zones list** with autocomplete and “type to filter” behavior.
- **City/country search** with online lookup for smaller locations.
- **Universal time converter** (IANA, abbreviations, UTC offsets, and city input).
- **Two‑city comparison** (difference, local time, and context summary).
- **Education tab**: structured explanation of UTC/IANA/offsets with history and context.
- **World map tab**: realistic map with UTC bands, day/night highlight and live city markers.
- **Time tiles dashboard** with analog + digital clocks.
  - Drag, resize, **magnetic snap**, full‑screen mode.
  - Optional **grid alignment** and auto‑scaling on full screen.
- **Market sessions** on tiles with active/inactive highlighting and blinking markers.
- **Session sounds**: open/close chimes + optional **ticking** synced to second hand.
- **Alarms, timers and stopwatch**:
  - Multiple alarms in different time zones.
  - Per‑alarm duration, sound, optional script execution.
  - Daily repeat for alarms without a date.
  - Global pause for all alarms/timers.
- **Tray integration** (minimize to tray, tray menu, mute/unmute).
- **Autostart** toggle for Windows (with optional “minimize to tray on boot”).
- **Settings persisted** in `%APPDATA%\WorldTimeSpecialist\settings.json`.

<a id="en-requirements"></a>

### 🧩 Requirements

- Windows 10/11
- Python 3.11+
- `tzdata` (IANA time zone database for `zoneinfo`)

<a id="en-run"></a>

### ▶ Run (PowerShell)

```powershell
cd C:\Users\Kosmo\Documents\Playground\world-time-specialist
py -m pip install -r requirements.txt
py app.py
```

<a id="en-build-portable"></a>

### 🛠 Build (Portable EXE)

```powershell
py -m pip install pyinstaller
py -m PyInstaller --clean WorldTimeSpecialist.spec
```

Output: `dist\WorldTimeSpecialist.exe`

<a id="en-build-installer"></a>

### 📦 Build (Installer EXE)

This project includes an NSIS script. Build the **one‑dir** package and run NSIS:

```powershell
py -m PyInstaller --clean --noconfirm --onedir --name WorldTimeSpecialist app.py `
  --icon assets\clock.ico --add-data "assets;assets" --collect-data tzdata

makensis installer\WorldTimeSpecialist.nsi
```

Output: `release\WorldTimeSpecialist-Setup.exe`

<a id="en-credits"></a>

### 📎 Credits

- Sounds: SoundJay (https://www.soundjay.com/)
- World map: NASA Blue Marble (public domain)

---

<a id="polski"></a>

## 🇵🇱 Polski

World Time Specialist to desktopowa aplikacja **Python (tkinter)** do pracy ze strefami czasowymi, zegarami świata, sesjami giełdowymi, alarmami i zaawansowanymi konwersjami czasu. Projekt jest **czytelny, wizualny i precyzyjny**, z pełnym wsparciem DST i szybkim wyszukiwaniem.

<a id="pl-features"></a>

### ✨ Najważniejsze funkcje

- **Czas bazowy**: `AUTO` (strefa systemu) lub `MANUAL` (wymuszona strefa bazowa). Wszystkie widoki liczą różnice względem bazy.
- **Dwa języki interfejsu**: polski i angielski (natychmiastowe przełączanie).
- **Lista stref IANA** z autouzupełnianiem i filtrowaniem podczas pisania.
- **Wyszukiwanie miast/krajów** z obsługą online dla mniejszych lokalizacji.
- **Uniwersalny konwerter czasu** (IANA, skróty, offsety UTC i wpisywane miasta).
- **Kalkulator porównawczy** dwóch miast/stref (różnica, czas lokalny, podsumowanie).
- **Zakładka Edukacja**: struktura pojęć UTC/IANA/offsety + historia i kontekst.
- **Mapa świata**: realistyczna mapa, pasma UTC, podświetlenie dnia/nocy i markery miast na żywo.
- **Kafelki czasu** z zegarami analogowymi i cyfrowymi.
  - Przeciąganie, zmiana rozmiaru, **magnetyczne przyciąganie**, pełny ekran.
  - Opcjonalne **wyrównanie do siatki** i auto‑skalowanie w pełnym ekranie.
- **Sesje giełdowe** na kafelkach z aktywnością i migającą sygnalizacją.
- **Dźwięki sesji**: start/koniec oraz opcjonalne **tykanie** zsynchronizowane z sekundnikiem.
- **Alarmy, timery i stoper**:
  - Wiele alarmów w różnych strefach czasowych.
  - Czas dzwonienia, dźwięk, opcjonalne skrypty.
  - Powtarzanie dzienne dla alarmów bez daty.
  - Globalna pauza dla całej sekcji alarmów/timerów.
- **Tray** (minimalizacja do traya, menu, wyciszanie).
- **Autostart** w Windows (z opcją „minimalizuj do traya przy starcie”).
- **Zapis ustawień** w `%APPDATA%\WorldTimeSpecialist\settings.json`.

<a id="pl-requirements"></a>

### 🧩 Wymagania

- Windows 10/11
- Python 3.11+
- `tzdata` (baza stref IANA dla `zoneinfo`)

<a id="pl-run"></a>

### ▶ Uruchomienie (PowerShell)

```powershell
cd C:\Users\Kosmo\Documents\Playground\world-time-specialist
py -m pip install -r requirements.txt
py app.py
```

<a id="pl-build-portable"></a>

### 🛠 Budowanie (Portable EXE)

```powershell
py -m pip install pyinstaller
py -m PyInstaller --clean WorldTimeSpecialist.spec
```

Wynik: `dist\WorldTimeSpecialist.exe`

<a id="pl-build-installer"></a>

### 📦 Budowanie (Installer EXE)

Projekt zawiera skrypt NSIS. Najpierw zbuduj paczkę **onedir**, potem uruchom NSIS:

```powershell
py -m PyInstaller --clean --noconfirm --onedir --name WorldTimeSpecialist app.py `
  --icon assets\clock.ico --add-data "assets;assets" --collect-data tzdata

makensis installer\WorldTimeSpecialist.nsi
```

Wynik: `release\WorldTimeSpecialist-Setup.exe`

<a id="pl-credits"></a>

### 📎 Credits

- Dźwięki: SoundJay (https://www.soundjay.com/)
- Mapa świata: NASA Blue Marble (public domain)
