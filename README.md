# 🏨 Caciorgna Hotels

Gestionale prenotazioni per tre strutture dello stesso proprietario, in **un'unica pagina
scorrevole** ottimizzata per smartphone (in particolare iPhone) e desktop.

- **Hotel Il Faro** — 17 camere (11–27): 12 doppie + 5 triple (la 27 anche quadrupla)
- **Palazzo Caciorgna** — 5 camere: 2 doppie + 3 triple
- **Villa del Cavaliere** — 6 camere: 5 doppie + 1 tripla

## Funzioni
- Vista **settimanale** a griglia (lun–dom) con riquadri **verde = libera** / **rosso = occupata**
- Selettore data/settimana a inizio pagina (dal 2026 in poi)
- Form prenotazione: intestatario (privato o ditta), telefono, email, tipo di uso, **deroga prezzo**
- **KPI incassi** in tempo reale: giorno · settimana · mese · anno
- Salvataggio persistente su `data/prenotazioni.csv`
- Elenco prenotazioni con eliminazione

## Avvio locale
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy su Streamlit Community Cloud
1. Carica la repo su GitHub.
2. Su share.streamlit.io collega la repo e indica `app.py`.

> ⚠️ **Persistenza dati**: su Streamlit Cloud il filesystem è effimero e si azzera ad ogni
> riavvio. Per conservare le prenotazioni a lungo termine, collega un archivio esterno
> (es. Google Sheets, un database, oppure il pattern *GitHub Actions → commit del CSV*).
> Il codice è già predisposto: tutta la lettura/scrittura passa da `carica_prenotazioni()`
> e `salva_prenotazioni()`, facili da reindirizzare verso un backend persistente.

## Listino standard (a notte)
| Struttura | Singola | Doppia | Tripla | Quadrupla |
|---|---|---|---|---|
| Hotel Il Faro | 45 € | 60 € | 75 € | 90 € |
| Palazzo Caciorgna | 50 € | 70 € | 90 € | — |
| Villa del Cavaliere | 50 € | 70 € | 80 € | — |

La deroga prezzo nel form sovrascrive la tariffa standard per la singola prenotazione.

## 📱 Icona app (rosso / giallo)
Nella cartella `assets/` trovi l'icona del brand pronta da salvare sullo smartphone:
- `caciorgna-icon-rounded-1024.png` — versione con angoli arrotondati (sembra un'app)
- `caciorgna-icon-1024.png` — versione quadrata piena (iOS/Android applicano la loro maschera)
- `apple-touch-icon-180.png`, `icon-512.png`, `icon-192.png` — formati per browser/PWA

**Aggiungere alla schermata Home dello smartphone**
- *iPhone (Safari):* apri l'app web → tasto **Condividi** → **Aggiungi a Home**. Per usare
  l'icona del brand come immagine dell'icona, salva prima `caciorgna-icon-rounded-1024.png`
  nelle Foto e impostala come immagine quando richiesto, oppure pubblica gli asset insieme
  all'app (vedi nota PWA sotto).
- *Android (Chrome):* menu **⋮** → **Aggiungi a schermata Home** / **Installa app**.

`assets/manifest.json` è già pronto: collegandolo nell'`<head>` (tramite un piccolo wrapper
HTML o un reverse proxy) lo smartphone userà automaticamente l'icona rossa come icona dell'app.
L'icona compare anche nella scheda del browser perché è impostata come `page_icon`.

