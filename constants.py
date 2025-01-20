# constants.py

# Game Constants
BINS = ['A', 'B', 'C']
PRODUCERS_PER_BIN = 3
ANIMALS_PER_BIN = 10
TOTAL_PRODUCERS_NEEDED_ALL_BINS = 3
TOTAL_ANIMALS_NEEDED_ALL_BINS = 5
TOTAL_PRODUCERS_NEEDED_SINGLE_BIN = 3
TOTAL_ANIMALS_NEEDED_SINGLE_BIN = 10

# Species Sheet Base Columns
BASE_SPECIES_COLUMNS = [
   'id', 
   'name', 
   'type', 
   'calories_provided', 
   'calories_needed', 
   'bin'
]

# Calorie Constants
MIN_CALORIES = 1000
MAX_CALORIES = 6000
CALORIE_STEP = 50

# Relationship Constants
SAME_BIN_RELATIONSHIP_PROBABILITY = 1  # 100% chance relationships are in same bin
DIFFERENT_BIN_RELATIONSHIP_PROBABILITY = 0  # 0% chance for cross-bin relationships
TARGET_PREDATORS = 2  # Most species should have 2-3 predators
TARGET_PREY = 2      # Most animals should have 2-3 prey

# Error Messages
ERROR_MESSAGES = {
   'invalid_producer_count_all_bins': 'Solution must contain exactly 3 producers when starting from all bins',
   'invalid_animal_count_all_bins': 'Solution must contain exactly 5 animals when starting from all bins',
   'invalid_producer_count_single_bin': 'Solution must contain exactly 3 producers when starting from a single bin',
   'invalid_animal_count_single_bin': 'Solution must contain exactly 10 animals when starting from a single bin',
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