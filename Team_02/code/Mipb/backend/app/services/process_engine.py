
from sqlalchemy.orm import Session
from app.db.models import ProcessInstance, Task, HistoryLog, User
import datetime

class ProcessEngine:
    def __init__(self, db: Session):
        self.db = db

    def start_process(self, process_key: str, user_id: int, initial_data: dict):
        # Create Instance
        instance = ProcessInstance(
            process_definition_key=process_key,
            requester_id=user_id,
            variables=initial_data,
            status="ACTIVE"
        )
        self.db.add(instance)
        self.db.flush() # get ID

        # Log History
        self.log_history(instance.id, None, user_id, "START_PROCESS", "Process started")

        # Determine First Task
        if process_key == "leave_request":
             # Start -> Head of O.U.
             self.create_task(instance.id, "Task_ReviewAndForward_HeadOU", "Review and approve leave request", role="Head of O.U.")
        
        elif process_key == "change_employment":
            # Start -> Head of O.U.
            self.create_task(instance.id, "Task_ReviewAndForward_HeadOU", "Review and forward application to PD", role="Head of O.U.")
            
        elif process_key == "decorations":
            # Start -> Submit (Head OU) - Automatic submission via Start Form
            # We skip creating "Task_SubmitApplication" because the user just filled it in StartProcess.
            # Directly move to the next step: Present for Acceptance (PD)
            self.create_task(instance.id, "Task_PresentApplicationsForAcceptance", "Present applications for acceptance (PRK/Chancellor)", role="PD (Personnel Department)")

        self.db.commit()
        return instance

    def complete_task(self, task_id: int, user_id: int, data: dict):
        task = self.db.query(Task).get(task_id)
        if not task:
            raise Exception("Task not found")
        
        instance = self.db.query(ProcessInstance).get(task.process_instance_id)
        
        # Update Variables
        current_vars = dict(instance.variables) if instance.variables else {}
        current_vars.update(data)
        instance.variables = current_vars
        
        # Log History
        self.log_history(instance.id, task.id, user_id, "COMPLETE_TASK", f"Completed {task.name}", str(data))
        
        # Mark Task Completed
        task.status = "COMPLETED"
        
        # Calculate Next Step
        self.route_process(instance, task.task_definition_key)
        
        self.db.commit()
        return instance

    def create_task(self, instance_id, task_key, name, role=None, user_id=None):
        new_task = Task(
            process_instance_id=instance_id,
            task_definition_key=task_key,
            name=name,
            assignee_role=role,
            assignee_user_id=user_id,
            status="PENDING"
        )
        self.db.add(new_task)
        return new_task

    def log_history(self, instance_id, task_id, user_id, action, comment, details=None):
        # Fetch user name for snapshot
        user_name = "System"
        if user_id:
            u = self.db.query(User).get(user_id)
            if u: user_name = u.full_name

        log = HistoryLog(
            process_instance_id=instance_id,
            task_id=task_id,
            user_id=user_id,
            user_name=user_name,
            action=action,
            comment=f"{comment} {details if details else ''}"
        )
        self.db.add(log)

    def route_process(self, instance, completed_task_key):
        vars = instance.variables
        
        # --- Leave Request Logic ---
        if instance.process_definition_key == "leave_request":
            if completed_task_key == "Task_ReviewAndForward_HeadOU":
                self.create_task(instance.id, "Task_ReviewApplication_PD", "Review leave request (check entitlement)", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_ReviewApplication_PD":
                # Gateway: IsAcademicTeacher
                is_academic = vars.get("is_academic", False) # Boolean from form
                if is_academic:
                    self.create_task(instance.id, "Task_Review_PRK", "Review application (PRK) and forward to PRN", role="Vice-Rector for Education (PRK)")
                else:
                    self.create_task(instance.id, "Task_MakeDecision_Chancellor", "Make decision (KAN) and return to PD", role="Chancellor (KAN)")
            
            elif completed_task_key == "Task_Review_PRK":
                self.create_task(instance.id, "Task_Review_PRN", "Review application (PRN) and forward to Rector", role="Vice-Rector for Scientific Affairs (PRN)")
            
            elif completed_task_key == "Task_Review_PRN":
                self.create_task(instance.id, "Task_MakeDecision_RKR", "Make decision (RKR) and return to PD", role="Rector (RKR)")
            
            elif completed_task_key in ["Task_MakeDecision_RKR", "Task_MakeDecision_Chancellor"]:
                # Join Gateway -> Inform Head OU
                self.create_task(instance.id, "Task_InformHeadOU", "Inform Head of O.U. about the decision", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_InformHeadOU":
                self.create_task(instance.id, "Task_ImplementChanges", "Register leave in HR system", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_ImplementChanges":
                self.end_process(instance, "COMPLETED")

        # --- Change of Employment Logic ---
        elif instance.process_definition_key == "change_employment":
            if completed_task_key == "Task_ReviewAndForward_HeadOU":
                self.create_task(instance.id, "Task_ReviewApplication_PD", "Review application (PD)", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_ReviewApplication_PD":
                 self.create_task(instance.id, "Task_Review_KWE", "Review application (Quartermaster)", role="Quartermaster (KWE)")
            
            elif completed_task_key == "Task_Review_KWE":
                is_academic = vars.get("is_academic", True) # Default true per doc?
                if is_academic:
                     self.create_task(instance.id, "Task_Review_PRK", "Review application (PRK) and forward to PRN", role="Vice-Rector for Education (PRK)")
                else:
                     self.create_task(instance.id, "Task_MakeDecision_Chancellor", "Make decision (KAN) and return to PD", role="Chancellor (KAN)")
            
            elif completed_task_key == "Task_Review_PRK":
                self.create_task(instance.id, "Task_Review_PRN", "Review application (PRN) and forward to Rector", role="Vice-Rector for Scientific Affairs (PRN)")

            elif completed_task_key == "Task_Review_PRN":
                 self.create_task(instance.id, "Task_MakeDecision_RKR", "Make decision (RKR) and return to PD", role="Rector (RKR)")

            elif completed_task_key in ["Task_MakeDecision_RKR", "Task_MakeDecision_Chancellor"]:
                self.create_task(instance.id, "Task_ImplementAndPrepare", "Implement, Prepare, and Inform", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_ImplementAndPrepare":
                self.create_task(instance.id, "Task_HandOverAndArchive", "Hand Over Documents and Archive", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_HandOverAndArchive":
                self.end_process(instance, "COMPLETED")

        # --- Decorations Logic ---
        elif instance.process_definition_key == "decorations":
            if completed_task_key == "Task_SubmitApplication":
                 self.create_task(instance.id, "Task_PresentApplicationsForAcceptance", "Present applications for acceptance (PRK/Chancellor)", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_PresentApplicationsForAcceptance":
                self.create_task(instance.id, "Task_ReviewApplications", "Review applications and forward to PD", role="Vice-Rector for Education (PRK)") # Or Chancellor? Scenario says PRK/Chancellor role. Used PRK user in scenario.
            
            elif completed_task_key == "Task_ReviewApplications":
                self.create_task(instance.id, "Task_PresentApplicationsToRKR", "Present reviewed applications to Rector", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_PresentApplicationsToRKR":
                self.create_task(instance.id, "Task_MakeDecision", "Make decision", role="Rector (RKR)")
            
            elif completed_task_key == "Task_MakeDecision":
                decision = vars.get("rkr_decision", "Rejected")
                if decision == "Accepted":
                    self.create_task(instance.id, "Task_ForwardApplicationsToMPD", "Forward accepted applications to MPD", role="PD (Personnel Department)")
                else:
                    self.end_process(instance, "REJECTED")
            
            elif completed_task_key == "Task_ForwardApplicationsToMPD":
                 self.create_task(instance.id, "Task_HandleApplicationsExternal", "Handle applications (external transfer)", role="MPD (Military Personnel Dept.)")
            
            elif completed_task_key == "Task_HandleApplicationsExternal":
                 self.create_task(instance.id, "Task_ReceiveDecision", "Receive decision on award", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_ReceiveDecision":
                 self.create_task(instance.id, "Task_EnterToRegister", "Enter decoration into register", role="PD (Personnel Department)")
            
            elif completed_task_key == "Task_EnterToRegister":
                 self.end_process(instance, "COMPLETED")

    def end_process(self, instance, status):
        instance.status = status
        self.log_history(instance.id, None, None, "END_PROCESS", f"Process ended with status {status}")

