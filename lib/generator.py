from typing import List, Set, Dict, Tuple
import random
from .species import Species, SpeciesType, Ecosystem
from .validator import SolutionValidator
from .ecosystem import FeedingSimulation
from .constants import BINS, PRODUCERS_PER_BIN, ANIMALS_PER_BIN

class ScenarioGenerator:
    def __init__(self):
        self.calorie_ranges = {
            'producer': (1000, 6000),
            'animal': {
                'provided': (1000, 6000),
                'needed': (1000, 6000)
            }
        }

    def _round_to_50(self, number: int) -> int:
        """Round a number to the nearest 50"""
        return round(number / 50) * 50

    def generate_scenario(self) -> Ecosystem:
        """Generate a complete scenario with valid species across all bins"""
        all_species = []
        
        # Generate producers for each bin
        for bin_id in BINS:
            producers = self._generate_producers(bin_id)
            all_species.extend(producers)
            
        # Generate animals for each bin
        for bin_id in BINS:
            animals = self._generate_animals(bin_id, all_species)
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
                calories_needed=0,  # Producers don't need calories
                bin=bin_id,
                food_sources=set(),  # Producers have no food sources
                eaten_by=set()
            )
            producers.append(producer)
        return producers

    def _generate_animals(self, bin_id: str, existing_species: List[Species]) -> List[Species]:
        """Generate animals for a specific bin"""
        animals = []
        for i in range(ANIMALS_PER_BIN):
            calories_provided = self._round_to_50(random.randint(*self.calorie_ranges['animal']['provided']))
            calories_needed = self._round_to_50(random.randint(*self.calorie_ranges['animal']['needed']))
            animal = Species(
                id=f"A_{bin_id}_{i+1}",
                name=f"Animal {bin_id}{i+1}",
                species_type=SpeciesType.ANIMAL,
                calories_provided=calories_provided,
                calories_needed=calories_needed,
                bin=bin_id,
                food_sources=set(),
                eaten_by=set()
            )
            animals.append(animal)
        return animals

    def _establish_relationships(self, species: List[Species]):
        """Establish food chain relationships between species"""
        producers = [s for s in species if s.species_type == SpeciesType.PRODUCER]
        animals = [s for s in species if s.species_type == SpeciesType.ANIMAL]
        
        # Ensure producers have no food sources and no calories needed
        for producer in producers:
            producer.food_sources = set()
            producer.calories_needed = 0
        
        for animal in animals:
            # Each animal has 40% chance to eat each producer in its bin
            for producer in producers:
                if producer.bin == animal.bin and random.random() < 0.4:
                    animal.food_sources.add(producer.id)
                    producer.eaten_by.add(animal.id)
            
            # Each animal has 30% chance to eat each smaller animal in its bin
            potential_prey = [a for a in animals 
                            if a.bin == animal.bin 
                            and a.calories_provided < animal.calories_provided
                            and a.id != animal.id]  # Prevent self-predation
            
            # Allow multiple prey selection
            for prey in potential_prey:
                if random.random() < 0.3:
                    animal.food_sources.add(prey.id)
                    prey.eaten_by.add(animal.id)


class SolutionGenerator:
    @staticmethod
    def generate_all_solutions(ecosystem: Ecosystem) -> List[List[Species]]:
        """Generate all possible valid solutions for the ecosystem"""
        from itertools import combinations
        
        all_solutions = []
        producers = ecosystem.get_producers()
        animals = ecosystem.get_animals()
        validator = SolutionValidator()
        
        # Generate all possible combinations of 3 producers and 5 animals
        for producer_combo in combinations(producers, 3):
            for animal_combo in combinations(animals, 5):
                solution = list(producer_combo) + list(animal_combo)
                
                # Validate the solution
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

    @staticmethod
    def get_best_solution(ecosystem: Ecosystem) -> Tuple[List[Species], float]:
        """Get the highest scoring valid solution"""
        solutions = SolutionGenerator.generate_all_solutions(ecosystem)
        ranked_solutions = SolutionGenerator.rank_solutions(solutions)
        
        if not ranked_solutions:
            raise ValueError("No valid solutions found")
            
        return ranked_solutions[0]