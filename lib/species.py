from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from enum import Enum
from .constants import MAX_PREDATORS, MAX_PREY

class SpeciesType(Enum):
    PRODUCER = "producer"
    ANIMAL = "animal"

@dataclass
class Species:
    id: str
    name: str
    species_type: SpeciesType
    calories_provided: int
    calories_needed: int
    bin: str  # A, B, or C
    predators: List[str] = field(default_factory=list)  # List of predator IDs
    prey: List[str] = field(default_factory=list)      # List of prey IDs

    def __post_init__(self):
        # Initialize empty lists if None
        self.predators = [] if self.predators is None else self.predators
        self.prey = [] if self.prey is None else self.prey
        
        # Enforce maximum lengths
        self.predators = self.predators[:MAX_PREDATORS]
        self.prey = self.prey[:MAX_PREY]
        
        # Enforce producer rules
        if self.species_type == SpeciesType.PRODUCER:
            self.calories_needed = 0
            self.prey = []  # Producers have no prey

    def add_predator(self, predator_id: str) -> bool:
        """Add a predator if space available"""
        if len(self.predators) < MAX_PREDATORS and predator_id not in self.predators:
            self.predators.append(predator_id)
            return True
        return False

    def add_prey(self, prey_id: str) -> bool:
        """Add a prey if space available and not a producer"""
        if self.species_type == SpeciesType.PRODUCER:
            return False
        if len(self.prey) < MAX_PREY and prey_id not in self.prey:
            self.prey.append(prey_id)
            return True
        return False

    def remove_predator(self, predator_id: str):
        """Remove a predator"""
        if predator_id in self.predators:
            self.predators.remove(predator_id)

    def remove_prey(self, prey_id: str):
        """Remove a prey"""
        if prey_id in self.prey:
            self.prey.remove(prey_id)

    def can_be_eaten_by(self, predator_id: str) -> bool:
        """Check if this species can be eaten by the predator"""
        return predator_id in self.predators

    def can_eat(self, prey_id: str) -> bool:
        """Check if this species can eat the prey"""
        return prey_id in self.prey

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Species):
            return False
        return self.id == other.id

class Ecosystem:
    def __init__(self, species: List[Species]):
        self.species = species
        self.species_dict = {s.id: s for s in species}

    def get_producers(self) -> List[Species]:
        """Get all producers in the ecosystem"""
        return [s for s in self.species if s.species_type == SpeciesType.PRODUCER]

    def get_animals(self) -> List[Species]:
        """Get all animals in the ecosystem"""
        return [s for s in self.species if s.species_type == SpeciesType.ANIMAL]

    def get_species_by_bin(self, bin_id: str) -> List[Species]:
        """Get all species in a specific bin"""
        return [s for s in self.species if s.bin == bin_id]

    def get_species_by_id(self, species_id: str) -> Optional[Species]:
        """Get a species by its ID"""
        return self.species_dict.get(species_id)

    def validate_relationships(self) -> bool:
        """Validate that all relationship references are valid"""
        all_ids = set(self.species_dict.keys())
        
        for species in self.species:
            # Check predators
            if not set(species.predators).issubset(all_ids):
                return False
            # Check prey
            if not set(species.prey).issubset(all_ids):
                return False
            # Validate producer constraints
            if species.species_type == SpeciesType.PRODUCER:
                if species.calories_needed != 0 or len(species.prey) != 0:
                    return False
            # Validate relationship limits
            if len(species.predators) > MAX_PREDATORS or len(species.prey) > MAX_PREY:
                return False
                    
        return True

    def add_species(self, species: Species):
        """Add a new species to the ecosystem"""
        self.species.append(species)
        self.species_dict[species.id] = species

    def remove_species(self, species_id: str):
        """Remove a species and clean up its relationships"""
        if species_id in self.species_dict:
            species = self.species_dict[species_id]
            
            # Remove this species from all prey's predators lists
            for prey_id in species.prey:
                if prey_id in self.species_dict:
                    self.species_dict[prey_id].remove_predator(species_id)
            
            # Remove this species from all predators' prey lists
            for predator_id in species.predators:
                if predator_id in self.species_dict:
                    self.species_dict[predator_id].remove_prey(species_id)
            
            # Remove from collections
            self.species.remove(species)
            del self.species_dict[species_id]

    def get_species_count_by_type(self) -> Dict[SpeciesType, int]:
        """Get count of species by type"""
        counts = {SpeciesType.PRODUCER: 0, SpeciesType.ANIMAL: 0}
        for species in self.species:
            counts[species.species_type] += 1
        return counts