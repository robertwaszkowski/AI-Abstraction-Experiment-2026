# -*- coding: utf-8 -*-
"""
================================================================================
TEST_DECORATIONS.PY - Unit Tests for Decorations and Medals Application
================================================================================
Testy jednostkowe weryfikujące poprawność działania aplikacji.

Uruchomienie: python test_decorations.py
================================================================================
"""

import unittest
import os
import sqlite3
import sys
from datetime import datetime

# Zmień katalog na lokalizację tego pliku
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Usuń istniejącą bazę testową
TEST_DB = "test_decorations.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# Nadpisz ścieżkę bazy danych przed importem modułów
import database
database.DATABASE_PATH = TEST_DB

# Import modułów aplikacji
from database import (
    initialize_database, get_all_users, get_user_by_id, get_users_by_role,
    create_application, get_application_by_id, get_applications_by_role,
    get_all_applications, get_statistics, get_application_history,
    ProcessState, UserRole, RKRDecision
)
from workflow import (
    get_task_name, can_user_process_application, get_available_actions,
    process_pd_present_to_prk, process_prk_review, process_pd_present_to_rector,
    process_rector_decision, process_pd_forward_to_mpd, process_mpd_external_handling,
    process_pd_receive_decision, process_pd_register
)


class TestDatabaseSetup(unittest.TestCase):
    """Testy inicjalizacji bazy danych"""
    
    @classmethod
    def setUpClass(cls):
        """Inicjalizacja bazy przed wszystkimi testami"""
        initialize_database()
    
    def test_01_database_file_exists(self):
        """Test: Plik bazy danych został utworzony"""
        self.assertTrue(os.path.exists(TEST_DB), "Plik bazy danych nie istnieje!")
    
    def test_02_users_table_has_data(self):
        """Test: Tabela użytkowników zawiera testowych użytkowników"""
        users = get_all_users()
        self.assertGreater(len(users), 0, "Brak użytkowników w bazie!")
        print(f"   ✓ Znaleziono {len(users)} użytkowników")
    
    def test_03_required_roles_exist(self):
        """Test: Wszystkie wymagane role są obecne"""
        users = get_all_users()
        roles = set(u['role'] for u in users)
        
        required_roles = [
            UserRole.HEAD_OF_OU,
            UserRole.PD,
            UserRole.PRK_CHANCELLOR,
            UserRole.RKR,
            UserRole.MPD
        ]
        
        for role in required_roles:
            self.assertIn(role, roles, f"Brak roli: {role}")
        print(f"   ✓ Wszystkie {len(required_roles)} wymaganych ról są obecne")
    
    def test_04_head_of_ou_user_exists(self):
        """Test: Użytkownik Head of O.U. istnieje (wymagany do składania wniosków)"""
        users = get_users_by_role(UserRole.HEAD_OF_OU)
        self.assertGreater(len(users), 0, "Brak użytkownika Head of O.U.!")
        print(f"   ✓ Head of O.U.: {users[0]['display_name']}")


class TestApplicationCreation(unittest.TestCase):
    """Testy tworzenia wniosków"""
    
    @classmethod
    def setUpClass(cls):
        """Pobierz użytkowników do testów"""
        cls.head_user = get_users_by_role(UserRole.HEAD_OF_OU)[0]
        cls.pd_user = get_users_by_role(UserRole.PD)[0]
    
    def test_01_create_application_success(self):
        """Test: Tworzenie wniosku działa poprawnie"""
        app_id = create_application(
            employee_name="Jan Kowalski",
            organizational_unit="IT Department",
            decoration_type="Gold Medal for Long Service",
            application_justification="Outstanding performance",
            created_by=self.head_user['id']
        )
        
        self.assertIsNotNone(app_id, "Nie udało się utworzyć wniosku!")
        self.assertGreater(app_id, 0, "ID wniosku powinno być > 0")
        print(f"   ✓ Utworzono wniosek ID: {app_id}")
        
        # Zapisz ID do użycia w kolejnych testach
        TestApplicationCreation.created_app_id = app_id
    
    def test_02_application_initial_state_correct(self):
        """Test: Nowy wniosek ma poprawny stan początkowy"""
        app = get_application_by_id(self.created_app_id)
        
        self.assertIsNotNone(app, "Nie znaleziono wniosku!")
        self.assertEqual(app['current_state'], ProcessState.PENDING_PRK_REVIEW,
                        f"Zły stan początkowy: {app['current_state']}")
        self.assertEqual(app['assigned_role'], UserRole.PD,
                        f"Zła przypisana rola: {app['assigned_role']}")
        print(f"   ✓ Stan początkowy: {app['current_state']}")
        print(f"   ✓ Przypisana rola: {app['assigned_role']}")
    
    def test_03_application_appears_in_pd_tasks(self):
        """Test: Nowy wniosek pojawia się w zadaniach PD"""
        tasks = get_applications_by_role(UserRole.PD)
        app_ids = [t['id'] for t in tasks]
        
        self.assertIn(self.created_app_id, app_ids, 
                     "Wniosek nie pojawił się w zadaniach PD!")
        print(f"   ✓ Wniosek widoczny w zadaniach PD")
    
    def test_04_application_history_created(self):
        """Test: Historia wniosku została utworzona"""
        history = get_application_history(self.created_app_id)
        
        self.assertGreater(len(history), 0, "Brak historii wniosku!")
        self.assertEqual(history[0]['action'], "Application Submitted",
                        f"Zła akcja w historii: {history[0]['action']}")
        print(f"   ✓ Historia: {len(history)} wpis(ów)")


class TestWorkflowTransitions(unittest.TestCase):
    """Testy przejść między stanami workflow"""
    
    @classmethod
    def setUpClass(cls):
        """Utwórz wniosek do testów workflow"""
        head_user = get_users_by_role(UserRole.HEAD_OF_OU)[0]
        cls.app_id = create_application(
            employee_name="Anna Testowa",
            organizational_unit="Finance",
            decoration_type="Silver Medal",
            application_justification="Test workflow",
            created_by=head_user['id']
        )
        
        # Pobierz użytkowników
        cls.pd_user = get_users_by_role(UserRole.PD)[0]
        cls.prk_user = get_users_by_role(UserRole.PRK_CHANCELLOR)[0]
        cls.rector_user = get_users_by_role(UserRole.RKR)[0]
        cls.mpd_user = get_users_by_role(UserRole.MPD)[0]
    
    def test_01_pd_present_to_prk(self):
        """Test: PD przekazuje wniosek do PRK/Chancellor"""
        result = process_pd_present_to_prk(
            application_id=self.app_id,
            user_id=self.pd_user['id'],
            comments="Test comment"
        )
        
        self.assertTrue(result, "Nie udało się przetworzyć zadania PD!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.UNDER_PRK_REVIEW)
        self.assertEqual(app['assigned_role'], UserRole.PRK_CHANCELLOR)
        print(f"   ✓ Stan: {app['current_state']}")
    
    def test_02_prk_review(self):
        """Test: PRK/Chancellor opiniuje wniosek"""
        result = process_prk_review(
            application_id=self.app_id,
            user_id=self.prk_user['id'],
            reviewer_opinion="Strongly support",
            comments="Excellent candidate"
        )
        
        self.assertTrue(result, "Nie udało się przetworzyć opinii PRK!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.PENDING_RECTOR_PRESENTATION)
        self.assertEqual(app['reviewer_opinion'], "Strongly support")
        print(f"   ✓ Stan: {app['current_state']}")
        print(f"   ✓ Opinia: {app['reviewer_opinion']}")
    
    def test_03_pd_present_to_rector(self):
        """Test: PD prezentuje wniosek Rektorowi"""
        result = process_pd_present_to_rector(
            application_id=self.app_id,
            user_id=self.pd_user['id']
        )
        
        self.assertTrue(result, "Nie udało się zaprezentować Rektorowi!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.PENDING_RECTOR_DECISION)
        self.assertEqual(app['assigned_role'], UserRole.RKR)
        print(f"   ✓ Stan: {app['current_state']}")
    
    def test_04_rector_accepts(self):
        """Test: Rektor akceptuje wniosek"""
        result = process_rector_decision(
            application_id=self.app_id,
            user_id=self.rector_user['id'],
            rkr_decision=RKRDecision.ACCEPTED
        )
        
        self.assertTrue(result, "Nie udało się przetworzyć decyzji Rektora!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.ACCEPTED_PENDING_MPD)
        self.assertEqual(app['rkr_decision'], RKRDecision.ACCEPTED)
        print(f"   ✓ Stan: {app['current_state']}")
        print(f"   ✓ Decyzja: {app['rkr_decision']}")
    
    def test_05_pd_forward_to_mpd(self):
        """Test: PD przekazuje do MPD"""
        result = process_pd_forward_to_mpd(
            application_id=self.app_id,
            user_id=self.pd_user['id']
        )
        
        self.assertTrue(result, "Nie udało się przekazać do MPD!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.MPD_EXTERNAL_HANDLING)
        self.assertEqual(app['assigned_role'], UserRole.MPD)
        print(f"   ✓ Stan: {app['current_state']}")
    
    def test_06_mpd_external(self):
        """Test: MPD obsługuje zewnętrznie"""
        result = process_mpd_external_handling(
            application_id=self.app_id,
            user_id=self.mpd_user['id']
        )
        
        self.assertTrue(result, "Nie udało się przetworzyć MPD!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.PENDING_DECISION_RECEIPT)
        print(f"   ✓ Stan: {app['current_state']}")
    
    def test_07_pd_receive_decision(self):
        """Test: PD otrzymuje decyzję"""
        result = process_pd_receive_decision(
            application_id=self.app_id,
            user_id=self.pd_user['id']
        )
        
        self.assertTrue(result, "Nie udało się przetworzyć otrzymania decyzji!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.PENDING_REGISTRATION)
        print(f"   ✓ Stan: {app['current_state']}")
    
    def test_08_pd_register(self):
        """Test: PD rejestruje odznaczenie"""
        result = process_pd_register(
            application_id=self.app_id,
            user_id=self.pd_user['id'],
            award_grant_date="2026-01-07"
        )
        
        self.assertTrue(result, "Nie udało się zarejestrować!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.COMPLETED)
        self.assertEqual(app['process_outcome'], "Completed")
        print(f"   ✓ Stan końcowy: {app['current_state']}")
        print(f"   ✓ Wynik: {app['process_outcome']}")


class TestRejectionWorkflow(unittest.TestCase):
    """Testy przepływu odrzucenia wniosku"""
    
    @classmethod
    def setUpClass(cls):
        """Utwórz wniosek do testów odrzucenia"""
        head_user = get_users_by_role(UserRole.HEAD_OF_OU)[0]
        cls.app_id = create_application(
            employee_name="Test Reject",
            organizational_unit="HR",
            decoration_type="Bronze Medal",
            application_justification="Test rejection",
            created_by=head_user['id']
        )
        
        cls.pd_user = get_users_by_role(UserRole.PD)[0]
        cls.prk_user = get_users_by_role(UserRole.PRK_CHANCELLOR)[0]
        cls.rector_user = get_users_by_role(UserRole.RKR)[0]
    
    def test_01_workflow_to_rector(self):
        """Przygotowanie: przeprowadź wniosek do decyzji Rektora"""
        process_pd_present_to_prk(self.app_id, self.pd_user['id'])
        process_prk_review(self.app_id, self.prk_user['id'], "Not recommended")
        process_pd_present_to_rector(self.app_id, self.pd_user['id'])
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.PENDING_RECTOR_DECISION)
        print(f"   ✓ Wniosek gotowy do decyzji")
    
    def test_02_rector_rejects(self):
        """Test: Rektor odrzuca wniosek"""
        result = process_rector_decision(
            application_id=self.app_id,
            user_id=self.rector_user['id'],
            rkr_decision=RKRDecision.REJECTED
        )
        
        self.assertTrue(result, "Nie udało się odrzucić wniosku!")
        
        app = get_application_by_id(self.app_id)
        self.assertEqual(app['current_state'], ProcessState.REJECTED)
        self.assertEqual(app['rkr_decision'], RKRDecision.REJECTED)
        self.assertEqual(app['process_outcome'], "Rejected")
        print(f"   ✓ Stan: {app['current_state']}")
        print(f"   ✓ Wynik: {app['process_outcome']}")


class TestPermissions(unittest.TestCase):
    """Testy uprawnień i kontroli dostępu"""
    
    @classmethod
    def setUpClass(cls):
        """Utwórz wniosek do testów uprawnień"""
        head_user = get_users_by_role(UserRole.HEAD_OF_OU)[0]
        cls.app_id = create_application(
            employee_name="Permission Test",
            organizational_unit="Security",
            decoration_type="Medal",
            application_justification="Test permissions",
            created_by=head_user['id']
        )
        
        cls.pd_user = get_users_by_role(UserRole.PD)[0]
        cls.rector_user = get_users_by_role(UserRole.RKR)[0]
    
    def test_01_wrong_role_cannot_process(self):
        """Test: Niewłaściwa rola nie może przetworzyć wniosku"""
        app = get_application_by_id(self.app_id)
        
        # Wniosek jest przypisany do PD, więc Rektor nie powinien móc go przetworzyć
        can_process = can_user_process_application(UserRole.RKR, app)
        self.assertFalse(can_process, "Rektor nie powinien móc przetworzyć wniosku w tym stanie!")
        print(f"   ✓ Rektor nie może przetworzyć wniosku przypisanego do PD")
    
    def test_02_correct_role_can_process(self):
        """Test: Właściwa rola może przetworzyć wniosek"""
        app = get_application_by_id(self.app_id)
        
        can_process = can_user_process_application(UserRole.PD, app)
        self.assertTrue(can_process, "PD powinno móc przetworzyć wniosek!")
        print(f"   ✓ PD może przetworzyć wniosek")
    
    def test_03_wrong_state_transition_fails(self):
        """Test: Niepoprawne przejście stanu kończy się błędem"""
        # Próba wykonania akcji PRK review gdy wniosek jest w stanie PENDING_PRK_REVIEW
        # (powinien być w stanie UNDER_PRK_REVIEW)
        prk_user = get_users_by_role(UserRole.PRK_CHANCELLOR)[0]
        
        result = process_prk_review(
            application_id=self.app_id,
            user_id=prk_user['id'],
            reviewer_opinion="Test"
        )
        
        self.assertFalse(result, "Akcja PRK nie powinna się udać w złym stanie!")
        print(f"   ✓ Niepoprawne przejście stanu zostało zablokowane")


class TestStatistics(unittest.TestCase):
    """Testy statystyk"""
    
    def test_01_statistics_correct(self):
        """Test: Statystyki zwracają poprawne dane"""
        stats = get_statistics()
        
        self.assertIn('total', stats)
        self.assertIn('completed', stats)
        self.assertIn('rejected', stats)
        self.assertIn('in_progress', stats)
        
        # Sprawdź że suma się zgadza
        calculated_total = stats['completed'] + stats['rejected'] + stats['in_progress']
        self.assertEqual(stats['total'], calculated_total,
                        f"Suma statystyk nie zgadza się: {stats}")
        
        print(f"   ✓ Łącznie: {stats['total']}")
        print(f"   ✓ Zakończone: {stats['completed']}")
        print(f"   ✓ Odrzucone: {stats['rejected']}")
        print(f"   ✓ W trakcie: {stats['in_progress']}")


class TestDataIntegrity(unittest.TestCase):
    """Testy integralności danych"""
    
    def test_01_application_has_all_required_fields(self):
        """Test: Wniosek zawiera wszystkie wymagane pola"""
        apps = get_all_applications()
        
        if not apps:
            self.skipTest("Brak wniosków do testu")
        
        app = apps[0]
        required_fields = [
            'id', 'employee_name', 'organizational_unit', 'decoration_type',
            'application_justification', 'current_state', 'assigned_role',
            'created_by', 'created_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, app, f"Brak pola: {field}")
        
        print(f"   ✓ Wszystkie {len(required_fields)} wymaganych pól jest obecnych")
    
    def test_02_history_tracks_all_transitions(self):
        """Test: Historia śledzi wszystkie przejścia"""
        apps = get_all_applications()
        completed_apps = [a for a in apps if a['current_state'] == ProcessState.COMPLETED]
        
        if not completed_apps:
            self.skipTest("Brak zakończonych wniosków do testu")
        
        app = completed_apps[0]
        history = get_application_history(app['id'])
        
        # Pełny workflow powinien mieć co najmniej 9 wpisów historii
        expected_min_entries = 9
        self.assertGreaterEqual(len(history), expected_min_entries,
                               f"Historia powinna mieć >= {expected_min_entries} wpisów, ma {len(history)}")
        
        print(f"   ✓ Historia zawiera {len(history)} wpisów")


# ============================================================================
# URUCHOMIENIE TESTÓW
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" TESTY JEDNOSTKOWE - DECORATIONS AND MEDALS APPLICATION")
    print("="*70 + "\n")
    
    # Uruchom testy
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Dodaj klasy testowe w odpowiedniej kolejności
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseSetup))
    suite.addTests(loader.loadTestsFromTestCase(TestApplicationCreation))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowTransitions))
    suite.addTests(loader.loadTestsFromTestCase(TestRejectionWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestPermissions))
    suite.addTests(loader.loadTestsFromTestCase(TestStatistics))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIntegrity))
    
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
            print(f"     {traceback.split(chr(10))[-2]}")
    
    if result.errors:
        print("\n BŁĘDY:")
        for test, traceback in result.errors:
            print(f"   ✗ {test}")
            print(f"     {traceback.split(chr(10))[-2]}")
    
    print("="*70)
    
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        print(f"\n Usunięto testową bazę danych: {TEST_DB}")
    
    sys.exit(0 if result.wasSuccessful() else 1)
