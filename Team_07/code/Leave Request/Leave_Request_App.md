# Leave Request Application - Dokumentacja procesu tworzenia

## Informacje ogólne
- **Nazwa aplikacji**: Leave Request System (DPE/1-3)
- **Wersja**: 1.0
- **Autor**: aideveloper
- **Data utworzenia**: 2025-12-18T09:03:41+01:00

---

## Polecenia użytkownika

### Polecenie 1
**Data/Czas**: 2025-12-18T08:32:30+01:00

**Treść polecenia**:
```
Twoim zadaniem od teraz jest przeanalizowanie dokładnie zawartości plików w podanym folderze. 
Znajdziesz w nim pliki z opisem działania projektu oraz diagram bpmn. Twoim zadaniem jest 
wykonać aplikację z interfejsem użytkownika, która na bazie informacji zawartych w dokumentach 
oraz diagramach, będzie realizować odpowiednie działania.

Technologie:
- ui - python streamlit
- baza danych - sqlite
- backend - python
- zawsze uzywaj venv do kazdego projektu osobno

Folder: Leave Request
```

---

## Podjęte działania

### Faza 1: Analiza dokumentacji
**Data/Czas**: 2025-12-18T08:32:30 - 2025-12-18T09:00:00

**Działania**:
1. Przeanalizowano strukturę folderu `Leave Request`
2. Wyodrębniono i przeanalizowano diagram BPMN (`Leave Request.bpmn`)
3. Wyodrębniono zawartość dokumentów:
   - `Leave Request Data.docx` - definicje danych procesu
   - `Leave Request Test Scenario.docx` - scenariusz testowy

**Odkrycia z analizy BPMN**:
- Proces obsługuje 6 ról: Head of O.U., Personnel Department (PD), Chancellor (KAN), Vice-Rector for Education (PRK), Vice-Rector for Scientific Affairs (PRN), Rector (RKR)
- Dwie ścieżki procesu:
  - Nauczyciel akademicki: Head O.U. → PD → PRK → PRN → Rector → PD (notify) → PD (register)
  - Pracownik nieakademicki: Head O.U. → PD → Chancellor → PD (notify) → PD (register)

**Narzędzia użyte**:
- `list_dir` - analiza struktury folderu
- `view_file` - odczyt pliku BPMN
- `run_command` + skrypt Python - ekstrakcja dokumentów DOCX
- `write_to_file` - utworzenie skryptu `extract_docs.py`

---

### Faza 2: Planowanie
**Data/Czas**: 2025-12-18T09:00:00 - 2025-12-18T09:03:41

**Działania**:
1. Utworzono plan implementacji (`implementation_plan.md`)
2. Zdefiniowano strukturę bazy danych
3. Zaprojektowano architekturę maszyny stanów
4. Zaplanowano interfejs Streamlit

**Narzędzia użyte**:
- `write_to_file` - utworzenie `task.md` i `implementation_plan.md`
- `notify_user` - uzyskanie zatwierdzenia planu od użytkownika

---

### Faza 3: Implementacja
**Data/Czas**: 2025-12-18T09:03:41 - 2025-12-18T09:15:00

**Działania**:
1. Utworzono wirtualne środowisko Python (`venv`)
2. Zainstalowano wymagane pakiety (`streamlit`)
3. Zaimplementowano moduł bazy danych (`database.py`)
4. Zaimplementowano silnik workflow (`workflow.py`)
5. Zaimplementowano interfejs Streamlit (`app.py`)
6. Naprawiono błąd "database is locked" przez dodanie timeout i WAL mode

**Pliki utworzone/zmodyfikowane**:

| Plik | Typ | Opis |
|------|-----|------|
| `venv/` | Katalog | Wirtualne środowisko Python |
| `database.py` | Nowy | Moduł SQLite z 3 tabelami (users, leave_requests, workflow_history) |
| `workflow.py` | Nowy | Silnik workflow z maszyną stanów |
| `app.py` | Nowy | Główna aplikacja Streamlit |
| `leave_request.db` | Nowy (auto) | Plik bazy danych SQLite |

**Narzędzia użyte**:
- `run_command` - utworzenie venv, instalacja streamlit
- `write_to_file` - utworzenie modułów Python
- `replace_file_content` - naprawa błędu bazy danych

---

### Faza 4: Weryfikacja
**Data/Czas**: 2025-12-18T09:15:00 - 2025-12-18T09:20:00

**Działania**:
1. Uruchomiono aplikację Streamlit
2. Zweryfikowano poprawność działania interfejsu
3. Aplikacja dostępna pod adresem: http://localhost:8502

**Narzędzia użyte**:
- `run_command` - uruchomienie streamlit
- `command_status` - sprawdzenie statusu aplikacji

---

## Odpowiedzi programu

### Architektura bazy danych

**Tabela `users`**:
- id (INTEGER PRIMARY KEY)
- username (TEXT UNIQUE)
- full_name (TEXT)
- role (TEXT)
- is_academic_teacher (BOOLEAN)
- leave_balance (INTEGER)

**Tabela `leave_requests`**:
- id (INTEGER PRIMARY KEY)
- employee_name, employee_position (TEXT)
- leave_type, leave_start_date, leave_end_date (TEXT)
- leave_duration_days (INTEGER)
- leave_substitute (TEXT, opcjonalne)
- is_academic_teacher (BOOLEAN)
- employee_leave_balance (INTEGER)
- current_state, current_assignee_role (TEXT)
- head_ou_decision, pd_review_status, prk_review_status, prn_review_status (TEXT)
- final_decision, final_decision_maker (TEXT)

**Tabela `workflow_history`**:
- id (INTEGER PRIMARY KEY)
- request_id (INTEGER, FK)
- action, from_state, to_state (TEXT)
- performed_by_role, performed_by_name (TEXT)
- decision, notes (TEXT)
- created_at (DATETIME)

---

### Stany workflow

| Stan | Opis | Rola wykonawcza |
|------|------|-----------------|
| head_ou_review | Weryfikacja przez Kierownika | Head of O.U. |
| pd_review | Weryfikacja przez Dział Personalny | Personnel Department |
| prk_review | Weryfikacja przez Prorektora ds. Kształcenia | PRK |
| prn_review | Weryfikacja przez Prorektora ds. Naukowych | PRN |
| rector_decision | Decyzja Rektora | Rector |
| chancellor_decision | Decyzja Kanclerza | Chancellor |
| notify_head_ou | Powiadomienie Kierownika | Personnel Department |
| register_hr | Rejestracja w systemie HR | Personnel Department |
| completed | Zakończony | - |
| rejected | Odrzucony | - |

---

## Instrukcje uruchomienia

1. Otwórz terminal w folderze `Leave Request`
2. Aktywuj środowisko wirtualne:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Uruchom aplikację:
   ```powershell
   streamlit run app.py
   ```
4. Otwórz przeglądarkę pod adresem: http://localhost:8502
5. Wybierz rolę w sidebarze i rozpocznij pracę z aplikacją

---

## Wymagania

- Python 3.8+
- Streamlit (zainstalowany w venv)
- SQLite3 (wbudowany w Python)

---

## Podsumowanie

Aplikacja Leave Request System została pomyślnie zaimplementowana zgodnie ze specyfikacją BPMN i dokumentacją. System obsługuje pełny workflow procesu składania wniosków urlopowych z rozróżnieniem ścieżek dla nauczycieli akademickich i pracowników nieakademickich.
