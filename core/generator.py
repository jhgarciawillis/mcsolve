import random
from typing import List, Set, Dict
from .species import Species, SpeciesType, Ecosystem
from ..utils.constants import BINS, PRODUCERS_PER_BIN, ANIMALS_PER_BIN

class ScenarioGenerator:
    def __init__(self):
        self.calorie_ranges = {
            'producer': (50, 200),
            'animal': {
                'provided': (30, 150),
                'needed': (20, 100)
            }
        }

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
            producer = Species(
                id=f"P_{bin_id}_{i+1}",
                name=f"Producer {bin_id}{i+1}",
                species_type=SpeciesType.PRODUCER,
                calories_provided=random.randint(*self.calorie_ranges['producer']),
                calories_needed=0,
                bin=bin_id
            )
            producers.append(producer)
        return producers

    def _generate_animals(self, bin_id: str, existing_species: List[Species]) -> List[Species]:
        """Generate animals for a specific bin"""
        animals = []
        for i in range(ANIMALS_PER_BIN):
            animal = Species(
                id=f"A_{bin_id}_{i+1}",
                name=f"Animal {bin_id}{i+1}",
                species_type=SpeciesType.ANIMAL,
                calories_provided=random.randint(*self.calorie_ranges['animal']['provided']),
                calories_needed=random.randint(*self.calorie_ranges['animal']['needed']),
                bin=bin_id
            )
            animals.append(animal)
        return animals

    def _establish_relationships(self, species: List[Species]):
        """Establish food chain relationships between species"""
        producers = [s for s in species if s.species_type == SpeciesType.PRODUCER]
        animals = [s for s in species if s.species_type == SpeciesType.ANIMAL]
        
        for animal in animals:
            # Each animal has 30% chance to eat each producer in its bin
            for producer in producers:
                if producer.bin == animal.bin and random.random() < 0.3:
                    animal.food_sources.add(producer.id)
                    producer.eaten_by.add(animal.id)
            
            # Each animal has 20% chance to eat each smaller animal in its bin
            potential_prey = [a for a in animals 
                            if a.bin == animal.bin 
                            and a.calories_provided < animal.calories_provided]
            
            for prey in potential_prey:
                if random.random() < 0.2:
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
        
        # Generate all possible combinations of 3 producers and 5 animals
        for producer_combo in combinations(producers, 3):
            for animal_combo in combinations(animals, 5):
                solution = list(producer_combo) + list(animal_combo)
                
                # Validate the solution
                validator = SolutionValidator()
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