from flask import Flask, url_for, request, render_template, redirect, flash, session
import sqlite3
from datetime import datetime

#######################################################################################################################

#######################################################################################################################

app = Flask(__name__)
app.secret_key='supersecretkey'

def db_setup():
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS users(
                name TEXT PRIMARY KEY,
                password TEXT
                )""")

    cur.execute("""
                CREATE TABLE IF NOT EXISTS blog_information(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_posting TEXT,
                blog_name TEXT,
                created_date DATE,
                content TEXT,
                FOREIGN KEY (user_posting) REFERENCES users (name)
                )""")
    conn.commit()
    conn.close()

#######################################################################################################################

#######################################################################################################################

@app.route('/')
def index():
    return redirect(url_for('show_login'))

@app.route('/login')
def show_login():
    flash('The login page', 'info')
    return render_template('login.html')

@app.route('/register')
def show_register():
    flash('The register page', 'info')
    return render_template('register.html')

@app.route('/blogs')
def show_blogs():
    if 'logged_in' in session and session['logged_in']:
        conn = sqlite3.connect('users.db')
        items = conn.execute('SELECT * FROM blog_information').fetchall()
        conn.close()
        flash('Showing all posts', 'info')
        return render_template('blog_page.html', items=items)
    else:
        flash('You must log in first!')
        return redirect(url_for('show_login'))
    
@app.route('/create_blog')
def show_create_blog():
    if 'logged_in' in session and session['logged_in']:
        flash('Create a blog page', 'info')
        return render_template('create_blog.html')
    else:
        flash('You must log in first!')
        return redirect(url_for('show_login'))

#######################################################################################################################

#######################################################################################################################


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    if not username or not password:
        flash('Both username and password are required', 'error')
        return redirect(url_for('show_login'))

    user = cur.execute('SELECT name, password FROM users WHERE name = ?', (username,)).fetchone()
    conn.close()

    if user is None or user[1] != password:
        flash('Invalid username or password', 'error')
        return redirect(url_for('show_login'))
    else:
        session['logged_in'] = True
        session['username'] = username
        flash(f'Welcome back, {username}!', 'success')
        return redirect(url_for('show_blogs'))


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    username_query = cur.execute('SELECT name FROM users WHERE name = ?', (username,)).fetchone()
    if username_query is not None:  
        flash(f'Username {username} is already taken', 'error')
        return redirect(url_for('show_register'))
    
    cur.execute("INSERT INTO users VALUES (?, ?)", (username, password))
    conn.commit()
    flash(f'Successfully created your account {username}')
    return redirect(url_for('show_login'))
    

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('show_login'))


@app.route('/create_blog', methods=['POST'])
def create_blog():
    username = session.get('username')
    blog_name = request.form.get('blog_name')
    content = request.form.get('blog_content')
    content = truncate_content(content)
    created_date = datetime.now().strftime('%d/%m/%Y')

    if len(blog_name) > 30:
        flash('Blog name too long. Maximum 16 characters allowed.', 'error')
        return redirect(url_for('show_create_blog'))
    
    try:
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO blog_information (user_posting, blog_name, created_date, content)
            VALUES (?, ?, ?, ?)
        """, (username, blog_name, created_date, content))
        conn.commit()
        flash('Blog post created successfully!', 'success')
    except sqlite3.Error as e:
        flash(f'Database error: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('show_blogs'))


@app.route('/profile/<username>')
def show_profile(username):
    if 'logged_in' in session:
        conn = sqlite3.connect('users.db')
        cursor = conn.execute('SELECT * FROM users WHERE name = ?', (username,))
        user_info = cursor.fetchone()
        username = user_info[0]
        items = conn.execute('SELECT * FROM blog_information WHERE user_posting = ?', (username,)).fetchall()
        conn.close()
        
        if user_info:
            flash(f"Showing user {username}'s profile", 'info')
            return render_template('profile.html', user=username, items=items)
        else:
            flash('User not found', 'error')
            return redirect(url_for('show_blogs'))
    else:
        flash('You must log in first!', 'error')
        return redirect(url_for('show_login'))
    
#######################################################################################################################

#######################################################################################################################

def truncate_content(content, length=200):
            if len(content) > length:
                return content[:length] + '...'
            return content

#######################################################################################################################

#######################################################################################################################
if __name__ == "__main__":
    db_setup()
    app.run(debug=True)