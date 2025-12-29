import streamlit as st
import pandas as pd
import datetime
import os
import json 
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- GSheets Veritabanı Bağlantısını Kur ---
def connect_gsheets():
    try:
        creds_str = st.secrets["connections"]["gsheets"]["service_account_info_str"]
        creds_json = json.loads(creds_str) 
        worksheet_name = st.secrets["connections"]["gsheets"]["worksheet_name"]
        
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open(worksheet_name)
        return spreadsheet
    except Exception as e:
        st.error(f"Google Sheets'e bağlanırken kritik hata (Secrets kontrolü): {e}")
        return None

ss = connect_gsheets()

# --- Antrenman Programı ---
program_lower = [
    "Bird Dog", "Superman", "Adduction (Kalça iç bacak makinesi)", 
    "Leg Extension", "Leg Curl", "Leg Press", "Standing Calf Raise",
    "Machine Fly", "Incline Dumbbell Press"
]
program_upper = [
    "Bird Dog", "Superman", "Lat Pulldown", "Seated Lateral Raise",
    "Rear Delt Fly Machine", "Triceps Pushdown (kablo)", "Preacher Curl",
    "Triceps Overhead Rope Extension", "Incline DB Curl", "Incline DB Shrug"
]
program_hareketleri = sorted(list(set(program_lower + program_upper)))
program_hareketleri.append("Diğer (Manuel Giriş)")

# === VERİ FONKSİYONLARI ===
def verileri_yukle(worksheet_adi, sutunlar):
    if ss is None: return pd.DataFrame(columns=sutunlar) 
    try:
        worksheet = ss.worksheet(worksheet_adi)
        data = worksheet.get_all_records()
        df = pd.DataFrame.from_records(data)
        
        if df.empty:
            return pd.DataFrame(columns=sutunlar)
        
        if len(df.columns) == len(sutunlar):
             df.columns = sutunlar
        
        if "Tarih" in df.columns:
            df["Tarih"] = pd.to_datetime(df["Tarih"], format='mixed', errors='coerce')
            df = df.dropna(subset=["Tarih"])
            
        return df
    except Exception as e:
        return pd.DataFrame(columns=sutunlar)

def veri_kaydet(worksheet_adi, yeni_kayit_df):
    if ss is None: return False
    try:
        worksheet = ss.worksheet(worksheet_adi)
        yeni_veri_listesi = yeni_kayit_df.values.tolist()
        worksheet.append_rows(yeni_veri_listesi, value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        st.error(f"Veri kaydedilirken hata oluştu: {e}")
        return False

def gsheet_to_dict(worksheet_adi, key_col, val_col):
    if ss is None: return {}
    try:
        worksheet = ss.worksheet(worksheet_adi)
        data = worksheet.get_all_records()
        df = pd.DataFrame.from_records(data)
        if df.empty: return {}
        df = df.dropna(how="all")
        return pd.Series(df[val_col].values, index=df[key_col]).to_dict()
    except: return {}

def dict_to_gsheet(worksheet_adi, data_dict, key_col, val_col):
    if ss is None: return False
    try:
        worksheet = ss.worksheet(worksheet_adi)
        df = pd.DataFrame(list(data_dict.items()), columns=[key_col, val_col])
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist(), value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        st.error(f"'{worksheet_adi}' sekmesi güncellenirken hata oluştu: {e}")
        return False

# --- Yardımcı Fonksiyonlar ---
def yukle_birakma_tarihleri():
    return gsheet_to_dict("Tarihler", "Kategori", "Tarih_Saat")

def kaydet_birakma_tarihi(kategori, tarih_saat_objesi):
    data = yukle_birakma_tarihleri()
    data[kategori] = tarih_saat_objesi.isoformat()
    return dict_to_gsheet("Tarihler", data, "Kategori", "Tarih_Saat")

def yukle_hedefler():
    return gsheet_to_dict("Hedefler", "Hedef_Adi", "Deger")

def kaydet_hedefler(hedefler_dict):
    return dict_to_gsheet("Hedefler", hedefler_dict, "Hedef_Adi", "Deger")

# === TEMA: "DİSİPLİN" (CSS KODU) ===
discipline_css = """
<style>
.stApp {
    background-image: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), url("https://wallpapercave.com/wp/wp6376332.jpg");
    background-size: cover; background-repeat: no-repeat; background-attachment: fixed;
    color: #C9D1D9;
}
.css-1d391kg { background-color: #161B22; border-right: 1px solid #30363D; background-image: none; }
h1, h2 { color: #FAFAFA; font-weight: bold; }
h3 { color: #E0E0E0; }
.stButton > button {
    background-color: #238636; color: #FFFFFF; border: none; border-radius: 8px;
    font-weight: bold; padding: 10px 24px; transition: all 0.3s ease;
}
.stButton > button:hover { background-color: #1A6328; transform: scale(1.02); }
.stMetric {
    background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 15px;
}
.stMetric > div > div:nth-child(2) { color: #FAFAFA; font-size: 2.5rem; }
.stMetric > div:nth-child(2) { color: #3FB950; }
.stMetric > div:nth-child(2) div[data-testid="metric-delta-negative"] { color: #F85149; }
[data-testid="stVerticalBlock"] .stMetric > div > div:nth-child(2) { font-size: 3.5rem; }
footer { visibility: hidden; }
.bottom-right-text {
    position: fixed; bottom: 10px; right: 15px; font-size: 1.1rem;
    font-style: italic; font-family: 'Georgia', serif; color: #C9D1D9; opacity: 0.7; z-index: 1000;
}
</style>
"""
st.markdown(discipline_css, unsafe_allow_html=True)

# === ARAYÜZ BAŞLANGICI ===
st.set_page_config(page_title="Gelişim Takipçisi", layout="wide")

# Verileri Yükle
antrenman_df = verileri_yukle("Antrenman", ["Tarih", "Hareket", "Ağırlık_kg", "Tekrar"])
kilo_df = verileri_yukle("Kilo", ["Tarih", "Kilo"])
quit_dates = yukle_birakma_tarihleri()
kilo_hedefleri = yukle_hedefler() 

# === KENAR ÇUBUĞU ===
with st.sidebar:
    st.title("Veri Girişi")
    
    with st.expander("🎯 Kilo Hedefleri", expanded=False):
        with st.form(key="hedef_formu"):
            start_val = float(kilo_hedefleri.get("start_kilo", 0.0))
            goal_val = float(kilo_hedefleri.get("goal_kilo", 0.0))
            start_kilo_input = st.number_input("Başlangıç (kg)", min_value=0.0, value=start_val, format="%.1f")
            goal_kilo_input = st.number_input("Hedef (kg)", min_value=0.0, value=goal_val, format="%.1f")
            if st.form_submit_button("Kaydet"):
                yeni_hedefler = {"start_kilo": str(start_kilo_input), "goal_kilo": str(goal_kilo_input)}
                if kaydet_hedefler(yeni_hedefler): st.success("Kaydedildi!"); st.rerun()

    with st.expander("⚖️ Kilo Girişi", expanded=False):
        with st.form(key="kilo_formu"):
            kilo_tarih = st.date_input("Tarih", datetime.date.today())
            kilo = st.number_input("Kilo (kg)", min_value=0.0, step=0.1, format="%.1f")
            if st.form_submit_button("Kaydet"):
                if kilo > 0:
                    if veri_kaydet("Kilo", pd.DataFrame([{"Tarih": kilo_tarih.isoformat(), "Kilo": kilo}])):
                        st.success("Kaydedildi!"); st.rerun()

    with st.expander("🏋️ Antrenman Girişi", expanded=True):
        with st.form(key="kayit_formu"):
            ant_tarih = st.date_input("Tarih", datetime.date.today())
            secilen_hareket = st.selectbox("Hareket", program_hareketleri)
            if secilen_hareket == "Diğer (Manuel Giriş)":
                secilen_hareket = st.text_input("Hareket Adı:")
            col1, col2 = st.columns(2)
            with col1: agirlik = st.number_input("Ağırlık (kg)", min_value=0.0, step=2.5, format="%.1f")
            with col2: tekrar = st.number_input("Tekrar", min_value=0, step=1)
            if st.form_submit_button("Kaydet"):
                if secilen_hareket:
                    if veri_kaydet("Antrenman", pd.DataFrame([{"Tarih": ant_tarih.isoformat(), "Hareket": secilen_hareket, "Ağırlık_kg": agirlik, "Tekrar": int(tekrar)}])):
                        st.success("Eklendi!"); st.rerun()

# === ANA SAYFA ===
st.title("Kişisel Gelişim Paneli")
st.markdown("---")

# === KPI PANELİ ===
col1, col2, col3 = st.columns(3)
with col1:
    if not kilo_df.empty:
        kilo_df["Kilo"] = pd.to_numeric(kilo_df["Kilo"], errors='coerce')
        son_kilo = kilo_df.dropna(subset=["Kilo"]).sort_values(by="Tarih", ascending=False).iloc[0]["Kilo"]
        st.metric("Mevcut Kilo", f"{son_kilo:.1f} kg")
    else: st.metric("Mevcut Kilo", "--")
with col2:
    if not antrenman_df.empty:
        antrenman_df["Ağırlık_kg"] = pd.to_numeric(antrenman_df["Ağırlık_kg"], errors='coerce')
        best = antrenman_df.dropna(subset=["Ağırlık_kg"]).loc[antrenman_df['Ağırlık_kg'].idxmax()]
        st.metric("En İyi Kaldırış (PR)", f"{best['Ağırlık_kg']:.1f} kg", f"{best['Hareket']}")
    else: st.metric("En İyi Kaldırış (PR)", "--")
with col3:
    st.metric("Toplam Antrenman Seti", len(antrenman_df))
st.markdown("---")

# === SEKMELER (SANSÜRLÜ) ===
# Son sekme adını 'XX' olarak değiştirdik.
tab_matrix, tab_grafik, tab_kilo, tab_sigara, tab_lol, tab_pmo = st.tabs([
    "📈 Gelişim", "🏋️ Grafikler", "⚖️ Kilo Analiz", "🚬 Sigara", "🎮 LoL", "🚫 XX"
])

with tab_matrix:
    if not antrenman_df.empty:
        antrenman_df["Ağırlık_kg"] = pd.to_numeric(antrenman_df["Ağırlık_kg"], errors='coerce')
        antrenman_df["Tekrar"] = pd.to_numeric(antrenman_df["Tekrar"], errors='coerce')
        df_clean = antrenman_df.dropna(subset=["Ağırlık_kg", "Tekrar"])
        summary = []
        for h in [x for x in program_hareketleri if x != "Diğer (Manuel Giriş)"]:
            h_df = df_clean[df_clean["Hareket"] == h]
            if not h_df.empty:
                last = h_df.sort_values(by="Tarih", ascending=False).iloc[0]
                pr = h_df.loc[h_df['Ağırlık_kg'].idxmax()]
                summary.append({
                    "Hareket": h, "Son Ağırlık": last['Ağırlık_kg'], "Son Tekrar": last['Tekrar'],
                    "PR (En İyi)": pr['Ağırlık_kg'], "Tarih": last['Tarih'].strftime('%Y-%m-%d')
                })
        st.dataframe(pd.DataFrame(summary), use_container_width=True)
    else: st.info("Henüz veri yok.")

with tab_grafik:
    if not antrenman_df.empty:
        h = st.selectbox("Hareket Seç", sorted(antrenman_df["Hareket"].unique()))
        h_df = antrenman_df[antrenman_df["Hareket"] == h].copy()
        if not h_df.empty:
            h_df["Tarih"] = pd.to_datetime(h_df["Tarih"])
            st.line_chart(h_df.sort_values("Tarih"), x="Tarih", y="Ağırlık_kg")

with tab_kilo:
    if not kilo_df.empty:
        kilo_df["Kilo"] = pd.to_numeric(kilo_df["Kilo"], errors='coerce')
        df_k = kilo_df.dropna(subset=["Kilo"]).sort_values("Tarih")
        base = alt.Chart(df_k).mark_line(point=True).encode(x='Tarih', y='Kilo', tooltip=['Tarih', 'Kilo']).interactive()
        
        layers = [base]
        s_k = float(kilo_hedefleri.get("start_kilo", 0)); g_k = float(kilo_hedefleri.get("goal_kilo", 0))
        if s_k > 0: layers.append(alt.Chart(pd.DataFrame({'y': [s_k]})).mark_rule(color='orange').encode(y='y'))
        if g_k > 0: layers.append(alt.Chart(pd.DataFrame({'y': [g_k]})).mark_rule(color='green').encode(y='y'))
        
        st.altair_chart(alt.layer(*layers).properties(title='Kilo Gelişimi'), use_container_width=True)

# --- SAYAÇLAR İÇİN ORTAK FONKSİYON ---
def create_counter(tab_obj, key_name, title, desc):
    with tab_obj:
        st.subheader(title)
        if key_name in quit_dates:
            try:
                q_date = datetime.datetime.fromisoformat(quit_dates[key_name])
                diff = datetime.datetime.now() - q_date
                days = diff.days; hours = diff.seconds // 3600
                if diff.total_seconds() < 0: st.warning("Gelecek tarih seçili!"); days=0; hours=0
                
                st.metric(f"Temiz Geçen Süre", f"{days} gün {hours} saat")
                st.success(f"Başlangıç: {q_date.strftime('%d.%m.%Y %H:%M')}")
                
                with st.expander("Sıfırla / Tarihi Düzenle"):
                    d = st.date_input("Tarih", q_date.date(), key=f"{key_name}_d")
                    t = st.time_input("Saat", q_date.time(), key=f"{key_name}_t")
                    if st.button("Güncelle", key=f"{key_name}_btn"):
                        if kaydet_birakma_tarihi(key_name, datetime.datetime.combine(d, t)): st.rerun()
            except: st.error("Tarih hatası. Sıfırlayın."); kaydet_birakma_tarihi(key_name, datetime.datetime.now())
        else:
            st.info(f"{desc} sayacını başlat:")
            with st.form(key=f"{key_name}_form"):
                d = st.date_input("Tarih", datetime.date.today())
                t = st.time_input("Saat", datetime.time(0,0))
                if st.form_submit_button("Başlat"):
                     kaydet_birakma_tarihi(key_name, datetime.datetime.combine(d, t)); st.rerun()

# Sayaçları Oluştur
create_counter(tab_sigara, "smoking_quit_date", "Sigarayı Bırakma", "Sigarasızlık")
create_counter(tab_lol, "lol_quit_date", "LoL'ü Bırakma", "LoL Oynamama")

# BURASI DEĞİŞTİ: Başlık ve açıklama "XX" yapıldı.
create_counter(tab_pmo, "pmo_quit_date", "XX Sayacı", "XX yapmama")

st.markdown('<div class="bottom-right-text">Ne için başladığını unutma.</div>', unsafe_allow_html=True)
