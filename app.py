from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

from collections import Counter

def time_ago(dt):
    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        months = int(seconds // 2592000)
        return f"{months} month{'s' if months > 1 else ''} ago"


# ---------------- INIT ----------------
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///site.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



migrate = Migrate(app, db)
# ---------------- MODELS ----------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(150), nullable=False)

    __table_args__ = (
    db.UniqueConstraint('slug', name='uq_project_slug'),
)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('User', backref='comments')
    project = db.relationship('Project', backref='comments')


class CommentReaction(db.Model):
    __tablename__ = "comment_reactions"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)

    reaction = db.Column(db.String(10))  # ❤️ 😂 🔥 👍

    # prevent duplicate reactions
    __table_args__ = (
        db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment'),
    )


# ---------------- CREATE TABLES ----------------


# ---------------- STATIC ----------------
@app.route('/sitemap.xml')
def sitemap():
    sitemap_path = os.path.join('static', 'sitemap.xml')
    if os.path.exists(sitemap_path):
        return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')
    else:
        abort(404)


# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/main')
def main():
    projects = Project.query.all()
    return render_template('main.html', projects=projects)


# 🔥 NEW SLUG-BASED ROUTE
@app.route('/project/<slug>')
def project_detail(slug):
    project = Project.query.filter_by(slug=slug).first_or_404()

    comments = Comment.query.filter_by(project_id=project.id)\
                            .order_by(Comment.created_at.desc())\
                            .all()
    for comment in comments:
        reactions = CommentReaction.query.filter_by(comment_id=comment.id).all()

        counts = Counter(r.reaction for r in reactions)

        comment.reaction_counts = {
            "❤️": counts.get("❤️", 0),
            "😂": counts.get("😂", 0),
            "🔥": counts.get("🔥", 0),
            "👍": counts.get("👍", 0),
        }

    for comment in comments:
        comment.time_ago = time_ago(comment.created_at)
    
    return render_template(
            f"Projects/{slug}.html",
            project=project,
            comments=comments
        )


@app.route('/edit_comment/<int:comment_id>', methods=['POST'])
def edit_comment(comment_id):
    if 'user_id' not in session:
        abort(403)

    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != session['user_id']:
        abort(403)

    comment.content = request.form['content']
    db.session.commit()

    flash("Comment updated", "success")
    return redirect(url_for('project_detail', slug=comment.project.slug))


@app.route('/like_comment/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.likes += 1
    db.session.commit()

    return redirect(request.referrer)

# ---------------- RESET ----------------
@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        flash("Password reset link sent (mock).", "info")
        return redirect(url_for('login'))

    return render_template('reset.html')


# ---------------- ADMIN ----------------

@app.route('/admin/add_project', methods=['GET', 'POST'])
def add_project():
    user = User.query.get(session.get('user_id'))

    if not user or not user.is_admin:
        abort(403)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        slug = request.form['slug']

        # 🔥 check duplicate slug
        if Project.query.filter_by(slug=slug).first():
            flash("Slug already exists!", "danger")
            return redirect(url_for('add_project'))

        project = Project(
            title=title,
            description=description,
            slug=slug
        )

        db.session.add(project)
        db.session.commit()

        flash("Project added!", "success")
        return redirect(url_for('main'))

    return render_template('admin/add_project.html')


@app.route('/admin/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    user = User.query.get(session.get('user_id'))

    if not user or not user.is_admin:
        abort(403)

    project = Project.query.get_or_404(project_id)

    db.session.delete(project)
    db.session.commit()

    flash("Project deleted", "info")
    return redirect(url_for('main'))


# ---------------- COMMENTS ----------------

@app.route('/add_comment/<int:project_id>', methods=['POST'])
def add_comment(project_id):
    if 'user_id' not in session:
        flash("Login required", "warning")
        return redirect(url_for('login'))

    new_comment = Comment(
        content=request.form['content'],
        user_id=session['user_id'],
        project_id=project_id
    )

    db.session.add(new_comment)
    db.session.commit()

    return redirect(url_for('project_detail', slug=Project.query.get(project_id).slug))


@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'user_id' not in session:
        abort(403)

    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != session['user_id']:
        abort(403)

    project_slug = Project.query.get(comment.project_id).slug

    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted", "info")
    return redirect(url_for('project_detail', slug=project_slug))


@app.route('/react_comment/<int:comment_id>/<reaction>', methods=['POST'])
def react_comment(comment_id, reaction):
    if 'user_id' not in session:
        abort(403)

    user_id = session['user_id']

    existing = CommentReaction.query.filter_by(
        user_id=user_id,
        comment_id=comment_id
    ).first()

    if existing:
        # change reaction
        existing.reaction = reaction
    else:
        new_reaction = CommentReaction(
            user_id=user_id,
            comment_id=comment_id,
            reaction=reaction
        )
        db.session.add(new_reaction)

    db.session.commit()
    return redirect(request.referrer)


# ---------------- AUTH ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username exists", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email exists", "danger")
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Account created", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and user.check_password(request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username

            flash("Logged in", "success")
            return redirect(url_for('index'))

        flash("Invalid login", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for('login'))


# ---------------- HIRE ME ----------------

@app.route("/hire-me", methods=["GET", "POST"])
def hire_me():
    if request.method == "POST":
        return "Thanks! I'll get back to you soon."
    return render_template("hire_me.html")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)