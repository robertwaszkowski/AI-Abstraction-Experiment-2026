# Decorations and Medals Application - Development Documentation

## aideveloper
### Decorations and Medals System v1.0

**Podsumowanie:** Aplikacja workflow do obsługi procesu przyznawania odznaczeń i medali zgodnie z diagramem BPMN DPE/1-6 - system Streamlit z bazą SQLite, obsługą 5 ról użytkowników i pełnym przepływem zatwierdzania/odrzucania wniosków.

---

## 1. Informacje o Projekcie

| Pole | Wartość |
|------|---------|
| **Data rozpoczęcia** | 2025-12-18 08:09:43 |
| **Data zakończenia** | 2025-12-18 08:24:XX |
| **Wersja** | 1.0 |
| **Autor** | aideveloper |
| **Technologie** | Python, Streamlit, SQLite |

---

## 2. Polecenie Użytkownika

**Czas:** 2025-12-18 08:09:43+01:00

```
Twoim zadaniem od teraz jest przeanalizowanie dokładnie zawartości plików w podanym folderze. 
Znajdziesz w nim pliki z opisem działania projektu oraz diagram bpmn. Twoim zadaniem jest 
wykonać aplikację z interfejsem użytkownika, która na bazie informacji zawartych w dokumentach 
oraz diagramach, będzie realizować odpowiednie działania.

Technologie:
- UI: Python Streamlit
- Baza danych: SQLite
- Backend: Python
- Zawsze używaj venv do każdego projektu osobno
```

---

## 3. Analiza Dokumentacji

### 3.1 Przeanalizowane Pliki

| Plik | Typ | Opis |
|------|-----|------|
| `Decorations and Medals.bpmn` | BPMN 2.0 | Diagram procesu z 5 rolami i 9 zadaniami |
| `Decorations and Medals Data.docx` | DOCX | Specyfikacja danych aplikacji |
| `Decorations and Medals Test Scenario.docx` | DOCX | Scenariusz testowy z użytkownikami |

### 3.2 Zidentyfikowane Role (z BPMN)

1. **Head of O.U.** (Kierownik Jednostki Organizacyjnej) - inicjuje wnioski
2. **Personnel Department (PD)** (Dział Personalny) - routing i rejestr
3. **PRK / Chancellor** (PRK/Kanclerz) - opiniuje wnioski
4. **Rector (RKR)** (Rektor) - podejmuje decyzje akceptacji/odrzucenia
5. **Military Personnel Department (MPD)** (WKW) - obsługa zewnętrzna

### 3.3 Model Danych

**Dane Aplikacji:**
- `employee_name` - imię i nazwisko pracownika
- `organizational_unit` - jednostka organizacyjna
- `decoration_type` - typ odznaczenia
- `application_justification` - uzasadnienie wniosku

**Dane Procesu:**
- `reviewer_opinion` - opinia PRK/Kanclerza
- `rkr_decision` - decyzja Rektora (Accepted/Rejected)
- `award_grant_date` - data przyznania odznaczenia
- `process_outcome` - wynik procesu (Completed/Rejected)

---

## 4. Podjęte Działania

### 4.1 Konfiguracja Środowiska

**Czas:** 2025-12-18 08:14:38+01:00

**Narzędzia użyte:**
- `python -m venv venv` - utworzenie wirtualnego środowiska
- `pip install streamlit` - instalacja zależności

**Wynik:** Środowisko wirtualne utworzone pomyślnie w folderze `venv/`

### 4.2 Utworzone Pliki

#### database.py (2025-12-18 08:15:XX)
**Opis:** Warstwa bazy danych SQLite

**Zawartość:**
- Klasy enum: `UserRole`, `ProcessState`, `RKRDecision`
- Tabele: `users`, `applications`, `process_history`
- Funkcje CRUD: `create_application`, `get_application_by_id`, `update_application_state`
- Użytkownicy testowi z dokumentacji scenariusza testowego

**Linie kodu:** ~400

---

#### workflow.py (2025-12-18 08:16:XX)
**Opis:** Logika maszyny stanów workflow

**Zawartość:**
- Mapowanie stanów na nazwy zadań
- Funkcje przejść dla każdego kroku procesu
- Walidacja uprawnień użytkowników
- Obsługa gateway'a decyzyjnego Rektora

**Linie kodu:** ~350

---

#### app.py (2025-12-18 08:17:XX)
**Opis:** Główna aplikacja Streamlit UI

**Zawartość:**
- Strona logowania z wyborem użytkowników według ról
- Dashboard z metrykami i zadaniami
- Formularze dla każdego kroku workflow
- Rejestr odznaczeń
- Historia aplikacji

**Linie kodu:** ~750

---

## 5. Weryfikacja

### 5.1 Test Scenariusza Zatwierdzenia

**Czas rozpoczęcia:** 2025-12-18 08:18:XX

**Kroki wykonane:**

| Krok | Użytkownik | Akcja | Wynik |
|------|------------|-------|-------|
| 1 | Holly Head | Złożenie wniosku dla Peter VRSci | ✅ Application ID: 1 |
| 2 | Penny Personnel | Przekazanie do PRK/Kanclerza | ✅ Forwarded |
| 3 | Paula VREdu | Opinia: "Strongly support" | ✅ Opinion saved |
| 4 | Penny Personnel | Prezentacja Rektorowi | ✅ Presented |
| 5 | Adam Rector | Decyzja: Accepted | ✅ Accepted |
| 6 | Penny Personnel | Przekazanie do MPD | ✅ Forwarded |
| 7 | Mike MPD | Obsługa zewnętrzna | ✅ External handled |
| 8 | Penny Personnel | Otrzymanie decyzji | ✅ Decision received |
| 9 | Penny Personnel | Wpis do rejestru | ✅ Registered + 🎈 |

**Wynik końcowy:** Proces zakończony sukcesem. Odznaczenie wpisane do rejestru.

### 5.2 Nagrania Testów

Nagrania z testów przeglądarki dostępne w:
- `app_test_approval_flow_1766042536496.webp`
- `test_pd_prk_steps_1766042648094.webp`
- `test_rector_mpd_completion_1766042809026.webp`
- `final_verification_1766042844390.webp`

---

## 6. Instrukcje Uruchomienia

1. **Aktywuj środowisko wirtualne:**
   ```powershell
   cd "c:\Users\pawel\Desktop\MIPB2\Re_ Projekt ai\Decorations and Medals"
   .\venv\Scripts\Activate.ps1
   ```

2. **Uruchom aplikację:**
   ```powershell
   streamlit run app.py
   ```

3. **Otwórz przeglądarkę:**
   Przejdź do `http://localhost:8501`

4. **Zaloguj się jako jeden z użytkowników testowych:**
   - Holly Head (Head of O.U.)
   - Penny Personnel (PD)
   - Paula VREdu (PRK/Chancellor)
   - Adam Rector (Rector)
   - Mike MPD (MPD)

5. **Wykonuj zadania zgodnie ze swoją rolą**

---

## 7. Struktura Projektu

```
Decorations and Medals/
├── venv/                    # Wirtualne środowisko Python
├── app.py                   # Główna aplikacja Streamlit
├── database.py              # Warstwa bazy danych SQLite
├── workflow.py              # Logika maszyny stanów
├── decorations_medals.db    # Baza danych (tworzona automatycznie)
├── DecorationsAndMedals.md  # Ta dokumentacja
├── Decorations and Medals.bpmn         # Diagram BPMN (źródło)
├── Decorations and Medals Data.docx    # Specyfikacja danych
└── Decorations and Medals Test Scenario.docx  # Scenariusz testowy
```

---

## 8. Czy chcesz wprowadzić jakiekolwiek dalsze zmiany?

Aplikacja jest w pełni funkcjonalna i przetestowana zgodnie ze scenariuszem testowym. Możliwe rozszerzenia:

- Dodanie autentykacji hasłem
- Eksport rejestru do PDF/Excel
- Powiadomienia email
- Wielojęzyczność (PL/EN)
- Statystyki i raporty analityczne
