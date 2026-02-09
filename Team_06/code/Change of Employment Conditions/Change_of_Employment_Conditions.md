# Dokumentacja Projektu: Change of Employment Conditions

## Polecenie

Stworzenie aplikacji z interfejsem użytkownika na podstawie plików w folderze (dokumentacja .docx i diagram .bpmn). Aplikacja ma realizować proces zmiany warunków zatrudnienia.

## Działania

1.  **Analiza plików**:
    *   Przeanalizowano plik `Change of Employment Conditions.bpmn` w celu zrozumienia przepływu procesu.
    *   Użyto skryptu Python do ekstrakcji tekstu z plików `.docx` (`Change of Employment Conditions Data.docx`, `Change of Employment Conditions Test Scenario.docx`), aby poznać szczegółowe wymagania danych i scenariusze testowe.

2.  **Przygotowanie środowiska**:
    *   Utworzono wirtualne środowisko Python (`venv`).
    *   Zainstalowano wymagane biblioteki: `streamlit`, `pandas`.

3.  **Implementacja**:
    *   **Baza danych (`database.py`)**: Utworzono moduł obsługi bazy danych SQLite do przechowywania wniosków i ich stanów.
    *   **Logika Procesu (`process.py`)**: Zaimplementowano silnik procesu odwzorowujący diagram BPMN. Obsługuje on przepływ zadań pomiędzy rolami (Head of O.U., PD, KWE, PRK, PRN, Rector, Chancellor).
    *   **Interfejs Użytkownika (`main.py`)**: Stworzono aplikację w Streamlit.
        *   Symulacja logowania dla różnych ról.
        *   Formularz składania nowego wniosku z **opcją wyboru gotowych presetów danych** (np. dla nauczyciela akademickiego).
        *   Listy zadań dla poszczególnych ról z formularzami decyzyjnymi.
        *   Podgląd historii wszystkich wniosków.

4.  **Weryfikacja**:
    *   Uruchomiono aplikację i zweryfikowano poprawność działania interfejsu oraz przepływu procesu.
    *   Naprawiono błąd `UnboundLocalError` w `main.py` związany z importem modułu bazy danych.

## Użyte Narzędzia

*   **Python**: Język programowania.
*   **Streamlit**: Framework do budowy interfejsu użytkownika.
*   **SQLite**: Baza danych.
*   **Pandas**: Obsługa danych tabelarycznych.
*   **Skrypty pomocnicze**: `extract_docx_v2.py` do analizy dokumentacji.

## Zmodyfikowane/Utworzone Pliki

*   `extract_docx_v2.py` (narzędzie pomocnicze)
*   `database.py`
*   `process.py`
*   `main.py`
*   `Change_of_Employment_Conditions.md` (ten plik)

## Data i Czas

*   Rozpoczęcie prac: 2025-12-03 11:05
*   Zakończenie prac: 2025-12-03 11:25
