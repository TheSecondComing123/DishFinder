import os
import sys
from sqlalchemy import not_

from app import app
from models import db, User, Review


def main():
    with app.app_context():
        # Get first 9 users by ID
        first_users = User.query.order_by(User.id).limit(9).all()
        keep_ids = [u.id for u in first_users]

        print(f"Keeping reviews from these user IDs: {keep_ids}")

        # Count total reviews before deletion
        total_reviews_before = Review.query.count()
        print(f"Total reviews before deletion: {total_reviews_before}")

        # Count reviews that will be kept
        kept_reviews = Review.query.filter(Review.user_id.in_(keep_ids)).count()
        print(f"Reviews that will be kept: {kept_reviews}")

        # Count reviews that will be deleted
        deleted_reviews = total_reviews_before - kept_reviews
        print(f"Reviews that will be deleted: {deleted_reviews}")

        # Perform deletion
        db.session.query(Review).filter(~Review.user_id.in_(keep_ids)).delete(
            synchronize_session=False
        )
        db.session.commit()

        # Count total reviews after deletion
        total_reviews_after = Review.query.count()
        print(f"Total reviews after deletion: {total_reviews_after}")

        print("Cleanup complete.")


if __name__ == "__main__":
    main()
