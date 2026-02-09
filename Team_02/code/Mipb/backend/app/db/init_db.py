
from sqlalchemy.orm import Session
from .models import User, Base
from .session import engine, SessionLocal

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

def init_db():
    db = SessionLocal()
    
    # Check if users exist
    if db.query(User).first():
        print("Users already seeded.")
        return

    users_data = [
        # Key Decision-Makers
        {"username": "adam.rector", "full_name": "Adam Rector", "role_name": "Rector (RKR)"},
        {"username": "carl.chancellor", "full_name": "Carl Chancellor", "role_name": "Chancellor (KAN)"},
        {"username": "paula.bredu", "full_name": "Paula VREdu", "role_name": "Vice-Rector for Education (PRK)"},
        {"username": "peter.vrsci", "full_name": "Peter VRSci", "role_name": "Vice-Rector for Scientific Affairs (PRN)"},
        
        # Departmental Roles
        {"username": "holly.head", "full_name": "Holly Head", "role_name": "Head of O.U."},
        {"username": "penny.personnel", "full_name": "Penny Personnel", "role_name": "PD (Personnel Department)"},
        {"username": "quentin.quartermaster", "full_name": "Quentin Quartermaster", "role_name": "Quartermaster (KWE)"},
        {"username": "mike.mpd", "full_name": "Mike MPD", "role_name": "MPD (Military Personnel Dept.)"},
        
        # Employee Personas (also act as Initiators/Requesters)
        {"username": "alice.academic", "full_name": "Alice Academic", "role_name": "Academic Teacher"},
        {"username": "nancy.nonacademic", "full_name": "Nancy NonAcademic", "role_name": "Non-Academic Employee"},
    ]

    for u in users_data:
        user = User(username=u["username"], full_name=u["full_name"], role_name=u["role_name"])
        db.add(user)
    
    db.commit()
    print("Users seeded successfully.")
    db.close()

if __name__ == "__main__":
    print("Initializing Database...")
    init_db()
