import pandas as pd
from typing import List, Dict, Set
from pathlib import Path
from ..core.species import Species, SpeciesType, Ecosystem
from .constants import REQUIRED_COLUMNS

class ExcelHandler:
    @staticmethod
    def read_scenario(file_path: str) -> Ecosystem:
        """Read scenario from Excel file and create Ecosystem object"""
        try:
            df = pd.read_excel(file_path)
            
            # Validate columns
            missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            species_list = []
            for _, row in df.iterrows():
                # Convert eaten_by and food_sources from string to set
                eaten_by = set(row['eaten_by'].split(',')) if pd.notna(row['eaten_by']) else set()
                food_sources = set(row['food_sources'].split(',')) if pd.notna(row['food_sources']) else set()
                
                species = Species(
                    id=row['id'],
                    name=row['name'],
                    species_type=SpeciesType(row['type']),
                    calories_provided=int(row['calories_provided']),
                    calories_needed=int(row['calories_needed']),
                    bin=row['bin'],
                    eaten_by=eaten_by,
                    food_sources=food_sources
                )
                species_list.append(species)
                
            return Ecosystem(species_list)
            
        except Exception as e:
            raise Exception(f"Error reading scenario file: {str(e)}")

    @staticmethod
    def write_scenario(ecosystem: Ecosystem, file_path: str):
        """Write ecosystem to Excel file"""
        data = []
        for species in ecosystem.species:
            data.append({
                'id': species.id,
                'name': species.name,
                'type': species.species_type.value,
                'calories_provided': species.calories_provided,
                'calories_needed': species.calories_needed,
                'bin': species.bin,
                'eaten_by': ','.join(species.eaten_by),
                'food_sources': ','.join(species.food_sources)
            })
            
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)

    @staticmethod
    def write_solution(solution: List[Species], feeding_history: List[Dict], file_path: str):
        """Write solution and feeding history to Excel file"""
        # Create solution sheet
        solution_data = [{
            'id': s.id,
            'name': s.name,
            'type': s.species_type.value,
            'calories_provided': s.calories_provided,
            'calories_needed': s.calories_needed,
            'bin': s.bin
        } for s in solution]
        
        # Create feeding history sheet
        history_data = [{
            'step': i+1,
            'predator': h['predator'],
            'prey': h['prey'],
            'calories_consumed': h['calories_consumed']
        } for i, h in enumerate(feeding_history)]
        
        with pd.ExcelWriter(file_path) as writer:
            pd.DataFrame(solution_data).to_excel(writer, sheet_name='Solution', index=False)
            pd.DataFrame(history_data).to_excel(writer, sheet_name='Feeding_History', index=False)