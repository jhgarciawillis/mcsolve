# Game Constants
BINS = ['A', 'B', 'C']
PRODUCERS_PER_BIN = 3
ANIMALS_PER_BIN = 10
TOTAL_PRODUCERS_NEEDED = 3
TOTAL_ANIMALS_NEEDED = 5

# Species Sheet Columns
SPECIES_COLUMNS = [
    'id', 
    'name', 
    'type', 
    'calories_provided', 
    'calories_needed', 
    'bin',
    'predator_1', 
    'predator_2', 
    'predator_3', 
    'predator_4',
    'prey_1', 
    'prey_2', 
    'prey_3', 
    'prey_4'
]

# Calorie Constants
MIN_CALORIES = 1000
MAX_CALORIES = 6000
CALORIE_STEP = 50

# Relationship Limits
MAX_PREDATORS = 4
MAX_PREY = 4
TARGET_PREDATORS = 2  # Most species should have 2-3 predators
TARGET_PREY = 2      # Most animals should have 2-3 prey

# Error Messages
ERROR_MESSAGES = {
    'invalid_producer_count': 'Solution must contain exactly 3 producers',
    'invalid_animal_count': 'Solution must contain exactly 5 animals',
    'calories_depleted': 'Species {} has been depleted of calories',
    'insufficient_calories': 'Species {} cannot obtain required calories',
    'invalid_bin': 'Not all species can coexist in the same bin'
}