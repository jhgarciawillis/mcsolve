from typing import List, Dict, Tuple, Optional
from species import Species, SpeciesType, Ecosystem
from ecosystem import FeedingSimulation
from constants import (
    TOTAL_PRODUCERS_NEEDED,
    TOTAL_ANIMALS_NEEDED,
    ERROR_MESSAGES,
    SCORING_WEIGHTS,
    MAX_PREDATORS,
    MAX_PREY
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
       if not self._validate_relationships(solution):
           errors.append(ERROR_MESSAGES['invalid_relationships'])
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
                       if self.debug_mode:
                           self.debug_container.write(
                               f"{species.name} needs {species.calories_needed} calories but couldn't obtain them"
                           )
                           
               if simulation.calories_remaining[species.id] <= 0:
                   errors.append(ERROR_MESSAGES['calories_depleted'].format(species.id))
                   if self.debug_mode:
                       self.debug_container.write(f"{species.name} was completely depleted")

       if self.debug_mode:
           if not errors:
               self.debug_container.write("Solution validation successful!")
               self.debug_container.write("Final calorie state:")
               for species in solution:
                   self.debug_container.write(
                       f"- {species.name}: {simulation.calories_remaining[species.id]} calories remaining"
                   )
                   
       return len(errors) == 0, errors

   def _validate_relationships(self, solution: List[Species]) -> bool:
       """Validate relationship consistency within the solution"""
       species_dict = {s.id: s for s in solution}
       
       for species in solution:
           if species.species_type == SpeciesType.ANIMAL:
               # Check if animal has any prey
               if not species.prey:
                   if self.debug_mode:
                       self.debug_container.write(f"{species.name} has no prey")
                   return False
               
               # Verify prey references are valid
               for prey_id in species.prey:
                   if prey_id not in species_dict:
                       if self.debug_mode:
                           self.debug_container.write(f"Invalid prey reference: {prey_id}")
                       return False
                       
                   prey = species_dict[prey_id]
                   if species.id not in prey.predators:
                       if self.debug_mode:
                           self.debug_container.write(
                               f"Inconsistent relationship: {species.name} lists {prey.name} as prey "
                               f"but is not listed as its predator"
                           )
                       return False
       
       return True

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

   def validate_ecosystem(self, ecosystem: Ecosystem) -> Tuple[bool, List[str]]:
       """Validate entire ecosystem structure"""
       errors = []
       
       # Check basic structure
       for bin_id in set(s.bin for s in ecosystem.species):
           bin_producers = ecosystem.get_bin_producers(bin_id)
           bin_animals = ecosystem.get_bin_animals(bin_id)
           
           if len(bin_producers) != 3:
               errors.append(f"Bin {bin_id} has {len(bin_producers)} producers (should be 3)")
           if len(bin_animals) != 10:
               errors.append(f"Bin {bin_id} has {len(bin_animals)} animals (should be 10)")
       
       # Check relationship consistency
       for species in ecosystem.species:
           for pred_id in species.predators:
               predator = ecosystem.get_species_by_id(pred_id)
               if not predator or species.id not in predator.prey:
                   errors.append(f"Inconsistent relationship found for {species.name}")
       
       return len(errors) == 0, errors