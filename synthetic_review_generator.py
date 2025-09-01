import random
from datetime import datetime, timedelta
import nltk
from nltk.corpus import words, wordnet
import re
import numpy as np
from faker import Faker
import os
import sys

# Add the current directory to path so Python can find your modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app and database models
from app import app
from models import db, User, Dish, Review

# Setup Flask context
app.app_context().__enter__()

# Setup
fake = Faker()
try:
    nltk.data.find("corpora/words")
except LookupError:
    nltk.download("words")
    nltk.download("wordnet")

# Get existing data from database
users = User.query.all()
dishes = Dish.query.all()

import hashlib


def deterministic_mean(dish, base_mean, variance):
    # Use dish.id or dish.name to create a reproducible seed
    seed = int(hashlib.sha256(dish.name.encode()).hexdigest(), 16) % (10**8)
    rng = np.random.default_rng(seed)
    return min(5, max(1, rng.normal(base_mean, variance)))


dish_true_means = {}
for dish in dishes:
    if "Italian" in dish.tags:
        base_mean = deterministic_mean(dish, 4.2, 0.3)
    elif "Mexican" in dish.tags:
        base_mean = deterministic_mean(dish, 4.0, 0.4)
    elif "Indian" in dish.tags:
        base_mean = deterministic_mean(dish, 3.2, 0.6)
    elif "American" in dish.tags:
        base_mean = deterministic_mean(dish, 3.8, 0.4)
    else:
        base_mean = deterministic_mean(dish, 3.7, 0.5)

    dish_true_means[dish.id] = base_mean

# Language and vocabulary for reviews
culinary_terms = [
    "texture",
    "flavor",
    "aroma",
    "taste",
    "mouthfeel",
    "balance",
    "seasoning",
    "tender",
    "crispy",
    "crunchy",
    "silky",
    "rich",
    "light",
    "heavy",
    "fresh",
    "savory",
    "sweet",
    "spicy",
    "tangy",
    "zesty",
    "bitter",
    "salty",
    "umami",
    "juicy",
    "moist",
    "dry",
    "overcooked",
    "undercooked",
    "al dente",
]

cooking_terms = [
    "simmer",
    "sauté",
    "roast",
    "bake",
    "fry",
    "grill",
    "broil",
    "braise",
    "poach",
    "steam",
    "blanch",
    "reduce",
    "caramelize",
    "deglaze",
    "marinate",
    "baste",
]

modifiers = [
    "very",
    "extremely",
    "incredibly",
    "surprisingly",
    "remarkably",
    "notably",
    "somewhat",
    "slightly",
    "a bit",
    "rather",
    "quite",
    "fairly",
]


# Personality-based comment generation
def generate_comment(dish, rating, user_type):
    # Create different reviewer personas
    if user_type == "enthusiast":
        return generate_enthusiast_comment(dish, rating)
    elif user_type == "critic":
        return generate_critic_comment(dish, rating)
    elif user_type == "casual":
        return generate_casual_comment(dish, rating)
    elif user_type == "expert":
        return generate_expert_comment(dish, rating)
    else:
        return generate_basic_comment(dish, rating)


def generate_enthusiast_comment(dish, rating):
    if rating >= 4:
        templates = [
            "Absolutely fell in love with this {dish_type}! The {aspect} was {positive_adj}.",
            "This {dish_type} is now a staple in our house. {positive_phrase}.",
            "Made this for {occasion} and everyone raved about it! The {aspect} was {positive_adj}.",
            "I've tried many {dish_type} recipes, and this one is by far the best! {positive_phrase}.",
            "Wow! This {dish_type} has such {positive_adj} {aspect}. Will definitely make again!",
        ]
    elif rating >= 3:
        templates = [
            "Pretty good {dish_type}, though I think the {aspect} could use a bit more {improvement}.",
            "Decent recipe. I added some {ingredient} to enhance the {aspect}.",
            "Good {dish_type}, but not amazing. The {aspect} was {neutral_adj}.",
            "Solid recipe with {positive_adj} {aspect}, but I prefer a bit more {improvement}.",
            "Made this {timeframe} - it was good but needed some adjustments to the {aspect}.",
        ]
    else:
        templates = [
            "Wanted to love this {dish_type}, but the {aspect} was too {negative_adj}.",
            "Had high hopes, but unfortunately the {aspect} didn't work for me.",
            "Followed the recipe exactly, but ended up with {negative_adj} {aspect}.",
            "Not sure what went wrong, but my {dish_type} turned out {negative_adj}.",
            "The {aspect} didn't come together as expected. Might try again with {improvement}.",
        ]

    positive_adj = [
        "amazing",
        "incredible",
        "perfect",
        "outstanding",
        "delightful",
        "excellent",
        "fantastic",
    ]
    neutral_adj = [
        "decent",
        "alright",
        "acceptable",
        "okay",
        "fine",
        "satisfactory",
        "passable",
    ]
    negative_adj = [
        "disappointing",
        "bland",
        "unbalanced",
        "overwhelming",
        "underwhelming",
        "off",
        "strange",
    ]
    aspects = [
        "flavor",
        "texture",
        "balance of spices",
        "cooking method",
        "sauce",
        "aroma",
        "preparation",
    ]
    improvements = [
        "seasoning",
        "spice",
        "herbs",
        "cooking time",
        "heat",
        "ingredients",
        "flavor",
    ]
    positive_phrases = [
        "Just the right balance of flavors",
        "Perfectly seasoned and prepared",
        "Such complex and delicious flavors",
        "The cooking time was spot on",
        "The ingredients complement each other perfectly",
    ]
    occasions = [
        "a family dinner",
        "a dinner party",
        "a potluck",
        "my partner",
        "friends",
        "a special occasion",
    ]
    timeframes = [
        "last night",
        "over the weekend",
        "for meal prep",
        "yesterday",
        "last week",
    ]
    dish_types = ["recipe", "dish", dish.name]

    template = random.choice(templates)

    # Get dish ingredients as a list for formatting
    dish_ingredients = dish.ingredients

    result = template.format(
        dish_type=random.choice(dish_types),
        aspect=random.choice(aspects),
        positive_adj=random.choice(positive_adj),
        negative_adj=random.choice(negative_adj),
        neutral_adj=random.choice(neutral_adj),
        improvement=random.choice(improvements),
        positive_phrase=random.choice(positive_phrases),
        occasion=random.choice(occasions),
        timeframe=random.choice(timeframes),
        ingredient=(
            random.choice(dish_ingredients) if dish_ingredients else "extra seasoning"
        ),
    )

    # Add personal touches
    if random.random() < 0.3:
        personal_touches = [
            " My family loved it!",
            " Can't wait to make it again!",
            " A new favorite in our rotation.",
            " Paired it with a nice wine.",
            " Great for meal prep!",
            " Perfect for a weeknight dinner.",
            " Much better than the restaurant version.",
        ]
        result += random.choice(personal_touches)

    # Add specific modifications
    if rating < 4 and random.random() < 0.4:
        modifications = [
            " I added a bit more garlic.",
            " Next time I'll reduce the cooking time slightly.",
            " I substituted some ingredients based on what I had.",
            " Used my Instant Pot instead of stovetop.",
            " Added some extra spices to suit our taste.",
            " Cut back on the salt a bit.",
            " Doubled the sauce because we love it saucy!",
        ]
        result += random.choice(modifications)

    return result


def generate_critic_comment(dish, rating):
    # Critics use more technical language and detailed analysis
    if rating >= 4:
        templates = [
            "An exceptional rendition of {dish_name}. The {technique} resulted in {positive_outcome}, while the {ingredient} provided {positive_effect}.",
            "This recipe demonstrates a masterful understanding of {cuisine} techniques. The {aspect} was {positive_adj} without being {negative_adj}.",
            "A thoughtfully crafted dish where the {ingredient} is properly {technique}, allowing the {flavor_profile} to shine through.",
            "An impressive balance of {flavor_profile} and {texture}. The {technique} is executed perfectly, creating a {positive_adj} finish.",
            "The {aspect} in this dish is noteworthy - {positive_outcome} that showcases proper {cuisine} principles.",
        ]
    elif rating >= 3:
        templates = [
            "A competent {dish_name}, though the {aspect} could benefit from {improvement}. The {technique} was {neutral_adj}.",
            "This recipe has potential but lacks {aspect}. The {ingredient} was {neutral_adj}, though {improvement} would elevate it.",
            "A decent effort that falls short in {aspect}. The {technique} results in {neutral_outcome}, but {improvement} would help.",
            "The fundamentals are sound, but the {flavor_profile} needs refinement. Consider {improvement} to enhance the {aspect}.",
            "An acceptable {cuisine} dish that doesn't quite reach its potential. The {technique} is {neutral_adj}, but lacks {aspect}.",
        ]
    else:
        templates = [
            "This recipe fundamentally misunderstands {cuisine} cooking. The {technique} leads to {negative_outcome}, while the {aspect} is {negative_adj}.",
            "A disappointing execution where the {ingredient} is {negative_adj}. The {aspect} lacks {missing_element}, resulting in {negative_outcome}.",
            "The {technique} in this recipe is problematic, leading to {negative_outcome}. The {flavor_profile} is {negative_adj} and unbalanced.",
            "This dish fails on several levels. The {aspect} is {negative_adj}, the {technique} is improperly executed, and the {flavor_profile} is muddled.",
            "A recipe that needs significant revision. The {ingredient} is {negative_adj}, the {technique} results in {negative_outcome}, and the overall dish lacks {missing_element}.",
        ]

    positive_adj = [
        "nuanced",
        "refined",
        "well-developed",
        "harmonious",
        "precise",
        "balanced",
        "complex",
    ]
    neutral_adj = [
        "adequate",
        "serviceable",
        "functional",
        "conventional",
        "standard",
        "predictable",
    ]
    negative_adj = [
        "one-dimensional",
        "poorly executed",
        "imbalanced",
        "flawed",
        "overworked",
        "underdeveloped",
    ]

    aspects = [
        "depth of flavor",
        "textural contrast",
        "aromatic profile",
        "acid balance",
        "seasoning progression",
        "flavor layering",
        "heat management",
    ]
    techniques = [
        "reduction",
        "caramelization",
        "deglazing",
        "emulsification",
        "rendering",
        "infusion",
        "fermentation",
        "searing",
    ]

    positive_outcomes = [
        "a depth of flavor rarely achieved in home cooking",
        "a perfect balance between richness and acidity",
        "layers of flavor that develop with each bite",
        "a texture that showcases technical skill",
        "an integration of flavors that demonstrates culinary understanding",
    ]
    neutral_outcomes = [
        "acceptable results though lacking distinction",
        "adequate flavor development",
        "serviceable texture though somewhat predictable",
        "functional results without notable flair",
        "conventional outcomes that satisfy without impressing",
    ]
    negative_outcomes = [
        "muddled flavors that compete rather than complement",
        "a texture that undermines the dish's potential",
        "an unpleasant mouthfeel that distracts from other elements",
        "a disharmony between key components",
        "a fundamental imbalance that ruins the eating experience",
    ]

    improvements = [
        "more careful attention to cooking temperature",
        "properly developing fond before deglazing",
        "a more judicious application of acid",
        "allowing flavors to bloom before proceeding",
        "a more refined balance of aromatics",
        "proper seasoning throughout the cooking process",
    ]

    missing_elements = [
        "depth",
        "balance",
        "technique",
        "restraint",
        "precision",
        "subtlety",
        "contrast",
    ]

    flavor_profiles = [
        "umami",
        "brightness",
        "richness",
        "pungency",
        "herbaceousness",
        "sweetness",
        "savoriness",
    ]
    positive_effects = [
        "depth",
        "complexity",
        "brightness",
        "richness",
        "warmth",
        "vibrancy",
        "roundness",
    ]
    textures = [
        "tenderness",
        "crispness",
        "silkiness",
        "creaminess",
        "flakiness",
        "juiciness",
    ]

    cuisines = [
        "French",
        "Italian",
        "Japanese",
        "Mediterranean",
        "regional",
        "classical",
        "traditional",
    ]

    ingredients = dish.ingredients
    ingredient = (
        random.choice(ingredients)[: random.randint(10, 20)]
        if ingredients
        else "primary ingredient"
    )

    template = random.choice(templates)
    result = template.format(
        dish_name=dish.name,
        aspect=random.choice(aspects),
        technique=random.choice(techniques),
        positive_outcome=random.choice(positive_outcomes),
        neutral_outcome=random.choice(neutral_outcomes),
        negative_outcome=random.choice(negative_outcomes),
        ingredient=ingredient,
        positive_adj=random.choice(positive_adj),
        neutral_adj=random.choice(neutral_adj),
        negative_adj=random.choice(negative_adj),
        positive_effect=random.choice(positive_effects),
        improvement=random.choice(improvements),
        missing_element=random.choice(missing_elements),
        flavor_profile=random.choice(flavor_profiles),
        texture=random.choice(textures),
        cuisine=random.choice(cuisines),
    )

    return result


def generate_casual_comment(dish, rating):
    # Casual reviewers use simple language, emojis, and brief comments
    if rating >= 4:
        templates = [
            "Yum! {loved_it}",
            "So good! {loved_it}",
            "Loved this! {positive_point}",
            "Really tasty! {positive_point}",
            "Made this last night. {loved_it}",
            "Super easy and delicious!",
            "This was a hit! {positive_point}",
            "{loved_it} Will make again!",
        ]
    elif rating >= 3:
        templates = [
            "Pretty good! {neutral_point}",
            "Not bad. {neutral_point}",
            "Decent recipe. {neutral_point}",
            "It was okay. {neutral_point}",
            "Made this for dinner. {neutral_point}",
            "Good but needed some tweaks.",
            "Solid recipe. {neutral_point}",
        ]
    else:
        templates = [
            "Didn't really work for me. {negative_point}",
            "Not a fan. {negative_point}",
            "Meh. {negative_point}",
            "Wouldn't make again. {negative_point}",
            "Something was off. {negative_point}",
            "Not what I expected. {negative_point}",
            "Didn't turn out right. {negative_point}",
        ]

    loved_it = [
        "Everyone enjoyed it!",
        "So flavorful!",
        "Made it twice already!",
        "Perfect recipe!",
        "Easy to make too!",
        "My new favorite!",
        "Sooo good!",
    ]

    positive_points = [
        "Great flavor.",
        "Quick and easy.",
        "Perfect for weeknights.",
        "Kids loved it too.",
        "Better than takeout.",
        "Really filling.",
        "Simple ingredients.",
    ]

    neutral_points = [
        "Added some extra spices.",
        "Needed more salt.",
        "Had to cook longer than stated.",
        "Used different veggies.",
        "Adjusted the seasoning.",
        "Okay for a quick meal.",
        "Nothing special but good.",
    ]

    negative_points = [
        "Too bland for me.",
        "Took way longer than stated.",
        "Too complicated.",
        "Missing something.",
        "Instructions weren't clear.",
        "Too much work for the result.",
        "Came out dry.",
    ]

    template = random.choice(templates)
    result = template.format(
        loved_it=random.choice(loved_it),
        positive_point=random.choice(positive_points),
        neutral_point=random.choice(neutral_points),
        negative_point=random.choice(negative_points),
    )

    # Add emojis for casual reviewers
    if random.random() < 0.5:
        if rating >= 4:
            emojis = ["😋", "😍", "👍", "🔥", "💯", "🤤", "❤️"]
        elif rating >= 3:
            emojis = ["😊", "👌", "🙂", "✌️"]
        else:
            emojis = ["😕", "👎", "😐", "🤔"]

        # Add 1-2 emojis
        emoji_count = random.randint(1, 2)
        selected_emojis = random.sample(emojis, emoji_count)

        # 50% chance at beginning, 50% at end
        if random.random() < 0.5:
            result = " ".join(selected_emojis) + " " + result
        else:
            result = result + " " + " ".join(selected_emojis)

    return result


def generate_expert_comment(dish, rating):
    # Experts focus on technique, authenticity, and detailed critiques
    if rating >= 4:
        templates = [
            "An excellent execution of {dish_name}. The {technique} is authentic and the {ingredient} is treated with proper respect. {positive_detail}",
            "This recipe captures the essence of traditional {dish_name}. The {technique} is masterfully described, resulting in {positive_outcome}.",
            "A technically sound approach to {dish_name}. The {aspect} demonstrates culinary expertise, particularly the {positive_detail}.",
            "From a culinary perspective, this {dish_name} recipe hits all the right notes. The {aspect} is particularly noteworthy - {positive_detail}.",
            "As someone who has prepared {dish_name} professionally, I can confirm this recipe achieves {positive_outcome} through proper {technique}.",
        ]
    elif rating >= 3:
        templates = [
            "A decent approach to {dish_name}, though the {technique} could be refined. {neutral_detail} I would recommend {improvement}.",
            "This recipe has the fundamentals correct, but lacks {aspect} in key areas. {neutral_detail}",
            "The core technique is sound, but I would adjust the {aspect}. {neutral_detail} In professional kitchens, we typically {improvement}.",
            "A good attempt that needs refinement. The {aspect} is acceptable, but {neutral_detail}. Consider {improvement}.",
            "Having cooked {dish_name} extensively, I find this recipe adequate but missing {aspect}. {neutral_detail}",
        ]
    else:
        templates = [
            "This recipe misses key fundamentals of {dish_name}. The {technique} as described will result in {negative_outcome}. {negative_detail}",
            "From a technical standpoint, this approach to {dish_name} is problematic. The {aspect} is flawed - {negative_detail}.",
            "Having cooked {dish_name} professionally, I must note several issues. The {technique} lacks {aspect}, leading to {negative_outcome}.",
            "This recipe fails to understand the principles behind {dish_name}. The {aspect} is incorrectly approached, resulting in {negative_detail}.",
            "A technically unsound recipe. The {technique} as described will not achieve proper {aspect}, instead resulting in {negative_outcome}.",
        ]

    techniques = [
        "mise en place",
        "heat management",
        "reduction technique",
        "emulsification method",
        "searing process",
        "deglazing approach",
        "resting method",
        "marination process",
        "flavor development",
        "aromatics preparation",
        "sauce building",
        "textural development",
    ]

    aspects = [
        "temperature control",
        "flavor layering",
        "ingredient preparation",
        "timing precision",
        "doneness indication",
        "balance of flavors",
        "textural contrast",
        "cooking vessel choice",
        "foundational technique",
        "taste progression",
        "spice blooming",
        "acid balance",
    ]

    positive_outcomes = [
        "exceptional depth of flavor",
        "perfect textural development",
        "professional-quality results",
        "balanced complexity",
        "proper mouthfeel and finish",
        "authentic flavor profile",
        "technical excellence in the final dish",
    ]

    negative_outcomes = [
        "inferior texture",
        "muted flavors",
        "component separation",
        "improper doneness",
        "inconsistent results",
        "unbalanced final product",
        "compromised integrity of ingredients",
    ]

    positive_details = [
        "The timing specifications are particularly precise, preventing common pitfalls.",
        "The ratio of aromatics to main ingredients shows a deep understanding of flavor development.",
        "The attention to temperature gradient demonstrates technical knowledge often overlooked.",
        "The specific order of operations preserves ingredient integrity expertly.",
        "The method of introducing acidity at the correct stage shows culinary knowledge.",
    ]

    neutral_details = [
        "The approach is conventional but lacks nuance in key areas.",
        "The technique is serviceable but misses opportunities for flavor development.",
        "The method achieves basic results but doesn't maximize ingredient potential.",
        "The process works but could be streamlined for more consistent outcomes.",
        "The approach is textbook but doesn't account for variable conditions.",
    ]

    negative_details = [
        "The fundamental technique violates established culinary principles.",
        "The temperature specified will inevitably result in protein denaturation issues.",
        "The lack of proper mise en place instruction leads to timing problems throughout.",
        "The ingredient ratios are unbalanced and will create disharmony in the final dish.",
        "The cooking time is insufficient for proper Maillard reaction development.",
    ]

    improvements = [
        "allowing ingredients to come to room temperature before cooking",
        "building a proper fond before deglazing",
        "seasoning incrementally throughout the cooking process",
        "monitoring doneness by texture rather than time",
        "properly resting proteins before serving",
        "blooming spices in fat before introducing liquids",
        "focusing on proper knife technique for consistent ingredient size",
    ]

    ingredients = dish.ingredients
    ingredient = (
        random.choice(ingredients)[: random.randint(10, 20)]
        if ingredients
        else "primary ingredient"
    )

    template = random.choice(templates)
    result = template.format(
        dish_name=dish.name,
        technique=random.choice(techniques),
        aspect=random.choice(aspects),
        ingredient=ingredient,
        positive_detail=random.choice(positive_details),
        neutral_detail=random.choice(neutral_details),
        negative_detail=random.choice(negative_details),
        positive_outcome=random.choice(positive_outcomes),
        negative_outcome=random.choice(negative_outcomes),
        improvement=random.choice(improvements),
    )

    # Add professional signoff occasionally
    if random.random() < 0.3:
        signoffs = [
            " -Former restaurant chef",
            " -Culinary school graduate",
            " -Professional cook's perspective",
            " -From a chef's standpoint",
            " -Industry veteran's take",
        ]
        result += random.choice(signoffs)

    return result


def generate_basic_comment(dish, rating):
    # Basic, general comments for variety
    if rating >= 4:
        comments = [
            f"Loved this {dish.name}! Great recipe.",
            f"Really enjoyed making this. Turned out delicious.",
            f"Excellent dish, will definitely make again.",
            f"This recipe was a hit with my family.",
            f"Fantastic flavor and easy to follow instructions.",
            f"One of the best {dish.name} recipes I've tried.",
            f"Absolutely delicious! Will be making this regularly.",
            f"Great recipe! Followed it exactly and it turned out perfect.",
        ]
    elif rating >= 3:
        comments = [
            f"Pretty good. Made some minor adjustments.",
            f"Decent recipe. Added a bit more seasoning.",
            f"Good {dish.name} recipe, but not exceptional.",
            f"Turned out okay. Might make again with some changes.",
            f"Not bad, but I've had better versions.",
            f"Solid recipe, though needed a bit more flavor.",
            f"It was good, but took longer than expected to prepare.",
            f"Decent dish. Family liked it well enough.",
        ]
    else:
        comments = [
            f"Didn't turn out well for me.",
            f"Not what I expected. Wouldn't make again.",
            f"Didn't care for this version of {dish.name}.",
            f"Recipe needs work. Lacked flavor.",
            f"Too complicated for the end result.",
            f"Disappointing outcome. Something was off with the recipe.",
            f"Not worth the effort. Couldn't salvage it.",
            f"Unfortunately this didn't work out at all.",
        ]

    return random.choice(comments)


# Generate realistic dates with activity patterns
def generate_organic_date_pattern():
    # Create a realistic temporal distribution
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # More reviews in certain periods (holidays, weekends)
    def date_weight(date):
        # Weekend bias
        if date.weekday() >= 5:  # Saturday or Sunday
            weight = 1.5
        else:
            weight = 1.0

        # Holiday season bias (November-December)
        if date.month in [11, 12]:
            weight *= 1.4

        # Summer cooking bias (June-August)
        if date.month in [6, 7, 8]:
            weight *= 1.3

        # January health kick
        if date.month == 1:
            weight *= 1.2

        return weight

    # Generate all possible dates
    date_range = []
    current = start_date
    while current <= end_date:
        date_range.append(current)
        current += timedelta(days=1)

    # Calculate weights
    weights = [date_weight(date) for date in date_range]

    # Return weighted random date
    selected_date = random.choices(date_range, weights=weights, k=1)[0]
    return selected_date.strftime("%Y-%m-%d")


# Rating distribution model (varies by dish)
def generate_rating_distribution(dish, persona):
    """
    Generate a rating (1–5) based on dish true mean and reviewer persona.
    Uses Beta distributions for skew and variance.
    """
    mean = dish_true_means[dish.id]

    # Persona-specific bias (alpha, beta for Beta distribution)
    persona_params = {
        "casual": (3, 1.5),  # Skews high, casuals usually 4–5
        "enthusiast": (4, 1.2),  # Heavy 5-star bias
        "critic": (2, 2.5),  # More low/mid reviews
        "expert": (2.2, 2),  # Stricter than critic
    }

    alpha, beta = persona_params.get(persona, (2.5, 2))  # default balance

    # Draw base rating from Beta(α, β), scaled 1–5
    raw_score = np.random.beta(alpha, beta) * 4 + 1
    rating = round(raw_score)

    # Influence from dish's "true mean"
    if random.random() < 0.6:  # 60% of time, ratings lean toward dish quality
        noise = np.random.normal(mean, 0.7)
        rating = round((rating + noise) / 2)

    return max(1, min(5, rating))


# Generate reviews
total_reviews = 0
target_reviews = 1000

# Mapping users to personas for consistency
user_personas = {}
for user in users:
    persona_weights = [0.4, 0.2, 0.3, 0.1]  # casual, critic, enthusiast, expert
    user_personas[user.username] = random.choices(
        ["casual", "critic", "enthusiast", "expert"], weights=persona_weights, k=1
    )[0]

# Distribute reviews organically across dishes
# Some dishes are more popular than others
dish_popularity = {}
for dish in dishes:
    # Base popularity
    popularity = random.uniform(0.5, 1.5)

    # Adjust for factors
    if "Quick" in dish.tags:
        popularity *= 1.2  # Quick recipes are more popular

    if "Vegetarian" in dish.tags:
        popularity *= 0.9  # Slightly less popular (statistically)

    if "Spicy" in dish.tags:
        popularity *= 0.85  # Polarizing

    dish_popularity[dish.id] = popularity

# Normalize popularity
total_popularity = sum(dish_popularity.values())
for dish_id in dish_popularity:
    dish_popularity[dish_id] /= total_popularity

# Distribute reviews based on popularity
dish_review_targets = {}
for dish_id, popularity in dish_popularity.items():
    # Allocate reviews by popularity, with some randomness
    allocated = int(target_reviews * popularity * random.uniform(0.8, 1.2))
    dish_review_targets[dish_id] = allocated

# Create reviews
for dish in dishes:
    # How many reviews for this dish
    target_for_dish = dish_review_targets.get(dish.id, 10)

    # Users who haven't already reviewed this dish
    reviewed_user_ids = [review.user_id for review in dish.reviews]
    available_users = [user for user in users if user.id not in reviewed_user_ids]

    if not available_users:
        continue

    # Limit by available users
    target_for_dish = min(target_for_dish, len(available_users))

    # Add new reviews
    new_reviews_count = 0
    for _ in range(target_for_dish):
        if not available_users:
            break

        user = random.choice(available_users)
        available_users.remove(user)

        # Get user's persona
        persona = user_personas.get(user.username, "casual")

        # Generate rating based on dish characteristics
        rating = generate_rating_distribution(dish, persona)

        # Generate comment based on rating and persona
        comment = generate_comment(dish, rating, persona)

        # Generate organic date
        review_date = datetime.strptime(
            generate_organic_date_pattern(), "%Y-%m-%d"
        ).date()

        # Create review in database
        review = Review(
            dish_id=dish.id,
            user_id=user.id,
            rating=rating,
            comment=comment,
            date=review_date,
        )
        db.session.add(review)
        new_reviews_count += 1
        total_reviews += 1

        # Commit periodically to avoid memory issues
        if total_reviews % 50 == 0:
            db.session.commit()

    print(
        f"Added {new_reviews_count} reviews to {dish.name}. Total reviews: {total_reviews}"
    )

    # Update dish's average rating
    if new_reviews_count > 0:
        dish.update_avg_rating()

# Final commit for any remaining reviews
db.session.commit()

print(f"Generation complete. Added {total_reviews} new reviews directly to database.")

# Generate some statistics
ratings_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
persona_count = {"casual": 0, "critic": 0, "enthusiast": 0, "expert": 0}
review_lengths = []

for dish in dishes:
    for review in dish.reviews:
        rating_key = int(review.rating)
        ratings_count[rating_key] = ratings_count.get(rating_key, 0) + 1
        review_lengths.append(len(review.comment))

        # Infer persona from review format (simplified)
        if "😋" in review.comment or "😍" in review.comment:
            persona_count["casual"] += 1
        elif "technique" in review.comment and len(review.comment) > 150:
            persona_count["expert"] += 1
        elif "balance of flavors" in review.comment:
            persona_count["critic"] += 1
        else:
            persona_count["enthusiast"] += 1

print("\nReview Statistics:")
print(f"Total reviews: {total_reviews}")
print(f"Rating distribution: {ratings_count}")
print(
    f"Average review length: {sum(review_lengths) / len(review_lengths) if review_lengths else 0:.1f} characters"
)
print(f"Persona distribution: {persona_count}")
print(f"Most common rating: {max(ratings_count, key=ratings_count.get)}")

# Optional: Export a CSV of review data for analysis
try:
    import csv

    with open("data/review_analytics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "dish_id",
                "dish_name",
                "user",
                "rating",
                "date",
                "comment_length",
                "cuisine",
            ]
        )

        for dish in dishes:
            cuisine = next(
                (
                    tag
                    for tag in dish.tags
                    if tag
                    in [
                        "Italian",
                        "Mexican",
                        "Japanese",
                        "Indian",
                        "Chinese",
                        "French",
                        "Thai",
                        "Vietnamese",
                        "Greek",
                        "American",
                    ]
                ),
                "Other",
            )

            for review in dish.reviews:
                writer.writerow(
                    [
                        dish.id,
                        dish.name,
                        review.author.username,
                        review.rating,
                        review.date,
                        len(review.comment),
                        cuisine,
                    ]
                )
    print("Review analytics exported to data/review_analytics.csv")
except Exception as e:
    print(f"Could not export analytics CSV: {e}")

# Optional: Generate word clouds for positive and negative reviews
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    from collections import Counter

    # Collect words from positive and negative reviews
    positive_words = []
    negative_words = []

    for dish in dishes:
        for review in dish.reviews:
            words = re.findall(r"\b[a-zA-Z]{3,15}\b", review.comment.lower())
            if review.rating >= 4:
                positive_words.extend(words)
            elif review.rating <= 2:
                negative_words.extend(words)

    # Remove common stopwords
    stopwords = set(
        [
            "the",
            "and",
            "was",
            "for",
            "this",
            "that",
            "with",
            "have",
            "but",
            "not",
            "are",
            "from",
            "were",
            "they",
            "you",
            "had",
            "has",
            "very",
            "would",
            "could",
            "should",
            "been",
            "did",
            "made",
            "much",
        ]
    )

    positive_words = [word for word in positive_words if word not in stopwords]
    negative_words = [word for word in negative_words if word not in stopwords]

    # Create word frequency counters
    positive_counter = Counter(positive_words)
    negative_counter = Counter(negative_words)

    # Generate word clouds
    if positive_counter:
        positive_cloud = WordCloud(
            width=800, height=400, background_color="white", max_words=100
        ).generate_from_frequencies(positive_counter)
        plt.figure(figsize=(10, 5))
        plt.imshow(positive_cloud, interpolation="bilinear")
        plt.axis("off")
        plt.title("Common Words in Positive Reviews")
        plt.savefig("data/positive_reviews_wordcloud.png")
        print(
            "Positive reviews word cloud saved to data/positive_reviews_wordcloud.png"
        )

    if negative_counter:
        negative_cloud = WordCloud(
            width=800, height=400, background_color="white", max_words=100
        ).generate_from_frequencies(negative_counter)
        plt.figure(figsize=(10, 5))
        plt.imshow(negative_cloud, interpolation="bilinear")
        plt.axis("off")
        plt.title("Common Words in Negative Reviews")
        plt.savefig("data/negative_reviews_wordcloud.png")
        print(
            "Negative reviews word cloud saved to data/negative_reviews_wordcloud.png"
        )

except Exception as e:
    print(f"Could not generate word clouds: {e}")

# Optional: Create rating distribution visualization
try:
    import matplotlib.pyplot as plt
    import numpy as np

    # Get average ratings by cuisine
    cuisine_ratings = {}
    for dish in dishes:
        cuisine = next(
            (
                tag
                for tag in dish.tags
                if tag
                in [
                    "Italian",
                    "Mexican",
                    "Japanese",
                    "Indian",
                    "Chinese",
                    "French",
                    "Thai",
                    "Vietnamese",
                    "Greek",
                    "American",
                ]
            ),
            "Other",
        )

        if cuisine not in cuisine_ratings:
            cuisine_ratings[cuisine] = []

        if dish.avg_rating is not None:
            cuisine_ratings[cuisine].append(dish.avg_rating)

    # Calculate averages
    cuisine_avgs = {}
    for cuisine, ratings in cuisine_ratings.items():
        if ratings:
            cuisine_avgs[cuisine] = sum(ratings) / len(ratings)

    if cuisine_avgs:
        # Sort by average rating
        sorted_cuisines = sorted(cuisine_avgs.items(), key=lambda x: x[1], reverse=True)
        cuisines = [x[0] for x in sorted_cuisines]
        avgs = [x[1] for x in sorted_cuisines]

        plt.figure(figsize=(12, 6))
        plt.bar(cuisines, avgs, color="skyblue")
        plt.xlabel("Cuisine")
        plt.ylabel("Average Rating")
        plt.title("Average Rating by Cuisine")
        plt.ylim(0, 5)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("data/cuisine_ratings.png")
        print("Cuisine rating chart saved to data/cuisine_ratings.png")

    # Rating distribution histogram
    all_ratings = []
    for dish in dishes:
        for review in dish.reviews:
            all_ratings.append(review.rating)

    if all_ratings:
        plt.figure(figsize=(10, 6))
        plt.hist(
            all_ratings,
            bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
            color="lightgreen",
            edgecolor="black",
            alpha=0.7,
        )
        plt.xlabel("Rating")
        plt.ylabel("Number of Reviews")
        plt.title("Distribution of Review Ratings")
        plt.xticks([1, 2, 3, 4, 5])
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.savefig("data/rating_distribution.png")
        print("Rating distribution histogram saved to data/rating_distribution.png")

    # Generate a time series of ratings
    dates = []
    time_ratings = []

    for dish in dishes:
        for review in dish.reviews:
            dates.append(review.date)
            time_ratings.append(review.rating)

    if dates and time_ratings:
        # Sort by date
        sorted_data = sorted(zip(dates, time_ratings))
        dates = [item[0] for item in sorted_data]
        time_ratings = [item[1] for item in sorted_data]

        # Calculate moving average
        window_size = min(30, len(dates))
        moving_avg = []

        for i in range(len(dates) - window_size + 1):
            window_avg = sum(time_ratings[i : i + window_size]) / window_size
            moving_avg.append(window_avg)

        plt.figure(figsize=(12, 6))
        plt.plot(dates[window_size - 1 :], moving_avg, color="purple", linewidth=2)
        plt.xlabel("Date")
        plt.ylabel("30-Day Moving Average Rating")
        plt.title("Rating Trend Over Time")
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.ylim(1, 5)
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.savefig("data/rating_trend.png")
        print("Rating trend chart saved to data/rating_trend.png")

except Exception as e:
    print(f"Could not generate visualizations: {e}")

print("\nReview generation and analysis complete!")
