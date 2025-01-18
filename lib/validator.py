from typing import List, Tuple, Dict
from .species import Species, SpeciesType, Ecosystem
from .ecosystem import FeedingSimulation
from .constants import ERROR_MESSAGES

class SolutionValidator:
    @staticmethod
    def validate_solution(ecosystem: Ecosystem, solution: List[Species]) -> Tuple[bool, List[str]]:
        """
        Validates if a proposed solution is valid
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check basic counts
        producers = [s for s in solution if s.species_type == SpeciesType.PRODUCER]
        animals = [s for s in solution if s.species_type == SpeciesType.ANIMAL]
        
        if len(producers) != 3:
            errors.append(ERROR_MESSAGES['invalid_producer_count'])
        if len(animals) != 5:
            errors.append(ERROR_MESSAGES['invalid_animal_count'])
            
        if errors:
            return False, errors
            
        # Simulate feeding rounds
        simulation = FeedingSimulation(solution)
        success, feeding_history = simulation.simulate_feeding_round()
        
        if not success:
            # Analyze why simulation failed
            for species in solution:
                if species.species_type == SpeciesType.ANIMAL:
                    if species.id not in simulation.has_eaten:
                        errors.append(ERROR_MESSAGES['insufficient_calories'].format(species.id))
                if simulation.calories_remaining[species.id] <= 0:
                    errors.append(ERROR_MESSAGES['calories_depleted'].format(species.id))
                    
        # Check bin compatibility
        if not SolutionValidator._check_bin_compatibility(solution):
            errors.append(ERROR_MESSAGES['invalid_bin'])
            
        return len(errors) == 0, errors

    @staticmethod
    def _check_bin_compatibility(solution: List[Species]) -> bool:
        """
        Checks if all species can exist in at least one common bin
        """
        bins = set.intersection(*[{s.bin} for s in solution])
        return len(bins) > 0

    @staticmethod
    def get_solution_score(solution: List[Species], feeding_history: List[Dict]) -> float:
        """
        Calculate a score for the solution based on:
        - Caloric efficiency
        - Food chain complexity
        - Species diversity
        """
        # Implementation of scoring logic
        score = 0.0
        
        # Caloric efficiency
        total_calories_needed = sum(s.calories_needed for s in solution if s.species_type == SpeciesType.ANIMAL)
        total_calories_consumed = sum(h['calories_consumed'] for h in feeding_history)
        caloric_efficiency = total_calories_needed / total_calories_consumed if total_calories_consumed > 0 else 0
        
        # Food chain complexity
        unique_relationships = len(set((h['predator'], h['prey']) for h in feeding_history))
        
        # Species diversity
        producer_ratio = len([s for s in solution if s.species_type == SpeciesType.PRODUCER]) / len(solution)
        
        score = (caloric_efficiency * 0.4 + 
                unique_relationships * 0.4 + 
                producer_ratio * 0.2)
                
        return score