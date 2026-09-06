# Vokabeltrainer ES → DE (A2)

Standalone-Desktop-Programm (tkinter), kein Browser. 336 Karten: 210 Nomen mit Artikel
und Plural, 78 Verben mit Kasus, 38 Adjektive, 10 Adverbien.

## Start

```
C:\Python314\python.exe vokabeltrainer.py
```

Alle drei Dateien im selben Ordner lassen. `fortschritt.json` und `audio\` legt das
Programm selbst an.

## Aussprache — Hochdeutsch erzwingen

Das Programm liest **nie** mit einer englischen Stimme vor. Findet es keine deutsche
Stimme, bleibt es stumm und zeigt den Hinweis in der Fusszeile.

**Empfohlen (neuronale de-DE-Stimme, klingt nahezu muttersprachlich):**

```
C:\Python314\python.exe -m pip install edge-tts
```

Danach stehen Katja, Conrad, Amala und Killian in der Auswahl unten links. Braucht beim
ersten Vorlesen eines Wortes Internet; die Datei landet in `audio\` und wird danach
offline wiederverwendet. Sprechtempo ist auf −10 % gesetzt.

**Offline-Alternative (Windows-Systemstimme, robotischer):**
Settings → Time & language → Speech → Manage voices → Add voices → *German (Germany)*.
Danach Windows neu starten. Erscheint die Stimme in den Windows-Einstellungen, aber nicht
in der Auswahl des Programms, ist sie nur als OneCore-Stimme registriert und für SAPI5
unsichtbar — dann bei edge-tts bleiben.

Mit dem Knopf **probar** die gewählte Stimme prüfen.

## Echte .exe (ohne Python auf ihrem Rechner)

```
C:\Python314\python.exe -m pip install pyinstaller edge-tts
C:\Python314\python.exe -m PyInstaller --onefile --noconsole --name Vokabeltrainer ^
  --add-data "vokabeln.csv;." --collect-all edge_tts vokabeltrainer.py
```

`Vokabeltrainer.exe` aus `dist\` zusammen mit `vokabeln.csv` weitergeben.

## Wortschatz erweitern

`vokabeln.csv` mit Excel öffnen (Semikolon-getrennt, UTF-8 mit BOM) und Zeilen anhängen.

| Spalte | Inhalt |
|---|---|
| `typ` | nomen / verb / adjektiv / adverb |
| `es` | spanische Vorderseite |
| `art` | der / die / das (nur Nomen) |
| `de` | deutsche Lösung |
| `plural` | Pluralform, oder `nur Singular` / `nur Plural` |
| `kasus` | z. B. `Akkusativ`, `Dativ`, `Dativ + Akkusativ`, `warten auf + Akkusativ`, `ohne Objekt` |
| `perfekt` | `hat gekauft`, `ist gefahren` |
| `bsp` | Beispielsatz (wird auf Knopf vorgelesen) |
| `alt` | weitere gültige Antworten, mit `\|` getrennt |
| `thema` | frei |

Kein Semikolon in den Textfeldern verwenden.

## Bewertung und Wiederholung

`richtig` / `fast` (Artikel oder ein Tippfehler) / `falsch`. Eingaben ohne Umlaute
(`Kueche`, `gross`) gelten als richtig — die spanische Tastatur hat kein ä/ö.
Für ä ö ü ß gibt es Knöpfe unter dem Eingabefeld.

Leitner-Kasten mit 5 Fächern: richtig → nächstes Fach (0 / 1 / 3 / 7 / 21 Tage),
falsch → zurück auf Fach 1. 20 Karten pro Runde, fällige zuerst.
