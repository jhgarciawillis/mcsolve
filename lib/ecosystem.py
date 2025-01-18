from typing import List, Dict, Set, Tuple
from .species import Species, SpeciesType, Ecosystem
from dataclasses import dataclass

@dataclass
class FeedingSimulation:
    def __init__(self, species: List[Species]):
        self.species = sorted(species, key=lambda x: x.calories_provided, reverse=True)
        self.calories_remaining = {s.id: s.calories_provided for s in species}
        self.has_eaten = set()
        self.feeding_history = []

    def simulate_feeding_round(self) -> Tuple[bool, List[dict]]:
        """
        Simulates one complete feeding round for all species
        Returns: (success, feeding_history)
        """
        for species in self.species:
            if species.species_type == SpeciesType.PRODUCER:
                continue
                
            if not self._feed_species(species):
                return False, self.feeding_history
                
        return True, self.feeding_history

    def _feed_species(self, species: Species) -> bool:
        if species.id in self.has_eaten:
            return True
            
        # Get available food sources sorted by calories
        available_food = self._get_available_food_sources(species)
        if not available_food:
            return False

        # Calculate calories needed from each source
        calories_needed = species.calories_needed
        if not self._distribute_feeding(species, available_food, calories_needed):
            return False

        self.has_eaten.add(species.id)
        return True

    def _get_available_food_sources(self, species: Species) -> List[Species]:
        return sorted(
            [s for s in self.species if s.id in species.food_sources and self.calories_remaining[s.id] > 0],
            key=lambda x: self.calories_remaining[x.id],
            reverse=True
        )

    def _distribute_feeding(self, predator: Species, prey: List[Species], calories_needed: int) -> bool:
        if not prey:
            return False
            
        # Handle equal calories case
        if len(prey) > 1 and self.calories_remaining[prey[0].id] == self.calories_remaining[prey[1].id]:
            calories_per_prey = calories_needed / len(prey)
            for p in prey:
                if self.calories_remaining[p.id] < calories_per_prey:
                    return False
                self.calories_remaining[p.id] -= calories_per_prey
                self.feeding_history.append({
                    "predator": predator.id,
                    "prey": p.id,
                    "calories_consumed": calories_per_prey
                })
        else:
            # Take from highest calorie source first
            if self.calories_remaining[prey[0].id] < calories_needed:
                return False
            self.calories_remaining[prey[0].id] -= calories_needed
            self.feeding_history.append({
                "predator": predator.id,
                "prey": prey[0].id,
                "calories_consumed": calories_needed
            })
            
        return True