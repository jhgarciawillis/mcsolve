from typing import List, Set, Dict, Tuple
import random
from .species import Species, SpeciesType, Ecosystem
from .validator import SolutionValidator
from .ecosystem import FeedingSimulation
from .constants import (
    BINS, PRODUCERS_PER_BIN, ANIMALS_PER_BIN,
    MIN_CALORIES, MAX_CALORIES, CALORIE_STEP,
    TARGET_PREDATORS, TARGET_PREY
)

class ScenarioGenerator:
    def __init__(self):
        self.calorie_ranges = {
            'producer': (MIN_CALORIES, MAX_CALORIES),
            'animal': {
                'provided': (MIN_CALORIES, MAX_CALORIES),
                'needed': (MIN_CALORIES, MAX_CALORIES)
            }
        }

    def _round_to_50(self, number: int) -> int:
        """Round a number to the nearest 50"""
        return round(number / CALORIE_STEP) * CALORIE_STEP

    def generate_scenario(self) -> Ecosystem:
        """Generate a complete scenario with valid species across all bins"""
        all_species = []
        
        # Generate producers for each bin
        for bin_id in BINS:
            producers = self._generate_producers(bin_id)
            all_species.extend(producers)
            
        # Generate animals for each bin
        for bin_id in BINS:
            animals = self._generate_animals(bin_id)
            all_species.extend(animals)
            
        # Establish food chain relationships
        self._establish_relationships(all_species)
        
        return Ecosystem(all_species)

    def _generate_producers(self, bin_id: str) -> List[Species]:
        """Generate producers for a specific bin"""
        producers = []
        for i in range(PRODUCERS_PER_BIN):
            calories = self._round_to_50(random.randint(*self.calorie_ranges['producer']))
            producer = Species(
                id=f"P_{bin_id}_{i+1}",
                name=f"Producer {bin_id}{i+1}",
                species_type=SpeciesType.PRODUCER,
                calories_provided=calories,
                calories_needed=0,
                bin=bin_id
            )
            producers.append(producer)
        return producers

    def _generate_animals(self, bin_id: str) -> List[Species]:
        """Generate animals for a specific bin"""
        animals = []
        for i in range(ANIMALS_PER_BIN):
            calories_provided = self._round_to_50(
                random.randint(*self.calorie_ranges['animal']['provided'])
            )
            calories_needed = self._round_to_50(
                random.randint(*self.calorie_ranges['animal']['needed'])
            )
            animal = Species(
                id=f"A_{bin_id}_{i+1}",
                name=f"Animal {bin_id}{i+1}",
                species_type=SpeciesType.ANIMAL,
                calories_provided=calories_provided,
                calories_needed=calories_needed,
                bin=bin_id
            )
            animals.append(animal)
        return animals

    def _establish_relationships(self, species: List[Species]):
        """Establish food chain relationships between species"""
        species_by_bin = {}
        for s in species:
            if s.bin not in species_by_bin:
                species_by_bin[s.bin] = {'producers': [], 'animals': []}
            if s.species_type == SpeciesType.PRODUCER:
                species_by_bin[s.bin]['producers'].append(s)
            else:
                species_by_bin[s.bin]['animals'].append(s)

        # For each bin
        for bin_id in BINS:
            bin_species = species_by_bin[bin_id]
            
            # Assign predators to producers (2-3 predators each)
            for producer in bin_species['producers']:
                num_predators = random.randint(2, 3)
                potential_predators = bin_species['animals'].copy()
                random.shuffle(potential_predators)
                
                for predator in potential_predators[:num_predators]:
                    predator.add_prey(producer.id)
                    producer.add_predator(predator.id)

            # Assign prey and predators to animals
            for animal in bin_species['animals']:
                # 2-3 prey for each animal
                potential_prey = ([s for s in bin_species['animals'] 
                                if s.calories_provided < animal.calories_provided
                                and s.id != animal.id] +
                               bin_species['producers'])
                
                if potential_prey:
                    num_prey = min(random.randint(2, 3), len(potential_prey))
                    selected_prey = random.sample(potential_prey, num_prey)
                    
                    for prey in selected_prey:
                        animal.add_prey(prey.id)
                        prey.add_predator(animal.id)


class SolutionGenerator:
    @staticmethod
    def generate_all_solutions(ecosystem: Ecosystem) -> List[List[Species]]:
        """Generate all possible valid solutions for the ecosystem"""
        from itertools import combinations
        
        all_solutions = []
        producers = ecosystem.get_producers()
        animals = ecosystem.get_animals()
        validator = SolutionValidator()
        
        for producer_combo in combinations(producers, 3):
            for animal_combo in combinations(animals, 5):
                solution = list(producer_combo) + list(animal_combo)
                is_valid, _ = validator.validate_solution(ecosystem, solution)
                if is_valid:
                    all_solutions.append(solution)
        
        return all_solutions

    @staticmethod
    def rank_solutions(solutions: List[List[Species]]) -> List[Tuple[List[Species], float]]:
        """Rank solutions by their score"""
        validator = SolutionValidator()
        scored_solutions = []
        
        for solution in solutions:
            simulation = FeedingSimulation(solution)
            success, feeding_history = simulation.simulate_feeding_round()
            
            if success:
                score = validator.get_solution_score(solution, feeding_history)
                scored_solutions.append((solution, score))
        
        return sorted(scored_solutions, key=lambda x: x[1], reverse=True)