# Dokumentacja Projektu MPP (Minimal Process Platform)

## 1. Instrukcja Uruchomienia

Aplikacja została przygotowana do uruchomienia w środowisku Docker.

### Wymagania
- Zainstalowany Docker oraz Docker Compose.
- Wolne porty: 3000 (Frontend), 8000 (Backend), 5432 (Baza Danych - jeśli mapowana).

### Krok po kroku
1. Otwórz terminal w katalogu głównym projektu.
2. Uruchom polecenie:
   ```bash
   docker compose up --build
   ```
3. Poczekaj, aż serwisy wstaną. Powinieneś zobaczyć logi informujące o starcie `mpp_backend`, `mpp_db` oraz `mpp_frontend`.
   - **Ważne**: Przy pierwszym uruchomieniu backend automatycznie zainicjuje bazę danych i utworzy użytkowników testowych.
4. Otwórz przeglądarkę pod adresem:
   **[http://localhost:3000](http://localhost:3000)**

## 2. Architektura Systemu

- **Frontend**: React (Vite) + TypeScript. Prosty interfejs SPA.
- **Backend**: Python (FastAPI). Obsługuje API REST oraz logikę biznesową (State Machine).
- **Baza Danych**: PostgreSQL 15.
- **Infrastruktura**: `docker-compose.yml` orkiestrujący 3 kontenery.

## 3. Scenariusze Testowe i Obsługa

Aplikacja obsługuje 3 procesy biznesowe zgodnie z dokumentacją.

### Logowanie
System nie wymaga hasła. Na ekranie startowym wybierz użytkownika (Rolę) z listy, aby "wcielić się" w nią. Lista jest zgodna z `Process to Roles Mapping.docx`.

### Procesy
1. **Wniosek Urlopowy (Leave Request)**
   - Ścieżka dla Nauczyciela Akademickiego (wymaga zgody Rektora).
   - Ścieżka dla pracownika niebędącego nauczycielem (zgoda Kanclerza).
2. **Zmiana Warunków Zatrudnienia**
   - Wielostopniowa akceptacja (Kierownik JO -> Dział Kadr -> Kwestor -> Rektor/Kanclerz).
3. **Wnioski o Odznaczenia**
   - Proces inicjowany przez Kierownika JO, zatwierdzany przez Rektora, obsługiwany zewnętrznie przez WKW.

## 4. Macierz Pokrycia (Coverage Matrix)

| Scenariusz / Krok | Rola (System) | Ekran / Formularz | Warunek BPMN | Status Implementacji |
| :--- | :--- | :--- | :--- | :--- |
| **Leave Request** | | | | |
| 1. Submit Request | Initiator (Teacher) | Start Form | - | Ręczne (API/UI) |
| 2. Review & Forward | Head of O.U. | Task Form | - | Zaimplementowano |
| 3. Review Entitlement | PD (Personnel) | Task Form | - | Zaimplementowano |
| 4. Bramka: Teacher? | System | - | `is_academic=True` | Zaimplementowano |
| 5. Review (PRK) | Vice-Rector Edu | Task Form | - | Zaimplementowano |
| 6. Review (PRN) | Vice-Rector Sci | Task Form | - | Zaimplementowano |
| 7. Decision (RKR) | Rector | Task Form | - | Zaimplementowano |
| 8. Inform Head OU | PD | Task Form | - | Zaimplementowano |
| 9. Register | PD | Task Form | - | Zaimplementowano |
| **Change Employment** | | | | |
| 1. Submit | Initiator | Start Form | - | Ręczne (API/UI) |
| 2. Review (HeadOU) | Head of O.U. | Task Form | - | Zaimplementowano |
| 3. Review (PD) | PD | Task Form | - | Zaimplementowano |
| 4. Review (KWE) | Quartermaster | Task Form | - | Zaimplementowano |
| 5. Bramka: Teacher? | System | - | `is_academic` Var | Zaimplementowano |
| ... Dalsze kroki | Odpowiednie role | Task Form | - | Zaimplementowano |
| **Decorations** | | | | |
| 1. Submit App | Head of O.U. | Start/Task Form | - | Zaimplementowano |
| 2. Present for Accept | PD | Task Form | - | Zaimplementowano |
| 3. Review | PRK / Chancellor | Task Form | - | Zaimplementowano |
| 4. Present to RKR | PD | Task Form | - | Zaimplementowano |
| 5. Decision | Rector | Task Form | - | Zaimplementowano |
| 6. Bramka: Accepted? | System | - | `rkr_decision` | Zaimplementowano |
| 7. Forward to MPD | PD | Task Form | - | Zaimplementowano |
| 8. Handle External | MPD | Task Form | - | Zaimplementowano |
| 9. Receive Decision | PD | Task Form | - | Zaimplementowano |
| 10. Register | PD | Task Form | - | Zaimplementowano |

## 5. Uwagi Techniczne dla Testera
- Baza danych jest resetowana po usunięciu wolumenu Dockera (`docker compose down -v`).
- Logi aplikacji można śledzić poleceniem `docker compose logs -f`.
- Interfejs jest w języku polskim (etykiety), natomiast nazwy ról i zmiennych w systemie pozostały angielskie dla zgodności z dokumentacją źródłową.
