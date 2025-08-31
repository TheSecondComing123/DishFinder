# add_chinese_dishes.py
"""
Script to add Lanzhou Beef Noodle Soup, Lanzhou Liangpi, and Roujiamo to the database
Run this script after your SQLite migration is complete.
"""

from flask import Flask
from models import db, Dish
import os


def setup_app():
    """Setup Flask app for adding dishes"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "temp-key"

    # Database Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f'sqlite:///{os.path.join(basedir, "food_app.db")}'
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    return app


def add_chinese_dishes():
    """Add the three Chinese dishes to the database"""

    # Get the next available dish IDs
    last_dish = Dish.query.order_by(Dish.id.desc()).first()
    next_id = last_dish.id + 1 if last_dish else 1

    dishes_to_add = [
        {
            "id": next_id,
            "name": "Lanzhou Beef Noodle Soup (兰州牛肉面)",
            "description": 'A traditional Chinese noodle soup from Lanzhou featuring clear broth, hand-pulled noodles, tender beef, and fresh vegetables. Known for its "one clear, two white, three red, four green, five yellow" characteristics.',
            "image": "/static/images/lanzhou_beef_noodles.png",
            "ingredients": [
                "400 g fresh hand-pulled noodles (or thick wheat noodles)",
                "300 g beef brisket, cut into chunks",
                "200 g beef bones",
                "2 L water",
                "3 slices fresh ginger",
                "2 scallions, cut into sections",
                "2 tbsp Shaoxing wine",
                "1 tbsp light soy sauce",
                "1 tsp salt",
                "100 g white radish, sliced",
                "2 tbsp chili oil (optional)",
                "2 cloves garlic, minced",
                "1 tsp white pepper",
                "Fresh cilantro, chopped",
                "Scallions, thinly sliced",
                "1 tbsp beef tallow or vegetable oil",
            ],
            "preparation": [
                "Soak beef bones in cold water for 2 hours to remove blood, then rinse clean.",
                "In a large pot, bring water to boil. Add beef bones and blanch for 5 minutes. Remove and rinse.",
                "Return bones to pot with fresh water, add ginger, scallions, and Shaoxing wine. Simmer for 2-3 hours until broth is clear and flavorful.",
                "In another pot, cook beef brisket with soy sauce, salt, and aromatics until tender, about 1.5 hours. Slice thinly when cool.",
                "Strain the bone broth and season with salt and white pepper. Keep hot.",
                "Cook white radish slices in the broth until tender, about 10 minutes.",
                "Cook noodles in boiling water according to package directions until al dente. Drain.",
                "To serve: place noodles in bowl, arrange sliced beef and radish on top.",
                "Ladle hot broth over noodles, ensuring everything is covered.",
                "Garnish with chopped cilantro, sliced scallions, and a drizzle of chili oil if desired.",
                "Serve immediately while steaming hot.",
            ],
            "tags": [
                "Chinese",
                "Soup",
                "Noodles",
                "Beef",
                "Dinner",
                "Traditional",
                "Lanzhou",
                "Halal",
            ],
        },
        {
            "id": next_id + 1,
            "name": "Lanzhou Liangpi (兰州凉皮)",
            "description": "Refreshing cold noodles from Lanzhou made with wheat starch, served in a tangy and spicy sauce with julienned vegetables. Perfect for hot summer days.",
            "image": "/static/images/lanzhou_liangpi.png",
            "ingredients": [
                "400 g wheat starch noodles (liangpi sheets)",
                "2 cucumbers, julienned",
                "1 carrot, julienned",
                "100 g bean sprouts, blanched",
                "2 tbsp sesame paste (tahini)",
                "3 tbsp light soy sauce",
                "2 tbsp black vinegar",
                "1 tbsp chili oil with sediment",
                "1 tsp sugar",
                "1 tsp salt",
                "2 cloves garlic, minced",
                "1 tsp sesame oil",
                "2 scallions, finely chopped",
                "Fresh cilantro, chopped",
                "1 tsp Sichuan peppercorn powder (optional)",
                "2 tbsp peanuts, crushed (optional)",
            ],
            "preparation": [
                "If using dried liangpi sheets, soak in warm water until soft and pliable, then cut into strips.",
                "If making from scratch, steam wheat starch batter in thin layers, then cut when cool.",
                "Prepare vegetables: julienne cucumbers and carrots into matchstick pieces.",
                "Blanch bean sprouts in boiling water for 30 seconds, then rinse with cold water and drain.",
                "Make the sauce: In a bowl, whisk sesame paste with a little warm water until smooth.",
                "Add soy sauce, black vinegar, chili oil, sugar, salt, and minced garlic to the sesame paste.",
                "Mix until well combined. Adjust seasoning to taste.",
                "In a large mixing bowl, combine the liangpi noodles with julienned vegetables.",
                "Pour the sauce over the noodle mixture and toss thoroughly to coat everything evenly.",
                "Let it marinate for 10 minutes to absorb flavors.",
                "Serve in bowls, garnished with chopped scallions, cilantro, and crushed peanuts.",
                "Drizzle with additional sesame oil and sprinkle Sichuan peppercorn powder if desired.",
            ],
            "tags": [
                "Chinese",
                "Cold Dish",
                "Noodles",
                "Vegetarian",
                "Summer",
                "Refreshing",
                "Lanzhou",
                "Spicy",
            ],
        },
        {
            "id": next_id + 2,
            "name": "Roujiamo (肉夹馍)",
            "description": 'Often called "Chinese hamburger," this is a popular street food featuring tender braised pork stuffed into a crispy, chewy flatbread. A perfect handheld meal with incredible flavors.',
            "image": "/static/images/roujiamo.png",
            "ingredients": [
                # For the bread (mo):
                "300 g all-purpose flour",
                "180 ml warm water",
                "1 tsp active dry yeast",
                "1 tsp sugar",
                "1 tsp salt",
                "2 tbsp vegetable oil",
                # For the pork filling:
                "800 g pork shoulder or belly, cut into large chunks",
                "3 tbsp light soy sauce",
                "2 tbsp dark soy sauce",
                "2 tbsp Shaoxing wine",
                "1 tbsp rock sugar",
                "4 slices fresh ginger",
                "3 scallions, cut into sections",
                "3 cloves garlic, smashed",
                "2 star anise",
                "1 cinnamon stick",
                "2 bay leaves",
                "1 tsp Sichuan peppercorns",
                "1 tsp salt",
                "2 cups water or chicken stock",
            ],
            "preparation": [
                "Make the bread: Dissolve yeast and sugar in warm water, let sit 5 minutes until foamy.",
                "Mix flour and salt in a bowl, add yeast mixture and oil. Knead into smooth dough.",
                "Cover and let rise for 1 hour until doubled in size.",
                "Divide dough into 8 pieces, roll each into a flat round about 10cm diameter.",
                "Heat a dry pan over medium heat. Cook each bread round for 3-4 minutes per side until golden and puffed. Set aside.",
                "For the pork: In a large pot or Dutch oven, combine pork with all braising ingredients.",
                "Bring to a boil, then reduce heat to low and simmer covered for 1.5-2 hours until very tender.",
                "Remove pork and shred or chop finely. Strain and reserve the braising liquid.",
                "Return shredded pork to pot with 1 cup of braising liquid. Simmer until liquid reduces and coats the meat.",
                "Taste and adjust seasoning with salt, soy sauce, or sugar as needed.",
                "To assemble: Cut a pocket in each bread round (don't cut all the way through).",
                "Stuff generously with the braised pork mixture.",
                "Serve immediately while the bread is still warm and the pork is hot.",
                "Optionally, briefly toast the stuffed roujiamo in a pan for extra crispiness.",
            ],
            "tags": [
                "Chinese",
                "Street Food",
                "Pork",
                "Sandwich",
                "Lunch",
                "Handheld",
                "Traditional",
                "Xi'an",
            ],
        },
    ]

    added_count = 0

    for dish_data in dishes_to_add:
        # Check if dish already exists
        existing = Dish.query.filter_by(name=dish_data["name"]).first()
        if existing:
            print(f"Dish '{dish_data['name']}' already exists, skipping...")
            continue

        # Create new dish
        dish = Dish(
            name=dish_data["name"],
            description=dish_data["description"],
            image=dish_data["image"],
            ingredients=dish_data["ingredients"],
            preparation=dish_data["preparation"],
            tags=dish_data["tags"],
        )

        try:
            db.session.add(dish)
            db.session.commit()
            added_count += 1
            print(f"✅ Added: {dish_data['name']}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding {dish_data['name']}: {e}")

    return added_count


def main():
    """Main function to add Chinese dishes"""
    print("Adding Chinese Dishes to Food App Database")
    print("=" * 50)

    app = setup_app()

    with app.app_context():
        try:
            added = add_chinese_dishes()
            print("\n" + "=" * 50)
            print(f"Successfully added {added} new dishes!")
            print("\nDishes added:")
            print("• Lanzhou Beef Noodle Soup (兰州牛肉面)")
            print("• Lanzhou Liangpi (兰州凉皮)")
            print("• Roujiamo (肉夹馍)")
            print(
                "\nNote: You'll need to add the corresponding images to your static/images/ folder:"
            )
            print("  - lanzhou_beef_noodles.png")
            print("  - lanzhou_liangpi.png")
            print("  - roujiamo.png")

        except Exception as e:
            print(f"Error: {e}")
            return 1

    return 0


if __name__ == "__main__":
    main()
