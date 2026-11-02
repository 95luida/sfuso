# Sfuso · piano anti jet lag

**Rimettiti in fuso.** Sfuso è un sito statico gratuito che crea un piano anti jet lag giorno per giorno: quando dormire, quando cercare o evitare la luce, fino a quando bere caffè, quando dormire in aereo, con esportazione nel calendario (.ics). Tutto il calcolo avviene nel browser: nessun dato viene inviato a un server.

👉 **https://www.dalpuntoweb.it/jet-lag/** — anche in [English](https://www.dalpuntoweb.it/jet-lag/en/), [Español](https://www.dalpuntoweb.it/jet-lag/es/), [Français](https://www.dalpuntoweb.it/jet-lag/fr/) e [Deutsch](https://www.dalpuntoweb.it/jet-lag/de/).

*A free, static jet lag planner: day-by-day sleep, light and caffeine schedule, in-flight sleep and calendar export. Everything runs in the browser. Available in 5 languages.*

## Cosa c'è
- **Calcolatore** con quadranti delle 24 ore per ogni giorno, voto di gravità, giudizio sull'orario di arrivo, modalità viaggio breve (1-3 giorni) ed esportazione `.ics`.
- **24 pagine meta** per lingua, con partenza dalla città di casa (Milano, Londra, Madrid, Parigi, Francoforte), fuso in inverno e in estate e orario di arrivo migliore.
- **Classifica** delle rotte con più jet lag.
- **4 strumenti**: convertitore di fusi orari, pianificatore di riunioni, calcolatore del sonno, ora nel mondo con la zona di notte in tempo reale sulla mappa.
- **6 guide**: bambini, voli notturni, viaggi di lavoro, melatonina e caffè, rientro a casa, luce.

## Il modello
Il minimo della temperatura corporea cade circa 2 ore prima della sveglia abituale. La luce nelle ore dopo quel punto anticipa l'orologio biologico, quella nelle ore prima lo ritarda. Verso est si anticipa di circa 1 ora al giorno, verso ovest si ritarda di circa 1,5 ore; oltre 9-10 ore verso est conviene ritardare. Fonti: Eastman & Burgess, *How To Travel the World Without Jet lag*, Sleep Medicine Clinics 2009; Herxheimer & Petrie, revisione Cochrane sulla melatonina, 2002.

Il piano dà indicazioni generali e non sostituisce il parere di un medico.

## Struttura
```
src/
  assets/      core.js (fusi, modello, mappa, .ics) · calc.js · tools.js · site.js · style.css · map.svg
  i18n/        it.json en.json es.json fr.json de.json (testi, indirizzi, nomi delle città)
  cities.py    città con fuso IANA e coordinate, mete con pagina propria
  guide*.json  guide per lingua
tools/
  build.py     genera site/jet-lag/ in tutte le lingue (hreflang, sitemap, JSON-LD)
  map.py       mappa del mondo a punti da world-atlas (Natural Earth)
vendor/        land-110m.json (world-atlas, ISC · dati Natural Earth, pubblico dominio)
```

## Generare il sito
Serve Python 3.12 o più recente:
```bash
python3 tools/map.py      # solo se cambi la mappa
python3 tools/build.py    # scrive site/jet-lag/
python3 -m http.server 5241 --directory site   # poi apri http://localhost:5241/jet-lag/
```
Per aggiungere una lingua basta un nuovo `src/i18n/<lingua>.json` con le stesse chiavi di `it.json` e un `src/guide.<lingua>.json`.

## Licenza
Codice sotto licenza [MIT](LICENSE). Progetto indipendente di Luigi · [dal punto web](https://www.dalpuntoweb.it/).
