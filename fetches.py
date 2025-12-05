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

# Fetch to get Patient by ID
@app.get("/patients/{pID}")
def get_patient_by_id(pID: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT P.pID, P.pFullName, P.pAddress, P.pPhone, P.pEmail, PI.providerName AS pInsurance, P.pDob, PI.providerName FROM Patients P LEFT JOIN PatientInsurance PI ON P.pID = PI.pID WHERE P.pID = %s LIMIT 1", (pID,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()
    if not patient:
        return {"patients": []}
    return {"patients": [patient]}

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


# GET, View Billings for billings page
@app.get("/billing/")
def get_all_billing():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary = True)
    cursor.execute("SELECT * FROM BillingInfo;")
    billings = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"billings": billings}

#GET, View Billing Details for patients accounts that are frozen
@app.get("/billing/outstanding")
def get_all_billing():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary = True)
    cursor.execute("SELECT * FROM FrozenAccounts;")
    billings = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"billings": billings}

# GET, View Patients for patients page
@app.get("/patients/")
def get_all_patients():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PatientsInfo;")
    patients = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"patients": patients}

# GET, for Rooms availability TODAY
@app.get("/rooms/{date}")
def get_today_rooms(date: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT A.rID, A.appTime, R.rType, P.pFullName "
        "FROM Appointments A "
        "INNER JOIN Rooms R ON R.rID = A.rID "
        "INNER JOIN Patients P ON P.pID = A.pID "
        "WHERE DATE(A.appTime) = %s "
        "ORDER BY A.appTime ASC;",
        (date,)
    )
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"rooms": rooms}


# POST, Create/Update Medical Record and Update Billing
@app.post("/medical-records/create")
async def create_medical_record(request: Request):
    data = await request.json()

    appID = data.get("appID")
    notes = data.get("notes", "")
    bCost = data.get("bCost", 0)  # charged amount, 0 or 150

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT pID, dID 
            FROM Appointments
            WHERE appID = %s
        """, (appID,))
        appt = cursor.fetchone()

        if not appt:
            return {"status": "error", "message": "Invalid appID"}

        pID, dID = appt

        cursor.execute("""
            INSERT INTO MedicalRecords (notes, pID, dID, appID)
            VALUES (%s, %s, %s, %s)
        """, (notes, pID, dID, appID))

        cursor.execute("""
            SELECT bID, bCost FROM Billing
            WHERE pID = %s
        """, (pID,))
        billing = cursor.fetchone()

        if billing:
            bID, old_cost = billing
            new_cost = old_cost + bCost

            cursor.execute("""
                UPDATE Billing
                SET bCost = %s,
                    Paid = FALSE,
                    frozen = CASE WHEN %s >= 150 THEN TRUE ELSE FALSE END
                WHERE bID = %s
            """, (new_cost, new_cost, bID))

        else:
            cursor.execute("""
                INSERT INTO Billing (pID, appID, bCost, frozen, Paid)
                VALUES (%s, %s, %s, %s, FALSE)
            """, (pID, appID, bCost, bCost >= 150))

        cursor.execute("""
            UPDATE Appointments
            SET appCompleted = TRUE
            WHERE appID = %s
        """, (appID,))

        conn.commit()
        return {"status": "success"}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()  

# POST, Add/Insert a New Patient
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

# POST, Update Patient Information
@app.post("/patient/update")
async def update_patient(request: Request):
    data = await request.json()

    pID = data.get("pID")
    pFullName = data.get("pFullName")
    pDob = data.get("pDob")
    pPhone = data.get("pPhone")
    pEmail = data.get("pEmail")
    pAddress = data.get("pAddress")
    providerName = data.get("providerName")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Update Patients table
    cursor.execute("""
        UPDATE Patients 
        SET pFullName = %s, pDob = %s, pPhone = %s, pEmail = %s, pAddress = %s
        WHERE pID = %s
    """, (pFullName, pDob, pPhone, pEmail, pAddress, pID))

    # Check insurance exists
    cursor.execute("SELECT pID FROM PatientInsurance WHERE pID = %s", (pID,))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("""
            UPDATE PatientInsurance
            SET providerName = %s, hasInsurance = %s
            WHERE pID = %s
        """, (providerName, providerName != "None", pID))
    else:
        cursor.execute("""
            INSERT INTO PatientInsurance (pID, providerName, hasInsurance)
            VALUES (%s, %s, %s)
        """, (pID, providerName, providerName != "None"))

    conn.commit()

    cursor.close()
    conn.close()

    return {"status": "success", "message": "Patient updated successfully"}

# Return T/F to Check for Insurance
@app.get("/hasInsurance/{pID}")
async def hasInsurance(pID: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT hasInsurance FROM PatientInsurance WHERE pID = %s", (pID,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        return {"hasInsurance": False}
    else:
        return {"hasInsurance": bool(result["hasInsurance"])}


    
# GET, Fetch All Medical Records for a Specific Patient
# GET: Fetch all medical records with expanded appointment info
@app.get("/patients/{pID}/records")
async def get_patient_records(pID: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            mr.mrID,
            mr.notes AS pNotes,
            mr.appID,

            a.appTime,
            a.appReason,
            a.dID,
            a.rID,

            COALESCE(d.docName, 'Unknown Doctor') AS doctorName,
            COALESCE(d.docType, 'Unknown Specialty') AS doctorType,

            b.bID

        FROM MedicalRecords mr
        JOIN Appointments a ON mr.appID = a.appID
        LEFT JOIN Doctor d ON a.dID = d.dID
        LEFT JOIN Billing b ON b.pID = mr.pID

        WHERE mr.pID = %s
        ORDER BY a.appTime DESC
    """, (pID,))

    records = cursor.fetchall()
    conn.close()

    return {
        "records": records,
        "total": len(records)
    }

# -----------------------------------------
# 1) GET PATIENT LIST FOR AUTOCOMPLETE
# -----------------------------------------
@app.get("/patientslist/")
async def list_patients():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT pFullName FROM Patients ORDER BY pFullName")
    names = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return {"patients": names}


# -----------------------------------------
# 2) GET DOCTOR LIST FOR AUTOCOMPLETE
# -----------------------------------------
@app.get("/doctorslist")
async def list_doctors():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT docName FROM Doctor ORDER BY docName")
    names = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return {"doctors": names}


# Post, Reserve a Room/Appointment
@app.post("/reserve")
async def reserve_room(request: Request):
    data = await request.json()

    patient_name = data.get("patient")
    doctor_name = data.get("doctor")
    reason = data.get("reason")
    room_letter = data.get("room")
    time_slot = data.get("time")
    date = data.get("date")

    if not all([patient_name, doctor_name, reason, room_letter, time_slot, date]):
        return {"status": "error", "message": "Missing fields"}

    full_time = f"{date} {time_slot}:00"

    # Convert letter → rID
    room_map = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
    rID = room_map.get(room_letter)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get pID
    cursor.execute("SELECT pID FROM Patients WHERE pFullName = %s", (patient_name,))
    p = cursor.fetchone()
    if not p:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Patient not found"}
    pID = p[0]

    # Get dID
    cursor.execute("SELECT dID FROM Doctor WHERE docName = %s", (doctor_name,))
    d = cursor.fetchone()
    if not d:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Doctor not found"}
    dID = d[0]

    # Ensure room not already booked
    cursor.execute(
        "SELECT appID FROM Appointments WHERE appTime = %s AND rID = %s",
        (full_time, rID)
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Room already booked at this time"}

    # Ensure billing record exists
    cursor.execute("SELECT bID, bCost FROM Billing WHERE pID = %s", (pID,))
    billing = cursor.fetchone()

    if billing:
        bID, bCost = billing
        if bCost >= 150:
                cursor.close()
                conn.close()
                print("ACCOUNT FROZEN DUE TO OUTSTANDING BALANCE")
                return {"status": "error", "message": "Account frozen due to outstanding balance"}
    else:
        cursor.execute(
            "INSERT INTO Billing (bCost, frozen, pID, Paid) VALUES (0, FALSE, %s, FALSE)",
            (pID,)
        )
        bID = cursor.lastrowid

    cursor.execute("""
        INSERT INTO Appointments 
        (appTime, appReason, appType, pID, dID, rID, bID)
        VALUES (%s, %s, 'General', %s, %s, %s, %s)
    """, (full_time, reason, pID, dID, rID, bID))
    print("execute")

    conn.commit()

    cursor.close()
    conn.close()

    return {"status": "success", "message": "Reservation completed"}

@app.get("/patients/{pID}")
async def get_patient_by_id(pID: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT P.pID, P.pFullName, P.pAddress, P.pPhone, P.pEmail, PI.providerName AS pInsurance, P.pDob, PI.providerName FROM Patients P LEFT JOIN PatientInsurance PI ON P.pID = PI.pID WHERE P.pID = %s LIMIT 1", (pID,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()
    if not patient:
        return {"patients": []}
    return {"patients": [patient]}

# Get Pay off Bill
@app.post("/paybill/{bID}")
async def pay_bill(bID: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""UPDATE Billing SET Paid = TRUE, bCost = 0, frozen = FALSE WHERE bID = %s""", (bID,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": "Bill paid successfully"}


@app.get("/appointments/{appID}")
async def get_appointment_details(appID: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            a.appID,
            a.pID,
            a.dID,
            a.rID,                
            a.appTime,
            a.appReason,
            a.appCompleted,
            p.pFullName,
            p.pPhone,
            p.pEmail,
            d.docName,
            d.docType

            FROM Appointments a
            JOIN Patients p ON a.pID = p.pID
            JOIN Doctor d ON a.dID = d.dID

            WHERE a.appID = %s
        """, (appID,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return {"error": "Appointment not found"}

    return {"appointment": row}