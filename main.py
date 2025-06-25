import sqlite3
import eventlet
import os
eventlet.monkey_patch()
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_socketio import SocketIO, emit
from datetime import datetime
import bleach
import threading
import os
import time
from werkzeug.utils import secure_filename
from flask import jsonify
from functools import wraps
import requests
from PIL import Image
import mutagen
import logging

app = Flask(__name__)
app.secret_key = '12345'

UPLOAD_FOLDER = 'static/chat_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov', 'jfif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/upload_media', methods=['POST'])
def upload_media():
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    media_type = 'video' if file.mimetype.startswith('video/') else 'image'

    try:
        # 1. Save the uploaded file first
        file.save(filepath)

        # 2. Process the saved file to strip metadata
        if media_type == 'image':
            with Image.open(filepath) as image:
                # This process removes EXIF data
                data = list(image.getdata())
                image_without_exif = Image.new(image.mode, image.size)
                image_without_exif.putdata(data)
                image_without_exif.save(filepath)

        elif media_type == 'video':
            try:
                # This process removes metadata tags from video/audio
                video_file = mutagen.File(filepath)
                if video_file:
                    video_file.delete()
                    video_file.save()
            except Exception as e:
                # If mutagen fails, the original file remains. Log the error.
                logging.error(f"Could not strip metadata from video '{filename}': {e}")
                pass

    except Exception as e:
        logging.error(f"Failed to process and save file '{filename}': {e}")
        return jsonify({'error': 'Failed to process file.'}), 500

    return jsonify({
        'url': f'/static/chat_uploads/{filename}',
        'media_type': media_type
    })



@app.route('/chat/hacking')
def chat_hacking():
    if 'user_name' not in session:
        return redirect(url_for('sign_in'))
    else:
        return render_template('chat_hacking.html', username=session['user_name'])

@app.route('/chat/carding')
def chat_carding():
    if 'user_name' not in session:
        return redirect(url_for('sign_in'))
    else:
        return render_template('chat_carding.html', username=session['user_name'])

@app.route('/chat/marketplace')
def chat_marketplace():
    if 'user_name' not in session:
        return redirect(url_for('sign_in'))
    else:
        return render_template('chat_marketplace.html', username=session['user_name'])

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'Admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def get_db_connection():
    conn = sqlite3.connect('my_blogs.db')
    conn.row_factory = sqlite3.Row
    return conn


def is_valid_image_url(url):
    if not url:
        return False
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if content_type.startswith('image/'):
                return True
    except requests.RequestException:
        return False
    return False


@app.route('/')
def index():
    items = []
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 8").fetchall()
        for row in rows:
            items.append(dict(row))
    return render_template('index.html', items=items)


@app.route('/add_question', methods=['POST'])
def add_question():
    question = request.form.get('question')


    if 'user' in session and 'user_name' in session:
        name = session['user_name']
        mail = session['user']
    else:

        name = request.form.get('name')
        mail = request.form.get('mail')


    if not name or not mail or not question:
        flash("გთხოვთ შეავსეთ ყველა ველი", "danger")
        return redirect(url_for('contact'))

    with get_db_connection() as conn:
        conn.execute('INSERT INTO contacts (name, email, question) VALUES (?, ?, ?)', (name, mail, question))

    flash("კითხვა წარმატებით გაიგზავნა!", "success")
    return redirect(url_for('contact'))


@app.route('/about_us')
def about_us():
    return render_template('about_us.html')


@app.route('/rules')
def rules():
    return render_template('rules.html')


@app.route('/contact')
def contact():
    questions = []
    # If a user is logged in, fetch their past questions to display on the page
    if 'user' in session:
        with get_db_connection() as conn:
            questions = conn.execute(
                "SELECT * FROM contacts WHERE email = ? ORDER BY id DESC",
                (session['user'],)
            ).fetchall()
    return render_template('contact.html', questions=questions)


@app.route('/leaks')
def leaks():
    return render_template('leaks.html')


def get_value(name):
    return (request.form.get(name) or request.args.get(name) or "").strip()


@app.route('/lookup', methods=['GET', 'POST'])
def lookup():
    results = []
    total = 0
    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    field_map = {
        "piradi_nomeri": "პირადი_ნომერი",
        "gvari": "გვარი",
        "saxeli": "სახელი",
        "mamis_saxeli": "მამის_სახელი",
        "dabadebis_weli": "დაბადების_წელი",
        "dmonac": "dmonac",
        "sqesi": "სქესი",
        "mowmibis_nomeri": "მოწმობის_ნომერი",
        "qucha": "ქუჩა",
        "raioni": "რაიონი"
    }

    fields = {db_col: get_value(input_name) for input_name, db_col in field_map.items()}

    if any(fields.values()):
        select_columns = list(fields.keys())
        query = f"SELECT {', '.join([f'`{col}`' for col in select_columns])} FROM ადამიანები WHERE 1=1"
        values = []

        for column, value in fields.items():
            if value:
                query += f" AND `{column}` = ?"
                values.append(value)

        paginated_query = query + " LIMIT ? OFFSET ?"
        count_query = f"SELECT COUNT(*) FROM ({query})"

        conn = sqlite3.connect('samuqalaqo.db')
        cursor = conn.cursor()
        cursor.execute(paginated_query, values + [per_page, offset])
        results = cursor.fetchall()

        cursor.execute(count_query, values)
        total = cursor.fetchone()[0]
        conn.close()

    return render_template(
        'infolookup.html',
        results=results,
        fields=fields,
        page=page,
        total=total,
        per_page=per_page
    )


@app.route('/leaks/e-whoring')
def ewhoring():
    return render_template('e-whoring.html')


@app.route('/leaks/carding')
def carding():
    return render_template('carding.html')


@app.route('/announcement/<int:id>')
def show_announcement(id):
    with get_db_connection() as conn:
        announcement = conn.execute("SELECT * FROM announcement WHERE id = ?", (id,)).fetchone()
    return render_template('show_announcement.html', announcement=announcement)

@app.route('/announcement')
def announcement():
    with get_db_connection() as conn:
        announcements = conn.execute("SELECT * FROM announcement ORDER BY id DESC").fetchall()
    return render_template('announcement.html', announcements=announcements)
@app.route('/posts')
def posts():
    search = request.args.get('search-value')
    with get_db_connection() as conn:
        if search:
            rows = conn.execute("SELECT * FROM posts WHERE title LIKE ?", ('%' + search + '%',)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM posts").fetchall()
    return render_template('posts.html', posts=[dict(row) for row in rows])


@app.route('/posts/<int:id>')
def show_post(id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (id,)).fetchone()
    return render_template('show_post.html', post=dict(row))


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        user_email = request.form.get('email')
        user_password = request.form.get('password')
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (user_email,)).fetchone()

        if row and row['status'] == 'banned':
            # This line has been changed to your custom message
            return render_template('sign_in.html', error="ბანი გადევს ბანიიი!!!")

        if row and row['password'] == user_password:
            session.permanent = True
            session['user'] = user_email
            session['user_id'] = row['id']
            session['user_name'] = row['username']
            session['role'] = row['role']

            if session['role'] == 'Admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('profile'))
        else:
            return render_template('sign_in.html', error="Invalid email or password")
    return render_template('sign_in.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_name', None)
    session.pop('role', None)
    return redirect(url_for('sign_in'))


@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html', user=session['user_name'])


@app.route('/admin_contacts')
@admin_required
def admin_contacts():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM contacts").fetchall()
    return render_template('admin_contacts.html', questions=[dict(row) for row in rows])


@app.route('/admin/create_items', methods=['GET', 'POST'])
@admin_required
def create_items():
    with get_db_connection() as conn:
        if request.method == 'POST':
            conn.execute('''
                         INSERT INTO posts (title, short_description, description, post_part1, post_part2, author,
                                            imageURL)
                         VALUES (?, ?, ?, ?, ?, ?, ?)
                         ''', (
                             request.form.get('title'),
                             request.form.get('short_description'),
                             request.form.get('description'),
                             request.form.get('post_part1'),
                             request.form.get('post_part2'),
                             request.form.get('author'),
                             request.form.get('imageURL'),
                         ))
        rows = conn.execute("SELECT * FROM posts").fetchall()
    return render_template('create_items.html', posts=[dict(row) for row in rows])



@app.route('/admin/delete_item/<int:id>')
@admin_required
def delete_item(id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (id,))
        rows = conn.execute("SELECT * FROM posts").fetchall()
    return render_template('create_items.html', posts=[dict(row) for row in rows])


@app.route('/admin/announcement', methods=['GET', 'POST'])
@admin_required
def add_announcement():
    with get_db_connection() as conn:
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            post_part1 = request.form.get('post_part1')
            imageURL = request.form.get('imageURL')

            if not is_valid_image_url(imageURL):
                flash("არასწორი URL", "danger")
                return redirect(url_for('add_announcement'))

            conn.execute('''
                         INSERT INTO announcement (title, description, post_part1, imageURL)
                         VALUES (?, ?, ?, ?)
                         ''', (title, description, post_part1, imageURL))

            conn.commit()
            flash("Announcement created successfully!", "success")
            return redirect(url_for('add_announcement'))

        rows = conn.execute("SELECT * FROM announcement ORDER BY id DESC").fetchall()
    return render_template('add_announcement.html', announcements=[dict(row) for row in rows])

@app.route('/admin/delete_announcement/<int:id>')
@admin_required
def delete_announcement(id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM announcement WHERE id = ?", (id,))
        conn.commit()
    return redirect(url_for('add_announcement'))


@app.route('/admin/update_item/<int:id>', methods=['GET', 'POST'])
@admin_required
def update_item(id):
    with get_db_connection() as conn:
        if request.method == 'POST':
            conn.execute('''
                         UPDATE posts
                         SET title             = ?,
                             short_description = ?,
                             description       = ?,
                             post_part1        = ?,
                             post_part2        = ?,
                             author            = ?,
                             imageURL          = ?
                         WHERE id = ?
                         ''', (
                             request.form.get('title'),
                             request.form.get('short_description'),
                             request.form.get('description'),
                             request.form.get('post_part1'),
                             request.form.get('post_part2'),
                             request.form.get('author'),
                             request.form.get('imageURL'),
                             id
                         ))
            return redirect(url_for('create_items'))
        else:
            row = conn.execute("SELECT * FROM posts WHERE id = ?", (id,)).fetchone()
            return render_template('update_item.html', post=dict(row))

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')  # not hashed
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent')

        with get_db_connection() as conn:
            # Create users table if it doesn't exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'Member',
                    status TEXT NOT NULL DEFAULT 'active',
                    avatar_url TEXT,
                    banner_url TEXT,
                    bio TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')

            # Optional other tables
            conn.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT, short_description TEXT, description TEXT,
                    post_part1 TEXT, post_part2 TEXT, author TEXT, imageURL TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, email TEXT, question TEXT
                )
            ''')

            # Check if user or email already exists
            if conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone() or \
               conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone():
                return render_template("register.html", error="Username or Email already exists")

            # Insert into database with all 5 values
            conn.execute('''
                INSERT INTO users (username, email, password, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password, ip_address, user_agent))

        return redirect(url_for('sign_in'))

    return render_template('register.html')


@app.route('/chat')
def chat():
    if 'user_name' not in session:
        return redirect(url_for('sign_in'))
    return render_template('chat.html', username=session['user_name'])


socketio = SocketIO(app)

messages = []
messages_hacking = []
messages_carding = []
messages_marketplace = []



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_blogs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@socketio.on('send_hacking')
def handle_hacking_chat(data):
    username = session.get('user_name')
    time_now = datetime.now().strftime('%H:%M:%S')
    msg = bleach.clean(data.get('msg', ''))[:500]
    img = data.get('img')
    message = {'user': username, 'msg': msg, 'img': img, 'time': time_now}
    messages_hacking.append(message)
    socketio.emit('hacking_message', message)

def clear_chat_hacking():
    while True:
        eventlet.sleep(5)
        messages_hacking.clear()
        socketio.emit('clear_hacking')


@socketio.on('send_carding')
def handle_carding_chat(data):
    username = session.get('user_name')
    time_now = datetime.now().strftime('%H:%M:%S')
    msg = bleach.clean(data.get('msg', ''))[:500]
    img = data.get('img')
    message = {'user': username, 'msg': msg, 'img': img, 'time': time_now}
    messages_carding.append(message)
    socketio.emit('carding_message', message)

def clear_chat_carding():
    while True:
        eventlet.sleep(5)
        messages_hacking.clear()
        socketio.emit('clear')

@socketio.on('send_marketplace')
def handle_marketplace_chat(data):
    username = session.get('user_name')
    time_now = datetime.now().strftime('%H:%M:%S')
    msg = bleach.clean(data.get('msg', ''))[:500]
    img = data.get('img')
    message = {'user': username, 'msg': msg, 'img': img, 'time': time_now}
    messages_marketplace.append(message)
    socketio.emit('marketplace_message', message)

def clear_chat_marketplace():
    while True:
        eventlet.sleep(5)
        messages_hacking.clear()
        socketio.emit('clear')

def clear_chat():
    while True:
        eventlet.sleep(5)
        messages.clear()
        socketio.emit('clear')


threading.Thread(target=clear_chat, daemon=True).start()
threading.Thread(target=clear_chat_hacking, daemon=True).start()
threading.Thread(target=clear_chat_carding, daemon=True).start()
threading.Thread(target=clear_chat_marketplace, daemon=True).start()


def cleanup_uploads():
    while True:
        now = time.time()
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                if now - os.path.getmtime(filepath) > 3600:
                    os.remove(filepath)
        eventlet.sleep(3600)


threading.Thread(target=cleanup_uploads, daemon=True).start()


@socketio.on('send')
def handle_send(data):
    username = session.get('user_name')
    if not username:
        return

    with get_db_connection() as conn:
        user = conn.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()

    role = user['role'] if user else ''
    style_class = ''
    if role == 'VIP': style_class = 'vip-glow'
    elif role == 'Respected Member': style_class = 'respected-glow'
    elif role == 'Admin': style_class = 'admin-glow'

    message = {
        'user': username,
        'msg': bleach.clean(data.get('msg', ''))[:500],
        'media_url': data.get('media_url'),
        'media_type': data.get('media_type'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'style_class': style_class
    }
    messages.append(message)
    socketio.emit('message', message)

@socketio.on('send')
def handle_send(data):
    username = session.get('user_name')
    if not username:
        return

    with get_db_connection() as conn:
        user = conn.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()

    role = user['role'] if user else ''
    style_class = ''
    if role == 'VIP': style_class = 'vip-glow'
    elif role == 'Respected Member': style_class = 'respected-glow'
    elif role == 'Admin': style_class = 'admin-glow'

    message = {
        'user': username,
        'msg': bleach.clean(data.get('msg', ''))[:500],
        'media_url': data.get('media_url'),
        'media_type': data.get('media_type'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'style_class': style_class
    }
    messages.append(message)
    socketio.emit('message', message)


@socketio.on('load')
def handle_load():
    for m in messages:
        emit('message', m)


@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('sign_in'))

    with get_db_connection() as conn:
        user_data = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (session['user'],)
        ).fetchone()

        user_posts = conn.execute(
            "SELECT * FROM posts WHERE author = ? ORDER BY id DESC",
            (user_data['username'],)
        ).fetchall()

        user_questions = conn.execute(
            "SELECT * FROM contacts WHERE email = ? ORDER BY id DESC",
            (user_data['email'],)
        ).fetchall()

    return render_template('profile.html', user=user_data, posts=user_posts, questions=user_questions)


@app.route('/admin/respond/<int:question_id>', methods=['POST'])
@admin_required
def respond_to_question(question_id):
    response_text = request.form.get('response')
    if not response_text:
        flash("Response cannot be empty.", "danger")
        return redirect(url_for('admin_contacts'))

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE contacts SET response = ? WHERE id = ?",
            (response_text, question_id)
        )
        conn.commit()

    flash("Response sent successfully.", "success")
    return redirect(url_for('admin_contacts'))


@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return redirect(url_for('sign_in'))

    banner_url = request.form.get('banner_url')
    avatar_url = request.form.get('avatar_url')
    bio = request.form.get('bio', '')

    if len(bio) > 300:
        flash("შენი ბიო ვერ იქნება 300 ასოზე მეტი", "danger")
        return redirect(url_for('profile'))

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET banner_url = ?, avatar_url = ?, bio = ? WHERE id = ?",
            (banner_url, avatar_url, bio, session['user_id'])
        )

    flash("პროფილი წარმატებით განახლდა", "success")
    return redirect(url_for('profile'))


@app.route('/profile/addpost', methods=['GET', 'POST'])
def addpost():
    if 'user' not in session:
        return redirect(url_for('sign_in'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        imageURL = form_data.get('imageURL')

        if not is_valid_image_url(imageURL):
            error_message = "არასწორი URL images"
            return render_template('addpost.html', error=error_message, post=form_data)

        title = form_data.get('title')
        short_description = form_data.get('short_description')
        description = form_data.get('description')
        post_part1 = form_data.get('post_part1')
        post_part2 = form_data.get('post_part2')
        author = session.get('user_name')

        if not author:
            return "Error: User not logged in properly.", 403

        with get_db_connection() as conn:
            conn.execute('''
                         INSERT INTO posts (title, short_description, description, post_part1, post_part2, author,
                                            imageURL)
                         VALUES (?, ?, ?, ?, ?, ?, ?)
                         ''', (title, short_description, description, post_part1, post_part2, author, imageURL))

        return redirect(url_for('posts'))

    return render_template('addpost.html', post={})



@app.route('/leaks/carding/GlovoWolt')
def glovo_wolt():
    return render_template('glovo&wolt.html')


@app.context_processor
def inject_user_style():
    def get_user_style_class(username):
        if not username:
            return ''
        with get_db_connection() as conn:
            user = conn.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()

        if user:
            if user['role'] == 'VIP':
                return 'vip-glow'
            elif user['role'] == 'Respected Member':
                return 'respected-glow'
            elif user['role'] == 'Admin':
                return 'admin-glow'
        return ''

    return dict(get_user_style_class=get_user_style_class)


@app.route('/admin/members')
@admin_required
def admin_members():
    with get_db_connection() as conn:
        users = conn.execute("SELECT id, username, email, role, status FROM users ORDER BY id").fetchall()

    roles = ['Member', 'VIP', 'Respected Member', 'Admin']
    statuses = ['active', 'banned']

    return render_template('adm_members.html', users=users, roles=roles, statuses=statuses)


@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
@admin_required
def update_user(user_id):

    if user_id == session.get('user_id'):
        flash("You cannot edit your own role or status.", "danger")
        return redirect(url_for('admin_members'))

    new_role = request.form.get('role')
    new_status = request.form.get('status')

    if new_role not in ['Member', 'VIP', 'Respected Member', 'Admin'] or new_status not in ['active', 'banned']:
        flash('Invalid role or status selected.', 'danger')
        return redirect(url_for('admin_members'))

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET role = ?, status = ? WHERE id = ?",
            (new_role, new_status, user_id)
        )

    flash(f"User #{user_id} has been updated.", "success")
    return redirect(url_for('admin_members'))


if __name__ == '__main__':
    socketio.run(app, debug=True)