from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'rafli_secret_key_2024'

# Database connection
def get_db():
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='rafli',
            password='saputra19',
            database='presensi_db'
        )
        return conn
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"🔐 Login attempt: {username}")
        
        db = get_db()
        if db:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            db.close()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                session['role'] = user.get('role', 'user')
                session['position'] = user.get('position', 'Staff')
                session['department'] = user.get('department', 'IT')
                
                print(f"✅ Login success: {user['full_name']}")
                flash('Login berhasil!', 'success')
                return redirect('/dashboard')
        
        flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    db = get_db()
    today = date.today()
    
    monthly_stats = {'total': 0}
    today_attendance = None
    recent_attendance = []
    
    if db:
        cursor = db.cursor(dictionary=True)
        
        # Stats bulan ini
        cursor.execute('''
            SELECT COUNT(*) as total FROM attendance 
            WHERE user_id = %s AND MONTH(date) = %s AND YEAR(date) = %s
        ''', (session['user_id'], today.month, today.year))
        monthly_stats = cursor.fetchone()
        
        # Hari ini
        cursor.execute('SELECT * FROM attendance WHERE user_id = %s AND date = %s', 
                     (session['user_id'], today))
        today_attendance = cursor.fetchone()
        
        # 7 hari terakhir
        cursor.execute('''
            SELECT * FROM attendance 
            WHERE user_id = %s 
            ORDER BY date DESC LIMIT 7
        ''', (session['user_id'],))
        recent_attendance = cursor.fetchall()
        
        cursor.close()
        db.close()
    
    return render_template('dashboard.html',
                         monthly_stats=monthly_stats,
                         today_attendance=today_attendance,
                         recent_attendance=recent_attendance,
                         today=today)

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user_id' not in session:
        return redirect('/login')
    
    today = date.today()
    
    if request.method == 'POST':
        action = request.form.get('action')
        current_time = datetime.now()
        
        print(f"🕒 Attendance: {action} by {session['username']}")
        
        db = get_db()
        if db:
            cursor = db.cursor(dictionary=True)
            
            try:
                if action == 'check_in':
                    # Cek apakah sudah check in
                    cursor.execute('SELECT id FROM attendance WHERE user_id = %s AND date = %s', 
                                 (session['user_id'], today))
                    if not cursor.fetchone():
                        status = 'Terlambat' if current_time.hour >= 9 else 'Hadir'
                        cursor.execute(
                            'INSERT INTO attendance (user_id, check_in, date, status) VALUES (%s, %s, %s, %s)',
                            (session['user_id'], current_time, today, status)
                        )
                        db.commit()
                        print("✅ Check-in success!")
                        flash('Check-in berhasil!', 'success')
                    else:
                        flash('Sudah check-in hari ini!', 'error')
                        
                elif action == 'check_out':
                    cursor.execute('SELECT id FROM attendance WHERE user_id = %s AND date = %s AND check_out IS NULL', 
                                 (session['user_id'], today))
                    if cursor.fetchone():
                        cursor.execute(
                            'UPDATE attendance SET check_out = %s WHERE user_id = %s AND date = %s',
                            (current_time, session['user_id'], today)
                        )
                        db.commit()
                        print("✅ Check-out success!")
                        flash('Check-out berhasil!', 'success')
                    else:
                        flash('Belum check-in atau sudah check-out!', 'error')
                
            except Exception as e:
                print(f"❌ Error: {e}")
                flash('Terjadi kesalahan!', 'error')
            finally:
                cursor.close()
                db.close()
        
        return redirect('/attendance')
    
    # GET request - show data
    db = get_db()
    attendance_history = []
    today_attendance = None
    
    if db:
        cursor = db.cursor(dictionary=True)
        
        # Riwayat
        cursor.execute('''
            SELECT * FROM attendance 
            WHERE user_id = %s 
            ORDER BY date DESC LIMIT 10
        ''', (session['user_id'],))
        attendance_history = cursor.fetchall()
        
        # Hari ini
        cursor.execute('SELECT * FROM attendance WHERE user_id = %s AND date = %s', 
                     (session['user_id'], today))
        today_attendance = cursor.fetchone()
        
        cursor.close()
        db.close()
    
    return render_template('attendance.html',
                         attendance_history=attendance_history,
                         today_attendance=today_attendance,
                         today=today)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    db = get_db()
    user_data = {}
    
    if db:
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
        user_data = cursor.fetchone() or {}
        cursor.close()
        db.close()
    
    return render_template('profile.html', user_data=user_data)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout berhasil!', 'success')
    return redirect('/login')

if __name__ == '__main__':
    print("🚀 Starting Flask Server...")
    print("📍 http://localhost:5600")
    print("👤 Test Accounts:")
    print("   Username: rafli")
    print("   Password: rafli123")
    print("   Username: admin")
    print("   Password: admin123")
    print("-" * 40)
    app.run(debug=True, host='0.0.0.0', port=5600)