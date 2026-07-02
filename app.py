import os
import urllib.request
import ssl
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import streamlit as st
from pilmoji import Pilmoji 

# Odblokowanie pobierania czcionek w środowisku sieciowym
ssl._create_default_https_context = ssl._create_unverified_context

# ==========================================
# KONFIGURACJA I INTELIGENTNE FUNKCJE
# ==========================================
def pobierz_czcionki():
    czcionki = {
        "Montserrat-Light.ttf": "https://raw.githubusercontent.com/googlefonts/montserrat/master/fonts/ttf/Montserrat-Light.ttf",
        "Montserrat-Bold.ttf": "https://raw.githubusercontent.com/googlefonts/montserrat/master/fonts/ttf/Montserrat-Bold.ttf"
    }
    for nazwa, url in czcionki.items():
        if not os.path.exists(nazwa):
            try:
                urllib.request.urlretrieve(url, nazwa)
            except Exception:
                pass

def wyciagnij_dominujacy_kolor(obrazek):
    """Pobiera najpopularniejszy kolor i automatycznie go rozjaśnia, by tekst był czytelny."""
    img = obrazek.convert("P", palette=Image.ADAPTIVE, colors=10)
    img = img.convert("RGB")
    
    colors = img.getcolors(100000)
    najczestszy = max(colors, key=lambda item: item[0])[1]
    
    r, g, b = najczestszy
    
    # Obliczamy postrzeganą jasność koloru
    jasnosc = (r * 299 + g * 587 + b * 114) / 1000
    
    # Jeśli kolor jest za ciemny, mieszamy go z bielą (robimy pastelowy odcień)
    if jasnosc < 180:
        r = min(255, int(r + (255 - r) * 0.65))
        g = min(255, int(g + (255 - g) * 0.65))
        b = min(255, int(b + (255 - b) * 0.65))
        
    return '#{:02x}{:02x}{:02x}'.format(r, g, b).upper()

def generuj_cien(obrazek, rozrost=40, rozmycie=25, offset_y=10):
    szerokosc = obrazek.width + rozrost * 2
    wysokosc = obrazek.height + rozrost * 2
    cien = Image.new('RGBA', (szerokosc, wysokosc), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(cien)
    draw.rectangle(
        [rozrost + 8, rozrost + offset_y, rozrost + obrazek.width - 8, rozrost + obrazek.height + offset_y],
        fill=(0, 0, 0, 50)
    )
    cien = cien.filter(ImageFilter.GaussianBlur(rozmycie))
    cien.paste(obrazek, (rozrost, rozrost))
    return cien

# ==========================================
# GŁÓWNY SILNIK GENERUJĄCY COVER
# ==========================================
def generuj_cover_fb(okladka_plik, miesiac_rok, styl_tla, kolor_tla="#EACDC7"):
    SZEROKOSC, WYSOKOSC = 1640, 624 
    
    okladka_img = Image.open(okladka_plik).convert("RGBA")
    
    if styl_tla == "Jednolity":
        tlo = Image.new('RGB', (SZEROKOSC, WYSOKOSC), kolor_tla)
    else:
        wspolczynnik = SZEROKOSC / okladka_img.width
        nowa_wys = int(okladka_img.height * wspolczynnik)
        tlo_rozmyte = okladka_img.resize((SZEROKOSC, nowa_wys), Image.Resampling.LANCZOS)
        
        offset_y = (nowa_wys - WYSOKOSC) // 2
        tlo_rozmyte = tlo_rozmyte.crop((0, offset_y, SZEROKOSC, offset_y + WYSOKOSC))
        
        tlo_rozmyte = tlo_rozmyte.filter(ImageFilter.GaussianBlur(60))
        biala_nakladka = Image.new('RGBA', (SZEROKOSC, WYSOKOSC), (255, 255, 255, 170))
        tlo = Image.alpha_composite(tlo_rozmyte.convert('RGBA'), biala_nakladka).convert('RGB')

    # Poprawione proporcje: odrobinę mniejsza okładka, żeby dać jej "oddech"
    docelowa_wys_okladki = 480
    proporcja = docelowa_wys_okladki / okladka_img.height
    docelowa_szer_okladki = int(okladka_img.width * proporcja)
    okladka_zeskalowana = okladka_img.resize((docelowa_szer_okladki, docelowa_wys_okladki), Image.Resampling.LANCZOS)
    
    okladka_z_cieniem = generuj_cien(okladka_zeskalowana)
    
    margines_prawa = 120 
    okladka_x = SZEROKOSC - docelowa_szer_okladki - margines_prawa
    wklej_x = okladka_x - 40 
    wklej_y = ((WYSOKOSC - docelowa_wys_okladki) // 2) - 40
    
    linia_podzialu_x = okladka_x - 70 
    
    # Poprawione logo: mniejsze, bardziej eleganckie
    if os.path.exists("logo_cnw.png"):
        logo = Image.open("logo_cnw.png").convert("RGBA")
        logo_szer = 400 
        logo_prop = logo_szer / logo.width
        logo_wys = int(logo.height * logo_prop)
        logo = logo.resize((logo_szer, logo_wys), Image.Resampling.LANCZOS)
        
        logo_x = linia_podzialu_x - logo_szer
        logo_y = 190
        tlo.paste(logo, (logo_x, logo_y), logo)
    else:
        logo_wys = 100
        logo_y = 190

    try:
        font_light = ImageFont.truetype("Montserrat-Light.ttf", 36)
        font_bold = ImageFont.truetype("Montserrat-Bold.ttf", 46)
    except Exception:
        font_light = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    kolor_tekstu = (35, 35, 35) 
    tekst_1 = "Najnowsze wydanie już dostępne"
    tekst_2 = miesiac_rok.upper()
    
    szer_t1 = font_light.getlength(tekst_1) if hasattr(font_light, 'getlength') else font_light.getbbox(tekst_1)[2]
    szer_t2 = font_bold.getlength(tekst_2) if hasattr(font_bold, 'getlength') else font_bold.getbbox(tekst_2)[2]
    
    y_tekst = logo_y + logo_wys + 25
    
    with Pilmoji(tlo) as pilmoji:
        pilmoji.text((linia_podzialu_x - szer_t1, y_tekst), tekst_1, fill=kolor_tekstu, font=font_light)
        y_tekst += 55
        pilmoji.text((linia_podzialu_x - szer_t2, y_tekst), tekst_2, fill=kolor_tekstu, font=font_bold)

    tlo.paste(okladka_z_cieniem, (wklej_x, wklej_y), okladka_z_cieniem)

    return tlo

# ==========================================
# INTERFEJS UŻYTKOWNIKA STREAMLIT
# ==========================================
st.set_page_config(page_title="Generator Covera FB", page_icon="🖼️", layout="centered")
pobierz_czcionki()

st.title("🖼️ Profesjonalny Generator Coverów FB")
st.write("Wgraj okładkę, wpisz miesiąc i sprawdź grafiki na jednej stronie!")

if 'covers_generated' not in st.session_state:
    st.session_state.covers_generated = False

with st.container():
    plik_okladki = st.file_uploader("Wgraj plik nowej okładki (PNG/JPG):", type=['png', 'jpg', 'jpeg'])
    
    domyslny_kolor = "#F1DEDC" 
    if plik_okladki:
        img_temp = Image.open(plik_okladki)
        domyslny_kolor = wyciagnij_dominujacy_kolor(img_temp)
        plik_okladki.seek(0) 

    miesiac_input = st.text_input("Wpisz miesiąc i rok wydania:", value="MAJ 2026 🔥")
    kolor_wybrany = st.color_picker("Odcień tła (zabezpieczony przed zbyt ciemnym kolorem):", domyslny_kolor)

    if st.button("🚀 Wygeneruj Oba Warianty", type="primary"):
        if plik_okladki and miesiac_input:
            with st.spinner("Składam grafiki, renderuję cienie i napisy..."):
                
                img_jednolity = generuj_cover_fb(plik_okladki, miesiac_input, "Jednolity", kolor_wybrany)
                img_rozmyty = generuj_cover_fb(plik_okladki, miesiac_input, "Rozmyty")
                
                buf1 = BytesIO()
                img_jednolity.save(buf1, format="JPEG", quality=100)
                st.session_state.bytes_jednolity = buf1.getvalue()
                
                buf2 = BytesIO()
                img_rozmyty.save(buf2, format="JPEG", quality=100)
                st.session_state.bytes_rozmyty = buf2.getvalue()
                
                st.session_state.nazwa_pliku_baza = miesiac_input.replace(" ", "_").strip()
                st.session_state.covers_generated = True
        else:
            st.warning("Upewnij się, że wgrałeś plik okładki oraz wpisałeś tekst!")

# WYŚWIETLANIE NA JEDNEJ PLANSZY (BEZ ZAKŁADEK)
if st.session_state.covers_generated:
    st.markdown("---")
    st.subheader("Oto Twoje grafiki (gotowe do pobrania):")
    
    st.markdown("### 🎨 Wersja z jednolitym tłem")
    st.image(st.session_state.bytes_jednolity, use_container_width=True)
    st.download_button(
        label="📥 Pobierz Wersję Jednolitą",
        data=st.session_state.bytes_jednolity,
        file_name=f"cover_jednolity_{st.session_state.nazwa_pliku_baza}.jpg",
        mime="image/jpeg",
        width="stretch",
        key="btn_jednolity"
    )
    
    st.markdown("---")
    
    st.markdown("### ✨ Wersja z rozmytym tłem")
    st.image(st.session_state.bytes_rozmyty, use_container_width=True)
    st.download_button(
        label="📥 Pobierz Wersję Rozmytą",
        data=st.session_state.bytes_rozmyty,
        file_name=f"cover_rozmyty_{st.session_state.nazwa_pliku_baza}.jpg",
        mime="image/jpeg",
        width="stretch",
        key="btn_rozmyty"
    )
