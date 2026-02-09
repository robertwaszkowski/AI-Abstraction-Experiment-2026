# System Zarządzania Procesami (MPP)

Dokumentacja uruchomienia i obsługi systemu budowanego w ramach projektu. System składa się z warstwy frontendowej (React), backendowej (FastAPI) oraz bazy danych (PostgreSQL).

## Wymagania

Aby uruchomić system w najprostszy sposób, potrzebujesz zainstalowanego:
*   **Docker Desktop** (dla Windows/Mac) lub **Docker Engine** + **Docker Compose** (dla Linux).

## Szybki Start (Zalecane)

Cały system jest skoneneryzowany. Aby go uruchomić:

1.  Otwórz terminal (PowerShell, CMD lub Bash) w głównym folderze projektu (tam gdzie jest plik `docker-compose.yml`).
2.  Uruchom komendę budującą i startującą kontenery:
    ```bash
    docker-compose up --build
    ```
3.  Poczekaj, aż wszystkie serwisy wystartują. Przy pierwszym uruchomieniu może to potrwać kilka minut (pobieranie obrazów, instalacja zależności).

## Dostęp do Aplikacji

Po pomyślnym uruchomieniu, usługi są dostępne pod następującymi adresami:

| Usługa | Adres URL | Opis |
| :--- | :--- | :--- |
| **Frontend** | [http://localhost:3000](http://localhost:3000) | Główny interfejs użytkownika (Logowanie, Lista Zadań, Historia) |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | API serwera |
| **Dokumentacja API** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interaktywna dokumentacja Swagger UI |
| **Baza Danych** | `localhost:5432` | PostgreSQL (do połączenia zewnętrznym klientem) |

## Dane Dostępowe

### Baza Danych (PostgreSQL)
*   **Host:** `localhost`
*   **Port:** `5432`
*   **Baza:** `mpp`
*   **Użytkownik:** `postgres`
*   **Hasło:** `postgres`

> **Uwaga dla użytkowników Docker-a:** Jeśli łączysz się z narzędzia uruchomionego w innym kontenerze (np. pgAdmin w Dockerze), jako hosta użyj `host.docker.internal` lub `mpp_db` (zależy od konfiguracji sieci).

### Przykładowi Użytkownicy Systemu
System przy starcie (jeśli baza jest pusta) automatycznie tworzy użytkowników testowych. Możesz zalogować się używając ich nazw użytkownika (hasło nie jest wymagane w obecnej wersji deweloperskiej lub jest domyślne - sprawdź implementację logowania).

*   **Rektor:** `adam.rector`
*   **Kanclerz:** `carl.chancellor`
*   **Dział Kadr (PD):** `penny.personnel`
*   **Wnioskodawcy:** `alice.academic`, `nancy.nonacademic`

## Rozwiązywanie Problemów

1.  **Błąd "Port already in use"**:
    *   Upewnij się, że nie masz uruchomionych innych usług na portach 3000, 8000 lub 5432.
    *   Jeśli masz lokalnie zainstalowanego Postgresa, zatrzymaj go usługę systemową.

2.  **Błąd połączenia z bazą danych w Backendzie**:
    *   Backend czeka na start bazy. Jeśli uruchomi się za szybko, może wyrzucić błąd. Docker Compose zazwyczaj restartuje go automatycznie, aż się połączy.

3.  **Zmiany w kodzie nie są widoczne**:
    *   Dla Frontendu (Vite) i Backendu (FastAPI z reload) zmiany w kodzie powinny być widoczne natychmiast (Hot Reload).
    *   Jeśli dodałeś nowe biblioteki do `requirements.txt` lub `package.json`, musisz przebudować kontenery:
        ```bash
        docker-compose up --build
        ```
