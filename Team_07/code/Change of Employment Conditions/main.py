import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from process import ProcessEngine, ROLE_HEAD_OU, ROLE_PD, ROLE_KWE, ROLE_PRK, ROLE_PRN, ROLE_RECTOR, ROLE_CHANCELLOR
from process import TASK_REVIEW_HEAD_OU, TASK_REVIEW_PD, TASK_REVIEW_KWE, TASK_REVIEW_PRK, TASK_REVIEW_PRN, TASK_DECISION_RKR, TASK_DECISION_KAN, TASK_IMPLEMENT_PREPARE, TASK_HANDOVER_ARCHIVE, TASK_COMPLETED

# Initialize Engine
engine = ProcessEngine()

# Page Config
st.set_page_config(
    page_title="Change of Employment Conditions",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for "aideveloper" aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .task-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("📄 Change of Employment Conditions")
    st.markdown("**v1.0** | Workflow Management System")
    
    # Instrukcja obsługi
    with st.expander("📖 **INSTRUKCJA OBSŁUGI** - Kliknij aby rozwinąć", expanded=False):
        st.markdown("""
        ### Jak korzystać z aplikacji?
        
        **1. Wybierz rolę** w menu bocznym (User Role)
        
        **2. Dostępne role:**
        | Rola | Użytkownik | Zadanie |
        |------|------------|---------|
        | Head of O.U. | Holly Head | Składa wnioski |
        | Personnel Dept. | Penny Personnel | Weryfikuje, routing |
        | KWE | Quentin | Opinia finansowa |
        | PRK | Paula VREdu | Opinia (akademiccy) |
        | PRN | Peter VRSci | Opinia (akademiccy) |
        | Rector | Adam Rector | Decyzja finalna |
        | Chancellor | Chancellor | Decyzja (nieakademiccy) |
        
        **3. Przepływ pracy:**
        1. Head O.U. → składa wniosek (New Application)
        2. PD → weryfikuje i ustala typ pracownika
        3. KWE → opinia finansowa
        4. PRK/PRN lub Chancellor → opinie
        5. Rector/Chancellor → decyzja finalna
        6. PD → implementacja i archiwizacja
        
        **4. Presety danych:**
        - Wybierz preset i kliknij "Apply Preset"
        - Dostępne: Academic Teacher Promotion, Administrative Staff
        """)
    
    st.markdown("---")

    # Sidebar - Role Selection (Login Simulation)
    st.sidebar.header("User Role")
    roles = [ROLE_HEAD_OU, ROLE_PD, ROLE_KWE, ROLE_PRK, ROLE_PRN, ROLE_RECTOR, ROLE_CHANCELLOR]
    
    # Map roles to test users for display
    role_users = {
        ROLE_HEAD_OU: "Holly Head",
        ROLE_PD: "Penny Personnel",
        ROLE_KWE: "Quentin Quartermaster",
        ROLE_PRK: "Paula VREdu",
        ROLE_PRN: "Peter VRSci",
        ROLE_RECTOR: "Adam Rector",
        ROLE_CHANCELLOR: "Chancellor"
    }
    
    selected_role = st.sidebar.selectbox("Select Role to Login", roles)
    st.sidebar.info(f"Logged in as: **{role_users.get(selected_role, 'Unknown')}**")
    
    # Navigation
    menu = ["My Tasks", "All Applications"]
    if selected_role == ROLE_HEAD_OU:
        menu.insert(0, "New Application")
    
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "New Application":
        render_new_application_form()
    elif choice == "My Tasks":
        render_my_tasks(selected_role)
    elif choice == "All Applications":
        render_all_applications()

def render_new_application_form():
    st.header("Start New Application")
    
    # Presets
    presets = {
        "Select a preset...": {
            "name": "",
            "conditions": "",
            "justification": "",
            "date": datetime.today()
        },
        "Academic Teacher Promotion": {
            "name": "Alice Academic",
            "conditions": "Promotion to Senior Lecturer, Salary 8000 PLN",
            "justification": "Outstanding performance and new project responsibilities",
            "date": datetime.today() + timedelta(days=30)
        },
        "Administrative Staff Adjustment": {
            "name": "Bob Admin",
            "conditions": "Change to full-time, Salary 4500 PLN",
            "justification": "Increased workload requiring full-time availability",
            "date": datetime.today() + timedelta(days=14)
        }
    }
    
    selected_preset = st.selectbox("Load Preset Data", list(presets.keys()))
    
    # Initialize session state for form fields if not present or if preset changed
    if "form_name" not in st.session_state:
        st.session_state.form_name = ""
        st.session_state.form_conditions = ""
        st.session_state.form_justification = ""
        st.session_state.form_date = datetime.today()

    # Update session state if a real preset is selected (simple logic: if user selects something other than default)
    # To avoid overwriting user manual edits on every rerun, we could use a button "Load Preset"
    # or just react to the change. Let's use a button for clarity or just update when changed.
    # Better approach for Streamlit: Use `key` in widgets and update them via callback or checking state.
    # Let's use a button to apply the preset to avoid complex state management issues.
    
    if selected_preset != "Select a preset...":
        if st.button("Apply Preset"):
            data = presets[selected_preset]
            st.session_state.form_name = data["name"]
            st.session_state.form_conditions = data["conditions"]
            st.session_state.form_justification = data["justification"]
            st.session_state.form_date = data["date"]
            st.rerun()

    with st.form("new_app_form"):
        col1, col2 = st.columns(2)
        with col1:
            # Lista pracowników
            employees = [
                "Alice Academic", "Bob Admin", "Charlie Consultant", 
                "David Developer", "Eve Engineer", "Frank Finance",
                "Grace HR", "Henry Head"
            ]
            
            # Jeśli w presecie jest imię spoza listy, dodaj je tymczasowo
            current_name = st.session_state.get("form_name", "")
            if current_name and current_name not in employees:
                employees.append(current_name)
            
            employee_name = st.selectbox(
                "Employee Name", 
                options=employees,
                index=employees.index(current_name) if current_name in employees else None,
                key="input_name",
                placeholder="Select employee..."
            )
            change_effective_date = st.date_input("Change Effective Date", value=st.session_state.get("form_date", datetime.today()), key="input_date")
        with col2:
            proposed_conditions = st.text_area("Proposed Conditions", value=st.session_state.get("form_conditions", ""), placeholder="e.g. Promotion to Senior Lecturer, Salary 8000 PLN", key="input_conditions")
        
        change_justification = st.text_area("Change Justification", value=st.session_state.get("form_justification", ""), placeholder="e.g. Outstanding performance...", key="input_justification")
        
        submitted = st.form_submit_button("Submit Application")
        if submitted:
            if employee_name and proposed_conditions:
                engine.start_process(employee_name, proposed_conditions, change_justification, change_effective_date)
                st.success("Application submitted successfully! It has been assigned to you for initial review.")
                # Clear form
                st.session_state.form_name = ""
                st.session_state.form_conditions = ""
                st.session_state.form_justification = ""
                st.session_state.form_date = datetime.today()
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

def render_my_tasks(role):
    st.header(f"Tasks for {role}")
    tasks = engine.get_tasks(role)
    
    if not tasks:
        st.info("No pending tasks for this role.")
        return

    for task in tasks:
        with st.container():
            st.markdown(f"""
            <div class="task-card">
                <h3>{task['employee_name']}</h3>
                <p><strong>Task:</strong> {task['current_task']}</p>
                <p><strong>Status:</strong> {task['process_status']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Details & Action"):
                render_task_action(task, role)

def render_task_action(task, role):
    st.markdown("### Application Details")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Employee:** {task['employee_name']}")
        st.write(f"**Effective Date:** {task['change_effective_date']}")
        st.write(f"**Justification:** {task['change_justification']}")
    with col2:
        st.write(f"**Proposed Conditions:** {task['proposed_conditions']}")
        st.write(f"**Is Academic:** {task['is_academic_teacher'] if task['is_academic_teacher'] is not None else 'Pending'}")

    st.markdown("---")
    st.markdown("### Action")
    
    with st.form(f"task_form_{task['id']}"):
        form_data = {}
        
        if task['current_task'] == TASK_REVIEW_HEAD_OU:
            status = st.selectbox("Head of O.U. Review Status", ["Approved", "Rejected"])
            form_data['head_of_ou_review_status'] = status
            
        elif task['current_task'] == TASK_REVIEW_PD:
            status = st.selectbox("PD Review Status", ["Confirmed", "Rejected"])
            is_academic = st.checkbox("Is an Academic Teacher?", value=True)
            form_data['pd_review_status'] = status
            form_data['is_academic_teacher'] = is_academic
            
        elif task['current_task'] == TASK_REVIEW_KWE:
            opinion = st.selectbox("Financial Opinion", ["Funds Available", "No Funds"])
            form_data['kwe_financial_opinion'] = opinion
            
        elif task['current_task'] == TASK_REVIEW_PRK:
            opinion = st.selectbox("PRK Opinion", ["Approved", "Rejected"])
            form_data['prk_opinion'] = opinion
            
        elif task['current_task'] == TASK_REVIEW_PRN:
            opinion = st.selectbox("PRN Opinion", ["Approved", "Rejected"])
            form_data['prn_opinion'] = opinion
            
        elif task['current_task'] == TASK_DECISION_RKR:
            decision = st.selectbox("Final Decision (Rector)", ["Approved", "Rejected"])
            form_data['final_decision'] = decision
            
        elif task['current_task'] == TASK_DECISION_KAN:
            decision = st.selectbox("Final Decision (Chancellor)", ["Approved", "Rejected"])
            form_data['final_decision'] = decision
            
        elif task['current_task'] == TASK_IMPLEMENT_PREPARE:
            st.write("Checklist:")
            st.checkbox("Inform Head of O.U.", value=True, disabled=True)
            st.checkbox("Implement changes in HR system", value=True, disabled=True)
            st.checkbox("Prepare confirming documents", value=True, disabled=True)
            st.info("Confirm that all actions have been performed.")
            
        elif task['current_task'] == TASK_HANDOVER_ARCHIVE:
            st.write("Checklist:")
            st.checkbox("Hand over documents to employee", value=True, disabled=True)
            st.checkbox("Attach 1 copy to personnel files", value=True, disabled=True)
            st.info("Confirm archiving.")

        submitted = st.form_submit_button("Complete Task")
        if submitted:
            success, msg = engine.complete_task(task['id'], task['current_task'], form_data)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

def render_all_applications():
    st.header("All Applications History")
    import database as db
    df = db.get_all_applications()
    
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No applications found.")

if __name__ == "__main__":
    main()
