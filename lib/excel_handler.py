# utils/excel_handler.py

import pandas as pd
import numpy as np
from typing import List, Dict
from pathlib import Path
from ..core.species import Species, SpeciesType, Ecosystem

class ExcelHandler:
    # Template structure
    REQUIRED_SHEETS = ['Species', 'Relationships']
    SPECIES_COLUMNS = [
        'id', 'name', 'type', 'calories_provided', 
        'calories_needed', 'bin'
    ]
    RELATIONSHIP_COLUMNS = ['predator_id', 'prey_id']

    @staticmethod
    def create_template(file_path: str):
        """Create an empty template Excel file"""
        with pd.ExcelWriter(file_path) as writer:
            # Species sheet
            species_df = pd.DataFrame(columns=ExcelHandler.SPECIES_COLUMNS)
            species_df.to_excel(writer, sheet_name='Species', index=False)
            
            # Relationships sheet
            relationships_df = pd.DataFrame(columns=ExcelHandler.RELATIONSHIP_COLUMNS)
            relationships_df.to_excel(writer, sheet_name='Relationships', index=False)
            
            # Add validation rules
            workbook = writer.book
            worksheet = writer.sheets['Species']
            
            # Add type dropdown
            type_validation = workbook.add_format({
                'validation': {
                    'type': 'list',
                    'source': ['producer', 'animal']
                }
            })
            worksheet.data_validation('C2:C1048576', type_validation)
            
            # Add bin dropdown
            bin_validation = workbook.add_format({
                'validation': {
                    'type': 'list',
                    'source': ['A', 'B', 'C']
                }
            })
            worksheet.data_validation('F2:F1048576', bin_validation)

    @staticmethod
    def validate_excel_format(file_path: str) -> tuple[bool, List[str]]:
        """Validate if Excel file matches required format"""
        errors = []
        try:
            xlsx = pd.ExcelFile(file_path)
            
            # Check required sheets
            missing_sheets = set(ExcelHandler.REQUIRED_SHEETS) - set(xlsx.sheet_names)
            if missing_sheets:
                errors.append(f"Missing sheets: {missing_sheets}")
                return False, errors
            
            # Check Species sheet
            species_df = pd.read_excel(xlsx, 'Species')
            missing_cols = set(ExcelHandler.SPECIES_COLUMNS) - set(species_df.columns)
            if missing_cols:
                errors.append(f"Missing columns in Species sheet: {missing_cols}")
            
            # Check Relationships sheet
            rel_df = pd.read_excel(xlsx, 'Relationships')
            missing_cols = set(ExcelHandler.RELATIONSHIP_COLUMNS) - set(rel_df.columns)
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