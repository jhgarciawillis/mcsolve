from dataclasses import dataclass
from typing import List, Set, Optional
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
    eaten_by: Set[str] = None  # Set of species IDs
    food_sources: Set[str] = None  # Set of species IDs
    
    def __post_init__(self):
        self.eaten_by = set() if self.eaten_by is None else self.eaten_by
        self.food_sources = set() if self.food_sources is None else self.food_sources
        if self.species_type == SpeciesType.PRODUCER:
            self.calories_needed = 0
            self.food_sources = set()

    def can_eat(self, other_species: 'Species') -> bool:
        return other_species.id in self.food_sources

    def can_be_eaten_by(self, other_species: 'Species') -> bool:
        return other_species.id in self.eaten_by

    def __hash__(self):
        return hash(self.id)

@dataclass
class Ecosystem:
    species: List[Species]
    
    def get_producers(self) -> List[Species]:
        return [s for s in self.species if s.species_type == SpeciesType.PRODUCER]
    
    def get_animals(self) -> List[Species]:
        return [s for s in self.species if s.species_type == SpeciesType.ANIMAL]
    
    def get_species_by_bin(self, bin_id: str) -> List[Species]:
        return [s for s in self.species if s.bin == bin_id]

    def validate_basic_constraints(self) -> bool:
        """
        Validates basic ecosystem constraints:
        - 3 producers per bin
        - 10 animals per bin
        """
        bins = set(s.bin for s in self.species)
        for bin_id in bins:
            bin_species = self.get_species_by_bin(bin_id)
            producers = [s for s in bin_species if s.species_type == SpeciesType.PRODUCER]
            animals = [s for s in bin_species if s.species_type == SpeciesType.ANIMAL]
            
            if len(producers) != 3 or len(animals) != 10:
                return False
        return True