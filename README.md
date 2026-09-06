# Vokabeltrainer Spanisch → Deutsch (A1 + A2)

1674 Karten. Der Wortschatz der Goethe-Wortlisten A1 und A2 ist vollständig abgedeckt
(1356 von 1362 Lemmata; die restlichen sechs sind Wortstämme wie `all` oder `best`, die
als Vollform enthalten sind).

Zwei Fassungen, eine gemeinsame Quelle:

| Datei | Zweck |
|---|---|
| `vokabeltrainer.py` | Desktop-Programm (tkinter), kein Browser |
| `index.html` | Web-App fürs iPhone, Karten fest eingebettet |
| `vokabeln.csv` | einzige Quelle für beide |
| `build_ios.py` | schreibt die Karten aus der CSV neu in `index.html` |
| `manifest.webmanifest`, `sw.js`, `icon-*.png` | Home-Screen-Symbol und Offline-Betrieb |

## Inhalt

| Kartentyp | Anzahl |
|---|---|
| Nomen (Artikel + Plural) | 929 |
| Verben (Kasus + Perfekt + Beispielsatz) | 300 |
| Adjektive | 189 |
| Adverbien | 86 |
| Lückensätze (Funktionswörter) | 84 |
| Zahlen | 38 |
| Redemittel | 24 |
| Konnektoren und Präpositionen | 24 |

Nach Niveau: 759 A1, 572 A2, 343 darüber hinaus.

Unten links stehen zwei Filter. **nivel** schaltet zwischen `todo`, `A1` und `A2`.
**tema** wählt eines von 31 Themengebieten, jeweils mit Kartenzahl — von `Verben (300)`
über `Essen (95)` bis `Farben (11)`. `todos` mischt alles zufällig durch. Beide Filter
wirken zusammen; ergibt eine Kombination keine Karten (etwa `Zahlen` + `A2`), meldet das
Programm das statt eine leere Runde zu starten. Die Themenliste wird aus der Spalte
`thema` erzeugt — ein neues Thema in der CSV erscheint automatisch im Menü.

## Vier Kartentypen

**Wortkarte** — spanisches Wort, deutsches Wort tippen. Bei Nomen erscheint Artikel und
Plural, bei Verben der Kasus (Akkusativ, Dativ, Dativ + Akkusativ, feste Präposition,
Modalverb, ohne Objekt), das Perfekt und ein Beispielsatz.

**Lückensatz** — für Funktionswörter, bei denen eine reine Übersetzung nichts bringt:

```
Kannst du ___ bitte helfen?          a mí (dativo)
→  mir          Personalpronomen Dativ
```

Vorgelesen wird der vollständige Satz.

**Zahlkarte** — Ziffer vorn, Schreibweise hinten. `17 → siebzehn`, `21 → einundzwanzig`.

**Redemittel** — ganze Wendungen: `Lo siento → Es tut mir leid`.

## Start am PC

```
C:\Python314\python.exe vokabeltrainer.py
```

`vokabeltrainer.py` und `vokabeln.csv` im selben Ordner lassen. `fortschritt.json` und
`audio\` legt das Programm selbst an.

Enter prüft die Antwort und springt zur nächsten Karte. Für ä ö ü ß gibt es Knöpfe unter
dem Eingabefeld; Eingaben ohne Umlaute (`Kueche`, `gross`) gelten ebenfalls als richtig,
weil die spanische Tastatur kein ä hat.

## Aussprache

Das Programm liest **nie** mit einer englischen Stimme vor. Ohne deutsche Stimme bleibt es
stumm und zeigt einen Hinweis.

**PC, empfohlen:**

```
C:\Python314\python.exe -m pip install edge-tts
```

Danach stehen die neuronalen de-DE-Stimmen Katja, Conrad, Amala und Killian zur Wahl.
Das erste Vorlesen eines Wortes braucht Internet, danach liegt die Datei in `audio\`.
Offline-Alternative: Settings → Time & language → Speech → Manage voices → *German (Germany)*.

**iPhone:** Einstellungen → Bedienungshilfen → Gesprochene Inhalte → Stimmen → Deutsch.
Die Siri-Stimmen (Helena, Martin) klingen deutlich besser als Anna. iOS spricht erst nach
einer Berührung — deshalb kommt der Ton beim Tippen auf *Comprobar*.

## iPhone-Fassung veröffentlichen

Alle Dateien liegen im Wurzelverzeichnis des Repos, GitHub Pages ist auf `main` / `(root)`
gestellt. Adresse:

```
https://sebastiankaspar.github.io/Deutsch-Vokabeln/
```

In **Safari** öffnen → Teilen → Zum Home-Bildschirm. Ab dem zweiten Start ohne Internet
nutzbar. `sw.js` holt `index.html` immer frisch aus dem Netz, sobald eine Verbindung
besteht — ein Update ist also nach dem Push sofort da.

## Wiederholungslogik

Leitner-Kasten mit fünf Fächern. Richtig → nächstes Fach, Wiedervorlage nach
0 / 1 / 3 / 7 / 21 Tagen. Falsch → zurück auf Fach 1. „Fast" (ein Tippfehler oder ein
falscher Artikel) lässt das Fach stehen. Eine Runde umfasst 20 Karten: erst die fälligen,
aufsteigend nach Fach, dann mit neuen aufgefüllt.

Der Fortschritt am PC (`fortschritt.json`) und auf dem iPhone (Safari-Speicher) sind
getrennt, es gibt keine Synchronisation.

## Wortschatz erweitern

`vokabeln.csv` mit Excel öffnen — Semikolon-getrennt, UTF-8 mit BOM — und Zeilen anhängen.

| Spalte | Inhalt |
|---|---|
| `typ` | nomen / verb / adjektiv / adverb / konnektor / praeposition / luecke / zahl / wendung |
| `es` | spanische Vorderseite, muss eindeutig sein |
| `art` | der / die / das (nur Nomen) |
| `de` | deutsche Lösung |
| `plural` | Pluralform oder `nur Singular` / `nur Plural` |
| `kasus` | `Akkusativ`, `Dativ`, `Dativ + Akkusativ`, `warten auf + Akkusativ`, `Modalverb`, `ohne Objekt`; bei Lückenkarten der Grammatikhinweis |
| `perfekt` | `hat gekauft`, `ist gefahren` |
| `bsp` | Beispielsatz, wird auf Knopfdruck vorgelesen |
| `alt` | weitere gültige Antworten, mit `\|` getrennt |
| `thema` | frei |
| `satz` | Lückensatz mit `___` an der Stelle der Lösung; leer bei Wortkarten |
| `niveau` | `A1`, `A2` oder `extra` |

Kein Semikolon in den Textfeldern. Danach:

```
C:\Python314\python.exe build_ios.py
git add . ; git commit -m "neue Woerter" ; git push
```

Die Karten-IDs hängen an der Zeilennummer. Zeilen anhängen ist unproblematisch —
Zeilen löschen oder umsortieren verschiebt die IDs und setzt den Fortschritt zurück.

## .exe für den PC bauen

```
C:\Python314\python.exe -m pip install pyinstaller edge-tts
C:\Python314\python.exe -m PyInstaller --onefile --noconsole --name Vokabeltrainer ^
  --add-data "vokabeln.csv;." --collect-all edge_tts vokabeltrainer.py
```

`Vokabeltrainer.exe` aus `dist\` zusammen mit `vokabeln.csv` weitergeben.
