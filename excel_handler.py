import pandas as pd
from typing import List, Dict, Tuple
from pathlib import Path
from species import Species, SpeciesType, Ecosystem
from constants import (
    SPECIES_COLUMNS,
    MIN_CALORIES,
    MAX_CALORIES,
    CALORIE_STEP,
    MAX_PREDATORS,
    MAX_PREY,
    BINS
)

class ExcelHandler:
    @staticmethod
    def create_template(file_path: str):
        """Create an empty template Excel file"""
        df = pd.DataFrame(columns=SPECIES_COLUMNS)
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Species', index=False)
            
            # Add data validation
            workbook = writer.book
            worksheet = writer.sheets['Species']
            
            # Add type dropdown
            type_validation = {
                'type': 'list',
                'source': ['producer', 'animal']
            }
            worksheet.data_validation('C2:C1048576', type_validation)
            
            # Add bin dropdown
            bin_validation = {
                'type': 'list',
                'source': ['A', 'B', 'C']
            }
            worksheet.data_validation('F2:F1048576', bin_validation)

    @staticmethod
    def validate_excel_format(file_path: str) -> Tuple[bool, List[str]]:
        """Validate if Excel file matches required format"""
        errors = []
        try:
            df = pd.read_excel(file_path)
            
            # Check required columns
            missing_cols = set(SPECIES_COLUMNS) - set(df.columns)
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
            invalid_bins = df[~df['bin'].isin(['A', 'B', 'C'])]
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
        species_list = []
        
        for _, row in df.iterrows():
            # Get predators and prey, filtering out empty values
            predators = [
                str(row[f'predator_{i}']) for i in range(1, MAX_PREDATORS + 1)
                if f'predator_{i}' in row and pd.notna(row[f'predator_{i}'])
            ]
            
            prey = [
                str(row[f'prey_{i}']) for i in range(1, MAX_PREY + 1)
                if f'prey_{i}' in row and pd.notna(row[f'prey_{i}'])
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
            # Pad predators and prey lists to fixed length
            predators = species.predators + [''] * (MAX_PREDATORS - len(species.predators))
            prey = species.prey + [''] * (MAX_PREY - len(species.prey))
            
            row = {
                'id': species.id,
                'name': species.name,
                'type': species.species_type.value,
                'calories_provided': species.calories_provided,
                'calories_needed': species.calories_needed,
                'bin': species.bin
            }
            
            # Add predator columns
            for i, pred in enumerate(predators, 1):
                row[f'predator_{i}'] = pred
                
            # Add prey columns
            for i, pr in enumerate(prey, 1):
                row[f'prey_{i}'] = pr
            
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, sheet_name='Species')

    @staticmethod
    def write_solution(solution: List[Species], feeding_history: List[Dict], file_path: str):
        """Write solution and feeding history to Excel file"""
        # Create Species data
        species_data = []
        
        for species in solution:
            species_data.append({
                'id': species.id,
                'name': species.name,
                'type': species.species_type.value,
                'calories_provided': species.calories_provided,
                'calories_needed': species.calories_needed,
                'bin': species.bin,
                'predator_1': species.predators[0] if len(species.predators) > 0 else '',
                'predator_2': species.predators[1] if len(species.predators) > 1 else '',
                'predator_3': species.predators[2] if len(species.predators) > 2 else '',
                'predator_4': species.predators[3] if len(species.predators) > 3 else '',
                'prey_1': species.prey[0] if len(species.prey) > 0 else '',
                'prey_2': species.prey[1] if len(species.prey) > 1 else '',
                'prey_3': species.prey[2] if len(species.prey) > 2 else '',
                'prey_4': species.prey[3] if len(species.prey) > 3 else ''
            })
        
        # Write to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Write species sheet
            pd.DataFrame(species_data).to_excel(writer, sheet_name='Species', index=False)
            
            # Write feeding history if provided
            if feeding_history:
                pd.DataFrame(feeding_history).to_excel(writer, sheet_name='Feeding_History', index=False)