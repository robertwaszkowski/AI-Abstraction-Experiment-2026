# -*- coding: utf-8 -*-
"""
===============================================================================
LEAVE REQUEST APPLICATION - UNIT TESTS
===============================================================================
Testy jednostkowe dla aplikacji Leave Request (DPE/1-3).

Testowane moduły:
- database.py - operacje bazodanowe
- workflow.py - silnik workflow

Uruchomienie:
    python test_leave_request.py

Autor: aideveloper
Wersja: 1.0
===============================================================================
"""

import unittest
import os
import sqlite3
import sys

# Dodanie bieżącego katalogu do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# FIXTURE: Przed importem modułów, ustawiamy testową bazę danych
# =============================================================================

# Używamy in-memory database dla pełnej izolacji od produkcyjnej aplikacji
TEST_DB_PATH = ":memory:"

# Importujemy moduły i podmieniamy ścieżkę bazy
import database
import workflow

# Podmiana ścieżki bazy danych PRZED inicjalizacją
database.DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_isolated.db")

# Usunięcie starej bazy testowej jeśli istnieje
if os.path.exists(database.DATABASE_PATH):
    try:
        os.remove(database.DATABASE_PATH)
    except:
        pass

# Reinicjalizacja z nową ścieżką
database.init_database()


# =============================================================================
# TESTY MODUŁU DATABASE - STAŁE I KLASY
# =============================================================================

class TestRolesClass(unittest.TestCase):
    """Testy dla klasy Roles."""
    
    def test_all_roles_returns_list(self):
        """Test: all_roles() zwraca listę."""
        roles = database.Roles.all_roles()
        self.assertIsInstance(roles, list)
    
    def test_all_roles_contains_seven_roles(self):
        """Test: all_roles() zawiera 7 ról."""
        roles = database.Roles.all_roles()
        self.assertEqual(len(roles), 7)
    
    def test_employee_role_value(self):
        """Test: Rola EMPLOYEE ma poprawną wartość."""
        self.assertEqual(database.Roles.EMPLOYEE, "Employee")
    
    def test_head_ou_role_value(self):
        """Test: Rola HEAD_OU ma poprawną wartość."""
        self.assertEqual(database.Roles.HEAD_OU, "Head of O.U.")
    
    def test_pd_role_value(self):
        """Test: Rola PD ma poprawną wartość."""
        self.assertEqual(database.Roles.PD, "Personnel Department")
    
    def test_prk_role_value(self):
        """Test: Rola PRK ma poprawną wartość."""
        self.assertEqual(database.Roles.PRK, "Vice-Rector for Education (PRK)")
    
    def test_prn_role_value(self):
        """Test: Rola PRN ma poprawną wartość."""
        self.assertEqual(database.Roles.PRN, "Vice-Rector for Scientific Affairs (PRN)")
    
    def test_rector_role_value(self):
        """Test: Rola RECTOR ma poprawną wartość."""
        self.assertEqual(database.Roles.RECTOR, "Rector (RKR)")
    
    def test_chancellor_role_value(self):
        """Test: Rola CHANCELLOR ma poprawną wartość."""
        self.assertEqual(database.Roles.CHANCELLOR, "Chancellor (KAN)")


class TestWorkflowStatesClass(unittest.TestCase):
    """Testy dla klasy WorkflowStates."""
    
    def test_submitted_state_value(self):
        """Test: Stan SUBMITTED ma poprawną wartość."""
        self.assertEqual(database.WorkflowStates.SUBMITTED, "submitted")
    
    def test_head_ou_review_state_value(self):
        """Test: Stan HEAD_OU_REVIEW ma poprawną wartość."""
        self.assertEqual(database.WorkflowStates.HEAD_OU_REVIEW, "head_ou_review")
    
    def test_pd_review_state_value(self):
        """Test: Stan PD_REVIEW ma poprawną wartość."""
        self.assertEqual(database.WorkflowStates.PD_REVIEW, "pd_review")
    
    def test_completed_state_value(self):
        """Test: Stan COMPLETED ma poprawną wartość."""
        self.assertEqual(database.WorkflowStates.COMPLETED, "completed")
    
    def test_rejected_state_value(self):
        """Test: Stan REJECTED ma poprawną wartość."""
        self.assertEqual(database.WorkflowStates.REJECTED, "rejected")


# =============================================================================
# TESTY MODUŁU DATABASE - OPERACJE NA BAZIE
# =============================================================================

class TestDatabaseConnection(unittest.TestCase):
    """Testy dla połączenia z bazą danych."""
    
    def test_get_connection_returns_connection_object(self):
        """Test: get_connection() zwraca obiekt Connection."""
        conn = database.get_connection()
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()
    
    def test_get_connection_uses_row_factory(self):
        """Test: Połączenie używa Row factory."""
        conn = database.get_connection()
        self.assertEqual(conn.row_factory, sqlite3.Row)
        conn.close()


class TestDatabaseTables(unittest.TestCase):
    """Testy dla tabel bazy danych."""
    
    def test_users_table_exists(self):
        """Test: Tabela users istnieje."""
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result)
    
    def test_leave_requests_table_exists(self):
        """Test: Tabela leave_requests istnieje."""
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leave_requests'")
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result)
    
    def test_workflow_history_table_exists(self):
        """Test: Tabela workflow_history istnieje."""
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_history'")
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result)


class TestDefaultUsers(unittest.TestCase):
    """Testy dla domyślnych użytkowników."""
    
    def test_default_users_exist(self):
        """Test: Domyślni użytkownicy są utworzeni."""
        users = database.get_all_users()
        self.assertGreater(len(users), 0)
    
    def test_alice_academic_exists(self):
        """Test: Użytkownik Alice Academic istnieje."""
        users = database.get_all_users()
        usernames = [u['username'] for u in users]
        self.assertIn('alice_academic', usernames)
    
    def test_holly_head_exists(self):
        """Test: Użytkownik Holly Head istnieje."""
        users = database.get_all_users()
        usernames = [u['username'] for u in users]
        self.assertIn('holly_head', usernames)


class TestLeaveRequestCRUD(unittest.TestCase):
    """Testy CRUD dla wniosków urlopowych."""
    
    def test_create_leave_request_returns_id(self):
        """Test: create_leave_request() zwraca ID."""
        request_id = database.create_leave_request(
            employee_name="Test User Create",
            employee_position="Tester",
            leave_type="Recreational",
            leave_start_date="2025-01-15",
            leave_end_date="2025-01-20",
            leave_duration_days=5
        )
        self.assertIsInstance(request_id, int)
        self.assertGreater(request_id, 0)
    
    def test_get_leave_request_returns_data(self):
        """Test: get_leave_request() zwraca dane wniosku."""
        request_id = database.create_leave_request(
            employee_name="Test User Get",
            employee_position="Developer",
            leave_type="Training",
            leave_start_date="2025-02-01",
            leave_end_date="2025-02-10",
            leave_duration_days=10
        )
        request = database.get_leave_request(request_id)
        self.assertIsNotNone(request)
        self.assertEqual(request['employee_name'], "Test User Get")
    
    def test_get_leave_request_not_found_returns_none(self):
        """Test: get_leave_request() dla nieistniejącego ID zwraca None."""
        request = database.get_leave_request(99999)
        self.assertIsNone(request)
    
    def test_update_leave_request_updates_data(self):
        """Test: update_leave_request() aktualizuje dane."""
        request_id = database.create_leave_request(
            employee_name="Test User Update",
            employee_position="Analyst",
            leave_type="Childcare",
            leave_start_date="2025-03-01",
            leave_end_date="2025-03-05",
            leave_duration_days=5
        )
        
        success = database.update_leave_request(request_id, {
            'head_ou_decision': 'Approved'
        })
        self.assertTrue(success)
        
        updated = database.get_leave_request(request_id)
        self.assertEqual(updated['head_ou_decision'], 'Approved')


class TestWorkflowHistory(unittest.TestCase):
    """Testy dla historii workflow."""
    
    def test_add_workflow_history_returns_id(self):
        """Test: add_workflow_history() zwraca ID."""
        request_id = database.create_leave_request(
            employee_name="History Test",
            employee_position="Manager",
            leave_type="Recreational",
            leave_start_date="2025-04-01",
            leave_end_date="2025-04-05",
            leave_duration_days=5
        )
        
        history_id = database.add_workflow_history(
            request_id=request_id,
            action="Test Action",
            from_state="head_ou_review",
            to_state="pd_review",
            performed_by_role=database.Roles.HEAD_OU
        )
        self.assertIsInstance(history_id, int)
        self.assertGreater(history_id, 0)
    
    def test_get_workflow_history_returns_list(self):
        """Test: get_workflow_history() zwraca listę."""
        request_id = database.create_leave_request(
            employee_name="History Get Test",
            employee_position="Designer",
            leave_type="Unpaid",
            leave_start_date="2025-05-01",
            leave_end_date="2025-05-03",
            leave_duration_days=3
        )
        
        history = database.get_workflow_history(request_id)
        self.assertIsInstance(history, list)


class TestStatistics(unittest.TestCase):
    """Testy dla statystyk."""
    
    def test_get_statistics_returns_dict(self):
        """Test: get_statistics() zwraca słownik."""
        stats = database.get_statistics()
        self.assertIsInstance(stats, dict)
    
    def test_get_statistics_contains_total_requests(self):
        """Test: Statystyki zawierają total_requests."""
        stats = database.get_statistics()
        self.assertIn('total_requests', stats)
    
    def test_get_statistics_contains_by_state(self):
        """Test: Statystyki zawierają by_state."""
        stats = database.get_statistics()
        self.assertIn('by_state', stats)


# =============================================================================
# TESTY MODUŁU WORKFLOW
# =============================================================================

class TestWorkflowHelpers(unittest.TestCase):
    """Testy dla funkcji pomocniczych workflow."""
    
    def test_get_state_description_returns_string(self):
        """Test: get_state_description() zwraca string."""
        desc = workflow.get_state_description(database.WorkflowStates.HEAD_OU_REVIEW)
        self.assertIsInstance(desc, str)
    
    def test_get_task_name_head_ou(self):
        """Test: Nazwa zadania dla HEAD_OU_REVIEW."""
        task = workflow.get_task_name(database.WorkflowStates.HEAD_OU_REVIEW)
        self.assertEqual(task, "Review and approve leave request")
    
    def test_get_task_name_pd(self):
        """Test: Nazwa zadania dla PD_REVIEW."""
        task = workflow.get_task_name(database.WorkflowStates.PD_REVIEW)
        self.assertEqual(task, "Review leave request (check entitlement)")
    
    def test_get_assignee_role_head_ou(self):
        """Test: Rola dla stanu HEAD_OU_REVIEW."""
        role = workflow.get_assignee_role(database.WorkflowStates.HEAD_OU_REVIEW)
        self.assertEqual(role, database.Roles.HEAD_OU)
    
    def test_get_assignee_role_completed_is_none(self):
        """Test: Rola dla stanu COMPLETED jest None."""
        role = workflow.get_assignee_role(database.WorkflowStates.COMPLETED)
        self.assertIsNone(role)
    
    def test_can_process_task_correct_role(self):
        """Test: can_process_task() zwraca True dla poprawnej roli."""
        result = workflow.can_process_task(
            database.Roles.HEAD_OU, 
            database.WorkflowStates.HEAD_OU_REVIEW
        )
        self.assertTrue(result)
    
    def test_can_process_task_wrong_role(self):
        """Test: can_process_task() zwraca False dla błędnej roli."""
        result = workflow.can_process_task(
            database.Roles.EMPLOYEE, 
            database.WorkflowStates.HEAD_OU_REVIEW
        )
        self.assertFalse(result)


class TestGetNextState(unittest.TestCase):
    """Testy dla funkcji get_next_state()."""
    
    def test_head_ou_approved_goes_to_pd(self):
        """Test: HEAD_OU_REVIEW + Approved -> PD_REVIEW."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.HEAD_OU_REVIEW, "Approved"
        )
        self.assertEqual(next_state, database.WorkflowStates.PD_REVIEW)
        self.assertEqual(next_role, database.Roles.PD)
    
    def test_head_ou_rejected_goes_to_rejected(self):
        """Test: HEAD_OU_REVIEW + Rejected -> REJECTED."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.HEAD_OU_REVIEW, "Rejected"
        )
        self.assertEqual(next_state, database.WorkflowStates.REJECTED)
    
    def test_pd_academic_goes_to_prk(self):
        """Test: PD_REVIEW + academic=True -> PRK_REVIEW."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.PD_REVIEW, "Approved", is_academic_teacher=True
        )
        self.assertEqual(next_state, database.WorkflowStates.PRK_REVIEW)
        self.assertEqual(next_role, database.Roles.PRK)
    
    def test_pd_non_academic_goes_to_chancellor(self):
        """Test: PD_REVIEW + academic=False -> CHANCELLOR_DECISION."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.PD_REVIEW, "Approved", is_academic_teacher=False
        )
        self.assertEqual(next_state, database.WorkflowStates.CHANCELLOR_DECISION)
        self.assertEqual(next_role, database.Roles.CHANCELLOR)
    
    def test_prk_approved_goes_to_prn(self):
        """Test: PRK_REVIEW + Approved -> PRN_REVIEW."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.PRK_REVIEW, "Approved"
        )
        self.assertEqual(next_state, database.WorkflowStates.PRN_REVIEW)
        self.assertEqual(next_role, database.Roles.PRN)
    
    def test_prn_approved_goes_to_rector(self):
        """Test: PRN_REVIEW + Approved -> RECTOR_DECISION."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.PRN_REVIEW, "Approved"
        )
        self.assertEqual(next_state, database.WorkflowStates.RECTOR_DECISION)
        self.assertEqual(next_role, database.Roles.RECTOR)
    
    def test_rector_approved_goes_to_notify(self):
        """Test: RECTOR_DECISION + Approved -> NOTIFY_HEAD_OU."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.RECTOR_DECISION, "Approved"
        )
        self.assertEqual(next_state, database.WorkflowStates.NOTIFY_HEAD_OU)
        self.assertEqual(next_role, database.Roles.PD)
    
    def test_chancellor_approved_goes_to_notify(self):
        """Test: CHANCELLOR_DECISION + Approved -> NOTIFY_HEAD_OU."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.CHANCELLOR_DECISION, "Approved"
        )
        self.assertEqual(next_state, database.WorkflowStates.NOTIFY_HEAD_OU)
        self.assertEqual(next_role, database.Roles.PD)
    
    def test_notify_goes_to_register(self):
        """Test: NOTIFY_HEAD_OU + Completed -> REGISTER_HR."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.NOTIFY_HEAD_OU, "Completed"
        )
        self.assertEqual(next_state, database.WorkflowStates.REGISTER_HR)
    
    def test_register_goes_to_completed(self):
        """Test: REGISTER_HR + Completed -> COMPLETED."""
        next_state, next_role = workflow.get_next_state(
            database.WorkflowStates.REGISTER_HR, "Completed"
        )
        self.assertEqual(next_state, database.WorkflowStates.COMPLETED)


class TestAvailableDecisions(unittest.TestCase):
    """Testy dla funkcji get_available_decisions()."""
    
    def test_head_ou_has_approved_rejected(self):
        """Test: HEAD_OU_REVIEW ma decyzje Approved/Rejected."""
        decisions = workflow.get_available_decisions(database.WorkflowStates.HEAD_OU_REVIEW)
        self.assertIn("Approved", decisions)
        self.assertIn("Rejected", decisions)
    
    def test_pd_has_entitlement_options(self):
        """Test: PD_REVIEW ma decyzje Entitlement."""
        decisions = workflow.get_available_decisions(database.WorkflowStates.PD_REVIEW)
        self.assertIn("Entitlement Confirmed", decisions)
        self.assertIn("Entitlement Exceeded", decisions)


class TestProcessTask(unittest.TestCase):
    """Testy dla funkcji process_task()."""
    
    def test_process_task_not_found_request(self):
        """Test: process_task() dla nieistniejącego wniosku zwraca błąd."""
        success, msg = workflow.process_task(
            request_id=99999,
            performed_by_role=database.Roles.HEAD_OU,
            decision="Approved"
        )
        self.assertFalse(success)
    
    def test_process_task_wrong_role_fails(self):
        """Test: process_task() z błędną rolą zwraca błąd."""
        request_id = database.create_leave_request(
            employee_name="Process Test Wrong Role",
            employee_position="Tester",
            leave_type="Recreational",
            leave_start_date="2025-06-01",
            leave_end_date="2025-06-05",
            leave_duration_days=5
        )
        
        success, msg = workflow.process_task(
            request_id=request_id,
            performed_by_role=database.Roles.EMPLOYEE,
            decision="Approved"
        )
        self.assertFalse(success)
    
    def test_process_task_correct_role_succeeds(self):
        """Test: process_task() z poprawną rolą działa."""
        request_id = database.create_leave_request(
            employee_name="Process Test Correct Role",
            employee_position="Manager",
            leave_type="Training",
            leave_start_date="2025-07-01",
            leave_end_date="2025-07-10",
            leave_duration_days=10
        )
        
        success, msg = workflow.process_task(
            request_id=request_id,
            performed_by_role=database.Roles.HEAD_OU,
            decision="Approved",
            update_fields={'head_ou_decision': 'Approved'}
        )
        self.assertTrue(success)
        
        # Weryfikacja zmiany stanu
        req = database.get_leave_request(request_id)
        self.assertEqual(req['current_state'], database.WorkflowStates.PD_REVIEW)


# =============================================================================
# CLEANUP
# =============================================================================

def tearDownModule():
    """Sprzątanie po wszystkich testach."""
    # Usunięcie testowej bazy danych
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except:
            pass
    
    # Usunięcie plików WAL/SHM
    for suffix in ['-wal', '-shm']:
        wal_path = TEST_DB_PATH + suffix
        if os.path.exists(wal_path):
            try:
                os.remove(wal_path)
            except:
                pass


# =============================================================================
# URUCHOMIENIE TESTÓW
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("LEAVE REQUEST APPLICATION - UNIT TESTS")
    print("=" * 70)
    print()
    
    # Uruchomienie testów
    unittest.main(verbosity=2)
