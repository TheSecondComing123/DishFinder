import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app
from models import db, User, Dish, Review

with app.app_context():
    # Count statistics
    total_users = User.query.count()
    total_dishes = Dish.query.count()
    total_reviews = Review.query.count()

    # Reviews per dish
    dish_stats = []
    for dish in Dish.query.all():
        review_count = len(dish.reviews)
        dish_stats.append((dish.id, dish.name, review_count, dish.avg_rating))

    # Print summary
    print(f"Total users: {total_users}")
    print(f"Total dishes: {total_dishes}")
    print(f"Total reviews: {total_reviews}")
    print("\nReviews per dish:")

    # Sort by number of reviews, highest first
    for dish_id, name, count, rating in sorted(
        dish_stats, key=lambda x: x[2], reverse=True
    ):
        print(f"Dish #{dish_id}: {name} - {count} reviews, {rating} avg rating")

    # Review distribution by rating
    ratings = {}
    for i in range(1, 6):
        ratings[i] = Review.query.filter_by(rating=i).count()

    print("\nRating distribution:")
    for rating, count in ratings.items():
        print(f"{rating} stars: {count} reviews ({count/total_reviews*100:.1f}%)")
