import os
import math
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
_SIMPLE_CACHE = {}

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


def calculate_wilson_score(dish):
    """
    Calculate Wilson score for a dish based on its reviews.
    Treats ratings of 4-5 stars as "positive" and 1-3 stars as "negative"
    This gives a more reliable ranking than simple averages.
    """
    if not dish.reviews or len(dish.reviews) == 0:
        return 0

    total_ratings = len(dish.reviews)
    positive_ratings = sum(1 for review in dish.reviews if review.rating >= 4)

    if total_ratings == 0:
        return 0

    # 95% confidence Wilson score calculation
    z = 1.96  # 95% confidence
    p = positive_ratings / total_ratings

    denominator = 1 + (z * z) / total_ratings
    numerator = (
        p
        + (z * z) / (2 * total_ratings)
        - z * math.sqrt((p * (1 - p) + (z * z) / (4 * total_ratings)) / total_ratings)
    )

    return numerator / denominator


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dishes", methods=["GET", "POST"])
@login_required
def list_dishes():
    all_tags = get_all_tags()

    # Handle both POST and GET requests
    if request.method == "POST":
        query = request.form.get("search", "").strip()
        sort = request.form.get("sort", "name")
    else:
        query = request.args.get("search", "").strip()
        sort = request.args.get("sort", "name")

    # Get filtered dishes
    filtered_dishes = search_dishes(query) if query else Dish.query.all()

    # Sort dishes
    if sort == "rating":
        # NEW: Sort by Wilson score instead of simple average
        filtered_dishes = sorted(
            filtered_dishes, key=lambda d: calculate_wilson_score(d), reverse=True
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
    """
    Comprehensive admin stats for dashboard use.

    Query params:
      start=YYYY-MM-DD       optional start date (inclusive)
      end=YYYY-MM-DD         optional end date (inclusive)
      min_reviews=N          minimum reviews for top/bottom lists (default 3)
      period=30              review trend window in days (default 30)
      export=csv             if present and equals 'csv', returns a CSV export
    """
    # Keep your debug guard
    if not app.debug:
        abort(403)

    # Helpers
    def parse_date_param(name, default_date):
        s = request.args.get(name, None)
        if not s:
            return default_date
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return default_date

    def dt_from_date(d):
        return datetime(d.year, d.month, d.day)

    def utcnow_date():
        return datetime.utcnow().date()

    # period handling (days)
    try:
        period_days = int(request.args.get("period", 30))
        if period_days < 1:
            period_days = 30
    except Exception:
        period_days = 30

    # compute default end and start
    end_date = parse_date_param("end", utcnow_date())
    # compute default_start as end_date - (period_days-1) days using timestamps
    end_ts = datetime(end_date.year, end_date.month, end_date.day).timestamp()
    start_ts = end_ts - (period_days - 1) * 86400
    start_date_guess = datetime.utcfromtimestamp(start_ts).date()

    start_date = parse_date_param("start", start_date_guess)

    # normalize if inverted
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    min_reviews = 1
    try:
        min_reviews = int(request.args.get("min_reviews", 3))
        if min_reviews < 1:
            min_reviews = 1
    except Exception:
        min_reviews = 3

    export_csv = request.args.get("export", "").lower() == "csv"

    # cache key and simple caching
    cache_key = (
        f"admin_stats:{start_date.isoformat()}:{end_date.isoformat()}:{min_reviews}"
    )
    if cache_key in _SIMPLE_CACHE:
        stats = _SIMPLE_CACHE[cache_key]
    else:
        # compute stats
        # Totals
        total_users = User.query.count()
        total_dishes = Dish.query.count()
        total_reviews = Review.query.count()
        avg_rating_row = db.session.query(db.func.avg(Review.rating)).scalar()
        avg_rating = float(avg_rating_row) if avg_rating_row is not None else 0.0

        # Most reviewed dish overall
        most_reviewed_row = (
            db.session.query(Dish, db.func.count(Review.id).label("rc"))
            .join(Review)
            .group_by(Dish.id)
            .order_by(db.func.count(Review.id).desc())
            .first()
        )
        if most_reviewed_row:
            most_reviewed_dish, most_reviewed_count = most_reviewed_row[0], int(
                most_reviewed_row[1]
            )
        else:
            most_reviewed_dish, most_reviewed_count = None, 0

        # Top and bottom dishes by avg_rating, with at least min_reviews
        dish_stats_rows = (
            db.session.query(
                Dish.id,
                Dish.name,
                Dish.avg_rating,
                db.func.count(Review.id).label("review_count"),
            )
            .outerjoin(Review)
            .group_by(Dish.id)
            .all()
        )

        # convert to plain tuples for sorting
        dish_stats = []
        for row in dish_stats_rows:
            did, dname, davg, dcount = row[0], row[1], row[2], int(row[3] or 0)
            davg_val = float(davg) if davg is not None else 0.0
            dish_stats.append((did, dname, davg_val, dcount))

        top_rated = []
        bottom_rated = []
        if dish_stats:
            # top by avg desc, tie-breaker by review_count desc
            dish_stats_sorted_top = sorted(
                dish_stats, key=lambda x: (-x[2], -x[3], x[1])
            )
            for did, name, ar, rc in dish_stats_sorted_top:
                if rc >= min_reviews:
                    top_rated.append(
                        {
                            "id": did,
                            "name": name,
                            "avg_rating": round(ar, 2),
                            "review_count": rc,
                        }
                    )
                    if len(top_rated) >= 10:
                        break

            # bottom by avg asc, tie-breaker review_count desc
            dish_stats_sorted_bottom = sorted(
                dish_stats, key=lambda x: (x[2], -x[3], x[1])
            )
            for did, name, ar, rc in dish_stats_sorted_bottom:
                if rc >= min_reviews:
                    bottom_rated.append(
                        {
                            "id": did,
                            "name": name,
                            "avg_rating": round(ar, 2),
                            "review_count": rc,
                        }
                    )
                    if len(bottom_rated) >= 10:
                        break

        # Newest dishes and latest reviews
        newest_dishes = Dish.query.order_by(Dish.created_at.desc()).limit(5).all()
        latest_reviews = Review.query.order_by(Review.created_at.desc()).limit(10).all()

        # rating distribution overall
        rating_distribution = {}
        for s in range(1, 6):
            rating_distribution[s] = Review.query.filter_by(rating=s).count()

        # reviews per day in range
        start_dt = dt_from_date(start_date)
        end_dt = dt_from_date(end_date)
        days = (end_dt - start_dt).days + 1
        review_trend = []
        for i in range(days):
            day_dt = datetime.utcfromtimestamp(start_dt.timestamp() + i * 86400)
            day_start = day_dt
            day_end = datetime.utcfromtimestamp(day_start.timestamp() + 86400)
            cnt = Review.query.filter(
                Review.created_at >= day_start,
                Review.created_at < day_end,
            ).count()
            review_trend.append({"date": day_start.date().isoformat(), "count": cnt})

        # percent change vs previous same-length period
        prev_start_ts = start_dt.timestamp() - days * 86400
        prev_start_dt = datetime.utcfromtimestamp(prev_start_ts)
        prev_end_dt = start_dt  # exclusive end is start_dt
        prev_count = Review.query.filter(
            Review.created_at >= prev_start_dt, Review.created_at < prev_end_dt
        ).count()
        cur_count = sum(r["count"] for r in review_trend)

        def pct_change(prev, cur):
            if prev == 0:
                return None if cur == 0 else 100.0
            return round((cur - prev) * 100.0 / prev, 2)

        review_percent_change = pct_change(prev_count, cur_count)

        # average and median-ish review length
        comment_rows = Review.query.with_entities(Review.comment).all()
        lengths = [len(r[0] or "") for r in comment_rows]
        avg_review_length = (
            round(float(sum(lengths)) / len(lengths), 2) if lengths else 0.0
        )
        median_review_length = None
        if lengths:
            lengths.sort()
            n = len(lengths)
            if n % 2 == 1:
                median_review_length = lengths[n // 2]
            else:
                median_review_length = (lengths[n // 2 - 1] + lengths[n // 2]) / 2

        # top reviewers
        top_reviewers_rows = (
            db.session.query(
                User.id, User.username, db.func.count(Review.id).label("rc")
            )
            .join(Review)
            .group_by(User.id)
            .order_by(db.func.count(Review.id).desc())
            .limit(10)
            .all()
        )
        top_reviewers = [
            {"id": row[0], "username": row[1], "review_count": int(row[2])}
            for row in top_reviewers_rows
        ]

        # tag usage counts and tag-level average dish rating (assumes Dish.tags is a list)
        tag_counts = {}
        tag_rating_acc = {}
        for dish in Dish.query.all():
            tags = dish.tags or []
            for t in tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
                tag_rating_acc.setdefault(t, []).append(
                    dish.avg_rating if dish.avg_rating is not None else 0.0
                )
        tag_summary = []
        # sort tags by count desc
        sorted_tags = sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
        for t, cnt in sorted_tags:
            ratings = tag_rating_acc.get(t, [])
            avg_t = round(sum(ratings) / len(ratings), 2) if ratings else None
            tag_summary.append({"tag": t, "count": cnt, "avg_rating": avg_t})

        # dish-level review counts and a sample review
        top_by_reviews_rows = (
            db.session.query(Dish.id, Dish.name, db.func.count(Review.id).label("rc"))
            .join(Review)
            .group_by(Dish.id)
            .order_by(db.func.count(Review.id).desc())
            .limit(10)
            .all()
        )
        by_reviews_sample = []
        for did, name, rc in top_by_reviews_rows:
            sample = (
                Review.query.filter(Review.dish_id == did)
                .order_by(Review.created_at.desc())
                .first()
            )
            by_reviews_sample.append(
                {
                    "id": did,
                    "name": name,
                    "review_count": int(rc),
                    "sample_review": sample.comment if sample else None,
                }
            )

        # monthly series for users and dishes (last 12 months)
        def add_months(base_dt, months):
            # months can be negative
            y = base_dt.year + (base_dt.month - 1 + months) // 12
            m = (base_dt.month - 1 + months) % 12 + 1
            return datetime(y, m, 1)

        def month_series_for(entity, months_back=12):
            dialect_name = db.engine.dialect.name if hasattr(db, "engine") else "other"
            if dialect_name == "sqlite":
                period_col = db.func.strftime("%Y-%m", entity.created_at)
            else:
                # try to_char for postgres / others
                period_col = db.func.to_char(entity.created_at, "YYYY-MM")
            q = (
                db.session.query(period_col.label("period"), db.func.count(entity.id))
                .group_by("period")
                .order_by("period")
                .all()
            )
            qmap = {str(row[0])[:7]: int(row[1]) for row in q}

            results = []
            # create months ending at current month
            now = datetime.utcnow()
            last_month_start = datetime(now.year, now.month, 1)
            for i in range(months_back - 1, -1, -1):
                mdt = add_months(last_month_start, -i)
                key = mdt.strftime("%Y-%m")
                results.append({"month": key, "count": qmap.get(key, 0)})
            return results

        users_by_month = month_series_for(User, 12)
        dishes_by_month = month_series_for(Dish, 12)

        # newest users
        newest_users = User.query.order_by(User.created_at.desc()).limit(5).all()

        # assemble stats
        stats = {
            "range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "totals": {
                "users": total_users,
                "dishes": total_dishes,
                "reviews": total_reviews,
                "avg_rating": round(avg_rating, 2),
            },
            "dishes": {
                "most_reviewed": (
                    most_reviewed_dish.to_dict() if most_reviewed_dish else None
                ),
                "most_reviewed_count": most_reviewed_count,
                "top_rated": top_rated,
                "bottom_rated": bottom_rated,
                "newest": [d.to_dict() for d in newest_dishes],
                "by_reviews_sample": by_reviews_sample,
            },
            "reviews": {
                "latest": [
                    {
                        "id": r.id,
                        "dish": {
                            "id": r.dish.id if r.dish else None,
                            "name": r.dish.name if r.dish else None,
                        },
                        "user": {
                            "id": r.author.id if r.author else None,
                            "username": r.author.username if r.author else None,
                        },
                        "rating": r.rating,
                        "comment": r.comment,
                        "date": (
                            r.date.isoformat()
                            if hasattr(r, "date") and r.date is not None
                            else None
                        ),
                    }
                    for r in latest_reviews
                ],
                "distribution": rating_distribution,
                "trend": review_trend,
                "trend_percent_change_vs_previous_period": review_percent_change,
                "avg_review_length": avg_review_length,
                "median_review_length": median_review_length,
            },
            "users": {
                "top_reviewers": top_reviewers,
                "newest": [
                    {
                        "id": u.id,
                        "username": u.username,
                        "joined": u.created_at.isoformat(),
                    }
                    for u in newest_users
                ],
                "users_by_month": users_by_month,
                "dishes_by_month": dishes_by_month,
            },
            "tags": {"top_tags": tag_summary},
            "meta": {
                "min_reviews_threshold": min_reviews,
                "computed_at": datetime.utcnow().isoformat(),
            },
        }

        # cache it (simple in-process cache)
        _SIMPLE_CACHE[cache_key] = stats
        _SIMPLE_CACHE["last_cache_time"] = datetime.utcnow().isoformat()

    # CSV export path
    if export_csv:
        # build CSV manually
        rows = []
        header = [
            "review_id",
            "dish_id",
            "dish_name",
            "user_id",
            "username",
            "rating",
            "date",
            "comment",
        ]
        rows.append(",".join(['"{}"'.format(h.replace('"', '""')) for h in header]))
        # fetch reviews in range
        range_start_dt = datetime(start_date.year, start_date.month, start_date.day)
        range_end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        reviews_q = (
            Review.query.filter(
                Review.created_at >= range_start_dt, Review.created_at <= range_end_dt
            )
            .order_by(Review.created_at.asc())
            .all()
        )
        for r in reviews_q:
            dish_name = r.dish.name if r.dish else ""
            username = r.author.username if r.author else ""
            comment = (r.comment or "").replace("\n", " ").replace("\r", " ")

            def esc(s):
                s2 = str(s).replace('"', '""')
                return f'"{s2}"'

            row = [
                esc(r.id),
                esc(r.dish_id),
                esc(dish_name),
                esc(r.user_id),
                esc(username),
                esc(r.rating),
                esc(
                    (
                        r.date.isoformat()
                        if hasattr(r, "date") and r.date is not None
                        else ""
                    )
                ),
                esc(comment),
            ]
            rows.append(",".join(row))
        csv_text = "\n".join(rows)
        headers = {
            "Content-Type": "text/csv",
            "Content-Disposition": f'attachment; filename="reviews_{start_date.isoformat()}_{end_date.isoformat()}.csv"',
        }
        return (csv_text, 200, headers)

    return jsonify(_SIMPLE_CACHE[cache_key])


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
