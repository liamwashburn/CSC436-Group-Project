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