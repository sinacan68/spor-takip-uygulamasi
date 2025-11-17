import streamlit as st
import pandas as pd
import datetime
import os
import json
import altair as alt
# === EN ÖNEMLİ DÜZELTME: Bu satır eksikti ===
from streamlit_gsheets.connection import GSheetsConnection

# --- GSheets Veritabanı Bağlantısını Kur ---
# Artık 'GSheetsConnection' tanınıyor olacak.
conn = st.connection("gsheets", type=GSheetsConnection)

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


# === YENİ VERİ FONKSİYONLARI (Google Sheets için) ===

# --- Antrenman ve Kilo Verileri (CSV yerine) ---
def verileri_yukle(worksheet_adi, sutunlar):
    """
    Google E-Tablosu'ndan Antrenman veya Kilo verisini okur.
    """
    try:
        df = conn.read(worksheet=worksheet_adi, usecols=list(range(len(sutunlar))), header=0)
        df = df.dropna(how="all")

        # Gelen veride sütun adı yoksa (örn. tamamen boş sayfa), bizimkini uygula
        if len(df.columns) == len(sutunlar):
            df.columns = sutunlar
        else:
            return pd.DataFrame(columns=sutunlar)  # Uyumsuzsa boş döndür

        # Tarih formatını düzelt
        if "Tarih" in df.columns:
            df["Tarih"] = pd.to_datetime(df["Tarih"], format='mixed', errors='coerce')
            df = df.dropna(subset=["Tarih"])  # Geçersiz tarih varsa o satırı at

        return df
    except Exception as e:
        # st.warning(f"'{worksheet_adi}' sekmesi okunurken bir hata oluştu: {e}")
        # st.info("Sekme boş olabilir, bu normaldir.")
        return pd.DataFrame(columns=sutunlar)


def veri_kaydet(worksheet_adi, yeni_kayit_df):
    """
    Google E-Tablosu'na yeni bir Antrenman veya Kilo verisi satırı ekler.
    """
    try:
        yeni_veri_listesi = yeni_kayit_df.values.tolist()
        conn.append_rows(worksheet=worksheet_adi, values=yeni_veri_listesi)
        return True
    except Exception as e:
        st.error(f"Veri kaydedilirken hata oluştu: {e}")
        return False


# --- Bırakma Tarihleri (JSON yerine) ---
def yukle_birakma_tarihleri():
    """
    Google E-Tablosu'ndaki 'Tarihler' sekmesini okur ve bir sözlüğe (dict) çevirir.
    """
    try:
        df = conn.read(worksheet="Tarihler", usecols=[0, 1], header=0)
        df = df.dropna(how="all")
        return pd.Series(df.Tarih_Saat.values, index=df.Kategori).to_dict()
    except:
        return {}


def kaydet_birakma_tarihi(kategori, tarih_saat_objesi):
    """
    Google E-Tablosu'ndaki 'Tarihler' sekmesini günceller.
    """
    try:
        df = conn.read(worksheet="Tarihler", header=0)
        df = df.dropna(how="all")

        tarih_str = tarih_saat_objesi.isoformat()

        if kategori in df["Kategori"].values:
            df.loc[df["Kategori"] == kategori, "Tarih_Saat"] = tarih_str
        else:
            yeni_satir = pd.DataFrame([{"Kategori": kategori, "Tarih_Saat": tarih_str}])
            df = pd.concat([df, yeni_satir], ignore_index=True)

        conn.update(worksheet="Tarihler", data=df)
        return True
    except Exception as e:
        st.error(f"Tarih kaydedilirken hata oluştu: {e}")
        return False


# --- Kilo Hedefleri (JSON yerine) ---
def yukle_hedefler():
    """
    Google E-Tablosu'ndaki 'Hedefler' sekmesini okur ve bir sözlüğe çevirir.
    """
    try:
        df = conn.read(worksheet="Hedefler", usecols=[0, 1], header=0)
        df = df.dropna(how="all")
        return pd.Series(df.Deger.values, index=df.Hedef_Adi).to_dict()
    except:
        return {}


def kaydet_hedefler(hedefler_dict):
    """
    Google E-Tablosu'ndaki 'Hedefler' sekmesini günceller.
    """
    try:
        df = pd.DataFrame(list(hedefler_dict.items()), columns=["Hedef_Adi", "Deger"])
        conn.update(worksheet="Hedefler", data=df)
        return True
    except Exception as e:
        st.error(f"Hedefler kaydedilirken hata oluştu: {e}")
        return False


# === YENİ VERİ FONKSİYONLARI BİTTİ ===


# === TEMA: "DİSİPLİN" (CSS KODU) ===
discipline_css = """
<style>
/* ... (Tüm CSS kodunuz aynı kaldı, değişiklik yok) ... */
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

# Verileri en başta bir kez yükleyelim (Artık Google Sheets'ten)
antrenman_df = verileri_yukle("Antrenman", ["Tarih", "Hareket", "Ağırlık_kg", "Tekrar"])
kilo_df = verileri_yukle("Kilo", ["Tarih", "Kilo"])
quit_dates = yukle_birakma_tarihleri()
kilo_hedefleri = yukle_hedefler()

# === KENAR ÇUBUĞU (SIDEBAR) ===
with st.sidebar:
    st.title("Yeni Veri Girişi")
    st.markdown("Günlük kayıtlarınızı girin.")

    with st.expander("🎯 Kilo Hedefleri Belirle", expanded=False):
        with st.form(key="hedef_formu"):
            start_val = float(kilo_hedefleri.get("start_kilo", 0.0))
            goal_val = float(kilo_hedefleri.get("goal_kilo", 0.0))

            start_kilo_input = st.number_input("Başlangıç Kilosu (kg)", min_value=0.0, value=start_val, format="%.1f")
            goal_kilo_input = st.number_input("Hedef Kilo (kg)", min_value=0.0, value=goal_val, format="%.1f")

            hedef_kaydet_butonu = st.form_submit_button("Kilo Hedeflerini Kaydet")

            if hedef_kaydet_butonu:
                yeni_hedefler = {"start_kilo": str(start_kilo_input), "goal_kilo": str(goal_kilo_input)}
                if kaydet_hedefler(yeni_hedefler):
                    st.success("Hedefler kaydedildi!");
                    st.rerun()
                else:
                    st.error("Hedefler kaydedilemedi.")

    with st.expander("⚖️ Yeni Kilo Kaydet", expanded=False):
        with st.form(key="kilo_formu"):
            kilo_tarih = st.date_input("Tarih", datetime.date.today(), key="kilo_tarih")
            kilo = st.number_input("Kilo (kg)", min_value=0.0, step=0.1, format="%.1f", key="kilo_kg")
            kilo_kaydet_butonu = st.form_submit_button(label="Kiloyu Kaydet")
            if kilo_kaydet_butonu:
                if kilo > 0:
                    yeni_kilo_veri_df = pd.DataFrame([
                        {"Tarih": kilo_tarih.isoformat(), "Kilo": kilo}
                    ])
                    if veri_kaydet("Kilo", yeni_kilo_veri_df):
                        st.success(f"{kilo} kg kaydedildi!");
                        st.rerun()
                else:
                    st.error("Geçerli bir kilo girin.")

    with st.expander("🏋️ Yeni Set Kaydet", expanded=True):
        with st.form(key="kayit_formu"):
            ant_tarih = st.date_input("Tarih", datetime.date.today(), key="ant_tarih")
            secilen_hareket = st.selectbox("Hareket", program_hareketleri, key="ant_hareket")
            if secilen_hareket == "Diğer (Manuel Giriş)":
                secilen_hareket = st.text_input("Hareket Adı:", key="ant_hareket_manuel")
            col1, col2 = st.columns(2)
            with col1:
                agirlik = st.number_input("Ağırlık (kg)", min_value=0.0, step=2.5, format="%.1f", key="ant_agirlik")
            with col2:
                tekrar = st.number_input("Tekrar", min_value=0, step=1, key="ant_tekrar")
            kaydet_butonu = st.form_submit_button(label="Seti Kaydet")
            if kaydet_butonu:
                if secilen_hareket and secilen_hareket != "Diğer (Manuel Giriş)":
                    yeni_veri_df = pd.DataFrame([
                        {"Tarih": ant_tarih.isoformat(), "Hareket": secilen_hareket, "Ağırlık_kg": agirlik,
                         "Tekrar": int(tekrar)}
                    ])
                    if veri_kaydet("Antrenman", yeni_veri_df):
                        st.success(f"'{secilen_hareket}' seti eklendi!");
                        st.rerun()
                else:
                    st.error("Lütfen geçerli bir hareket seçin.")

# === ANA SAYFA İÇERİĞİ ===
st.title("Kişisel Gelişim Paneli")
st.markdown("Disiplin, gelişimin temelidir.")
st.markdown("---")

# === METRİK (KPI) PANELİ ===
st.header("Genel Durum (Anlık)")
col1, col2, col3 = st.columns(3)
with col1:
    if not kilo_df.empty:
        kilo_df["Kilo"] = pd.to_numeric(kilo_df["Kilo"], errors='coerce')
        kilo_df = kilo_df.dropna(subset=["Kilo"])
        if not kilo_df.empty:
            son_kilo_kaydi = kilo_df.sort_values(by="Tarih", ascending=False).iloc[0]
            son_kilo = son_kilo_kaydi["Kilo"]
            kilo_delta = None
            if len(kilo_df) > 1:
                onceki_kilo = kilo_df.sort_values(by="Tarih", ascending=False).iloc[1]["Kilo"]
                kilo_delta = son_kilo - onceki_kilo
            st.metric("Mevcut Kilo", f"{son_kilo:.1f} kg",
                      f"{kilo_delta:.1f} kg" if kilo_delta is not None else "İlk Kayıt")
        else:
            st.metric("Mevcut Kilo", "Kayıt Yok")
    else:
        st.metric("Mevcut Kilo", "Kayıt Yok")
with col2:
    if not antrenman_df.empty:
        antrenman_df["Ağırlık_kg"] = pd.to_numeric(antrenman_df["Ağırlık_kg"], errors='coerce')
        antrenman_df = antrenman_df.dropna(subset=["Ağırlık_kg"])
        if not antrenman_df.empty:
            best_lift = antrenman_df.loc[antrenman_df['Ağırlık_kg'].idxmax()]
            st.metric("Kişisel Rekor (PR)", f"{best_lift['Ağırlık_kg']:.1f} kg",
                      f"{best_lift['Hareket']} ({best_lift['Tekrar']} tekrar)")
        else:
            st.metric("Kişisel Rekor (PR)", "Kayıt Yok")
    else:
        st.metric("Kişisel Rekor (PR)", "Kayıt Yok")
with col3:
    toplam_set = len(antrenman_df)
    st.metric("Toplam Kayıtlı Set", f"{toplam_set} set")
st.markdown("---")

# === GRAFİK BÖLÜMÜ (SEKMELER) ===
st.header("Odak Alanları")
tab_matrix, tab_grafik, tab_kilo, tab_sigara, tab_lol = st.tabs([
    "📈 Gelişim Matrisi",
    "🏋️ Antrenman Grafikleri",
    "⚖️ Vücut Ağırlığı",
    "🚬 Sigarayı Bırakma",
    "🎮 LoL'ü Bırakma"
])

# --- Sekme 1: Gelişim Matrisi ---
with tab_matrix:
    st.subheader("Antrenman Programı ve Gelişim Matrisi")
    st.info("Bu tablo, programınızdaki hareketler için en son ve en iyi ağırlıklarınızı 'Excel' gibi gösterir.")
    if antrenman_df.empty:
        st.warning("Matrisi oluşturmak için önce en az bir antrenman seti girmeniz gerekiyor.")
    else:
        antrenman_df["Ağırlık_kg"] = pd.to_numeric(antrenman_df["Ağırlık_kg"], errors='coerce')
        antrenman_df["Tekrar"] = pd.to_numeric(antrenman_df["Tekrar"], errors='coerce')
        antrenman_df_clean = antrenman_df.dropna(subset=["Ağırlık_kg", "Tekrar"])

        defined_exercises = [ex for ex in program_hareketleri if ex != "Diğer (Manuel Giriş)"]
        summary_data = []
        for hareket in defined_exercises:
            hareket_df = antrenman_df_clean[antrenman_df_clean["Hareket"] == hareket]
            if hareket_df.empty:
                summary_data.append(
                    {"Hareket": hareket, "En Son Ağırlık (kg)": "-", "En Son Tekrar": "-", "En İyi Ağırlık (PR)": "-",
                     "En Son Tarih": "-", "Toplam Set": 0})
            else:
                hareket_df_sorted = hareket_df.sort_values(by="Tarih", ascending=False)
                last_entry = hareket_df_sorted.iloc[0]
                pr_entry = hareket_df.loc[hareket_df['Ağırlık_kg'].idxmax()]
                summary_data.append({
                    "Hareket": hareket,
                    "En Son Ağırlık (kg)": f"{last_entry['Ağırlık_kg']:.1f}",
                    "En Son Tekrar": f"{last_entry['Tekrar']:.0f}",
                    "En İyi Ağırlık (PR)": f"{pr_entry['Ağırlık_kg']:.1f}",
                    "En Son Tarih": last_entry['Tarih'].strftime('%Y-%m-%d'),
                    "Toplam Set": len(hareket_df)
                })
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

# --- Sekme 2: Antrenman Grafikleri ---
with tab_grafik:
    if antrenman_df.empty:
        st.info("Grafik göstermek için henüz antrenman kaydı yok.")
    else:
        kayitli_hareketler = sorted(antrenman_df["Hareket"].unique())
        grafik_icin_hareket = st.selectbox("Hangi hareketin grafiğini görmek istersin?", kayitli_hareketler)

        antrenman_df["Ağırlık_kg"] = pd.to_numeric(antrenman_df["Ağırlık_kg"], errors='coerce')
        antrenman_df["Tekrar"] = pd.to_numeric(antrenman_df["Tekrar"], errors='coerce')
        antrenman_df_numeric = antrenman_df.dropna(subset=['Ağırlık_kg', 'Tekrar'])

        hareket_df = antrenman_df_numeric[antrenman_df_numeric["Hareket"] == grafik_icin_hareket].copy()

        if not hareket_df.empty:
            hareket_df = hareket_df.sort_values(by="Tarih")

            st.subheader(f"{grafik_icin_hareket} - Ağırlık Galişimi (kg)")
            st.line_chart(hareket_df, x="Tarih", y="Ağırlık_kg")

            hareket_df["Hacim (kg)"] = hareket_df["Ağırlık_kg"] * hareket_df["Tekrar"]
            st.subheader(f"{grafik_icin_hareket} - Hacim Gelişimi (Ağırlık x Tekrar)")
            st.line_chart(hareket_df, x="Tarih", y="Hacim (kg)")

            with st.expander("Bu harekete ait tüm set kayıtları"):
                st.dataframe(hareket_df.sort_values(by="Tarih", ascending=False))
        else:
            st.warning("Bu hareket için henüz veri yok.")

# --- Sekme 3: Vücut Ağırlığı Grafiği (HEDEF ÇİZGİLİ) ---
with tab_kilo:
    if kilo_df.empty:
        st.info("Grafik göstermek için henüz kilo kaydı yok.")
    else:
        kilo_df["Kilo"] = pd.to_numeric(kilo_df["Kilo"], errors='coerce')
        kilo_df_sirali = kilo_df.dropna(subset=["Kilo"]).sort_values(by="Tarih")

        if kilo_df_sirali.empty:
            st.info("Grafik göstermek için geçerli kilo kaydı yok.")
        else:
            st.subheader("Günlük Kilo Değişimi ve Hedefler")
            base_chart = alt.Chart(kilo_df_sirali).mark_line(point=True).encode(
                x=alt.X('Tarih', title='Tarih'),
                y=alt.Y('Kilo', title='Kilo (kg)'),
                tooltip=['Tarih', 'Kilo']
            ).interactive()

            chart_layers = [base_chart]
            start_kilo = float(kilo_hedefleri.get("start_kilo", 0))
            goal_kilo = float(kilo_hedefleri.get("goal_kilo", 0))

            if start_kilo > 0:
                start_line = alt.Chart(pd.DataFrame({'y': [start_kilo]})).mark_rule(color='#FFA500',
                                                                                    strokeDash=[5, 5]).encode(y='y')
                start_text = alt.Chart(
                    pd.DataFrame({'y': [start_kilo], 'label': [f'Başlangıç: {start_kilo} kg']})).mark_text(
                    align='left', dx=5, dy=-10, color='#FFA500', baseline='bottom'
                ).encode(y='y', text='label')
                chart_layers.append(start_line);
                chart_layers.append(start_text)

            if goal_kilo > 0:
                goal_line = alt.Chart(pd.DataFrame({'y': [goal_kilo]})).mark_rule(color='#238636').encode(y='y')
                goal_text = alt.Chart(pd.DataFrame({'y': [goal_kilo], 'label': [f'Hedef: {goal_kilo} kg']})).mark_text(
                    align='left', dx=5, dy=-10, color='#238636', baseline='bottom'
                ).encode(y='y', text='label')
                chart_layers.append(goal_line);
                chart_layers.append(goal_text)

            final_chart = alt.layer(*chart_layers).properties(title='Kilo Değişim Grafiği')
            st.altair_chart(final_chart, use_container_width=True)

            st.subheader("Haftalık Kilo Ortalaması")
            try:
                kilo_df_haftalik = kilo_df_sirali.set_index("Tarih").resample('W')["Kilo"].mean()
                if not kilo_df_haftalik.empty:
                    st.bar_chart(kilo_df_haftalik)
                else:
                    st.info("Haftalık ortalama için yeterli veri yok.")
            except Exception as e:
                st.error(f"Haftalık ortalama hesaplanırken bir hata oluştu: {e}")

            with st.expander("Tüm kilo kayıtları"):
                st.dataframe(kilo_df_sirali.sort_values(by="Tarih", ascending=False))

# --- Sekme 4: Sigara Bırakma ---
with tab_sigara:
    st.subheader("Sigarayı Bırakma Takipçisi")
    kategori_key = "smoking_quit_date"

    if kategori_key in quit_dates:
        try:
            quit_datetime = datetime.datetime.fromisoformat(quit_dates[kategori_key])
            simdi = datetime.datetime.now()
            gecen_zaman = (simdi - quit_datetime)

            if gecen_zaman.total_seconds() < 0:
                toplam_gun = 0;
                kalan_saat = 0
                st.warning(
                    f"Bırakma tarihi gelecek bir tarih ({quit_datetime.strftime('%Y-%m-%d %H:%M')}). Sayaç 0 olarak ayarlandı.")
            else:
                toplam_gun = gecen_zaman.days;
                kalan_saat = gecen_zaman.seconds // 3600

            gosterim_metni = f"{toplam_gun} gün {kalan_saat} saat"
            st.metric("🚭 Sigarasız Geçen Süre", gosterim_metni)
            st.success(f"Tebrikler! {quit_datetime.strftime('%Y-%m-%d %H:%M')} tarihinden beri sigara içmiyorsunuz.")

            with st.expander("Tarihi/Saati Değiştir veya Sıfırla"):
                st.error("Yeni bir tarih/saat seçmek, eski kaydı kalıcı olarak değiştirecektir.")
                guncel_tarih = st.date_input("Yeni Bırakma Tarihi", value=quit_datetime.date(), key="sigara_yeni_tarih")
                guncel_saat = st.time_input("Yeni Bırakma Saati", value=quit_datetime.time(), key="sigara_yeni_saat")

                if st.button("Tarihi Güncelle", key="sigara_guncelle"):
                    yeni_datetime = datetime.datetime.combine(guncel_tarih, guncel_saat)
                    if kaydet_birakma_tarihi(kategori_key, yeni_datetime):
                        st.success("Tarih/saat güncellendi!");
                        st.rerun()

        except Exception as e:
            st.error(f"Kayıtlı tarih okunurken bir hata oluştu: {e}. Lütfen tarihi sıfırlayın.")
            if st.button("Kaydı Sıfırla", key="sigara_bozuk_sifirla"):
                kaydet_birakma_tarihi(kategori_key, datetime.datetime.now());
                st.rerun()
    else:
        st.info("Sigarayı bıraktığınız tarih ve saati seçin, sayacı başlatın.")
        with st.form(key="sigara_formu"):
            secilen_tarih = st.date_input("Hangi tarihte bıraktınız?", datetime.date.today())
            secilen_saat = st.time_input("Hangi saatte bıraktınız? (24-saat formatı)", datetime.time(0, 0))
            kaydet_butonu = st.form_submit_button("Sayacı Başlat")
            if kaydet_butonu:
                yeni_datetime = datetime.datetime.combine(secilen_tarih, secilen_saat)
                if yeni_datetime > datetime.datetime.now(): st.warning("Gelecek bir tarih/saat seçtiniz.")
                if kaydet_birakma_tarihi(kategori_key, yeni_datetime):
                    st.success("Tarih/saat kaydedildi! Sayacınız başladı.");
                    st.rerun()
                else:
                    st.error("Tarih/saat kaydedilemedi.")

# --- Sekme 5: LoL Bırakma ---
with tab_lol:
    st.subheader("League of Legends Bırakma Takipçisi")
    kategori_key_lol = "lol_quit_date"

    if kategori_key_lol in quit_dates:
        try:
            quit_datetime_lol = datetime.datetime.fromisoformat(quit_dates[kategori_key_lol])
            simdi_lol = datetime.datetime.now()
            gecen_zaman_lol = (simdi_lol - quit_datetime_lol)

            if gecen_zaman_lol.total_seconds() < 0:
                toplam_gun_lol = 0;
                kalan_saat_lol = 0
                st.warning(
                    f"Bırakma tarihi gelecek bir tarih ({quit_datetime_lol.strftime('%Y-%m-%d %H:%M')}). Sayaç 0 olarak ayarlandı.")
            else:
                toplam_gun_lol = gecen_zaman_lol.days;
                kalan_saat_lol = gecen_zaman_lol.seconds // 3600

            gosterim_metni_lol = f"{toplam_gun_lol} gün {kalan_saat_lol} saat"
            st.metric("🎮 Oynamadan Geçen Süre", gosterim_metni_lol)
            st.success(f"Tebrikler! {quit_datetime_lol.strftime('%Y-%m-%d %H:%M')} tarihinden beri oynamıyorsunuz.")

            with st.expander("Tarihi/Saati Değiştir veya Sıfırla"):
                st.error("Yeni bir tarih/saat seçmek, eski kaydı kalıcı olarak değiştirecektir.")
                guncel_tarih_lol = st.date_input("Yeni Bırakma Tarihi", value=quit_datetime_lol.date(),
                                                 key="lol_yeni_tarih")
                guncel_saat_lol = st.time_input("Yeni Bırakma Saati", value=quit_datetime_lol.time(),
                                                key="lol_yeni_saat")

                if st.button("Tarihi Güncelle", key="lol_guncelle"):
                    yeni_datetime_lol = datetime.datetime.combine(guncel_tarih_lol, guncel_saat_lol)
                    if kaydet_birakma_tarihi(kategori_key_lol, yeni_datetime_lol):
                        st.success("Tarih/saat güncellendi!");
                        st.rerun()

        except Exception as e:
            st.error(f"Kayıtlı tarih okunurken bir hata oluştu: {e}. Lütfen tarihi sıfırlayın.")
            if st.button("Kaydı Sıfırla", key="lol_bozuk_sifirla"):
                kaydet_birakma_tarihi(kategori_key_lol, datetime.datetime.now());
                st.rerun()
    else:
        st.info("League of Legends'ı bıraktığınız tarih ve saati seçin, sayacı başlatın.")
        with st.form(key="lol_formu"):
            secilen_tarih_lol = st.date_input("Hangi tarihte bıraktınız?", datetime.date.today(), key="lol_tarih")
            secilen_saat_lol = st.time_input("Hangi saatte bıraktınız? (24-saat formatı)", datetime.time(0, 0),
                                             key="lol_saat")
            kaydet_butonu_lol = st.form_submit_button("Sayacı Başlat")
            if kaydet_butonu_lol:
                yeni_datetime_lol = datetime.datetime.combine(secilen_tarih_lol, secilen_saat_lol)
                if yeni_datetime_lol > datetime.datetime.now(): st.warning("Gelecek bir tarih/saat seçtiniz.")
                if kaydet_birakma_tarihi(kategori_key_lol, yeni_datetime_lol):
                    st.success("Tarih/saat kaydedildi! Sayacınız başladı.");
                    st.rerun()
                else:
                    st.error("Tarih/saat kaydedilemedi.")

# --- Sağ Alt Köşe Yazısı ---
bottom_right_text_html = """
<div class="bottom-right-text">
Ne için başladığını unutma.
</div>
"""
st.markdown(bottom_right_text_html, unsafe_allow_html=True)