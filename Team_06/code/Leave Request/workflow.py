# -*- coding: utf-8 -*-
"""
===============================================================================
LEAVE REQUEST APPLICATION - WORKFLOW ENGINE
===============================================================================
Silnik workflow dla aplikacji Leave Request (DPE/1-3).

Zawiera:
- Maszynę stanów dla przepływu procesu
- Logikę routingu dla nauczycieli akademickich vs nieakademickich
- Funkcje przejść między stanami

Autor: aideveloper
Wersja: 1.0
===============================================================================
"""

from typing import Dict, Optional, Tuple, Any
from database import (
    WorkflowStates, 
    Roles, 
    get_leave_request, 
    update_leave_request,
    add_workflow_history
)


# =============================================================================
# MAPOWANIE STANÓW NA OPISY
# =============================================================================

STATE_DESCRIPTIONS: Dict[str, str] = {
    WorkflowStates.SUBMITTED: "Wniosek złożony",
    WorkflowStates.HEAD_OU_REVIEW: "Weryfikacja przez Kierownika Jednostki",
    WorkflowStates.PD_REVIEW: "Weryfikacja przez Dział Personalny",
    WorkflowStates.PRK_REVIEW: "Weryfikacja przez Prorektora ds. Kształcenia",
    WorkflowStates.PRN_REVIEW: "Weryfikacja przez Prorektora ds. Naukowych",
    WorkflowStates.RECTOR_DECISION: "Decyzja Rektora",
    WorkflowStates.CHANCELLOR_DECISION: "Decyzja Kanclerza",
    WorkflowStates.NOTIFY_HEAD_OU: "Powiadomienie Kierownika Jednostki",
    WorkflowStates.REGISTER_HR: "Rejestracja w systemie HR",
    WorkflowStates.COMPLETED: "Zakończony",
    WorkflowStates.REJECTED: "Odrzucony"
}


# =============================================================================
# MAPOWANIE STANÓW NA ROLE WYKONAWCZE
# =============================================================================

STATE_TO_ROLE: Dict[str, str] = {
    WorkflowStates.HEAD_OU_REVIEW: Roles.HEAD_OU,
    WorkflowStates.PD_REVIEW: Roles.PD,
    WorkflowStates.PRK_REVIEW: Roles.PRK,
    WorkflowStates.PRN_REVIEW: Roles.PRN,
    WorkflowStates.RECTOR_DECISION: Roles.RECTOR,
    WorkflowStates.CHANCELLOR_DECISION: Roles.CHANCELLOR,
    WorkflowStates.NOTIFY_HEAD_OU: Roles.PD,
    WorkflowStates.REGISTER_HR: Roles.PD,
}


# =============================================================================
# NAZWY ZADAŃ DLA KAŻDEGO STANU
# =============================================================================

STATE_TASK_NAMES: Dict[str, str] = {
    WorkflowStates.HEAD_OU_REVIEW: "Review and approve leave request",
    WorkflowStates.PD_REVIEW: "Review leave request (check entitlement)",
    WorkflowStates.PRK_REVIEW: "Review application (PRK) and forward to PRN",
    WorkflowStates.PRN_REVIEW: "Review application (PRN) and forward to Rector",
    WorkflowStates.RECTOR_DECISION: "Make decision (RKR) and return to PD",
    WorkflowStates.CHANCELLOR_DECISION: "Make decision (KAN) and return to PD",
    WorkflowStates.NOTIFY_HEAD_OU: "Inform Head of O.U. about the decision",
    WorkflowStates.REGISTER_HR: "Register leave in HR system",
}


# =============================================================================
# FUNKCJE POMOCNICZE
# =============================================================================

def get_state_description(state: str) -> str:
    """
    Zwraca czytelny opis stanu workflow.
    
    Args:
        state: Identyfikator stanu.
        
    Returns:
        str: Opis stanu w języku polskim.
    """
    return STATE_DESCRIPTIONS.get(state, state)


def get_task_name(state: str) -> str:
    """
    Zwraca nazwę zadania dla danego stanu.
    
    Args:
        state: Identyfikator stanu.
        
    Returns:
        str: Nazwa zadania (po angielsku, zgodnie z BPMN).
    """
    return STATE_TASK_NAMES.get(state, "Unknown Task")


def get_assignee_role(state: str) -> Optional[str]:
    """
    Zwraca rolę odpowiedzialną za dany stan workflow.
    
    Args:
        state: Identyfikator stanu.
        
    Returns:
        str lub None: Rola wykonawcza lub None dla stanów końcowych.
    """
    return STATE_TO_ROLE.get(state)


def can_process_task(current_role: str, request_state: str) -> bool:
    """
    Sprawdza czy użytkownik z daną rolą może przetworzyć zadanie.
    
    Args:
        current_role: Aktualna rola użytkownika.
        request_state: Stan wniosku.
        
    Returns:
        bool: True jeśli rola może przetworzyć zadanie.
    """
    required_role = get_assignee_role(request_state)
    return required_role == current_role


# =============================================================================
# LOGIKA PRZEJŚĆ STANÓW
# =============================================================================

def get_next_state(
    current_state: str, 
    decision: str,
    is_academic_teacher: bool = True
) -> Tuple[str, str]:
    """
    Określa następny stan workflow na podstawie aktualnego stanu i decyzji.
    
    Implementuje logikę routingu zgodną z diagramem BPMN:
    - Dla nauczycieli akademickich: PRK -> PRN -> Rector
    - Dla pracowników nieakademickich: Chancellor
    
    Args:
        current_state: Aktualny stan workflow.
        decision: Podjęta decyzja (np. 'Approved', 'Rejected').
        is_academic_teacher: Czy pracownik jest nauczycielem akademickim.
        
    Returns:
        Tuple[str, str]: (następny_stan, rola_wykonawcza)
    """
    
    # -------------------------------------------------------------------------
    # HEAD OF O.U. REVIEW
    # -------------------------------------------------------------------------
    if current_state == WorkflowStates.HEAD_OU_REVIEW:
        if decision == "Rejected":
            return WorkflowStates.REJECTED, None
        else:
            return WorkflowStates.PD_REVIEW, Roles.PD
    
    # -------------------------------------------------------------------------
    # PERSONNEL DEPARTMENT REVIEW
    # -------------------------------------------------------------------------
    elif current_state == WorkflowStates.PD_REVIEW:
        # Bramka: "Concerns an academic teacher?"
        if is_academic_teacher:
            # Ścieżka dla nauczycieli akademickich: do PRK
            return WorkflowStates.PRK_REVIEW, Roles.PRK
        else:
            # Ścieżka dla pracowników nieakademickich: do Chancellor
            return WorkflowStates.CHANCELLOR_DECISION, Roles.CHANCELLOR
    
    # -------------------------------------------------------------------------
    # PRK REVIEW (Vice-Rector for Education) - tylko dla academic teachers
    # -------------------------------------------------------------------------
    elif current_state == WorkflowStates.PRK_REVIEW:
        if decision == "Rejected":
            return WorkflowStates.REJECTED, None
        else:
            return WorkflowStates.PRN_REVIEW, Roles.PRN
    
    # -------------------------------------------------------------------------
    # PRN REVIEW (Vice-Rector for Scientific Affairs) - tylko dla academic teachers
    # -------------------------------------------------------------------------
    elif current_state == WorkflowStates.PRN_REVIEW:
        if decision == "Rejected":
            return WorkflowStates.REJECTED, None
        else:
            return WorkflowStates.RECTOR_DECISION, Roles.RECTOR
    
    # -------------------------------------------------------------------------
    # RECTOR DECISION (dla academic teachers)
    # -------------------------------------------------------------------------
    elif current_state == WorkflowStates.RECTOR_DECISION:
        # Niezależnie od decyzji, przechodzi do powiadomienia
        # Final decision jest zapisywana osobno
        return WorkflowStates.NOTIFY_HEAD_OU, Roles.PD
    
    # -------------------------------------------------------------------------
    # CHANCELLOR DECISION (dla non-academic employees)
    # -------------------------------------------------------------------------
    elif current_state == WorkflowStates.CHANCELLOR_DECISION:
        # Niezależnie od decyzji, przechodzi do powiadomienia
        return WorkflowStates.NOTIFY_HEAD_OU, Roles.PD
    
    # -------------------------------------------------------------------------
    # NOTIFY HEAD OF O.U.
    # -------------------------------------------------------------------------
    elif current_state == WorkflowStates.NOTIFY_HEAD_OU:
        return WorkflowStates.REGISTER_HR, Roles.PD
    
    # -------------------------------------------------------------------------
    # REGISTER IN HR SYSTEM
    # -------------------------------------------------------------------------
    elif current_state == WorkflowStates.REGISTER_HR:
        return WorkflowStates.COMPLETED, None
    
    # -------------------------------------------------------------------------
    # STAN DOMYŚLNY
    # -------------------------------------------------------------------------
    else:
        return current_state, None


# =============================================================================
# GŁÓWNA FUNKCJA PRZETWARZANIA ZADANIA
# =============================================================================

def process_task(
    request_id: int,
    performed_by_role: str,
    decision: str,
    notes: Optional[str] = None,
    update_fields: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str]:
    """
    Przetwarza zadanie workflow - główna funkcja przejścia stanu.
    
    Args:
        request_id: ID wniosku do przetworzenia.
        performed_by_role: Rola użytkownika wykonującego zadanie.
        decision: Podjęta decyzja.
        notes: Opcjonalne notatki.
        update_fields: Dodatkowe pola do aktualizacji w wniosku.
        
    Returns:
        Tuple[bool, str]: (sukces, komunikat)
    """
    # Pobierz aktualny wniosek
    request = get_leave_request(request_id)
    if not request:
        return False, "Wniosek nie został znaleziony."
    
    current_state = request['current_state']
    
    # Sprawdź uprawnienia
    if not can_process_task(performed_by_role, current_state):
        expected_role = get_assignee_role(current_state)
        return False, f"Brak uprawnień. To zadanie wymaga roli: {expected_role}"
    
    # Sprawdź czy wniosek nie jest już zakończony
    if current_state in [WorkflowStates.COMPLETED, WorkflowStates.REJECTED]:
        return False, "Ten wniosek został już zakończony."
    
    # Pobierz is_academic_teacher (może być zaktualizowane w update_fields)
    is_academic = request['is_academic_teacher']
    if update_fields and 'is_academic_teacher' in update_fields:
        is_academic = update_fields['is_academic_teacher']
    
    # Określ następny stan
    next_state, next_role = get_next_state(current_state, decision, is_academic)
    
    # Przygotuj aktualizacje
    all_updates = {
        'current_state': next_state,
        'current_assignee_role': next_role
    }
    
    # Dodaj dodatkowe pola do aktualizacji
    if update_fields:
        all_updates.update(update_fields)
    
    # Wykonaj aktualizację
    success = update_leave_request(request_id, all_updates)
    
    if success:
        # Dodaj wpis do historii
        task_name = get_task_name(current_state)
        add_workflow_history(
            request_id=request_id,
            action=task_name,
            from_state=current_state,
            to_state=next_state,
            performed_by_role=performed_by_role,
            decision=decision,
            notes=notes
        )
        
        next_state_desc = get_state_description(next_state)
        return True, f"Zadanie wykonane pomyślnie. Nowy status: {next_state_desc}"
    else:
        return False, "Wystąpił błąd podczas aktualizacji wniosku."


# =============================================================================
# FUNKCJE POMOCNICZE DLA UI
# =============================================================================

def get_available_decisions(state: str) -> list:
    """
    Zwraca listę dostępnych decyzji dla danego stanu.
    
    Args:
        state: Aktualny stan workflow.
        
    Returns:
        list: Lista dostępnych decyzji.
    """
    if state == WorkflowStates.HEAD_OU_REVIEW:
        return ["Approved", "Rejected"]
    elif state == WorkflowStates.PD_REVIEW:
        return ["Entitlement Confirmed", "Entitlement Exceeded"]
    elif state in [WorkflowStates.PRK_REVIEW, WorkflowStates.PRN_REVIEW]:
        return ["Approved", "Rejected"]
    elif state in [WorkflowStates.RECTOR_DECISION, WorkflowStates.CHANCELLOR_DECISION]:
        return ["Approved", "Rejected"]
    elif state in [WorkflowStates.NOTIFY_HEAD_OU, WorkflowStates.REGISTER_HR]:
        return ["Completed"]
    else:
        return []


def get_required_fields(state: str) -> list:
    """
    Zwraca listę wymaganych pól do wypełnienia dla danego stanu.
    
    Args:
        state: Aktualny stan workflow.
        
    Returns:
        list: Lista nazw pól.
    """
    if state == WorkflowStates.HEAD_OU_REVIEW:
        return ['head_ou_decision']
    elif state == WorkflowStates.PD_REVIEW:
        return ['pd_review_status', 'is_academic_teacher']
    elif state == WorkflowStates.PRK_REVIEW:
        return ['prk_review_status']
    elif state == WorkflowStates.PRN_REVIEW:
        return ['prn_review_status']
    elif state in [WorkflowStates.RECTOR_DECISION, WorkflowStates.CHANCELLOR_DECISION]:
        return ['final_decision', 'final_decision_maker']
    else:
        return []
