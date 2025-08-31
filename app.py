import json
import os
from datetime import datetime
from typing import TypedDict, List, Optional
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from data.constants import (
    USER_ID,
    USERNAME,
    PASSWORD,
    DISH_ID,
    DISH_NAME,
    DISH_TAGS,
    DISH_REVIEWS,
)

# ── App Setup ─────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretkey")

login_manager = LoginManager(app)
login_manager.login_view = "login"

# ── File Paths ────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(BASE_DIR, "users")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)

DISHES_PATH = os.path.join(DATA_DIR, "dishes.json")
USERS_PATH = os.path.join(USERS_DIR, "users.json")


# ── Type Hints ─────────────────────────────────────────────────────
class Review(TypedDict):
    user: str
    rating: int
    comment: str
    date: str


class Dish(TypedDict):
    id: int
    name: str
    description: str
    image: str
    ingredients: List[str]
    preparation: List[str]
    tags: List[str]
    reviews: List[Review]


class UserData(TypedDict):
    id: int
    username: str
    password: str


# ── JSON Utilities ────────────────────────────────────────────────
def load_json(path) -> list:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(path, data) -> None:
    if os.path.exists(path):
        backup = f"{path}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
        os.rename(path, backup)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ── Load Data ─────────────────────────────────────────────────────
dishes: List[Dish] = load_json(DISHES_PATH)
users: List[UserData] = load_json(USERS_PATH)

for dish in dishes:
    dish.setdefault(DISH_REVIEWS, [])
    dish.setdefault(DISH_TAGS, [])
    dish[DISH_TAGS].sort(key=str.lower)
    reviews = dish[DISH_REVIEWS]
    dish["avg_rating"] = (
        round(sum(r["rating"] for r in reviews) / len(reviews), 2) if reviews else None
    )
    dish[DISH_REVIEWS].sort(key=lambda r: r["date"], reverse=True)


# ── Helpers ───────────────────────────────────────────────────────
def get_user_by_username(username: str) -> Optional[UserData]:
    return next((u for u in users if u[USERNAME] == username), None)


def get_dish_by_id(dish_id: int) -> Optional[Dish]:
    return next((d for d in dishes if d[DISH_ID] == dish_id), None)


def search_dishes(query: str) -> List[Dish]:
    terms = [term.strip().lower() for term in query.split(",") if term.strip()]
    result = []
    seen_ids = set()

    for dish in dishes:
        name = dish[DISH_NAME].lower()
        desc = dish.get("description", "").lower()
        tags = [tag.lower() for tag in dish.get(DISH_TAGS, [])]

        if any(
            term in name or term in desc or any(term in tag for tag in tags)
            for term in terms
        ):
            if dish[DISH_ID] not in seen_ids:
                result.append(dish)
                seen_ids.add(dish[DISH_ID])

    return result


# ── User Class ────────────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    user = next((u for u in users if u[USER_ID] == int(user_id)), None)
    return User(**user) if user else None


# ── Routes ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", dishes=dishes)


@app.route("/dishes", methods=["GET", "POST"])
@login_required
def list_dishes():
    all_tags = sorted({tag for dish in dishes for tag in dish.get(DISH_TAGS, [])})
    query = request.form.get("search", "").strip()
    sort = request.form.get("sort", "name")
    filtered = search_dishes(query) if query else list(dishes)

    if sort == "rating":
        filtered.sort(key=lambda d: d.get("avg_rating") or 0, reverse=True)
    elif sort == "name":
        filtered.sort(key=lambda d: d[DISH_NAME].lower())

    return render_template(
        "dishes.html",
        dishes=filtered,
        tags=all_tags,
        current_search=query,
        current_sort=sort,
    )


@app.route("/dish/<int:dish_id>")
@login_required
def dish_detail(dish_id: int):
    dish = get_dish_by_id(dish_id)
    if not dish:
        abort(404)
    return render_template("dish_detail.html", dish=dish)


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

    if not (1 <= rating <= 5) or not comment:
        flash("Rating (1–5) and a comment are required.", "warning")
        return redirect(url_for("dish_detail", dish_id=dish_id))

    dish = get_dish_by_id(dish_id)
    if not dish:
        abort(404)

    new_review: Review = {
        "user": current_user.username,
        "rating": rating,
        "comment": comment,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    dish[DISH_REVIEWS].append(new_review)
    dish[DISH_REVIEWS].sort(key=lambda r: r["date"], reverse=True)
    dish["avg_rating"] = round(
        sum(r["rating"] for r in dish[DISH_REVIEWS]) / len(dish[DISH_REVIEWS]), 2
    )

    save_json(DISHES_PATH, dishes)
    flash("Review added successfully.", "success")
    return redirect(url_for("dish_detail", dish_id=dish_id))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("list_dishes"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            flash("Username and password required.", "warning")
        elif get_user_by_username(username):
            flash("Username already exists.", "danger")
        else:
            new_id = max((u[USER_ID] for u in users), default=0) + 1
            users.append({USER_ID: new_id, USERNAME: username, PASSWORD: password})
            save_json(USERS_PATH, users)
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("list_dishes"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user_data = get_user_by_username(username)

        if user_data and user_data[PASSWORD] == password:
            login_user(User(**user_data))
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for("list_dishes"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ── Debug Route (Safe) ─────────────────────────────────────────────
@app.route("/admin/raw")
def admin_raw():
    if not app.debug:
        abort(403)
    return {"dishes": dishes, "users": users}


# ── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
