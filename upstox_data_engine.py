import streamlit as st
import pandas as pd
import numpy as np
import requests, gzip, io, time, base64
from pathlib import Path
from datetime import date, timedelta

# ============================================================
# SHAFIQ ALPHA | STOCK MARKET RESEARCH & INTELLIGENCE
# Founded & Developed by Magray Shafiq
# Research and Paper Trading Only - No Live Orders
# ============================================================

st.set_page_config(
    page_title="SHAFIQ ALPHA | Stock Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = "https://api.upstox.com"
INSTRUMENT_URLS = {
    "NSE": "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz",
    "BSE": "https://assets.upstox.com/market-quote/instruments/exchange/BSE.json.gz"
}
NIFTY_KEY = "NSE_INDEX|Nifty 50"

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
.block-container{max-width:1600px;padding:1rem 1.1rem 2rem}
[data-testid="stSidebar"]{background:#07172b}
h1,h2,h3{color:#f4d477!important}
.sa-hero{display:flex;align-items:center;gap:25px;position:relative;overflow:hidden;
 padding:22px 26px;margin:2px 0 14px;border-radius:22px;
 border:1px solid rgba(255,205,73,.75);
 background:radial-gradient(ellipse at 88% 15%,rgba(0,230,135,.17),transparent 28%),
 linear-gradient(110deg,#07172c,#06101f 62%,#08213a);
 box-shadow:0 12px 34px rgba(0,0,0,.45),inset 0 0 28px rgba(0,145,255,.12)}
.sa-hero:after{content:"";position:absolute;left:-5%;right:-5%;bottom:4px;height:8px;
 background:linear-gradient(90deg,#06b8ff,#f4b928,#fff0a3,#f2a900,#08b9ff);
 transform:rotate(-1.2deg);filter:drop-shadow(0 0 8px #e8b82c)}
.sa-avatar{width:220px;height:220px;flex:0 0 220px;padding:5px;border-radius:50%;
 background:linear-gradient(135deg,#fff4ae,#e8a91d,#fff2a3);
 box-shadow:0 0 0 5px rgba(242,190,54,.16),0 0 32px rgba(255,192,45,.42)}
.sa-avatar img{width:100%;height:100%;object-fit:cover;object-position:center 18%;transform:scale(1.12);
 border-radius:50%;border:3px solid #061326}
.sa-brand-title{font-size:clamp(2.4rem,5vw,4.4rem);font-weight:900;line-height:1.03;
 letter-spacing:.025em;background:linear-gradient(100deg,#ffbd25,#fff1b4 32%,#dceeff 53%,#13c9ff 78%,#71f5ce);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sa-subtitle{font-size:clamp(.85rem,1.7vw,1.25rem);font-weight:800;letter-spacing:.07em;color:#f5f8ff;margin-top:9px}
.sa-credit{font-size:1rem;color:#d5e3f6;margin-top:9px}
.sa-live{display:inline-block;margin-top:11px;padding:7px 13px;border-radius:20px;color:#7fffc2;
 background:rgba(0,220,130,.10);border:1px solid rgba(0,230,145,.45);font-size:.76rem;font-weight:800}
.sa-title{font-size:1.3rem;font-weight:900;color:#f5d66d;margin:16px 0 10px}
.sa-panel{background:linear-gradient(145deg,rgba(9,37,66,.97),rgba(4,15,31,.98));
 border:1px solid rgba(46,157,232,.75);border-radius:17px;padding:14px 16px;
 box-shadow:0 9px 25px rgba(0,0,0,.28)}
.sa-snapshot-row{display:flex;justify-content:space-between;gap:10px;padding:10px 2px;
 border-bottom:1px solid rgba(121,176,220,.24);color:#eaf3ff}
.stButton>button,.stDownloadButton>button{border:1px solid rgba(255,220,103,.8)!important;
 border-radius:10px!important;background:linear-gradient(110deg,#ffe37a,#d99a18)!important;
 color:#111827!important;font-weight:900!important;min-height:2.55rem}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#0d3765,#07182f);
 border:1px solid #168de2;border-radius:16px;padding:13px 15px}
div[data-testid="stMetric"] label{color:#d9eaff!important;font-weight:700}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#fff!important;font-weight:900}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid rgba(43,150,230,.75);border-radius:12px;overflow:hidden}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{background:#0d2037!important;color:#fff!important}
div[data-testid="stRadio"]>div{gap:8px;flex-wrap:nowrap;overflow-x:auto;white-space:nowrap;padding:5px 2px 12px}
div[data-testid="stRadio"] label{flex:0 0 auto;min-width:max-content;color:#eaf3ff!important;background:linear-gradient(145deg,#102944,#07172a);
 border:1px solid #27608a;border-radius:10px;padding:8px 13px;margin:0;min-height:42px}
div[data-testid="stRadio"] label:has(input:checked){background:linear-gradient(110deg,#ffdf62,#e8a91d);border:1px solid #fff0a0}
div[data-testid="stRadio"] label p{color:#eaf3ff!important;font-weight:700} div[data-testid="stRadio"] label:has(input:checked) p{color:#101827!important;font-weight:900}
@media(max-width:700px){
 .block-container{padding-left:.65rem;padding-right:.65rem}
 .sa-hero{gap:12px;padding:15px 10px;border-radius:15px;min-height:230px}
 .sa-avatar{width:190px;height:190px;flex-basis:190px}
 .sa-brand-title{font-size:1.75rem;letter-spacing:0}
 .sa-subtitle{font-size:.65rem;letter-spacing:0}
 .sa-credit{font-size:.72rem}
 .sa-live{font-size:.58rem;padding:5px 7px}
}
</style>
""", unsafe_allow_html=True)

def render_brand():
    photo = Path(__file__).parent / "assets" / "founder_portrait.png"
    if not photo.exists():
        photo = Path(__file__).parent / "founder_portrait.png"
    if photo.exists():
        encoded = base64.b64encode(photo.read_bytes()).decode("ascii")
        avatar = f'<div class="sa-avatar"><img src="data:image/png;base64,{encoded}" alt="Founder"></div>'
    else:
        avatar = '<div class="sa-avatar" style="display:grid;place-items:center;color:#111;font-size:2rem;font-weight:900">SA</div>'
    st.markdown(f"""
    <div class="sa-hero">{avatar}
      <div style="min-width:0;position:relative;z-index:1">
        <div class="sa-brand-title">SHAFIQ ALPHA</div>
        <div class="sa-subtitle">STOCK MARKET RESEARCH &amp; INTELLIGENCE</div>
        <div class="sa-credit">Founded &amp; Developed by Magray Shafiq</div>
        <div class="sa-live">● MARKET RESEARCH &nbsp; | &nbsp; PAPER TRADING ONLY</div>
      </div>
    </div>""", unsafe_allow_html=True)

render_brand()

# Session state
for k,v in {
 "instruments":None,"market_data":None,"scanner_data":None,
 "last_refresh":None,"last_custom_result":None,"custom_conditions":[]
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
    return d.get("data",{}) if "error" not in d else {}

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
    end=date.today(); start=end-timedelta(days=365*years)
    u=f"{BASE}/v3/historical-candle/{key}/days/1/{end}/{start}"
    x=api_get(u,timeout=45); candles=x.get("data",{}).get("candles",[]) if "error" not in x else []
    if not candles: return pd.DataFrame()
    d=pd.DataFrame(candles,columns=["Date","Open","High","Low","Close","Volume","OI"])
    d["Date"]=pd.to_datetime(d["Date"])
    for c in ["Open","High","Low","Close","Volume"]: d[c]=pd.to_numeric(d[c],errors="coerce")
    return add_indicators(d.sort_values("Date"))

def get_nifty_intraday():
    u=f"{BASE}/v3/historical-candle/intraday/{NIFTY_KEY}/1minute"
    x=api_get(u); rows=x.get("data",{}).get("candles",[]) if "error" not in x else []
    if not rows: return pd.DataFrame()
    d=pd.DataFrame(rows,columns=["Date","Open","High","Low","Close","Volume","OI"])
    d["Date"]=pd.to_datetime(d["Date"]); d["Close"]=pd.to_numeric(d["Close"],errors="coerce")
    return d.sort_values("Date")

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
        m={">":s>v,">=":s>=v,"<":s<v,"<=":s<=v,"=":s==v}.get(op)
        if m is not None: masks.append(m.fillna(False))
    if not masks: return d
    result=masks[0]
    for m in masks[1:]: result=(result&m) if logic=="AND" else (result|m)
    return d[result]

# Top navigation replaces the old left-side radio menu
pages=["Dashboard","Market Scanner","Company Search","Company Fundamentals","Historical Analysis","Custom Screener"]
icons=["🏠","🔎","🏢","📊","📈","⚙️"]
page=st.radio("MAIN MENU",pages,horizontal=True,format_func=lambda x:f"{icons[pages.index(x)]} {x}",key="top_navigation")
st.markdown("---")

with st.sidebar:
    st.markdown("## ⚙️ CONTROL PANEL")
    if st.button("🔄 Download NSE + BSE Database",use_container_width=True):
        with st.spinner("Downloading NSE + BSE instruments..."):
            st.session_state.instruments=load_all_instruments()
            st.session_state.market_data=None; st.session_state.scanner_data=None
        st.success(f"{len(st.session_state.instruments):,} instruments loaded")
    if st.button("📡 Refresh Live Market Data",use_container_width=True):
        if st.session_state.instruments is None: st.error("پہلے Database ڈاؤن لوڈ کریں۔")
        else:
            p=st.progress(0)
            with st.spinner("Fetching Upstox Full Market Quotes..."):
                q=fetch_all_quotes(st.session_state.instruments,p)
                st.session_state.market_data=q
                st.session_state.scanner_data=build_scanner_data(st.session_state.instruments,q)
                st.session_state.last_refresh=time.strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"{len(q):,} quote records received")
    st.divider()
    st.caption(f"Database: {len(st.session_state.instruments):,}" if st.session_state.instruments is not None else "Database: Not loaded")
    st.caption(f"Market Quotes: {len(st.session_state.market_data):,}" if st.session_state.market_data is not None else "Market Quotes: Not loaded")
    if st.session_state.last_refresh: st.caption("Last refresh: "+st.session_state.last_refresh)

instruments=st.session_state.instruments
scanner=st.session_state.scanner_data

if page=="Dashboard":
    st.markdown('<div class="sa-title">📊 MARKET DASHBOARD</div>',unsafe_allow_html=True)
    if scanner is None or scanner.empty:
        st.info("شروع کرنے کے لیے Sidebar میں Download NSE + BSE Database، پھر Refresh Live Market Data دبائیں۔")
    else:
        total=len(scanner); live=int(scanner["LTP"].notna().sum()); vols=int(scanner["Volume"].notna().sum())
        a,b,c,d=st.columns(4)
        a.metric("👥 Total Companies",f"{total:,}")
        b.metric("📈 Live Prices",f"{live:,}")
        c.metric("▰ Volume Available",f"{vols:,}")
        d.metric("🏦 Exchanges","NSE + BSE")
        st.write("")
        left,right=st.columns([1.8,1])
        with left:
            st.markdown('<div class="sa-title">📈 MARKET OVERVIEW — NIFTY 50</div>',unsafe_allow_html=True)
            nq=fetch_quote_batch([NIFTY_KEY]); nq=next(iter(nq.values()),{}) if nq else {}
            if nq.get("last_price") is not None:
                lp=float(nq["last_price"]); ch=float(nq.get("net_change") or 0)
                prev=lp-ch; pct=ch/prev*100 if prev else 0
                st.success(f"NIFTY 50  {lp:,.2f}  {'▲' if ch>=0 else '▼'} {pct:+.2f}%")
            nh=cached_nifty()
            if not nh.empty: st.line_chart(nh.set_index("Date")[["Close"]],height=330)
            elif not nq: st.warning("NIFTY 50 feed فی الحال دستیاب نہیں۔")
        with right:
            st.markdown('<div class="sa-title">🌐 MARKET SNAPSHOT</div>',unsafe_allow_html=True)
            valid=scanner.dropna(subset=["LTP"]).copy()
            chg=pd.to_numeric(valid["Net Change"],errors="coerce").fillna(0)
            vol=pd.to_numeric(valid["Volume"],errors="coerce").fillna(0)
            avg=pd.to_numeric(valid["Average Price"],errors="coerce").fillna(pd.to_numeric(valid["LTP"],errors="coerce"))
            traded=float((avg*vol).sum()/1e7)
            st.markdown(f'<div class="sa-panel"><div class="sa-snapshot-row">🟢 Advances <b style="color:#27ee79">{int((chg>0).sum()):,}</b></div><div class="sa-snapshot-row">🔻 Declines <b style="color:#ff5353">{int((chg<0).sum()):,}</b></div><div class="sa-snapshot-row">➖ Unchanged <b style="color:#ffca43">{int((chg==0).sum()):,}</b></div><div class="sa-snapshot-row">💹 Est. Traded Value <b>₹ {traded:,.2f} Cr</b></div></div>',unsafe_allow_html=True)
            st.caption("Estimated value = average price × reported volume; not official exchange turnover.")
        st.markdown('<div class="sa-title">🏆 TOP VOLUME STOCKS</div>',unsafe_allow_html=True)
        top=scanner.dropna(subset=["Volume"]).sort_values("Volume",ascending=False).head(10)
        if top.empty: st.warning("Volume data ابھی دستیاب نہیں۔")
        else:
            show=top[["Symbol","Company","Exchange","LTP","Net Change","Volume"]].copy()
            show.insert(0,"#",range(1,len(show)+1))
            show=show.rename(columns={"LTP":"LTP (₹)","Net Change":"Change (₹)"})
            st.dataframe(show,use_container_width=True,hide_index=True,height=390)
        st.download_button("⬇️ Download Dashboard CSV",scanner.to_csv(index=False).encode(), "shafiq_alpha_dashboard.csv","text/csv")

elif page=="Market Scanner":
    st.markdown('<div class="sa-title">🔎 NSE + BSE MARKET SCANNER</div>',unsafe_allow_html=True)
    if scanner is None or scanner.empty: st.warning("پہلے Live Market Data Refresh کریں۔")
    else:
        x,y,z=st.columns(3); ex=x.selectbox("Exchange",["ALL","NSE","BSE"])
        lo=y.number_input("Minimum Price",min_value=0.0,value=0.0)
        hi=z.number_input("Maximum Price",min_value=0.0,value=100000.0)
        mv=st.number_input("Minimum Daily Volume",min_value=0,value=0)
        out=scanner.copy()
        if ex!="ALL": out=out[out.Exchange==ex]
        out=out[pd.to_numeric(out.LTP,errors="coerce").between(lo,hi)&(pd.to_numeric(out.Volume,errors="coerce")>=mv)]
        st.metric("Matching Stocks",f"{len(out):,}")
        st.dataframe(out,use_container_width=True,hide_index=True)
        st.download_button("⬇️ Export Scanner CSV",out.to_csv(index=False).encode(),"shafiq_alpha_scanner.csv","text/csv")

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
        fields=[f for f in ["LTP","Volume","Net Change","Market Cap (Cr)"] if f in scanner]
        st.info("AND میں تمام شرائط پوری ہوں؛ OR میں کم از کم ایک شرط پوری ہو۔")
        logic=st.radio("Filter Logic",["AND","OR"],horizontal=True)
        if not st.session_state.custom_conditions: st.session_state.custom_conditions=[{"field":"Volume","operation":">","value":100000}]
        if st.button("➕ Add Condition"): st.session_state.custom_conditions.append({"field":fields[0],"operation":">","value":0})
        for i,c in enumerate(st.session_state.custom_conditions):
            a,b,cc,dd=st.columns([2,1,2,1])
            c["field"]=a.selectbox(f"Field {i+1}",fields,index=fields.index(c["field"]) if c["field"] in fields else 0,key=f"f{i}")
            c["operation"]=b.selectbox("Operator",[">",">=","<","<=","="],key=f"o{i}")
            c["value"]=cc.number_input("Value",value=float(c["value"]),key=f"v{i}")
            if dd.button("Remove",key=f"r{i}"):
                st.session_state.custom_conditions.pop(i); st.rerun()
        if st.button("🚀 Run Custom Screener"):
            st.session_state.last_custom_result=apply_filters(scanner,st.session_state.custom_conditions,logic)
        result=st.session_state.last_custom_result
        if isinstance(result,pd.DataFrame):
            st.success(f"{len(result):,} stocks matched.")
            st.dataframe(result,use_container_width=True,hide_index=True)
            st.download_button("⬇️ Export Custom Screener",result.to_csv(index=False).encode(),"shafiq_alpha_custom_screener.csv","text/csv")

st.divider()
st.markdown("""<div style="text-align:center;color:#9eb5d1;padding:12px">
<div style="font-size:1.2rem;font-weight:900;letter-spacing:.12em;color:#f4d477">SHAFIQ ALPHA</div>
Stock Market Research &amp; Intelligence<br>Founded &amp; Developed by Magray Shafiq<br>
Research and Paper Trading Only | No Live Orders</div>""",unsafe_allow_html=True)
