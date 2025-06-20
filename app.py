from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# --- App Config ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# --- Initialize DB ---
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))  # 'admin' or 'doctor'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    problem = db.Column(db.String(255))
    report = db.Column(db.String(255))  # filename

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    department = db.Column(db.String(100))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    date = db.Column(db.String(50))
    patient = db.relationship('Patient')
    doctor = db.relationship('Doctor')

# --- Routes ---

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        confirm = request.form['confirm']
        role = request.form['role']

        if pwd != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=uname).first()
        if existing_user:
            flash("Username already exists", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(pwd)
        new_user = User(username=uname, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = User.query.filter_by(username=uname).first()
        if user and check_password_hash(user.password, pwd):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    p = Patient.query.count()
    d = Doctor.query.count()
    a = Appointment.query.count()
    return render_template('dashboard/index.html', p=p, d=d, a=a)

@app.route('/patients')
def patients():
    data = Patient.query.all()
    return render_template('patients/index.html', patients=data)

@app.route('/patients/add', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        problem = request.form['problem']
        file = request.files['report']
        filename = ''
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_patient = Patient(name=name, age=age, gender=gender, problem=problem, report=filename)
        db.session.add(new_patient)
        db.session.commit()
        return redirect(url_for('patients'))
    return render_template('patients/add.html')

@app.route('/patients/edit/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    patient = Patient.query.get(id)
    if request.method == 'POST':
        patient.name = request.form['name']
        patient.age = request.form['age']
        patient.gender = request.form['gender']
        patient.problem = request.form['problem']
        db.session.commit()
        return redirect(url_for('patients'))
    return render_template('patients/edit.html', patient=patient)

@app.route('/patients/delete/<int:id>')
def delete_patient(id):
    db.session.delete(Patient.query.get(id))
    db.session.commit()
    return redirect(url_for('patients'))

@app.route('/doctors')
def doctors():
    data = Doctor.query.all()
    return render_template('doctors/index.html', doctors=data)

@app.route('/doctors/add', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        name = request.form['name']
        dept = request.form['department']
        new_doc = Doctor(name=name, department=dept)
        db.session.add(new_doc)
        db.session.commit()
        return redirect(url_for('doctors'))
    return render_template('doctors/add.html')

@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    if request.method == 'POST':
        pid = request.form['patient']
        did = request.form['doctor']
        date = request.form['date']
        new_app = Appointment(patient_id=pid, doctor_id=did, date=date)
        db.session.add(new_app)
        db.session.commit()
        return redirect(url_for('appointments'))
    all_appointments = Appointment.query.all()
    return render_template('appointments/index.html', appointments=all_appointments, patients=patients, doctors=doctors)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Run ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
