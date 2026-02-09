"""
================================================================================
WORKFLOW.PY - Workflow State Machine for Decorations and Medals Application
================================================================================
This module implements the workflow logic based on the BPMN diagram.
It handles state transitions, role assignments, and task routing.

Author: aideveloper
Version: 1.0
================================================================================
"""

from typing import Dict, List, Tuple, Optional
from database import (
    ProcessState, UserRole, RKRDecision,
    get_application_by_id, update_application_state
)


# ============================================================================
# WORKFLOW CONFIGURATION
# ============================================================================

# Define the mapping of current state to the task name for UI display
STATE_TASK_NAMES: Dict[str, str] = {
    ProcessState.PENDING_PRK_REVIEW: "Present applications for acceptance (PRK/Chancellor)",
    ProcessState.UNDER_PRK_REVIEW: "Review applications and forward to PD",
    ProcessState.PENDING_RECTOR_PRESENTATION: "Present reviewed applications to Rector",
    ProcessState.PENDING_RECTOR_DECISION: "Make decision",
    ProcessState.ACCEPTED_PENDING_MPD: "Forward accepted applications to MPD",
    ProcessState.MPD_EXTERNAL_HANDLING: "Handle applications (external transfer)",
    ProcessState.PENDING_DECISION_RECEIPT: "Receive decision on award",
    ProcessState.PENDING_REGISTRATION: "Enter decoration into register",
}

# Define which role is responsible for each state
STATE_ROLE_MAPPING: Dict[str, str] = {
    ProcessState.PENDING_PRK_REVIEW: UserRole.PD,
    ProcessState.UNDER_PRK_REVIEW: UserRole.PRK_CHANCELLOR,
    ProcessState.PENDING_RECTOR_PRESENTATION: UserRole.PD,
    ProcessState.PENDING_RECTOR_DECISION: UserRole.RKR,
    ProcessState.ACCEPTED_PENDING_MPD: UserRole.PD,
    ProcessState.MPD_EXTERNAL_HANDLING: UserRole.MPD,
    ProcessState.PENDING_DECISION_RECEIPT: UserRole.PD,
    ProcessState.PENDING_REGISTRATION: UserRole.PD,
}


# ============================================================================
# WORKFLOW TRANSITION FUNCTIONS
# ============================================================================

def get_task_name(state: str) -> str:
    """
    Get the human-readable task name for a given process state.
    
    Args:
        state: Current process state.
        
    Returns:
        str: Human-readable task name.
    """
    return STATE_TASK_NAMES.get(state, state)


def get_next_state_after_action(current_state: str, decision: Optional[str] = None) -> Tuple[str, str]:
    """
    Determine the next state and assigned role after a task action.
    
    This implements the BPMN workflow transitions:
    - Start -> Submit Application -> PD Review -> PRK/Chancellor Review
    - -> PD Present to Rector -> Rector Decision
    - If Accepted: -> PD Forward to MPD -> MPD Handle -> PD Receive -> PD Register -> End
    - If Rejected: -> End (Rejected)
    
    Args:
        current_state: The current process state.
        decision: Optional decision value for gateway transitions.
        
    Returns:
        Tuple[str, str]: (next_state, assigned_role)
    """
    transitions = {
        # PD presents to PRK/Chancellor -> Goes to PRK/Chancellor for review
        ProcessState.PENDING_PRK_REVIEW: (
            ProcessState.UNDER_PRK_REVIEW, 
            UserRole.PRK_CHANCELLOR
        ),
        
        # PRK/Chancellor reviews -> Goes back to PD to present to Rector
        ProcessState.UNDER_PRK_REVIEW: (
            ProcessState.PENDING_RECTOR_PRESENTATION, 
            UserRole.PD
        ),
        
        # PD presents to Rector -> Goes to Rector for decision
        ProcessState.PENDING_RECTOR_PRESENTATION: (
            ProcessState.PENDING_RECTOR_DECISION, 
            UserRole.RKR
        ),
        
        # Rector makes decision -> Branches based on decision
        # This is handled specially in process_rector_decision()
        
        # PD forwards to MPD -> Goes to MPD for external handling
        ProcessState.ACCEPTED_PENDING_MPD: (
            ProcessState.MPD_EXTERNAL_HANDLING, 
            UserRole.MPD
        ),
        
        # MPD handles external transfer -> Goes to PD to receive decision
        ProcessState.MPD_EXTERNAL_HANDLING: (
            ProcessState.PENDING_DECISION_RECEIPT, 
            UserRole.PD
        ),
        
        # PD receives decision -> Goes to PD to register
        ProcessState.PENDING_DECISION_RECEIPT: (
            ProcessState.PENDING_REGISTRATION, 
            UserRole.PD
        ),
        
        # PD enters to register -> Process complete
        ProcessState.PENDING_REGISTRATION: (
            ProcessState.COMPLETED, 
            UserRole.PD  # No further assignment
        ),
    }
    
    return transitions.get(current_state, (current_state, UserRole.PD))


# ============================================================================
# TASK PROCESSING FUNCTIONS
# ============================================================================

def process_pd_present_to_prk(application_id: int, user_id: int, comments: Optional[str] = None) -> bool:
    """
    Process the "Present applications for acceptance (PRK/Chancellor)" task.
    PD verifies the application is complete and forwards to PRK/Chancellor.
    
    Args:
        application_id: ID of the application.
        user_id: ID of the user performing the action.
        comments: Optional comments.
        
    Returns:
        bool: True if successful.
    """
    app = get_application_by_id(application_id)
    if not app or app["current_state"] != ProcessState.PENDING_PRK_REVIEW:
        return False
    
    new_state, new_role = get_next_state_after_action(ProcessState.PENDING_PRK_REVIEW)
    
    return update_application_state(
        application_id=application_id,
        new_state=new_state,
        assigned_role=new_role,
        performed_by=user_id,
        action="Present applications for acceptance (PRK/Chancellor)",
        comments=comments
    )


def process_prk_review(
    application_id: int, 
    user_id: int, 
    reviewer_opinion: str,
    comments: Optional[str] = None
) -> bool:
    """
    Process the "Review applications and forward to PD" task.
    PRK/Chancellor reviews and provides an opinion.
    
    Args:
        application_id: ID of the application.
        user_id: ID of the user performing the action.
        reviewer_opinion: The reviewer's opinion text.
        comments: Optional comments.
        
    Returns:
        bool: True if successful.
    """
    app = get_application_by_id(application_id)
    if not app or app["current_state"] != ProcessState.UNDER_PRK_REVIEW:
        return False
    
    new_state, new_role = get_next_state_after_action(ProcessState.UNDER_PRK_REVIEW)
    
    return update_application_state(
        application_id=application_id,
        new_state=new_state,
        assigned_role=new_role,
        performed_by=user_id,
        action="Review applications and forward to PD",
        comments=comments,
        reviewer_opinion=reviewer_opinion
    )


def process_pd_present_to_rector(application_id: int, user_id: int, comments: Optional[str] = None) -> bool:
    """
    Process the "Present reviewed applications to Rector" task.
    PD collates the opinion and presents to Rector.
    
    Args:
        application_id: ID of the application.
        user_id: ID of the user performing the action.
        comments: Optional comments.
        
    Returns:
        bool: True if successful.
    """
    app = get_application_by_id(application_id)
    if not app or app["current_state"] != ProcessState.PENDING_RECTOR_PRESENTATION:
        return False
    
    new_state, new_role = get_next_state_after_action(ProcessState.PENDING_RECTOR_PRESENTATION)
    
    return update_application_state(
        application_id=application_id,
        new_state=new_state,
        assigned_role=new_role,
        performed_by=user_id,
        action="Present reviewed applications to Rector",
        comments=comments
    )


def process_rector_decision(
    application_id: int, 
    user_id: int, 
    rkr_decision: str,
    comments: Optional[str] = None
) -> bool:
    """
    Process the "Make decision" task.
    Rector makes the final accept/reject decision.
    This is a gateway task that branches based on the decision.
    
    Args:
        application_id: ID of the application.
        user_id: ID of the user performing the action.
        rkr_decision: The decision (RKRDecision.ACCEPTED or RKRDecision.REJECTED).
        comments: Optional comments.
        
    Returns:
        bool: True if successful.
    """
    app = get_application_by_id(application_id)
    if not app or app["current_state"] != ProcessState.PENDING_RECTOR_DECISION:
        return False
    
    # Gateway logic: branch based on decision
    if rkr_decision == RKRDecision.ACCEPTED:
        new_state = ProcessState.ACCEPTED_PENDING_MPD
        new_role = UserRole.PD
        process_outcome = None  # Not final yet
    else:
        new_state = ProcessState.REJECTED
        new_role = UserRole.PD  # No further assignment
        process_outcome = "Rejected"
    
    return update_application_state(
        application_id=application_id,
        new_state=new_state,
        assigned_role=new_role,
        performed_by=user_id,
        action="Make decision",
        comments=comments,
        rkr_decision=rkr_decision,
        process_outcome=process_outcome
    )


def process_pd_forward_to_mpd(application_id: int, user_id: int, comments: Optional[str] = None) -> bool:
    """
    Process the "Forward accepted applications to MPD" task.
    PD forwards the accepted application to MPD.
    
    Args:
        application_id: ID of the application.
        user_id: ID of the user performing the action.
        comments: Optional comments.
        
    Returns:
        bool: True if successful.
    """
    app = get_application_by_id(application_id)
    if not app or app["current_state"] != ProcessState.ACCEPTED_PENDING_MPD:
        return False
    
    new_state, new_role = get_next_state_after_action(ProcessState.ACCEPTED_PENDING_MPD)
    
    return update_application_state(
        application_id=application_id,
        new_state=new_state,
        assigned_role=new_role,
        performed_by=user_id,
        action="Forward accepted applications to MPD",
        comments=comments
    )


def process_mpd_external_handling(application_id: int, user_id: int, comments: Optional[str] = None) -> bool:
    """
    Process the "Handle applications (external transfer)" task.
    MPD handles the external transfer to appropriate body.
    
    Args:
        application_id: ID of the application.
        user_id: ID of the user performing the action.
        comments: Optional comments.
        
    Returns:
        bool: True if successful.
    """
    app = get_application_by_id(application_id)
    if not app or app["current_state"] != ProcessState.MPD_EXTERNAL_HANDLING:
        return False
    
    new_state, new_role = get_next_state_after_action(ProcessState.MPD_EXTERNAL_HANDLING)
    
    return update_application_state(
        application_id=application_id,
        new_state=new_state,
        assigned_role=new_role,
        performed_by=user_id,
        action="Handle applications (external transfer)",
        comments=comments
    )


def process_pd_receive_decision(application_id: int, user_id: int, comments: Optional[str] = None) -> bool:
    """
    Process the "Receive decision on award" task.
    PD receives and confirms the external decision.
    
    Args:
        application_id: ID of the application.
        user_id: ID of the user performing the action.
        comments: Optional comments.
        
    Returns:
        bool: True if successful.
    """
    app = get_application_by_id(application_id)
    if not app or app["current_state"] != ProcessState.PENDING_DECISION_RECEIPT:
        return False
    
    new_state, new_role = get_next_state_after_action(ProcessState.PENDING_DECISION_RECEIPT)
    
    return update_application_state(
        application_id=application_id,
        new_state=new_state,
        assigned_role=new_role,
        performed_by=user_id,
        action="Receive decision on award",
        comments=comments
    )


def process_pd_register(
    application_id: int, 
    user_id: int, 
    award_grant_date: str,
    comments: Optional[str] = None
) -> bool:
    """
    Process the "Enter decoration into register" task.
    PD enters the decoration into the official register.
    
    Args:
        application_id: ID of the application.
        user_id: ID of the user performing the action.
        award_grant_date: The date the award was granted (YYYY-MM-DD).
        comments: Optional comments.
        
    Returns:
        bool: True if successful.
    """
    app = get_application_by_id(application_id)
    if not app or app["current_state"] != ProcessState.PENDING_REGISTRATION:
        return False
    
    new_state, new_role = get_next_state_after_action(ProcessState.PENDING_REGISTRATION)
    
    return update_application_state(
        application_id=application_id,
        new_state=new_state,
        assigned_role=new_role,
        performed_by=user_id,
        action="Enter decoration into register",
        comments=comments,
        award_grant_date=award_grant_date,
        process_outcome="Completed"
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def can_user_process_application(user_role: str, application: Dict) -> bool:
    """
    Check if a user with given role can process an application.
    
    Args:
        user_role: The user's role.
        application: The application dictionary.
        
    Returns:
        bool: True if the user can process the application.
    """
    if application is None:
        return False
    
    # Check if the application is in a final state
    if application["current_state"] in [ProcessState.COMPLETED, ProcessState.REJECTED]:
        return False
    
    # Check if the role matches the assigned role
    return application["assigned_role"] == user_role


def get_available_actions(current_state: str) -> List[str]:
    """
    Get the available actions for a given process state.
    
    Args:
        current_state: The current process state.
        
    Returns:
        List[str]: List of available action names.
    """
    actions = {
        ProcessState.PENDING_PRK_REVIEW: ["Confirm and forward to PRK/Chancellor"],
        ProcessState.UNDER_PRK_REVIEW: ["Approve with opinion"],
        ProcessState.PENDING_RECTOR_PRESENTATION: ["Present to Rector"],
        ProcessState.PENDING_RECTOR_DECISION: ["Accept", "Reject"],
        ProcessState.ACCEPTED_PENDING_MPD: ["Forward to MPD"],
        ProcessState.MPD_EXTERNAL_HANDLING: ["Confirm external transfer"],
        ProcessState.PENDING_DECISION_RECEIPT: ["Confirm decision received"],
        ProcessState.PENDING_REGISTRATION: ["Enter to register"],
    }
    return actions.get(current_state, [])
