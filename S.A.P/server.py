from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField
from wtforms.csrf.session import SessionCSRF
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import re
import os

load_dotenv()
Sign_up_TEMPLATE = 'Sign-up.html'
app = Flask(__name__, template_folder='templates')

csrf = CSRFProtect(app)
csrf.init_app(app)
app.config['WTF_CSRF_ENABLED'] = True


app.secret_key = os.getenv("MY_SECRET_KEY")


app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


bcrypt = Bcrypt(app)
mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'database'


class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM login WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        user = User()
        user.id = user_data[0]
        user.name = user_data[1]
        user.email = user_data[2]
        return user
    return None

class MyForm(FlaskForm):
    name = StringField('Name')
    email = StringField('Email')
    password = PasswordField('Password')
    submit = SubmitField('Submit')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/My_blog/Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM login WHERE email = %s", (email,))
        user_data = cur.fetchone()
        cur.close()

        if user_data and bcrypt.check_password_hash(user_data[3], password):
            user = User()
            user.id = user_data[0]
            user.name = user_data[1]
            user.email = user_data[2]

            login_user(user)
            return redirect(url_for('home'))

        else:
            flash('Invalid email or password', 'error')

    return render_template('Login.html')


email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$')

def is_valid_email(email):
    return bool(email_pattern.match(email))

password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[!-,._])[A-Za-z!-,._0-9]{8,}$')

def is_valid_password(password):
    return bool(password_pattern.match(password))


@app.route('/My_blog/Register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if not is_valid_email(email):
            flash('Invalid email format. Please use a valid email address.', 'error')
            return render_template(Sign_up_TEMPLATE, error_message='Invalid email format. Please use a valid email address.')

        if not is_valid_password(password):
            flash('Password must contain at least one lowercase letter, one uppercase letter, and one special character (! - . _) and must be at least 8 characters long.', 'error')
            return render_template(Sign_up_TEMPLATE, error_message='Password must contain at least one lowercase letter, one uppercase letter, and one special character (!-,._) and must be at least 8 characters long.')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM login WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        cur.close()

        if existing_user:
            flash('Email already exists. Please use a different email.', 'error')
            return render_template(Sign_up_TEMPLATE, error_message='Email already exists. Please use a different email.')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO login (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        mysql.connection.commit()
        cur.close()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template(Sign_up_TEMPLATE)

@app.route('/My_blog/Home')
@login_required
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT title, description FROM recipes")
    recipes = cur.fetchall()
    cur.close()
    return render_template('home.html', recipes=recipes)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=False)
