# Game Constants
BINS = ['A', 'B', 'C']
PRODUCERS_PER_BIN = 3
ANIMALS_PER_BIN = 10
TOTAL_PRODUCERS_NEEDED = 3
TOTAL_ANIMALS_NEEDED = 5

# Excel Constants
REQUIRED_SHEETS = ['Species', 'Relationships']
SPECIES_COLUMNS = ['id', 'name', 'type', 'calories_provided', 'calories_needed', 'bin']
RELATIONSHIP_COLUMNS = ['predator_id', 'prey_id']

# Error Messages
ERROR_MESSAGES = {
    'invalid_producer_count': 'Solution must contain exactly 3 producers',
    'invalid_animal_count': 'Solution must contain exactly 5 animals',
    'calories_depleted': 'Species {} has been depleted of calories',
    'insufficient_calories': 'Species {} cannot obtain required calories',
    'invalid_bin': 'Not all species can coexist in the same bin'
}