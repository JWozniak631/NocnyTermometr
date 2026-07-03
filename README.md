# Nocny Termometr Polski 🌙

Autorska aplikacja analityczna w Streamlit sprawdzająca, czy w polskich miastach problemem jest wyłącznie upalne popołudnie, czy także noc bez ochłodzenia. Aplikacja pobiera rzeczywiste dane historyczne z Open-Meteo Historical Weather API i buduje dashboard z filtrami, KPI, mapą oraz kilkoma typami wykresów.

## Temat projektu

**Pytanie badawcze:** Czy w wybranych polskich miastach większy problem stanowią dni upalne, czy noce tropikalne?

Aplikacja porównuje 12 miast: Warszawa, Kraków, Łódź, Wrocław, Poznań, Gdańsk, Szczecin, Lublin, Białystok, Rzeszów, Katowice i Toruń. Zakres danych w kodzie to lata 2019–2024, a użytkownik może dodatkowo zawężać daty w panelu bocznym.

## Źródło danych

- Open-Meteo Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
- Endpoint używany w aplikacji: `https://archive-api.open-meteo.com/v1/archive`
- Dane są pobierane przez REST API, bez klucza API.

Wykorzystywane zmienne dzienne:

- `temperature_2m_max`
- `temperature_2m_mean`
- `temperature_2m_min`
- `apparent_temperature_max`
- `apparent_temperature_min`
- `precipitation_sum`
- `precipitation_hours`
- `sunshine_duration`
- `wind_speed_10m_max`
- `weather_code`

## Co robi aplikacja

1. Pobiera dzienne dane pogodowe dla współrzędnych miast.
2. Czyści dane:
   - konwertuje typy,
   - usuwa duplikaty `miasto–data`,
   - sprawdza braki,
   - interpoluje krótkie luki w obrębie miasta,
   - tworzy raport braków przed i po czyszczeniu.
3. Dodaje kolumny pochodne:
   - rok, miesiąc, pora roku,
   - dzień upalny: `tmax >= 30°C`,
   - noc tropikalna: `tmin >= 20°C`,
   - dzień suchy: `opad < 1 mm`,
   - dzień z intensywnym opadem: `opad >= 10 mm`,
   - amplituda dobowa,
   - anomalia temperatury względem średniego miesiąca dla miasta,
   - autorski indeks `urban_heat_stress`.
4. Prezentuje dashboard z KPI, tabelami i wykresami.

## Typy wykresów

Projekt spełnia wymaganie minimum 5 typów wykresów. Zawiera m.in.:

- wykres liniowy,
- wykres słupkowy,
- heatmapę,
- scatter plot,
- boxplot,
- area chart,
- mapę punktową,
- treemapę.

## Widgety i filtry

Aplikacja zawiera więcej niż 3 widgety:

- `multiselect` — wybór miast,
- `date_input` — zakres dat,
- `selectbox` — główna metryka,
- `slider` — minimalny próg temperatury maksymalnej,
- `multiselect` — pory roku,
- `checkbox` — pokazanie tabeli roboczej.

## Struktura plików

```text
.
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
└── .gitignore
```

## Uruchomienie lokalne

W terminalu w folderze projektu:

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Instalacja bibliotek:

```bash
pip install -r requirements.txt
```

Start aplikacji:

```bash
streamlit run app.py
```

## Deployment na Streamlit Community Cloud

1. Utwórz publiczne repozytorium na GitHubie, np. `nocny-termometr-polski`.
2. Wgraj do repozytorium pliki z tego folderu:
   - `app.py`,
   - `requirements.txt`,
   - `README.md`,
   - `.streamlit/config.toml`,
   - `.gitignore`.
3. Wejdź na https://share.streamlit.io/ i zaloguj się przez GitHub.
4. Kliknij **Create app** / **New app**.
5. Wybierz repozytorium, branch `main` i plik startowy `app.py`.
6. Kliknij **Deploy**.
7. Po wdrożeniu skopiuj publiczny link `https://...streamlit.app` i wklej go w Moodle.

## Co wpisać w README po wdrożeniu

Po wdrożeniu możesz dopisać na górze README:

```md
Działająca aplikacja: https://twoj-link.streamlit.app
Repozytorium GitHub: https://github.com/twoj-login/nocny-termometr-polski
```

## Ograniczenia

- Dane Open-Meteo są reanalizą dla współrzędnych, nie pomiarem z konkretnej ulicy.
- Porównanie miast pokazuje przybliżony obraz klimatu miejskiego, a nie oficjalny ranking meteorologiczny.
- Aplikacja wymaga internetu, bo pobiera dane z API.

## Autor

Wpisz swoje imię i nazwisko przed oddaniem projektu.
