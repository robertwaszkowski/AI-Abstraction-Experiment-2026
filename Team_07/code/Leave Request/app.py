# -*- coding: utf-8 -*-
"""
===============================================================================
LEAVE REQUEST APPLICATION - MAIN STREAMLIT APP
===============================================================================
aideveloper
Leave Request Application v1.0

Aplikacja do zarządzania wnioskami urlopowymi (DPE/1-3) z interfejsem 
użytkownika opartym na Streamlit. Implementuje pełny workflow BPMN z 
rozróżnieniem ścieżek dla nauczycieli akademickich i pracowników 
nieakademickich.

Autor: aideveloper
Wersja: 1.0
===============================================================================
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Optional

# Import modułów aplikacji
from database import (
    Roles,
    WorkflowStates,
    init_database,
    get_all_users,
    create_leave_request,
    get_leave_request,
    get_all_leave_requests,
    get_pending_requests_for_role,
    get_workflow_history,
    get_statistics
)
from workflow import (
    get_state_description,
    get_task_name,
    get_available_decisions,
    get_required_fields,
    process_task,
    can_process_task
)


# =============================================================================
# KONFIGURACJA STRONY
# =============================================================================

st.set_page_config(
    page_title="Leave Request System (DPE/1-3)",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# STYLE CSS
# =============================================================================

st.markdown("""
<style>
    /* Główny kontener */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(120deg, #1e3a5f 0%, #2d5a87 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Karty zadań */
    .task-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e9ecef;
        border-left: 4px solid #2d5a87;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .task-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-approved {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-rejected {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .status-completed {
        background-color: #cce5ff;
        color: #004085;
    }
    
    /* Timeline */
    .timeline-item {
        position: relative;
        padding-left: 30px;
        padding-bottom: 20px;
        border-left: 2px solid #2d5a87;
        margin-left: 10px;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -8px;
        top: 0;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background-color: #2d5a87;
        border: 2px solid #fff;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2d5a87;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* Form styling */
    .stForm {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    
    /* Role indicator */
    .role-indicator {
        background: linear-gradient(120deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 500;
        display: inline-block;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# INICJALIZACJA SESSION STATE
# =============================================================================

def init_session_state():
    """Inicjalizuje zmienne sesji."""
    if 'current_role' not in st.session_state:
        st.session_state.current_role = Roles.EMPLOYEE
    if 'selected_request_id' not in st.session_state:
        st.session_state.selected_request_id = None
    if 'view' not in st.session_state:
        st.session_state.view = 'dashboard'


# =============================================================================
# SIDEBAR - WYBÓR ROLI
# =============================================================================

def render_sidebar():
    """Renderuje sidebar z wyborem roli i nawigacją."""
    with st.sidebar:
        st.markdown("### 🏛️ MUT Leave Request System")
        st.markdown("**DPE/1-3: Leave Request Process**")
        
        # Instrukcja obsługi
        with st.expander("📖 INSTRUKCJA", expanded=False):
            st.markdown("""
            **Jak korzystać:**
            
            1. **Wybierz rolę** z listy poniżej
            2. **Employee** - składa wnioski
            3. Pozostałe role - przetwarzają
            
            **Przepływ pracy:**
            - Nauczyciel akademicki:
              Head O.U. → PD → PRK → PRN → Rector
            - Pracownik nieakademicki:
              Head O.U. → PD → Chancellor
            
            **Nawigacja:**
            - 📋 Dashboard - zadania
            - ➕ Nowy wniosek (Employee)
            - 📜 Wszystkie wnioski
            """)
        st.divider()
        
        # Wybór roli (symulacja logowania)
        st.markdown("#### 👤 Wybierz rolę:")
        selected_role = st.selectbox(
            "Zalogowany jako:",
            options=Roles.all_roles(),
            index=Roles.all_roles().index(st.session_state.current_role),
            key="role_selector"
        )
        
        if selected_role != st.session_state.current_role:
            st.session_state.current_role = selected_role
            st.session_state.view = 'dashboard'
            st.rerun()
        
        st.markdown(f"""
        <div class="role-indicator">
            🎭 {st.session_state.current_role}
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Statystyki
        stats = get_statistics()
        st.markdown("#### 📊 Statystyki:")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Łącznie", stats['total_requests'])
            st.metric("Oczekujące", stats['pending'])
        with col2:
            st.metric("Zakończone", stats['completed'])
            st.metric("Odrzucone", stats['rejected'])
        
        st.divider()
        
        # Nawigacja
        st.markdown("#### 🧭 Nawigacja:")
        
        if st.button("📋 Dashboard", use_container_width=True):
            st.session_state.view = 'dashboard'
            st.session_state.selected_request_id = None
            st.rerun()
        
        if st.session_state.current_role == Roles.EMPLOYEE:
            if st.button("➕ Nowy wniosek", use_container_width=True):
                st.session_state.view = 'new_request'
                st.rerun()
        
        if st.button("📜 Wszystkie wnioski", use_container_width=True):
            st.session_state.view = 'all_requests'
            st.session_state.selected_request_id = None
            st.rerun()


# =============================================================================
# FORMULARZ NOWEGO WNIOSKU
# =============================================================================

def render_new_request_form():
    """Renderuje formularz składania nowego wniosku urlopowego."""
    st.markdown('<h1 class="main-header">📝 Nowy Wniosek Urlopowy</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Formularz 23/DPE - Leave Request Form</p>', unsafe_allow_html=True)
    
    with st.form("leave_request_form", clear_on_submit=True):
        st.markdown("### 👤 Dane pracownika")
        col1, col2 = st.columns(2)
        
        # Przygotowanie listy pracowników
        users = get_all_users()
        user_names = [u['full_name'] for u in users] if users else []
        # Dodatkowe przykładowe dane jeśli lista jest krótka
        sample_employees = ["Jan Kowalski", "Anna Nowak", "Piotr Wiśniewski", "Maria Wójcik"]
        candidate_names = sorted(list(set(user_names + sample_employees)))
        
        with col1:
            employee_name = st.selectbox(
                "Imię i nazwisko *",
                options=candidate_names,
                index=None,
                placeholder="Wybierz pracownika"
            )
            employee_position = st.text_input(
                "Stanowisko *",
                placeholder="np. Professor, Assistant"
            )
        
        with col2:
            is_academic = st.selectbox(
                "Typ pracownika *",
                options=["Nauczyciel akademicki", "Pracownik nieakademicki"],
                index=0
            )
            leave_balance = st.number_input(
                "Pozostałe dni urlopu",
                min_value=0,
                max_value=50,
                value=26
            )
        
        st.markdown("### 🗓️ Szczegóły urlopu")
        col3, col4 = st.columns(2)
        
        with col3:
            leave_type = st.selectbox(
                "Typ urlopu *",
                options=[
                    "Recreational (wypoczynkowy)",
                    "Childcare (opieka nad dzieckiem)",
                    "Exceptional Circumstance (okolicznościowy)",
                    "Unpaid (bezpłatny)",
                    "Training (szkoleniowy)",
                    "Other (inny)"
                ]
            )
            leave_start = st.date_input(
                "Data rozpoczęcia *",
                value=date.today() + timedelta(days=7),
                min_value=date.today()
            )
        
        with col4:
            leave_substitute = st.selectbox(
                "Osoba zastępująca (opcjonalnie)",
                options=["Brak"] + candidate_names,
                index=0
            )
            leave_end = st.date_input(
                "Data zakończenia *",
                value=date.today() + timedelta(days=14),
                min_value=date.today()
            )
        
        # Obliczenie liczby dni
        if leave_end >= leave_start:
            duration = (leave_end - leave_start).days + 1
        else:
            duration = 0
        
        st.info(f"📅 Liczba dni urlopu: **{duration}** dni")
        
        if duration > leave_balance:
            st.warning(f"⚠️ Uwaga: Wnioskowana liczba dni ({duration}) przekracza dostępne saldo ({leave_balance})!")
        
        st.divider()
        
        submitted = st.form_submit_button(
            "📤 Złóż wniosek",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # Walidacja
            if not employee_name or not employee_position:
                st.error("❌ Proszę wypełnić wszystkie wymagane pola!")
            elif duration <= 0:
                st.error("❌ Data zakończenia musi być po dacie rozpoczęcia!")
            else:
                # Utworzenie wniosku
                is_academic_bool = (is_academic == "Nauczyciel akademicki")
                
                request_id = create_leave_request(
                    employee_name=employee_name,
                    employee_position=employee_position,
                    leave_type=leave_type.split(" (")[0],  # Tylko angielska nazwa
                    leave_start_date=leave_start.strftime("%Y-%m-%d"),
                    leave_end_date=leave_end.strftime("%Y-%m-%d"),
                    leave_duration_days=duration,
                    leave_substitute=leave_substitute if leave_substitute else None,
                    is_academic_teacher=is_academic_bool,
                    employee_leave_balance=leave_balance
                )
                
                st.success(f"✅ Wniosek został złożony pomyślnie! Numer wniosku: **#{request_id}**")
                st.info("ℹ️ Wniosek został przekazany do Kierownika Jednostki Organizacyjnej (Head of O.U.) do zatwierdzenia.")
                
                # Powrót do dashboard
                st.session_state.view = 'dashboard'
                st.rerun()


# =============================================================================
# DASHBOARD - LISTA ZADAŃ
# =============================================================================

def render_dashboard():
    """Renderuje główny dashboard z listą zadań dla aktualnej roli."""
    role = st.session_state.current_role
    
    st.markdown(f'<h1 class="main-header">📋 Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">Zadania do wykonania dla roli: {role}</p>', unsafe_allow_html=True)
    
    # Pobierz zadania dla roli
    pending_requests = get_pending_requests_for_role(role)
    
    if not pending_requests:
        st.info("🎉 Brak zadań do wykonania. Wszystkie wnioski zostały przetworzone!")
        return
    
    st.markdown(f"### 📬 Oczekujące zadania ({len(pending_requests)})")
    
    for req in pending_requests:
        render_task_card(req)


def render_task_card(request: dict):
    """Renderuje kartę pojedynczego zadania."""
    state = request['current_state']
    task_name = get_task_name(state)
    state_desc = get_state_description(state)
    
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="task-card">
                <strong>📌 Wniosek #{request['id']}</strong><br>
                <span style="color: #6c757d;">👤 {request['employee_name']} - {request['employee_position']}</span><br>
                <strong>📋 Zadanie:</strong> {task_name}<br>
                <span style="color: #495057;">📅 {request['leave_start_date']} → {request['leave_end_date']} ({request['leave_duration_days']} dni)</span><br>
                <span style="color: #17a2b8;">🏷️ Typ: {request['leave_type']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            is_academic = "✅ Tak" if request['is_academic_teacher'] else "❌ Nie"
            st.markdown(f"""
            **Status:** {state_desc}<br>
            **Nauczyciel akad.:** {is_academic}<br>
            **Saldo urlopu:** {request['employee_leave_balance']} dni
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("🔍 Przetwórz", key=f"process_{request['id']}", use_container_width=True):
                st.session_state.selected_request_id = request['id']
                st.session_state.view = 'process_task'
                st.rerun()
            
            if st.button("📜 Historia", key=f"history_{request['id']}", use_container_width=True):
                st.session_state.selected_request_id = request['id']
                st.session_state.view = 'view_history'
                st.rerun()


# =============================================================================
# PRZETWARZANIE ZADANIA
# =============================================================================

def render_process_task():
    """Renderuje formularz przetwarzania zadania."""
    request_id = st.session_state.selected_request_id
    
    if not request_id:
        st.error("Nie wybrano wniosku!")
        return
    
    request = get_leave_request(request_id)
    if not request:
        st.error("Wniosek nie został znaleziony!")
        return
    
    role = st.session_state.current_role
    state = request['current_state']
    task_name = get_task_name(state)
    
    # Sprawdź uprawnienia
    if not can_process_task(role, state):
        st.error(f"❌ Nie masz uprawnień do przetworzenia tego zadania. Wymagana rola: {request['current_assignee_role']}")
        return
    
    st.markdown(f'<h1 class="main-header">⚙️ Przetwarzanie zadania</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{task_name}</p>', unsafe_allow_html=True)
    
    # Informacje o wniosku
    with st.expander("📋 Szczegóły wniosku", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Numer wniosku:** #{request['id']}  
            **Pracownik:** {request['employee_name']}  
            **Stanowisko:** {request['employee_position']}  
            **Typ urlopu:** {request['leave_type']}  
            """)
        
        with col2:
            is_academic = "✅ Tak" if request['is_academic_teacher'] else "❌ Nie"
            st.markdown(f"""
            **Okres:** {request['leave_start_date']} → {request['leave_end_date']}  
            **Liczba dni:** {request['leave_duration_days']}  
            **Osoba zastępująca:** {request['leave_substitute'] or 'Nie wskazano'}  
            **Nauczyciel akademicki:** {is_academic}  
            **Saldo urlopu:** {request['employee_leave_balance']} dni
            """)
        
        # Poprzednie decyzje
        if request['head_ou_decision']:
            st.info(f"📝 **Decyzja Head of O.U.:** {request['head_ou_decision']}")
        if request['pd_review_status']:
            st.info(f"📝 **Status PD:** {request['pd_review_status']}")
        if request['prk_review_status']:
            st.info(f"📝 **Status PRK:** {request['prk_review_status']}")
        if request['prn_review_status']:
            st.info(f"📝 **Status PRN:** {request['prn_review_status']}")
    
    # Formularz decyzji
    st.markdown("### ✍️ Podjęcie decyzji")
    
    with st.form("decision_form"):
        update_fields = {}
        
        # Dostępne decyzje zależne od stanu
        decisions = get_available_decisions(state)
        decision = st.selectbox("Decyzja *", options=decisions)
        
        # Specjalne pola dla PD - ustawienie is_academic_teacher
        if state == WorkflowStates.PD_REVIEW:
            st.markdown("#### 🔀 Routing wniosku")
            is_academic_choice = st.radio(
                "Czy pracownik jest nauczycielem akademickim? *",
                options=["Tak (ścieżka PRK → PRN → Rector)", "Nie (ścieżka Chancellor)"],
                index=0 if request['is_academic_teacher'] else 1
            )
            update_fields['is_academic_teacher'] = is_academic_choice.startswith("Tak")
            update_fields['pd_review_status'] = decision
        
        # Pola decyzji dla poszczególnych stanów
        if state == WorkflowStates.HEAD_OU_REVIEW:
            update_fields['head_ou_decision'] = decision
        elif state == WorkflowStates.PRK_REVIEW:
            update_fields['prk_review_status'] = decision
        elif state == WorkflowStates.PRN_REVIEW:
            update_fields['prn_review_status'] = decision
        elif state in [WorkflowStates.RECTOR_DECISION, WorkflowStates.CHANCELLOR_DECISION]:
            update_fields['final_decision'] = decision
            update_fields['final_decision_maker'] = "Rector" if state == WorkflowStates.RECTOR_DECISION else "Chancellor"
        
        # Notatki
        notes = st.text_area(
            "Notatki (opcjonalnie)",
            placeholder="Dodatkowe uwagi lub komentarze..."
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button(
                "✅ Zatwierdź i prześlij dalej",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            cancelled = st.form_submit_button(
                "❌ Anuluj",
                use_container_width=True
            )
        
        if submitted:
            success, message = process_task(
                request_id=request_id,
                performed_by_role=role,
                decision=decision,
                notes=notes if notes else None,
                update_fields=update_fields
            )
            
            if success:
                st.success(f"✅ {message}")
                st.session_state.view = 'dashboard'
                st.session_state.selected_request_id = None
                st.rerun()
            else:
                st.error(f"❌ {message}")
        
        if cancelled:
            st.session_state.view = 'dashboard'
            st.session_state.selected_request_id = None
            st.rerun()


# =============================================================================
# HISTORIA WORKFLOW
# =============================================================================

def render_history():
    """Renderuje historię workflow dla wybranego wniosku."""
    request_id = st.session_state.selected_request_id
    
    if not request_id:
        st.error("Nie wybrano wniosku!")
        return
    
    request = get_leave_request(request_id)
    if not request:
        st.error("Wniosek nie został znaleziony!")
        return
    
    st.markdown(f'<h1 class="main-header">📜 Historia wniosku #{request_id}</h1>', unsafe_allow_html=True)
    
    # Informacje o wniosku
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pracownik", request['employee_name'])
    with col2:
        st.metric("Status", get_state_description(request['current_state']))
    with col3:
        st.metric("Typ urlopu", request['leave_type'])
    
    st.divider()
    
    # Timeline
    history = get_workflow_history(request_id)
    
    if not history:
        st.info("Brak historii dla tego wniosku.")
        return
    
    st.markdown("### 📅 Timeline procesu")
    
    for entry in history:
        with st.container():
            st.markdown(f"""
            <div class="timeline-item">
                <strong>📌 {entry['action']}</strong><br>
                <span style="color: #6c757d;">🕐 {entry['created_at']}</span><br>
                <span>🎭 Rola: {entry['performed_by_role']}</span><br>
                {f"<span>✅ Decyzja: <strong>{entry['decision']}</strong></span><br>" if entry['decision'] else ""}
                {f"<span style='color: #495057;'>📝 {entry['notes']}</span>" if entry['notes'] else ""}
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("⬅️ Powrót do Dashboard", use_container_width=True):
        st.session_state.view = 'dashboard'
        st.session_state.selected_request_id = None
        st.rerun()


# =============================================================================
# LISTA WSZYSTKICH WNIOSKÓW
# =============================================================================

def render_all_requests():
    """Renderuje listę wszystkich wniosków urlopowych."""
    st.markdown('<h1 class="main-header">📚 Wszystkie wnioski</h1>', unsafe_allow_html=True)
    
    requests = get_all_leave_requests()
    
    if not requests:
        st.info("Brak wniosków w systemie.")
        return
    
    # Filtrowanie
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filtruj po statusie:",
            options=["Wszystkie", "Oczekujące", "Zakończone", "Odrzucone"]
        )
    
    with col2:
        type_filter = st.selectbox(
            "Filtruj po typie:",
            options=["Wszystkie"] + list(set(r['leave_type'] for r in requests))
        )
    
    with col3:
        search = st.text_input("Szukaj po nazwisku:", placeholder="np. Kowalski")
    
    # Filtrowanie danych
    filtered = requests
    
    if status_filter == "Oczekujące":
        filtered = [r for r in filtered if r['current_state'] not in [WorkflowStates.COMPLETED, WorkflowStates.REJECTED]]
    elif status_filter == "Zakończone":
        filtered = [r for r in filtered if r['current_state'] == WorkflowStates.COMPLETED]
    elif status_filter == "Odrzucone":
        filtered = [r for r in filtered if r['current_state'] == WorkflowStates.REJECTED]
    
    if type_filter != "Wszystkie":
        filtered = [r for r in filtered if r['leave_type'] == type_filter]
    
    if search:
        filtered = [r for r in filtered if search.lower() in r['employee_name'].lower()]
    
    st.markdown(f"**Znaleziono:** {len(filtered)} wniosków")
    st.divider()
    
    # Wyświetlanie jako tabela
    for req in filtered:
        state = req['current_state']
        state_desc = get_state_description(state)
        
        # Kolor statusu
        if state == WorkflowStates.COMPLETED:
            status_class = "status-approved"
        elif state == WorkflowStates.REJECTED:
            status_class = "status-rejected"
        else:
            status_class = "status-pending"
        
        is_academic = "✅" if req['is_academic_teacher'] else "❌"
        
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.markdown(f"""
                **#{req['id']}** - {req['employee_name']}  
                {req['employee_position']}
                """)
            
            with col2:
                st.markdown(f"""
                📅 {req['leave_start_date']} → {req['leave_end_date']}  
                🏷️ {req['leave_type']} ({req['leave_duration_days']} dni)
                """)
            
            with col3:
                st.markdown(f"""
                <span class="status-badge {status_class}">{state_desc}</span><br>
                Akad.: {is_academic}
                """, unsafe_allow_html=True)
            
            with col4:
                if st.button("📜", key=f"all_hist_{req['id']}", help="Zobacz historię"):
                    st.session_state.selected_request_id = req['id']
                    st.session_state.view = 'view_history'
                    st.rerun()
            
            st.divider()


# =============================================================================
# GŁÓWNA FUNKCJA
# =============================================================================

def main():
    """Główna funkcja aplikacji."""
    # Inicjalizacja
    init_database()
    init_session_state()
    
    # Renderuj sidebar
    render_sidebar()
    
    # Renderuj główny content w zależności od widoku
    view = st.session_state.view
    
    if view == 'dashboard':
        render_dashboard()
    elif view == 'new_request':
        render_new_request_form()
    elif view == 'process_task':
        render_process_task()
    elif view == 'view_history':
        render_history()
    elif view == 'all_requests':
        render_all_requests()
    else:
        render_dashboard()


# =============================================================================
# URUCHOMIENIE APLIKACJI
# =============================================================================

if __name__ == "__main__":
    main()
