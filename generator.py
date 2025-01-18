from typing import List, Set, Dict, Tuple
import random
from species import Species, SpeciesType, Ecosystem
from validator import SolutionValidator
from ecosystem import FeedingSimulation
from constants import (
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
    def generate_all_solutions(ecosystem: Ecosystem, debug_container=None, debug_mode=False) -> List[List[Species]]:
        """Generate all possible valid solutions for the ecosystem"""
        from itertools import combinations
        
        if debug_mode:
            debug_container.write("Starting solution generation...")
        
        all_solutions = []
        producers = ecosystem.get_producers()
        animals = ecosystem.get_animals()
        validator = SolutionValidator()
        
        if debug_mode:
            debug_container.write(f"Total producers available: {len(producers)}")
            debug_container.write(f"Total animals available: {len(animals)}")
        
        producer_combinations = list(combinations(producers, 3))
        animal_combinations = list(combinations(animals, 5))
        
        if debug_mode:
            debug_container.write(f"Total producer combinations: {len(producer_combinations)}")
            debug_container.write(f"Total animal combinations: {len(animal_combinations)}")
            total_combinations = len(producer_combinations) * len(animal_combinations)
            debug_container.write(f"Total possible combinations: {total_combinations}")
            
            progress_step = max(1, total_combinations // 100)
            combination_count = 0
        
        for producer_combo in producer_combinations:
            for animal_combo in animal_combinations:
                if debug_mode:
                    combination_count += 1
                    if combination_count % progress_step == 0:
                        progress = (combination_count / total_combinations) * 100
                        debug_container.write(f"Progress: {progress:.1f}% ({combination_count}/{total_combinations})")
                
                solution = list(producer_combo) + list(animal_combo)
                
                if debug_mode:
                    debug_container.write(f"\nTesting combination {combination_count}:")
                    debug_container.write(f"Producers: {[p.name for p in producer_combo]}")
                    debug_container.write(f"Animals: {[a.name for a in animal_combo]}")
                
                # Validate the solution
                is_valid, errors = validator.validate_solution(ecosystem, solution)
                
                if debug_mode and not is_valid:
                    debug_container.write(f"Invalid solution: {errors}")
                
                if is_valid:
                    if debug_mode:
                        debug_container.write("Valid solution found!")
                    all_solutions.append(solution)
        
        if debug_mode:
            debug_container.write(f"\nSolution generation complete. Found {len(all_solutions)} valid solutions.")
        
        return all_solutions

    @staticmethod
    def rank_solutions(solutions: List[List[Species]], debug_container=None, debug_mode=False) -> List[Tuple[List[Species], float]]:
        """Rank solutions by their score"""
        validator = SolutionValidator()
        scored_solutions = []
        
        if debug_mode:
            debug_container.write("\nStarting solution ranking...")
            debug_container.write(f"Total solutions to rank: {len(solutions)}")
        
        for i, solution in enumerate(solutions):
            if debug_mode:
                debug_container.write(f"\nRanking solution {i+1}/{len(solutions)}")
            
            simulation = FeedingSimulation(solution)
            success, feeding_history = simulation.simulate_feeding_round()
            
            if success:
                score = validator.get_solution_score(solution, feeding_history)
                scored_solutions.append((solution, score))
                
                if debug_mode:
                    debug_container.write(f"Solution {i+1} score: {score:.2f}")
                    debug_container.write("Feeding history:")
                    for feed in feeding_history:
                        debug_container.write(f"- {feed['predator']} ate {feed['calories_consumed']} calories from {feed['prey']}")
            else:
                if debug_mode:
                    debug_container.write(f"Solution {i+1} failed feeding simulation")
        
        ranked_solutions = sorted(scored_solutions, key=lambda x: x[1], reverse=True)
        
        if debug_mode:
            debug_container.write("\nRanking complete.")
            debug_container.write(f"Top score: {ranked_solutions[0][1] if ranked_solutions else 0}")
        
        return ranked_solutions