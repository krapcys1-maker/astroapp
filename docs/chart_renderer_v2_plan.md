# Chart Renderer V2 Plan

## Cel

Zbudowac stabilny, deterministyczny renderer kolowego wykresu astrologicznego, ktory wizualnie da klasyczny, gesty i czytelny uklad w stylu referencyjnych chartow.

Kluczowe zalozenie:
- nie ruszamy obliczen astrologicznych,
- przebudowujemy tylko geometrie, layout i warstwy renderingu.

Docelowy efekt:
- zodiac ring, house ring, planet ring i aspect wheel dzialaja jako osobne, spojne warstwy,
- osie ASC/DSC/MC/IC sa idealnie naprzeciw siebie,
- planety nie nachodza na siebie ani na linie,
- ticki nie wchodza na znaki,
- caly wheel jest wizualnie gesty, ale czytelny.

## Zakres

W scope:
- `app/ui/widgets/natal_chart_widget.py`
- ewentualne male helpery geometryczne w `app/utils/`
- debug overlay dla renderera

Poza scope:
- zmiana astrologicznych obliczen pozycji
- zmiana modeli danych chartu
- zmiana logiki Swiss Ephemeris
- eksperymenty z zewnetrznymi rendererami

## Zasady architektoniczne

### 1. Twarde rozdzielenie

Rozdzielamy:
- silnik obliczen astrologicznych
- silnik renderingu

Renderer ma dostac gotowe dane:
- longitude planet,
- cusp angles,
- ASC/DSC/MC/IC,
- aspekty.

Renderer nie interpretuje astrologii, tylko rysuje.

### 2. Jeden wspolny transform kata

Wszystko ma korzystac z jednej funkcji transformacji:
- wejscie: dlugosc ekliptyczna w stopniach
- wyjscie: kat ekranowy w radianach

Ta sama funkcja obsluguje:
- znaki zodiaku
- cuspy domow
- planety
- osie
- anchor points aspektow

Zakaz lokalnych wyjatkow typu:
- plus 90
- minus 180
- specjalny obrut tylko dla jednej warstwy

### 3. Renderer oparty o pasy radialne

Wheel nie jest jednym kolem. Wheel to zestaw wspolsrodkowych pasow.

Minimalny radial spec:
- `outer_border_band`
- `degree_tick_band`
- `zodiac_label_band`
- `planet_band`
- `house_grid_band`
- `aspect_circle_band`
- `center_clear_zone`

Kazda warstwa ma:
- `inner_radius`
- `outer_radius`
- jasny cel
- zakaz wchodzenia na inne warstwy

### 4. Golden images jako twardy baseline

Po kazdej fazie zapisujemy referencyjny render PNG i traktujemy go jako baseline dla nastepnej fazy.

Cel:
- nie naprawic jednego miejsca kosztem dwoch innych
- miec punkt porownania po kazdej iteracji

Zasada:
- po kazdym kroku zapisujemy lokalny PNG referencyjny
- nastepny render porownujemy wizualnie do poprzedniego baseline
- jesli nowa zmiana rozwala stare poprawki, krok nie jest zaakceptowany

Minimalny zestaw baseline:
- jeden chart referencyjny z ciasnym klastrem przy ASC
- jeden chart z innym rozkladem planet

### 5. Twarde testy geometrii

Poza zwyklym `pytest` dokladamy asercje geometrii renderera.

Minimalne warunki:
- ASC i DSC roznia sie o 180 stopni
- MC i IC roznia sie o 180 stopni
- tick end radius nigdy nie wchodzi w `zodiac_label_band`
- planeta po collision nadal siedzi w `planet_band`

Cel:
- wylapac bledy geometrii zanim beda widoczne dopiero na screenie
- nie polegac tylko na ocenie wizualnej

## Docelowa geometria renderera

### Outer wheel

Warstwy od zewnatrz do srodka:
1. outer border
2. tick band
3. zodiac glyph band
4. inner border outer wheel
5. planet band
6. house outer ring
7. house inner ring
8. aspect circle
9. center clear zone

### Radial constants

Docelowo wszystkie promienie maja wyjsc z jednej tabeli lub jednej struktury, np.:
- `R_outer`
- `R_tick_outer`
- `R_tick_inner_1`
- `R_tick_inner_5`
- `R_tick_inner_10`
- `R_zodiac_label`
- `R_outer_wheel_inner_border`
- `R_planet_base`
- `R_house_outer`
- `R_house_inner`
- `R_aspect`
- `R_center_clear`

Zakaz:
- przypadkowych magic numbers rozrzuconych po metodach
- lokalnych `-7`, `+12`, `-19` bez wspolnego modelu

## Plan wdrozenia

### Faza A - Geometria bazowa

#### Krok A1. Jeden transform kata

Do zrobienia:
- wydzielic jedna funkcje transformacji dlugosci na kat ekranowy
- podmienic wszystkie warstwy, zeby korzystaly z niej

Akceptacja:
- ASC i DSC sa idealnie naprzeciw
- MC i IC sa idealnie naprzeciw
- planety, znaki i cuspy leza na tym samym systemie osi

#### Krok A2. Radial band spec

Do zrobienia:
- wprowadzic jedna strukture opisujaca wszystkie promienie
- outer wheel i inner wheel maja byc skladane tylko z tych promieni

Akceptacja:
- ticki, znaki, planety i domy maja osobne pasy
- zadna warstwa nie przecina drugiej

#### Krok A3. Debug overlay

Do zrobienia:
- dodac debug mode renderera
- pokazac:
  - ring boundaries
  - anchor points
  - sector wedges
  - bboxy labeli
  - grupy kolizji

Akceptacja:
- mozna jednym rzutem oka zobaczyc, gdzie cos siedzi na zlym promieniu
- baseline PNG po tym kroku jest zapisany i zachowany do porownania

### Faza B - Outer wheel

#### Krok B1. Zodiac ring

Do zrobienia:
- 12 sektorow po 30 stopni
- wyrazne granice znakow
- znaki w srodku swojego sektora
- bez wchodzenia tickow w pas znakow

Akceptacja:
- wszystkie 12 znakow jest rowno rozlozone
- ticki nie nachodza na znaki
- render po zmianie przechodzi porownanie do poprzedniego baseline bez regresji w innych warstwach

#### Krok B2. Degree tick band

Do zrobienia:
- tick co 1 stopien
- dluzszy tick co 5 stopni
- najdluzszy co 10 stopni
- wszystkie ticki tylko w tick band

Akceptacja:
- tick hierarchy jest czytelna
- ticki sa radialne i rowno rozstawione
- tick end radius nigdy nie przecina `zodiac_label_band`

### Faza C - House wheel

#### Krok C1. House grid band

Do zrobienia:
- dwa ringi domow
- linie cuspow zgodnie z realnymi katami, nie rowno co 30 stopni
- numery domow na osobnym house-number ring

Akceptacja:
- domy sa rozlozone zgodnie z obliczonymi cuspami
- numery domow sa czytelne i centralne w sektorach

#### Krok C2. Osie kardynalne

Do zrobienia:
- ASC, DSC, MC, IC jako osobna warstwa
- grubsze, bardziej kontrastowe
- podpisy i degree labels bez przecinania przez linie

Akceptacja:
- osie sa najczytelniejsze po outer border
- label nie siedzi na linii

### Faza D - Planet ring

#### Krok D1. Planet anchor model

Do zrobienia:
- kazda planeta ma:
  - angle
  - base radius
  - glyph
  - bez labelu pozycji w pierwszej wersji
  - retro marker dopiero po ustabilizowaniu ukladu

Akceptacja:
- planety sa rysowane tylko na dedykowanym pasie planet
- nie siedza ani na tickach, ani na ringach domow
- pierwsza wersja planet to czysty glyph layout bez tekstow

#### Krok D2. Collision engine

Do zrobienia:
- grupowac planety po bliskosci katowej
- klaster rozkladac radialnie
- zachowac kolejnosc po longitude
- nie dopuszczac do nachodzenia planet, labeli i osi

Strategia:
- cluster detection po odleglosci katowej
- radial stack jako glowny mechanizm
- tangential fallback tylko awaryjnie i minimalnie

Akceptacja:
- bliskie planety nie nachodza na siebie
- nie wychodza poza planet band
- nie uciekaja miedzy sektorami

#### Krok D3. Planet labels

Do zrobienia:
- po ustabilizowaniu glyphow przywrocic czytelne etykiety pozycji
- degree/minute/sign/retro tylko jesli nie rozwala layoutu
- najpierw stabilnosc, potem bogatsza informacja

Akceptacja:
- kazdy block planety jest jedna jednostka wizualna
- zadna etykieta nie siedzi na house line ani na zodiac ring
- labels wracaja dopiero po przejsciu testow geometrii dla samego glyph layoutu

### Faza E - Aspect wheel

#### Krok E1. Inner aspect anchors

Do zrobienia:
- jeden wspolny promien kotwiczenia linii aspektow
- anchor liczony z tego samego transformu co planety

Akceptacja:
- linie trafiaja dokladnie w punkty kotwiczenia
- nic nie wyglada jak losowa kreska

#### Krok E2. Aspect styling

Do zrobienia:
- czerwone: hard aspects
- niebieskie: soft aspects
- opcjonalnie przerywane dla slabszych
- clipping do inner aspect area

Akceptacja:
- aspekty sa czytelne, ale nie dominuja calego wykresu

### Faza F - Readability i polish

#### Krok F1. Hierarchia wizualna

Poziomy waznosci:
1. outer border i osie kardynalne
2. granice znakow i glowne linie
3. planety
4. domy
5. ticki
6. aspekty jako najlzejsza warstwa

Akceptacja:
- wykres nie jest szara papka
- wzrok naturalnie czyta zewnetrze, planety, potem srodek

#### Krok F2. Typography

Do zrobienia:
- osobne rozmiary dla:
  - zodiac glyphs
  - planet glyphs
  - house numbers
  - osi
  - degree labels
- centrowanie tekstu
- optyczne korekty glyphow

Akceptacja:
- nic nie jest przypadkowo zbyt male albo zbyt wielkie

#### Krok F3. Opcjonalny polish

Mozliwe dodatki po ustabilizowaniu geometrii:
- delikatne cieniowanie sektorow zodiaku
- halo pod znakami albo etykietami
- lepsza hierarchia grubosci linii

## Definicja "done"

Renderer v2 uznajemy za skonczony dopiero gdy:
- znaki siedza idealnie w swoich sektorach
- ticki nie wchodza w znaki
- planety nie nachodza na siebie
- planety nie dotykaja zodiac ring ani house lines
- domy sa poprawnie rozlozone po realnych cuspach
- ASC i DSC sa idealnie naprzeciw
- MC i IC sa idealnie naprzeciw
- aspect lines trafiaja w poprawne anchor points
- caly wheel wyglada gesty, symetryczny i czytelny

## Kryteria akceptacji per iteracja

W kazdym kroku sprawdzamy:
- render lokalny PNG
- porownanie z baseline PNG z poprzedniej fazy
- `ruff check .`
- `pytest`
- twarde asercje geometrii renderera

Manualnie sprawdzamy:
- cluster przy ASC
- dol przy IC
- prawa strone przy Jupiter/Moon
- top przy MC i wezly
- czy znak/ticki/planeta nie wchodza na siebie

Automatycznie sprawdzamy:
- osie kardynalne sa naprzeciw
- ticki nie wchodza w pas znakow
- planety po collision sa nadal w `planet_band`

## Kolejnosc realizacji

Kolejnosc wykonawcza bez skakania:
1. wspolny transform kata
2. radial band spec
3. debug overlay
4. zodiac ring
5. tick band
6. house wheel
7. osie kardynalne
8. planet ring bez tekstow
9. collision engine planet
10. labels planet
11. aspect wheel
12. readability polish

## Decyzje projektowe

- Nie wracamy do przypadkowych lokalnych offsetow jako glownej strategii.
- Nie mieszamy juz napraw wizualnych z obliczeniami astrologicznymi.
- Nie opieramy sie na zewnetrznym rendererze.
- Budujemy renderer v2 warstwa po warstwie.

## Plik referencyjny

Punktem odniesienia dla efektu koncowego jest klasyczny, gesty wheel chart o strukturze:
- mocny zodiac ring,
- czytelne ticki,
- planety na dedykowanym bandzie,
- osobny ring domow,
- wyrazne osie kardynalne,
- uporzadkowany srodek aspektow.
