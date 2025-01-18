from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from species import Species, SpeciesType, Ecosystem
from constants import (
    MIN_CALORIES, 
    MAX_CALORIES,
    CALORIE_STEP,
    TOTAL_PRODUCERS_NEEDED,
    TOTAL_ANIMALS_NEEDED
)

class FeedingSimulation:
   def __init__(self, species: List[Species], debug_container=None, debug_mode=False):
       # Sort species by calories provided (highest first)
       self.species = sorted(species, key=lambda x: x.calories_provided, reverse=True)
       self.calories_remaining = {s.id: s.calories_provided for s in species}
       self.has_eaten = set()
       self.feeding_history = []
       self.debug_container = debug_container
       self.debug_mode = debug_mode
       
       if self.debug_mode:
           self.debug_container.write("\nInitializing Feeding Simulation:")
           self.debug_container.write(f"Total species: {len(species)}")
           self.debug_container.write("Initial calories:")
           for s in self.species:
               self.debug_container.write(f"- {s.name}: {self.calories_remaining[s.id]}")

   def simulate_feeding_round(self) -> Tuple[bool, List[dict]]:
       """Simulates one complete feeding round"""
       if self.debug_mode:
           self.debug_container.write("\nStarting feeding simulation...")
       
       # Process species in order of highest calories provided
       for species in self.species:
           if species.species_type == SpeciesType.PRODUCER:
               if self.debug_mode:
                   self.debug_container.write(f"\nSkipping producer: {species.name}")
               continue
           
           if self.debug_mode:
               self.debug_container.write(f"\nProcessing: {species.name}")
               self.debug_container.write(f"Calories needed: {species.calories_needed}")
               self.debug_container.write(f"Available prey: {[s.name for s in self._get_available_prey(species)]}")
           
           if not self._feed_species(species):
               if self.debug_mode:
                   self.debug_container.write(f"Failed to feed {species.name}")
                   self.debug_container.write("Current calorie state:")
                   for s in self.species:
                       self.debug_container.write(f"- {s.name}: {self.calories_remaining[s.id]}")
               return False, self.feeding_history
       
       if self.debug_mode:
           self.debug_container.write("\nFeeding simulation completed successfully")
           self.debug_container.write("Final calorie state:")
           for s in self.species:
               self.debug_container.write(f"- {s.name}: {self.calories_remaining[s.id]}")
       
       return True, self.feeding_history

   def _feed_species(self, species: Species) -> bool:
       """Feed a single species"""
       if species.id in self.has_eaten:
           if self.debug_mode:
               self.debug_container.write(f"{species.name} has already eaten")
           return True
       
       available_prey = self._get_available_prey(species)
       if not available_prey:
           if self.debug_mode:
               self.debug_container.write(f"No available prey for {species.name}")
           return False
       
       # Calculate total available calories
       total_available = sum(self.calories_remaining[p.id] for p in available_prey)
       if total_available < species.calories_needed:
           if self.debug_mode:
               self.debug_container.write(
                   f"Insufficient calories available: {total_available} < {species.calories_needed}"
               )
           return False

       if not self._distribute_feeding(species, available_prey, species.calories_needed):
           if self.debug_mode:
               self.debug_container.write(f"Failed to distribute feeding for {species.name}")
           return False

       self.has_eaten.add(species.id)
       return True

   def _distribute_feeding(self, predator: Species, prey: List[Species], calories_needed: int) -> bool:
       """Distribute feeding across available prey"""
       if not prey:
           return False
       
       if self.debug_mode:
           self.debug_container.write(f"\nDistributing feeding for {predator.name}")
           self.debug_container.write(f"Calories needed: {calories_needed}")
       
       calories_still_needed = calories_needed
       
       # Group prey by available calories
       calories_groups = {}
       for p in prey:
           remaining = self.calories_remaining[p.id]
           if remaining not in calories_groups:
               calories_groups[remaining] = []
           calories_groups[remaining].append(p)
       
       if self.debug_mode:
           self.debug_container.write("Prey groups by calories:")
           for calories, group in calories_groups.items():
               self.debug_container.write(f"- {calories} calories: {[p.name for p in group]}")
       
       # Process groups in descending order of calories
       for calories, group in sorted(calories_groups.items(), reverse=True):
           if len(group) > 1:
               # Multiple prey with same calories - distribute evenly
               calories_per_prey = min(calories, calories_still_needed / len(group))
               if self.debug_mode:
                   self.debug_container.write(f"Multiple prey with {calories} calories")
                   self.debug_container.write(f"Taking {calories_per_prey} from each")
               
               for p in group:
                   if self.calories_remaining[p.id] < calories_per_prey:
                       continue
                   
                   self.calories_remaining[p.id] -= calories_per_prey
                   calories_still_needed -= calories_per_prey
                   
                   self.feeding_history.append({
                       "predator": predator.id,
                       "prey": p.id,
                       "calories_consumed": calories_per_prey
                   })
                   
                   if self.debug_mode:
                       self.debug_container.write(
                           f"{predator.name} consumed {calories_per_prey} calories from {p.name}"
                       )
           else:
               # Single prey - take what's needed
               p = group[0]
               calories_to_take = min(self.calories_remaining[p.id], calories_still_needed)
               self.calories_remaining[p.id] -= calories_to_take
               calories_still_needed -= calories_to_take
               
               self.feeding_history.append({
                   "predator": predator.id,
                   "prey": p.id,
                   "calories_consumed": calories_to_take
               })
               
               if self.debug_mode:
                   self.debug_container.write(
                       f"{predator.name} consumed {calories_to_take} calories from {p.name}"
                   )
           
           if calories_still_needed <= 0:
               break
       
       if self.debug_mode:
           self.debug_container.write(
               f"Calories still needed after distribution: {calories_still_needed}"
           )
           
       return calories_still_needed <= 0

   def _get_available_prey(self, species: Species) -> List[Species]:
       """Get all available prey for a species, sorted by remaining calories"""
       # Get prey that still have calories available
       available = [s for s in self.species 
                   if s.id in species.prey and self.calories_remaining[s.id] > 0]
       
       # Sort by remaining calories and same bin preference
       return sorted(
           available,
           key=lambda x: (x.bin == species.bin, self.calories_remaining[x.id]),
           reverse=True
       )

   def get_feeding_stats(self) -> Dict:
       """Get statistics about the feeding simulation"""
       return {
           'total_species': len(self.species),
           'species_fed': len(self.has_eaten),
           'total_calories_consumed': sum(f['calories_consumed'] for f in self.feeding_history),
           'feeding_interactions': len(self.feeding_history),
           'remaining_calories': self.calories_remaining.copy(),
           'average_consumption': sum(f['calories_consumed'] for f in self.feeding_history) / 
                                len(self.feeding_history) if self.feeding_history else 0
       }

   def get_species_feeding_summary(self, species_id: str) -> Dict:
       """Get feeding summary for a specific species"""
       consumed_as_prey = sum(
           f['calories_consumed'] for f in self.feeding_history 
           if f['prey'] == species_id
       )
       consumed_as_predator = sum(
           f['calories_consumed'] for f in self.feeding_history 
           if f['predator'] == species_id
       )
       return {
           'consumed_as_prey': consumed_as_prey,
           'consumed_as_predator': consumed_as_predator,
           'remaining_calories': self.calories_remaining[species_id],
           'interactions_as_prey': len([f for f in self.feeding_history if f['prey'] == species_id]),
           'interactions_as_predator': len([f for f in self.feeding_history if f['predator'] == species_id])
       }