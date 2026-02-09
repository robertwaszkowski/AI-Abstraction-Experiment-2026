"""
================================================================================
APP.PY - Main Streamlit Application for Decorations and Medals System
================================================================================
This is the main user interface for the Decorations and Medals workflow
management system. It provides role-based views for all process participants.

Author: aideveloper
Version: 1.0
================================================================================
"""

import streamlit as st
from datetime import datetime, date
from typing import Optional, Dict, Any

# Import database and workflow modules
import database as db
from database import ProcessState, UserRole, RKRDecision
import workflow as wf


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Decorations and Medals System",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================

st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 1rem;
    }
    
    /* Card-like containers for tasks */
    .task-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Status badges */
    .status-pending {
        background-color: #ffc107;
        color: #212529;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-completed {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-rejected {
        background-color: #dc3545;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        margin-bottom: 0.5rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        text-align: center;
        border-left: 4px solid;
    }
    
    .metric-card.blue { border-left-color: #667eea; }
    .metric-card.green { border-left-color: #28a745; }
    .metric-card.red { border-left-color: #dc3545; }
    .metric-card.orange { border-left-color: #fd7e14; }
    
    /* Info boxes */
    .info-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    /* Application details */
    .app-details {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    /* Timeline styling */
    .timeline-item {
        padding: 1rem;
        border-left: 3px solid #667eea;
        margin-left: 1rem;
        margin-bottom: 0.5rem;
        background: #f8f9fa;
        border-radius: 0 8px 8px 0;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all required session state variables."""
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    if "selected_application" not in st.session_state:
        st.session_state.selected_application = None


# ============================================================================
# AUTHENTICATION / USER SELECTION
# ============================================================================

def render_login_page():
    """Render the login/user selection page."""
    st.markdown("""
    <div class="main-header">
        <h1>🎖️ Decorations and Medals System</h1>
        <p>Military University of Technology - DPE/1-6 Process</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instrukcja obsługi
    with st.expander("📖 **INSTRUKCJA OBSŁUGI** - Kliknij aby rozwinąć", expanded=False):
        st.markdown("""
        ### Jak korzystać z aplikacji?
        
        **1. Wybierz użytkownika** - kliknij na przycisk z nazwą użytkownika poniżej
        
        **2. Dostępne role i ich zadania:**
        
        | Rola | Użytkownik | Zadanie |
        |------|------------|---------|
        | **Head of O.U.** | Holly Head | Składa wnioski o odznaczenia |
        | **Personnel Dept.** | Penny Personnel | Przekazuje wnioski, rejestruje |
        | **PRK/Chancellor** | Paula VREdu | Opiniuje wnioski |
        | **Rector** | Adam Rector | Podejmuje decyzje (akceptacja/odrzucenie) |
        | **MPD** | Mike MPD | Obsługa zewnętrzna |
        
        **3. Pełny przepływ pracy (workflow):**
        1. 👤 **Holly Head** → składa wniosek (➕ New Application)
        2. 📋 **Penny Personnel** → przekazuje do PRK (Process Task)
        3. ✍️ **Paula VREdu** → wydaje opinię
        4. 📋 **Penny Personnel** → prezentuje Rektorowi
        5. ⚖️ **Adam Rector** → akceptuje lub odrzuca
        6. 📋 **Penny Personnel** → przekazuje do MPD
        7. 🏛️ **Mike MPD** → obsługa zewnętrzna
        8. 📋 **Penny Personnel** → rejestruje w rejestrze odznaczeń
        
        **4. Nawigacja po zalogowaniu:**
        - **📊 Dashboard** - przegląd zadań i statystyki
        - **📋 My Tasks** - Twoje zadania do wykonania
        - **➕ New Application** - złóż nowy wniosek (tylko Head of O.U.)
        - **📜 All Applications** - wszystkie wnioski
        - **🏆 Decorations Register** - rejestr odznaczeń
        """)
    
    st.markdown("---")
    st.markdown("### Select User to Login")
    st.markdown("Choose a user from the list below to simulate their role in the workflow.")
    
    # Get all users
    users = db.get_all_users()
    
    # Group users by role
    roles = {}
    for user in users:
        role = user["role"]
        if role not in roles:
            roles[role] = []
        roles[role].append(user)
    
    # Create columns for different roles
    cols = st.columns(len(roles))
    
    for idx, (role, role_users) in enumerate(roles.items()):
        with cols[idx]:
            st.markdown(f"**{role}**")
            for user in role_users:
                if st.button(
                    f"👤 {user['display_name']}", 
                    key=f"login_{user['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_user = user
                    st.rerun()


def render_sidebar():
    """Render the sidebar with navigation and user info."""
    user = st.session_state.current_user
    
    with st.sidebar:
        st.markdown(f"### 👤 {user['display_name']}")
        st.markdown(f"**Role:** {user['role']}")
        st.divider()
        
        # Navigation buttons
        st.markdown("### Navigation")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.session_state.selected_application = None
            st.rerun()
        
        if st.button("📋 My Tasks", use_container_width=True):
            st.session_state.page = "tasks"
            st.session_state.selected_application = None
            st.rerun()
        
        # Show "New Application" only for Head of O.U.
        if user["role"] == UserRole.HEAD_OF_OU:
            if st.button("➕ New Application", use_container_width=True):
                st.session_state.page = "new_application"
                st.session_state.selected_application = None
                st.rerun()
        
        if st.button("📜 All Applications", use_container_width=True):
            st.session_state.page = "all_applications"
            st.session_state.selected_application = None
            st.rerun()
        
        if st.button("🏆 Decorations Register", use_container_width=True):
            st.session_state.page = "register"
            st.session_state.selected_application = None
            st.rerun()
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.page = "dashboard"
            st.session_state.selected_application = None
            st.rerun()


# ============================================================================
# DASHBOARD PAGE
# ============================================================================

def render_dashboard():
    """Render the main dashboard page."""
    user = st.session_state.current_user
    
    st.markdown("""
    <div class="main-header">
        <h1>🎖️ Decorations and Medals System</h1>
        <p>Military University of Technology - DPE/1-6 Process</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get statistics
    stats = db.get_statistics()
    pending_tasks = db.get_applications_by_role(user["role"])
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Applications", stats["total"])
    
    with col2:
        st.metric("⏳ In Progress", stats["in_progress"])
    
    with col3:
        st.metric("✅ Completed", stats["completed"])
    
    with col4:
        st.metric("❌ Rejected", stats["rejected"])
    
    st.divider()
    
    # Pending tasks for current user
    st.markdown(f"### 📬 Your Pending Tasks ({len(pending_tasks)})")
    
    if pending_tasks:
        for app in pending_tasks:
            task_name = wf.get_task_name(app["current_state"])
            
            with st.expander(f"📄 {app['employee_name']} - {app['decoration_type']}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Task:** {task_name}")
                    st.markdown(f"**Employee:** {app['employee_name']}")
                    st.markdown(f"**Unit:** {app['organizational_unit']}")
                    st.markdown(f"**Submitted:** {app['created_at']}")
                
                with col2:
                    if st.button("Process Task", key=f"process_{app['id']}", use_container_width=True):
                        st.session_state.selected_application = app["id"]
                        st.session_state.page = "process_task"
                        st.rerun()
    else:
        st.info("No pending tasks for your role.")


# ============================================================================
# NEW APPLICATION PAGE
# ============================================================================

def render_new_application():
    """Render the new application form (for Head of O.U. only)."""
    st.markdown("## ➕ Submit New Application for Distinction")
    
    with st.form("new_application_form"):
        st.markdown("### Employee Information")
        
        # Pobierz użytkowników z bazy jako potencjalnych kandydatów
        users = db.get_all_users()
        # Dodaj przykładowych pracowników do listy
        additional_employees = [
            {"display_name": "Jan Kowalski"},
            {"display_name": "Anna Nowak"},
            {"display_name": "Piotr Wiśniewski"},
            {"display_name": "Maria Wójcik"},
            {"display_name": "Krzysztof Kamiński"}
        ]
        
        # Połącz listy i wyciągnij nazwy
        candidate_names = [u["display_name"] for u in users] + [e["display_name"] for e in additional_employees]
        candidate_names = sorted(list(set(candidate_names))) # Unikalne i posortowane
        
        employee_name = st.selectbox(
            "Employee Name *",
            options=candidate_names,
            index=None,
            placeholder="Select the nominated employee"
        )
        
        organizational_unit = st.text_input(
            "Organizational Unit *",
            placeholder="Enter the organizational unit"
        )
        
        st.markdown("### Decoration Details")
        
        decoration_type = st.selectbox(
            "Decoration Type *",
            options=[
                "Gold Medal for Long Service",
                "Silver Medal for Long Service",
                "Bronze Medal for Long Service",
                "Medal for Merit for National Defense",
                "Medal of the Armed Forces in Service of the Homeland",
                "Other Decoration"
            ]
        )
        
        application_justification = st.text_area(
            "Application Justification *",
            placeholder="Enter a detailed justification for the award, including specific achievements and reasons...",
            height=200
        )
        
        st.divider()
        
        submitted = st.form_submit_button("📤 Submit Application", use_container_width=True)
        
        if submitted:
            # Validate form
            if not employee_name or not organizational_unit or not application_justification:
                st.error("Please fill in all required fields.")
            else:
                # Create the application
                try:
                    app_id = db.create_application(
                        employee_name=employee_name,
                        organizational_unit=organizational_unit,
                        decoration_type=decoration_type,
                        application_justification=application_justification,
                        created_by=st.session_state.current_user["id"]
                    )
                    
                    st.success(f"✅ Application submitted successfully! (ID: {app_id})")
                    st.info("The application has been forwarded to the Personnel Department.")
                    
                    # Reset form by rerunning
                    if st.button("Submit Another Application"):
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error submitting application: {str(e)}")


# ============================================================================
# TASK PROCESSING PAGE
# ============================================================================

def render_process_task():
    """Render the task processing page based on current state."""
    app_id = st.session_state.selected_application
    
    if app_id is None:
        st.warning("No application selected.")
        return
    
    app = db.get_application_by_id(app_id)
    
    if app is None:
        st.error("Application not found.")
        return
    
    user = st.session_state.current_user
    
    # Check if user can process this application
    if not wf.can_user_process_application(user["role"], app):
        st.error("You are not authorized to process this application at its current state.")
        return
    
    task_name = wf.get_task_name(app["current_state"])
    
    st.markdown(f"## 📋 {task_name}")
    
    # Display application details
    render_application_details(app)
    
    st.divider()
    
    # Render the appropriate form based on current state
    current_state = app["current_state"]
    
    if current_state == ProcessState.PENDING_PRK_REVIEW:
        render_pd_present_to_prk_form(app)
    elif current_state == ProcessState.UNDER_PRK_REVIEW:
        render_prk_review_form(app)
    elif current_state == ProcessState.PENDING_RECTOR_PRESENTATION:
        render_pd_present_to_rector_form(app)
    elif current_state == ProcessState.PENDING_RECTOR_DECISION:
        render_rector_decision_form(app)
    elif current_state == ProcessState.ACCEPTED_PENDING_MPD:
        render_pd_forward_to_mpd_form(app)
    elif current_state == ProcessState.MPD_EXTERNAL_HANDLING:
        render_mpd_external_form(app)
    elif current_state == ProcessState.PENDING_DECISION_RECEIPT:
        render_pd_receive_decision_form(app)
    elif current_state == ProcessState.PENDING_REGISTRATION:
        render_pd_register_form(app)


def render_application_details(app: Dict[str, Any]):
    """Render the application details in a consistent format."""
    st.markdown("### 📄 Application Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Application ID:** {app['id']}")
        st.markdown(f"**Employee Name:** {app['employee_name']}")
        st.markdown(f"**Organizational Unit:** {app['organizational_unit']}")
        st.markdown(f"**Decoration Type:** {app['decoration_type']}")
    
    with col2:
        st.markdown(f"**Current State:** {app['current_state']}")
        st.markdown(f"**Submitted By:** {app['created_by_name']}")
        st.markdown(f"**Submitted At:** {app['created_at']}")
        
        if app.get("reviewer_opinion"):
            st.markdown(f"**PRK/Chancellor Opinion:** {app['reviewer_opinion']}")
        
        if app.get("rkr_decision"):
            st.markdown(f"**Rector Decision:** {app['rkr_decision']}")
    
    st.markdown("**Application Justification:**")
    st.markdown(f"> {app['application_justification']}")


# ============================================================================
# TASK-SPECIFIC FORMS
# ============================================================================

def render_pd_present_to_prk_form(app: Dict[str, Any]):
    """Form for PD to present application to PRK/Chancellor."""
    st.markdown("### ✍️ Task: Present Applications for Acceptance")
    st.info("Review the application details above and confirm to forward to PRK/Chancellor for review.")
    
    with st.form("pd_present_prk_form"):
        comments = st.text_area("Comments (optional)", placeholder="Enter any comments...")
        
        if st.form_submit_button("✅ Confirm and Forward to PRK/Chancellor", use_container_width=True):
            success = wf.process_pd_present_to_prk(
                application_id=app["id"],
                user_id=st.session_state.current_user["id"],
                comments=comments
            )
            
            if success:
                st.success("Application forwarded to PRK/Chancellor for review.")
                st.session_state.selected_application = None
                st.session_state.page = "tasks"
                st.rerun()
            else:
                st.error("Failed to process the task. Please try again.")


def render_prk_review_form(app: Dict[str, Any]):
    """Form for PRK/Chancellor to review and provide opinion."""
    st.markdown("### ✍️ Task: Review Applications and Forward to PD")
    st.info("Review the application and provide your opinion.")
    
    with st.form("prk_review_form"):
        reviewer_opinion = st.text_area(
            "Reviewer Opinion *",
            placeholder="Enter your opinion on this application (e.g., 'Strongly support', 'Support with reservations', 'Do not support')...",
            height=150
        )
        
        comments = st.text_area("Additional Comments (optional)", placeholder="Enter any additional comments...")
        
        if st.form_submit_button("✅ Submit Opinion and Approve", use_container_width=True):
            if not reviewer_opinion:
                st.error("Please provide your opinion.")
            else:
                success = wf.process_prk_review(
                    application_id=app["id"],
                    user_id=st.session_state.current_user["id"],
                    reviewer_opinion=reviewer_opinion,
                    comments=comments
                )
                
                if success:
                    st.success("Opinion submitted. Application returned to Personnel Department.")
                    st.session_state.selected_application = None
                    st.session_state.page = "tasks"
                    st.rerun()
                else:
                    st.error("Failed to process the task. Please try again.")


def render_pd_present_to_rector_form(app: Dict[str, Any]):
    """Form for PD to present reviewed application to Rector."""
    st.markdown("### ✍️ Task: Present Reviewed Applications to Rector")
    st.info("The application has been reviewed by PRK/Chancellor. Present to Rector for final decision.")
    
    # Show the PRK/Chancellor opinion
    if app.get("reviewer_opinion"):
        st.markdown(f"**PRK/Chancellor Opinion:** {app['reviewer_opinion']}")
    
    with st.form("pd_present_rector_form"):
        comments = st.text_area("Comments (optional)", placeholder="Enter any comments...")
        
        if st.form_submit_button("✅ Present to Rector", use_container_width=True):
            success = wf.process_pd_present_to_rector(
                application_id=app["id"],
                user_id=st.session_state.current_user["id"],
                comments=comments
            )
            
            if success:
                st.success("Application presented to Rector for decision.")
                st.session_state.selected_application = None
                st.session_state.page = "tasks"
                st.rerun()
            else:
                st.error("Failed to process the task. Please try again.")


def render_rector_decision_form(app: Dict[str, Any]):
    """Form for Rector to make accept/reject decision."""
    st.markdown("### ✍️ Task: Make Decision")
    st.warning("This is the final decision point. Choose to Accept or Reject the application.")
    
    # Show the PRK/Chancellor opinion
    if app.get("reviewer_opinion"):
        st.markdown(f"**PRK/Chancellor Opinion:** {app['reviewer_opinion']}")
    
    with st.form("rector_decision_form"):
        decision = st.radio(
            "Decision *",
            options=[RKRDecision.ACCEPTED, RKRDecision.REJECTED],
            format_func=lambda x: "✅ Accept Application" if x == RKRDecision.ACCEPTED else "❌ Reject Application",
            horizontal=True
        )
        
        comments = st.text_area("Decision Notes (optional)", placeholder="Enter any notes regarding your decision...")
        
        if st.form_submit_button("📝 Submit Decision", use_container_width=True):
            success = wf.process_rector_decision(
                application_id=app["id"],
                user_id=st.session_state.current_user["id"],
                rkr_decision=decision,
                comments=comments
            )
            
            if success:
                if decision == RKRDecision.ACCEPTED:
                    st.success("Application ACCEPTED. Forwarded to Personnel Department for MPD transfer.")
                else:
                    st.error("Application REJECTED. Process ended.")
                st.session_state.selected_application = None
                st.session_state.page = "tasks"
                st.rerun()
            else:
                st.error("Failed to process the task. Please try again.")


def render_pd_forward_to_mpd_form(app: Dict[str, Any]):
    """Form for PD to forward accepted application to MPD."""
    st.markdown("### ✍️ Task: Forward Accepted Applications to MPD")
    st.success(f"✅ This application has been ACCEPTED by the Rector.")
    st.info("Forward the accepted application to the Military Personnel Department.")
    
    with st.form("pd_forward_mpd_form"):
        comments = st.text_area("Comments (optional)", placeholder="Enter any comments...")
        
        if st.form_submit_button("✅ Forward to MPD", use_container_width=True):
            success = wf.process_pd_forward_to_mpd(
                application_id=app["id"],
                user_id=st.session_state.current_user["id"],
                comments=comments
            )
            
            if success:
                st.success("Application forwarded to Military Personnel Department.")
                st.session_state.selected_application = None
                st.session_state.page = "tasks"
                st.rerun()
            else:
                st.error("Failed to process the task. Please try again.")


def render_mpd_external_form(app: Dict[str, Any]):
    """Form for MPD to handle external transfer."""
    st.markdown("### ✍️ Task: Handle Applications (External Transfer)")
    st.info("Process the external transfer to the appropriate body.")
    
    with st.form("mpd_external_form"):
        comments = st.text_area(
            "Transfer Notes",
            placeholder="Enter notes about the external transfer (e.g., reference number, date sent)..."
        )
        
        if st.form_submit_button("✅ Confirm External Transfer Complete", use_container_width=True):
            success = wf.process_mpd_external_handling(
                application_id=app["id"],
                user_id=st.session_state.current_user["id"],
                comments=comments
            )
            
            if success:
                st.success("External transfer confirmed. Awaiting decision receipt.")
                st.session_state.selected_application = None
                st.session_state.page = "tasks"
                st.rerun()
            else:
                st.error("Failed to process the task. Please try again.")


def render_pd_receive_decision_form(app: Dict[str, Any]):
    """Form for PD to receive external decision."""
    st.markdown("### ✍️ Task: Receive Decision on Award")
    st.info("Confirm that the external decision has been received for this award application.")
    
    with st.form("pd_receive_decision_form"):
        comments = st.text_area(
            "Decision Details",
            placeholder="Enter details about the received decision..."
        )
        
        if st.form_submit_button("✅ Confirm Decision Received", use_container_width=True):
            success = wf.process_pd_receive_decision(
                application_id=app["id"],
                user_id=st.session_state.current_user["id"],
                comments=comments
            )
            
            if success:
                st.success("Decision receipt confirmed. Ready for registration.")
                st.session_state.selected_application = None
                st.session_state.page = "tasks"
                st.rerun()
            else:
                st.error("Failed to process the task. Please try again.")


def render_pd_register_form(app: Dict[str, Any]):
    """Form for PD to enter decoration into register."""
    st.markdown("### ✍️ Task: Enter Decoration into Register")
    st.success("🎉 This is the final step! Enter the decoration into the official register.")
    
    with st.form("pd_register_form"):
        award_grant_date = st.date_input(
            "Award Grant Date *",
            value=date.today()
        )
        
        comments = st.text_area(
            "Registration Notes (optional)",
            placeholder="Enter any notes for the registration record..."
        )
        
        if st.form_submit_button("✅ Complete Registration", use_container_width=True):
            success = wf.process_pd_register(
                application_id=app["id"],
                user_id=st.session_state.current_user["id"],
                award_grant_date=award_grant_date.strftime("%Y-%m-%d"),
                comments=comments
            )
            
            if success:
                st.success("🎖️ Decoration successfully registered! Process completed.")
                st.balloons()  # Celebrate!
                st.session_state.selected_application = None
                st.session_state.page = "register"
                st.rerun()
            else:
                st.error("Failed to process the task. Please try again.")


# ============================================================================
# TASKS LIST PAGE
# ============================================================================

def render_tasks_page():
    """Render the list of pending tasks for current user."""
    user = st.session_state.current_user
    
    st.markdown(f"## 📋 My Tasks")
    
    pending_tasks = db.get_applications_by_role(user["role"])
    
    if not pending_tasks:
        st.info("🎉 No pending tasks. You're all caught up!")
        return
    
    st.markdown(f"You have **{len(pending_tasks)}** pending task(s).")
    
    for app in pending_tasks:
        task_name = wf.get_task_name(app["current_state"])
        
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**{app['employee_name']}**")
                st.markdown(f"*{app['decoration_type']}*")
            
            with col2:
                st.markdown(f"📌 {task_name}")
                st.markdown(f"🏢 {app['organizational_unit']}")
            
            with col3:
                if st.button("Process ➡️", key=f"task_{app['id']}", use_container_width=True):
                    st.session_state.selected_application = app["id"]
                    st.session_state.page = "process_task"
                    st.rerun()
            
            st.divider()


# ============================================================================
# ALL APPLICATIONS PAGE
# ============================================================================

def render_all_applications():
    """Render all applications in the system."""
    st.markdown("## 📜 All Applications")
    
    applications = db.get_all_applications()
    
    if not applications:
        st.info("No applications in the system yet.")
        return
    
    # Status filter
    status_filter = st.selectbox(
        "Filter by Status",
        options=["All", "In Progress", "Completed", "Rejected"]
    )
    
    # Apply filter
    if status_filter == "Completed":
        applications = [a for a in applications if a["current_state"] == ProcessState.COMPLETED]
    elif status_filter == "Rejected":
        applications = [a for a in applications if a["current_state"] == ProcessState.REJECTED]
    elif status_filter == "In Progress":
        applications = [a for a in applications if a["current_state"] not in [ProcessState.COMPLETED, ProcessState.REJECTED]]
    
    st.markdown(f"Showing **{len(applications)}** application(s).")
    
    for app in applications:
        # Determine status badge
        if app["current_state"] == ProcessState.COMPLETED:
            status_class = "status-completed"
            status_text = "Completed"
        elif app["current_state"] == ProcessState.REJECTED:
            status_class = "status-rejected"
            status_text = "Rejected"
        else:
            status_class = "status-pending"
            status_text = "In Progress"
        
        with st.expander(f"📄 {app['employee_name']} - {app['decoration_type']} ({status_text})"):
            render_application_details(app)
            
            # Show history
            st.markdown("### 📜 Process History")
            history = db.get_application_history(app["id"])
            
            for entry in history:
                st.markdown(f"""
                <div class="timeline-item">
                    <strong>{entry['action']}</strong><br/>
                    <small>By: {entry['performed_by_name']} | {entry['timestamp']}</small><br/>
                    {f"<em>{entry['comments']}</em>" if entry['comments'] else ""}
                </div>
                """, unsafe_allow_html=True)


# ============================================================================
# DECORATIONS REGISTER PAGE
# ============================================================================

def render_register():
    """Render the decorations register (completed applications)."""
    st.markdown("## 🏆 Decorations Register")
    st.markdown("Official register of awarded decorations and medals.")
    
    completed = db.get_completed_applications()
    
    if not completed:
        st.info("No decorations have been registered yet.")
        return
    
    st.markdown(f"Total registered awards: **{len(completed)}**")
    st.divider()
    
    # Display as a table
    for app in completed:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{app['employee_name']}**")
            st.markdown(f"*{app['organizational_unit']}*")
        
        with col2:
            st.markdown(f"🎖️ **{app['decoration_type']}**")
        
        with col3:
            st.markdown(f"📅 Awarded: **{app['award_grant_date']}**")
        
        with col4:
            if st.button("View", key=f"view_{app['id']}", use_container_width=True):
                st.session_state.selected_application = app["id"]
                st.session_state.page = "view_application"
                st.rerun()
        
        st.divider()


# ============================================================================
# VIEW APPLICATION PAGE
# ============================================================================

def render_view_application():
    """Render detailed view of an application."""
    app_id = st.session_state.selected_application
    
    if app_id is None:
        st.warning("No application selected.")
        return
    
    app = db.get_application_by_id(app_id)
    
    if app is None:
        st.error("Application not found.")
        return
    
    st.markdown(f"## 📄 Application Details")
    
    # Back button
    if st.button("← Back"):
        st.session_state.selected_application = None
        st.session_state.page = "all_applications"
        st.rerun()
    
    render_application_details(app)
    
    st.divider()
    
    # Show history
    st.markdown("### 📜 Complete Process History")
    history = db.get_application_history(app["id"])
    
    for entry in history:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{entry['action']}**")
                if entry['comments']:
                    st.markdown(f"*{entry['comments']}*")
            with col2:
                st.markdown(f"👤 {entry['performed_by_name']}")
                st.markdown(f"📅 {entry['timestamp']}")
            st.divider()


# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Initialize database
    db.initialize_database()
    
    # Check if user is logged in
    if st.session_state.current_user is None:
        render_login_page()
    else:
        # Render sidebar
        render_sidebar()
        
        # Route to appropriate page
        page = st.session_state.page
        
        if page == "dashboard":
            render_dashboard()
        elif page == "tasks":
            render_tasks_page()
        elif page == "new_application":
            render_new_application()
        elif page == "process_task":
            render_process_task()
        elif page == "all_applications":
            render_all_applications()
        elif page == "register":
            render_register()
        elif page == "view_application":
            render_view_application()
        else:
            render_dashboard()


# Run the application
if __name__ == "__main__":
    main()
