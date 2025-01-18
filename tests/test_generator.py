import unittest
from lib.generator import ScenarioGenerator, SolutionGenerator
from core.species import Species, SpeciesType, Ecosystem
from lib.constants import BINS, PRODUCERS_PER_BIN, ANIMALS_PER_BIN

class TestScenarioGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ScenarioGenerator()

    def test_scenario_generation(self):
        ecosystem = self.generator.generate_scenario()
        
        # Test basic counts
        self.assertEqual(len(ecosystem.get_producers()), PRODUCERS_PER_BIN * len(BINS))
        self.assertEqual(len(ecosystem.get_animals()), ANIMALS_PER_BIN * len(BINS))
        
        # Test bin distribution
        for bin_id in BINS:
            bin_species = ecosystem.get_species_by_bin(bin_id)
            producers = [s for s in bin_species if s.species_type == SpeciesType.PRODUCER]
            animals = [s for s in bin_species if s.species_type == SpeciesType.ANIMAL]
            
            self.assertEqual(len(producers), PRODUCERS_PER_BIN)
            self.assertEqual(len(animals), ANIMALS_PER_BIN)

    def test_relationship_establishment(self):
        ecosystem = self.generator.generate_scenario()
        
        # Test that each animal has at least one food source
        for animal in ecosystem.get_animals():
            self.assertGreater(len(animal.food_sources), 0)
            
        # Test that each producer is eaten by at least one animal
        for producer in ecosystem.get_producers():
            self.assertGreater(len(producer.eaten_by), 0)

class TestSolutionGenerator(unittest.TestCase):
    def setUp(self):
        self.scenario_generator = ScenarioGenerator()
        self.solution_generator = SolutionGenerator()
        self.ecosystem = self.scenario_generator.generate_scenario()

    def test_solution_generation(self):
        solutions = self.solution_generator.generate_all_solutions(self.ecosystem)
        
        for solution in solutions:
            # Test solution composition
            producers = [s for s in solution if s.species_type == SpeciesType.PRODUCER]
            animals = [s for s in solution if s.species_type == SpeciesType.ANIMAL]
            
            self.assertEqual(len(producers), 3)
            self.assertEqual(len(animals), 5)
            
            # Test solution validity
            self.assertTrue(all(p in self.ecosystem.species for p in producers))
            self.assertTrue(all(a in self.ecosystem.species for a in animals))

    def test_solution_ranking(self):
        solutions = self.solution_generator.generate_all_solutions(self.ecosystem)
        ranked_solutions = self.solution_generator.rank_solutions(solutions)
        
        # Test ranking order
        self.assertTrue(all(ranked_solutions[i][1] >= ranked_solutions[i+1][1] 
                          for i in range(len(ranked_solutions)-1)))