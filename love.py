import base64
import io
import os
import random

import requests
import streamlit as st
from PIL import Image, ImageOps

# ============================================================
# 1. EDIT BAGIAN INI: nama, foto, musik, teks, dan alur halaman
# ============================================================
NAMA = "mega"  # ganti dengan nama dia

# Musik latar: taruh satu file lagu (.mp3/.m4a/.ogg/.wav) di folder "musik"
# yang berada di samping file ini. Nama file bebas. Disarankan di bawah 5 MB.
# Biarkan True saat mencoba di laptop agar pesan masalah muncul di layar.
# Ubah ke False sebelum deploy.
TAMPILKAN_PERINGATAN = False

# Notifikasi ke HP kamu lewat ntfy.sh (gratis, tanpa akun).
# Ganti dengan kode acak yang panjang dan susah ditebak, lalu berlangganan
# topik yang sama di aplikasi ntfy di HP kamu.
TOPIK_NTFY = "i-love-u-mega-ayu-balqis-250525"

# Setiap halaman punya: gambar (opsional), judul, teks.
# Pilih salah satu bentuk tombol:
#   "tombol": (teks, tujuan)                     -> satu tombol
#   "kiri": (teks, tujuan) + "kanan": (teks, tujuan) -> dua tombol
# Halaman tanpa tombol akan jadi halaman akhir.
PAGES = {
    "cover": {
        "gambar": None,
        "judul": "Dari aku buat Kamu",
        "teks": "Nyalain suara HP nya yaa, abis itu buka pesan ini<3.",
        "tombol": ("Buka pesan", "awal"),
    },
    "awal": {
        "gambar": "foto/1.jpg",
        "judul": "Hai, {nama}",
        "teks": "Aku gatau ini bakal bikin perasaan kamu membaik atau engga, but i hope this make u happy today. Boleh aku minta waktunya sebentar buat baca ini sampe akhir?",
        "kiri": ("Boleh, aku bakal baca sampe akhir", "cerita"),
        "kanan": ("Nanti dulu deh, aku sibuk bgt", "nanti"),
    },
    "nanti": {
        "gambar": "foto/2.jpg",
        "judul": "YAHH, aku cuman mau minta maaf",
        "teks": "Aku gamau kamu pergi dan aku gamau liat kamu sama cowo lain, KAMU TUH PUNYA AKUU!!",
        "kiri": ("Yaudah, aku mau baca", "cerita"),
        "kanan": ("Balik ke awal", "awal"),
    },
    "cerita": {
        "gambar": "foto/3.jpg",
        "judul": "Sayang, aku minta maaf yaa",
        "teks": "Maafin semua kesalahan aku yg gabisa aku sebut satu-satu yaa. Aku bener-bener serius sama hubungan ini. Aku mau kita balik kaya dulu, saling sayang satu sama lain.",
        "kiri": ("IYAA, aku maafin ko :)", "perasaan"),
        "kanan": ("Terus?", "perasaan"),
    },
    "perasaan": {
        "gambar": "foto/4.jpg",
        "judul": "Aku sayang kamu, {nama}",
        "teks": "Aku mau kita mulai lagi semuanya, aku mau kita bangkit dan kita berubah jadi lebih baik. Kamu mau maafin aku dan balik lagi sama aku?",
        "kiri": ("Iya, aku mau", "ya"),
        "kanan": ("Maaf, belum bisa", "tidak"),
    },
    "ya": {
        "gambar": "foto/5.jpg",
        "judul": "YEAYYYY, aku bakal buktiin",
        "teks": "Kita pacaran lagii sekarang. Kali ini aku serius dan semoga aku bisa balikin perasaaan kamu ke aku. BTW, klo kamu tau lagu ini relate bgt sama kita tau, aku sengaja pilih lagu ini karena maknanya dalem bgt",
        "balon": True,
    },
    "tidak": {
        "gambar": None,
        "judul": "Terima kasih sudah jujur",
        "teks": "Aku menghargai jawabanmu. Aku bakal nunggu kamu terus dan aku bakal berusaha untuk jadi lebih baik demi kamu. kamu bakal tetep jadi tujuan hidup aku. love u meg",
    },
}
HALAMAN_COVER = "cover"
HALAMAN_ULANG = "awal"  # tujuan tombol "Ulangi dari awal" (musik tetap jalan)

# ============================================================
# 2. TAMPILAN (CSS) dan latar hati melayang
# ============================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@600&family=DM+Sans:wght@400;500&display=swap');

.stApp {
  background: linear-gradient(160deg, #2B1030 0%, #6B2148 100%);
  background-attachment: fixed;
}
header, footer, #MainMenu { visibility: hidden; }

/* Hati melayang memenuhi seluruh layar, di belakang isi */
.hearts { position: fixed; inset: 0; overflow: hidden; z-index: 0; pointer-events: none; }
.heart {
  position: absolute; bottom: -60px; line-height: 1; opacity: 0;
  animation-name: melayang; animation-timing-function: linear; animation-iteration-count: infinite;
}
@keyframes melayang {
  0%   { transform: translate(0, 0) rotate(0deg); opacity: 0; }
  10%  { opacity: .7; }
  90%  { opacity: .7; }
  100% { transform: translate(var(--geser), -115vh) rotate(var(--putar)); opacity: 0; }
}

/* Isi memenuhi layar HP; di layar lebar jadi kolom tengah */
.block-container, [data-testid="stMainBlockContainer"] {
  position: relative; z-index: 1;
  width: 100%;
  max-width: 560px !important;
  min-height: 100dvh;
  margin: 0 auto !important;
  padding: 2rem 1.5rem 5.5rem 1.5rem !important;
  background: transparent;
}
.block-container > [data-testid="stVerticalBlock"] {
  min-height: calc(100dvh - 7.5rem);
  justify-content: center;
  gap: 1.25rem;
}
@media (min-width: 700px) {
  .block-container, [data-testid="stMainBlockContainer"] {
    margin: 4vh auto !important;
    min-height: 92vh;
    border-radius: 24px;
    background: rgba(43, 16, 48, 0.55);
  }
  .block-container > [data-testid="stVerticalBlock"] { min-height: calc(92vh - 7.5rem); }
}

.isi, .isi .judul, .isi .teks { text-align: center !important; }
.isi { animation: muncul .7s ease both; }
@keyframes muncul { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
.isi img { width: 100%; max-height: 42dvh; object-fit: cover; border-radius: 18px; margin-bottom: 1.25rem; }
.isi .judul { font-family: 'Caveat', cursive; font-size: 3.1rem; line-height: 1.1; color: #FFF1F4; margin: 0 0 .6rem 0; text-shadow: 0 2px 12px rgba(43,16,48,.8); }
.isi .teks  { font-family: 'DM Sans', sans-serif; font-size: 1.15rem; line-height: 1.65; color: #FFE3EA; max-width: 40ch; margin: 0 auto; text-shadow: 0 1px 8px rgba(43,16,48,.8); }

/* Tombol selebar layar dan mudah ditekan jempol */
.stButton, [data-testid="stButton"] { width: 100% !important; }
.stButton > button { width: 100% !important; min-height: 3.4rem; border-radius: 16px; padding: .7rem 1rem; }
.stButton > button p, .stButton > button div { font-family: 'DM Sans', sans-serif; font-weight: 500; font-size: 1.05rem; }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] { background: #FF5C8A; border: 2px solid #FF5C8A; }
.stButton > button[kind="primary"] *, .stButton > button[data-testid="stBaseButton-primary"] * { color: #2B1030 !important; }
.stButton > button[kind="secondary"], .stButton > button[data-testid="stBaseButton-secondary"] { background: rgba(43,16,48,.5); border: 2px solid #FFB3C6; }
.stButton > button[kind="secondary"] *, .stButton > button[data-testid="stBaseButton-secondary"] * { color: #FFD6E0 !important; }
.stButton > button:hover { filter: brightness(1.1); }
.stButton > button:focus-visible { outline: 3px solid #FFF1F4; outline-offset: 2px; }

/* Pemutar musik kecil di bawah layar */
[data-testid="stAudio"] {
  position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%);
  width: min(92vw, 420px); height: 40px; z-index: 5; opacity: .9;
}

@media (prefers-reduced-motion: reduce) {
  .heart { animation: none; opacity: .5; bottom: auto; top: var(--atas); }
  .isi { animation: none; }
}
</style>
"""


def hati_melayang(jumlah=28):
    acak = random.Random(7)  # seed tetap supaya posisi hati konsisten
    warna = ["#FF8FAB", "#FFB3C6", "#FF5C8A", "#FFD6E0"]
    bagian = []
    for _ in range(jumlah):
        ukuran = acak.randint(16, 44)
        gaya = (
            f"left:{acak.randint(0, 96)}%;"
            f"font-size:{ukuran}px;"
            f"color:{acak.choice(warna)};"
            f"animation-duration:{acak.randint(9, 20)}s;"
            f"animation-delay:-{acak.randint(0, 18)}s;"
            f"--geser:{acak.randint(-60, 60)}px;"
            f"--putar:{acak.randint(-40, 40)}deg;"
            f"--atas:{acak.randint(5, 90)}%;"
        )
        bagian.append(f'<span class="heart" style="{gaya}">&#9829;</span>')
    return '<div class="hearts" aria-hidden="true">' + "".join(bagian) + "</div>"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def cari_musik():
    folder = os.path.join(BASE_DIR, "musik")
    if os.path.isdir(folder):
        for nama in sorted(os.listdir(folder)):
            if nama.lower().endswith((".mp3", ".m4a", ".ogg", ".wav")):
                return os.path.join(folder, nama)
    return None


EKSTENSI_GAMBAR = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def cari_gambar(nama):
    # Cocokkan berdasarkan nama tanpa ekstensi: "foto/1.jpg" akan menemukan
    # 1.jpg, 1.JPG, 1.jpeg, 1.png, dan seterusnya di folder "foto".
    if not nama:
        return None
    nama_dasar = os.path.splitext(os.path.basename(nama))[0].lower()
    folder = os.path.join(BASE_DIR, "foto")
    if os.path.isdir(folder):
        for berkas in sorted(os.listdir(folder)):
            dasar, ekstensi = os.path.splitext(berkas)
            if dasar.lower() == nama_dasar and ekstensi.lower() in EKSTENSI_GAMBAR:
                return os.path.join(folder, berkas)
    return None


@st.cache_data(show_spinner=False)
def gambar_base64(path):
    # GIF dipakai apa adanya supaya tetap bergerak.
    if path.lower().endswith(".gif"):
        with open(path, "rb") as f:
            return "gif", base64.b64encode(f.read()).decode()
    # Foto HP biasanya besar. Dikecilkan dan diputar sesuai orientasinya.
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img.thumbnail((1000, 1000))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return "jpeg", base64.b64encode(buf.getvalue()).decode()


def gambar_html(nama):
    path = cari_gambar(nama)
    if not path:
        return ""
    try:
        jenis, data = gambar_base64(path)
    except Exception:
        return ""
    return f'<img src="data:image/{jenis};base64,{data}" alt="Foto kenangan">'


# ============================================================
# 3. LOGIKA HALAMAN
# ============================================================
st.set_page_config(page_title="Untukmu", page_icon="💌", layout="centered")

if "halaman" not in st.session_state:
    st.session_state.halaman = HALAMAN_COVER


def kirim_notifikasi(pesan):
    try:
        requests.post(f"https://ntfy.sh/{TOPIK_NTFY}", data=pesan.encode("utf-8"), timeout=5)
    except Exception:
        pass  # kalau gagal kirim, web tetap berjalan normal


def pindah(tujuan, label=""):
    st.session_state.halaman = tujuan
    kirim_notifikasi(f"Dia menekan: {label} (halaman berikutnya: {tujuan})")


kunci = st.session_state.halaman
halaman = PAGES[kunci]

# Slot musik dibuat paling awal agar posisinya tetap dan musik tidak
# mulai dari awal setiap pindah halaman. Musik baru mulai setelah cover
# dibuka, karena browser hanya mengizinkan suara setelah ada ketukan.
slot_musik = st.container()
with slot_musik:
    if kunci != HALAMAN_COVER:
        file_musik = cari_musik()
        if file_musik:
            st.audio(file_musik, loop=True, autoplay=True)
        elif TAMPILKAN_PERINGATAN:
            st.warning("File musik tidak ditemukan. Taruh lagu di folder: " + os.path.join(BASE_DIR, "musik"))

st.markdown(CSS + hati_melayang(), unsafe_allow_html=True)

if halaman.get("gambar") and TAMPILKAN_PERINGATAN and not gambar_html(halaman["gambar"]):
    st.warning(
        "Foto untuk halaman ini tidak ditemukan atau tidak bisa dibuka. "
        "Taruh file bernama '"
        + os.path.splitext(os.path.basename(halaman["gambar"]))[0]
        + "' (.jpg/.jpeg/.png/.webp) di folder: "
        + os.path.join(BASE_DIR, "foto")
    )

isi = (
    '<div class="isi">'
    + gambar_html(halaman.get("gambar"))
    + f'<div class="judul">{halaman["judul"].format(nama=NAMA)}</div>'
    + f'<div class="teks">{halaman["teks"].format(nama=NAMA)}</div>'
    + "</div>"
)
st.markdown(isi, unsafe_allow_html=True)

if halaman.get("balon") and st.session_state.get("balon_untuk") != kunci:
    st.balloons()
    st.session_state.balon_untuk = kunci

if "tombol" in halaman:
    label, tujuan = halaman["tombol"]
    st.button(label, key=f"{kunci}_tombol", type="primary", on_click=pindah, args=(tujuan, label))
elif "kiri" in halaman and "kanan" in halaman:
    kolom_kiri, kolom_kanan = st.columns(2)
    with kolom_kiri:
        label, tujuan = halaman["kiri"]
        st.button(label, key=f"{kunci}_kiri", type="primary", on_click=pindah, args=(tujuan, label))
    with kolom_kanan:
        label, tujuan = halaman["kanan"]
        st.button(label, key=f"{kunci}_kanan", type="secondary", on_click=pindah, args=(tujuan, label))
else:
    st.button("Ulangi dari awal", key=f"{kunci}_ulang", type="secondary", on_click=pindah, args=(HALAMAN_ULANG, "Ulangi dari awal"))
