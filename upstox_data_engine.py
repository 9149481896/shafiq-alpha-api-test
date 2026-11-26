import streamlit as st
import pandas as pd
import numpy as np
import requests, gzip, io, time, base64, html, json, re
from urllib.parse import quote
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# SHAFIQ ALPHA | STOCK MARKET RESEARCH & INTELLIGENCE
# Founded & Developed by Magray Shafiq
# Research and Paper Trading Only - No Live Orders
# ============================================================

st.set_page_config(
    page_title="SHAFIQ ALPHA | Stock Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto"
)

BASE = "https://api.upstox.com"
INSTRUMENT_URLS = {
    "NSE": "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz",
    "BSE": "https://assets.upstox.com/market-quote/instruments/exchange/BSE.json.gz"
}
NIFTY_KEY = "NSE_INDEX|Nifty 50"
IST = timezone(timedelta(hours=5, minutes=30))

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{color-scheme:dark}
html,body,[class*="css"]{font-family:Inter,sans-serif}
.stApp{
 background:radial-gradient(ellipse at 5% 0%,rgba(0,142,255,.18),transparent 32%),
 radial-gradient(ellipse at 94% 10%,rgba(0,220,130,.11),transparent 28%),
 linear-gradient(145deg,#061326 0%,#020813 58%,#071326 100%);color:#eef5ff}
#MainMenu,footer{visibility:hidden}
.block-container{max-width:1300px;padding:3.8rem 1.1rem 2rem}
[data-testid="stHeader"]{background:rgba(3,10,22,.92)}
[data-testid="stSidebar"]{background:#07172b}
h1,h2,h3{color:#f4d477!important}
.sa-hero{display:flex;align-items:center;gap:28px;position:relative;overflow:hidden;
 padding:20px 24px 30px;margin:0 0 12px;border-radius:20px;border:1px solid rgba(255,205,73,.65);
 background:radial-gradient(ellipse at 86% 20%,rgba(0,230,120,.20),transparent 34%),linear-gradient(110deg,#07172c,#050d1b 60%,#08213a);
 box-shadow:0 12px 34px rgba(0,0,0,.45),inset 0 0 28px rgba(0,145,255,.12)}
.sa-hero:after{content:"";position:absolute;left:-5%;right:-5%;bottom:5px;height:9px;
 background:linear-gradient(90deg,#06b8ff,#f4b928,#fff0a3,#f2a900,#08b9ff);
 transform:rotate(-1.2deg);filter:drop-shadow(0 0 8px #e8b82c)}
.sa-avatar{width:240px;aspect-ratio:1;flex:0 0 240px;box-sizing:border-box;padding:6px;border-radius:50%;
 background:linear-gradient(135deg,#fff4ae,#e8a91d 55%,#fff2a3);position:relative;z-index:1;
 box-shadow:0 0 0 5px rgba(242,190,54,.16),0 0 32px rgba(255,192,45,.45)}
.sa-face{width:100%;height:100%;overflow:hidden;position:relative;border-radius:50%;background:#fff}
/* Crops the empty white area of the 800x800 portrait so the face fills the circle */
.sa-face img{position:absolute;width:173.9%!important;max-width:none!important;height:auto;left:-15.2%;top:-37%;margin:0}
.sa-brand{min-width:0;position:relative;z-index:1}
.sa-brand-title{font-size:clamp(2.1rem,5.4vw,4.4rem);font-weight:900;line-height:1.05;
 background:linear-gradient(180deg,#fff3b0 10%,#f6c43c 55%,#c98a0c);
 -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.sa-subtitle{font-size:clamp(.82rem,1.7vw,1.3rem);font-weight:800;color:#fff;margin-top:8px}
.sa-credit{font-size:clamp(.78rem,1.2vw,1rem);color:#d5e3f6;margin-top:8px}
.sa-live{display:inline-block;margin-top:11px;padding:6px 12px;border-radius:20px;color:#7fffc2;
 background:rgba(0,220,130,.10);border:1px solid rgba(0,230,145,.45);font-size:.72rem;font-weight:800}
.sa-art{position:absolute;right:10px;top:8px;width:25%;max-height:75%;opacity:.8;pointer-events:none}
.sa-title{font-size:1.3rem;font-weight:900;color:#f5d66d;margin:16px 0 10px}
.sa-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:4px 0 14px}
.sa-kpi{display:flex;align-items:center;gap:12px;padding:16px 14px;border-radius:15px;border:1px solid;min-width:0;
 box-shadow:inset 0 0 22px rgba(255,255,255,.07),0 8px 20px rgba(0,0,0,.35)}
.sa-kpi i{font-style:normal;font-size:2rem}
.sa-kpi span{display:block;font-size:.82rem;font-weight:700;color:#eaf3ff}
.sa-kpi b{display:block;font-size:1.75rem;font-weight:900;color:#fff;line-height:1.2}
.sa-kpi small{display:block;font-size:.68rem;color:#cfe0f5}
.sa-blue{background:linear-gradient(145deg,#0a4fb4,#061c45);border-color:#2492ff}
.sa-green{background:linear-gradient(145deg,#087a2c,#04261a);border-color:#2ee66b}
.sa-purple{background:linear-gradient(145deg,#6a1b9a,#220a3d);border-color:#c45cff}
.sa-orange{background:linear-gradient(145deg,#b35a00,#3d1d03);border-color:#ffa126}
.sa-grid{display:grid;grid-template-columns:minmax(0,1.9fr) minmax(0,1fr);gap:14px;margin-bottom:14px}
.sa-panel{background:linear-gradient(145deg,rgba(9,37,66,.97),rgba(4,15,31,.98));
 border:1px solid rgba(46,157,232,.75);border-radius:17px;padding:14px 16px;min-width:0;
 box-shadow:0 9px 25px rgba(0,0,0,.28)}
.sa-panel.sa-snap{border-color:#8a63d2}
.sa-panel.sa-top{border-color:#b9922f;padding:14px 10px}
.sa-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;
 font-size:1.12rem;font-weight:900;color:#fff;margin-bottom:10px}
.sa-top .sa-head{color:#f5d66d}
.sa-pill{font-size:.82rem;padding:6px 12px;border-radius:20px;border:1px solid}
.sa-pill.up{color:#43f58a;border-color:#1d9e55;background:#073a24}
.sa-pill.down{color:#ff7474;border-color:#a53b3b;background:#3a0d12}
.sa-chart{display:flex;gap:6px}
.sa-yaxis{display:flex;flex-direction:column;justify-content:space-between;height:200px;font-size:.7rem;color:#bcd0ea;text-align:right}
.sa-plot{flex:1;min-width:0}
.sa-plot img{width:100%!important;max-width:100%!important;height:200px;display:block}
.sa-xaxis{display:flex;justify-content:space-between;font-size:.7rem;color:#bcd0ea;margin-top:5px}
.sa-note{font-size:.7rem;color:#93acc9;margin-top:7px}
.sa-snapshot-row{display:flex;justify-content:space-between;gap:10px;padding:13px 2px;
 border-bottom:1px solid rgba(121,176,220,.24);color:#eaf3ff}
.sa-table{width:100%;border-collapse:collapse;table-layout:auto;margin:0;font-size:.86rem;color:#eef5ff}
.sa-table th{background:#0c3a6e;color:#fff;padding:9px 8px;border:1px solid #1d4f80;text-align:left}
.sa-table td{padding:9px 8px;border:1px solid #17395d}
.sa-table .num{text-align:right;white-space:nowrap}
.sa-table .sub{display:none;font-size:.62rem;font-weight:500;color:#a9c0dc}
.sa-up{color:#2ef07c}.sa-down{color:#ff5c5c}.sa-flat{color:#ffca43}
.stButton>button,.stDownloadButton>button{border:1px solid rgba(255,220,103,.8)!important;
 border-radius:10px!important;background:linear-gradient(110deg,#ffe37a,#d99a18)!important;
 color:#111827!important;font-weight:900!important;min-height:2.55rem}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#0d3765,#07182f);
 border:1px solid #168de2;border-radius:16px;padding:13px 15px}
div[data-testid="stMetric"] label{color:#d9eaff!important;font-weight:700}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#fff!important;font-weight:900}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid rgba(43,150,230,.75);border-radius:12px;overflow:hidden}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{background:#0d2037!important;color:#fff!important}
.st-key-top_navigation,.st-key-top_navigation [data-testid="stRadio"]{width:100%!important}
.st-key-top_navigation [role="radiogroup"]{display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;width:100%}
.st-key-top_navigation [role="radiogroup"] label{display:flex;justify-content:center;align-items:center;margin:0;
 min-height:50px;padding:6px 4px;border-radius:11px;border:1px solid #27608a;background:linear-gradient(145deg,#102944,#07172a)}
.st-key-top_navigation [role="radiogroup"] label>div:first-child:not(:has(p)){display:none}
.st-key-top_navigation label p{color:#eaf3ff!important;font-weight:700;font-size:.84rem;text-align:center;line-height:1.25}
.st-key-top_navigation label:has(input:checked){background:linear-gradient(110deg,#ffdf62,#e8a91d);border-color:#fff0a0;box-shadow:0 0 14px rgba(255,200,50,.5)}
.st-key-top_navigation label:has(input:checked) p{color:#101827!important;font-weight:900}
@media(max-width:900px){.sa-grid{grid-template-columns:minmax(0,1fr)}}
@media(max-width:700px){
 .block-container{padding-left:.6rem;padding-right:.6rem}
 .sa-hero{gap:12px;padding:16px 10px 28px;border-radius:15px}
 .sa-avatar{width:44vw;flex-basis:44vw;max-width:240px;padding:4px}
 .sa-brand-title{font-size:clamp(1.8rem,10vw,3rem)}
 .sa-subtitle{font-size:.7rem}
 .sa-credit{font-size:.7rem}
 .sa-live{font-size:.56rem;padding:5px 7px}
 .sa-art{display:none}
 .st-key-top_navigation [role="radiogroup"]{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
 .st-key-top_navigation label p{font-size:.72rem}
 .sa-kpis{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
 .sa-kpi{gap:8px;padding:12px 8px}.sa-kpi i{font-size:1.4rem}.sa-kpi b{font-size:1.3rem}.sa-kpi span{font-size:.7rem}
 .sa-panel.sa-top{padding:10px 5px}
 .sa-table{font-size:.68rem}.sa-table th,.sa-table td{padding:7px 3px}
 .sa-table .wide{display:none}
 .sa-table .sub{display:block;max-width:24vw;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
}
</style>
""", unsafe_allow_html=True)

def image_uri(path, mime="image/png"):
    return f"data:{mime};base64,"+base64.b64encode(path.read_bytes()).decode("ascii")

def svg_uri(svg):
    return "data:image/svg+xml;base64,"+base64.b64encode(svg.encode()).decode("ascii")

def header_art():
    # Optional: upload assets/bull.png to show your own bull artwork in the header
    bull = Path(__file__).parent / "assets" / "bull.png"
    if bull.exists(): return image_uri(bull)
    bars=[(12,92,22),(34,80,28),(56,86,18),(78,66,30),(100,72,20),(122,52,32),(144,58,22),(166,36,34),(188,42,22),(210,20,34)]
    body="".join(f'<line x1="{x+5}" y1="{y-9}" x2="{x+5}" y2="{y+h+9}" stroke="{c}" stroke-width="1.5"/><rect x="{x}" y="{y}" width="10" height="{h}" fill="{c}"/>'
        for i,(x,y,h) in enumerate(bars) for c in ["#e5484d" if i%3==2 else "#22d366"])
    arrow='<path d="M8 82 C70 78 110 55 200 8" fill="none" stroke="#3dff8b" stroke-width="3"/><path d="M184 6 L204 5 L195 23 Z" fill="#3dff8b"/>'
    return svg_uri(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 232 140">{body}{arrow}</svg>')

def render_brand():
    photo = Path(__file__).parent / "assets" / "founder_portrait.png"
    if not photo.exists():
        photo = Path(__file__).parent / "founder_portrait.png"
    if photo.exists():
        avatar = f'<div class="sa-avatar"><div class="sa-face"><img src="{image_uri(photo)}" alt="Magray Shafiq"></div></div>'
    else:
        avatar = '<div class="sa-avatar" style="display:grid;place-items:center;color:#111;font-size:2rem;font-weight:900">SA</div>'
    st.markdown(
        f'<div class="sa-hero">{avatar}<div class="sa-brand">'
        '<div class="sa-brand-title">SHAFIQ ALPHA</div>'
        '<div class="sa-subtitle">STOCK MARKET RESEARCH &amp; INTELLIGENCE</div>'
        '<div class="sa-credit">Founded &amp; Developed by Magray Shafiq</div>'
        '<div class="sa-live">● MARKET RESEARCH | PAPER TRADING ONLY</div>'
        f'</div><img class="sa-art" src="{header_art()}" alt=""></div>',
        unsafe_allow_html=True)

render_brand()

# Session state
for k,v in {
 "instruments":None,"market_data":None,"scanner_data":None,
 "last_refresh":None,"last_custom_result":None,"custom_conditions":[],"adv_conditions":[]
}.items():
    if k not in st.session_state: st.session_state[k]=v

def get_token():
    try: return str(st.secrets.get("UPSTOX_ANALYTICS_TOKEN","")).strip()
    except Exception: return ""

TOKEN=get_token()
if not TOKEN:
    st.error("UPSTOX_ANALYTICS_TOKEN نہیں ملا۔ Streamlit Secrets میں Token چیک کریں۔")
    st.stop()

HEADERS={"Authorization":f"Bearer {TOKEN}","Accept":"application/json","Content-Type":"application/json"}

def api_get(url,params=None,timeout=35):
    try:
        r=requests.get(url,headers=HEADERS,params=params,timeout=timeout)
        if r.status_code==200: return r.json()
        return {"error":r.status_code,"message":r.text[:350]}
    except Exception as e: return {"error":"REQUEST_ERROR","message":str(e)}

@st.cache_data(ttl=86400,show_spinner=False)
def download_instruments(exchange):
    r=requests.get(INSTRUMENT_URLS[exchange],timeout=60); r.raise_for_status()
    raw=r.content
    if raw[:2]==b"\x1f\x8b": raw=gzip.decompress(raw)
    return pd.read_json(io.BytesIO(raw))

def load_all_instruments():
    frames=[]
    for ex in ["NSE","BSE"]:
        try:
            d=download_instruments(ex)
            if "instrument_type" in d: d=d[d.instrument_type.astype(str).str.upper()=="EQ"]
            if "isin" in d: d=d[d["isin"].notna() & (d["isin"].astype(str).str.len()>5)]
            if "instrument_key" in d: d=d.drop_duplicates("instrument_key")
            d["Exchange"]=ex; frames.append(d)
        except Exception as e: st.warning(f"{ex} instrument download error: {e}")
    if not frames: return pd.DataFrame()
    out=pd.concat(frames,ignore_index=True)
    if "instrument_key" in out: out=out.drop_duplicates("instrument_key")
    return out

def fetch_quote_batch(keys):
    d=api_get(f"{BASE}/v2/market-quote/quotes",{"instrument_key":",".join(keys)},timeout=45)
    if "error" in d:
        st.session_state["quote_error"]=f'{d.get("error")}: {d.get("message","")}'
        return {}
    return d.get("data",{})

def fetch_all_quotes(instruments,progress=None):
    if instruments.empty: return pd.DataFrame()
    keys=instruments.instrument_key.dropna().astype(str).unique().tolist()
    quotes={}
    batches=[keys[i:i+500] for i in range(0,len(keys),500)]
    for i,b in enumerate(batches):
        quotes.update(fetch_quote_batch(b))
        if progress: progress.progress((i+1)/max(1,len(batches)))
        time.sleep(.15)
    rows=[]
    for key,q in quotes.items():
        o=q.get("ohlc") or {}
        rows.append({"instrument_key":q.get("instrument_token",key),"Quote Symbol":q.get("symbol"),
         "LTP":q.get("last_price"),"Volume":q.get("volume"),"Average Price":q.get("average_price"),
         "Open":o.get("open"),"High":o.get("high"),"Low":o.get("low"),"Close":o.get("close"),
         "Net Change":q.get("net_change"),"Buy Quantity":q.get("total_buy_quantity"),
         "Sell Quantity":q.get("total_sell_quantity"),"Quote Time":q.get("timestamp")})
    return pd.DataFrame(rows)

def build_scanner_data(instruments,quotes):
    if instruments.empty or quotes.empty: return pd.DataFrame()
    d=instruments.merge(quotes,on="instrument_key",how="left")
    ren={"trading_symbol":"Symbol","name":"Company","isin":"ISIN","face_value":"Face Value",
         "instrument_key":"Instrument Key"}
    d=d.rename(columns={k:v for k,v in ren.items() if k in d.columns})
    for c in ["Symbol","Company","ISIN","LTP","Volume","Net Change","Average Price","Face Value"]:
        if c not in d: d[c]=np.nan
    for c in ["LTP","Volume","Net Change","Average Price","Face Value"]:
        d[c]=pd.to_numeric(d[c],errors="coerce")
    d["Market Cap (Cr)"]=np.nan
    d["Market Cap Status"]="Not available from live quote feed"
    return d

def rsi(series,n=14):
    delta=series.diff(); gain=delta.clip(lower=0); loss=-delta.clip(upper=0)
    ag=gain.ewm(alpha=1/n,min_periods=n,adjust=False).mean()
    al=loss.ewm(alpha=1/n,min_periods=n,adjust=False).mean()
    rs=ag/al.replace(0,np.nan)
    return 100-100/(1+rs)

def add_indicators(d):
    d=d.copy(); c=pd.to_numeric(d["Close"],errors="coerce")
    d["EMA 9"]=c.ewm(span=9,adjust=False).mean()
    d["EMA 21"]=c.ewm(span=21,adjust=False).mean()
    d["SMA 50"]=c.rolling(50).mean(); d["SMA 200"]=c.rolling(200).mean()
    d["RSI 14"]=rsi(c); return d

def get_history(key,years=5):
    end=date.today(); start=end-timedelta(days=int(365*years))
    u=f"{BASE}/v3/historical-candle/{key}/days/1/{end}/{start}"
    x=api_get(u,timeout=45); candles=x.get("data",{}).get("candles",[]) if "error" not in x else []
    if not candles: return pd.DataFrame()
    d=pd.DataFrame(candles,columns=["Date","Open","High","Low","Close","Volume","OI"])
    d["Date"]=pd.to_datetime(d["Date"])
    for c in ["Open","High","Low","Close","Volume"]: d[c]=pd.to_numeric(d[c],errors="coerce")
    return add_indicators(d.sort_values("Date"))

def candle_frame(payload):
    rows=payload.get("data",{}).get("candles",[]) if "error" not in payload else []
    if not rows: return pd.DataFrame()
    d=pd.DataFrame(rows,columns=["Date","Open","High","Low","Close","Volume","OI"])
    d["Date"]=pd.to_datetime(d["Date"]); d["Close"]=pd.to_numeric(d["Close"],errors="coerce")
    return d.dropna(subset=["Close"]).sort_values("Date")

def get_nifty_intraday():
    key=quote(NIFTY_KEY,safe="")
    d=candle_frame(api_get(f"{BASE}/v3/historical-candle/intraday/{key}/minutes/1"))
    if not d.empty: return d
    # Market closed / before open: show the most recent trading session
    end=datetime.now(IST).date(); start=end-timedelta(days=10)
    d=candle_frame(api_get(f"{BASE}/v3/historical-candle/{key}/minutes/1/{end}/{start}"))
    if d.empty: return d
    return d[d["Date"].dt.date==d["Date"].dt.date.max()]

@st.cache_data(ttl=60,show_spinner=False)
def cached_nifty(): return get_nifty_intraday()

def fundamentals(isin):
    endpoints={
      "Profile":("profile",{}),"Key Ratios":("key-ratios",{}),
      "Income Statement":("income-statement",{"type":"consolidated","time_period":"quarterly"}),
      "Balance Sheet":("balance-sheet",{"type":"consolidated","fs":"true"}),
      "Cash Flow":("cash-flow",{"type":"consolidated"}),
      "Share Holdings":("share-holdings",{})
    }
    out={}
    for label,(ep,params) in endpoints.items():
        out[label]=api_get(f"{BASE}/v2/fundamentals/{isin}/{ep}",params)
        time.sleep(.15)
    return out

def apply_filters(d,conditions,logic):
    if d.empty or not conditions: return d
    masks=[]
    for c in conditions:
        f=c["field"]
        if f not in d: continue
        s=pd.to_numeric(d[f],errors="coerce")
        try: v=float(c["value"])
        except: continue
        op=c["operation"]
        m={">":s>v,">=":s>=v,"<":s<v,"<=":s<=v,"=":s==v,"!=":(s!=v)&s.notna()}.get(op)
        if m is not None: masks.append(m.fillna(False))
    if not masks: return d
    result=masks[0]
    for m in masks[1:]: result=(result&m) if logic=="AND" else (result|m)
    return d[result]

# ---------- Scanner / Screener data ----------
SCREEN_COLUMNS=["Symbol","Company","Exchange","Security Type","LTP","Change %","Net Change","Volume",
    "Est. Traded Value (Cr)","Open","High","Low","Close","Average Price","Buy Quantity","Sell Quantity",
    "ISIN","Quote Time","Instrument Key"]
TEXT_COLUMNS=["Symbol","Company","Exchange","Security Type","ISIN","Quote Time","Instrument Key"]
OPERATORS=[">",">=","<","<=","=","!="]

def screener_view(d):
    d=with_change_pct(d)
    prefix=d["ISIN"].astype(str).str.upper().str[:3]
    d["Security Type"]=np.select([prefix=="INE",prefix=="INF"],["Company Share","ETF / Fund"],default="Other")
    avg=pd.to_numeric(d.get("Average Price"),errors="coerce")
    d["Est. Traded Value (Cr)"]=avg*pd.to_numeric(d["Volume"],errors="coerce")/1e7
    # Keep only useful columns, and hide any column that has no data at all
    out=d[[c for c in SCREEN_COLUMNS if c in d.columns]]
    return out.dropna(axis=1,how="all")

def type_filter(d,key):
    choice=st.selectbox("Security Type",["Company Share","ETF / Fund","Other","ALL"],key=key)
    return d if choice=="ALL" else d[d["Security Type"]==choice]

def show_table(d):
    d=d.drop(columns=["Instrument Key"],errors="ignore")
    formats={c:st.column_config.NumberColumn(format="%.2f") for c in d.columns if pd.api.types.is_float_dtype(d[c])}
    st.dataframe(d,use_container_width=True,hide_index=True,column_config=formats)

def new_condition(field="Volume",operation=">",value=100000.0):
    st.session_state["condition_counter"]=st.session_state.get("condition_counter",0)+1
    return {"id":st.session_state["condition_counter"],"field":field,"operation":operation,"value":float(value)}

# ---------- Advanced data: RSI / Market Cap / Fundamentals ----------
TECH_NAMES=["RSI 14","SMA 50","SMA 200","52W High","52W Low"]
# (display name, match mode, key patterns, endpoint tag)
ALIAS=[
 ("Market Cap","exact",["marketcap","mcap","marketcapitalization","marketcapitalisation","marketcapcr"],"KR"),
 ("PE","exact",["pe","peratio","pettm","priceearnings","priceearningsratio","pricetoearnings"],"KR"),
 ("ROE %","exact",["roe","returnonequity","roepercent"],"KR"),
 ("ROCE %","exact",["roce","returnoncapitalemployed"],"KR"),
 ("Debt/Equity","exact",["debttoequity","debtequity","debtequityratio","de","deratio"],"KR"),
 ("EPS","exact",["eps","epsttm","earningspershare","basiceps"],"KR"),
 ("Dividend Yield %","exact",["dividendyield","divyield"],"KR"),
 ("Promoter Holding %","contains",["promoter"],"SH"),
]
ALIAS_NAMES=[a[0] for a in ALIAS]
FUND_ENDPOINTS={"KR":("key-ratios",{}),"SH":("share-holdings",{}),
                "IS":("income-statement",{"type":"consolidated","time_period":"quarterly"})}

def norm(s): return re.sub(r"[^a-z0-9]","",str(s).lower())

def flatten(o,p=""):
    out={}
    if isinstance(o,dict):
        for k,v in o.items(): out.update(flatten(v,f"{p}.{k}" if p else str(k)))
    elif isinstance(o,list):
        if o: out.update(flatten(o[0],p))   # lists: first row only
    else: out[p]=o
    return out

def to_float(v):
    if v is None or isinstance(v,bool): return None
    try: return float(str(v).replace(",","").replace("%","").strip())
    except Exception: return None

def add_aliases(flat):
    out=dict(flat)
    for name,mode,pats,tag in ALIAS:
        for k,v in flat.items():
            if not k.startswith(tag+"."): continue
            rest=k.split(".",1)[1]; last=norm(rest.split(".")[-1]); full=norm(rest)
            ok=(last in pats) if mode=="exact" else (any(p in full for p in pats) and "pledge" not in full)
            if ok: out[name]=v; break
    return out

def fund_flat(isin):
    out={}
    for tag,(ep,params) in FUND_ENDPOINTS.items():
        x=api_get(f"{BASE}/v2/fundamentals/{isin}/{ep}",params)
        if "error" in x: continue
        for k,v in flatten(x.get("data",x)).items():
            f=to_float(v)
            if f is not None: out[f"{tag}.{k}"]=f
    return add_aliases(out)

def tech_for(key):
    h=get_history(key,1.5)
    if h.empty or len(h)<20: return {}
    last=h.iloc[-1]; y=h.tail(252)
    return {"RSI 14":last["RSI 14"],"SMA 50":last["SMA 50"],"SMA 200":last["SMA 200"],
            "52W High":y["High"].max(),"52W Low":y["Low"].min()}

def run_parallel(fn,items,label,workers=4):
    res={}
    if not items: return res
    bar=st.progress(0,text=label)
    with ThreadPoolExecutor(workers) as ex:
        futs={ex.submit(fn,i):i for i in items}
        for n,f in enumerate(as_completed(futs),1):
            try: res[futs[f]]=f.result()
            except Exception: res[futs[f]]={}
            bar.progress(n/len(items),text=f"{label} {n}/{len(items)}")
    bar.empty()
    return res

def attach(short,cache,keys):
    extra=pd.DataFrame([cache.get(k,{}) for k in keys],index=short.index)
    extra=extra[[c for c in extra.columns if c not in short.columns]]
    return pd.concat([short,extra],axis=1)

def run_screener(data,c1,l1,c2,l2,limit):
    base=apply_filters(data,c1,l1)
    n_base=len(base)
    if not c2: return base,list(base.columns),n_base,n_base
    sort_col="Est. Traded Value (Cr)" if "Est. Traded Value (Cr)" in base else "Volume"
    short=base.sort_values(sort_col,ascending=False).head(limit).copy()
    used=[c["field"] for c in c2]
    need_tech=any(f in TECH_NAMES for f in used)
    need_fund=any(f not in TECH_NAMES for f in used)
    today=str(date.today())
    if need_tech:
        tc=st.session_state.setdefault("tech_cache",{})
        keys=short["Instrument Key"].astype(str).tolist()
        missing=[k for k in dict.fromkeys(keys) if f"{k}|{today}" not in tc]
        for k,v in run_parallel(tech_for,missing,"RSI / Technical ڈیٹا").items(): tc[f"{k}|{today}"]=v
        short=attach(short,{k:tc.get(f"{k}|{today}",{}) for k in keys},keys)
        for n in TECH_NAMES:
            if n not in short: short[n]=np.nan
    if need_fund:
        fc=st.session_state.setdefault("fund_cache",{})
        isins=short["ISIN"].astype(str).tolist()
        missing=[i for i in dict.fromkeys(isins) if i not in fc]
        for k,v in run_parallel(fund_flat,missing,"Fundamentals ڈیٹا").items(): fc[k]=v
        short=attach(short,fc,isins)
        for n in ALIAS_NAMES:
            if n not in short: short[n]=np.nan
        st.session_state["extra_cols"]=sorted({c for v in fc.values() for c in v if c not in ALIAS_NAMES})
    for f in dict.fromkeys(used):
        if f in short and short[f].isna().all():
            st.warning(f'"{f}" کا ڈیٹا Upstox سے نہیں ملا۔ نیچے "دستیاب فیلڈز" دیکھیں۔')
    result=apply_filters(short,c2,l2)
    cols=list(data.columns)+(TECH_NAMES if need_tech else [])+(ALIAS_NAMES if need_fund else [])+used
    cols=[c for c in dict.fromkeys(cols) if c in result.columns]
    return result,cols,n_base,len(short)

def condition_builder(name,fields,default_field,default_value,prefix,min_one):
    conds=st.session_state[name]
    if min_one and not conds: conds.append(new_condition(default_field,">",default_value))
    if st.button("➕ Add Condition",key=f"add_{prefix}"): conds.append(new_condition(default_field,">",default_value))
    for n,c in enumerate(list(conds),1):
        if "id" not in c: c.update(new_condition(c["field"],c["operation"],c["value"]))
        k=c["id"]
        a,b,cc,dd=st.columns([2,1,2,1])
        c["field"]=a.selectbox(f"Field {n}",fields,index=fields.index(c["field"]) if c["field"] in fields else 0,key=f"{prefix}f{k}")
        c["operation"]=b.selectbox("Operator",OPERATORS,index=OPERATORS.index(c["operation"]),key=f"{prefix}o{k}")
        c["value"]=cc.number_input("Value",value=float(c["value"]),key=f"{prefix}v{k}")
        if dd.button("Remove",key=f"{prefix}r{k}"):
            st.session_state[name]=[x for x in conds if x.get("id")!=k]
            st.session_state.last_custom_result=None
            st.rerun()
    return st.session_state[name]

# ---------- Dashboard components ----------
def nifty_panel_html(nq, candles):
    pill=""; up=True
    if nq.get("last_price") is not None:
        lp=float(nq["last_price"]); text=f"NIFTY 50&nbsp; {lp:,.2f}"
        if nq.get("net_change") is not None:
            ch=float(nq["net_change"]); prev=lp-ch; up=ch>=0
            if prev: text+=f"&nbsp; {'▲' if up else '▼'} {ch/prev*100:+.2f}%"
        pill=f'<span class="sa-pill {"up" if up else "down"}">{text}</span>'
    elif not candles.empty:
        up=candles["Close"].iloc[-1]>=candles["Close"].iloc[0]
    head=f'<div class="sa-panel"><div class="sa-head"><span>📈 Market Overview</span>{pill}</div>'
    if candles.empty:
        return head+'<div class="sa-note">NIFTY 50 chart data فی الحال دستیاب نہیں۔</div></div>'
    day=candles["Date"].iloc[-1]
    open_t=day.replace(hour=9,minute=15,second=0); close_t=day.replace(hour=15,minute=30,second=0)
    first=min(open_t,candles["Date"].iloc[0]); last=max(close_t,candles["Date"].iloc[-1])
    span=(last-first).total_seconds()
    lo=float(candles["Close"].min()); hi=float(candles["Close"].max())
    pad=max((hi-lo)*.1,1.0); lo-=pad; hi+=pad
    pts=" ".join(f"{(t-first).total_seconds()/span*1000:.1f},{(hi-v)/(hi-lo)*300:.1f}" for t,v in zip(candles["Date"],candles["Close"]))
    x0=(candles["Date"].iloc[0]-first).total_seconds()/span*1000
    x1=(candles["Date"].iloc[-1]-first).total_seconds()/span*1000
    color="#35f06f" if up else "#ff5a5a"
    grid="".join(f'<line x1="0" x2="1000" y1="{y}" y2="{y}" stroke="#7fa8d0" stroke-opacity=".22" vector-effect="non-scaling-stroke"/>' for y in (1,100,200,299))
    svg=('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 300" preserveAspectRatio="none">'
         f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}" stop-opacity=".55"/><stop offset="1" stop-color="{color}" stop-opacity=".03"/></linearGradient></defs>{grid}'
         f'<polygon points="{x0:.1f},300 {pts} {x1:.1f},300" fill="url(#g)"/>'
         f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>')
    yl="".join(f"<span>{hi-(hi-lo)*i/3:,.0f}</span>" for i in range(4))
    xl="".join(f"<span>{(first+timedelta(seconds=span*i/4)).strftime('%H:%M')}</span>" for i in range(5))
    return (head+f'<div class="sa-chart"><div class="sa-yaxis">{yl}</div><div class="sa-plot">'
            f'<img src="{svg_uri(svg)}" alt="NIFTY 50 intraday chart"><div class="sa-xaxis">{xl}</div></div></div>'
            f'<div class="sa-note">Session: {day.strftime("%d %b %Y")} · 1-minute candles · Upstox</div></div>')

def with_change_pct(d):
    d=d.copy()
    ltp=pd.to_numeric(d["LTP"],errors="coerce"); ch=pd.to_numeric(d["Net Change"],errors="coerce")
    prev=ltp-ch
    d["Change %"]=(ch/prev.where(prev>0))*100
    return d

def kpi_html(d):
    isin=d["ISIN"].dropna().astype(str)
    counts=d["Exchange"].value_counts()
    names=[e for e in ["NSE","BSE"] if counts.get(e,0)>0]
    cards=[
      ("sa-blue","👥","Total Companies",f"{isin.nunique():,}",f"{len(d):,} listings"),
      ("sa-green","📈","Live Prices",f"{int(d['LTP'].notna().sum()):,}",f"of {len(d):,} listings"),
      ("sa-purple","📚","Volume Available",f"{int(d['Volume'].notna().sum()):,}",f"of {len(d):,} listings"),
      ("sa-orange","🏦","Exchanges"," + ".join(names) or "—"," · ".join(f"{e} {int(counts.get(e,0)):,}" for e in ["NSE","BSE"]))]
    return '<div class="sa-kpis">'+"".join(f'<div class="sa-kpi {c}"><i>{i}</i><div><span>{t}</span><b>{v}</b><small>{n}</small></div></div>' for c,i,t,v,n in cards)+'</div>'

def snapshot_html(d):
    valid=with_change_pct(d.dropna(subset=["LTP"]))
    chg=pd.to_numeric(valid["Net Change"],errors="coerce").dropna()
    vol=pd.to_numeric(valid["Volume"],errors="coerce").fillna(0)
    avg=pd.to_numeric(valid["Average Price"],errors="coerce").fillna(pd.to_numeric(valid["LTP"],errors="coerce"))
    traded=float((avg*vol).sum()/1e7)
    rows=[("🟢 Advances",f"{int((chg>0).sum()):,}","sa-up"),("🔻 Declines",f"{int((chg<0).sum()):,}","sa-down"),
          ("➖ Unchanged",f"{int((chg==0).sum()):,}","sa-flat"),("💹 Est. Traded Value",f"₹ {traded:,.0f} Cr","")]
    return ('<div class="sa-panel sa-snap"><div class="sa-head"><span>🌐 Market Snapshot</span></div>'
        +"".join(f'<div class="sa-snapshot-row"><span>{a}</span><b class="{c}">{b}</b></div>' for a,b,c in rows)
        +'<div class="sa-note">Listing-wise counts. Traded value is an estimate (average price × volume), not official turnover.</div></div>')

def indian_number(n):
    s=str(int(n))
    if len(s)<=3: return s
    head,tail=s[:-3],s[-3:]; parts=[]
    while len(head)>2: parts.insert(0,head[-2:]); head=head[:-2]
    return ",".join([head]+parts+[tail])

def top_volume_html(d):
    top=with_change_pct(d.dropna(subset=["Volume"]).sort_values("Volume",ascending=False).head(5))
    body=""
    for n,(_,r) in enumerate(top.iterrows(),1):
        sym=html.escape(str(r["Symbol"])); name=html.escape(str(r["Company"]))
        pct=r["Change %"]
        if pd.isna(pct): change,cls="—",""
        elif pct>0: change,cls=f"▲ +{pct:.2f}%","sa-up"
        elif pct<0: change,cls=f"▼ {pct:.2f}%","sa-down"
        else: change,cls="0.00%","sa-flat"
        ltp="—" if pd.isna(r["LTP"]) else f'{r["LTP"]:,.2f}'
        ex=html.escape(str(r["Exchange"]))
        body+=(f'<tr><td>{n}</td><td><b>{sym}</b><span class="sub">{ex} · {name}</span></td><td class="wide">{name}</td>'
               f'<td class="wide">{ex}</td><td class="num">{ltp}</td><td class="num {cls}">{change}</td><td class="num">{indian_number(r["Volume"])}</td></tr>')
    if not body: body='<tr><td colspan="7">Volume data ابھی دستیاب نہیں۔</td></tr>'
    return ('<div class="sa-panel sa-top"><div class="sa-head"><span>🏆 Top 5 Volume Stocks</span></div><table class="sa-table"><thead><tr>'
            '<th>#</th><th>Symbol</th><th class="wide">Company</th><th class="wide">Exchange</th><th>LTP (₹)</th><th>Change %</th><th>Volume</th>'
            f'</tr></thead><tbody>{body}</tbody></table></div>')

def refresh_market_data():
    st.session_state["quote_error"]=None
    p=st.progress(0)
    with st.spinner("Fetching Upstox Full Market Quotes..."):
        q=fetch_all_quotes(st.session_state.instruments,p)
    p.empty()
    err=st.session_state.get("quote_error")
    if q.empty:
        st.error(f"Upstox سے کوئی Quote نہیں ملا۔ {err or ''}")
        return False
    st.session_state.market_data=q
    st.session_state.scanner_data=build_scanner_data(st.session_state.instruments,q)
    st.session_state.last_refresh=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    if err: st.warning(f"کچھ Quotes نہیں ملے: {err}")
    st.success(f"{len(q):,} quote records received")
    return True

# Top navigation replaces the old left-side radio menu
pages=["Dashboard","Market Scanner","Company Search","Company Fundamentals","Historical Analysis","Custom Screener"]
nav_labels=["🏠 Dashboard","🔎 Market Scanner","🏢 Company Search","📊 Fundamentals","📈 Historical","⚙️ Custom Screener"]
page=st.radio("MAIN MENU",pages,horizontal=True,format_func=lambda x:nav_labels[pages.index(x)],key="top_navigation",label_visibility="collapsed")

with st.sidebar:
    st.markdown("## ⚙️ CONTROL PANEL")
    if st.button("🔄 Download NSE + BSE Database",use_container_width=True):
        with st.spinner("Downloading NSE + BSE instruments..."):
            st.session_state.instruments=load_all_instruments()
            st.session_state.market_data=None; st.session_state.scanner_data=None
        st.success(f"{len(st.session_state.instruments):,} instruments loaded")
    if st.button("📡 Refresh Live Market Data",use_container_width=True):
        if st.session_state.instruments is None: st.error("پہلے Database ڈاؤن لوڈ کریں۔")
        else: refresh_market_data()
    st.divider()
    st.caption(f"Database: {len(st.session_state.instruments):,}" if st.session_state.instruments is not None else "Database: Not loaded")
    st.caption(f"Market Quotes: {len(st.session_state.market_data):,}" if st.session_state.market_data is not None else "Market Quotes: Not loaded")
    if st.session_state.last_refresh: st.caption("Last refresh: "+st.session_state.last_refresh)

instruments=st.session_state.instruments
scanner=st.session_state.scanner_data

if page=="Dashboard":
    if st.button("🔄 Load / Refresh Live Market Data",use_container_width=True,key="dashboard_refresh"):
        if st.session_state.instruments is None or st.session_state.instruments.empty:
            with st.spinner("Downloading NSE + BSE instruments..."):
                st.session_state.instruments=load_all_instruments()
        if st.session_state.instruments.empty: st.error("Instrument Database ڈاؤن لوڈ نہیں ہو سکا۔")
        elif refresh_market_data(): st.rerun()
    scanner=st.session_state.scanner_data
    ready=scanner is not None and not scanner.empty
    if ready:
        st.markdown(kpi_html(scanner),unsafe_allow_html=True)
    else:
        st.info("Live data دیکھنے کے لیے اوپر والا بٹن دبائیں۔")
    nq=fetch_quote_batch([NIFTY_KEY]); nq=next(iter(nq.values()),{}) if nq else {}
    overview=nifty_panel_html(nq,cached_nifty())
    if ready:
        st.markdown(f'<div class="sa-grid">{overview}{snapshot_html(scanner)}</div>',unsafe_allow_html=True)
        st.markdown(top_volume_html(scanner),unsafe_allow_html=True)
        st.caption("Last refresh: "+str(st.session_state.last_refresh))
        st.download_button("⬇️ Download Dashboard CSV",scanner.to_csv(index=False).encode(), "shafiq_alpha_dashboard.csv","text/csv")
    else:
        st.markdown(overview,unsafe_allow_html=True)

elif page=="Market Scanner":
    st.markdown('<div class="sa-title">🔎 NSE + BSE MARKET SCANNER</div>',unsafe_allow_html=True)
    if scanner is None or scanner.empty: st.warning("پہلے Live Market Data Refresh کریں۔")
    else:
        x,y,z=st.columns(3); ex=x.selectbox("Exchange",["ALL","NSE","BSE"])
        lo=y.number_input("Minimum Price",min_value=0.0,value=0.0)
        hi=z.number_input("Maximum Price",min_value=0.0,value=100000.0)
        mv=st.number_input("Minimum Daily Volume",min_value=0,value=0)
        out=type_filter(screener_view(scanner),"scanner_type")
        if ex!="ALL": out=out[out.Exchange==ex]
        out=out[pd.to_numeric(out.LTP,errors="coerce").between(lo,hi)&(pd.to_numeric(out.Volume,errors="coerce")>=mv)]
        st.metric("Matching Stocks",f"{len(out):,}")
        show_table(out)
        st.download_button("⬇️ Export Scanner CSV",out.drop(columns=["Instrument Key"],errors="ignore").to_csv(index=False).encode(),"shafiq_alpha_scanner.csv","text/csv")

elif page=="Company Search":
    st.markdown('<div class="sa-title">🏢 COMPANY SEARCH</div>',unsafe_allow_html=True)
    if instruments is None: st.warning("Instrument Database پہلے ڈاؤن لوڈ کریں۔")
    else:
        query=st.text_input("Company Name / Trading Symbol / ISIN").strip().upper()
        if query:
            cols=[c for c in ["trading_symbol","name","isin"] if c in instruments]
            mask=pd.Series(False,index=instruments.index)
            for col in cols: mask|=instruments[col].astype(str).str.upper().str.contains(query,na=False)
            found=instruments[mask].head(100)
            if found.empty: st.warning("کوئی کمپنی نہیں ملی۔")
            else:
                idx=st.selectbox("Select Company",found.index,format_func=lambda i:f'{found.loc[i].get("trading_symbol","")} | {found.loc[i].get("name","")}')
                st.dataframe(found.loc[[idx]],use_container_width=True,hide_index=True)

elif page=="Company Fundamentals":
    st.markdown('<div class="sa-title">📊 COMPANY FUNDAMENTALS</div>',unsafe_allow_html=True)
    if instruments is None: st.warning("پہلے Instrument Database ڈاؤن لوڈ کریں۔")
    else:
        query=st.text_input("Enter Company Symbol or ISIN").strip().upper()
        if query:
            mask=instruments.trading_symbol.astype(str).str.upper().str.contains(query,na=False)|instruments.isin.astype(str).str.upper().str.contains(query,na=False)
            found=instruments[mask].head(100)
            if found.empty: st.warning("Company نہیں ملی۔")
            else:
                idx=st.selectbox("Choose Company",found.index,format_func=lambda i:f'{found.loc[i].get("trading_symbol","")} | {found.loc[i].get("isin","")}')
                row=found.loc[idx]; st.write(f"**Company:** {row.get('name','')}"); st.write(f"**ISIN:** {row.get('isin','')}")
                if st.button("Fetch Company Fundamentals"):
                    with st.spinner("Fetching fundamentals..."):
                        data=fundamentals(str(row.get("isin","")))
                    for label,value in data.items():
                        with st.expander(label): st.json(value)

elif page=="Historical Analysis":
    st.markdown('<div class="sa-title">📈 HISTORICAL PRICE ANALYSIS</div>',unsafe_allow_html=True)
    if instruments is None: st.warning("Instrument Database پہلے ڈاؤن لوڈ کریں۔")
    else:
        query=st.text_input("Enter Trading Symbol").strip().upper()
        years=st.selectbox("Historical Period",[1,2,3,5,10,15,20],index=3)
        if query:
            found=instruments[instruments.trading_symbol.astype(str).str.upper().eq(query)]
            if found.empty: st.warning("Trading Symbol نہیں ملا۔")
            else:
                idx=st.selectbox("Select Exchange",found.index,format_func=lambda i:str(found.loc[i].get("Exchange","")))
                if st.button("Fetch Historical Data"):
                    with st.spinner("Downloading Historical Candles..."): hist=get_history(str(found.loc[idx].instrument_key),years)
                    if hist.empty: st.error("Historical Data دستیاب نہیں۔")
                    else:
                        st.success(f"{len(hist):,} records loaded")
                        st.dataframe(hist.tail(100),use_container_width=True,hide_index=True)
                        st.line_chart(hist.set_index("Date")[["Close","EMA 9","EMA 21"]],height=330)
                        st.download_button("⬇️ Download Historical CSV",hist.to_csv(index=False).encode(),f"{query}_historical.csv","text/csv")

elif page=="Custom Screener":
    st.markdown('<div class="sa-title">⚙️ SHAFIQ ALPHA CUSTOM SCREENER</div>',unsafe_allow_html=True)
    if scanner is None or scanner.empty: st.warning("پہلے Live Market Data Refresh کریں۔")
    else:
        data=screener_view(scanner)
        fields=[f for f in data.columns if f not in TEXT_COLUMNS]
        data=type_filter(data,"screener_type")
        exchange=st.selectbox("Exchange",["ALL"]+sorted(scanner["Exchange"].dropna().unique().tolist()),key="screener_exchange")
        if exchange!="ALL": data=data[data["Exchange"]==exchange]

        st.markdown("#### 1️⃣ بنیادی فلٹر (Price / Volume)")
        st.caption("AND میں تمام شرائط پوری ہوں؛ OR میں کم از کم ایک شرط پوری ہو۔")
        logic1=st.radio("Filter Logic",["AND","OR"],horizontal=True,key="screener_logic")
        conds1=condition_builder("custom_conditions",fields,"Volume",100000.0,"b1",True)

        st.markdown("#### 2️⃣ RSI / Market Cap / Fundamentals")
        st.caption("یہ فلٹر صرف پہلے فلٹر کے نتیجے (زیادہ ٹریڈ ویلیو والے اسٹاکس) پر چلتے ہیں۔ خالی چھوڑیں تو یہ مرحلہ نہیں چلے گا۔")
        limit=st.slider("زیادہ سے زیادہ اسٹاکس جن کا ڈیٹا منگوانا ہے",10,300,100,10,key="adv_limit")
        logic2=st.radio("Logic (مرحلہ 2)",["AND","OR"],horizontal=True,key="adv_logic")
        adv_fields=TECH_NAMES+ALIAS_NAMES+[c for c in st.session_state.get("extra_cols",[]) if c not in ALIAS_NAMES]
        conds2=condition_builder("adv_conditions",adv_fields,"RSI 14",30.0,"b2",False)
        show_all=st.checkbox("تمام خام کالم دکھائیں",key="adv_show_all")
        with st.expander("🔧 دستیاب فیلڈز (Upstox سے ملے)"):
            ex_cols=st.session_state.get("extra_cols",[])
            if ex_cols: st.write(", ".join(ex_cols))
            else: st.caption("پہلی بار Run کرنے کے بعد یہاں فہرست آئے گی۔")

        def mini(cs): return [{x:c[x] for x in ["field","operation","value"]} for c in cs]
        signature=json.dumps([mini(conds1),logic1,mini(conds2),logic2,limit,exchange,
                              st.session_state.get("screener_type"),st.session_state.last_refresh],default=str)
        if st.button("🚀 Run Custom Screener"):
            res,cols,n_base,n_short=run_screener(data,conds1,logic1,conds2,logic2,limit)
            st.session_state.last_custom_result=res
            st.session_state["result_cols"]=cols
            st.session_state["result_info"]=(n_base,n_short)
            st.session_state["result_signature"]=signature
        result=st.session_state.last_custom_result
        if isinstance(result,pd.DataFrame):
            if st.session_state.get("result_signature")!=signature:
                st.warning("شرائط بدل گئی ہیں۔ دوبارہ Run Custom Screener دبائیں۔")
            else:
                n_base,n_short=st.session_state.get("result_info",(len(result),len(result)))
                if n_short!=n_base or conds2:
                    st.success(f"بنیادی فلٹر: {n_base:,} ملے · ڈیٹا چیک: {n_short:,} · آخری نتیجہ: {len(result):,}")
                else:
                    st.success(f"{len(result):,} of {len(data):,} listings matched.")
                shown=result if show_all else result[[c for c in st.session_state.get("result_cols",list(result.columns)) if c in result.columns]]
                show_table(shown)
                st.download_button("⬇️ Export Custom Screener",shown.drop(columns=["Instrument Key"],errors="ignore").to_csv(index=False).encode(),"shafiq_alpha_custom_screener.csv","text/csv")

st.divider()
st.markdown("""<div style="text-align:center;color:#9eb5d1;padding:12px">
<div style="font-size:1.2rem;font-weight:900;letter-spacing:.12em;color:#f4d477">SHAFIQ ALPHA</div>
Stock Market Research &amp; Intelligence<br>Founded &amp; Developed by Magray Shafiq<br>
Research and Paper Trading Only | No Live Orders</div>""",unsafe_allow_html=True)
