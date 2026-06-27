# 🏨 Caciorgna Hotel

Gestionale prenotazioni per tre strutture dello stesso proprietario, in **un'unica pagina
scorrevole** ottimizzata per smartphone (in particolare iPhone).

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
