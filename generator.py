from typing import List, Set, Dict, Tuple
import random
import time
from itertools import combinations
from species import Species, SpeciesType, Ecosystem
from validator import SolutionValidator
from ecosystem import FeedingSimulation
from constants import (
    BINS, 
    PRODUCERS_PER_BIN, 
    ANIMALS_PER_BIN,
    TOTAL_PRODUCERS_NEEDED, 
    TOTAL_ANIMALS_NEEDED,
    MIN_CALORIES, 
    MAX_CALORIES, 
    CALORIE_STEP,
    TARGET_PREDATORS, 
    TARGET_PREY,
    SAME_BIN_RELATIONSHIP_PROBABILITY,
    DIFFERENT_BIN_RELATIONSHIP_PROBABILITY,
    MAX_ATTEMPTS_PER_BIN,
    SOLUTION_TIMEOUT
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

    def _calculate_bin_total_calories(self, bin_producers: List[Species]) -> int:
        """Calculate total calories provided by producers in a bin"""
        return sum(p.calories_provided for p in bin_producers)

    def _rank_bins_by_calories(self, species: List[Species]) -> List[Tuple[str, int]]:
        """Rank bins by total producer calories"""
        bin_calories = {}
        for bin_id in BINS:
            producers = [s for s in species 
                        if s.species_type == SpeciesType.PRODUCER and s.bin == bin_id]
            bin_calories[bin_id] = self._calculate_bin_total_calories(producers)
        return sorted(bin_calories.items(), key=lambda x: x[1], reverse=True)

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

    def _establish_bin_relationships(self, producers: List[Species], animals: List[Species]):
        """Establish relationships within a bin"""
        # Sort animals by calories provided (descending)
        animals_sorted = sorted(animals, key=lambda x: x.calories_provided, reverse=True)
        
        # Assign predators to producers (2-3 predators each)
        for producer in producers:
            num_predators = random.randint(2, 3)
            potential_predators = animals_sorted.copy()
            random.shuffle(potential_predators)
            
            for predator in potential_predators[:num_predators]:
                predator.add_prey(producer.id)
                producer.add_predator(predator.id)

        # Assign prey and predators to animals
        for i, animal in enumerate(animals_sorted):
            # Potential prey are animals with lower calories
            potential_prey = animals_sorted[i+1:] + producers
            
            if potential_prey:
                num_prey = min(random.randint(2, 3), len(potential_prey))
                selected_prey = random.sample(potential_prey, num_prey)
                
                for prey in selected_prey:
                    animal.add_prey(prey.id)
                    prey.add_predator(animal.id)

    def _establish_relationships(self, species: List[Species]):
        """Establish all relationships"""
        # First establish same-bin relationships
        for bin_id in BINS:
            bin_species = [s for s in species if s.bin == bin_id]
            bin_producers = [s for s in bin_species if s.species_type == SpeciesType.PRODUCER]
            bin_animals = [s for s in bin_species if s.species_type == SpeciesType.ANIMAL]
            
            self._establish_bin_relationships(bin_producers, bin_animals)

class SolutionGenerator:
    @staticmethod
    def _create_solution_subset(producers: List[Species], animals: tuple) -> List[Species]:
        """Create a valid solution subset with updated relationships"""
        solution = []
        solution_ids = set()
        
        # Convert animals tuple to list and combine with producers
        all_species = producers + list(animals)
        
        # Add all selected species and collect their IDs
        for species in all_species:
            solution.append(species)
            solution_ids.add(species.id)
        
        # Create new species instances with filtered relationships
        filtered_solution = []
        for species in solution:
            # Create a new instance to avoid modifying original
            new_species = Species(
                id=species.id,
                name=species.name,
                species_type=species.species_type,
                calories_provided=species.calories_provided,
                calories_needed=species.calories_needed,
                bin=species.bin,
                predators=[p for p in species.predators if p in solution_ids],
                prey=[p for p in species.prey if p in solution_ids]
            )
            filtered_solution.append(new_species)
            
        return filtered_solution

    @staticmethod
    def generate_solutions(ecosystem: Ecosystem, debug_container=None, debug_mode=False) -> List[List[Species]]:
        """Generate all valid solutions"""
        start_time = time.time()
        solutions = []
        
        # Try bins in order of producer calories
        ranked_bins = ScenarioGenerator()._rank_bins_by_calories(ecosystem.species)
        
        for bin_id, calories in ranked_bins:
            if debug_mode:
                debug_container.write(f"\nTrying bin {bin_id} (Total calories: {calories})")
            
            bin_producers = [s for s in ecosystem.species 
                        if s.species_type == SpeciesType.PRODUCER and s.bin == bin_id]
            bin_animals = [s for s in ecosystem.species 
                        if s.species_type == SpeciesType.ANIMAL and s.bin == bin_id]
            
            bin_solutions = SolutionGenerator._generate_bin_solutions(
                bin_producers, bin_animals, debug_container, debug_mode
            )
            
            solutions.extend(bin_solutions)
            
            if debug_mode:
                debug_container.write(f"Found {len(bin_solutions)} solutions in bin {bin_id}")
            
            if time.time() - start_time > SOLUTION_TIMEOUT:
                if debug_mode:
                    debug_container.write("Solution timeout reached")
                break
        
        if debug_mode:
            debug_container.write(f"\nTotal solutions found across all bins: {len(solutions)}")
        
        return solutions

    @staticmethod
    def _generate_bin_solutions(producers: List[Species], animals: List[Species], 
                              debug_container=None, debug_mode=False) -> List[List[Species]]:
        """Generate solutions for a specific bin"""
        solutions = []
        validator = SolutionValidator(debug_container, debug_mode)
        
        if debug_mode:
            debug_container.write(f"Attempting combinations with {len(producers)} producers and {len(animals)} animals")
        
        for animal_combo in combinations(animals, TOTAL_ANIMALS_NEEDED):
            # Create filtered solution with only valid relationships
            solution = SolutionGenerator._create_solution_subset(producers, animal_combo)
            
            # Validate the solution
            is_valid, _ = validator.validate_solution(Ecosystem(solution), solution)
            
            if is_valid:
                solutions.append(solution)
                
                if debug_mode:
                    debug_container.write(f"Found valid solution! Total solutions: {len(solutions)}")
        
        return solutions

    @staticmethod
    def rank_solutions(solutions: List[List[Species]], debug_container=None, debug_mode=False) -> List[Tuple[List[Species], float]]:
        """Rank solutions by their score"""
        validator = SolutionValidator(debug_container, debug_mode)
        scored_solutions = []
        
        if debug_mode:
            debug_container.write("\nStarting solution ranking...")
            debug_container.write(f"Total solutions to rank: {len(solutions)}")
        
        for i, solution in enumerate(solutions):
            if debug_mode:
                debug_container.write(f"\nRanking solution {i+1}/{len(solutions)}")
            
            simulation = FeedingSimulation(solution, debug_container, debug_mode)
            success, feeding_history = simulation.simulate_feeding_round()
            
            if success:
                score = validator.get_solution_score(solution, feeding_history)
                scored_solutions.append((solution, score))
                
                if debug_mode:
                    debug_container.write(f"Solution {i+1} score: {score:.2f}")
                    debug_container.write("Feeding history:")
                    for feed in feeding_history:
                        debug_container.write(
                            f"- {feed['predator']} ate {feed['calories_consumed']} calories from {feed['prey']}"
                        )
            else:
                if debug_mode:
                    debug_container.write(f"Solution {i+1} failed feeding simulation")
        
        ranked_solutions = sorted(scored_solutions, key=lambda x: x[1], reverse=True)
        
        if debug_mode:
            debug_container.write("\nRanking complete.")
            if ranked_solutions:
                debug_container.write(f"Top score: {ranked_solutions[0][1]}")
            else:
                debug_container.write("No valid solutions found after ranking")
        
        return ranked_solutions