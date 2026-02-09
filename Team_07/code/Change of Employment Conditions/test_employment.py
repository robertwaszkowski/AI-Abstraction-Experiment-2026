# -*- coding: utf-8 -*-
"""
================================================================================
TEST_EMPLOYMENT.PY - Unit Tests for Change of Employment Conditions Application
================================================================================
Testy jednostkowe weryfikujące poprawność działania aplikacji.

Uruchomienie: python test_employment.py
================================================================================
"""

import unittest
import os
import sqlite3
import sys
from datetime import datetime, timedelta

# Zmień katalog na lokalizację tego pliku
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Usuń istniejącą bazę testową
TEST_DB = "test_employment.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# Nadpisz ścieżkę bazy danych przed importem modułów
import database
database.DB_FILE = TEST_DB

# Import modułów aplikacji
from database import init_db, create_application, get_application, update_application, get_tasks_for_role, get_all_applications
from process import (
    ProcessEngine, 
    ROLE_HEAD_OU, ROLE_PD, ROLE_KWE, ROLE_PRK, ROLE_PRN, ROLE_RECTOR, ROLE_CHANCELLOR,
    TASK_REVIEW_HEAD_OU, TASK_REVIEW_PD, TASK_REVIEW_KWE, TASK_REVIEW_PRK, TASK_REVIEW_PRN,
    TASK_DECISION_RKR, TASK_DECISION_KAN, TASK_IMPLEMENT_PREPARE, TASK_HANDOVER_ARCHIVE, TASK_COMPLETED
)


class TestDatabaseSetup(unittest.TestCase):
    """Testy inicjalizacji bazy danych"""
    
    def test_01_database_initializes(self):
        """Test: Baza danych inicjalizuje się poprawnie"""
        init_db()
        self.assertTrue(os.path.exists(TEST_DB), "Plik bazy danych nie istnieje!")
        print(f"   ✓ Baza danych utworzona: {TEST_DB}")
    
    def test_02_tables_exist(self):
        """Test: Tabela applications istnieje"""
        conn = sqlite3.connect(TEST_DB)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
        result = c.fetchone()
        conn.close()
        
        self.assertIsNotNone(result, "Tabela applications nie istnieje!")
        print(f"   ✓ Tabela applications istnieje")


class TestProcessEngine(unittest.TestCase):
    """Testy silnika procesów"""
    
    @classmethod
    def setUpClass(cls):
        """Inicjalizacja silnika"""
        cls.engine = ProcessEngine()
    
    def test_01_start_process(self):
        """Test: Tworzenie nowego wniosku"""
        app_id = self.engine.start_process(
            employee_name="Jan Kowalski",
            proposed_conditions="Promotion to Senior",
            change_justification="Outstanding performance",
            change_effective_date=datetime.today() + timedelta(days=30)
        )
        
        self.assertIsNotNone(app_id, "Nie udało się utworzyć wniosku!")
        self.assertGreater(app_id, 0, "ID wniosku powinno być > 0")
        print(f"   ✓ Utworzono wniosek ID: {app_id}")
        
        TestProcessEngine.app_id = app_id
    
    def test_02_initial_state_correct(self):
        """Test: Nowy wniosek ma poprawny stan początkowy"""
        app = self.engine.get_application(self.app_id)
        
        self.assertIsNotNone(app, "Nie znaleziono wniosku!")
        self.assertEqual(app['current_task'], TASK_REVIEW_HEAD_OU,
                        f"Zły task początkowy: {app['current_task']}")
        self.assertEqual(app['assignee_role'], ROLE_HEAD_OU,
                        f"Zła przypisana rola: {app['assignee_role']}")
        self.assertEqual(app['process_status'], 'In Progress')
        print(f"   ✓ Stan początkowy: {app['current_task']}")
        print(f"   ✓ Przypisana rola: {app['assignee_role']}")


class TestAcademicWorkflow(unittest.TestCase):
    """Testy pełnego przepływu dla nauczyciela akademickiego"""
    
    @classmethod
    def setUpClass(cls):
        """Utwórz wniosek do testów"""
        cls.engine = ProcessEngine()
        cls.app_id = cls.engine.start_process(
            employee_name="Anna Akademicka",
            proposed_conditions="Promotion to Professor",
            change_justification="Research excellence",
            change_effective_date=datetime.today() + timedelta(days=30)
        )
    
    def test_01_head_ou_approves(self):
        """Test: Head of O.U. zatwierdza wniosek"""
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_REVIEW_HEAD_OU)
        
        success, msg = self.engine.complete_task(
            self.app_id, 
            TASK_REVIEW_HEAD_OU, 
            {'head_of_ou_review_status': 'Approved'}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_REVIEW_PD)
        self.assertEqual(app['assignee_role'], ROLE_PD)
        print(f"   ✓ Przejście do: {app['current_task']}")
    
    def test_02_pd_reviews_academic(self):
        """Test: PD weryfikuje i ustawia typ pracownika"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_REVIEW_PD,
            {'pd_review_status': 'Confirmed', 'is_academic_teacher': True}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_REVIEW_KWE)
        self.assertEqual(app['assignee_role'], ROLE_KWE)
        self.assertEqual(app['is_academic_teacher'], 1)  # True as integer
        print(f"   ✓ Przejście do: {app['current_task']}")
        print(f"   ✓ is_academic_teacher: {app['is_academic_teacher']}")
    
    def test_03_kwe_reviews(self):
        """Test: KWE wydaje opinię finansową"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_REVIEW_KWE,
            {'kwe_financial_opinion': 'Funds Available'}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        # Dla akademika -> PRK
        self.assertEqual(app['current_task'], TASK_REVIEW_PRK)
        self.assertEqual(app['assignee_role'], ROLE_PRK)
        print(f"   ✓ Przejście do: {app['current_task']} (ścieżka akademicka)")
    
    def test_04_prk_reviews(self):
        """Test: PRK opiniuje"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_REVIEW_PRK,
            {'prk_opinion': 'Approved'}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_REVIEW_PRN)
        self.assertEqual(app['assignee_role'], ROLE_PRN)
        print(f"   ✓ Przejście do: {app['current_task']}")
    
    def test_05_prn_reviews(self):
        """Test: PRN opiniuje"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_REVIEW_PRN,
            {'prn_opinion': 'Approved'}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_DECISION_RKR)
        self.assertEqual(app['assignee_role'], ROLE_RECTOR)
        print(f"   ✓ Przejście do: {app['current_task']}")
    
    def test_06_rector_decides(self):
        """Test: Rektor podejmuje decyzję"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_DECISION_RKR,
            {'final_decision': 'Approved'}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_IMPLEMENT_PREPARE)
        self.assertEqual(app['assignee_role'], ROLE_PD)
        print(f"   ✓ Przejście do: {app['current_task']}")
    
    def test_07_pd_implements(self):
        """Test: PD implementuje zmiany"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_IMPLEMENT_PREPARE,
            {}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_HANDOVER_ARCHIVE)
        print(f"   ✓ Przejście do: {app['current_task']}")
    
    def test_08_pd_archives(self):
        """Test: PD archiwizuje dokumenty"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_HANDOVER_ARCHIVE,
            {}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_COMPLETED)
        self.assertEqual(app['process_status'], 'Completed')
        self.assertIsNone(app['assignee_role'])
        print(f"   ✓ Proces zakończony: {app['process_status']}")


class TestNonAcademicWorkflow(unittest.TestCase):
    """Testy przepływu dla pracownika nieakademickiego"""
    
    @classmethod
    def setUpClass(cls):
        """Utwórz wniosek do testów"""
        cls.engine = ProcessEngine()
        cls.app_id = cls.engine.start_process(
            employee_name="Bob Admin",
            proposed_conditions="Change to full-time",
            change_justification="Increased workload",
            change_effective_date=datetime.today() + timedelta(days=14)
        )
    
    def test_01_workflow_to_kwe(self):
        """Przygotowanie: przeprowadź wniosek do KWE"""
        self.engine.complete_task(self.app_id, TASK_REVIEW_HEAD_OU, 
                                  {'head_of_ou_review_status': 'Approved'})
        self.engine.complete_task(self.app_id, TASK_REVIEW_PD,
                                  {'pd_review_status': 'Confirmed', 'is_academic_teacher': False})
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_REVIEW_KWE)
        print(f"   ✓ Wniosek w stanie: {app['current_task']}")
    
    def test_02_kwe_routes_to_chancellor(self):
        """Test: KWE przekierowuje do Kanclerza (nieakademik)"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_REVIEW_KWE,
            {'kwe_financial_opinion': 'Funds Available'}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        # Dla nieakademika -> Chancellor
        self.assertEqual(app['current_task'], TASK_DECISION_KAN)
        self.assertEqual(app['assignee_role'], ROLE_CHANCELLOR)
        print(f"   ✓ Przejście do: {app['current_task']} (ścieżka nieakademicka)")
    
    def test_03_chancellor_decides(self):
        """Test: Kanclerz podejmuje decyzję"""
        success, msg = self.engine.complete_task(
            self.app_id,
            TASK_DECISION_KAN,
            {'final_decision': 'Approved'}
        )
        
        self.assertTrue(success, f"Błąd: {msg}")
        
        app = self.engine.get_application(self.app_id)
        self.assertEqual(app['current_task'], TASK_IMPLEMENT_PREPARE)
        print(f"   ✓ Przejście do: {app['current_task']}")


class TestTaskAssignment(unittest.TestCase):
    """Testy przypisywania zadań do ról"""
    
    @classmethod
    def setUpClass(cls):
        """Utwórz wnioski testowe"""
        cls.engine = ProcessEngine()
        # Utwórz wniosek przypisany do Head O.U.
        cls.app_id = cls.engine.start_process(
            employee_name="Task Test",
            proposed_conditions="Test",
            change_justification="Test",
            change_effective_date=datetime.today()
        )
    
    def test_01_get_tasks_for_head_ou(self):
        """Test: Pobieranie zadań dla Head of O.U."""
        tasks = self.engine.get_tasks(ROLE_HEAD_OU)
        
        self.assertIsInstance(tasks, list, "Powinien zwrócić listę")
        app_ids = [t['id'] for t in tasks]
        self.assertIn(self.app_id, app_ids, "Wniosek powinien być widoczny")
        print(f"   ✓ Znaleziono {len(tasks)} zadań dla Head O.U.")
    
    def test_02_get_tasks_for_pd_empty(self):
        """Test: PD nie ma zadań dla nowego wniosku"""
        tasks = self.engine.get_tasks(ROLE_PD)
        app_ids = [t['id'] for t in tasks]
        
        # Nasz nowy wniosek nie powinien być przypisany do PD
        self.assertNotIn(self.app_id, app_ids, 
                        "Nowy wniosek nie powinien być widoczny dla PD")
        print(f"   ✓ PD nie widzi nowego wniosku (poprawnie)")


class TestDataIntegrity(unittest.TestCase):
    """Testy integralności danych"""
    
    def test_01_all_applications_returns_dataframe(self):
        """Test: get_all_applications zwraca DataFrame"""
        df = get_all_applications()
        
        import pandas as pd
        self.assertIsInstance(df, pd.DataFrame, "Powinien zwrócić DataFrame")
        print(f"   ✓ Znaleziono {len(df)} wniosków w bazie")
    
    def test_02_application_has_required_fields(self):
        """Test: Wniosek zawiera wymagane pola"""
        engine = ProcessEngine()
        app_id = engine.start_process(
            employee_name="Field Test",
            proposed_conditions="Test",
            change_justification="Test",
            change_effective_date=datetime.today()
        )
        
        app = engine.get_application(app_id)
        
        required_fields = [
            'id', 'employee_name', 'proposed_conditions', 'change_justification',
            'current_task', 'assignee_role', 'process_status'
        ]
        
        for field in required_fields:
            self.assertIn(field, app, f"Brak pola: {field}")
        
        print(f"   ✓ Wszystkie {len(required_fields)} wymaganych pól jest obecnych")


class TestPotentialBugs(unittest.TestCase):
    """Testy potencjalnych błędów i edge cases"""
    
    @classmethod
    def setUpClass(cls):
        cls.engine = ProcessEngine()
    
    def test_01_get_nonexistent_application(self):
        """Test: Pobieranie nieistniejącego wniosku"""
        app = self.engine.get_application(99999)
        self.assertIsNone(app, "Powinien zwrócić None dla nieistniejącego wniosku")
        print(f"   ✓ Poprawna obsługa nieistniejącego wniosku")
    
    def test_02_complete_task_nonexistent(self):
        """Test: Wykonanie zadania dla nieistniejącego wniosku"""
        success, msg = self.engine.complete_task(99999, TASK_REVIEW_HEAD_OU, {})
        self.assertFalse(success, "Powinno się nie udać")
        print(f"   ✓ Poprawna obsługa błędu: {msg}")
    
    def test_03_rejection_handling(self):
        """Test: Obsługa odrzucenia przez Head O.U."""
        app_id = self.engine.start_process(
            employee_name="Reject Test",
            proposed_conditions="Test",
            change_justification="Test",
            change_effective_date=datetime.today()
        )
        
        # Odrzucenie przez Head O.U.
        success, msg = self.engine.complete_task(
            app_id, 
            TASK_REVIEW_HEAD_OU, 
            {'head_of_ou_review_status': 'Rejected'}
        )
        
        # POTENCJALNY BUG: Sprawdź co się dzieje przy odrzuceniu
        app = self.engine.get_application(app_id)
        
        # Jeśli odrzucenie nie jest obsługiwane, wniosek zostaje w tym samym stanie
        # To może być błąd w logice!
        if app['current_task'] == TASK_REVIEW_HEAD_OU:
            print(f"   ⚠️ UWAGA: Odrzucenie nie zmienia stanu wniosku!")
            print(f"      Obecny stan: {app['current_task']}")
            print(f"      To może być błąd - brak obsługi ścieżki odrzucenia")
        else:
            print(f"   ✓ Odrzucenie obsłużone: {app['current_task']}")


# ============================================================================
# URUCHOMIENIE TESTÓW
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" TESTY JEDNOSTKOWE - CHANGE OF EMPLOYMENT CONDITIONS")
    print("="*70 + "\n")
    
    # Uruchom testy
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Dodaj klasy testowe w odpowiedniej kolejności
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseSetup))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAcademicWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestNonAcademicWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskAssignment))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestPotentialBugs))
    
    # Uruchom z verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Podsumowanie
    print("\n" + "="*70)
    print(" PODSUMOWANIE")
    print("="*70)
    print(f" Testy wykonane: {result.testsRun}")
    print(f" Sukces: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f" Błędy: {len(result.failures)}")
    print(f" Wyjątki: {len(result.errors)}")
    
    if result.failures:
        print("\n NIEUDANE TESTY:")
        for test, traceback in result.failures:
            print(f"   ✗ {test}")
            # Print last line of traceback
            lines = traceback.strip().split('\n')
            print(f"     {lines[-1] if lines else traceback}")
    
    if result.errors:
        print("\n BŁĘDY:")
        for test, traceback in result.errors:
            print(f"   ✗ {test}")
            lines = traceback.strip().split('\n')
            print(f"     {lines[-1] if lines else traceback}")
    
    print("="*70)
    
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        print(f"\n Usunięto testową bazę danych: {TEST_DB}")
    
    sys.exit(0 if result.wasSuccessful() else 1)
