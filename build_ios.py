#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schreibt die Vokabeln aus vokabeln.csv neu in iphone/index.html.

Aufruf nach jeder Änderung an vokabeln.csv:
    C:\\Python314\\python.exe build_ios.py
Danach index.html erneut zu GitHub hochladen.
"""

import csv
import json
import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent


def finden(name, ordner):
    for kandidat in (HIER / name, HIER / ordner / name, HIER.parent / name):
        if kandidat.exists():
            return kandidat
    raise SystemExit(f"{name} nicht gefunden.")


def karten_lesen(pfad):
    karten = []
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        for i, z in enumerate(csv.DictReader(f, delimiter=";")):
            de, es = (z.get("de") or "").strip(), (z.get("es") or "").strip()
            if not de or not es:
                continue
            karten.append({
                "id": f"{i}:{de.lower()}",
                "typ": (z.get("typ") or "").strip().lower(),
                "es": es,
                "art": (z.get("art") or "").strip(),
                "de": de,
                "plural": (z.get("plural") or "").strip(),
                "kasus": (z.get("kasus") or "").strip(),
                "perfekt": (z.get("perfekt") or "").strip(),
                "bsp": (z.get("bsp") or "").strip(),
                "alt": [a.strip() for a in (z.get("alt") or "").split("|") if a.strip()],
                "thema": (z.get("thema") or "").strip(),
                "satz": (z.get("satz") or "").strip(),
                "niveau": (z.get("niveau") or "").strip(),
            })
    if not karten:
        raise SystemExit("Keine Vokabeln gefunden.")
    return karten


def main():
    csv_pfad = finden("vokabeln.csv", "iphone")
    html_pfad = finden("index.html", "iphone")
    karten = karten_lesen(csv_pfad)
    daten = json.dumps(karten, ensure_ascii=False, separators=(",", ":"))

    html = html_pfad.read_text(encoding="utf-8")
    neu, treffer = re.subn(r"const VOKABELN = \[.*?\];",
                           "const VOKABELN = " + daten.replace("\\", "\\\\") + ";",
                           html, count=1, flags=re.S)
    if treffer != 1:
        raise SystemExit("Zeile 'const VOKABELN = [...];' in index.html nicht gefunden.")
    html_pfad.write_text(neu, encoding="utf-8")
    print(f"{len(karten)} Karten in {html_pfad} geschrieben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
