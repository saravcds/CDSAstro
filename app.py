"""Jyotish Workbench - a Streamlit app for Vedic astrology calculations."""
import hmac
import json
import os
import time as _time
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import astro_core as ac
import llm_qa

st.set_page_config(page_title="Jyotish Workbench", page_icon="🪐", layout="wide")


def secret(name: str, default=None):
    """Read a value from Streamlit secrets, falling back to an environment variable."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:  # no secrets file configured
        pass
    return os.environ.get(name, default)


def require_password() -> None:
    """Block the app until the correct password is entered. Fails closed if none is set."""
    expected = secret("APP_PASSWORD")
    if not expected:
        st.error("This app is locked. Set APP_PASSWORD in the app's secrets (or environment) to enable sign-in.")
        st.stop()
    if st.session_state.get("authenticated"):
        return
    st.title("🪐 Jyotish Workbench")
    fails = st.session_state.get("login_fails", 0)
    wait_until = st.session_state.get("login_wait_until", 0.0)
    with st.form("login"):
        pw = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in", type="primary")
    if ok:
        if _time.time() < wait_until:
            st.error(f"Too many attempts. Try again in {int(wait_until - _time.time()) + 1} seconds.")
        elif hmac.compare_digest(pw.encode(), str(expected).encode()):
            st.session_state.authenticated = True
            st.session_state.login_fails = 0
            st.rerun()
        else:
            fails += 1
            st.session_state.login_fails = fails
            if fails >= 5:
                st.session_state.login_wait_until = _time.time() + 30 * (fails - 4)
            st.error("Incorrect password.")
    st.stop()


require_password()

st.markdown("""
<style>
.sc {display:grid; grid-template-columns:repeat(4,1fr); grid-template-rows:repeat(4,minmax(78px,auto));
     gap:0; max-width:460px; border:1px solid rgba(128,128,128,.55); font-size:.92rem;}
.sc-cell {border:1px solid rgba(128,128,128,.45); padding:4px 6px; position:relative;}
.sc-asc {background:rgba(255,166,0,.13);}
.sc-sign {font-size:.7rem; opacity:.65;}
.sc-asctag {font-size:.68rem; font-weight:700; color:#d97706; margin-left:6px;}
.sc-pl {font-weight:600; margin-top:4px; line-height:1.35;}
.sc-center {grid-column:2 / span 2; grid-row:2 / span 2; display:flex; align-items:center;
     justify-content:center; text-align:center; font-weight:600; padding:8px; opacity:.85;
     border:1px solid rgba(128,128,128,.45);}
.small-note {font-size:.8rem; opacity:.7;}
.cards {display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; margin:4px 0 16px;}
.card {border:1px solid rgba(128,128,128,.35); border-left:4px solid rgba(128,128,128,.5);
       border-radius:10px; padding:10px 12px;}
.card.good {border-left-color:#16a34a;} .card.bad {border-left-color:#dc2626;}
.card.mixed {border-left-color:#d97706;}
.card .lbl {font-size:.78rem; opacity:.7;}
.card .val {font-size:1.22rem; font-weight:650; line-height:1.3; word-break:break-word;}
.card .sub {font-size:.8rem; opacity:.75; margin-top:2px;}
</style>
""", unsafe_allow_html=True)

CITIES = {
    "Coimbatore, India": (11.0168, 76.9558, "Asia/Kolkata"),
    "Chennai, India": (13.0827, 80.2707, "Asia/Kolkata"),
    "Madurai, India": (9.9252, 78.1198, "Asia/Kolkata"),
    "Tiruchirappalli, India": (10.7905, 78.7047, "Asia/Kolkata"),
    "Bengaluru, India": (12.9716, 77.5946, "Asia/Kolkata"),
    "Hyderabad, India": (17.3850, 78.4867, "Asia/Kolkata"),
    "Secunderabad, India": (17.4399, 78.4983, "Asia/Kolkata"),
    "Visakhapatnam, India": (17.6868, 83.2185, "Asia/Kolkata"),
    "Vijayawada, India": (16.5062, 80.6480, "Asia/Kolkata"),
    "Kochi, India": (9.9312, 76.2673, "Asia/Kolkata"),
    "Thiruvananthapuram, India": (8.5241, 76.9366, "Asia/Kolkata"),
    "Mumbai, India": (19.0760, 72.8777, "Asia/Kolkata"),
    "Pune, India": (18.5204, 73.8567, "Asia/Kolkata"),
    "Nagpur, India": (21.1458, 79.0882, "Asia/Kolkata"),
    "Ahmedabad, India": (23.0225, 72.5714, "Asia/Kolkata"),
    "Delhi, India": (28.6139, 77.2090, "Asia/Kolkata"),
    "Jaipur, India": (26.9124, 75.7873, "Asia/Kolkata"),
    "Lucknow, India": (26.8467, 80.9462, "Asia/Kolkata"),
    "Chandigarh, India": (30.7333, 76.7794, "Asia/Kolkata"),
    "Dehradun, India": (30.3165, 78.0322, "Asia/Kolkata"),
    "Kolkata, India": (22.5726, 88.3639, "Asia/Kolkata"),
    "Guwahati, India": (26.1445, 91.7362, "Asia/Kolkata"),
    "Silchar, India": (24.8333, 92.7789, "Asia/Kolkata"),
    "Dubai, UAE": (25.2048, 55.2708, "Asia/Dubai"),
    "Abu Dhabi, UAE": (24.4539, 54.3773, "Asia/Dubai"),
    "Port of Spain, Trinidad": (10.6549, -61.5019, "America/Port_of_Spain"),
    "Kingston, Jamaica": (17.9712, -76.7936, "America/Jamaica"),
    "Willemstad, Curaçao": (12.1091, -68.9316, "America/Curacao"),
    "Oranjestad, Aruba": (12.5092, -70.0086, "America/Aruba"),
    "Paramaribo, Suriname": (5.8520, -55.2038, "America/Paramaribo"),
    "Singapore": (1.3521, 103.8198, "Asia/Singapore"),
    "London, UK": (51.5074, -0.1278, "Europe/London"),
    "New York, USA": (40.7128, -74.0060, "America/New_York"),
    "Washington DC, USA": (38.9072, -77.0369, "America/New_York"),
}
OTHER = "Other (enter coordinates)"
TZ_OPTIONS = sorted({v[2] for v in CITIES.values()} | {"UTC", "Asia/Kathmandu", "Asia/Colombo",
                                                         "Europe/Amsterdam", "America/Los_Angeles",
                                                         "America/Chicago", "Australia/Sydney"})
PROFILE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

def load_profiles() -> dict:
    """Profiles come from the PROFILES_JSON secret (private, persistent) and/or a local profiles.json."""
    out = {}
    raw = secret("PROFILES_JSON")
    if raw:
        try:
            out.update(json.loads(raw) if isinstance(raw, str) else dict(raw))
        except Exception:
            st.warning("PROFILES_JSON secret could not be read as JSON.")
    try:
        with open(PROFILE_FILE, encoding="utf-8") as f:
            out.update(json.load(f))
    except Exception:
        pass
    return out


if "profiles" not in st.session_state:
    st.session_state.profiles = load_profiles()
profiles: dict = st.session_state.profiles


def fmt(jd: float, tz: str, with_time: bool = False) -> str:
    d = ac.jd_to_local(jd, tz)
    return d.strftime("%d %b %Y %H:%M") if with_time else d.strftime("%d %b %Y")


def hm(jd: float, tz: str) -> str:
    return ac.jd_to_local(jd, tz).strftime("%H:%M")


with st.sidebar:
    st.title("🪐 Jyotish Workbench")
    names = sorted(profiles)
    sel = st.selectbox("Person", names, index=0 if names else None,
                       placeholder="Add a person below") if names else None

    with st.expander("Add or edit a person", expanded=not names):
        base = profiles.get(sel, {}) if (sel and st.checkbox("Edit selected person", value=False)) else {}
        nm = st.text_input("Name", value=base.get("name", ""))
        bd = st.date_input("Date of birth", value=date.fromisoformat(base["date"]) if base else date(1985, 1, 1),
                           min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY")
        bt = st.time_input("Time of birth (24h)",
                           value=time.fromisoformat(base["time"]) if base else time(12, 0),
                           step=timedelta(minutes=1))
        city_opts = list(CITIES) + [OTHER]
        cidx = city_opts.index(base["place"]) if base.get("place") in CITIES else (len(city_opts) - 1 if base else 0)
        city = st.selectbox("Place of birth", city_opts, index=cidx)
        if city == OTHER:
            c1, c2 = st.columns(2)
            lat = c1.number_input("Latitude (N +)", value=float(base.get("lat", 0.0)), format="%.4f")
            lon = c2.number_input("Longitude (E +)", value=float(base.get("lon", 0.0)), format="%.4f")
            tz_default = base.get("tz", "Asia/Kolkata")
            tz = st.selectbox("Time zone", TZ_OPTIONS,
                              index=TZ_OPTIONS.index(tz_default) if tz_default in TZ_OPTIONS else 0)
            place = st.text_input("Place name", value=base.get("place_name", base.get("place", "")))
        else:
            lat, lon, tz = CITIES[city]
            place = city
            st.caption(f"{lat:.4f}, {lon:.4f} · {tz}")
        if st.button("Save person", type="primary", width="stretch", disabled=not nm.strip()):
            profiles[nm.strip()] = dict(name=nm.strip(), date=bd.isoformat(), time=bt.strftime("%H:%M"),
                                        lat=lat, lon=lon, tz=tz, place=place)
            st.success(f"Saved {nm.strip()}")
            st.rerun()
        if sel and st.button(f"Delete {sel}", width="stretch"):
            profiles.pop(sel, None)
            st.rerun()

    with st.expander("Import / export profiles"):
        up = st.file_uploader("Import profiles.json", type="json")
        if up is not None:
            try:
                data = json.load(up)
                profiles.update(data)
                st.success(f"Imported {len(data)} profile(s)")
            except Exception as e:  # noqa: BLE001
                st.error(f"Could not read file: {e}")
        st.download_button("Download profiles.json", json.dumps(profiles, indent=2),
                           file_name="profiles.json", mime="application/json",
                           width="stretch", disabled=not profiles)
        if st.button("Save to server file", width="stretch", disabled=not profiles):
            try:
                with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                    json.dump(profiles, f, indent=2)
                st.success("Saved. Note: on Streamlit Cloud this file resets on redeploy.")
            except Exception as e:  # noqa: BLE001
                st.error(str(e))

    st.header("Settings")
    ayan = st.selectbox("Ayanamsa", list(ac.AYANAMSAS), index=0)
    node = st.radio("Rahu / Ketu", ["True", "Mean"], horizontal=True)
    year_len = st.selectbox("Dasha year length (days)", [365.25, 365.2425, 360.0], index=0)
    st.divider()
    if st.button("Sign out", width="stretch"):
        for k in ("authenticated", "chats"):
            st.session_state.pop(k, None)
        st.rerun()


@st.cache_data(show_spinner=False)
def chart_for(name, d_iso, t_str, tz, lat, lon, place, ayan, node):
    dt = datetime.fromisoformat(f"{d_iso}T{t_str}")
    return ac.compute_chart(name, dt, tz, lat, lon, place, ayan, node)


@st.cache_data(show_spinner=False)
def dashas_for(key, _ch, yl):
    return ac.vimshottari(_ch, yl, depth=3)


@st.cache_data(show_spinner=False)
def yogini_for(key, _ch, yl):
    return ac.yogini_dasha(_ch, yl, cycles=3)


def get_chart(p: dict) -> ac.Chart:
    return chart_for(p["name"], p["date"], p["time"], p["tz"], float(p["lat"]), float(p["lon"]),
                     p.get("place", ""), ayan, node)


def chart_key(p: dict) -> tuple:
    return (p["name"], p["date"], p["time"], p["tz"], p["lat"], p["lon"], ayan, node, year_len)


SOUTH_LAYOUT = [[11, 0, 1, 2], [10, None, None, 3], [9, None, None, 4], [8, 7, 6, 5]]


def south_chart(placements: dict, retro: set, title: str) -> str:
    asc = placements["Asc"]
    cells = {i: [] for i in range(12)}
    for p in ac.PLANETS:
        lab = ac.ABBR[p] + ("<sup>R</sup>" if p in retro else "")
        cells[placements[p]].append(lab)
    html = ['<div class="sc">']
    for r, row in enumerate(SOUTH_LAYOUT):
        for c, s in enumerate(row):
            if s is None:
                if r == 1 and c == 1:
                    html.append(f'<div class="sc-center">{title}</div>')
                continue
            cls = "sc-cell sc-asc" if s == asc else "sc-cell"
            tag = '<span class="sc-asctag">Asc</span>' if s == asc else ""
            html.append(f'<div class="{cls}" style="grid-row:{r + 1};grid-column:{c + 1}">'
                        f'<span class="sc-sign">{ac.SIGN_SHORT[s]}</span>{tag}'
                        f'<div class="sc-pl">{" ".join(cells[s])}</div></div>')
    html.append("</div>")
    return "".join(html)


def cards(items: list) -> None:
    """items: (label, value, sub, tone) with tone in good/bad/mixed/''."""
    html = ['<div class="cards">']
    for it in items:
        lbl, val, sub, tone = (list(it) + ["", ""])[:4]
        html.append(f'<div class="card {tone}"><div class="lbl">{lbl}</div><div class="val">{val}</div>'
                    f'<div class="sub">{sub}</div></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def hm_d(jd: float, tz: str, d: date) -> str:
    x = ac.jd_to_local(jd, tz)
    return x.strftime("%H:%M") + (" (+1)" if x.date() > d else "")


def location_picker(key: str, default_place: str, default: tuple):
    key = f"{key}_{sel}"
    opts = list(CITIES) + [OTHER]
    idx = opts.index(default_place) if default_place in CITIES else len(opts) - 1
    city = st.selectbox("Location", opts, index=idx, key=f"{key}_city")
    if city == OTHER:
        c1, c2, c3 = st.columns(3)
        la = c1.number_input("Lat", value=float(default[0]), format="%.4f", key=f"{key}_lat")
        lo = c2.number_input("Lon", value=float(default[1]), format="%.4f", key=f"{key}_lon")
        tz = c3.selectbox("Time zone", TZ_OPTIONS,
                          index=TZ_OPTIONS.index(default[2]) if default[2] in TZ_OPTIONS else 0,
                          key=f"{key}_tz")
        return la, lo, tz
    return CITIES[city]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if not sel:
    st.title("Jyotish Workbench")
    st.info("Add a person in the sidebar to begin, or import a profiles.json file.")
    st.stop()

prof = profiles[sel]
ch = get_chart(prof)
tz0 = ch.tz
md_list = dashas_for(chart_key(prof), ch, year_len)
now_jd = ac.to_jd(datetime.now(ZoneInfo(tz0)).replace(tzinfo=None), tz0)
chain = ac.current_chain(md_list, now_jd)

st.title(f"{ch.name}")
st.caption(f"Born {ch.dt_local.strftime('%d %b %Y, %H:%M')} · {ch.place or f'{ch.lat:.2f}, {ch.lon:.2f}'} · "
           f"{ch.tz} · {ayan} ayanamsa {ch.ayan_value:.4f}° · {node} node")

tabs = st.tabs(["Birth chart", "Dashas", "Yogas & Jaimini", "Transits & key dates", "Daily",
                "Muhurta finder", "Compatibility", "Ask AI", "About"])

# ---- Birth chart ------------------------------------------------------------
with tabs[0]:
    P = ch.planets
    moon = P["Moon"]
    cards([("Ascendant", f"{ac.SIGNS[ch.asc_sign]} {ac.fmt_deg(ch.asc)}", ac.NAKSHATRAS[ac.nak_of(ch.asc)]),
           ("Moon sign", ac.SIGNS[moon["sign"]], ac.fmt_deg(moon["lon"])),
           ("Birth star", ac.NAKSHATRAS[moon["nak"]], f"pada {moon['pada']}"),
           ("Current dasha", " – ".join(p.lord for p in chain),
            f"until {fmt(chain[-1].end, tz0)}" if chain else "")])

    col1, col2 = st.columns(2)
    retro = {p for p in ac.PLANETS if P[p]["retro"]}
    with col1:
        st.subheader("D1 Rasi chart")
        st.markdown(south_chart(ac.varga_chart(ch, 1), retro, "Rasi (D1)<br>South Indian"),
                    unsafe_allow_html=True)
    with col2:
        vsel = st.selectbox("Divisional chart", [k for k in ac.VARGAS if k != 1],
                            index=4, format_func=lambda k: ac.VARGAS[k])
        st.subheader(ac.VARGAS[vsel].split(" (")[0])
        st.markdown(south_chart(ac.varga_chart(ch, vsel), retro, ac.VARGAS[vsel].replace(" (", "<br>(")),
                    unsafe_allow_html=True)

    st.subheader("Planets")
    d9 = ac.varga_chart(ch, 9)
    rows = []
    for p in ac.PLANETS:
        d = P[p]
        rows.append({"Planet": p, "Sign": ac.SIGNS[d["sign"]], "Degree": ac.fmt_deg(d["lon"]),
                     "Nakshatra": f"{ac.NAKSHATRAS[d['nak']]} {d['pada']}", "House": d["house"],
                     "Dignity": d["dignity"], "Retro": "R" if d["retro"] else "",
                     "Combust": "C" if d["combust"] else "",
                     "Star lord": d["star_lord"], "Sub lord (KP)": d["sub_lord"],
                     "Sub-sub": d["subsub_lord"], "KP house": d["kp_house"],
                     "Vargottama": "Yes" if d9[p] == d["sign"] else "",
                     "Aspects houses": ", ".join(map(str, ac.aspected_houses(p, d["house"]))),
                     "Function": ac.functional_nature(ch, p)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    with st.expander("Readings (rule-based)", expanded=True):
        st.markdown(f"**Ascendant {ac.SIGNS[ch.asc_sign]}:** {ac.LAGNA_TRAITS[ch.asc_sign]}")
        st.markdown(f"**Moon in {ac.SIGNS[moon['sign']]} (emotional nature):** {ac.LAGNA_TRAITS[moon['sign']]}")
        for p in ac.PLANETS:
            st.markdown("- " + ac.planet_reading(ch, p))

    with st.expander("House lords"):
        st.dataframe(pd.DataFrame([{"House": h, "Sign": ac.SIGNS[(ch.asc_sign + h - 1) % 12],
                                    "Lord": ch.lord_of_house(h),
                                    "Lord placed in house": P[ch.lord_of_house(h)]["house"],
                                    "Themes": ac.HOUSE_THEMES[h]} for h in range(1, 13)]),
                     hide_index=True, width="stretch")

    with st.expander("KP cusps (Placidus)"):
        cr = []
        for i, cl in enumerate(ch.cusps):
            sl, st_l, sub, ss = ac.kp_lords(cl)
            cr.append({"Cusp": i + 1, "Sign": ac.SIGNS[ac.sign_of(cl)], "Degree": ac.fmt_deg(cl),
                       "Nakshatra": ac.NAKSHATRAS[ac.nak_of(cl)], "Sign lord": sl, "Star lord": st_l,
                       "Sub lord": sub, "Sub-sub": ss})
        st.dataframe(pd.DataFrame(cr), hide_index=True, width="stretch")
        st.caption("For strict KP work, choose the KP (Krishnamurti) ayanamsa in Settings.")

# ---- Dashas -----------------------------------------------------------------
with tabs[1]:
    st.subheader("Vimshottari dasha")
    if chain:
        cards([(lvl, p.lord, f"{fmt(p.start, tz0)} → {fmt(p.end, tz0)}")
               for lvl, p in zip(["Mahadasha", "Antardasha", "Pratyantar"], chain)])
        st.markdown(f"**Mahadasha {chain[0].lord}:** {ac.dasha_interpretation(ch, chain[0].lord)}")
        if len(chain) > 1:
            st.markdown(f"**Antardasha {chain[1].lord}:** {ac.dasha_interpretation(ch, chain[1].lord)}")

    md_rows = [{"": "▶" if chain and m is chain[0] else "", "Mahadasha": m.lord,
                "Start": fmt(m.start, tz0), "End": fmt(m.end, tz0),
                "Years": ac.DASHA_YEARS[m.lord]} for m in md_list]
    st.dataframe(pd.DataFrame(md_rows), hide_index=True, width="stretch")
    c1, c2 = st.columns(2)
    md_idx = c1.selectbox("Show antardashas of", range(len(md_list)),
                          index=md_list.index(chain[0]) if chain else 0,
                          format_func=lambda i: f"{md_list[i].lord} ({fmt(md_list[i].start, tz0)[-4:]}–{fmt(md_list[i].end, tz0)[-4:]})")
    md = md_list[md_idx]
    cur_ad = chain[1] if len(chain) > 1 and chain[0] is md else None
    ad_idx = c2.selectbox("Show pratyantars of", range(len(md.children)),
                          index=md.children.index(cur_ad) if cur_ad else 0,
                          format_func=lambda i: f"{md.lord}–{md.children[i].lord}")
    c1.dataframe(pd.DataFrame([{"": "▶" if a is cur_ad else "", "Antardasha": f"{md.lord}–{a.lord}",
                                "Start": fmt(a.start, tz0), "End": fmt(a.end, tz0)} for a in md.children]),
                 hide_index=True, width="stretch")
    ad = md.children[ad_idx]
    cur_pd = chain[2] if len(chain) > 2 and chain[1] is ad else None
    c2.dataframe(pd.DataFrame([{"": "▶" if q is cur_pd else "", "Pratyantar": f"{md.lord}–{ad.lord}–{q.lord}",
                                "Start": fmt(q.start, tz0), "End": fmt(q.end, tz0)} for q in ad.children]),
                 hide_index=True, width="stretch")

    st.subheader("Yogini dasha")
    yd = yogini_for(chart_key(prof), ch, year_len)
    ychain = ac.current_chain(yd, now_jd)
    if ychain:
        st.markdown(f"Current: **{ychain[0].lord}** ({ac.YOGINI_LORD[ychain[0].lord]}) "
                    f"{fmt(ychain[0].start, tz0)} → {fmt(ychain[0].end, tz0)}"
                    + (f" · sub-period **{ychain[1].lord}** ({ac.YOGINI_LORD[ychain[1].lord]}) until "
                       f"{fmt(ychain[1].end, tz0)}" if len(ychain) > 1 else ""))
    with st.expander("All Yogini periods"):
        st.dataframe(pd.DataFrame([{"": "▶" if ychain and y is ychain[0] else "", "Yogini": y.lord,
                                    "Planet": ac.YOGINI_LORD[y.lord], "Start": fmt(y.start, tz0),
                                    "End": fmt(y.end, tz0)} for y in yd]),
                     hide_index=True, width="stretch")

# ---- Yogas & Jaimini --------------------------------------------------------
with tabs[2]:
    yogas = ac.detect_yogas(ch)
    st.subheader("Yogas found")
    for y in [y for y in yogas if y["present"]]:
        st.success(f"**{y['name']}** — {y['meaning']}  \n{y['detail']}")
    with st.expander("Yogas checked but not present"):
        for y in [y for y in yogas if not y["present"]]:
            st.markdown(f"- **{y['name']}**: {y['detail']}")
    st.caption("Automatic yoga detection covers common classical rules only.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Jaimini chara karakas")
        st.dataframe(pd.DataFrame([{"Karaka": k, "Planet": p, "Degree in sign": f"{d:.2f}°"}
                                   for k, p, d in ac.chara_karakas(ch)]),
                     hide_index=True, width="stretch")
    with c2:
        st.subheader("Functional nature")
        st.dataframe(pd.DataFrame([{"Planet": p, "Rules houses": ", ".join(map(str, ch.houses_owned(p))) or "-",
                                    "Nature": ac.functional_nature(ch, p)} for p in ac.PLANETS]),
                     hide_index=True, width="stretch")

    st.subheader("Saturn cycles: Sade Sati, Ashtama and Kantaka Shani")
    ss = ac.sade_sati(ch, 95)
    st.dataframe(pd.DataFrame([{"": "▶" if s["start"] <= now_jd < s["end"] else "", "Phase": s["phase"],
                                "Saturn in": s["sign"], "From": fmt(s["start"], tz0),
                                "To": fmt(s["end"], tz0)} for s in ss]),
                 hide_index=True, width="stretch", height=360)

# ---- Transits -----------------------------------------------------------------
with tabs[3]:
    c1, c2 = st.columns([1, 2])
    tdate = c1.date_input("Transit date", value=date.today(), format="DD/MM/YYYY", key="tr_date")
    tj = ac.to_jd(datetime(tdate.year, tdate.month, tdate.day, 12), tz0)
    st.subheader(f"Planets on {tdate.strftime('%d %b %Y')} (gochara)")
    gr = ac.gochara(ch, tj)
    st.dataframe(pd.DataFrame([{"Planet": r["planet"], "Sign": r["sign"], "Degree": r["degree"],
                                "Nakshatra": r["nakshatra"], "R": "R" if r["retro"] else "",
                                "House from Asc": r["house_from_asc"], "House from Moon": r["house_from_moon"],
                                "Classical result": r["result"]} for r in gr]),
                 hide_index=True, width="stretch")
    st.caption("Classical result uses the house from the natal Moon (gochara phala), without vedha.")

    st.subheader("Key dates ahead")
    months = st.slider("Months ahead", 3, 60, 18)
    with st.spinner("Scanning transits, stations, eclipses and dasha changes..."):
        ev = ac.key_events(ch, tj, months, md_list)
    cats = sorted({e["category"] for e in ev})
    pick = st.multiselect("Show", cats, default=[c for c in cats if "sub-sub" not in c])
    st.dataframe(pd.DataFrame([{"Date": fmt(e["jd"], tz0), "Type": e["category"], "Event": e["event"]}
                               for e in ev if e["category"] in pick]),
                 hide_index=True, width="stretch", height=520)

# ---- Daily --------------------------------------------------------------------
with tabs[4]:
    c1, c2 = st.columns([1, 2])
    dday = c1.date_input("Date", value=date.today(), format="DD/MM/YYYY", key="daily_date")
    with c2:
        la, lo, dtz = location_picker("daily", ch.place, (ch.lat, ch.lon, ch.tz))
    fc = ac.daily_forecast(ch, dday, la, lo, dtz)
    pc = fc["panchang"]
    sc = fc["score"]
    cards([("Day rating", f"{sc}/100", "good day" if sc >= 65 else "mixed day" if sc >= 45 else "careful day",
            "good" if sc >= 65 else "mixed" if sc >= 45 else "bad"),
           ("Tara Bala (midday)", fc["tara"], ac.TARA_MEANING[fc["tara"]],
            {"good": "good", "bad": "bad", "mixed": "mixed"}[fc["tara_quality"]]),
           ("Moon", ac.SIGNS[fc["moon_sign"]],
            f"house {fc['house_from_asc']} from Asc · {fc['house_from_moon']} from Moon"),
           ("Weekday", pc["weekday"], f"lord {pc['vara_lord']}")])
    st.progress(fc["score"] / 100)
    for t in fc["text"]:
        st.markdown(f"- {t}")
    with st.expander("How the rating is built"):
        st.dataframe(pd.DataFrame([{"Factor": w, "Points": p} for w, p in fc["parts"]]),
                     hide_index=True, width="stretch")
        st.caption("Starts at 50. The rating is an indicator built from traditional rules, not a forecast.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Panchang")
        rows = [("Sunrise / sunset", f"{hm(pc['sunrise'], dtz)} / {hm(pc['sunset'], dtz)}")]
        for s, e, v in pc["tithi"]:
            rows.append(("Tithi", f"{ac.tithi_name(v)}  ({hm_d(s, dtz, dday)}–{hm_d(e, dtz, dday)})"))
        for s, e, (tn, tq) in fc["tara_segments"]:
            nk = ac.NAKSHATRAS[next(v for a, b, v in pc["nakshatra"] if a == s)]
            rows.append(("Nakshatra", f"{nk} – {tn} tara  ({hm_d(s, dtz, dday)}–{hm_d(e, dtz, dday)})"))
        for s, e, v in pc["moon_sign_segments"]:
            rows.append(("Moon sign", f"{ac.SIGNS[v]}  ({hm_d(s, dtz, dday)}–{hm_d(e, dtz, dday)})"))
        rows += [("Yoga (at sunrise)", pc["yoga"] + (" (inauspicious)" if pc["yoga"] in ac.BAD_YOGAS else "")),
                 ("Karana (at sunrise)", pc["karana"]),
                 ("Rahu Kalam", f"{hm(pc['rahu_kalam'][0], dtz)}–{hm(pc['rahu_kalam'][1], dtz)}"),
                 ("Yamagandam", f"{hm(pc['yamagandam'][0], dtz)}–{hm(pc['yamagandam'][1], dtz)}"),
                 ("Gulika", f"{hm(pc['gulika'][0], dtz)}–{hm(pc['gulika'][1], dtz)}"),
                 ("Abhijit muhurta", f"{hm(pc['abhijit'][0], dtz)}–{hm(pc['abhijit'][1], dtz)}")]
        st.dataframe(pd.DataFrame(rows, columns=["Item", "Value"]), hide_index=True, width="stretch",
                     height=36 * (len(rows) + 1) + 4)
        st.caption("Times marked (+1) fall after midnight, before the next sunrise.")
    with c2:
        st.subheader("Best windows today")
        if fc["good_windows"]:
            for s, e in fc["good_windows"]:
                st.markdown(f"- **{hm(s, dtz)} – {hm(e, dtz)}**")
        else:
            st.markdown("No window combines a favourable star with no Rahu/Yama/Gulika period. "
                        "Keep the day for routine work.")
        st.caption("Daylight slots outside Rahu Kalam, Yamagandam and Gulika, while the star is favourable for this person.")

    st.subheader("Hour by hour (hora)")
    now_local = datetime.now(ZoneInfo(dtz))
    now_j = ac.to_jd(now_local.replace(tzinfo=None), dtz)
    st.dataframe(pd.DataFrame([{"": "▶" if h["start"] <= now_j < h["end"] else "",
                                "Time": f"{hm(h['start'], dtz)}–{hm(h['end'], dtz)}",
                                "Day/Night": "Day" if h["day"] else "Night", "Hora lord": h["lord"],
                                "Good for": h["good_for"], "For this chart": h["for_you"]}
                               for h in fc["horas"]]),
                 hide_index=True, width="stretch", height=600)

# ---- Muhurta ---------------------------------------------------------------------
with tabs[5]:
    st.subheader("Find good dates and times")
    c1, c2 = st.columns(2)
    purpose = c1.selectbox("Purpose", list(ac.MUHURTA_PURPOSES))
    with c2:
        mla, mlo, mtz = location_picker("muh", ch.place, (ch.lat, ch.lon, ch.tz))
    c1, c2, c3 = st.columns(3)
    d0 = c1.date_input("From", value=date.today(), format="DD/MM/YYYY", key="m_from")
    d1 = c2.date_input("To", value=date.today() + timedelta(days=60), format="DD/MM/YYYY", key="m_to")
    hrs = c3.slider("Hours of day", 5, 21, (8, 18))
    c1, c2, c3, c4 = st.columns(4)
    shukla = c1.checkbox("Waxing moon only")
    ashtami = c2.checkbox("Avoid Ashtami", value=True)
    ecl = c3.number_input("Avoid days around eclipses", 0, 7, 3)
    others = ["(none)"] + [n for n in sorted(profiles) if n != sel]
    sec_name = c4.selectbox("Also good for", others)
    second = get_chart(profiles[sec_name]) if sec_name != "(none)" else None
    if (d1 - d0).days > 400:
        st.warning("Please choose a range of up to about 13 months.")
    elif st.button("Find dates", type="primary"):
        with st.spinner("Searching..."):
            res = ac.find_muhurtas(ch, purpose, d0, d1, mla, mlo, mtz, shukla, ashtami, int(ecl),
                                   second, hrs)
        if not res:
            st.info("No window met every condition. Try a longer range or relax an option.")
        else:
            st.dataframe(pd.DataFrame([{"Date": r["date"].strftime("%a %d %b %Y"),
                                        "Window": f"{hm(r['start'], mtz)}–{hm(r['end'], mtz)}",
                                        "Nakshatra": r["nakshatra"], "Tara": r["tara"], "Tithi": r["tithi"],
                                        "Moon in house": r["moon_house"]} for r in res]),
                         hide_index=True, width="stretch")
    st.caption("Rules: purpose-specific stars, favourable Tara Bala, no Rikta tithi or Amavasya, Moon not in the "
               "8th/12th from the Ascendant or 8th from the Moon, outside Rahu Kalam/Yamagandam/Gulika, "
               "eclipse buffer, and no Mercury retrograde for contracts and property.")

# ---- Compatibility ---------------------------------------------------------------
with tabs[6]:
    others = [n for n in sorted(profiles) if n != sel]
    if not others:
        st.info("Add a second person to compare charts.")
    else:
        c1, c2 = st.columns(2)
        other = c1.selectbox("Compare with", others)
        mode = c2.radio("Type", ["Professional / friendship", "Marriage (Ashtakoota)"], horizontal=True)
        ob = get_chart(profiles[other])
        if mode.startswith("Marriage"):
            groom_is_a = st.radio("Groom", [sel, other], horizontal=True) == sel
            g, b = (ch, ob) if groom_is_a else (ob, ch)
            rows = ac.ashtakoota(g, b)
            total = sum(r["score"] for r in rows)
            verdict = ("Excellent" if total >= 28 else "Good" if total >= 24 else
                       "Acceptable" if total >= 18 else "Below the usual threshold of 18")
            cards([("Ashtakoota score", f"{total:g} / 36", verdict,
                    "good" if total >= 24 else "mixed" if total >= 18 else "bad")])
            st.dataframe(pd.DataFrame([{"Koota": r["koota"], "Score": f"{r['score']:g} / {r['max']}",
                                        f"{g.name} / {b.name}": r["detail"]} for r in rows]),
                         hide_index=True, width="stretch")
            mg = st.columns(2)
            for col, cx in zip(mg, (g, b)):
                mk = ac.manglik(cx)
                col.markdown(f"**{cx.name} – Mars dosha:** from Ascendant "
                             f"{'yes' if mk['from_asc'] else 'no'}, from Moon {'yes' if mk['from_moon'] else 'no'}, "
                             f"from Venus {'yes' if mk['from_venus'] else 'no'} (houses {mk['houses']})")
            st.caption("Ashtakoota uses the common North/South Indian tables; some schools differ slightly in "
                       "Vashya and Gana scoring and in dosha cancellations.")
        orb = st.slider("Orb for planet contacts (°)", 1.0, 8.0, 5.0, 0.5)
        sy = ac.synastry(ch, ob, orb)
        st.subheader("Working relationship")
        def tone_rel(txt):
            return "bad" if txt.startswith(("6/8", "2/12")) else "good"
        ta, tb = sy["tara_a_to_b"], sy["tara_b_to_a"]
        cards([(f"{other} is, for {sel}", ta[0], ac.TARA_MEANING[ta[0]], ta[1]),
               (f"{sel} is, for {other}", tb[0], ac.TARA_MEANING[tb[0]], tb[1]),
               ("Ascendants", sy["asc_relation"].split(" - ")[0], sy["asc_relation"].split(" - ")[-1],
                tone_rel(sy["asc_relation"])),
               ("Moon signs", sy["moon_relation"].split(" - ")[0], sy["moon_relation"].split(" - ")[-1],
                tone_rel(sy["moon_relation"]))])
        la_, lb_, r1, r2 = sy["lagna_lords"]
        if la_ == lb_:
            st.markdown(f"Ascendant lords: both charts are ruled by **{la_}**.")
        else:
            st.markdown(f"Ascendant lords: {sel}'s **{la_}** treats {other}'s **{lb_}** as *{r1}*; "
                        f"{lb_} treats {la_} as *{r2}*.")
        st.markdown("**House overlays:** " + " · ".join(f"{k} {v}" for k, v in sy["overlays"].items()))
        st.dataframe(pd.DataFrame(sy["contacts"]).rename(columns={"contact": "Contact", "orb": "Orb (°)",
                                                                  "reading": "Reading"}),
                     hide_index=True, width="stretch")

# ---- Ask AI -------------------------------------------------------------------------


@st.cache_data(show_spinner=False, ttl=3 * 3600)
def ai_context(key, _ch, _md, others_key, _others, day_iso):
    return llm_qa.build_context(_ch, _md, date.fromisoformat(day_iso), _others)


with tabs[7]:
    api_key = secret("ANTHROPIC_API_KEY")
    if not api_key:
        st.info("To enable questions, add ANTHROPIC_API_KEY to the app's secrets "
                "(Streamlit Cloud: app menu → Settings → Secrets). See README.")
    else:
        c1, c2 = st.columns([2, 1])
        other_names = c1.multiselect("Also include these people (for relationship or team questions)",
                                     [n for n in sorted(profiles) if n != sel])
        default_model = secret("ANTHROPIC_MODEL", llm_qa.MODELS[0])
        model_opts = llm_qa.MODELS if default_model in llm_qa.MODELS else [default_model] + llm_qa.MODELS
        model = c2.selectbox("Model", model_opts, index=model_opts.index(default_model))

        today_local = datetime.now(ZoneInfo(tz0)).date()
        others = [(get_chart(profiles[n]), dashas_for(chart_key(profiles[n]), get_chart(profiles[n]), year_len))
                  for n in other_names]
        with st.spinner("Preparing chart data..."):
            ctx = ai_context(chart_key(prof), ch, md_list, tuple(chart_key(profiles[n]) for n in other_names),
                             others, today_local.isoformat())

        chats = st.session_state.setdefault("chats", {})
        hist = chats.setdefault(sel, [])
        st.caption("Answers are generated by an AI model from the app's own calculations. "
                   "They are interpretations, not certainties.")
        sugg = ["How does my week look for work and money?",
                "What are my best and most difficult periods in the next 12 months?",
                "Which dates suit signing an agreement this month?",
                "What does my chart say about career and leadership?"]
        sc = st.columns(len(sugg))
        picked = None
        for i, s in enumerate(sugg):
            if sc[i].button(s, key=f"sugg_{i}", width="stretch"):
                picked = s

        for m in hist:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        q = st.chat_input(f"Ask about {sel}'s chart...") or picked
        if q:
            hist.append({"role": "user", "content": q})
            with st.chat_message("user"):
                st.markdown(q)
            with st.chat_message("assistant"):
                try:
                    msgs = hist[-20:]
                    answer = st.write_stream(llm_qa.stream_answer(api_key, model, ctx, msgs))
                    hist.append({"role": "assistant", "content": answer if isinstance(answer, str) else str(answer)})
                except Exception as e:  # noqa: BLE001
                    hist.pop()
                    st.error(f"The AI request failed: {e}")
        cc1, cc2 = st.columns([1, 3])
        if cc1.button("Clear conversation", disabled=not hist):
            chats[sel] = []
            st.rerun()
        with st.expander("See the chart data sent to the AI"):
            st.code(ctx, language="text")

# ---- About --------------------------------------------------------------------------
with tabs[8]:
    st.markdown("""
### What this app calculates
- **Positions:** Swiss Ephemeris (built-in Moshier ephemeris), sidereal, with your chosen ayanamsa and node.
  These are the same calculations used by Jagannatha Hora, Parashara's Light and AstroSage; small differences
  come from settings (ayanamsa, true or mean node, dasha year length).
- **Parashari:** whole-sign houses, dignities, combustion, aspects, divisional charts (D2, D3, D4, D7, D9, D10, D12),
  Vimshottari dasha to pratyantar level, functional nature, common yogas, gochara.
- **KP:** Placidus cusps with sign, star, sub and sub-sub lords for planets and cusps.
- **Jaimini:** seven chara karakas.
- **Other timing:** Yogini dasha, Saturn cycles, key dates (sign changes, stations, eclipses on natal points,
  dasha changes).
- **Daily:** panchang, Tara Bala, Chandra Bala, Rahu Kalam, Yamagandam, Gulika, Abhijit, 24 horas.
- **Muhurta:** search for windows by purpose.
- **Compatibility:** Ashtakoota (36 points), Mars dosha, and a professional synastry view.

### Limits
- No software can give perfect predictions. Interpretations here are rule-based summaries of traditional
  principles. They are a starting point for judgement, not certainties.
- Birth time accuracy matters: a few minutes can change the Ascendant degree, KP cusps and divisional charts.
- Shadbala, Ashtakavarga and many rarer yogas are not included yet.
- Not financial, legal, medical or relationship advice.

### Ask AI
The Ask AI tab sends the computed chart data shown in "See the chart data sent to the AI" to Anthropic's
Claude API, together with your question. The model is instructed to interpret only that data. Answers are
AI-generated interpretations and can be wrong; check important points against the other tabs.

### Privacy and access
- The app requires a password (APP_PASSWORD secret).
- Birth details are personal data. Keep them in the PROFILES_JSON secret or import them per session.
  Never commit a profiles.json with real people's data to the repository.
- Questions in Ask AI, and the chart data of the people selected, are sent to the Claude API.
""")

st.caption("Traditional astrology for reflection and planning. Not a substitute for professional advice.")
