from dataclasses import dataclass, field
from typing import List, Set, Dict
from enum import Enum

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
    eaten_by: Set[str] = field(default_factory=set)  # Set of species IDs
    food_sources: Set[str] = field(default_factory=set)  # Set of species IDs

    def __post_init__(self):
        # Initialize empty sets if None
        self.eaten_by = set() if self.eaten_by is None else self.eaten_by
        self.food_sources = set() if self.food_sources is None else self.food_sources
        
        # Enforce producer rules
        if self.species_type == SpeciesType.PRODUCER:
            self.calories_needed = 0
            self.food_sources = set()  # Producers have no prey

    def can_eat(self, other_species: 'Species') -> bool:
        """Check if this species can eat another species"""
        return other_species.id in self.food_sources

    def can_be_eaten_by(self, other_species: 'Species') -> bool:
        """Check if this species can be eaten by another species"""
        return other_species.id in self.eaten_by

    def add_food_source(self, other_species: 'Species'):
        """Add a species as a food source"""
        if self.species_type != SpeciesType.PRODUCER:
            self.food_sources.add(other_species.id)
            other_species.eaten_by.add(self.id)

    def remove_food_source(self, other_species: 'Species'):
        """Remove a species from food sources"""
        self.food_sources.discard(other_species.id)
        other_species.eaten_by.discard(self.id)

    def get_all_prey(self, species_dict: Dict[str, 'Species']) -> List['Species']:
        """Get all species this species can eat"""
        return [species_dict[species_id] for species_id in self.food_sources]

    def get_all_predators(self, species_dict: Dict[str, 'Species']) -> List['Species']:
        """Get all species that can eat this species"""
        return [species_dict[species_id] for species_id in self.eaten_by]

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

    def get_species_by_id(self, species_id: str) -> Species:
        """Get a species by its ID"""
        return self.species_dict.get(species_id)

    def get_food_web(self) -> Dict[str, Set[str]]:
        """Get the complete food web as a dictionary of relationships"""
        return {s.id: s.food_sources for s in self.species}

    def validate_relationships(self) -> bool:
        """Validate that all relationship references are valid"""
        all_ids = set(self.species_dict.keys())
        
        for species in self.species:
            # Check food sources
            if not species.food_sources.issubset(all_ids):
                return False
            # Check eaten_by
            if not species.eaten_by.issubset(all_ids):
                return False
            # Validate producer constraints
            if species.species_type == SpeciesType.PRODUCER:
                if species.calories_needed != 0 or len(species.food_sources) != 0:
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
            
            # Remove this species from all food sources' eaten_by sets
            for food_id in species.food_sources:
                if food_id in self.species_dict:
                    self.species_dict[food_id].eaten_by.discard(species_id)
            
            # Remove this species from all predators' food_sources sets
            for predator_id in species.eaten_by:
                if predator_id in self.species_dict:
                    self.species_dict[predator_id].food_sources.discard(species_id)
            
            # Remove from collections
            self.species.remove(species)
            del self.species_dict[species_id]

    def get_species_count_by_type(self) -> Dict[SpeciesType, int]:
        """Get count of species by type"""
        counts = {SpeciesType.PRODUCER: 0, SpeciesType.ANIMAL: 0}
        for species in self.species:
            counts[species.species_type] += 1
        return counts