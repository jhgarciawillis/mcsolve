import pandas as pd
from typing import List, Dict, Tuple
from pathlib import Path
from species import Species, SpeciesType, Ecosystem
from constants import (
    BASE_SPECIES_COLUMNS,
    MIN_CALORIES,
    MAX_CALORIES,
    CALORIE_STEP,
    BINS,
    PRODUCERS_PER_BIN,
    ANIMALS_PER_BIN
)
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

class ExcelHandler:
    @staticmethod
    def _get_predator_prey_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Get all predator and prey columns from dataframe"""
        predator_cols = [col for col in df.columns if col.startswith('predator_')]
        prey_cols = [col for col in df.columns if col.startswith('prey_')]
        return predator_cols, prey_cols

    @staticmethod
    def create_template(file_path: str, all_bins: bool = True):
        """Create an empty template Excel file"""
        if all_bins:
            bins = BINS
        else:
            bins = ['A']  # Default to single bin
        
        # Create a workbook and select the active worksheet
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = 'Species'

        # Create headers
        headers = ['id', 'name', 'type', 'calories_provided', 'calories_needed', 'bin']
        worksheet.append(headers)

        # Add data
        for bin_id in bins:
            # Add producers
            for i in range(PRODUCERS_PER_BIN):
                worksheet.append([
                    f'P_{bin_id}_{i+1}', 
                    f'Producer {bin_id}{i+1}', 
                    'producer', 
                    0, 
                    0, 
                    bin_id
                ])
            
            # Add animals
            for i in range(ANIMALS_PER_BIN):
                worksheet.append([
                    f'A_{bin_id}_{i+1}', 
                    f'Animal {bin_id}{i+1}', 
                    'animal', 
                    0, 
                    0, 
                    bin_id
                ])

        # Add type validation
        type_validation = DataValidation(type="list", formula1='"producer,animal"', allow_blank=False)
        type_validation.add_sqref(f'C2:C{len(worksheet["A"])+1}')
        worksheet.add_data_validation(type_validation)

        # Add bin validation
        bin_validation = DataValidation(type="list", formula1=f'"{",".join(bins)}"', allow_blank=False)
        bin_validation.add_sqref(f'F2:F{len(worksheet["A"])+1}')
        worksheet.add_data_validation(bin_validation)

        # Save the workbook
        workbook.save(file_path)

    @staticmethod
    def validate_excel_format(file_path: str) -> Tuple[bool, List[str]]:
        """Validate if Excel file matches required format"""
        errors = []
        try:
            df = pd.read_excel(file_path)
            
            # Check required columns
            missing_cols = set(BASE_SPECIES_COLUMNS) - set(df.columns)
            if missing_cols:
                errors.append(f"Missing columns: {missing_cols}")
            
            # Validate data types
            try:
                df['calories_provided'] = df['calories_provided'].astype(int)
                df['calories_needed'] = df['calories_needed'].astype(int)
                
                # Validate calorie ranges
                invalid_calories = df[
                    (df['calories_provided'] % CALORIE_STEP != 0) |
                    ((df['calories_provided'] != 0) & 
                     ((df['calories_provided'] < MIN_CALORIES) | 
                      (df['calories_provided'] > MAX_CALORIES)))
                ]
                if not invalid_calories.empty:
                    errors.append("Invalid calorie values found")
                
            except ValueError:
                errors.append("Calories must be integer values")
            
            # Validate types
            invalid_types = df[~df['type'].isin(['producer', 'animal'])]
            if not invalid_types.empty:
                errors.append("Invalid species types found")
            
            # Validate bins
            invalid_bins = df[~df['bin'].isin(BINS)]
            if not invalid_bins.empty:
                errors.append("Invalid bin values found")
            
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
        
        df = pd.read_excel(file_path)
        predator_cols, prey_cols = ExcelHandler._get_predator_prey_columns(df)
        species_list = []
        
        for _, row in df.iterrows():
            # Get all non-empty predators and prey
            predators = [
                str(row[col]) for col in predator_cols
                if pd.notna(row[col])
            ]
            
            prey = [
                str(row[col]) for col in prey_cols
                if pd.notna(row[col])
            ]
            
            species = Species(
                id=str(row['id']),
                name=str(row['name']),
                species_type=SpeciesType(row['type']),
                calories_provided=int(row['calories_provided']),
                calories_needed=int(row['calories_needed']),
                bin=str(row['bin']),
                predators=predators,
                prey=prey
            )
            species_list.append(species)
        
        return Ecosystem(species_list)

    @staticmethod
    def write_scenario(ecosystem: Ecosystem, file_path: str):
        """Write ecosystem to Excel file"""
        data = []
        
        for species in ecosystem.species:
            row = {
                'id': species.id,
                'name': species.name,
                'type': species.species_type.value,
                'calories_provided': species.calories_provided,
                'calories_needed': species.calories_needed,
                'bin': species.bin
            }
            
            # Add predator columns
            for i, pred in enumerate(species.predators, 1):
                row[f'predator_{i}'] = pred
                
            # Add prey columns
            for i, prey in enumerate(species.prey, 1):
                row[f'prey_{i}'] = prey
            
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, sheet_name='Species')

    @staticmethod
    def write_solution(solution: List[Species], feeding_history: List[Dict], file_path: str):
        """Write solution and feeding history to Excel file"""
        # Create Species data
        species_data = []
        
        for species in solution:
            row = {
                'id': species.id,
                'name': species.name,
                'type': species.species_type.value,
                'calories_provided': species.calories_provided,
                'calories_needed': species.calories_needed,
                'bin': species.bin
            }
            
            # Add predator columns
            for i, pred in enumerate(species.predators, 1):
                row[f'predator_{i}'] = pred
                
            # Add prey columns
            for i, prey in enumerate(species.prey, 1):
                row[f'prey_{i}'] = prey
                
            species_data.append(row)
        
        # Write to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Write species sheet
            pd.DataFrame(species_data).to_excel(writer, sheet_name='Species', index=False)
            
            # Write feeding history if provided
            if feeding_history:
                pd.DataFrame(feeding_history).to_excel(writer, sheet_name='Feeding_History', index=False)