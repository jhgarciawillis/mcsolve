from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
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
    predators: List[str] = field(default_factory=list)  # List of predator IDs
    prey: List[str] = field(default_factory=list)      # List of prey IDs

    def __post_init__(self):
        # Initialize empty lists if None
        self.predators = [] if self.predators is None else self.predators
        self.prey = [] if self.prey is None else self.prey

        # Enforce producer rules
        if self.species_type == SpeciesType.PRODUCER:
            self.calories_needed = 0
            self.prey = []  # Producers have no prey

    def create_copy(self) -> 'Species':
        """Create a deep copy of the species with new relationship lists"""
        return Species(
            id=self.id,
            name=self.name,
            species_type=self.species_type,
            calories_provided=self.calories_provided,
            calories_needed=self.calories_needed,
            bin=self.bin,
            predators=self.predators.copy(),
            prey=self.prey.copy()
        )

    def add_predator(self, predator_id: str) -> bool:
        """Add a predator"""
        if predator_id not in self.predators:
            self.predators.append(predator_id)
            return True
        return False

    def add_prey(self, prey_id: str) -> bool:
        """Add a prey if not a producer"""
        if self.species_type == SpeciesType.PRODUCER:
            return False
        if prey_id not in self.prey:
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
            
    def filter_relationships_by_bin(self, species_dict: Dict[str, 'Species']):
        """Filter relationships to only include species from the same bin"""
        self.predators = [pred_id for pred_id in self.predators 
                         if pred_id in species_dict and
                         species_dict[pred_id].bin == self.bin]
        
        self.prey = [prey_id for prey_id in self.prey
                    if prey_id in species_dict and
                    species_dict[prey_id].bin == self.bin]

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Species):
            return False
        return self.id == other.id

    def __str__(self):
        return f"{self.name} ({self.species_type.value}) in Bin {self.bin}"

    def __repr__(self):
        return f"Species(id='{self.id}', name='{self.name}', type={self.species_type.value})"

class Ecosystem:
    def __init__(self, species: List[Species]):
        self.species = species
        self.species_dict = {s.id: s for s in species}
        self._validate_ecosystem()

    def _validate_ecosystem(self):
        """Validate ecosystem consistency"""
        solution_ids = {s.id for s in self.species}
        
        for species in self.species:
            # Validate predator references
            invalid_predators = [pred_id for pred_id in species.predators 
                               if pred_id not in solution_ids]
            if invalid_predators:
                raise ValueError(f"Invalid predator reference {invalid_predators[0]} in {species.name}")
            
            # Validate prey references
            invalid_prey = [prey_id for prey_id in species.prey 
                          if prey_id not in solution_ids]
            if invalid_prey:
                raise ValueError(f"Invalid prey reference {invalid_prey[0]} in {species.name}")

    def get_producers(self) -> List[Species]:
        """Get all producers in the ecosystem"""
        return [s for s in self.species if s.species_type == SpeciesType.PRODUCER]

    def get_animals(self) -> List[Species]:
        """Get all animals in the ecosystem"""
        return [s for s in self.species if s.species_type == SpeciesType.ANIMAL]

    def get_species_by_bin(self, bin_id: str) -> List[Species]:
        """Get all species in a specific bin"""
        return [s for s in self.species if s.bin == bin_id]

    def get_bin_producers(self, bin_id: str) -> List[Species]:
        """Get producers from a specific bin"""
        return [s for s in self.species 
                if s.species_type == SpeciesType.PRODUCER and s.bin == bin_id]

    def get_bin_animals(self, bin_id: str) -> List[Species]:
        """Get animals from a specific bin"""
        return [s for s in self.species 
                if s.species_type == SpeciesType.ANIMAL and s.bin == bin_id]

    def get_bin_calories(self, bin_id: str) -> int:
        """Get total producer calories in a bin"""
        return sum(s.calories_provided for s in self.get_bin_producers(bin_id))

    def get_species_by_id(self, species_id: str) -> Optional[Species]:
        """Get a species by its ID"""
        return self.species_dict.get(species_id)

    def add_species(self, species: Species):
        """Add a new species to the ecosystem"""
        if species.id not in self.species_dict:
            self.species.append(species)
            self.species_dict[species.id] = species

    def remove_species(self, species_id: str):
        """Remove a species and clean up its relationships"""
        if species_id in self.species_dict:
            species = self.species_dict[species_id]
            
            # Remove from all prey's predators lists
            for prey_id in species.prey:
                if prey_id in self.species_dict:
                    self.species_dict[prey_id].remove_predator(species_id)
            
            # Remove from all predators' prey lists
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

    def get_bin_statistics(self, bin_id: str) -> Dict:
        """Get statistics for a specific bin"""
        bin_species = self.get_species_by_bin(bin_id)
        return {
            'total_species': len(bin_species),
            'producers': len([s for s in bin_species if s.species_type == SpeciesType.PRODUCER]),
            'animals': len([s for s in bin_species if s.species_type == SpeciesType.ANIMAL]),
            'total_calories': self.get_bin_calories(bin_id)
        }