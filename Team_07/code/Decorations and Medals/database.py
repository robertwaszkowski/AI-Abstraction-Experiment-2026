"""
================================================================================
DATABASE.PY - Database Layer for Decorations and Medals Application
================================================================================
This module provides SQLite database functionality for the Decorations and Medals
workflow application. It handles all data persistence including users, applications,
and process history tracking.

Author: aideveloper
Version: 1.0
================================================================================
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Database file path - stored in the same directory as the application
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "decorations_medals.db")


# ============================================================================
# ENUM DEFINITIONS
# ============================================================================

class UserRole:
    """
    User roles corresponding to BPMN lanes.
    Each role has specific tasks they can perform in the workflow.
    """
    HEAD_OF_OU = "Head of O.U."           # Kierownik J.O. - initiates applications
    PD = "Personnel Department"            # Dział Personalny (DPE) - routing & register
    PRK_CHANCELLOR = "PRK / Chancellor"    # PRK/Kanclerz - reviews applications
    RKR = "Rector"                         # Rektor (RKR) - final decision maker
    MPD = "Military Personnel Department"  # Wojskowa Komenda Osobowa (WKW)


class ProcessState:
    """
    Process states corresponding to BPMN tasks.
    These states define where an application is in the workflow.
    """
    # Initial state - application just created
    SUBMITTED = "Submitted"
    
    # After Head of O.U. submits, waiting for PD to present to PRK/Chancellor
    PENDING_PRK_REVIEW = "Pending PRK/Chancellor Review"
    
    # PRK/Chancellor is reviewing the application
    UNDER_PRK_REVIEW = "Under PRK/Chancellor Review"
    
    # After PRK review, waiting for PD to present to Rector
    PENDING_RECTOR_PRESENTATION = "Pending Rector Presentation"
    
    # Rector is making the decision
    PENDING_RECTOR_DECISION = "Pending Rector Decision"
    
    # After Rector accepts, waiting for PD to forward to MPD
    ACCEPTED_PENDING_MPD = "Accepted - Pending MPD Forward"
    
    # MPD is handling external transfer
    MPD_EXTERNAL_HANDLING = "MPD External Handling"
    
    # Waiting for PD to receive external decision
    PENDING_DECISION_RECEIPT = "Pending Decision Receipt"
    
    # Waiting for PD to enter to register
    PENDING_REGISTRATION = "Pending Registration"
    
    # Final states
    COMPLETED = "Completed"
    REJECTED = "Rejected"


class RKRDecision:
    """
    Rector's decision options for the application.
    """
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


# ============================================================================
# DATABASE CONNECTION MANAGEMENT
# ============================================================================

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures proper connection handling and automatic closing.
    
    Yields:
        sqlite3.Connection: Active database connection with row factory enabled.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enables dict-like access to rows
        yield conn
    finally:
        if conn:
            conn.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def initialize_database():
    """
    Initialize the database with all required tables.
    Creates tables if they don't exist and populates with test users.
    
    Tables created:
    - users: User accounts with roles
    - applications: Decoration/medal applications with all process data
    - process_history: Audit log of all workflow actions
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # ================================================================
        # USERS TABLE
        # Stores all system users with their assigned roles
        # ================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ================================================================
        # APPLICATIONS TABLE
        # Main table storing all decoration/medal applications
        # Contains both initiation data and process routing data
        # ================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Application Data (Initiation) --
                employee_name TEXT NOT NULL,
                organizational_unit TEXT NOT NULL,
                decoration_type TEXT NOT NULL,
                application_justification TEXT NOT NULL,
                
                -- Process Approval and Routing Data --
                reviewer_opinion TEXT,
                rkr_decision TEXT,
                award_grant_date DATE,
                process_outcome TEXT,
                
                -- Workflow State Management --
                current_state TEXT NOT NULL DEFAULT 'Submitted',
                assigned_role TEXT NOT NULL,
                
                -- Audit Fields --
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Foreign Key --
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # ================================================================
        # PROCESS HISTORY TABLE
        # Audit log tracking all actions taken on applications
        # ================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT,
                performed_by INTEGER NOT NULL,
                comments TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Foreign Keys --
                FOREIGN KEY (application_id) REFERENCES applications(id),
                FOREIGN KEY (performed_by) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        
        # Insert test users from the test scenario document
        _insert_test_users(cursor, conn)
        
        # Insert sample applications
        _insert_sample_applications(cursor, conn)


def _insert_test_users(cursor, conn):
    """
    Insert test users from the test scenario document.
    Only inserts if the users table is empty (first run).
    
    Test Users (from documentation):
    - Holly Head: Head of O.U. (Initiator)
    - Penny Personnel: Personnel Department (PD)
    - Paula VREdu: PRK / Chancellor
    - Adam Rector: Rector (RKR)
    - Mike MPD: Military Personnel Department
    """
    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        return  # Users already exist, skip insertion
    
    # Test users from the test scenario document
    test_users = [
        ("holly.head", "Holly Head", UserRole.HEAD_OF_OU),
        ("penny.personnel", "Penny Personnel", UserRole.PD),
        ("paula.vredu", "Paula VREdu", UserRole.PRK_CHANCELLOR),
        ("adam.rector", "Adam Rector", UserRole.RKR),
        ("mike.mpd", "Mike MPD", UserRole.MPD),
    ]
    
    for username, display_name, role in test_users:
        cursor.execute("""
            INSERT INTO users (username, display_name, role)
            VALUES (?, ?, ?)
        """, (username, display_name, role))
    
    conn.commit()


def _insert_sample_applications(cursor, conn):
    """
    Insert sample applications for demonstration purposes.
    Only running if table is empty.
    """
    cursor.execute("SELECT COUNT(*) FROM applications")
    if cursor.fetchone()[0] > 0:
        return

    # Get user IDs using a temporary cursor to avoid row_factory issues if any
    # Actually row_factory is set to sqlite3.Row in get_db_connection
    cursor.execute("SELECT id, role FROM users")
    
    # We need to fetch all and iterate because 'role' is not unique (though in test users it is mostly unique)
    user_rows = cursor.fetchall()
    users = {row["role"]: row["id"] for row in user_rows}
    
    holly_id = users.get(UserRole.HEAD_OF_OU, 1)
    
    samples = [
         ("Janusz Kowalski", "Faculty of Cybernetics", "Gold Medal for Long Service",
          "Wieloletnia, wzorowa praca dydaktyczna.", ProcessState.PENDING_PRK_REVIEW, UserRole.PD),
         ("Anna Nowak", "Faculty of Electronics", "Bronze Medal for Long Service",
          "Zasługi w projektach badawczych.", ProcessState.PENDING_RECTOR_DECISION, UserRole.RKR),
         ("Piotr Wiśniewski", "Administration", "Silver Medal for Long Service",
          "Wsparcie administracyjne.", ProcessState.SUBMITTED, UserRole.PD)
    ]
    
    for emp, unit, dec, just, state, role in samples:
        cursor.execute("""
            INSERT INTO applications (
                employee_name, organizational_unit, decoration_type, application_justification,
                current_state, assigned_role, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (emp, unit, dec, just, state, role, holly_id))
        
    conn.commit()


# ============================================================================
# USER OPERATIONS
# ============================================================================

def get_all_users() -> List[Dict[str, Any]]:
    """
    Retrieve all users from the database.
    
    Returns:
        List[Dict]: List of user dictionaries with id, username, display_name, role.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, display_name, role FROM users ORDER BY role, display_name")
        return [dict(row) for row in cursor.fetchall()]


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific user by their ID.
    
    Args:
        user_id: The user's database ID.
        
    Returns:
        Dict or None: User data dictionary or None if not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, display_name, role FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_users_by_role(role: str) -> List[Dict[str, Any]]:
    """
    Retrieve all users with a specific role.
    
    Args:
        role: The role to filter by (use UserRole constants).
        
    Returns:
        List[Dict]: List of user dictionaries with the specified role.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, display_name, role FROM users WHERE role = ?", (role,))
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# APPLICATION OPERATIONS
# ============================================================================

def create_application(
    employee_name: str,
    organizational_unit: str,
    decoration_type: str,
    application_justification: str,
    created_by: int
) -> int:
    """
    Create a new decoration/medal application.
    
    Args:
        employee_name: Full name of the nominated employee.
        organizational_unit: Organizational unit of the employee.
        decoration_type: Type of decoration/medal being requested.
        application_justification: Justification text for the award.
        created_by: ID of the user creating the application.
        
    Returns:
        int: The ID of the newly created application.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create the application with initial state
        cursor.execute("""
            INSERT INTO applications (
                employee_name,
                organizational_unit,
                decoration_type,
                application_justification,
                current_state,
                assigned_role,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_name,
            organizational_unit,
            decoration_type,
            application_justification,
            ProcessState.PENDING_PRK_REVIEW,  # First task goes to PD
            UserRole.PD,                       # PD presents to PRK/Chancellor
            created_by
        ))
        
        application_id = cursor.lastrowid
        
        # Log the creation in process history
        cursor.execute("""
            INSERT INTO process_history (
                application_id, action, from_state, to_state, performed_by, comments
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            application_id,
            "Application Submitted",
            None,
            ProcessState.PENDING_PRK_REVIEW,
            created_by,
            f"Application submitted for {employee_name}"
        ))
        
        conn.commit()
        return application_id


def get_application_by_id(application_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific application by its ID.
    
    Args:
        application_id: The application's database ID.
        
    Returns:
        Dict or None: Application data dictionary or None if not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, u.display_name as created_by_name
            FROM applications a
            LEFT JOIN users u ON a.created_by = u.id
            WHERE a.id = ?
        """, (application_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_applications_by_role(role: str) -> List[Dict[str, Any]]:
    """
    Get all applications currently assigned to a specific role.
    These are the pending tasks for users with that role.
    
    Args:
        role: The role to filter by (use UserRole constants).
        
    Returns:
        List[Dict]: List of application dictionaries assigned to the role.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, u.display_name as created_by_name
            FROM applications a
            LEFT JOIN users u ON a.created_by = u.id
            WHERE a.assigned_role = ?
            AND a.current_state NOT IN (?, ?)
            ORDER BY a.created_at DESC
        """, (role, ProcessState.COMPLETED, ProcessState.REJECTED))
        return [dict(row) for row in cursor.fetchall()]


def get_all_applications() -> List[Dict[str, Any]]:
    """
    Get all applications in the system.
    
    Returns:
        List[Dict]: List of all application dictionaries.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, u.display_name as created_by_name
            FROM applications a
            LEFT JOIN users u ON a.created_by = u.id
            ORDER BY a.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_completed_applications() -> List[Dict[str, Any]]:
    """
    Get all successfully completed applications (decoration register).
    
    Returns:
        List[Dict]: List of completed application dictionaries.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, u.display_name as created_by_name
            FROM applications a
            LEFT JOIN users u ON a.created_by = u.id
            WHERE a.current_state = ?
            ORDER BY a.award_grant_date DESC
        """, (ProcessState.COMPLETED,))
        return [dict(row) for row in cursor.fetchall()]


def update_application_state(
    application_id: int,
    new_state: str,
    assigned_role: str,
    performed_by: int,
    action: str,
    comments: Optional[str] = None,
    **extra_fields
) -> bool:
    """
    Update an application's state and assigned role.
    Also logs the action in process history.
    
    Args:
        application_id: ID of the application to update.
        new_state: The new process state.
        assigned_role: The role now responsible for the application.
        performed_by: ID of the user performing the action.
        action: Description of the action taken.
        comments: Optional comments about the action.
        **extra_fields: Additional fields to update (e.g., reviewer_opinion).
        
    Returns:
        bool: True if update was successful, False otherwise.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get current state for history
        cursor.execute("SELECT current_state FROM applications WHERE id = ?", (application_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        old_state = row["current_state"]
        
        # Build dynamic update query for extra fields
        update_fields = ["current_state = ?", "assigned_role = ?", "updated_at = ?"]
        update_values = [new_state, assigned_role, datetime.now()]
        
        # Add any extra fields to update
        for field, value in extra_fields.items():
            update_fields.append(f"{field} = ?")
            update_values.append(value)
        
        update_values.append(application_id)
        
        cursor.execute(f"""
            UPDATE applications 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, update_values)
        
        # Log to process history
        cursor.execute("""
            INSERT INTO process_history (
                application_id, action, from_state, to_state, performed_by, comments
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (application_id, action, old_state, new_state, performed_by, comments))
        
        conn.commit()
        return True


# ============================================================================
# PROCESS HISTORY OPERATIONS
# ============================================================================

def get_application_history(application_id: int) -> List[Dict[str, Any]]:
    """
    Get the complete history of actions for an application.
    
    Args:
        application_id: The application's database ID.
        
    Returns:
        List[Dict]: List of history entries ordered by timestamp.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.*, u.display_name as performed_by_name
            FROM process_history h
            LEFT JOIN users u ON h.performed_by = u.id
            WHERE h.application_id = ?
            ORDER BY h.timestamp ASC
        """, (application_id,))
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# DATABASE STATISTICS
# ============================================================================

def get_statistics() -> Dict[str, Any]:
    """
    Get various statistics about applications in the system.
    
    Returns:
        Dict: Statistics including counts by state and other metrics.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        stats = {}
        
        # Total applications
        cursor.execute("SELECT COUNT(*) FROM applications")
        stats["total"] = cursor.fetchone()[0]
        
        # Completed
        cursor.execute("SELECT COUNT(*) FROM applications WHERE current_state = ?", 
                      (ProcessState.COMPLETED,))
        stats["completed"] = cursor.fetchone()[0]
        
        # Rejected
        cursor.execute("SELECT COUNT(*) FROM applications WHERE current_state = ?", 
                      (ProcessState.REJECTED,))
        stats["rejected"] = cursor.fetchone()[0]
        
        # In progress
        stats["in_progress"] = stats["total"] - stats["completed"] - stats["rejected"]
        
        return stats


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Initialize database when module is imported
if __name__ != "__main__":
    initialize_database()
