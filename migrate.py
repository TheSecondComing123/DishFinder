# migrate.py - Standalone migration script
"""
Migration script to convert JSON data to SQLite database.

Usage:
    python migrate.py

This script will:
1. Create a backup of your existing JSON files
2. Initialize the SQLite database
3. Migrate all users, dishes, and reviews from JSON to SQLite
4. Verify the migration was successful
"""

import os
import sys
from flask import Flask
from models import (
    db,
    User,
    Dish,
    Review,
    migrate_json_data,
    backup_json_data,
    create_tables,
)


def setup_app():
    """Setup Flask app for migration"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "migration-key"

    # Database Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f'sqlite:///{os.path.join(basedir, "food_app.db")}'
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    return app


def verify_migration():
    """Verify that the migration was successful"""
    print("\n" + "=" * 50)
    print("MIGRATION VERIFICATION")
    print("=" * 50)

    user_count = User.query.count()
    dish_count = Dish.query.count()
    review_count = Review.query.count()

    print(f"Users migrated: {user_count}")
    print(f"Dishes migrated: {dish_count}")
    print(f"Reviews migrated: {review_count}")

    # Check some sample data
    if user_count > 0:
        sample_user = User.query.first()
        print(f"Sample user: {sample_user.username}")

    if dish_count > 0:
        sample_dish = Dish.query.first()
        print(f"Sample dish: {sample_dish.name}")
        print(f"  - Ingredients count: {len(sample_dish.ingredients)}")
        print(f"  - Tags count: {len(sample_dish.tags)}")

    if review_count > 0:
        sample_review = Review.query.first()
        print(f"Sample review: {sample_review.rating}* for {sample_review.dish.name}")

    print("\n" + "=" * 50)
    print("Migration verification completed!")
    print("=" * 50)


def main():
    """Main migration function"""
    print("Starting Food App Migration from JSON to SQLite")
    print("=" * 60)

    # Check if JSON files exist
    if not os.path.exists("data/dishes.json"):
        print("ERROR: data/dishes.json not found!")
        print("Make sure you're running this script from the correct directory.")
        sys.exit(1)

    if not os.path.exists("users/users.json"):
        print("ERROR: users/users.json not found!")
        print("Make sure you're running this script from the correct directory.")
        sys.exit(1)

    # Setup Flask app
    app = setup_app()

    with app.app_context():
        try:
            # Step 1: Backup existing JSON data
            print("Step 1: Creating backup of JSON data...")
            backup_dir = backup_json_data()

            # Step 2: Create database tables
            print("Step 2: Creating database tables...")
            create_tables()

            # Step 3: Migrate data
            print("Step 3: Migrating data from JSON to SQLite...")
            migrate_json_data()

            # Step 4: Verify migration
            print("Step 4: Verifying migration...")
            verify_migration()

            print("\n" + "✅ MIGRATION COMPLETED SUCCESSFULLY! ✅")
            print(f"📁 Backup created in: {backup_dir}")
            print("💾 Database created: food_app.db")
            print("\nYou can now run your Flask app with the new SQLite database!")
            print("Don't forget to install the required dependencies:")
            print("pip install Flask-SQLAlchemy")

        except Exception as e:
            print(f"\n❌ MIGRATION FAILED: {e}")
            print(
                "\nThe migration was not completed. Your original JSON files are safe."
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
