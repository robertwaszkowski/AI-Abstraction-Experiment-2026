# -*- coding: utf-8 -*-
"""
===============================================================================
LEAVE REQUEST APPLICATION - DATABASE MODULE
===============================================================================
Moduł bazy danych SQLite dla aplikacji Leave Request (DPE/1-3).

Zawiera:
- Definicje tabel: users, leave_requests, workflow_history
- Funkcje CRUD dla wszystkich operacji bazodanowych
- Inicjalizacja bazy z domyślnymi użytkownikami

Autor: aideveloper
Wersja: 1.0
===============================================================================
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# =============================================================================
# KONFIGURACJA BAZY DANYCH
# =============================================================================

# Ścieżka do pliku bazy danych (w tym samym folderze co aplikacja)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leave_request.db")


# =============================================================================
# DEFINICJE STANÓW WORKFLOW
# =============================================================================

class WorkflowStates:
    """Klasa przechowująca wszystkie możliwe stany workflow."""
    SUBMITTED = "submitted"
    HEAD_OU_REVIEW = "head_ou_review"
    PD_REVIEW = "pd_review"
    PRK_REVIEW = "prk_review"
    PRN_REVIEW = "prn_review"
    RECTOR_DECISION = "rector_decision"
    CHANCELLOR_DECISION = "chancellor_decision"
    NOTIFY_HEAD_OU = "notify_head_ou"
    REGISTER_HR = "register_hr"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Roles:
    """Klasa przechowująca wszystkie role użytkowników."""
    EMPLOYEE = "Employee"
    HEAD_OU = "Head of O.U."
    PD = "Personnel Department"
    PRK = "Vice-Rector for Education (PRK)"
    PRN = "Vice-Rector for Scientific Affairs (PRN)"
    RECTOR = "Rector (RKR)"
    CHANCELLOR = "Chancellor (KAN)"
    
    @classmethod
    def all_roles(cls) -> List[str]:
        """Zwraca listę wszystkich ról."""
        return [cls.EMPLOYEE, cls.HEAD_OU, cls.PD, cls.PRK, cls.PRN, cls.RECTOR, cls.CHANCELLOR]


# =============================================================================
# POŁĄCZENIE Z BAZĄ DANYCH
# =============================================================================

def get_connection() -> sqlite3.Connection:
    """
    Tworzy i zwraca połączenie z bazą danych SQLite.
    
    Używa timeout=30 sekund aby uniknąć błędów 'database is locked'.
    Włącza WAL mode dla lepszej współbieżności.
    
    Returns:
        sqlite3.Connection: Połączenie z bazą danych.
    """
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Umożliwia dostęp do kolumn po nazwie
    # Włącz WAL mode dla lepszej współbieżności
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# =============================================================================
# INICJALIZACJA BAZY DANYCH
# =============================================================================

def init_database() -> None:
    """
    Inicjalizuje bazę danych - tworzy tabele jeśli nie istnieją
    oraz dodaje domyślnych użytkowników.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # ---------------------------------------------------------------------
        # Tabela użytkowników (users)
        # ---------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                is_academic_teacher BOOLEAN DEFAULT 0,
                leave_balance INTEGER DEFAULT 26,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ---------------------------------------------------------------------
        # Tabela wniosków urlopowych (leave_requests)
        # ---------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Dane z formularza 23/DPE (Request Initiation Data)
                employee_name TEXT NOT NULL,
                employee_position TEXT NOT NULL,
                leave_type TEXT NOT NULL,
                leave_start_date DATE NOT NULL,
                leave_end_date DATE NOT NULL,
                leave_duration_days INTEGER NOT NULL,
                leave_substitute TEXT,
                request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Dane routingu (Contextual and Routing Data)
                is_academic_teacher BOOLEAN DEFAULT 1,
                employee_leave_balance INTEGER DEFAULT 26,
                
                -- Status workflow
                current_state TEXT DEFAULT 'head_ou_review',
                current_assignee_role TEXT DEFAULT 'Head of O.U.',
                
                -- Decyzje (Process-Generated Data)
                head_ou_decision TEXT,
                pd_review_status TEXT,
                lss_opinion_notes TEXT,
                prk_review_status TEXT,
                prn_review_status TEXT,
                final_decision TEXT,
                final_decision_maker TEXT,
                
                -- Metadane
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ---------------------------------------------------------------------
        # Tabela historii workflow (workflow_history)
        # ---------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT,
                performed_by_role TEXT NOT NULL,
                performed_by_name TEXT,
                decision TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES leave_requests (id)
            )
        """)
        
        # ---------------------------------------------------------------------
        # Dodanie domyślnych użytkowników (zgodnie ze scenariuszem testowym)
        # ---------------------------------------------------------------------
        default_users = [
            ("alice_academic", "Alice Academic", Roles.EMPLOYEE, True, 26),
            ("bob_staff", "Bob Staff", Roles.EMPLOYEE, False, 26),
            ("holly_head", "Holly Head", Roles.HEAD_OU, False, 26),
            ("penny_personnel", "Penny Personnel", Roles.PD, False, 26),
            ("paula_vredu", "Paula VREdu", Roles.PRK, False, 26),
            ("peter_vrsci", "Peter VRSci", Roles.PRN, False, 26),
            ("adam_rector", "Adam Rector", Roles.RECTOR, False, 26),
            ("karl_chancellor", "Karl Chancellor", Roles.CHANCELLOR, False, 26),
        ]
        
        for user_data in default_users:
            try:
                cursor.execute("""
                    INSERT INTO users (username, full_name, role, is_academic_teacher, leave_balance)
                    VALUES (?, ?, ?, ?, ?)
                """, user_data)
            except sqlite3.IntegrityError:
                # Użytkownik już istnieje - pomijamy
                pass
        
        conn.commit()
        
        # ---------------------------------------------------------------------
        # Dodanie przykładowych wniosków (jeśli tabela pusta)
        # ---------------------------------------------------------------------
        cursor.execute("SELECT COUNT(*) FROM leave_requests")
        if cursor.fetchone()[0] == 0:
            samples = [
                ("Alice Academic", "Professor", "Recreational", "2025-07-01", "2025-07-14", 14, "Bob Staff", 1, WorkflowStates.PD_REVIEW, Roles.PD),
                ("Bob Staff", "Admin", "Unpaid", "2025-06-01", "2025-06-05", 5, None, 0, WorkflowStates.HEAD_OU_REVIEW, Roles.HEAD_OU),
                ("Charlie Consultant", "Lecturer", "Training", "2025-09-01", "2025-09-03", 3, "Alice Academic", 1, WorkflowStates.COMPLETED, None) # Completed - no role
            ]

            for s in samples:
                 cursor.execute("""
                    INSERT INTO leave_requests (
                        employee_name, employee_position, leave_type,
                        leave_start_date, leave_end_date, leave_duration_days,
                        leave_substitute, is_academic_teacher, employee_leave_balance,
                        current_state, current_assignee_role
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], 26, s[8], s[9]))
            
            conn.commit()
        
    finally:
        conn.close()


# =============================================================================
# OPERACJE NA UŻYTKOWNIKACH
# =============================================================================

def get_all_users() -> List[Dict[str, Any]]:
    """
    Pobiera wszystkich użytkowników z bazy danych.
    
    Returns:
        List[Dict]: Lista słowników z danymi użytkowników.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY role, full_name")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_users_by_role(role: str) -> List[Dict[str, Any]]:
    """
    Pobiera użytkowników o określonej roli.
    
    Args:
        role: Nazwa roli użytkownika.
        
    Returns:
        List[Dict]: Lista użytkowników z daną rolą.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = ?", (role,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# =============================================================================
# OPERACJE NA WNIOSKACH URLOPOWYCH
# =============================================================================

def create_leave_request(
    employee_name: str,
    employee_position: str,
    leave_type: str,
    leave_start_date: str,
    leave_end_date: str,
    leave_duration_days: int,
    leave_substitute: Optional[str] = None,
    is_academic_teacher: bool = True,
    employee_leave_balance: int = 26
) -> int:
    """
    Tworzy nowy wniosek urlopowy.
    
    Args:
        employee_name: Imię i nazwisko pracownika.
        employee_position: Stanowisko pracownika.
        leave_type: Typ urlopu.
        leave_start_date: Data rozpoczęcia urlopu.
        leave_end_date: Data zakończenia urlopu.
        leave_duration_days: Liczba dni urlopu.
        leave_substitute: Osoba zastępująca (opcjonalne).
        is_academic_teacher: Czy pracownik jest nauczycielem akademickim.
        employee_leave_balance: Saldo dni urlopowych.
        
    Returns:
        int: ID utworzonego wniosku.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO leave_requests (
                employee_name, employee_position, leave_type,
                leave_start_date, leave_end_date, leave_duration_days,
                leave_substitute, is_academic_teacher, employee_leave_balance,
                current_state, current_assignee_role
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_name, employee_position, leave_type,
            leave_start_date, leave_end_date, leave_duration_days,
            leave_substitute, is_academic_teacher, employee_leave_balance,
            WorkflowStates.HEAD_OU_REVIEW, Roles.HEAD_OU
        ))
        
        request_id = cursor.lastrowid
        
        # Dodaj wpis do historii bezpośrednio (unikamy deadlocka)
        cursor.execute("""
            INSERT INTO workflow_history (
                request_id, action, from_state, to_state,
                performed_by_role, performed_by_name, decision, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id, "Leave Request Submitted", None, WorkflowStates.HEAD_OU_REVIEW,
            Roles.EMPLOYEE, employee_name, None, f"Leave type: {leave_type}, Duration: {leave_duration_days} days"
        ))
        
        conn.commit()
        return request_id
        
    finally:
        conn.close()


def get_leave_request(request_id: int) -> Optional[Dict[str, Any]]:
    """
    Pobiera szczegóły wniosku urlopowego.
    
    Args:
        request_id: ID wniosku.
        
    Returns:
        Dict lub None: Dane wniosku lub None jeśli nie znaleziono.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_leave_requests() -> List[Dict[str, Any]]:
    """
    Pobiera wszystkie wnioski urlopowe.
    
    Returns:
        List[Dict]: Lista wszystkich wniosków.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leave_requests ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_pending_requests_for_role(role: str) -> List[Dict[str, Any]]:
    """
    Pobiera wnioski oczekujące na działanie dla danej roli.
    
    Args:
        role: Rola użytkownika.
        
    Returns:
        List[Dict]: Lista wniosków przypisanych do danej roli.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM leave_requests 
            WHERE current_assignee_role = ? 
            AND current_state NOT IN (?, ?)
            ORDER BY created_at DESC
        """, (role, WorkflowStates.COMPLETED, WorkflowStates.REJECTED))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_leave_request(
    request_id: int,
    updates: Dict[str, Any]
) -> bool:
    """
    Aktualizuje wniosek urlopowy.
    
    Args:
        request_id: ID wniosku do aktualizacji.
        updates: Słownik z polami do aktualizacji.
        
    Returns:
        bool: True jeśli aktualizacja się powiodła, False w przeciwnym razie.
    """
    if not updates:
        return False
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Budowanie zapytania UPDATE
        set_clauses = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [request_id]
        
        cursor.execute(f"""
            UPDATE leave_requests 
            SET {set_clauses}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        
        conn.commit()
        return cursor.rowcount > 0
        
    finally:
        conn.close()


# =============================================================================
# OPERACJE NA HISTORII WORKFLOW
# =============================================================================

def add_workflow_history(
    request_id: int,
    action: str,
    from_state: Optional[str],
    to_state: str,
    performed_by_role: str,
    performed_by_name: Optional[str] = None,
    decision: Optional[str] = None,
    notes: Optional[str] = None
) -> int:
    """
    Dodaje wpis do historii workflow.
    
    Args:
        request_id: ID wniosku.
        action: Opis wykonanej akcji.
        from_state: Stan przed akcją.
        to_state: Stan po akcji.
        performed_by_role: Rola wykonującego.
        performed_by_name: Imię wykonującego.
        decision: Podjęta decyzja (opcjonalne).
        notes: Dodatkowe notatki (opcjonalne).
        
    Returns:
        int: ID wpisu w historii.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workflow_history (
                request_id, action, from_state, to_state,
                performed_by_role, performed_by_name, decision, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id, action, from_state, to_state,
            performed_by_role, performed_by_name, decision, notes
        ))
        
        conn.commit()
        return cursor.lastrowid
        
    finally:
        conn.close()


def get_workflow_history(request_id: int) -> List[Dict[str, Any]]:
    """
    Pobiera historię workflow dla danego wniosku.
    
    Args:
        request_id: ID wniosku.
        
    Returns:
        List[Dict]: Lista wpisów historii w kolejności chronologicznej.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM workflow_history 
            WHERE request_id = ? 
            ORDER BY created_at ASC
        """, (request_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# =============================================================================
# STATYSTYKI
# =============================================================================

def get_statistics() -> Dict[str, Any]:
    """
    Pobiera statystyki systemu.
    
    Returns:
        Dict: Słownik ze statystykami.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Całkowita liczba wniosków
        cursor.execute("SELECT COUNT(*) as total FROM leave_requests")
        total = cursor.fetchone()['total']
        
        # Wnioski według statusu
        cursor.execute("""
            SELECT current_state, COUNT(*) as count 
            FROM leave_requests 
            GROUP BY current_state
        """)
        by_state = {row['current_state']: row['count'] for row in cursor.fetchall()}
        
        # Wnioski według typu urlopu
        cursor.execute("""
            SELECT leave_type, COUNT(*) as count 
            FROM leave_requests 
            GROUP BY leave_type
        """)
        by_type = {row['leave_type']: row['count'] for row in cursor.fetchall()}
        
        return {
            'total_requests': total,
            'by_state': by_state,
            'by_type': by_type,
            'pending': total - by_state.get(WorkflowStates.COMPLETED, 0) - by_state.get(WorkflowStates.REJECTED, 0),
            'completed': by_state.get(WorkflowStates.COMPLETED, 0),
            'rejected': by_state.get(WorkflowStates.REJECTED, 0)
        }
        
    finally:
        conn.close()


# =============================================================================
# INICJALIZACJA PRZY IMPORCIE
# =============================================================================

# Automatyczna inicjalizacja bazy przy pierwszym imporcie modułu
init_database()
