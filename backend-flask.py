"""
AuraLearn – Flask Backend
Complete routes: Auth, Student Dashboard, Admin Dashboard,
Courses, Modules, Quiz, Results, Certificates, Feedback, Orders
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, date
import os, io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
app.secret_key = 'auralearn_super_secret_2025'

# ── MYSQL CONFIG ──────────────────────────────────────────
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''          # your MySQL password
app.config['MYSQL_DB'] = 'auralearn'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ── UPLOAD CONFIG ─────────────────────────────────────────
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif','mp4','pdf','doc','docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        fn = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        file.save(path)
        return fn
    return None

# ── DECORATORS ────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*a, **kw)
    return deco

def admin_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if session.get('role_id') != 1:
            flash('Admin access only.', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*a, **kw)
    return deco

def db_query(sql, args=(), one=False, commit=False):
    cur = mysql.connection.cursor()
    cur.execute(sql, args)
    if commit:
        mysql.connection.commit()
        cur.close()
        return cur.lastrowid
    rv = cur.fetchone() if one else cur.fetchall()
    cur.close()
    return rv

# ════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ════════════════════════════════════════════════════════

@app.route('/')
def index():
    courses = db_query("SELECT c.*,cat.category_name FROM Course c LEFT JOIN Category cat ON c.category_id=cat.category_id LIMIT 10")
    instructors = db_query("SELECT DISTINCT instructor_name FROM Course LIMIT 4")
    feedback = db_query("SELECT f.*,u.full_name,u.profile_image,c.course_name FROM Feedback f JOIN User u ON f.user_id=u.user_id JOIN Course c ON f.course_id=c.course_id ORDER BY f.feedback_id DESC LIMIT 12")
    zoom = db_query("SELECT z.*,c.course_name FROM Zoom_Classes z JOIN Course c ON z.course_id=c.course_id ORDER BY z.class_date LIMIT 3")
    return render_template('index.html', courses=courses, feedback=feedback, zoom=zoom)

# ── AUTH ──────────────────────────────────────────────────
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name  = request.form['full_name']
        email = request.form['email']
        pwd   = generate_password_hash(request.form['password'])
        existing = db_query("SELECT user_id FROM User WHERE email=%s", (email,), one=True)
        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        db_query("INSERT INTO User (full_name,email,password,role_id) VALUES (%s,%s,%s,2)",
                 (name, email, pwd), commit=True)
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pwd   = request.form['password']
        user  = db_query("SELECT * FROM User WHERE email=%s", (email,), one=True)
        if user and check_password_hash(user['password'], pwd):
            session['user_id']   = user['user_id']
            session['full_name'] = user['full_name']
            session['role_id']   = user['role_id']
            session['profile']   = user['profile_image']
            if user['role_id'] == 1:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ════════════════════════════════════════════════════════
# STUDENT DASHBOARD
# ════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def student_dashboard():
    uid = session['user_id']
    enrollments = db_query("""
        SELECT e.*,c.course_name,c.thumbnail,c.instructor_name,c.duration
        FROM Enrollment e JOIN Course c ON e.course_id=c.course_id
        WHERE e.user_id=%s""", (uid,))
    results = db_query("""
        SELECT r.*,t.total_marks,m.module_title,c.course_name
        FROM Result r JOIN Test t ON r.test_id=t.test_id
        JOIN Module m ON t.module_id=m.module_id
        JOIN Course c ON m.course_id=c.course_id
        WHERE r.user_id=%s ORDER BY r.taken_at DESC LIMIT 5""", (uid,))
    certs = db_query("""
        SELECT ce.*,c.course_name FROM Certificates ce
        JOIN Course c ON ce.course_id=c.course_id
        WHERE ce.user_id=%s""", (uid,))
    zoom = db_query("""
        SELECT z.*,c.course_name FROM Zoom_Classes z
        JOIN Course c ON z.course_id=c.course_id
        JOIN Enrollment e ON e.course_id=z.course_id
        WHERE e.user_id=%s AND z.class_date>=NOW()
        ORDER BY z.class_date LIMIT 5""", (uid,))
    return render_template('student/dashboard.html',
        enrollments=enrollments, results=results, certs=certs, zoom=zoom)

@app.route('/course/<int:cid>')
@login_required
def course_detail(cid):
    uid = session['user_id']
    course = db_query("SELECT c.*,cat.category_name FROM Course c LEFT JOIN Category cat ON c.category_id=cat.category_id WHERE c.course_id=%s", (cid,), one=True)
    modules = db_query("SELECT * FROM Module WHERE course_id=%s ORDER BY order_no", (cid,))
    enrolled = db_query("SELECT * FROM Enrollment WHERE user_id=%s AND course_id=%s", (uid,cid), one=True)
    feedback = db_query("SELECT f.*,u.full_name,u.profile_image FROM Feedback f JOIN User u ON f.user_id=u.user_id WHERE f.course_id=%s ORDER BY f.feedback_id DESC", (cid,))
    zoom = db_query("SELECT * FROM Zoom_Classes WHERE course_id=%s ORDER BY class_date", (cid,))
    return render_template('student/course_detail.html', course=course, modules=modules, enrolled=enrolled, feedback=feedback, zoom=zoom)

@app.route('/enroll/<int:cid>', methods=['POST'])
@login_required
def enroll(cid):
    uid = session['user_id']
    existing = db_query("SELECT enroll_id FROM Enrollment WHERE user_id=%s AND course_id=%s", (uid,cid), one=True)
    if not existing:
        db_query("INSERT INTO Enrollment (user_id,course_id) VALUES (%s,%s)", (uid,cid), commit=True)
        flash('Enrolled successfully!', 'success')
    return redirect(url_for('course_detail', cid=cid))

@app.route('/module/<int:mid>')
@login_required
def module_view(mid):
    mod = db_query("SELECT m.*,c.course_name FROM Module m JOIN Course c ON m.course_id=c.course_id WHERE m.module_id=%s", (mid,), one=True)
    test = db_query("SELECT * FROM Test WHERE module_id=%s", (mid,), one=True)
    return render_template('student/module.html', mod=mod, test=test)

# ── QUIZ ──────────────────────────────────────────────────
@app.route('/quiz/<int:test_id>')
@login_required
def quiz(test_id):
    test = db_query("SELECT t.*,m.module_title FROM Test t JOIN Module m ON t.module_id=m.module_id WHERE t.test_id=%s", (test_id,), one=True)
    questions = db_query("SELECT * FROM Questions WHERE module_id=%s", (test['module_id'],))
    return render_template('student/quiz.html', test=test, questions=questions)

@app.route('/quiz/submit/<int:test_id>', methods=['POST'])
@login_required
def quiz_submit(test_id):
    uid = session['user_id']
    test = db_query("SELECT * FROM Test WHERE test_id=%s", (test_id,), one=True)
    questions = db_query("SELECT * FROM Questions WHERE module_id=%s", (test['module_id'],))
    score = 0
    for q in questions:
        qid = q['question_id']
        selected = request.form.get(f'q_{qid}')
        solution = db_query("SELECT * FROM Solution WHERE question_id=%s", (qid,), one=True)
        correct = solution and solution['correct_option'] == selected
        if correct: score += 1
        db_query("INSERT INTO Attempt (user_id,question_id,selected_option,is_correct) VALUES (%s,%s,%s,%s)",
                 (uid, qid, selected, 1 if correct else 0), commit=True)
    total = len(questions)
    pct = (score/total*100) if total else 0
    judgment = 'pass' if pct >= (test['passing_marks']/test['total_marks']*100) else 'fail'
    db_query("INSERT INTO Result (user_id,test_id,score,judgment) VALUES (%s,%s,%s,%s)",
             (uid, test_id, score, judgment), commit=True)
    if judgment == 'pass':
        mod = db_query("SELECT course_id FROM Module WHERE module_id=%s", (test['module_id'],), one=True)
        existing = db_query("SELECT certificate_id FROM Certificates WHERE user_id=%s AND course_id=%s", (uid, mod['course_id']), one=True)
        if not existing:
            db_query("INSERT INTO Certificates (user_id,course_id,issue_date) VALUES (%s,%s,%s)",
                     (uid, mod['course_id'], date.today()), commit=True)
    return redirect(url_for('quiz_result', test_id=test_id))

@app.route('/quiz/result/<int:test_id>')
@login_required
def quiz_result(test_id):
    uid = session['user_id']
    result = db_query("SELECT r.*,t.total_marks,t.passing_marks FROM Result r JOIN Test t ON r.test_id=t.test_id WHERE r.test_id=%s AND r.user_id=%s ORDER BY r.taken_at DESC LIMIT 1", (test_id, uid), one=True)
    attempts = db_query("""
        SELECT a.*,q.question_text,q.option_a,q.option_b,q.option_c,q.option_d,s.correct_option,s.explanation
        FROM Attempt a JOIN Questions q ON a.question_id=q.question_id
        LEFT JOIN Solution s ON s.question_id=q.question_id
        WHERE a.user_id=%s ORDER BY a.attempted_at DESC""", (uid,))
    return render_template('student/quiz_result.html', result=result, attempts=attempts)

# ── CERTIFICATE PDF ───────────────────────────────────────
@app.route('/certificate/download/<int:cert_id>')
@login_required
def download_cert(cert_id):
    uid = session['user_id']
    cert = db_query("""
        SELECT ce.*,u.full_name,c.course_name FROM Certificates ce
        JOIN User u ON ce.user_id=u.user_id JOIN Course c ON ce.course_id=c.course_id
        WHERE ce.certificate_id=%s AND ce.user_id=%s""", (cert_id, uid), one=True)
    if not cert:
        flash('Certificate not found.', 'danger')
        return redirect(url_for('student_dashboard'))
    buf = io.BytesIO()
    p = pdf_canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    p.setFillColorRGB(.04,.03,.09)
    p.rect(0,0,w,h,fill=1)
    p.setFillColorRGB(.48,.23,.93)
    p.setFont('Helvetica-Bold', 36)
    p.drawCentredString(w/2, h-120, 'AuraLearn')
    p.setFillColorRGB(1,1,1)
    p.setFont('Helvetica-Bold', 24)
    p.drawCentredString(w/2, h-200, 'Certificate of Completion')
    p.setFont('Helvetica', 16)
    p.drawCentredString(w/2, h-270, f'This certifies that')
    p.setFont('Helvetica-Bold', 22)
    p.setFillColorRGB(.4,.91,.96)
    p.drawCentredString(w/2, h-310, cert['full_name'])
    p.setFillColorRGB(1,1,1)
    p.setFont('Helvetica', 16)
    p.drawCentredString(w/2, h-350, 'has successfully completed the course')
    p.setFont('Helvetica-Bold', 20)
    p.setFillColorRGB(.48,.23,.93)
    p.drawCentredString(w/2, h-390, cert['course_name'])
    p.setFillColorRGB(.6,.6,.6)
    p.setFont('Helvetica', 12)
    p.drawCentredString(w/2, h-450, f"Issue Date: {cert['issue_date']}")
    p.setFont('Helvetica', 10)
    p.drawCentredString(w/2, 60, f"Certificate ID: AL-{cert['certificate_id']:06d} | Verify at auralearn.com")
    p.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"AuraLearn_Certificate_{cert_id}.pdf", mimetype='application/pdf')

# ── FEEDBACK ──────────────────────────────────────────────
@app.route('/feedback/<int:cid>', methods=['POST'])
@login_required
def add_feedback(cid):
    uid = session['user_id']
    rating = request.form.get('rating', 5)
    review = request.form.get('review', '')
    db_query("INSERT INTO Feedback (user_id,course_id,rating,review) VALUES (%s,%s,%s,%s)",
             (uid, cid, rating, review), commit=True)
    flash('Feedback submitted!', 'success')
    return redirect(url_for('course_detail', cid=cid))

# ── ORDERS ────────────────────────────────────────────────
@app.route('/order/<int:mid>', methods=['POST'])
@login_required
def place_order(mid):
    uid = session['user_id']
    mod = db_query("SELECT * FROM Module WHERE module_id=%s", (mid,), one=True)
    course = db_query("SELECT price FROM Course WHERE course_id=%s", (mod['course_id'],), one=True)
    db_query("INSERT INTO Orders (user_id,module_id,price,payment_status,from_date,to_date) VALUES (%s,%s,%s,'paid',NOW(),DATE_ADD(NOW(),INTERVAL 30 DAY))",
             (uid, mid, course['price']), commit=True)
    flash('Module purchased!', 'success')
    return redirect(url_for('module_view', mid=mid))

# ════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ════════════════════════════════════════════════════════

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'users':   db_query("SELECT COUNT(*) AS c FROM User WHERE role_id=2", one=True)['c'],
        'courses': db_query("SELECT COUNT(*) AS c FROM Course", one=True)['c'],
        'enrolled':db_query("SELECT COUNT(*) AS c FROM Enrollment", one=True)['c'],
        'revenue': db_query("SELECT COALESCE(SUM(price),0) AS c FROM Orders WHERE payment_status='paid'", one=True)['c'],
    }
    recent_users = db_query("SELECT * FROM User ORDER BY created_at DESC LIMIT 8")
    recent_orders = db_query("SELECT o.*,u.full_name,m.module_title FROM Orders o JOIN User u ON o.user_id=u.user_id JOIN Module m ON o.module_id=m.module_id ORDER BY o.created_at DESC LIMIT 8")
    feedback = db_query("SELECT f.*,u.full_name,c.course_name FROM Feedback f JOIN User u ON f.user_id=u.user_id JOIN Course c ON f.course_id=c.course_id ORDER BY f.feedback_id DESC LIMIT 6")
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users, recent_orders=recent_orders, feedback=feedback)

# ── ADMIN: COURSES ────────────────────────────────────────
@app.route('/admin/courses')
@login_required
@admin_required
def admin_courses():
    courses = db_query("SELECT c.*,cat.category_name FROM Course c LEFT JOIN Category cat ON c.category_id=cat.category_id")
    cats = db_query("SELECT * FROM Category")
    return render_template('admin/courses.html', courses=courses, cats=cats)

@app.route('/admin/courses/add', methods=['POST'])
@login_required
@admin_required
def admin_add_course():
    thumb = save_file(request.files.get('thumbnail')) or 'default_course.jpg'
    db_query("INSERT INTO Course (course_name,description,thumbnail,instructor_name,duration,price,category_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
             (request.form['course_name'], request.form['description'], thumb,
              request.form['instructor_name'], request.form['duration'],
              request.form['price'], request.form['category_id']), commit=True)
    flash('Course added!', 'success')
    return redirect(url_for('admin_courses'))

@app.route('/admin/courses/delete/<int:cid>')
@login_required
@admin_required
def admin_delete_course(cid):
    db_query("DELETE FROM Course WHERE course_id=%s", (cid,), commit=True)
    flash('Course deleted.', 'warning')
    return redirect(url_for('admin_courses'))

# ── ADMIN: MODULES ────────────────────────────────────────
@app.route('/admin/modules')
@login_required
@admin_required
def admin_modules():
    modules = db_query("SELECT m.*,c.course_name FROM Module m JOIN Course c ON m.course_id=c.course_id ORDER BY m.course_id,m.order_no")
    courses = db_query("SELECT course_id,course_name FROM Course")
    return render_template('admin/modules.html', modules=modules, courses=courses)

@app.route('/admin/modules/add', methods=['POST'])
@login_required
@admin_required
def admin_add_module():
    vid = save_file(request.files.get('video'))
    doc = save_file(request.files.get('document'))
    db_query("INSERT INTO Module (course_id,module_title,content,order_no,video_url,document_file) VALUES (%s,%s,%s,%s,%s,%s)",
             (request.form['course_id'], request.form['module_title'], request.form['content'],
              request.form['order_no'], vid, doc), commit=True)
    flash('Module added!', 'success')
    return redirect(url_for('admin_modules'))

# ── ADMIN: USERS ──────────────────────────────────────────
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = db_query("SELECT u.*,r.role_name FROM User u JOIN Role r ON u.role_id=r.role_id ORDER BY u.created_at DESC")
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/delete/<int:uid>')
@login_required
@admin_required
def admin_delete_user(uid):
    db_query("DELETE FROM User WHERE user_id=%s", (uid,), commit=True)
    flash('User deleted.', 'warning')
    return redirect(url_for('admin_users'))

# ── ADMIN: QUESTIONS ──────────────────────────────────────
@app.route('/admin/questions')
@login_required
@admin_required
def admin_questions():
    questions = db_query("SELECT q.*,m.module_title,s.correct_option FROM Questions q JOIN Module m ON q.module_id=m.module_id LEFT JOIN Solution s ON s.question_id=q.question_id")
    modules = db_query("SELECT module_id,module_title FROM Module")
    return render_template('admin/questions.html', questions=questions, modules=modules)

@app.route('/admin/questions/add', methods=['POST'])
@login_required
@admin_required
def admin_add_question():
    qid = db_query("INSERT INTO Questions (module_id,question_text,option_a,option_b,option_c,option_d) VALUES (%s,%s,%s,%s,%s,%s)",
                   (request.form['module_id'], request.form['question_text'],
                    request.form['option_a'], request.form['option_b'],
                    request.form['option_c'], request.form['option_d']), commit=True)
    db_query("INSERT INTO Solution (question_id,correct_option,explanation) VALUES (%s,%s,%s)",
             (qid, request.form['correct_option'], request.form['explanation']), commit=True)
    flash('Question added!', 'success')
    return redirect(url_for('admin_questions'))

# ── ADMIN: ZOOM CLASSES ───────────────────────────────────
@app.route('/admin/zoom')
@login_required
@admin_required
def admin_zoom():
    classes = db_query("SELECT z.*,c.course_name FROM Zoom_Classes z JOIN Course c ON z.course_id=c.course_id ORDER BY z.class_date")
    courses = db_query("SELECT course_id,course_name FROM Course")
    return render_template('admin/zoom.html', classes=classes, courses=courses)

@app.route('/admin/zoom/add', methods=['POST'])
@login_required
@admin_required
def admin_add_zoom():
    db_query("INSERT INTO Zoom_Classes (course_id,class_title,zoom_link,class_date,instructor) VALUES (%s,%s,%s,%s,%s)",
             (request.form['course_id'], request.form['class_title'],
              request.form['zoom_link'], request.form['class_date'], request.form['instructor']), commit=True)
    flash('Zoom class added!', 'success')
    return redirect(url_for('admin_zoom'))

# ── ADMIN: ANALYTICS API ──────────────────────────────────
@app.route('/admin/api/stats')
@login_required
@admin_required
def admin_stats_api():
    enrollments_by_cat = db_query("""
        SELECT cat.category_name, COUNT(*) AS total
        FROM Enrollment e JOIN Course c ON e.course_id=c.course_id
        JOIN Category cat ON c.category_id=cat.category_id
        GROUP BY cat.category_name""")
    monthly_revenue = db_query("""
        SELECT DATE_FORMAT(created_at,'%b') AS month, SUM(price) AS revenue
        FROM Orders WHERE payment_status='paid'
        GROUP BY MONTH(created_at) ORDER BY MONTH(created_at)""")
    return jsonify({'enrollments': list(enrollments_by_cat), 'revenue': list(monthly_revenue)})

# ── ADMIN: CATEGORIES ─────────────────────────────────────
@app.route('/admin/categories/add', methods=['POST'])
@login_required
@admin_required
def admin_add_category():
    db_query("INSERT INTO Category (category_name) VALUES (%s)", (request.form['category_name'],), commit=True)
    flash('Category added!', 'success')
    return redirect(url_for('admin_courses'))

# ── COURSES LISTING ───────────────────────────────────────
@app.route('/courses')
def courses_page():
    cat_id = request.args.get('cat', '')
    search = request.args.get('q', '')
    if cat_id:
        courses = db_query("SELECT c.*,cat.category_name FROM Course c LEFT JOIN Category cat ON c.category_id=cat.category_id WHERE c.category_id=%s", (cat_id,))
    elif search:
        courses = db_query("SELECT c.*,cat.category_name FROM Course c LEFT JOIN Category cat ON c.category_id=cat.category_id WHERE c.course_name LIKE %s", (f'%{search}%',))
    else:
        courses = db_query("SELECT c.*,cat.category_name FROM Course c LEFT JOIN Category cat ON c.category_id=cat.category_id")
    cats = db_query("SELECT * FROM Category")
    return render_template('courses.html', courses=courses, cats=cats)

if __name__ == '__main__':
    app.run(debug=True)
