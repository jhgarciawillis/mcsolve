from typing import List, Dict, Tuple, Optional
from species import Species, SpeciesType, Ecosystem
from ecosystem import FeedingSimulation
from constants import (
    TOTAL_PRODUCERS_NEEDED,
    TOTAL_ANIMALS_NEEDED,
    ERROR_MESSAGES,
    SCORING_WEIGHTS
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
            self.debug_container.write("Producer calories: " + 
                                    ", ".join([f"{p.name}: {p.calories_provided}" for p in producers]))
        
        # Validate counts
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

        # Validate bin compatibility
        unique_bins = set(s.bin for s in solution)
        if len(unique_bins) > 1:
            if self.debug_mode:
                self.debug_container.write(f"Multiple bins detected: {unique_bins}")
            errors.append(ERROR_MESSAGES['invalid_bin'])
            return False, errors

        # Validate relationships
        relationship_errors = self._validate_relationships(solution)
        if relationship_errors:
            errors.extend(relationship_errors)
            return False, errors

        # Simulate feeding rounds
        if self.debug_mode:
            self.debug_container.write("\nStarting feeding simulation...")
            
        simulation = FeedingSimulation(solution, self.debug_container, self.debug_mode)
        success, feeding_history = simulation.simulate_feeding_round()
        
        if not success:
            if self.debug_mode:
                self.debug_container.write("Feeding simulation failed")
            
            # Check for specific failures
            for species in solution:
                if species.species_type == SpeciesType.ANIMAL:
                    if species.id not in simulation.has_eaten:
                        errors.append(f"{species.name} couldn't obtain required calories of {species.calories_needed}")
                
                # Check for depleted species
                remaining_calories = simulation.calories_remaining[species.id]
                if remaining_calories <= 0:
                    errors.append(f"{species.name} would be depleted to {remaining_calories} calories")
                    if self.debug_mode:
                        self.debug_container.write(
                            f"{species.name} would end with {remaining_calories} calories"
                        )
        
        if self.debug_mode:
            if not errors:
                self.debug_container.write("Solution validation successful!")
                self.debug_container.write("Final calorie states:")
                for species in solution:
                    self.debug_container.write(
                        f"- {species.name}: {simulation.calories_remaining[species.id]} calories remaining"
                    )
                    
        return len(errors) == 0, errors

    def _validate_relationships(self, solution: List[Species]) -> List[str]:
        """Validate relationships between species"""
        errors = []
        solution_ids = {s.id for s in solution}
        species_dict = {s.id: s for s in solution}
        
        for species in solution:
            if species.species_type == SpeciesType.PRODUCER:
                # Producers must have no prey
                if species.prey:
                    errors.append(f"Producer {species.name} should not have prey")
                if species.calories_needed != 0:
                    errors.append(f"Producer {species.name} should not need calories")
                # Producers must have predators
                if not species.predators:
                    errors.append(f"Producer {species.name} must have at least one predator")
            else:
                # Animals must have prey
                if not species.prey:
                    errors.append(f"Animal {species.name} has no prey")
                    continue
                
                # Validate prey references
                invalid_prey = set(species.prey) - solution_ids
                if invalid_prey:
                    errors.append(f"Invalid prey references in {species.name}: {invalid_prey}")

                # Validate total available calories from prey
                potential_calories = sum(species_dict[prey_id].calories_provided 
                                      for prey_id in species.prey 
                                      if prey_id in species_dict)
                if potential_calories < species.calories_needed:
                    errors.append(
                        f"{species.name} needs {species.calories_needed} calories but maximum "
                        f"available from prey is {potential_calories}"
                    )

            # Validate bi-directional relationships
            for prey_id in species.prey:
                if prey_id in species_dict:
                    prey = species_dict[prey_id]
                    if species.id not in prey.predators:
                        errors.append(
                            f"Inconsistent relationship: {species.name} lists {prey.name} as prey "
                            f"but is not listed as its predator"
                        )
        
        return errors

    def get_solution_score(self, solution: List[Species], feeding_history: List[Dict]) -> float:
        """Calculate a score for the solution"""
        if self.debug_mode:
            self.debug_container.write("\nCalculating solution score...")
        
        # Calculate caloric efficiency
        total_calories_needed = sum(s.calories_needed for s in solution if s.species_type == SpeciesType.ANIMAL)
        total_calories_consumed = sum(h['calories_consumed'] for h in feeding_history)
        caloric_efficiency = total_calories_needed / total_calories_consumed if total_calories_consumed > 0 else 0
        
        # Calculate relationship complexity
        unique_relationships = len(set((h['predator'], h['prey']) for h in feeding_history))
        max_possible_relationships = TOTAL_ANIMALS_NEEDED * (TOTAL_PRODUCERS_NEEDED + TOTAL_ANIMALS_NEEDED - 1)
        relationship_complexity = unique_relationships / max_possible_relationships if max_possible_relationships > 0 else 0
        
        # Calculate producer ratio
        producer_ratio = len([s for s in solution if s.species_type == SpeciesType.PRODUCER]) / len(solution)
        
        if self.debug_mode:
            self.debug_container.write(f"Caloric efficiency: {caloric_efficiency:.2f}")
            self.debug_container.write(f"Relationship complexity: {relationship_complexity:.2f}")
            self.debug_container.write(f"Producer ratio: {producer_ratio:.2f}")
        
        # Calculate final score using weights
        score = (
            caloric_efficiency * SCORING_WEIGHTS['caloric_efficiency'] +
            relationship_complexity * SCORING_WEIGHTS['relationship_complexity'] +
            producer_ratio * SCORING_WEIGHTS['producer_ratio']
        )
        
        if self.debug_mode:
            self.debug_container.write(f"Final score: {score:.2f}")
        
        return score