from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, HTTPException
import mysql.connector
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection setup
def get_db_connection():
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="Meatball#11",    
        database="primarycare"
    )
    return conn
# Fetch to get Today's Appointments View 
@app.get("/Appointments/")
def get_appointments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("select * " \
                    "from TodayAppointments;")
    appointments = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"appointments": appointments}

# Endpoint, Delete Button
@app.delete("/DeleteAppointment/{appID}")
def delete_appointment(appID: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM Appointments WHERE appID = %s", (appID,))

    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return 400 if deleted == 0 else 200

# Fetch View Billings for billings page
@app.get("billing/")
def get_all_billing():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary = True)
    cursor.execute = ("SELECT * FROM BillingInfo;")
    billings = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"billings": billings}

# Fetch View Patients for patients page
@app.get("/patients/")
def get_all_patients():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PatientsInfo;")
    patients = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"patients": patients}

# Get for Rooms availability TODAY
@app.get("/rooms/today")
def get_today_rooms():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM TodayRooms;")
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"rooms": rooms}


# Create Medical Records
@app.post("/medical-records/create")
async def create_medical_record(request: Request):
    data = await request.json()
    pID = data.get("pID")
    dID = data.get("dID")
    appID = data.get("appID")
    pmNotes = data.get("pmNotes")
    notes = data.get("notes")
    pmName = data.get("pmName")
    pmDosage = data.get("pmDosage")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO PrescribedMedicine (pmName, pmDosage, pmNotes) VALUES (%s, %s, %s)",
            (pmName, pmDosage, pmNotes),
        )
        medID = cursor.lastrowid

        cursor.execute(
            "INSERT INTO MedicalRecords (notes, medID, pID, dID, appID) VALUES (%s, %s, %s, %s, %s)",
            (notes, medID, pID, dID, appID),
        )

        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

# Add a New Patient
@app.post("/patients/create")
async def create_patient(request: Request):
    data = await request.json()
    pFullName = data.get("pFullName")
    pDob = data.get("pDob")
    pSex = data.get("pSex")
    pPhone = data.get("pPhone")
    pEmail = data.get("pEmail")
    pAddress = data.get("pAddress")
    providerName = data.get("providerName")
    pID = data.get("pID")
    hasInsurance = providerName is not None
    
    
    if not all([pFullName, pDob, pSex, pPhone, pEmail, pAddress]):
        return {"status": "error", "message": "Missing Required Fields"}

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO Patients (pFullName, pDob, pSex, pPhone, pEmail, pAddress) VALUES (%s, %s, %s, %s, %s, %s)",
            (pFullName, pDob, pSex, pPhone, pEmail, pAddress),
        )
        pID = cursor.lastrowid
        cursor.execute(
            "INSERT INTO PatientInsurance (pID, hasInsurance, providerName) VALUES (%s, %s, %s)",
            (pID, hasInsurance, providerName),
        )
        conn.commit()
        return {"status": "success", "message": "Patient Successfully Added"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

# Update a Patient
@app.post("/patient/update")
async def update_patient(request: Request):
    data = await request.json()
    pFullName = data.get("pFullName")
    pDob = data.get("pDob")
    pSex = data.get("pSex")
    pPhone = data.get("pPhone")
    pEmail = data.get("pEmail")
    pAddress = data.get("pAddress")
    providerName = data.get("providerName")
    pID = data.get("pID")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE Patients SET pFullName = s%, pDob = s%, pSex = s%, pPhone = s%, pEmail = s%, pAddress = s%, providerName = s%, pID = s%", (pFullName, pDob, pSex, pPhone, pEmail, pAddress, providerName, pID))

    conn.commit()
    conn.close()

    return {"status": "success", "message": f"{pFullName} {pID} updated successfully"}
