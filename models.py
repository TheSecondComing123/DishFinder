from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    reviews = db.relationship(
        "Review", backref="author", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Dish(db.Model):
    __tablename__ = "dishes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    avg_rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Store JSON data as text (SQLite doesn't have native JSON support)
    _ingredients = db.Column("ingredients", db.Text)
    _preparation = db.Column("preparation", db.Text)
    _tags = db.Column("tags", db.Text)

    # Relationships
    reviews = db.relationship(
        "Review", backref="dish", lazy=True, cascade="all, delete-orphan"
    )

    # Properties to handle JSON serialization/deserialization
    @property
    def ingredients(self):
        return json.loads(self._ingredients) if self._ingredients else []

    @ingredients.setter
    def ingredients(self, value):
        self._ingredients = json.dumps(value) if value else None

    @property
    def preparation(self):
        return json.loads(self._preparation) if self._preparation else []

    @preparation.setter
    def preparation(self, value):
        self._preparation = json.dumps(value) if value else None

    @property
    def tags(self):
        return json.loads(self._tags) if self._tags else []

    @tags.setter
    def tags(self, value):
        self._tags = json.dumps(value) if value else None

    def update_avg_rating(self):
        """Calculate and update the average rating for this dish"""
        if self.reviews:
            total_rating = sum(review.rating for review in self.reviews)
            self.avg_rating = round(total_rating / len(self.reviews), 2)
        else:
            self.avg_rating = 0.0
        db.session.commit()

    def to_dict(self):
        """Convert dish to dictionary (for JSON responses)"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "ingredients": self.ingredients,
            "preparation": self.preparation,
            "tags": self.tags,
            "avg_rating": self.avg_rating,
            "reviews": [review.to_dict() for review in self.reviews],
        }

    def __repr__(self):
        return f"<Dish {self.name}>"


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(
        db.Integer, db.ForeignKey("dishes.id"), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="valid_rating"),
        db.UniqueConstraint("dish_id", "user_id", name="unique_user_dish_review"),
    )

    def to_dict(self):
        """Convert review to dictionary"""
        return {
            "id": self.id,
            "user": self.author.username,
            "rating": self.rating,
            "comment": self.comment,
            "date": self.date.strftime("%Y-%m-%d"),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Review {self.rating}* by {self.author.username} for {self.dish.name}>"


# Migration script helper functions
def create_tables():
    """Create all database tables"""
    db.create_all()
    print("Database tables created successfully!")


def migrate_json_data():
    """Migrate data from JSON files to SQLite database"""
    import os
    import json
    from werkzeug.security import generate_password_hash

    # Get the base directory
    BASE_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(BASE_DIR, "data")
    USERS_DIR = os.path.join(BASE_DIR, "users")

    # Paths to JSON files
    DISHES_PATH = os.path.join(DATA_DIR, "dishes.json")
    USERS_PATH = os.path.join(USERS_DIR, "users.json")

    print("Starting data migration...")

    try:
        # Migrate Users
        if os.path.exists(USERS_PATH):
            print("Migrating users...")
            with open(USERS_PATH, "r", encoding="utf-8") as f:
                users_data = json.load(f)

            for user_data in users_data:
                # Check if user already exists
                existing_user = User.query.filter_by(
                    username=user_data["username"]
                ).first()
                if not existing_user:
                    user = User(
                        username=user_data["username"],
                        password_hash=generate_password_hash(
                            user_data["password"]
                        ),  # Hash the password
                    )
                    db.session.add(user)

            db.session.commit()
            print(f"Migrated {len(users_data)} users")

        # Migrate Dishes
        if os.path.exists(DISHES_PATH):
            print("Migrating dishes...")
            with open(DISHES_PATH, "r", encoding="utf-8") as f:
                dishes_data = json.load(f)

            for dish_data in dishes_data:
                # Check if dish already exists
                existing_dish = Dish.query.filter_by(id=dish_data["id"]).first()
                if not existing_dish:
                    dish = Dish(
                        id=dish_data["id"],
                        name=dish_data["name"],
                        description=dish_data.get("description", ""),
                        image=dish_data.get("image", ""),
                        ingredients=dish_data.get("ingredients", []),
                        preparation=dish_data.get("preparation", []),
                        tags=dish_data.get("tags", []),
                        avg_rating=dish_data.get("avg_rating", 0.0),
                    )
                    db.session.add(dish)

            db.session.commit()
            print(f"Migrated {len(dishes_data)} dishes")

            # Migrate Reviews
            print("Migrating reviews...")
            review_count = 0
            for dish_data in dishes_data:
                dish = Dish.query.get(dish_data["id"])
                if dish and "reviews" in dish_data:
                    for review_data in dish_data["reviews"]:
                        # Find the user
                        user = User.query.filter_by(
                            username=review_data["user"]
                        ).first()
                        if user:
                            # Check if review already exists
                            existing_review = Review.query.filter_by(
                                dish_id=dish.id, user_id=user.id
                            ).first()

                            if not existing_review:
                                # Parse date
                                review_date = datetime.strptime(
                                    review_data["date"], "%Y-%m-%d"
                                ).date()

                                review = Review(
                                    dish_id=dish.id,
                                    user_id=user.id,
                                    rating=int(
                                        float(review_data["rating"])
                                    ),  # Handle float ratings
                                    comment=review_data["comment"],
                                    date=review_date,
                                )
                                db.session.add(review)
                                review_count += 1

            db.session.commit()
            print(f"Migrated {review_count} reviews")

            # Update average ratings
            print("Updating average ratings...")
            for dish in Dish.query.all():
                dish.update_avg_rating()

        print("Data migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        db.session.rollback()
        raise


def backup_json_data():
    """Create backup of existing JSON data before migration"""
    import os
    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"json_backup_{timestamp}"

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Backup data directory
    if os.path.exists("data"):
        shutil.copytree("data", os.path.join(backup_dir, "data"))

    # Backup users directory
    if os.path.exists("users"):
        shutil.copytree("users", os.path.join(backup_dir, "users"))

    print(f"JSON data backed up to {backup_dir}")
    return backup_dir
