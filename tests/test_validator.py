import unittest
from lib.validator import SolutionValidator
from core.species import Species, SpeciesType, Ecosystem
from lib.ecosystem import FeedingSimulation

class TestSolutionValidator(unittest.TestCase):
    def setUp(self):
        # Create a simple test ecosystem
        self.producer = Species(
            id="P1", name="Producer 1",
            species_type=SpeciesType.PRODUCER,
            calories_provided=100, calories_needed=0,
            bin="A"
        )
        
        self.herbivore = Species(
            id="A1", name="Herbivore 1",
            species_type=SpeciesType.ANIMAL,
            calories_provided=50, calories_needed=30,
            bin="A", food_sources={"P1"}
        )
        
        self.carnivore = Species(
            id="A2", name="Carnivore 1",
            species_type=SpeciesType.ANIMAL,
            calories_provided=80, calories_needed=40,
            bin="A", food_sources={"A1"}
        )
        
        self.producer.eaten_by.add(self.herbivore.id)
        self.herbivore.eaten_by.add(self.carnivore.id)
        
        self.validator = SolutionValidator()

    def test_valid_solution(self):
        solution = [self.producer, self.herbivore, self.carnivore]
        is_valid, errors = self.validator.validate_solution(
            Ecosystem(solution), solution
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_invalid_counts(self):
        # Test with too few producers
        solution = [self.herbivore, self.carnivore]
        is_valid, errors = self.validator.validate_solution(
            Ecosystem(solution), solution
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("producer" in error for error in errors))

    def test_caloric_depletion(self):
        # Create scenario where herbivore needs more calories than producer has
        self.herbivore.calories_needed = 150
        solution = [self.producer, self.herbivore, self.carnivore]
        is_valid, errors = self.validator.validate_solution(
            Ecosystem(solution), solution
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("depleted" in error for error in errors))

    def test_bin_compatibility(self):
        # Create species in different bins
        self.carnivore.bin = "B"
        solution = [self.producer, self.herbivore, self.carnivore]
        is_valid, errors = self.validator.validate_solution(
            Ecosystem(solution), solution
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("bin" in error for error in errors))