from flask import Flask, render_template, request, redirect

from flask import Flask
import pyodbc
import os

app = Flask(__name__)

# ✅ Default home route
@app.route('/')
def home():
    return "Welcome to the Flask App!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


# ✅ Azure SQL Database Credentials
DB_SERVER = os.getenv("DB_SERVER", "dlinkrouterlocal.database.windows.net,1433")  
DB_NAME = os.getenv("DB_NAME", "medicalhtdb")  
DB_USER = os.getenv("DB_USER", "CloudSAa8b76aaa")  
DB_PASSWORD = os.getenv("DB_PASSWORD", "System2025")  

def get_db_connection():

    try:
        print("\n🔍 **DEBUG: Attempting to connect to Azure SQL Server** 🔍")
        print(f"🔹 SERVER: {DB_SERVER}")
        print(f"🔹 DATABASE: {DB_NAME}")
        print(f"🔹 USER: {DB_USER}")
        print(f"🔹 PASSWORD: {DB_PASSWORD}")  # NOTE: Be careful exposing this in real logs!

        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={dlinkrouterlocal.database.windows.net,1433};"
            f"DATABASE={medicalhtdb};"
            f"UID={admin_user};"
            f"PWD={System2025};"
            f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        print("✅ SUCCESS: Azure SQL Database connection established!")
        return conn
    except Exception as e:
        print(f"❌ ERROR: Database connection failed! Reason: {e}")
        return None


    conn = get_db_connection()
    cursor = conn.cursor()

    page = request.args.get('page', 1, type=int)  # Get current page, default is 1
    records_per_page = 20  # Number of patients per page
    offset = (page - 1) * records_per_page  # Calculate the offset

    # ✅ Fetch paginated patient list
    cursor.execute("""
        SELECT PatientID, FirstName, LastName, BirthDate, CNP, Phone, Address, FamilyDoctor
        FROM Patients
        ORDER BY PatientID
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """, (offset, records_per_page))

    patients = cursor.fetchall()

    # ✅ Get total patient count
    cursor.execute("SELECT COUNT(*) FROM Patients")
    total_patients = cursor.fetchone()[0]

    total_pages = (total_patients // records_per_page) + (1 if total_patients % records_per_page > 0 else 0)

    conn.close()

    return render_template('home.html', patients=patients, page=page, total_pages=total_pages)

@app.route('/search', methods=['GET'])
def search():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = request.args.get('query', '').strip()
    dob_search = request.args.get('dob_search', '').strip()

    # ✅ Base SQL Query
    sql = "SELECT * FROM Patients WHERE 1=1"
    params = []

    if query:
        sql += " AND (FirstName LIKE ? OR LastName LIKE ? OR Phone LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

    if dob_search:
        sql += " AND BirthDate = ?"
        params.append(dob_search)

    cursor.execute(sql, params)
    searched_patients = cursor.fetchall()

    # ✅ Get total patient count for pagination (Fix NoneType issue)
    cursor.execute("SELECT COUNT(*) FROM Patients")
    count_result = cursor.fetchone()
    total_patients = count_result[0] if count_result else 0  # ✅ Ensures no NoneType error

    total_pages = max((total_patients // 20) + (1 if total_patients % 20 > 0 else 0), 1)  # Ensure at least 1 page

    conn.close()

    return render_template('home.html', 
                           searched_patients=searched_patients, 
                           patients=searched_patients if searched_patients else [],  
                           page=1,  
                           total_pages=total_pages)  # ✅ Always pass `total_pages`


@app.route('/view_patient/<int:id>')
def view_patient(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch patient details (No changes here)
    cursor.execute("""
        SELECT PatientID, FirstName, LastName, BirthDate, CNP, Phone, Address, FamilyDoctor, Notes
        FROM Patients
        WHERE PatientID=?
    """, (id,))
    patient = cursor.fetchone()

    if not patient:
        return "❌ Patient not found in database", 404

    # Pagination logic for appointments
    page = request.args.get('page', 1, type=int)  # Get current page, default is 1
    records_per_page = 10  # Change this if you want more or fewer appointments per page
    offset = (page - 1) * records_per_page  # Calculate offset

    # Fetch paginated appointment history
    cursor.execute("""
        SELECT AppointmentID, AppointmentDate, AppointmentTime, ClinicDoctor, 
               Reason, Status, PaymentTaken, PaymentType
        FROM Appointments
        WHERE PatientID = ?
        ORDER BY AppointmentDate DESC, AppointmentTime DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """, (id, offset, records_per_page))

    appointments = cursor.fetchall()

    # Get total number of appointments for pagination
    cursor.execute("""
        SELECT COUNT(*) FROM Appointments WHERE PatientID = ?
    """, (id,))
    total_appointments = cursor.fetchone()[0]

    total_pages = (total_appointments // records_per_page) + (1 if total_appointments % records_per_page > 0 else 0)

    return render_template('view_patient.html', 
                           patient=patient, 
                           appointments=appointments, 
                           page=page, 
                           total_pages=total_pages)

# Edit Patient
@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birth_date = request.form['birth_date']
        cnp = request.form['cnp']
        phone = request.form['phone']
        address = request.form['address']
        family_doctor = request.form['family_doctor']
        notes = request.form['notes']
        
        cursor.execute("""
            UPDATE Patients
            SET FirstName=?, LastName=?, BirthDate=?, CNP=?, Phone=?, Address=?, FamilyDoctor=?, Notes=?
            WHERE PatientID=?
        """, (first_name, last_name, birth_date, cnp, phone, address, family_doctor, notes, id))
        conn.commit()
        conn.close()
        return redirect(f'/view_patient/{id}')
    
    cursor.execute("SELECT PatientID, FirstName, LastName, BirthDate, CNP, Phone, Address, FamilyDoctor, Notes FROM Patients WHERE PatientID=?", (id,))
    patient = cursor.fetchone()
    conn.close()
    return render_template('edit_patient.html', patient=patient)

# Add Patient
@app.route('/add_patient', methods=['POST'])
def add_patient():
    conn = get_db_connection()
    cursor = conn.cursor()
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    birth_date = request.form['birth_date']
    cnp = request.form['cnp']
    phone = request.form['phone']
    address = request.form['address']
    family_doctor = request.form['family_doctor']
    notes = request.form['notes']
    
    cursor.execute("""
        INSERT INTO Patients (FirstName, LastName, BirthDate, CNP, Phone, Address, FamilyDoctor, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, birth_date, cnp, phone, address, family_doctor, notes))
    conn.commit()
    conn.close()
    return redirect('/')

# ✅ View and Manage Appointments Page
@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get selected date from the request
    selected_date = request.args.get('appointment_date', '').strip()

    # Get current page number from the request, default is page 1
    page = request.args.get('page', 1, type=int)
    records_per_page = 20  # Change this number if you want more or fewer appointments per page
    offset = (page - 1) * records_per_page

    # ✅ Corrected SQL Query to Use `Patients` and Add Pagination
    sql = """
        SELECT a.AppointmentID, p.FirstName, p.LastName, a.AppointmentDate, 
               a.AppointmentTime, a.ClinicDoctor, a.Reason, a.Comments, 
               a.Status, a.PaymentTaken, a.PaymentType
        FROM Appointments a
        JOIN Patients p ON a.PatientID = p.PatientID
        WHERE 1=1
    """
    params = []

    # Apply date filter if selected
    if selected_date:
        sql += " AND a.AppointmentDate = ?"
        params.append(selected_date)

    sql += " ORDER BY a.AppointmentDate DESC, a.AppointmentTime DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params.extend([offset, records_per_page])

    cursor.execute(sql, params)
    appointments = cursor.fetchall()

    # Get total number of appointments for pagination
    count_sql = """
        SELECT COUNT(*)
        FROM Appointments a
        JOIN Patients p ON a.PatientID = p.PatientID
        WHERE 1=1
    """
    count_params = []

    if selected_date:
        count_sql += " AND a.AppointmentDate = ?"
        count_params.append(selected_date)

    cursor.execute(count_sql, count_params)
    total_appointments = cursor.fetchone()[0]

    total_pages = (total_appointments // records_per_page) + (1 if total_appointments % records_per_page > 0 else 0)

    return render_template('appointments.html', 
                           appointments=appointments, 
                           selected_date=selected_date, 
                           page=page, 
                           total_pages=total_pages)

# Schedule Appointment
@app.route('/schedule_appointment', methods=['GET'])
def schedule_appointment():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get patient_id from query parameters
    patient_id = request.args.get('patient_id')

    # Fetch all patients with their BirthDate
    cursor.execute("SELECT PatientID, FirstName, LastName, BirthDate FROM Patients")
    patients = cursor.fetchall()

    # Fetch selected patient details if scheduling from "View Patient"
    selected_patient = None
    if patient_id:
        cursor.execute("SELECT PatientID, FirstName, LastName, BirthDate FROM Patients WHERE PatientID=?", (patient_id,))
        selected_patient = cursor.fetchone()

    return render_template('schedule_appointment.html', patients=patients, selected_patient=selected_patient)

@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Retrieve form data
        patient_id = request.form.get('patient_id')
        birth_date = request.form.get('birth_date')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        clinic_doctor = request.form.get('clinic_doctor')
        reason = request.form.get('reason', '')
        comments = request.form.get('comments', '')
        status = "Scheduled"
        payment_taken = request.form.get('payment_taken', 'No')
        payment_type = request.form.get('payment_type', 'Not Specified')
        if not patient_id or not appointment_date or not appointment_time:
            return "❌ Error: Missing required fields", 400

        # Insert into the database
        cursor.execute("""
    INSERT INTO Appointments (
        PatientID, BirthDate, AppointmentDate, AppointmentTime, 
        ClinicDoctor, Reason, Comments, PaymentTaken, PaymentType, Status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (patient_id, birth_date, appointment_date, appointment_time, clinic_doctor, reason, comments, payment_taken, payment_type, status))


        conn.commit()
        return redirect(f'/view_patient/{patient_id}')

    except Exception as e:
        return f"❌ Database Insert Error: {str(e)}", 500

    finally:
        cursor.close()
        conn.close()
# ✅ Update Appointment Route (NEW: Allows rescheduling, changing doctor, status, etc.)
@app.route('/update_appointment/<int:appointment_id>', methods=['POST'])
def update_appointment(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    selected_date = request.form.get('selected_date', '')

    # Retrieve form data
    appointment_date = request.form.get('appointment_date')
    appointment_time = request.form.get('appointment_time')
    clinic_doctor = request.form.get('clinic_doctor')
    reason = request.form.get('reason')
    comments = request.form.get('comments')
    status = request.form.get('status')
    payment_taken = request.form.get('payment_taken')
    payment_type = request.form['payment_type']

    patient_id = request.form.get('patient_id')  # Get patient_id if available
    selected_date = request.form.get('selected_date')  # Get selected date filter
    referrer = request.referrer  # Get the previous page

    try:
        cursor.execute("""
            UPDATE Appointments
            SET AppointmentDate=?, AppointmentTime=?, ClinicDoctor=?, Reason=?, Comments=?, Status=?, PaymentTaken=?, PaymentType=?
            WHERE AppointmentID=?
        """, (appointment_date, appointment_time, clinic_doctor, reason, comments, status, payment_taken, payment_type, appointment_id))

        conn.commit()

        # ✅ If the request came from the Patient Details page, return there
        if referrer and "/view_patient/" in referrer:
            return redirect(referrer)

        # ✅ Redirect to Appointments List, keeping the selected date
        if selected_date:
            return redirect(f'/appointments?appointment_date={selected_date}')
        else:
            return redirect('/appointments')

    except Exception as e:
        return f"❌ Database Update Error: {str(e)}", 500

    finally:
        cursor.close()
        conn.close()

# Number of records per page
RECORDS_PER_PAGE = 30  


# Run the App
if __name__ == '__main__':
    app.run(debug=True)
