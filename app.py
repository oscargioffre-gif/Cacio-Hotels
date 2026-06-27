# -*- coding: utf-8 -*-
"""
Caciorgna Hotel — Gestionale prenotazioni per tre strutture.

Singola pagina scorrevole, ottimizzata per smartphone (in particolare iPhone),
con vista settimanale a griglia, inserimento prenotazioni, listino con deroghe
e calcolo incassi (giorno / settimana / mese / anno).

Avvio locale:  streamlit run app.py
Deploy:        compatibile con Streamlit Community Cloud (vedi note sul CSV).
"""

import os
import uuid
import datetime as dt
from calendar import monthrange

import pandas as pd
import streamlit as st

# =============================================================================
# 1. CONFIGURAZIONE PAGINA
# =============================================================================
# Nota: Streamlit accetta solo layout="centered" o "wide".
# "centered" è la scelta migliore per il mobile: limita la larghezza dei
# contenuti rendendoli pieni-schermo su iPhone ed eleganti su desktop.
st.set_page_config(
    page_title="Caciorgna Hotel",
    page_icon="🏨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# 2. COSTANTI: STRUTTURE, CAMERE E LISTINO PREZZI
# =============================================================================
# Tipi di camera usati internamente:
#   "doppia"      -> usabile come singola o doppia
#   "tripla"      -> usabile come singola, doppia o tripla
#   "tripla_quad" -> come la tripla ma usabile anche come quadrupla (camera 27)

# --- Hotel Il Faro: camere 11-27 (17 totali) ---------------------------------
# 12 doppie (11-22) + 5 triple (23-27), la 27 anche quadrupla.
_faro_rooms = {}
for n in range(11, 23):          # 11..22 -> 12 doppie
    _faro_rooms[n] = "doppia"
for n in range(23, 27):          # 23..26 -> 4 triple
    _faro_rooms[n] = "tripla"
_faro_rooms[27] = "tripla_quad"  # 27 -> tripla usabile anche come quadrupla

HOTELS = {
    "Hotel Il Faro": {
        "icona": "🗼",
        "rooms": _faro_rooms,
        # Listino giornaliero per tipo di USO
        "prezzi": {"Singola": 45, "Doppia": 60, "Tripla": 75, "Quadrupla": 90},
    },
    "Palazzo Caciorgna": {
        "icona": "🏛️",
        # 5 camere: 2 doppie (1-2) + 3 triple (3-5)
        "rooms": {1: "doppia", 2: "doppia", 3: "tripla", 4: "tripla", 5: "tripla"},
        "prezzi": {"Singola": 50, "Doppia": 70, "Tripla": 90},
    },
    "Villa del Cavaliere": {
        "icona": "🏰",
        # 6 camere: 5 doppie (1-5) + 1 tripla (6)
        "rooms": {1: "doppia", 2: "doppia", 3: "doppia", 4: "doppia", 5: "doppia", 6: "tripla"},
        "prezzi": {"Singola": 50, "Doppia": 70, "Tripla": 80},
    },
}

# Opzioni di "uso" ammesse in base al tipo fisico della camera.
USI_PER_TIPO = {
    "doppia": ["Singola", "Doppia"],
    "tripla": ["Singola", "Doppia", "Tripla"],
    "tripla_quad": ["Singola", "Doppia", "Tripla", "Quadrupla"],
}

# Etichetta breve del tipo camera (mostrata in griglia).
TIPO_LABEL = {"doppia": "Doppia", "tripla": "Tripla", "tripla_quad": "Tripla/Quad"}

# File di salvataggio persistente.
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "prenotazioni.csv")

# Colonne del CSV / dei record prenotazione.
COLONNE = [
    "id", "hotel", "camera", "tipo_camera", "uso",
    "check_in", "check_out", "tipo_cliente", "intestatario",
    "telefono", "email", "prezzo_notte", "prezzo_standard", "deroga",
    "note", "creato_il",
]

# Giorni della settimana in italiano (abbreviati).
GIORNI_IT = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
MESI_IT = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]


# =============================================================================
# 3. STILE (CSS) — identità visiva e ottimizzazione mobile
# =============================================================================
def inietta_css():
    """Inietta il foglio di stile globale (font, palette, griglia, card)."""
    st.markdown(
        """
        <style>
        /* --- Tipografia: display serif + sans pulito (Google Fonts) --- */
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

        :root{
            --marine:   #0F2A3A;   /* blu marino profondo  */
            --marine-2: #163b50;
            --ottone:   #C7A24A;   /* ottone / oro         */
            --avorio:   #FBF8F3;   /* fondo avorio caldo   */
            --inchiostro:#1B2B34;  /* testo scuro          */
            --libera:   #2E8B6B;   /* verde salvia (libera)*/
            --occupata: #C8553D;   /* terracotta (occupata)*/
        }

        /* Sfondo generale e font del corpo */
        [data-testid="stAppViewContainer"]{
            background: var(--avorio);
        }
        html, body, [data-testid="stAppViewContainer"] *{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: var(--inchiostro);
        }
        /* Margini ridotti in alto per guadagnare spazio su mobile */
        .block-container{ padding-top: 1.2rem; padding-bottom: 3rem; }

        /* --- Testata --- */
        .app-header{
            background: linear-gradient(135deg, var(--marine) 0%, var(--marine-2) 100%);
            border-radius: 18px;
            padding: 22px 20px;
            margin-bottom: 18px;
            box-shadow: 0 8px 24px rgba(15,42,58,.18);
            border: 1px solid rgba(199,162,74,.25);
        }
        .app-header h1{
            font-family: 'Fraunces', serif !important;
            color: #fff !important;
            font-size: 30px; font-weight: 700; margin: 0; letter-spacing: .3px;
        }
        .app-header .pedice{
            color: var(--ottone); font-size: 13px; font-weight: 600;
            text-transform: uppercase; letter-spacing: 2px; margin-top: 4px;
        }

        /* --- Card KPI incassi --- */
        .kpi-grid{ display:flex; flex-wrap:wrap; gap:10px; margin: 4px 0 18px; }
        .kpi-card{
            flex: 1 1 140px;
            background:#fff; border:1px solid #ece5d8; border-left:5px solid var(--ottone);
            border-radius:14px; padding:12px 14px; box-shadow:0 2px 8px rgba(27,43,52,.05);
        }
        .kpi-card .etichetta{ font-size:11px; text-transform:uppercase; letter-spacing:1px;
            color:#7b746a; font-weight:600; }
        .kpi-card .valore{ font-family:'Fraunces',serif; font-size:26px; font-weight:700;
            color:var(--marine); margin-top:2px; }

        /* --- Titolo struttura --- */
        .hotel-titolo{
            font-family:'Fraunces',serif; font-size:21px; font-weight:600;
            color:var(--marine); margin:22px 0 6px; padding-bottom:6px;
            border-bottom:2px solid var(--ottone);
        }
        .hotel-meta{ font-size:12.5px; color:#7b746a; margin:-2px 0 10px; }

        /* --- Griglia settimanale --- */
        .grid-wrap{ overflow-x:auto; -webkit-overflow-scrolling:touch;
            border-radius:14px; border:1px solid #ece5d8; background:#fff;
            box-shadow:0 2px 8px rgba(27,43,52,.05); margin-bottom:6px; }
        table.week-grid{ border-collapse:separate; border-spacing:4px; padding:6px;
            width:100%; min-width:520px; }
        table.week-grid th{
            font-size:11px; font-weight:600; color:#5b5750; text-align:center;
            padding:4px 2px; line-height:1.15; white-space:nowrap;
        }
        table.week-grid td.room-col, table.week-grid th.room-col{
            text-align:left; white-space:nowrap; position:sticky; left:0;
            background:#fff; z-index:2; padding-left:6px;
        }
        table.week-grid td.room-col{
            font-size:12px; font-weight:600; color:var(--marine);
            border-right:1px solid #eee;
        }
        table.week-grid td.room-col small{ display:block; color:#9a948a; font-weight:500; font-size:10px; }
        /* Celle stato camera */
        .cell{ border-radius:9px; text-align:center; font-size:10.5px; font-weight:600;
            padding:8px 4px; min-width:58px; color:#fff; line-height:1.1; }
        .cell.free{ background:var(--libera); }
        .cell.occ{ background:var(--occupata); }
        .cell .nome{ display:block; font-weight:700; font-size:10.5px;
            white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:62px; }
        .cell .uso{ display:block; font-size:9px; opacity:.9; font-weight:500; }

        /* Riepilogo libere/occupate sotto la griglia */
        .occ-sum{ font-size:12px; color:#5b5750; margin:4px 2px 2px; }
        .occ-sum b.lib{ color:var(--libera); } .occ-sum b.occ{ color:var(--occupata); }

        /* Bottoni Streamlit in tinta */
        .stButton>button{ border-radius:10px; font-weight:600; }
        div[data-testid="stForm"]{ border:1px solid #ece5d8; border-radius:14px;
            background:#fff; padding:6px 14px 4px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 4. PERSISTENZA DEI DATI (CSV + session_state)
# =============================================================================
def carica_prenotazioni():
    """Carica le prenotazioni dal CSV (se esiste) come lista di dizionari."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype=str).fillna("")
            records = df.to_dict("records")
            # Conversione dei tipi (CSV salva tutto come stringa).
            for r in records:
                r["camera"] = int(float(r["camera"]))
                r["prezzo_notte"] = float(r["prezzo_notte"])
                r["prezzo_standard"] = float(r.get("prezzo_standard") or 0)
                r["deroga"] = str(r.get("deroga")).lower() in ("true", "1", "vero")
            return records
        except Exception as e:
            st.warning(f"Impossibile leggere il file dati: {e}")
            return []
    return []


def salva_prenotazioni():
    """Scrive su CSV lo stato corrente delle prenotazioni (salvataggio persistente)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    df = pd.DataFrame(st.session_state.prenotazioni, columns=COLONNE)
    df.to_csv(DATA_FILE, index=False)


# =============================================================================
# 5. FUNZIONI DI SUPPORTO (date, prezzi, occupazione, incassi)
# =============================================================================
def a_data(s):
    """Converte una stringa ISO (YYYY-MM-DD) in oggetto date."""
    if isinstance(s, dt.date):
        return s
    return dt.date.fromisoformat(str(s))


def inizio_settimana(d):
    """Restituisce il lunedì della settimana che contiene la data d."""
    return d - dt.timedelta(days=d.weekday())


def giorni_settimana(d):
    """Lista dei 7 giorni (lun->dom) della settimana che contiene d."""
    lun = inizio_settimana(d)
    return [lun + dt.timedelta(days=i) for i in range(7)]


def prezzo_standard(hotel, uso):
    """Tariffa standard a notte per un certo uso nella struttura indicata."""
    return float(HOTELS[hotel]["prezzi"].get(uso, 0))


def camera_occupata_il(hotel, camera, giorno):
    """Restituisce la prenotazione che occupa hotel/camera in quel giorno, o None.

    Convenzione alberghiera: si pagano le notti da check_in (incluso) a
    check_out (escluso). Il giorno di check_out la camera torna libera.
    """
    for p in st.session_state.prenotazioni:
        if p["hotel"] == hotel and int(p["camera"]) == int(camera):
            if a_data(p["check_in"]) <= giorno < a_data(p["check_out"]):
                return p
    return None


def c_e_sovrapposizione(hotel, camera, check_in, check_out, escludi_id=None):
    """True se esiste già una prenotazione che si sovrappone alle date indicate."""
    for p in st.session_state.prenotazioni:
        if escludi_id and p["id"] == escludi_id:
            continue
        if p["hotel"] == hotel and int(p["camera"]) == int(camera):
            if a_data(p["check_in"]) < check_out and check_in < a_data(p["check_out"]):
                return True
    return False


def incasso_intervallo(inizio, fine):
    """Incasso totale nelle notti comprese in [inizio, fine) (fine esclusa)."""
    totale = 0.0
    for p in st.session_state.prenotazioni:
        ci, co = a_data(p["check_in"]), a_data(p["check_out"])
        s = max(ci, inizio)
        e = min(co, fine)
        notti = (e - s).days
        if notti > 0:
            totale += notti * float(p["prezzo_notte"])
    return totale


def euro(x):
    """Formatta un importo in stile italiano: 1.234 €."""
    return f"{x:,.0f} €".replace(",", ".")


# =============================================================================
# 6. COSTRUZIONE HTML DELLA GRIGLIA SETTIMANALE
# =============================================================================
def abbrevia(nome, n=9):
    """Abbrevia un nome lungo per la cella (con puntini di sospensione)."""
    nome = (nome or "").strip()
    return nome if len(nome) <= n else nome[: n - 1] + "…"


def griglia_hotel_html(hotel, settimana):
    """Genera la tabella HTML (verde=libera / rosso=occupata) per una struttura."""
    rooms = HOTELS[hotel]["rooms"]

    # Intestazione con i 7 giorni.
    html = '<div class="grid-wrap"><table class="week-grid"><tr>'
    html += '<th class="room-col">Camera</th>'
    for d in settimana:
        html += f'<th>{GIORNI_IT[d.weekday()]}<br>{d.strftime("%d/%m")}</th>'
    html += "</tr>"

    # Una riga per camera.
    for camera, tipo in rooms.items():
        html += (
            f'<tr><td class="room-col">N. {camera}'
            f'<small>{TIPO_LABEL[tipo]}</small></td>'
        )
        for d in settimana:
            p = camera_occupata_il(hotel, camera, d)
            if p:
                nome = abbrevia(p["intestatario"])
                html += (
                    f'<td><div class="cell occ" title="{p["intestatario"]} — {p["uso"]}">'
                    f'<span class="nome">{nome}</span>'
                    f'<span class="uso">{p["uso"]}</span></div></td>'
                )
            else:
                html += '<td><div class="cell free">libera</div></td>'
        html += "</tr>"

    html += "</table></div>"
    return html


# =============================================================================
# 7. INIZIALIZZAZIONE STATO
# =============================================================================
def init_stato():
    if "prenotazioni" not in st.session_state:
        st.session_state.prenotazioni = carica_prenotazioni()


# =============================================================================
# 8. SEZIONI DELL'INTERFACCIA
# =============================================================================
def sezione_testata():
    st.markdown(
        """
        <div class="app-header">
            <h1>🏨 Caciorgna Hotel</h1>
            <div class="pedice">Gestione · Il Faro · Palazzo Caciorgna · Villa del Cavaliere</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sezione_kpi(giorno):
    """Calcola e mostra i 4 KPI di incasso (giorno/settimana/mese/anno)."""
    sett = giorni_settimana(giorno)
    lun, dom_next = sett[0], sett[-1] + dt.timedelta(days=1)

    # Mese del giorno selezionato.
    primo_mese = giorno.replace(day=1)
    ultimo_giorno = monthrange(giorno.year, giorno.month)[1]
    fine_mese = primo_mese + dt.timedelta(days=ultimo_giorno)
    # Anno del giorno selezionato.
    primo_anno = dt.date(giorno.year, 1, 1)
    fine_anno = dt.date(giorno.year + 1, 1, 1)

    inc_giorno = incasso_intervallo(giorno, giorno + dt.timedelta(days=1))
    inc_sett = incasso_intervallo(lun, dom_next)
    inc_mese = incasso_intervallo(primo_mese, fine_mese)
    inc_anno = incasso_intervallo(primo_anno, fine_anno)

    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="etichetta">Incasso giorno</div>
                <div class="valore">{euro(inc_giorno)}</div>
            </div>
            <div class="kpi-card">
                <div class="etichetta">Settimana</div>
                <div class="valore">{euro(inc_sett)}</div>
            </div>
            <div class="kpi-card">
                <div class="etichetta">{MESI_IT[giorno.month - 1]}</div>
                <div class="valore">{euro(inc_mese)}</div>
            </div>
            <div class="kpi-card">
                <div class="etichetta">Anno {giorno.year}</div>
                <div class="valore">{euro(inc_anno)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sezione_form_prenotazione(giorno_default):
    """Form dedicato per inserire una nuova prenotazione."""
    with st.expander("➕  Nuova prenotazione", expanded=False):

        # Selettori fuori dal form: servono a far reagire l'interfaccia
        # (l'elenco usi e il prezzo standard dipendono da hotel/camera/uso).
        c1, c2 = st.columns(2)
        hotel = c1.selectbox("Struttura", list(HOTELS.keys()), key="f_hotel")
        rooms = HOTELS[hotel]["rooms"]
        camera = c2.selectbox(
            "Camera",
            list(rooms.keys()),
            format_func=lambda n: f"N. {n} ({TIPO_LABEL[rooms[n]]})",
            key="f_camera",
        )
        tipo = rooms[camera]
        usi = USI_PER_TIPO[tipo]
        uso = st.selectbox("Tipo di uso", usi, key="f_uso")

        prezzo_std = prezzo_standard(hotel, uso)
        st.caption(f"Tariffa standard a notte: **{euro(prezzo_std)}**")

        with st.form("form_prenotazione", clear_on_submit=True):
            c3, c4 = st.columns(2)
            check_in = c3.date_input(
                "Check-in", value=giorno_default,
                min_value=dt.date(2026, 1, 1), key="f_in",
            )
            check_out = c4.date_input(
                "Check-out", value=giorno_default + dt.timedelta(days=1),
                min_value=dt.date(2026, 1, 1), key="f_out",
            )

            tipo_cliente = st.radio(
                "Tipologia cliente", ["Privato", "Ditta"],
                horizontal=True, key="f_tipo_cliente",
            )
            intestatario = st.text_input(
                "Cognome e Nome  /  Ragione sociale", key="f_intestatario",
                placeholder="Es. Rossi Mario  oppure  Rossi S.r.l.",
            )

            c5, c6 = st.columns(2)
            telefono = c5.text_input("Telefono", key="f_tel", placeholder="+39 ...")
            email = c6.text_input("Email", key="f_email", placeholder="nome@dominio.it")

            # --- Deroga prezzo ---
            applica_deroga = st.checkbox("Applica deroga prezzo (tariffa manuale)", key="f_deroga")
            prezzo_deroga = st.number_input(
                "Prezzo a notte derogato (€)",
                min_value=0.0, step=5.0, value=float(prezzo_std),
                disabled=not applica_deroga, key="f_prezzo_deroga",
            )

            note = st.text_area("Note (facoltative)", key="f_note", height=70)

            inviato = st.form_submit_button("💾  Salva prenotazione", use_container_width=True)

        if inviato:
            # --- Validazioni ---
            if not intestatario.strip():
                st.error("Inserisci il nominativo o la ragione sociale.")
                return
            if check_out <= check_in:
                st.error("Il check-out deve essere successivo al check-in.")
                return
            if c_e_sovrapposizione(hotel, camera, check_in, check_out):
                st.error(
                    f"La camera N. {camera} di {hotel} è già prenotata in queste date."
                )
                return

            prezzo_notte = float(prezzo_deroga) if applica_deroga else prezzo_std

            nuova = {
                "id": uuid.uuid4().hex[:8],
                "hotel": hotel,
                "camera": int(camera),
                "tipo_camera": tipo,
                "uso": uso,
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "tipo_cliente": tipo_cliente,
                "intestatario": intestatario.strip(),
                "telefono": telefono.strip(),
                "email": email.strip(),
                "prezzo_notte": prezzo_notte,
                "prezzo_standard": prezzo_std,
                "deroga": bool(applica_deroga),
                "note": note.strip(),
                "creato_il": dt.datetime.now().isoformat(timespec="seconds"),
            }
            st.session_state.prenotazioni.append(nuova)
            salva_prenotazioni()
            notti = (check_out - check_in).days
            st.success(
                f"Prenotazione salvata: {intestatario.strip()} — N. {camera} "
                f"({uso}), {notti} notti, totale {euro(notti * prezzo_notte)}."
            )


def sezione_griglie(giorno):
    """Mostra, struttura per struttura, la griglia settimanale verde/rosso."""
    settimana = giorni_settimana(giorno)
    lun, dom = settimana[0], settimana[-1]
    st.markdown(
        f"#### 📅 Settimana dal {lun.strftime('%d/%m/%Y')} al {dom.strftime('%d/%m/%Y')}"
    )

    for hotel, conf in HOTELS.items():
        rooms = conf["rooms"]
        n_doppie = sum(1 for t in rooms.values() if t == "doppia")
        n_triple = sum(1 for t in rooms.values() if t.startswith("tripla"))

        st.markdown(
            f'<div class="hotel-titolo">{conf["icona"]} {hotel}</div>'
            f'<div class="hotel-meta">{len(rooms)} camere · '
            f'{n_doppie} doppie · {n_triple} triple</div>',
            unsafe_allow_html=True,
        )
        st.markdown(griglia_hotel_html(hotel, settimana), unsafe_allow_html=True)

        # Riepilogo libere/occupate per il giorno selezionato.
        occupate = sum(
            1 for c in rooms if camera_occupata_il(hotel, c, giorno) is not None
        )
        libere = len(rooms) - occupate
        st.markdown(
            f'<div class="occ-sum">Il {giorno.strftime("%d/%m")}: '
            f'<b class="lib">{libere} libere</b> · '
            f'<b class="occ">{occupate} occupate</b></div>',
            unsafe_allow_html=True,
        )


def sezione_gestione():
    """Elenco prenotazioni con possibilità di cancellazione."""
    with st.expander("📋  Prenotazioni registrate / Elimina", expanded=False):
        prenotazioni = st.session_state.prenotazioni
        if not prenotazioni:
            st.info("Nessuna prenotazione registrata.")
            return

        # Tabella riassuntiva.
        righe = []
        for p in sorted(prenotazioni, key=lambda x: a_data(x["check_in"])):
            notti = (a_data(p["check_out"]) - a_data(p["check_in"])).days
            righe.append(
                {
                    "Struttura": p["hotel"],
                    "Camera": f'N. {p["camera"]}',
                    "Uso": p["uso"] + (" ⚠️" if p["deroga"] else ""),
                    "Intestatario": p["intestatario"],
                    "Check-in": a_data(p["check_in"]).strftime("%d/%m/%y"),
                    "Check-out": a_data(p["check_out"]).strftime("%d/%m/%y"),
                    "€/notte": euro(p["prezzo_notte"]),
                    "Totale": euro(notti * float(p["prezzo_notte"])),
                }
            )
        st.dataframe(pd.DataFrame(righe), use_container_width=True, hide_index=True)

        # Selezione ed eliminazione.
        opzioni = {
            f'{p["intestatario"]} · {p["hotel"]} N.{p["camera"]} · '
            f'{a_data(p["check_in"]).strftime("%d/%m/%y")}': p["id"]
            for p in prenotazioni
        }
        scelta = st.selectbox("Seleziona una prenotazione da eliminare", list(opzioni.keys()))
        if st.button("🗑️  Elimina prenotazione selezionata"):
            target = opzioni[scelta]
            st.session_state.prenotazioni = [
                p for p in st.session_state.prenotazioni if p["id"] != target
            ]
            salva_prenotazioni()
            st.success("Prenotazione eliminata.")
            st.rerun()


# =============================================================================
# 9. MAIN
# =============================================================================
def main():
    inietta_css()
    init_stato()
    sezione_testata()

    # --- Selettore data/settimana (dal 2026 in poi) ---
    oggi = dt.date.today()
    default = oggi if oggi >= dt.date(2026, 1, 1) else dt.date(2026, 1, 1)
    giorno = st.date_input(
        "Giorno / settimana di riferimento",
        value=default,
        min_value=dt.date(2026, 1, 1),
        format="DD/MM/YYYY",
        help="La griglia mostra la settimana (lun-dom) che contiene questa data.",
    )

    # --- KPI incassi sempre in vista in cima ---
    sezione_kpi(giorno)

    # --- Form di inserimento prenotazione ---
    sezione_form_prenotazione(giorno)

    # --- Griglie settimanali per le tre strutture ---
    sezione_griglie(giorno)

    # --- Gestione/eliminazione prenotazioni ---
    sezione_gestione()

    st.caption(
        "Dati salvati in data/prenotazioni.csv. Su Streamlit Community Cloud il "
        "filesystem è temporaneo: per conservare i dati a lungo termine collega "
        "un database o un repo GitHub (vedi README)."
    )


if __name__ == "__main__":
    main()
