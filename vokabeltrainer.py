#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vokabeltrainer Spanisch -> Deutsch (Niveau A2)
Standalone-Desktop-Programm, kein Browser. Nur Python-Standardbibliothek.

Ablauf:  spanisches Wort -> deutsches Wort tippen -> Auflösung + Vorlesen.
Nomen mit Artikel und Plural, Verben mit Kasus (Akkusativ / Dativ / Präposition).

Fortschritt: Leitner-Karteikasten (5 Fächer), gespeichert in fortschritt.json.

Sprachausgabe: NUR deutsche Stimmen. Ohne deutsche Stimme bleibt das Programm
stumm und zeigt einen Hinweis — es liest niemals mit einer englischen Stimme vor.
  1. edge-tts  (neuronale de-DE-Stimmen, beste Qualität; pip install edge-tts)
  2. SAPI5     (Windows, deutsche Systemstimme, offline)
  3. say       (macOS)      4. espeak-ng (Linux)
Erzeugte Audiodateien liegen im Ordner "audio" und werden wiederverwendet.
"""

import csv
import ctypes
import hashlib
import json
import platform
import random
import re
import shutil
import subprocess
import sys
import threading
from datetime import date, timedelta
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TK_VERFUEGBAR = True
except ImportError:                                    # pragma: no cover
    TK_VERFUEGBAR = False

try:
    import edge_tts                                    # noqa: F401
    EDGE_LIB = True
except Exception:                                      # pragma: no cover
    EDGE_LIB = False

# ---------------------------------------------------------------- Konstanten

DATEI_VOKABELN = "vokabeln.csv"
DATEI_FORTSCHRITT = "fortschritt.json"
ORDNER_AUDIO = "audio"
KARTEN_PRO_RUNDE = 20

EDGE_STIMMEN = [
    ("de-DE-KatjaNeural", "Katja (de-DE, neuronal)"),
    ("de-DE-ConradNeural", "Conrad (de-DE, neuronal)"),
    ("de-DE-AmalaNeural", "Amala (de-DE, neuronal)"),
    ("de-DE-KillianNeural", "Killian (de-DE, neuronal)"),
]
HINWEIS_KEINE_STIMME = "sin voz alemana — instalar:  pip install edge-tts"
FAECHER = {1: 0, 2: 1, 3: 3, 4: 7, 5: 21}              # Fach -> Tage bis Wiederholung

FARBE_BG = "#f4f4f2"
FARBE_KARTE = "#ffffff"
FARBE_TEXT = "#1c1c1c"
FARBE_GRAU = "#6b6b6b"
FARBE_BLAU = "#1f5fa9"
FARBE_GRUEN = "#1a7f37"
FARBE_ROT = "#c22b2b"
FARBE_GELB = "#a86400"

KASUS_FARBE = {
    "Akkusativ": FARBE_BLAU,
    "Dativ": FARBE_GELB,
    "Dativ + Akkusativ": "#6b3fa0",
    "ohne Objekt": FARBE_GRAU,
}

TYP_ES = {
    "nomen": "sustantivo",
    "verb": "verbo",
    "adjektiv": "adjetivo",
    "adverb": "adverbio",
}

# ------------------------------------------------------------------- Pfade


def programm_ordner() -> Path:
    """Ordner neben dem Skript bzw. neben der .exe (PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def datei_suchen(name: str) -> Path:
    """Erst neben dem Programm suchen, dann im PyInstaller-Bundle."""
    extern = programm_ordner() / name
    if extern.exists():
        return extern
    gebundelt = Path(getattr(sys, "_MEIPASS", programm_ordner())) / name
    return gebundelt


# --------------------------------------------------------------- Sprachausgabe


class Sprecher:
    """Deutsche Sprachausgabe. Ohne deutsche Stimme wird nichts vorgelesen."""

    def __init__(self, cache_ordner: Path):
        self.system = platform.system()
        self.cache = cache_ordner
        try:
            self.cache.mkdir(exist_ok=True)
        except Exception:
            pass
        self.stimmen = []          # [{"art": ..., "name": ..., "label": ...}]
        self.aktiv = None
        self.hinweis = HINWEIS_KEINE_STIMME
        self._laeuft = set()
        self._schloss = threading.Lock()
        self._erkennen()

    # -- Erkennung ---------------------------------------------------------

    def _erkennen(self):
        if EDGE_LIB or shutil.which("edge-tts"):
            for name, label in EDGE_STIMMEN:
                self.stimmen.append({"art": "edge", "name": name, "label": label})
        if self.system == "Windows":
            for name in self._sapi_deutsche_stimmen():
                self.stimmen.append({"art": "sapi", "name": name,
                                     "label": f"{name} (Windows, offline)"})
        elif self.system == "Darwin":
            for name in self._mac_deutsche_stimmen():
                self.stimmen.append({"art": "say", "name": name,
                                     "label": f"{name} (macOS, offline)"})
        else:
            for befehl in ("espeak-ng", "espeak", "spd-say"):
                if shutil.which(befehl):
                    self.stimmen.append({"art": befehl, "name": "de",
                                         "label": f"{befehl} de (offline)"})
                    break
        if self.stimmen:
            self.aktiv = self.stimmen[0]
            self.hinweis = "voz: " + self.aktiv["label"]

    def _sapi_deutsche_stimmen(self):
        """Nur Stimmen mit deutscher Culture — englische werden ignoriert."""
        ps = (
            "Add-Type -AssemblyName System.Speech;"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$s.GetInstalledVoices()|Where-Object "
            "{$_.VoiceInfo.Culture.Name -like 'de*'}|"
            "ForEach-Object {Write-Output $_.VoiceInfo.Name}"
        )
        try:
            aus = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                capture_output=True, text=True, timeout=25,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return [z.strip() for z in aus.stdout.splitlines() if z.strip()]
        except Exception:
            return []

    def _mac_deutsche_stimmen(self):
        try:
            aus = subprocess.run(["say", "-v", "?"], capture_output=True,
                                 text=True, timeout=10).stdout
        except Exception:
            return []
        return [z.split()[0] for z in aus.splitlines()
                if len(z.split()) >= 2 and z.split()[1].startswith("de_")]

    # -- Auswahl -----------------------------------------------------------

    def labels(self):
        return [s["label"] for s in self.stimmen]

    def waehlen(self, label):
        for s in self.stimmen:
            if s["label"] == label:
                self.aktiv = s
                self.hinweis = "voz: " + label
                return

    # -- Ausgabe -----------------------------------------------------------

    def sag(self, text):
        self._starten(text, abspielen=True)

    def vorbereiten(self, text):
        """Audio im Hintergrund erzeugen, damit die Auflösung sofort klingt."""
        self._starten(text, abspielen=False)

    def _starten(self, text, abspielen):
        if not text or not self.aktiv:
            return
        threading.Thread(target=self._arbeiten, args=(text, self.aktiv, abspielen),
                         daemon=True).start()

    def _arbeiten(self, text, stimme, abspielen):
        try:
            if stimme["art"] in ("edge", "sapi"):
                pfad = self._datei(text, stimme)
                if pfad and abspielen:
                    self._abspielen(pfad)
            elif abspielen:
                self._direkt(text, stimme)
        except Exception:
            pass

    def _datei(self, text, stimme):
        endung = ".mp3" if stimme["art"] == "edge" else ".wav"
        schluessel = hashlib.sha1(f"{stimme['name']}|{text}".encode("utf-8")).hexdigest()[:16]
        pfad = self.cache / f"{schluessel}{endung}"
        if pfad.exists() and pfad.stat().st_size > 0:
            return pfad
        with self._schloss:
            if str(pfad) in self._laeuft:
                return None
            self._laeuft.add(str(pfad))
        try:
            if stimme["art"] == "edge":
                self._edge_erzeugen(text, stimme["name"], pfad)
            else:
                self._sapi_erzeugen(text, stimme["name"], pfad)
        finally:
            with self._schloss:
                self._laeuft.discard(str(pfad))
        return pfad if pfad.exists() and pfad.stat().st_size > 0 else None

    def _edge_erzeugen(self, text, stimme, pfad):
        if EDGE_LIB:
            import asyncio
            import edge_tts as et

            async def lauf():
                await et.Communicate(text, stimme, rate="-10%").save(str(pfad))

            asyncio.run(lauf())
            return
        exe = shutil.which("edge-tts")
        if exe:
            subprocess.run([exe, "--voice", stimme, "--rate=-10%", "--text", text,
                            "--write-media", str(pfad)],
                           capture_output=True, timeout=60,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def _sapi_erzeugen(self, text, stimme, pfad):
        sicher = text.replace("'", "''")
        ps = (
            "Add-Type -AssemblyName System.Speech;"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            f"$s.SelectVoice('{stimme}');$s.Rate=-1;"
            f"$s.SetOutputToWaveFile('{pfad}');$s.Speak('{sicher}');$s.Dispose()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True, timeout=60,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def _abspielen(self, pfad: Path):
        if self.system == "Windows":
            alias = "vok" + hashlib.sha1(str(pfad).encode()).hexdigest()[:8]
            mci = ctypes.windll.winmm.mciSendStringW
            typ = "mpegvideo" if pfad.suffix == ".mp3" else "waveaudio"
            mci(f'open "{pfad}" type {typ} alias {alias}', None, 0, None)
            mci(f"play {alias} wait", None, 0, None)
            mci(f"close {alias}", None, 0, None)
        elif self.system == "Darwin":
            subprocess.run(["afplay", str(pfad)], capture_output=True, timeout=60)
        else:
            for spieler in ("mpv", "ffplay", "mpg123", "aplay"):
                if shutil.which(spieler):
                    args = {"mpv": ["--really-quiet"],
                            "ffplay": ["-nodisp", "-autoexit", "-loglevel", "quiet"]
                            }.get(spieler, [])
                    subprocess.run([spieler] + args + [str(pfad)],
                                   capture_output=True, timeout=60)
                    return

    def _direkt(self, text, stimme):
        if stimme["art"] == "say":
            subprocess.run(["say", "-v", stimme["name"], "-r", "150", text],
                           capture_output=True, timeout=30)
        elif stimme["art"] == "spd-say":
            subprocess.run(["spd-say", "-l", "de", "-w", text],
                           capture_output=True, timeout=30)
        else:
            subprocess.run([stimme["art"], "-v", "de", "-s", "130", text],
                           capture_output=True, timeout=30)


def sprechtext(karte) -> str:
    """Text, der vorgelesen wird: Nomen mit Artikel und Plural."""
    if karte["typ"] == "nomen":
        wort = f"{karte['art']} {karte['de']}" if karte["art"] else karte["de"]
        if karte["plural"] and karte["plural"] not in ("nur Plural", "nur Singular"):
            return f"{wort}. Plural: die {karte['plural']}."
        return wort
    return karte["de"]


# ------------------------------------------------------------------ Vokabeln


def vokabeln_laden(pfad: Path):
    karten = []
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        for i, zeile in enumerate(csv.DictReader(f, delimiter=";")):
            de = (zeile.get("de") or "").strip()
            es = (zeile.get("es") or "").strip()
            if not de or not es:
                continue
            karten.append({
                "id": f"{i}:{de.lower()}",
                "typ": (zeile.get("typ") or "").strip().lower(),
                "es": es,
                "art": (zeile.get("art") or "").strip(),
                "de": de,
                "plural": (zeile.get("plural") or "").strip(),
                "kasus": (zeile.get("kasus") or "").strip(),
                "perfekt": (zeile.get("perfekt") or "").strip(),
                "bsp": (zeile.get("bsp") or "").strip(),
                "alt": [a.strip() for a in (zeile.get("alt") or "").split("|") if a.strip()],
                "thema": (zeile.get("thema") or "").strip(),
            })
    if not karten:
        raise ValueError("Keine Vokabeln gefunden.")
    return karten


# ------------------------------------------------- Antwortprüfung (testbar)


def normalisieren(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"^(der|die|das)\s+", "", t)
    t = re.sub(r"^(sich)\s+", "", t)
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z ]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def artikel_der_eingabe(text: str):
    m = re.match(r"^\s*(der|die|das)\b", text.strip().lower())
    return m.group(1) if m else None


def abstand(a: str, b: str) -> int:
    if a == b:
        return 0
    vorher = list(range(len(b) + 1))
    for i, za in enumerate(a, 1):
        aktuell = [i]
        for j, zb in enumerate(b, 1):
            aktuell.append(min(vorher[j] + 1, aktuell[j - 1] + 1,
                               vorher[j - 1] + (za != zb)))
        vorher = aktuell
    return vorher[-1]


def pruefen(eingabe: str, karte: dict) -> str:
    """Gibt 'richtig', 'fast' oder 'falsch' zurück."""
    if not eingabe.strip():
        return "falsch"
    nutzer = normalisieren(eingabe)
    loesungen = [normalisieren(karte["de"])] + [normalisieren(a) for a in karte["alt"]]
    if nutzer in loesungen:
        art = artikel_der_eingabe(eingabe)
        if karte["typ"] == "nomen" and art and art != karte["art"]:
            return "fast"
        return "richtig"
    for loesung in loesungen:
        if len(loesung) >= 5 and abstand(nutzer, loesung) <= 1:
            return "fast"
    return "falsch"


# ---------------------------------------------------------------- Fortschritt


def fortschritt_laden(pfad: Path) -> dict:
    try:
        with open(pfad, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def fortschritt_speichern(pfad: Path, daten: dict):
    try:
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def runde_zusammenstellen(karten, fortschritt, anzahl=KARTEN_PRO_RUNDE):
    heute = date.today().isoformat()
    faellig, neu = [], []
    for k in karten:
        stand = fortschritt.get(k["id"])
        if stand is None:
            neu.append(k)
        elif stand.get("faellig", heute) <= heute:
            faellig.append((stand.get("fach", 1), k))
    faellig.sort(key=lambda p: p[0])
    runde = [k for _, k in faellig][:anzahl]
    random.shuffle(neu)
    runde += neu[:max(0, anzahl - len(runde))]
    random.shuffle(runde)
    return runde


def stand_aktualisieren(fortschritt, karte, ergebnis):
    stand = fortschritt.get(karte["id"], {"fach": 1, "richtig": 0, "falsch": 0})
    fach = stand.get("fach", 1)
    if ergebnis == "richtig":
        fach = min(5, fach + 1)
        stand["richtig"] = stand.get("richtig", 0) + 1
    elif ergebnis == "falsch":
        fach = 1
        stand["falsch"] = stand.get("falsch", 0) + 1
    stand["fach"] = fach
    stand["faellig"] = (date.today() + timedelta(days=FAECHER[fach])).isoformat()
    fortschritt[karte["id"]] = stand
    return fortschritt


# ----------------------------------------------------------------- Oberfläche


class Trainer:
    def __init__(self, wurzel, karten, sprecher, pfad_fortschritt):
        self.w = wurzel
        self.karten = karten
        self.sprecher = sprecher
        self.pfad_fortschritt = pfad_fortschritt
        self.fortschritt = fortschritt_laden(pfad_fortschritt)
        self.runde = []
        self.index = 0
        self.treffer = 0
        self.aufgeloest = False
        self.karte = None

        self.familie = {"Windows": "Segoe UI", "Darwin": "Helvetica Neue"}.get(
            platform.system(), "DejaVu Sans")
        self.f_klein = (self.familie, 10)
        self.f_normal = (self.familie, 12)
        self.f_eingabe = (self.familie, 20)
        self.f_gross = (self.familie, 34, "bold")
        self.f_loesung = (self.familie, 28, "bold")

        self._oberflaeche_bauen()
        self._runde_starten()

    # ---------------------------------------------------------- Aufbau

    def _oberflaeche_bauen(self):
        self.w.title("Vokabeltrainer  ·  español → alemán  (A2)")
        self.w.configure(bg=FARBE_BG)
        self.w.geometry("760x620")
        self.w.minsize(680, 560)

        kopf = tk.Frame(self.w, bg=FARBE_BG)
        kopf.pack(fill="x", padx=24, pady=(18, 6))
        self.l_zaehler = tk.Label(kopf, text="", font=self.f_klein,
                                  bg=FARBE_BG, fg=FARBE_GRAU)
        self.l_zaehler.pack(side="left")
        self.l_punkte = tk.Label(kopf, text="", font=self.f_klein,
                                 bg=FARBE_BG, fg=FARBE_GRAU)
        self.l_punkte.pack(side="right")

        karte = tk.Frame(self.w, bg=FARBE_KARTE, highlightthickness=1,
                         highlightbackground="#e0e0dc")
        karte.pack(fill="both", expand=True, padx=24, pady=6)

        self.l_typ = tk.Label(karte, text="", font=self.f_klein,
                              bg=FARBE_KARTE, fg=FARBE_GRAU)
        self.l_typ.pack(pady=(26, 0))
        self.l_frage = tk.Label(karte, text="", font=self.f_gross, bg=FARBE_KARTE,
                                fg=FARBE_TEXT, wraplength=640, justify="center")
        self.l_frage.pack(pady=(4, 18))

        self.e_antwort = tk.Entry(karte, font=self.f_eingabe, justify="center",
                                  relief="flat", bg="#f0f0ec", fg=FARBE_TEXT,
                                  insertbackground=FARBE_TEXT)
        self.e_antwort.pack(ipady=8, padx=90, fill="x")

        umlaute = tk.Frame(karte, bg=FARBE_KARTE)
        umlaute.pack(pady=8)
        for zeichen in ("ä", "ö", "ü", "ß", "Ä", "Ö", "Ü"):
            tk.Button(umlaute, text=zeichen, font=self.f_normal, width=3,
                      relief="flat", bg="#e8e8e4", fg=FARBE_TEXT, cursor="hand2",
                      command=lambda z=zeichen: self._zeichen_einfuegen(z)
                      ).pack(side="left", padx=3)

        self.b_pruefen = tk.Button(karte, text="Comprobar   ⏎", font=self.f_normal,
                                   relief="flat", bg=FARBE_BLAU, fg="white",
                                   activebackground="#17457a", activeforeground="white",
                                   cursor="hand2", padx=22, pady=8,
                                   command=self._weiter)
        self.b_pruefen.pack(pady=(4, 10))

        self.loesung = tk.Frame(karte, bg=FARBE_KARTE)
        self.loesung.pack(fill="both", expand=True, padx=30)

        self.l_urteil = tk.Label(self.loesung, text="", font=(self.familie, 13, "bold"),
                                 bg=FARBE_KARTE)
        self.l_urteil.pack()
        self.l_wort = tk.Label(self.loesung, text="", font=self.f_loesung,
                               bg=FARBE_KARTE, fg=FARBE_TEXT, wraplength=640)
        self.l_wort.pack(pady=(2, 2))
        self.l_grammatik = tk.Label(self.loesung, text="", font=self.f_normal,
                                    bg=FARBE_KARTE, wraplength=640, justify="center")
        self.l_grammatik.pack()
        self.l_extra = tk.Label(self.loesung, text="", font=self.f_normal,
                                bg=FARBE_KARTE, fg=FARBE_GRAU, wraplength=640,
                                justify="center")
        self.l_extra.pack(pady=(2, 0))

        knoepfe = tk.Frame(self.loesung, bg=FARBE_KARTE)
        knoepfe.pack(pady=10)
        self.b_ton_wort = tk.Button(knoepfe, text="🔊 palabra", font=self.f_klein,
                                    relief="flat", bg="#e8e8e4", cursor="hand2",
                                    padx=12, pady=5,
                                    command=lambda: self.sprecher.sag(sprechtext(self.karte)))
        self.b_ton_wort.pack(side="left", padx=4)
        self.b_ton_satz = tk.Button(knoepfe, text="🔊 frase", font=self.f_klein,
                                    relief="flat", bg="#e8e8e4", cursor="hand2",
                                    padx=12, pady=5,
                                    command=lambda: self.sprecher.sag(self.karte["bsp"]))
        self.b_ton_satz.pack(side="left", padx=4)

        fuss = tk.Frame(self.w, bg=FARBE_BG)
        fuss.pack(fill="x", padx=24, pady=(4, 14))
        tk.Label(fuss, text="voz:", font=self.f_klein, bg=FARBE_BG,
                 fg=FARBE_GRAU).pack(side="left")
        if self.sprecher.stimmen:
            self.v_stimme = tk.StringVar(value=self.sprecher.aktiv["label"])
            auswahl = ttk.Combobox(fuss, textvariable=self.v_stimme, state="readonly",
                                   values=self.sprecher.labels(), width=28,
                                   font=self.f_klein)
            auswahl.pack(side="left", padx=6)
            auswahl.bind("<<ComboboxSelected>>", self._stimme_gewechselt)
            tk.Button(fuss, text="probar", font=self.f_klein, relief="flat",
                      bg="#e8e8e4", cursor="hand2", padx=10,
                      command=self._stimme_testen).pack(side="left")
        else:
            tk.Label(fuss, text=HINWEIS_KEINE_STIMME, font=self.f_klein,
                     bg=FARBE_BG, fg=FARBE_ROT).pack(side="left", padx=6)
        tk.Button(fuss, text="Terminar", font=self.f_klein, relief="flat",
                  bg=FARBE_BG, fg=FARBE_GRAU, cursor="hand2",
                  command=self.w.destroy).pack(side="right")

        self.w.bind("<Return>", lambda e: self._weiter())
        self.w.bind("<KP_Enter>", lambda e: self._weiter())
        self.w.bind("<Escape>", lambda e: self.w.destroy())

    def _stimme_gewechselt(self, _ereignis=None):
        self.sprecher.waehlen(self.v_stimme.get())
        self._stimme_testen()

    def _stimme_testen(self):
        self.sprecher.sag("Guten Tag. Ich spreche Hochdeutsch.")

    def _zeichen_einfuegen(self, zeichen):
        self.e_antwort.insert("insert", zeichen)
        self.e_antwort.focus_set()

    # ---------------------------------------------------------- Ablauf

    def _runde_starten(self):
        self.runde = runde_zusammenstellen(self.karten, self.fortschritt)
        self.index = 0
        self.treffer = 0
        if not self.runde:
            self._alles_erledigt()
            return
        self._frage_zeigen()

    def _frage_zeigen(self):
        self.aufgeloest = False
        self.karte = self.runde[self.index]
        self.l_zaehler.config(
            text=f"Tarjeta {self.index + 1} / {len(self.runde)}  ·  {self.karte['thema']}")
        self.l_punkte.config(text=f"Aciertos: {self.treffer}")
        self.l_typ.config(text=TYP_ES.get(self.karte["typ"], ""))
        self.l_frage.config(text=self.karte["es"])
        for etikett in (self.l_urteil, self.l_wort, self.l_grammatik, self.l_extra):
            etikett.config(text="")
        self.b_ton_wort.pack_forget()
        self.b_ton_satz.pack_forget()
        self.b_pruefen.config(text="Comprobar   ⏎", bg=FARBE_BLAU)
        self.e_antwort.config(state="normal")
        self.e_antwort.delete(0, "end")
        self.e_antwort.focus_set()
        self.sprecher.vorbereiten(sprechtext(self.karte))

    def _weiter(self):
        if self.aufgeloest:
            self.index += 1
            if self.index >= len(self.runde):
                self._runde_beenden()
            else:
                self._frage_zeigen()
        else:
            self._aufloesen()

    def _aufloesen(self):
        ergebnis = pruefen(self.e_antwort.get(), self.karte)
        if ergebnis == "richtig":
            self.treffer += 1
            self.l_urteil.config(text="¡Correcto!", fg=FARBE_GRUEN)
        elif ergebnis == "fast":
            self.l_urteil.config(text="Casi — mira bien el artículo / la ortografía",
                                 fg=FARBE_GELB)
        else:
            self.l_urteil.config(text="Incorrecto", fg=FARBE_ROT)

        self.fortschritt = stand_aktualisieren(self.fortschritt, self.karte, ergebnis)
        fortschritt_speichern(self.pfad_fortschritt, self.fortschritt)

        k = self.karte
        self.l_wort.config(text=(f"{k['art']} {k['de']}" if k["art"] else k["de"]))

        if k["typ"] == "nomen":
            plural = k["plural"]
            text = "" if plural in ("nur Plural", "nur Singular", "") else f"Plural: die {plural}"
            if plural in ("nur Plural", "nur Singular"):
                text = plural
            self.l_grammatik.config(text=text, fg=FARBE_GRAU)
        elif k["typ"] == "verb":
            kasus = k["kasus"]
            farbe = KASUS_FARBE.get(kasus, FARBE_GRUEN)
            self.l_grammatik.config(text=f"→  {kasus}", fg=farbe)
        else:
            self.l_grammatik.config(text="", fg=FARBE_GRAU)

        zusatz = []
        if k["perfekt"]:
            zusatz.append(f"Perfekt: {k['perfekt']}")
        if k["bsp"]:
            zusatz.append(k["bsp"])
        if k["alt"]:
            zusatz.append("también: " + ", ".join(k["alt"]))
        self.l_extra.config(text="\n".join(zusatz))

        self.b_ton_wort.pack(side="left", padx=4)
        if k["bsp"]:
            self.b_ton_satz.pack(side="left", padx=4)

        self.e_antwort.config(state="disabled")
        self.b_pruefen.config(text="Siguiente   ⏎", bg="#3a3a38")
        self.aufgeloest = True
        self.sprecher.sag(sprechtext(k))

    def _runde_beenden(self):
        quote = round(100 * self.treffer / max(1, len(self.runde)))
        self.l_typ.config(text="")
        self.l_frage.config(text=f"{self.treffer} / {len(self.runde)}  ·  {quote} %")
        self.l_urteil.config(text="Ronda terminada", fg=FARBE_GRUEN)
        self.l_wort.config(text="")
        self.l_grammatik.config(text="")
        self.l_extra.config(text="Pulsa ⏎ para la siguiente ronda.", fg=FARBE_GRAU)
        self.b_ton_wort.pack_forget()
        self.b_ton_satz.pack_forget()
        self.e_antwort.config(state="disabled")
        self.b_pruefen.config(text="Otra ronda   ⏎", bg=FARBE_BLAU)
        self.aufgeloest = False
        self.w.bind("<Return>", lambda e: self._runde_starten())
        self.b_pruefen.config(command=self._neustart)

    def _neustart(self):
        self.w.bind("<Return>", lambda e: self._weiter())
        self.b_pruefen.config(command=self._weiter)
        self._runde_starten()

    def _alles_erledigt(self):
        self.l_typ.config(text="")
        self.l_frage.config(text="¡Todo repasado por hoy!")
        self.l_extra.config(text="Vuelve mañana — las tarjetas están programadas.",
                            fg=FARBE_GRAU)
        self.e_antwort.config(state="disabled")
        self.b_pruefen.config(state="disabled")


# ---------------------------------------------------------------------- Start


def main():
    if not TK_VERFUEGBAR:
        print("tkinter fehlt. Unter Windows Python von python.org installieren "
              "(tkinter ist dort enthalten).")
        return 1

    pfad = datei_suchen(DATEI_VOKABELN)
    wurzel = tk.Tk()
    try:
        karten = vokabeln_laden(pfad)
    except Exception as fehler:
        wurzel.withdraw()
        messagebox.showerror("Vokabeltrainer",
                             f"{DATEI_VOKABELN} konnte nicht gelesen werden:\n{fehler}\n\n"
                             f"Erwartet unter: {pfad}")
        return 1

    Trainer(wurzel, karten, Sprecher(programm_ordner() / ORDNER_AUDIO),
            programm_ordner() / DATEI_FORTSCHRITT)
    wurzel.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
