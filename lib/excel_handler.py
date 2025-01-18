import pandas as pd
from typing import List, Dict, Tuple
from pathlib import Path
from .species import Species, SpeciesType, Ecosystem
from .constants import REQUIRED_SHEETS, SPECIES_COLUMNS, RELATIONSHIP_COLUMNS

class ExcelHandler:
    @staticmethod
    def create_template(file_path: str):
        """Create an empty template Excel file"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Species sheet
            species_df = pd.DataFrame(columns=SPECIES_COLUMNS)
            species_df.to_excel(writer, sheet_name='Species', index=False)
            
            # Relationships sheet
            relationships_df = pd.DataFrame(columns=RELATIONSHIP_COLUMNS)
            relationships_df.to_excel(writer, sheet_name='Relationships', index=False)

    @staticmethod
    def validate_excel_format(file_path: str) -> Tuple[bool, List[str]]:
        """Validate if Excel file matches required format"""
        errors = []
        try:
            xlsx = pd.ExcelFile(file_path)
            
            # Check required sheets
            missing_sheets = set(REQUIRED_SHEETS) - set(xlsx.sheet_names)
            if missing_sheets:
                errors.append(f"Missing sheets: {missing_sheets}")
                return False, errors
            
            # Check Species sheet
            species_df = pd.read_excel(xlsx, 'Species')
            missing_cols = set(SPECIES_COLUMNS) - set(species_df.columns)
            if missing_cols:
                errors.append(f"Missing columns in Species sheet: {missing_cols}")
            
            # Check Relationships sheet
            rel_df = pd.read_excel(xlsx, 'Relationships')
            missing_cols = set(RELATIONSHIP_COLUMNS) - set(rel_df.columns)
            if missing_cols:
                errors.append(f"Missing columns in Relationships sheet: {missing_cols}")
            
            # Validate data types
            try:
                species_df['calories_provided'] = species_df['calories_provided'].astype(int)
                species_df['calories_needed'] = species_df['calories_needed'].astype(int)
            except ValueError:
                errors.append("Calories must be integer values")
            
            # Validate relationships reference valid species
            species_ids = set(species_df['id'])
            invalid_predators = set(rel_df['predator_id']) - species_ids
            invalid_prey = set(rel_df['prey_id']) - species_ids
            
            if invalid_predators:
                errors.append(f"Invalid predator IDs: {invalid_predators}")
            if invalid_prey:
                errors.append(f"Invalid prey IDs: {invalid_prey}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Error reading Excel file: {str(e)}")
            return False, errors

    @staticmethod
    def read_scenario(file_path: str) -> Ecosystem:
        """Read scenario from Excel file with validation"""
        is_valid, errors = ExcelHandler.validate_excel_format(file_path)
        if not is_valid:
            raise ValueError(f"Invalid Excel format: {'; '.join(errors)}")
        
        # Read both sheets
        species_df = pd.read_excel(file_path, 'Species')
        relationships_df = pd.read_excel(file_path, 'Relationships')
        
        # Build relationships dictionary
        relationships = {}
        for _, row in relationships_df.iterrows():
            predator_id = row['predator_id']
            prey_id = row['prey_id']
            if predator_id not in relationships:
                relationships[predator_id] = {'food_sources': set(), 'eaten_by': set()}
            if prey_id not in relationships:
                relationships[prey_id] = {'food_sources': set(), 'eaten_by': set()}
            
            relationships[predator_id]['food_sources'].add(prey_id)
            relationships[prey_id]['eaten_by'].add(predator_id)
        
        # Create species objects
        species_list = []
        for _, row in species_df.iterrows():
            species_id = row['id']
            rels = relationships.get(species_id, {'food_sources': set(), 'eaten_by': set()})
            
            species = Species(
                id=species_id,
                name=row['name'],
                species_type=SpeciesType(row['type']),
                calories_provided=int(row['calories_provided']),
                calories_needed=int(row['calories_needed']),
                bin=row['bin'],
                eaten_by=rels['eaten_by'],
                food_sources=rels['food_sources']
            )
            species_list.append(species)
        
        return Ecosystem(species_list)

    @staticmethod
    def write_scenario(ecosystem: Ecosystem, file_path: str):
        """Write ecosystem to Excel file"""
        # Create Species data
        species_data = []
        relationships_data = []
        
        for species in ecosystem.species:
            species_data.append({
                'id': species.id,
                'name': species.name,
                'type': species.species_type.value,
                'calories_provided': species.calories_provided,
                'calories_needed': species.calories_needed,
                'bin': species.bin
            })
            
            # Create relationship data
            for food_source in species.food_sources:
                relationships_data.append({
                    'predator_id': species.id,
                    'prey_id': food_source
                })
        
        # Write to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            pd.DataFrame(species_data).to_excel(writer, sheet_name='Species', index=False)
            pd.DataFrame(relationships_data).to_excel(writer, sheet_name='Relationships', index=False)

    @staticmethod
    def write_solution(solution: List[Species], feeding_history: List[Dict], file_path: str):
        """Write solution and feeding history to Excel file"""
        species_data = [{
            'id': s.id,
            'name': s.name,
            'type': s.species_type.value,
            'calories_provided': s.calories_provided,
            'calories_needed': s.calories_needed,
            'bin': s.bin
        } for s in solution]
        
        relationships_data = []
        for species in solution:
            for food_source in species.food_sources:
                relationships_data.append({
                    'predator_id': species.id,
                    'prey_id': food_source
                })
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            pd.DataFrame(species_data).to_excel(writer, sheet_name='Species', index=False)
            pd.DataFrame(relationships_data).to_excel(writer, sheet_name='Relationships', index=False)
            if feeding_history:
                pd.DataFrame(feeding_history).to_excel(writer, sheet_name='Feeding_History', index=False)