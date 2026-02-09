# System RoleCall

Aplikacja do zarządzania procesami obsługująca "Zmianę warunków zatrudnienia", "Odznaczenia" i "Wnioski urlopowe".

## Wymagania wstępne

*   **Node.js** (v18 lub nowszy)
*   **Docker Desktop** (musi być uruchomiony)

## 1. Instalacja

1.  Otwórz terminal w folderze projektu.
2.  Zainstaluj zależności:
    ```bash
    npm install
    ```

## 2. Konfiguracja Bazy Danych

1.  Uruchom kontener bazy danych PostgreSQL:
    ```bash
    docker-compose up -d
    ```
2.  Wypchnij schemat bazy danych:
    ```bash
    npx prisma db push
    ```

## 3. Uruchomienie Aplikacji

1.  Uruchom serwer deweloperski:
    ```bash
    npm run dev
    ```
2.  Otwórz przeglądarkę pod adresem: `http://localhost:9002` (lub port widoczny w terminalu).

## 4. Zarządzanie Bazą Danych

Aby przeglądać i edytować surowe dane w bazie:
```bash
npx prisma studio
```
To otworzy wizualny edytor pod adresem `http://localhost:5555`.

### Ręczne Dane Połączenia
Jeśli używasz narzędzia takiego jak DBeaver:
*   **Host**: `localhost`
*   **Port**: `5432`
*   **Użytkownik**: `postgres`
*   **Hasło**: `password`
*   **Baza danych**: `rolecall`

