from typing import List, Dict, Tuple, Set, Optional
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
        self.species = species
        self.calories_remaining = {s.id: s.calories_provided for s in species}
        self.has_eaten = set()  # Track which species have fed
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

        while True:
            # Find next species with highest remaining calories that hasn't eaten yet
            next_predator = self._get_next_predator()
            if not next_predator:
                break  # No more species that can feed
                
            if self.debug_mode:
                self.debug_container.write(f"\nNext predator: {next_predator.name}")
                self.debug_container.write(f"Current calories: {self.calories_remaining[next_predator.id]}")
                self.debug_container.write(f"Calories needed: {next_predator.calories_needed}")
            
            if not self._feed_species(next_predator):
                if self.debug_mode:
                    self.debug_container.write(f"Failed to feed {next_predator.name}")
                    self.debug_container.write("Current calorie state:")
                    for s in self.species:
                        self.debug_container.write(f"- {s.name}: {self.calories_remaining[s.id]}")
                return False, self.feeding_history

            # Check if any species has 0 or negative calories after feeding
            for species in self.species:
                if self.calories_remaining[species.id] <= 0:
                    if self.debug_mode:
                        self.debug_container.write(f"{species.name} has been depleted to {self.calories_remaining[species.id]} calories")
                    return False, self.feeding_history

        # Check if any species that needs to eat hasn't eaten
        for species in self.species:
            if species.species_type == SpeciesType.ANIMAL and species.id not in self.has_eaten:
                if self.debug_mode:
                    self.debug_container.write(f"{species.name} failed to eat")
                return False, self.feeding_history
        
        # Final check for any species with 0 or negative calories
        for species in self.species:
            if self.calories_remaining[species.id] <= 0:
                if self.debug_mode:
                    self.debug_container.write(f"{species.name} ended with {self.calories_remaining[species.id]} calories")
                return False, self.feeding_history
        
        if self.debug_mode:
            self.debug_container.write("\nFeeding simulation completed successfully")
            self.debug_container.write("Final calorie state:")
            for s in self.species:
                self.debug_container.write(f"- {s.name}: {self.calories_remaining[s.id]}")
        
        return True, self.feeding_history

    def _get_next_predator(self) -> Optional[Species]:
        """Get next species that should feed (highest remaining calories that hasn't eaten)"""
        available_predators = [s for s in self.species 
                             if s.species_type == SpeciesType.ANIMAL 
                             and s.id not in self.has_eaten]
        if not available_predators:
            return None
        
        return max(available_predators, key=lambda x: self.calories_remaining[x.id])

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
        
        if not self._distribute_feeding(species, available_prey, species.calories_needed):
            if self.debug_mode:
                self.debug_container.write(f"Failed to distribute feeding for {species.name}")
            return False

        self.has_eaten.add(species.id)
        return True

    def _distribute_feeding(self, predator: Species, prey: List[Species], calories_needed: int) -> bool:
        """Distribute feeding across prey"""
        if not prey:
            return False
        
        if self.debug_mode:
            self.debug_container.write(f"\nDistributing feeding for {predator.name}")
            self.debug_container.write(f"Calories needed: {calories_needed}")
        
        # Group prey by available calories
        calories_groups = {}
        for p in prey:
            remaining = self.calories_remaining[p.id]
            if remaining not in calories_groups:
                calories_groups[remaining] = []
            calories_groups[remaining].append(p)
        
        # Take from highest calorie prey first
        max_calories = max(calories_groups.keys())
        max_calorie_prey = calories_groups[max_calories]
        
        if len(max_calorie_prey) > 1:
            # Multiple prey with same calories - distribute evenly
            calories_per_prey = calories_needed / len(max_calorie_prey)
            for p in max_calorie_prey:
                new_calories = self.calories_remaining[p.id] - calories_per_prey
                if new_calories <= 0:  # Check before applying
                    if self.debug_mode:
                        self.debug_container.write(f"Would deplete {p.name} to {new_calories}")
                    return False
                
                self.calories_remaining[p.id] = new_calories
                self.feeding_history.append({
                    "predator": predator.id,
                    "prey": p.id,
                    "calories_consumed": calories_per_prey
                })
                
                if self.debug_mode:
                    self.debug_container.write(
                        f"Took {calories_per_prey} calories from {p.name} "
                        f"({self.calories_remaining[p.id]} remaining)"
                    )
        else:
            # Single prey - take all needed calories
            prey = max_calorie_prey[0]
            new_calories = self.calories_remaining[prey.id] - calories_needed
            if new_calories <= 0:  # Check before applying
                if self.debug_mode:
                    self.debug_container.write(f"Would deplete {prey.name} to {new_calories}")
                return False
                
            self.calories_remaining[prey.id] = new_calories
            self.feeding_history.append({
                "predator": predator.id,
                "prey": prey.id,
                "calories_consumed": calories_needed
            })
            
            if self.debug_mode:
                self.debug_container.write(
                    f"Took {calories_needed} calories from {prey.name} "
                    f"({self.calories_remaining[prey.id]} remaining)"
                )
            
        return True

    def _get_available_prey(self, species: Species) -> List[Species]:
        """Get all available prey for a species, sorted by current calories"""
        available = [s for s in self.species 
                    if s.id in species.prey and self.calories_remaining[s.id] > 0]
        
        return sorted(
            available,
            key=lambda x: self.calories_remaining[x.id],
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