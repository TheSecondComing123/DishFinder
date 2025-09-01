import sys
import os
import random
from faker import Faker
from werkzeug.security import generate_password_hash

# Add the current directory to path so Python can find your modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app and database models
from app import app
from models import db, User

# Initialize faker
fake = Faker()


# Define user generation function
def generate_users(num_users=200):
    with app.app_context():
        # Check current user count
        current_count = User.query.count()
        print(f"Current user count: {current_count}")

        # Create new users
        new_users = 0
        existing_usernames = {user.username for user in User.query.all()}

        for i in range(num_users):
            # Generate a variety of username styles
            username_type = random.random()
            if username_type < 0.25:
                # FirstLast style
                username = f"{fake.first_name()}{fake.last_name()}"
            elif username_type < 0.5:
                # FirstLast + numbers
                username = (
                    f"{fake.first_name()}{fake.last_name()}{random.randint(1, 99)}"
                )
            elif username_type < 0.7:
                # Interest-based
                interests = [
                    "foodie",
                    "chef",
                    "cook",
                    "gourmet",
                    "kitchen",
                    "baking",
                    "eats",
                    "taste",
                    "flavor",
                    "culinary",
                ]
                username = f"{random.choice(interests)}{fake.first_name()}"
            elif username_type < 0.85:
                # Adjective + Noun
                adjectives = [
                    "hungry",
                    "happy",
                    "crazy",
                    "super",
                    "mega",
                    "awesome",
                    "clever",
                    "quick",
                    "sleepy",
                ]
                nouns = [
                    "chef",
                    "cook",
                    "baker",
                    "eater",
                    "foodie",
                    "gourmet",
                    "taster",
                    "kitchen",
                    "plate",
                ]
                username = f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(1, 999)}"
            else:
                # Random word combos
                username = f"{fake.word()}{fake.word().capitalize()}"

            # Ensure username is unique
            if username in existing_usernames:
                username = f"{username}{random.randint(10, 99)}"

            # Skip if still not unique (unlikely but possible)
            if username in existing_usernames:
                continue

            existing_usernames.add(username)

            # Generate a random password (8-15 chars)
            password = fake.password(length=random.randint(8, 15))
            password_hash = generate_password_hash(password)

            # Create the user
            user = User(username=username, password_hash=password_hash)
            db.session.add(user)
            new_users += 1

            # Commit in batches of 50
            if new_users % 50 == 0:
                db.session.commit()
                print(f"Added {new_users} users so far...")

        # Final commit for remaining users
        db.session.commit()

        # Verify result
        final_count = User.query.count()
        print(f"User generation complete!")
        print(f"Previous user count: {current_count}")
        print(f"New users added: {new_users}")
        print(f"Current user count: {final_count}")

        # Print a few sample users
        print("\nSample users:")
        for user in User.query.order_by(User.id.desc()).limit(5).all():
            print(f"ID: {user.id}, Username: {user.username}")


if __name__ == "__main__":
    generate_users(200)
