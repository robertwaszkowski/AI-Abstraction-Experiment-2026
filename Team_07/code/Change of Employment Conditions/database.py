import sqlite3
from datetime import datetime
import pandas as pd

DB_FILE = "employment_conditions.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT,
            proposed_conditions TEXT,
            change_justification TEXT,
            change_effective_date TEXT,
            is_academic_teacher BOOLEAN,
            
            head_of_ou_review_status TEXT,
            pd_review_status TEXT,
            kwe_financial_opinion TEXT,
            prk_opinion TEXT,
            prn_opinion TEXT,
            final_decision TEXT,
            
            process_status TEXT,
            current_task TEXT,
            assignee_role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if table is empty
    c.execute("SELECT COUNT(*) FROM applications")
    if c.fetchone()[0] == 0:
        samples = [
            ("Alice Academic", "Promotion to Professor", "Research Excellence", "2025-10-01", "In Progress", "Review application (PD)", "PD (Personnel Department)"),
            ("Bob Staff", "Change to Part-time", "Personal reasons", "2025-06-01", "In Progress", "Review application (Quartermaster)", "Quartermaster (KWE)"),
            ("Charlie Consultant", "Salary Increase", "Market Adjustment", "2025-05-01", "Completed", "Completed", None)
        ]
        
        for emp, cond, just, date, status, task, role in samples:
             c.execute('''
                INSERT INTO applications (
                    employee_name, proposed_conditions, change_justification, change_effective_date,
                    process_status, current_task, assignee_role
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (emp, cond, just, date, status, task, role))

    conn.commit()
    conn.close()

def create_application(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO applications (
            employee_name, proposed_conditions, change_justification, change_effective_date,
            process_status, current_task, assignee_role
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['employee_name'], data['proposed_conditions'], data['change_justification'], data['change_effective_date'],
        data['process_status'], data['current_task'], data['assignee_role']
    ))
    app_id = c.lastrowid
    conn.commit()
    conn.close()
    return app_id

def get_application(app_id):
    conn = get_connection()
    # Return as dictionary
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM applications WHERE id = ?', (app_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_application(app_id, updates):
    conn = get_connection()
    c = conn.cursor()
    
    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [app_id]
    
    c.execute(f'UPDATE applications SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()

def get_tasks_for_role(role):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM applications WHERE assignee_role = ?', (role,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_applications():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM applications", conn)
    conn.close()
    return df
