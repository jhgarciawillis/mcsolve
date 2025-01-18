from typing import List, Dict, Tuple, Optional
from species import Species, SpeciesType, Ecosystem
from ecosystem import FeedingSimulation
from constants import (
    TOTAL_PRODUCERS_NEEDED, TOTAL_ANIMALS_NEEDED,
    ERROR_MESSAGES
)
class SolutionValidator:
    def __init__(self, debug_container=None, debug_mode=False):
        self.debug_container = debug_container
        self.debug_mode = debug_mode

    def validate_solution(self, ecosystem: Ecosystem, solution: List[Species]) -> Tuple[bool, List[str]]:
        """Validates if a proposed solution is valid"""
        errors = []
        
        if self.debug_mode:
            self.debug_container.write("\nValidating solution...")
            self.debug_container.write(f"Solution size: {len(solution)} species")
        
        # Check basic counts
        producers = [s for s in solution if s.species_type == SpeciesType.PRODUCER]
        animals = [s for s in solution if s.species_type == SpeciesType.ANIMAL]
        
        if self.debug_mode:
            self.debug_container.write(f"Producers in solution: {len(producers)}")
            self.debug_container.write(f"Animals in solution: {len(animals)}")
        
        if len(producers) != TOTAL_PRODUCERS_NEEDED:
            errors.append(ERROR_MESSAGES['invalid_producer_count'])
        if len(animals) != TOTAL_ANIMALS_NEEDED:
            errors.append(ERROR_MESSAGES['invalid_animal_count'])
            
        if errors:
            if self.debug_mode:
                self.debug_container.write("Basic count validation failed:")
                for error in errors:
                    self.debug_container.write(f"- {error}")
            return False, errors
            
        # Simulate feeding rounds
        if self.debug_mode:
            self.debug_container.write("\nStarting feeding simulation...")
            
        simulation = FeedingSimulation(solution, self.debug_container, self.debug_mode)
        success, feeding_history = simulation.simulate_feeding_round()
        
        if not success:
            if self.debug_mode:
                self.debug_container.write("Feeding simulation failed")
            # Analyze why simulation failed
            for species in solution:
                if species.species_type == SpeciesType.ANIMAL:
                    if species.id not in simulation.has_eaten:
                        errors.append(ERROR_MESSAGES['insufficient_calories'].format(species.id))
                if simulation.calories_remaining[species.id] <= 0:
                    errors.append(ERROR_MESSAGES['calories_depleted'].format(species.id))
        
        # Check bin compatibility
        bins = set(s.bin for s in solution)
        if len(bins) > 1:
            errors.append(ERROR_MESSAGES['invalid_bin'])
            if self.debug_mode:
                self.debug_container.write(f"Found species from multiple bins: {bins}")
                
        is_valid = len(errors) == 0
        if self.debug_mode:
            self.debug_container.write(f"\nValidation {'succeeded' if is_valid else 'failed'}")
            if not is_valid:
                self.debug_container.write("Errors found:")
                for error in errors:
                    self.debug_container.write(f"- {error}")
                    
        return is_valid, errors

    def get_solution_score(self, solution: List[Species], feeding_history: List[Dict]) -> float:
        """Calculate a score for the solution"""
        if self.debug_mode:
            self.debug_container.write("\nCalculating solution score...")
        
        # Calculate various scoring components
        total_calories_needed = sum(s.calories_needed for s in solution if s.species_type == SpeciesType.ANIMAL)
        total_calories_consumed = sum(h['calories_consumed'] for h in feeding_history)
        caloric_efficiency = total_calories_needed / total_calories_consumed if total_calories_consumed > 0 else 0
        
        unique_relationships = len(set((h['predator'], h['prey']) for h in feeding_history))
        producer_ratio = len([s for s in solution if s.species_type == SpeciesType.PRODUCER]) / len(solution)
        
        if self.debug_mode:
            self.debug_container.write(f"Caloric efficiency: {caloric_efficiency:.2f}")
            self.debug_container.write(f"Unique relationships: {unique_relationships}")
            self.debug_container.write(f"Producer ratio: {producer_ratio:.2f}")
        
        # Calculate final score
        score = (caloric_efficiency * 0.4 + 
                unique_relationships * 0.4 + 
                producer_ratio * 0.2)
                
        if self.debug_mode:
            self.debug_container.write(f"Final score: {score:.2f}")
        
        return score