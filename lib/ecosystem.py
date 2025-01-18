from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from .species import Species, SpeciesType, Ecosystem
from .constants import BINS

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
        """
        Attempt to feed a single species
        Returns True if successful, False if species cannot obtain required calories
        """
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
        """Get all available food sources for a species, sorted by remaining calories"""
        return sorted(
            [s for s in self.species 
             if s.id in species.food_sources and self.calories_remaining[s.id] > 0],
            key=lambda x: self.calories_remaining[x.id],
            reverse=True
        )

    def _distribute_feeding(self, predator: Species, prey: List[Species], calories_needed: int) -> bool:
        """
        Distribute feeding across multiple prey
        Returns True if predator obtains all needed calories, False otherwise
        """
        if not prey:
            return False
        
        # Calculate total available calories
        total_available = sum(self.calories_remaining[p.id] for p in prey)
        if total_available < calories_needed:
            return False
        
        calories_still_needed = calories_needed
        
        # Group prey by available calories
        calories_groups = {}
        for p in prey:
            remaining = self.calories_remaining[p.id]
            if remaining not in calories_groups:
                calories_groups[remaining] = []
            calories_groups[remaining].append(p)
        
        # Handle equal distribution for same-calorie groups
        for calories, group in sorted(calories_groups.items(), reverse=True):
            if len(group) > 1:
                calories_per_prey = min(calories, calories_still_needed / len(group))
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
            else:
                # Single prey in this calorie group
                p = group[0]
                calories_to_take = min(self.calories_remaining[p.id], calories_still_needed)
                self.calories_remaining[p.id] -= calories_to_take
                calories_still_needed -= calories_to_take
                
                self.feeding_history.append({
                    "predator": predator.id,
                    "prey": p.id,
                    "calories_consumed": calories_to_take
                })
            
            if calories_still_needed <= 0:
                break
        
        return calories_still_needed <= 0

    def get_remaining_calories(self) -> Dict[str, int]:
        """Get remaining calories for all species"""
        return self.calories_remaining

    def get_feeding_sequence(self) -> List[Dict]:
        """Get the complete feeding history"""
        return self.feeding_history

    def validate_ecosystem_stability(self) -> Tuple[bool, List[str]]:
        """
        Validate if the ecosystem is stable after feeding
        Returns: (is_stable, list_of_issues)
        """
        issues = []
        
        # Check if all animals got their required calories
        for species in self.species:
            if species.species_type == SpeciesType.ANIMAL:
                if species.id not in self.has_eaten:
                    issues.append(f"{species.name} could not obtain required calories")
        
        # Check if any species was completely depleted
        for species_id, calories in self.calories_remaining.items():
            if calories <= 0:
                species = next(s for s in self.species if s.id == species_id)
                issues.append(f"{species.name} was completely depleted")
        
        return len(issues) == 0, issues