from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from collections import Counter
from datetime import datetime
import os


# ---------------- HELPERS ----------------

def time_ago(dt):
    if not dt:
        return "just now"

    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds // 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds // 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


# ---------------- INIT ----------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///site.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


# ---------------- MODELS ----------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(150), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    comments = db.relationship(
        "Comment",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    user = db.relationship("User", backref="comments")
    project = db.relationship("Project", back_populates="comments")
    reactions = db.relationship(
        "CommentReaction",
        back_populates="comment",
        cascade="all, delete-orphan",
        lazy=True,
    )


class CommentReaction(db.Model):
    __tablename__ = "comment_reactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=False)
    reaction = db.Column(db.String(10), nullable=False)

    comment = db.relationship("Comment", back_populates="reactions")

    __table_args__ = (
        db.UniqueConstraint("user_id", "comment_id", name="unique_user_comment"),
    )


# ---------------- STATIC ----------------

@app.route("/sitemap.xml")
def sitemap():
    sitemap_path = os.path.join("static", "sitemap.xml")
    if os.path.exists(sitemap_path):
        return send_from_directory("static", "sitemap.xml", mimetype="application/xml")
    abort(404)


# ---------------- ROUTES ----------------

@app.route("/")
def index():
    projects = Project.query.order_by(Project.id.desc()).all()
    return render_template("index.html", projects=projects)


@app.route("/main")
def main():
    projects = Project.query.order_by(Project.id.desc()).all()
    return render_template("main.html", projects=projects)


@app.route("/Projects/<slug>")
def project_detail(slug):
    project = Project.query.filter_by(slug=slug).first_or_404()

    comments = Comment.query.filter_by(project_id=project.id) \
        .order_by(Comment.created_at.desc()) \
        .all()

    current_user_id = session.get("user_id")

    for comment in comments:
        counts = Counter(r.reaction for r in comment.reactions if r.reaction)
        comment.reaction_counts = {
            "❤️": counts.get("❤️", 0),
            "😂": counts.get("😂", 0),
            "🔥": counts.get("🔥", 0),
            "👍": counts.get("👍", 0),
        }

        comment.time_ago = time_ago(comment.created_at)
        comment.user_reaction = None

    return render_template(
        f"Projects/{slug}.html",
        project=project,
        comments=comments,
    )


@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        flash("Password reset link sent (mock).", "info")
        return redirect(url_for("login"))
    return render_template("reset.html")


# ---------------- ADMIN ----------------

@app.route("/admin/add_project", methods=["GET", "POST"])
def add_project():
    user = User.query.get(session.get("user_id"))

    if not user or not user.is_admin:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        slug = request.form.get("slug", "").strip()

        if not title or not description or not slug:
            flash("All fields are required.", "danger")
            return redirect(url_for("add_project"))

        if Project.query.filter_by(slug=slug).first():
            flash("Slug already exists.", "danger")
            return redirect(url_for("add_project"))

        project = Project(
            title=title,
            description=description,
            slug=slug,
        )

        db.session.add(project)
        db.session.commit()

        flash("Project added successfully.", "success")
        return redirect(url_for("main"))

    return render_template("admin/add_project.html")


@app.route("/admin/delete_project/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    user = User.query.get(session.get("user_id"))

    if not user or not user.is_admin:
        abort(403)

    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()

    flash("Project deleted.", "info")
    return redirect(url_for("main"))


# ---------------- COMMENTS ----------------

@app.route("/add_comment/<int:project_id>", methods=["POST"])
def add_comment(project_id):
    if "user_id" not in session:
        flash("Login required to comment.", "warning")
        return redirect(url_for("login"))

    project = Project.query.get_or_404(project_id)
    content = request.form.get("content", "").strip()

    if not content:
        flash("Comment cannot be empty.", "danger")
        return redirect(url_for("project_detail", slug=project.slug))

    new_comment = Comment(
        content=content,
        user_id=session["user_id"],
        project_id=project_id,
    )

    db.session.add(new_comment)
    db.session.commit()

    flash("Comment posted.", "success")
    return redirect(url_for("project_detail", slug=project.slug))


@app.route("/edit_comment/<int:comment_id>", methods=["POST"])
def edit_comment(comment_id):
    if "user_id" not in session:
        abort(403)

    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != session["user_id"]:
        abort(403)

    content = request.form.get("content", "").strip()
    if not content:
        flash("Comment cannot be empty.", "danger")
        return redirect(url_for("project_detail", slug=comment.project.slug))

    comment.content = content
    db.session.commit()

    flash("Comment updated.", "success")
    return redirect(url_for("project_detail", slug=comment.project.slug))


@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    if "user_id" not in session:
        abort(403)

    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != session["user_id"]:
        abort(403)

    project_slug = comment.project.slug

    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted.", "info")
    return redirect(url_for("project_detail", slug=project_slug))


@app.route("/react_comment/<int:comment_id>", methods=["POST"])
def react_comment(comment_id):
    if "user_id" not in session:
        abort(403)

    reaction = request.form.get("reaction", "")  # ← get from form
    allowed = {"❤️", "😂", "🔥", "👍"}
    if reaction not in allowed:
        abort(400)

    comment = Comment.query.get_or_404(comment_id)

    existing = CommentReaction.query.filter_by(
        user_id=session["user_id"],
        comment_id=comment_id,
    ).first()

    if existing:
        if existing.reaction == reaction:
            db.session.delete(existing)
        else:
            existing.reaction = reaction
    else:
        db.session.add(CommentReaction(
            user_id=session["user_id"],
            comment_id=comment_id,
            reaction=reaction,
        ))

    db.session.commit()
    return redirect(url_for("project_detail", slug=comment.project.slug))


# ---------------- AUTH ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Account created. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username

            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))

        flash("Invalid login details.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


# ---------------- HIRE ME ----------------

@app.route("/hire-me", methods=["GET", "POST"])
def hire_me():
    if request.method == "POST":
        return "Thanks! I'll get back to you soon."
    return render_template("hire_me.html")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)