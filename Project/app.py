import email
from operator import ge
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="D3lph1nuSQL!",
    database="haprs"
)

cursor = db.cursor(dictionary=True)
schema_cursor = db.cursor()

with open("schema.sql", "r") as file:
    sql_script = file.read()

sql_script = sql_script.replace("delimiter $$", "")
sql_script = sql_script.replace("delimiter ;", "")

statements = sql_script.split("$$")

for statement in statements:
    stmt = statement.strip()

    if stmt:
        try:
            schema_cursor.execute(stmt)

            while schema_cursor.nextset():
                pass

        except Exception as e:
            print(e)

db.commit()

schema_cursor.close()

def seed_data():
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) AS count FROM Patient")
    result = cursor.fetchone()

    if result['count'] > 0:
        print("Sample data already exists.")
        return

    sql = """

    INSERT INTO Specialization (specializationName) VALUES
    ('Cardiology'),
    ('Neurology'),
    ('Orthopedics'),
    ('Dermatology'),
    ('Pediatrics');

    INSERT INTO Doctor (name, sid, phone, email, room, availability_schedule) VALUES
    ('Dr. Raj Sharma', 1, '9876543210', 'raj.sharma@haprs.com', 101, 'Mon-Fri 9AM-1PM'),
    ('Dr. Meera Kapoor', 2, '9876543211', 'meera.kapoor@haprs.com', 102, 'Mon-Wed 2PM-6PM'),
    ('Dr. Arjun Singh', 3, '9876543212', 'arjun.singh@haprs.com', 103, 'Tue-Sat 10AM-4PM'),
    ('Dr. Priya Nair', 4, '9876543213', 'priya.nair@haprs.com', 104, 'Mon-Fri 11AM-5PM'),
    ('Dr. Aman Verma', 5, '9876543214', 'aman.verma@haprs.com', 105, 'Daily 9AM-12PM');

    INSERT INTO Patient
    (firstName, lastName, dob, gender, phone, email, address, bloodgrp, insuranceID, registrationDate)
    VALUES
    ('Rahul', 'Mehta', '1998-05-12', 'Male', '9991110001', 'rahul@gmail.com', 'Delhi', 'A+', 'INS1001', '2026-05-01'),
    ('Sneha', 'Verma', '2001-08-21', 'Female', '9991110002', 'sneha@gmail.com', 'Noida', 'B+', 'INS1002', '2026-05-02'),
    ('Amit', 'Sharma', '1995-01-14', 'Male', '9991110003', 'amit@gmail.com', 'Gurgaon', 'O+', 'INS1003', '2026-05-03'),
    ('Pooja', 'Nair', '1999-09-10', 'Female', '9991110004', 'pooja@gmail.com', 'Faridabad', 'AB+', 'INS1004', '2026-05-04'),
    ('Karan', 'Singh', '1997-11-30', 'Male', '9991110005', 'karan@gmail.com', 'Ghaziabad', 'A-', 'INS1005', '2026-05-05');

    INSERT INTO Appointment
    (pid, did, aptDate, aptTime, status, reasonForVisit)
    VALUES
    (1, 1, '2026-05-10', '10:00:00', 'Completed', 'Chest pain'),
    (2, 2, '2026-05-10', '11:00:00', 'Not Completed', 'Migraine'),
    (3, 3, '2026-05-11', '12:30:00', 'Completed', 'Knee injury'),
    (4, 4, '2026-05-11', '14:00:00', 'Cancelled', 'Skin allergy'),
    (5, 5, '2026-05-12', '09:30:00', 'Not Completed', 'Fever and cough');

    INSERT INTO MedicalRecord
    (pid, did, visitDate, diagnosis, prescription, testRecommended, notes)
    VALUES
    (1, 1, '2026-05-10', 'Mild cardiac stress', 'Aspirin', 'ECG', 'Avoid stress'),
    (2, 2, '2026-05-10', 'Migraine', 'Painkillers', 'MRI', 'Reduce screen time'),
    (3, 3, '2026-05-11', 'Ligament strain', 'Pain relief gel', 'X-Ray', 'Rest for 2 weeks'),
    (4, 4, '2026-05-11', 'Allergic dermatitis', 'Antihistamines', 'Blood test', 'Avoid allergens'),
    (5, 5, '2026-05-12', 'Viral fever', 'Paracetamol', 'CBC', 'Hydration advised');

    INSERT INTO Billing
    (pid, aid, consultationFee, testCharges, pharmaCharges, totalAmount, paymentStatus, paymentMode)
    VALUES
    (1, 1, 500, 1200, 300, 2000, 'Paid', 'Card'),
    (2, 2, 400, 2500, 200, 3100, 'Pending', 'Insurance'),
    (3, 3, 600, 1000, 250, 1850, 'Paid', 'Cash'),
    (4, 4, 450, 500, 150, 1100, 'Unpaid', 'Cash'),
    (5, 5, 350, 700, 100, 1150, 'Pending', 'Card');

    """

    for statement in sql.split(";"):
        if statement.strip():
            cursor.execute(statement)

    db.commit()
    print("Sample data inserted successfully.")

seed_data()

@app.route('/table-structure')
def table_structure():
    cursor.execute("DESCRIBE Patient")
    columns = cursor.fetchall()
    return jsonify(columns)

# -------------------- PATIENT --------------------

@app.route('/patients',methods=['POST'])
def add_patient():
    data = request.json
    firstName = data['firstName']
    lastName = data['lastName']
    dob = data['dob']
    gender = data['gender']
    phone = data['phone']
    email = data['email']
    address = data['address']
    bloodgrp = data['bloodgrp']
    insuranceID = data['insuranceID']
    registrationDate = data['registrationDate']

    query = "insert into Patient (firstName,lastName, dob, gender, phone, email, address, bloodgrp, insuranceID, registrationDate) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (firstName, lastName, dob, gender, phone, email, address, bloodgrp, insuranceID, registrationDate))
    db.commit()

    return jsonify({"message": "Patient added successfully"})

@app.route('/patients', methods=['GET'])
def get_patients():
    cursor.execute("SELECT * FROM Patient")
    result = cursor.fetchall()
    return jsonify(result)

# -------------------- SPECIALIZATION --------------------

@app.route('/specializations', methods=['POST'])
def add_specialization():
    data = request.json
    name = data['specializationName']

    query = "INSERT INTO Specialization (specializationName) VALUES (%s)"
    cursor.execute(query, (name,))
    db.commit()

    return jsonify({"message": "Specialization added successfully"})


@app.route('/specializations', methods=['GET'])
def get_specializations():
    cursor.execute("SELECT * FROM Specialization")
    return jsonify(cursor.fetchall())


# -------------------- DOCTOR --------------------

@app.route('/doctors', methods=['POST'])
def add_doctor():
    data = request.json

    query = """INSERT INTO Doctor (name, sid, phone, email, room, availability_schedule)
               VALUES (%s, %s, %s, %s, %s, %s)"""

    cursor.execute(query, (
        data['name'],
        data.get('sid'),
        data['phone'],
        data['email'],
        data['room'],
        data['availability_schedule']
    ))

    db.commit()
    return jsonify({"message": "Doctor added successfully"})


@app.route('/doctors', methods=['GET'])
def get_doctors():
    cursor.execute("SELECT * FROM Doctor")
    return jsonify(cursor.fetchall())


# -------------------- APPOINTMENT --------------------

@app.route('/appointments', methods=['POST'])
def add_appointment():
    data = request.json

    query = """INSERT INTO Appointment (pid, did, aptDate, aptTime, status, reasonForVisit)
               VALUES (%s, %s, %s, %s, %s, %s)"""
    try:

        cursor.callproc('book_and_bill', (
            data['pid'],
            data.get('did'),
            data.get('aptDate'),
            data.get('aptTime'),
            data.get('status'),
            data['reasonForVisit']
        ))

        db.commit()
        return jsonify({"message": "Appointment + Billing created"})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/appointments', methods=['GET'])
def get_appointments():
    cursor.execute("SELECT * FROM Appointment")

    appointments = cursor.fetchall()

    for appointment in appointments:
        if appointment['aptTime']:
            appointment['aptTime'] = str(appointment['aptTime'])

    return jsonify(appointments)


# -------------------- MEDICAL RECORD --------------------

@app.route('/records', methods=['POST'])
def add_record():
    data = request.json

    query = """INSERT INTO MedicalRecord (pid, did, visitDate, diagnosis, prescription, testRecommended, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    cursor.execute(query, (
        data['pid'],
        data.get('did'),
        data['visitDate'],
        data['diagnosis'],
        data['prescription'],
        data['testRecommended'],
        data['notes']
    ))

    db.commit()
    return jsonify({"message": "Medical record added"})


@app.route('/records', methods=['GET'])
def get_records():
    cursor.execute("SELECT * FROM MedicalRecord")
    return jsonify(cursor.fetchall())


# -------------------- BILLING --------------------

@app.route('/billing', methods=['POST'])
def add_bill():
    data = request.json

    total = data['consultationFee'] + data['testCharges'] + data['pharmaCharges']

    query = """INSERT INTO Billing (pid, aid, consultationFee, testCharges, pharmaCharges, totalAmount, paymentStatus, paymentMode)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

    cursor.execute(query, (
        data['pid'],
        data['aid'],
        data['consultationFee'],
        data['testCharges'],
        data['pharmaCharges'],
        total,
        data.get('paymentStatus', 'Pending'),
        data['paymentMode']
    ))

    db.commit()
    return jsonify({"message": "Bill created"})


@app.route('/billing', methods=['GET'])
def get_billing():
    cursor.execute("SELECT * FROM Billing")
    return jsonify(cursor.fetchall())


# -------------------- DELETE ROUTES --------------------

@app.route('/patients/<int:pid>', methods=['DELETE'])
def delete_patient(pid):
    cursor.execute("DELETE FROM Patient WHERE pid = %s", (pid,))
    db.commit()
    return jsonify({"message": "Patient deleted"})

@app.route('/specializations/<int:sid>', methods=['DELETE'])
def delete_specialization(sid):
    cursor.execute("DELETE FROM Specialization WHERE sid = %s", (sid,))
    db.commit()
    return jsonify({"message": "Specialization deleted"})

@app.route('/doctors/<int:did>', methods=['DELETE'])
def delete_doctor(did):
    cursor.execute("DELETE FROM Doctor WHERE did = %s", (did,))
    db.commit()
    return jsonify({"message": "Doctor deleted"})

@app.route('/appointments/<int:aid>', methods=['DELETE'])
def delete_appointment(aid):
    cursor.execute("DELETE FROM Appointment WHERE aid = %s", (aid,))
    db.commit()
    return jsonify({"message": "Appointment deleted"})

@app.route('/records/<int:rid>', methods=['DELETE'])
def delete_record(rid):
    cursor.execute("DELETE FROM MedicalRecord WHERE rid = %s", (rid,))
    db.commit()
    return jsonify({"message": "Record deleted"})

@app.route('/billing/<int:bid>', methods=['DELETE'])
def delete_billing(bid):
    cursor.execute("DELETE FROM Billing WHERE bid = %s", (bid,))
    db.commit()
    return jsonify({"message": "Billing deleted"})

# -------------------- UPDATE ROUTES --------------------

@app.route('/patients/<int:pid>', methods=['PUT'])
def update_patient(pid):
    data = request.json

    query = """UPDATE Patient SET firstName=%s, lastName=%s, dob=%s, gender=%s,
               phone=%s, email=%s, address=%s, bloodgrp=%s, insuranceID=%s, registrationDate=%s
               WHERE pid=%s"""

    cursor.execute(query, (
        data['firstName'], data['lastName'], data['dob'], data['gender'],
        data['phone'], data['email'], data['address'], data['bloodgrp'],
        data['insuranceID'], data['registrationDate'], pid
    ))

    db.commit()
    return jsonify({"message": "Patient updated"})

@app.route('/doctors/<int:did>', methods=['PUT'])
def update_doctor(did):
    data = request.json

    query = """UPDATE Doctor SET name=%s, sid=%s, phone=%s, email=%s,
               room=%s, availability_schedule=%s
               WHERE did=%s"""

    cursor.execute(query, (
        data['name'], data.get('sid'), data['phone'], data['email'],
        data['room'], data['availability_schedule'], did
    ))

    db.commit()
    return jsonify({"message": "Doctor updated"})

@app.route('/appointments/<int:aid>', methods=['PUT'])
def update_appointment(aid):
    data = request.json

    query = """UPDATE Appointment SET pid=%s, did=%s, aptDate=%s,
               aptTime=%s, status=%s, reasonForVisit=%s
               WHERE aid=%s"""

    cursor.execute(query, (
        data['pid'], data.get('did'), data['aptDate'],
        data['aptTime'], data['status'], data['reasonForVisit'], aid
    ))

    db.commit()
    return jsonify({"message": "Appointment updated"})

@app.route('/records/<int:rid>', methods=['PUT'])
def update_record(rid):
    data = request.json

    query = """UPDATE MedicalRecord SET pid=%s, did=%s, visitDate=%s,
               diagnosis=%s, prescription=%s, testRecommended=%s, notes=%s
               WHERE rid=%s"""

    cursor.execute(query, (
        data['pid'], data.get('did'), data['visitDate'],
        data['diagnosis'], data['prescription'],
        data['testRecommended'], data['notes'], rid
    ))

    db.commit()
    return jsonify({"message": "Record updated"})

@app.route('/billing/<int:bid>', methods=['PUT'])
def update_billing(bid):
    data = request.json

    total = data['consultationFee'] + data['testCharges'] + data['pharmaCharges']

    query = """UPDATE Billing SET pid=%s, aid=%s, consultationFee=%s,
               testCharges=%s, pharmaCharges=%s, totalAmount=%s,
               paymentStatus=%s, paymentMode=%s
               WHERE bid=%s"""

    cursor.execute(query, (
        data['pid'], data['aid'], data['consultationFee'],
        data['testCharges'], data['pharmaCharges'], total,
        data['paymentStatus'], data['paymentMode'], bid
    ))

    db.commit()
    return jsonify({"message": "Billing updated"})

# -------------------- VIEW QUERIES --------------------

@app.route('/appointments/full', methods=['GET'])
def get_appointment_full():

    cursor.execute("SELECT * FROM appointment_full_view")

    appointments = cursor.fetchall()

    for appointment in appointments:
        if 'apttime' in appointment and appointment['apttime']:
            appointment['apttime'] = str(appointment['apttime'])

    return jsonify(appointments)

@app.route('/appointments/daily-summary', methods=['GET'])
def get_daily_summary():
    cursor.execute("SELECT * FROM daily_appointment_summary")
    return jsonify(cursor.fetchall())

@app.route('/billing/full', methods=['GET'])
def get_billing_full():

    cursor.execute("SELECT * FROM billing_full_view")

    bills = cursor.fetchall()

    for bill in bills:
        if 'apttime' in bill and bill['apttime']:
            bill['apttime'] = str(bill['apttime'])

    return jsonify(bills)

@app.route('/doctors/workload', methods=['GET'])
def get_doctor_workload():
    cursor.execute("SELECT * FROM doctor_workload_view")
    return jsonify(cursor.fetchall())

@app.route('/patients/history/<int:pid>', methods=['GET'])
def get_patient_history(pid):
    query = "SELECT * FROM patient_history_view WHERE pid = %s"
    cursor.execute(query, (pid,))
    return jsonify(cursor.fetchall())

@app.route('/revenue/summary', methods=['GET'])
def get_revenue_summary():
    cursor.execute("SELECT * FROM revenue_summary_view")
    return jsonify(cursor.fetchall())

# -------------------- JOIN QUERIES --------------------

@app.route('/records/full', methods=['GET'])
def get_full_records():
    query = """
    SELECT r.rid, r.visitDate, r.diagnosis,
           p.firstName, p.lastName,
           d.name AS doctor_name
    FROM MedicalRecord r
    JOIN Patient p ON r.pid = p.pid
    LEFT JOIN Doctor d ON r.did = d.did
    """

    cursor.execute(query)
    return jsonify(cursor.fetchall())

@app.route('/doctors/full', methods=['GET'])
def get_doctors_with_specialization():
    query = """
    SELECT d.did, d.name, s.specializationName, d.room
    FROM Doctor d
    LEFT JOIN Specialization s ON d.sid = s.sid
    """

    cursor.execute(query)
    return jsonify(cursor.fetchall())

if __name__ == '__main__':
    app.run(debug=True)