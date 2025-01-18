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

# Relationship Constants
MAX_PREDATORS = 4
MAX_PREY = 4
TARGET_PREDATORS = 2  # Most species should have 2-3 predators
TARGET_PREY = 2      # Most animals should have 2-3 prey
SAME_BIN_RELATIONSHIP_PROBABILITY = 1  # 100% chance relationships are in same bin
DIFFERENT_BIN_RELATIONSHIP_PROBABILITY = 0  # 0% chance for cross-bin relationships

# Error Messages
ERROR_MESSAGES = {
   'invalid_producer_count': 'Solution must contain exactly 3 producers',
   'invalid_animal_count': 'Solution must contain exactly 5 animals',
   'calories_depleted': 'Species {} has been depleted of calories',
   'insufficient_calories': 'Species {} cannot obtain required calories',
   'invalid_bin': 'Not all species can coexist in the same bin',
   'invalid_relationships': 'Too many cross-bin relationships detected',
   'no_solution_in_bin': 'No valid solution found in bin {}',
}

# Generation Parameters
MAX_ATTEMPTS_PER_BIN = 1000  # Maximum number of attempts to find solution in a bin
SOLUTION_TIMEOUT = 300  # Maximum seconds to spend looking for solutions

# Scoring Weights
SCORING_WEIGHTS = {
   'caloric_efficiency': 0.4,
   'relationship_complexity': 0.4,
   'producer_ratio': 0.2
}

# Debug Constants
DEBUG_PROGRESS_STEP = 100  # Show progress every N combinations