from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
import os

# Initialize app
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for sessions

# Database URI (encode $ as %24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# User model
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create tables
with app.app_context():
    db.create_all()






@app.route('/sitemap.xml')
def sitemap():
    return send_file('static/sitemap.xml', mimetype='application/xml')




# ---------------- ROUTES ----------------

@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html', username=username)

@app.route('/main')
def main():
    return render_template('main.html')





# Fusion 360
@app.route("/goals_new/fusion360")
def fusion360_goal():
    return render_template("goals_new/fusion360/index.html")



# IOT Section
@app.route("/goals_new/iot")
def iot_goal():
    return render_template("goals_new/iot/index.html")


@app.route("/goals_new/iot/notes")
def iot_notes():
    return render_template("goals_new/iot/notes.html")


@app.route("/goals_new/iot/drive")
def iot_deep_dive():
    return render_template("goals_new/iot/drive.html")

# Python Section
@app.route("/goals_new/python")
def python_page():
    return render_template("goals_new/python.html")



# PCB
@app.route("/goals_new/pcb/notes")
def pcb_notes_lower():
    return render_template("goals_new/pcb/notes.html")

@app.route("/goals_new/pcb")
def pcb_goal():
    return render_template("goals_new/pcb/index.html")


# Frontend
@app.route("/goals_new/frontend/notes")
def frontend_notes():
    return render_template("goals_new/frontend/notes.html")

@app.route("/goals_new/frontend")
def frontend_goal():
    return render_template("goals_new/frontend/index.html")


# -------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for('register'))

        # Create user
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("User registered successfully! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

# -------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome, {user.username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# -------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# -------- RESET PASSWORD ----------
@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Password reset link sent to your email (mock).", "info")
        else:
            flash("Email not found.", "danger")
        return redirect(url_for('login'))

    return render_template('reset.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
