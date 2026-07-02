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
# KONFIGURACJA I POBIERANIE CZCIONEK
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

def generuj_cien(obrazek, rozrost=50, rozmycie=35, offset_y=15):
    """Generuje realistyczny, miękki cień pod okładką."""
    szerokosc = obrazek.width + rozrost * 2
    wysokosc = obrazek.height + rozrost * 2
    cien = Image.new('RGBA', (szerokosc, wysokosc), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(cien)
    draw.rectangle(
        [rozrost + 10, rozrost + offset_y, rozrost + obrazek.width - 10, rozrost + obrazek.height + offset_y],
        fill=(0, 0, 0, 60)
    )
    cien = cien.filter(ImageFilter.GaussianBlur(rozmycie))
    cien.paste(obrazek, (rozrost, rozrost))
    return cien

# ==========================================
# GŁÓWNY SILNIK GENERUJĄCY COVER
# ==========================================
def generuj_cover_fb(okladka_plik, miesiac_rok, styl_tla, kolor_tla="#EACDC7"):
    SZEROKOSC, WYSOKOSC = 1640, 624 
    
    # 1. PRZYGOTOWANIE TŁA
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
        biala_nakladka = Image.new('RGBA', (SZEROKOSC, WYSOKOSC), (255, 255, 255, 180))
        tlo = Image.alpha_composite(tlo_rozmyte.convert('RGBA'), biala_nakladka).convert('RGB')

    # 2. PRZYGOTOWANIE OKŁADKI
    docelowa_wys_okladki = 540
    proporcja = docelowa_wys_okladki / okladka_img.height
    docelowa_szer_okladki = int(okladka_img.width * proporcja)
    okladka_zeskalowana = okladka_img.resize((docelowa_szer_okladki, docelowa_wys_okladki), Image.Resampling.LANCZOS)
    
    okladka_z_cieniem = generuj_cien(okladka_zeskalowana)
    
    margines_prawa = 110 
    okladka_x = SZEROKOSC - docelowa_szer_okladki - margines_prawa
    wklej_x = okladka_x - 50 
    wklej_y = ((WYSOKOSC - docelowa_wys_okladki) // 2) - 50
    
    # 3. WGRYWANIE LOGO
    linia_podzialu_x = okladka_x - 60 
    y_logo_dol = 250 
    
    if os.path.exists("logo_cnw.png"):
        logo = Image.open("logo_cnw.png").convert("RGBA")
        logo_szer = 500 
        logo_prop = logo_szer / logo.width
        logo_wys = int(logo.height * logo_prop)
        logo = logo.resize((logo_szer, logo_wys), Image.Resampling.LANCZOS)
        
        logo_x = linia_podzialu_x - logo_szer
        logo_y = y_logo_dol - logo_wys
        tlo.paste(logo, (logo_x, logo_y), logo)

    # 4. RYSOWANIE TEKSTÓW Z OBSŁUGĄ EMOJI
    try:
        font_light = ImageFont.truetype("Montserrat-Light.ttf", 40)
        font_bold = ImageFont.truetype("Montserrat-Bold.ttf", 52)
    except Exception:
        font_light = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    kolor_tekstu = (35, 35, 35) 
    tekst_1 = "Najnowsze wydanie już dostępne"
    tekst_2 = miesiac_rok.upper()
    
    szer_t1 = font_light.getlength(tekst_1) if hasattr(font_light, 'getlength') else font_light.getbbox(tekst_1)[2]
    szer_t2 = font_bold.getlength(tekst_2) if hasattr(font_bold, 'getlength') else font_bold.getbbox(tekst_2)[2]
    
    y_tekst = y_logo_dol + 30
    
    with Pilmoji(tlo) as pilmoji:
        pilmoji.text((linia_podzialu_x - szer_t1, y_tekst), tekst_1, fill=kolor_tekstu, font=font_light)
        y_tekst += 60
        pilmoji.text((linia_podzialu_x - szer_t2, y_tekst), tekst_2, fill=kolor_tekstu, font=font_bold)

    # Naklejamy okładkę z cieniem
    tlo.paste(okladka_z_cieniem, (wklej_x, wklej_y), okladka_z_cieniem)

    return tlo

# ==========================================
# INTERFEJS UŻYTKOWNIKA STREAMLIT
# ==========================================
st.set_page_config(page_title="Generator Covera FB", page_icon="🖼️", layout="centered")
pobierz_czcionki()

st.title("🖼️ Profesjonalny Generator Coverów FB")
st.write("Wgraj okładkę, wpisz miesiąc i odbierz automatycznie oba warianty tła strony!")

if 'covers_generated' not in st.session_state:
    st.session_state.covers_generated = False

with st.container():
    plik_okladki = st.file_uploader("Wgraj plik nowej okładki (PNG/JPG):", type=['png', 'jpg', 'jpeg'])
    miesiac_input = st.text_input("Wpisz miesiąc i rok wydania:", value="MAJ 2026 🔥")
    kolor_wybrany = st.color_picker("Wybierz odcień dla wersji jednolitej (domyślnie pastelowy róż):", "#F1DEDC")

    if st.button("🚀 Wygeneruj Oba Warianty", type="primary"):
        if plik_okladki and miesiac_input:
            with st.spinner("Składam grafiki, renderuję cienie i napisy..."):
                
                # Generujemy obie wersje na raz i trzymamy w pamięci podręcznej
                img_jednolity = generuj_cover_fb(plik_okladki, miesiac_input, "Jednolity", kolor_wybrany)
                img_rozmyty = generuj_cover_fb(plik_okladki, miesiac_input, "Rozmyty")
                
                # Konwersja na bajty do pobrania
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

# WYŚWIETLANIE W ZAKŁADKACH (TABS)
if st.session_state.covers_generated:
    st.markdown("---")
    st.subheader("📥 Wybierz i pobierz wersję dla siebie:")
    
    tab1, tab2 = st.tabs(["💗 Wersja z jednolitym tłem", "✨ Wersja z rozmytym tłem"])
    
    with tab1:
        st.image(st.session_state.bytes_jednolity, use_container_width=True)
        st.download_button(
            label="📥 Pobierz Wersję Jednolitą",
            data=st.session_state.bytes_jednolity,
            file_name=f"cover_jednolity_{st.session_state.nazwa_pliku_baza}.jpg",
            mime="image/jpeg",
            width="stretch"
        )
        
    with tab2:
        st.image(st.session_state.bytes_rozmyty, use_container_width=True)
        st.download_button(
            label="📥 Pobierz Wersję Rozmytą",
            data=st.session_state.bytes_rozmyty,
            file_name=f"cover_rozmyty_{st.session_state.nazwa_pliku_baza}.jpg",
            mime="image/jpeg",
            width="stretch"
        )
