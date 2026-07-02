import os
import urllib.request
import ssl
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Odblokowanie pobierania czcionek na systemach macOS
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
                print(f"Pobieram brakującą czcionkę: {nazwa}...")
                urllib.request.urlretrieve(url, nazwa)
            except Exception as e:
                print(f"Błąd pobierania {nazwa}: {e}")

def generuj_cien(obrazek, rozrost=50, rozmycie=35, offset_y=15):
    """Generuje realistyczny, bardzo miękki cień pod okładką."""
    szerokosc = obrazek.width + rozrost * 2
    wysokosc = obrazek.height + rozrost * 2
    cien = Image.new('RGBA', (szerokosc, wysokosc), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(cien)
    # Rysujemy delikatnie półprzezroczysty, mniejszy prostokąt, żeby cień nie był za mocny
    draw.rectangle(
        [rozrost + 10, rozrost + offset_y, rozrost + obrazek.width - 10, rozrost + obrazek.height + offset_y],
        fill=(0, 0, 0, 60)
    )
    cien = cien.filter(ImageFilter.GaussianBlur(rozmycie))
    cien.paste(obrazek, (rozrost, rozrost))
    return cien

# ==========================================
# GŁÓWNY GENERATOR
# ==========================================
def generuj_cover_fb(okladka_plik, miesiac_rok, styl_tla, kolor_tla="#EACDC7"):
    SZEROKOSC, WYSOKOSC = 1640, 624 
    
    # 1. PRZYGOTOWANIE TŁA
    okladka_img = Image.open(okladka_plik).convert("RGBA")
    
    if styl_tla == "Jednolity":
        tlo = Image.new('RGB', (SZEROKOSC, WYSOKOSC), kolor_tla)
    else:
        # Bardziej rozmyte i jaśniejsze tło (jak na Twoim wzorze)
        wspolczynnik = SZEROKOSC / okladka_img.width
        nowa_wys = int(okladka_img.height * wspolczynnik)
        tlo_rozmyte = okladka_img.resize((SZEROKOSC, nowa_wys), Image.Resampling.LANCZOS)
        
        offset_y = (nowa_wys - WYSOKOSC) // 2
        tlo_rozmyte = tlo_rozmyte.crop((0, offset_y, SZEROKOSC, offset_y + WYSOKOSC))
        
        tlo_rozmyte = tlo_rozmyte.filter(ImageFilter.GaussianBlur(60))
        biala_nakladka = Image.new('RGBA', (SZEROKOSC, WYSOKOSC), (255, 255, 255, 180))
        tlo = Image.alpha_composite(tlo_rozmyte.convert('RGBA'), biala_nakladka).convert('RGB')

    # 2. PRZYGOTOWANIE OKŁADKI (Większa okładka, bliższa krawędzi)
    docelowa_wys_okladki = 540
    proporcja = docelowa_wys_okladki / okladka_img.height
    docelowa_szer_okladki = int(okladka_img.width * proporcja)
    okladka_zeskalowana = okladka_img.resize((docelowa_szer_okladki, docelowa_wys_okladki), Image.Resampling.LANCZOS)
    
    okladka_z_cieniem = generuj_cien(okladka_zeskalowana)
    
    margines_prawa = 110 # Odległość okładki od prawej krawędzi covera
    okladka_x = SZEROKOSC - docelowa_szer_okladki - margines_prawa
    wklej_x = okladka_x - 50 # korekta o rozrost cienia
    wklej_y = ((WYSOKOSC - docelowa_wys_okladki) // 2) - 50
    
    # 3. WGRYWANIE LOGO (I WYRÓWNANIE)
    draw = ImageDraw.Draw(tlo)
    linia_podzialu_x = okladka_x - 60 # Oś, do której wyrównujemy prawą stronę tekstu i logo
    
    y_logo_dol = 250 
    
    if os.path.exists("logo_cnw.png"):
        logo = Image.open("logo_cnw.png").convert("RGBA")
        logo_szer = 500 # Powiększone logo
        logo_prop = logo_szer / logo.width
        logo_wys = int(logo.height * logo_prop)
        logo = logo.resize((logo_szer, logo_wys), Image.Resampling.LANCZOS)
        
        logo_x = linia_podzialu_x - logo_szer
        logo_y = y_logo_dol - logo_wys
        tlo.paste(logo, (logo_x, logo_y), logo)

    # 4. RYSOWANIE TEKSTÓW (Prawidłowe czcionki i rozmiary)
    try:
        font_light = ImageFont.truetype("Montserrat-Light.ttf", 40)
        font_bold = ImageFont.truetype("Montserrat-Bold.ttf", 52)
    except Exception as e:
        print("Używam czcionki awaryjnej. Błąd:", e)
        font_light = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    kolor_tekstu = (35, 35, 35) # Ciemny grafit
    tekst_1 = "Najnowsze wydanie już dostępne"
    tekst_2 = miesiac_rok.upper()
    
    szer_t1 = font_light.getlength(tekst_1) if hasattr(font_light, 'getlength') else font_light.getbbox(tekst_1)[2]
    szer_t2 = font_bold.getlength(tekst_2) if hasattr(font_bold, 'getlength') else font_bold.getbbox(tekst_2)[2]
    
    y_tekst = y_logo_dol + 30
    draw.text((linia_podzialu_x - szer_t1, y_tekst), tekst_1, fill=kolor_tekstu, font=font_light)
    y_tekst += 60
    draw.text((linia_podzialu_x - szer_t2, y_tekst), tekst_2, fill=kolor_tekstu, font=font_bold)

    # Naklejamy okładkę na końcu
    tlo.paste(okladka_z_cieniem, (wklej_x, wklej_y), okladka_z_cieniem)

    return tlo

# ==========================================
# BLOK STARTOWY (Uruchamia się po wciśnięciu RUN)
# ==========================================
if __name__ == "__main__":
    pobierz_czcionki()
    
    # PARAMETRY DO TESTÓW:
    nazwa_pliku_okladki = "okladka.jpg" 
    jaki_miesiac = "MAJ 2026"
    kolor_rozowy = "#F1DEDC" # Dopasowany do Twojego wzoru
    
    print("Rozpoczynam generowanie grafik...")
    
    if os.path.exists(nazwa_pliku_okladki):
        # Generujemy od razu OBA warianty
        wersja_jednolita = generuj_cover_fb(nazwa_pliku_okladki, jaki_miesiac, "Jednolity", kolor_rozowy)
        wersja_rozmyta = generuj_cover_fb(nazwa_pliku_okladki, jaki_miesiac, "Rozmyty")
        
        # Zapisujemy pliki
        nazwa_1 = "COVER_1_JEDNOLITY.jpg"
        nazwa_2 = "COVER_2_ROZMYTY.jpg"
        
        wersja_jednolita.save(nazwa_1, quality=100)
        wersja_rozmyta.save(nazwa_2, quality=100)
        
        # Otwieramy podgląd obu plików
        wersja_jednolita.show()
        wersja_rozmyta.show()
        
        print(f"✅ Sukces! Wygenerowano i otwarto dwie wersje covera.")
    else:
        print(f"❌ BŁĄD: Nie znalazłem pliku '{nazwa_pliku_okladki}'. Upewnij się, że jest w tym samym folderze.")
