import os
from datetime import datetime
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_

# Import our models
from models import db, User, Dish, Review

# App Setup
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", "supersecretkey")

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f'sqlite:///{os.path.join(basedir, "food_app.db")}'
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Helper Functions
def search_dishes(query):
    """Search dishes by name, description, or tags"""
    if not query:
        return Dish.query.all()

    # Split query into terms
    terms = [term.strip().lower() for term in query.split(",") if term.strip()]

    if not terms:
        return Dish.query.all()

    # Build search conditions
    search_conditions = []

    for term in terms:
        # Search in name, description, and tags
        name_condition = Dish.name.ilike(f"%{term}%")
        desc_condition = Dish.description.ilike(f"%{term}%")
        tags_condition = Dish._tags.ilike(f"%{term}%")

        search_conditions.append(or_(name_condition, desc_condition, tags_condition))

    # Combine all conditions with OR
    if search_conditions:
        final_condition = or_(*search_conditions)
        return Dish.query.filter(final_condition).all()

    return Dish.query.all()


def get_all_tags():
    """Get all unique tags from all dishes"""
    all_tags = set()
    dishes = Dish.query.all()

    for dish in dishes:
        if dish.tags:
            all_tags.update(dish.tags)

    return sorted(all_tags, key=str.lower)


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dishes", methods=["GET", "POST"])
@login_required
def list_dishes():
    all_tags = get_all_tags()
    query = request.form.get("search", "").strip() if request.method == "POST" else ""
    sort = request.form.get("sort", "name") if request.method == "POST" else "name"

    # Get filtered dishes
    filtered_dishes = search_dishes(query) if query else Dish.query.all()

    # Sort dishes
    if sort == "rating":
        filtered_dishes = sorted(
            filtered_dishes, key=lambda d: d.avg_rating or 0, reverse=True
        )
    elif sort == "name":
        filtered_dishes = sorted(filtered_dishes, key=lambda d: d.name.lower())
    elif sort == "newest":
        filtered_dishes = sorted(
            filtered_dishes, key=lambda d: d.created_at, reverse=True
        )

    return render_template(
        "dishes.html",
        dishes=filtered_dishes,
        tags=all_tags,
        current_search=query,
        current_sort=sort,
    )


@app.route("/dish/<int:dish_id>")
@login_required
def dish_detail(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    # Sort reviews by date (newest first)
    reviews = sorted(dish.reviews, key=lambda r: r.created_at, reverse=True)
    return render_template("dish_detail.html", dish=dish, reviews=reviews)


@app.route("/rate", methods=["POST"])
@login_required
def rate_dish():
    try:
        dish_id = int(request.form["dish_id"])
        rating = int(request.form["rating"])
        comment = request.form["comment"].strip()
    except (KeyError, ValueError):
        flash("Invalid form submission.", "danger")
        return redirect(request.referrer or url_for("list_dishes"))

    # Validate rating and comment
    if not (1 <= rating <= 5) or not comment:
        flash("Rating (1–5) and a comment are required.", "warning")
        return redirect(url_for("dish_detail", dish_id=dish_id))

    # Get the dish
    dish = Dish.query.get_or_404(dish_id)

    # Check if user already reviewed this dish
    existing_review = Review.query.filter_by(
        dish_id=dish_id, user_id=current_user.id
    ).first()

    if existing_review:
        # Update existing review
        existing_review.rating = rating
        existing_review.comment = comment
        existing_review.date = datetime.now().date()
        flash("Your review has been updated.", "success")
    else:
        # Create new review
        new_review = Review(
            dish_id=dish_id, user_id=current_user.id, rating=rating, comment=comment
        )
        db.session.add(new_review)
        flash("Review added successfully.", "success")

    try:
        db.session.commit()
        # Update average rating
        dish.update_avg_rating()
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while saving your review.", "danger")
        app.logger.error(f"Error saving review: {e}")

    return redirect(url_for("dish_detail", dish_id=dish_id))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("list_dishes"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        # Validation
        if not username or not password:
            flash("Username and password are required.", "warning")
        elif len(username) < 3:
            flash("Username must be at least 3 characters long.", "warning")
        elif len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
        elif User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose another.", "danger")
        else:
            # Create new user
            user = User(
                username=username, password_hash=generate_password_hash(password)
            )
            try:
                db.session.add(user)
                db.session.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("login"))
            except Exception as e:
                db.session.rollback()
                flash("An error occurred during registration.", "danger")
                app.logger.error(f"Registration error: {e}")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("list_dishes"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome back, {username}!", "success")
            next_page = request.args.get("next")
            return (
                redirect(next_page) if next_page else redirect(url_for("list_dishes"))
            )
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f"Goodbye, {username}! You have been logged out.", "info")
    return redirect(url_for("index"))


# API Routes (for future mobile app or AJAX calls)
@app.route("/api/dishes")
@login_required
def api_dishes():
    """API endpoint to get all dishes"""
    dishes = Dish.query.all()
    return jsonify([dish.to_dict() for dish in dishes])


@app.route("/api/dishes/<int:dish_id>")
@login_required
def api_dish_detail(dish_id):
    """API endpoint to get a specific dish"""
    dish = Dish.query.get_or_404(dish_id)
    return jsonify(dish.to_dict())


@app.route("/api/search")
@login_required
def api_search():
    """API endpoint for dish search"""
    query = request.args.get("q", "")
    dishes = search_dishes(query)
    return jsonify([dish.to_dict() for dish in dishes])


# Admin Routes (for development/debugging)
@app.route("/admin/stats")
@login_required
def admin_stats():
    """Simple stats page"""
    if not app.debug:
        abort(403)

    stats = {
        "total_users": User.query.count(),
        "total_dishes": Dish.query.count(),
        "total_reviews": Review.query.count(),
        "avg_rating": db.session.query(db.func.avg(Review.rating)).scalar() or 0,
        "most_reviewed_dish": db.session.query(Dish)
        .join(Review)
        .group_by(Dish.id)
        .order_by(db.func.count(Review.id).desc())
        .first(),
    }

    return jsonify(stats)


# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500


@app.errorhandler(403)
def forbidden_error(error):
    return render_template("errors/403.html"), 403


# Database initialization
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized!")


def migrate_from_json():
    """Migrate data from JSON files"""
    with app.app_context():
        from models import migrate_json_data, backup_json_data

        # Create backup first
        backup_dir = backup_json_data()
        print(f"Created backup: {backup_dir}")

        # Create tables
        db.create_all()

        # Migrate data
        migrate_json_data()
        print("Migration completed!")


# CLI Commands (run with flask command)
@app.cli.command()
def init_database():
    """Initialize the database."""
    init_db()


@app.cli.command()
def migrate_json():
    """Migrate data from JSON files to database."""
    migrate_from_json()


@app.cli.command()
def create_sample_user():
    """Create a sample admin user."""
    user = User(username="admin", password_hash=generate_password_hash("admin123"))
    try:
        db.session.add(user)
        db.session.commit()
        print("Sample admin user created (username: admin, password: admin123)")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {e}")


if __name__ == "__main__":
    # Initialize database on first run
    with app.app_context():
        db.create_all()

    app.run(debug=True)
