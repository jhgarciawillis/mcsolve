import streamlit as st
import pandas as pd
import os
from species import Species, SpeciesType, Ecosystem
from generator import ScenarioGenerator, SolutionGenerator
from validator import SolutionValidator
from excel_handler import ExcelHandler
from constants import *

st.set_page_config(
    page_title="McKinsey Solve Game Helper",
    page_icon="🌿",
    layout="wide"
)

def create_temp_directory():
    if not os.path.exists("temp"):
        os.makedirs("temp")

def main():
    create_temp_directory()
    
    st.title("McKinsey Solve Game Helper")
    
    menu = ["Generate Scenario", "Find Solutions", "Check Solution"]
    choice = st.sidebar.selectbox("Select Mode", menu)
    
    if choice == "Generate Scenario":
        generate_scenario_page()
    elif choice == "Find Solutions":
        find_solutions_page()
    else:
        check_solution_page()

def generate_scenario_page():
    st.header("Generate New Scenario")
    
    if st.button("Generate New Scenario"):
        with st.spinner("Generating scenario..."):
            generator = ScenarioGenerator()
            ecosystem = generator.generate_scenario()
            
            # Save to temporary file
            temp_file = "temp/scenario.xlsx"
            ExcelHandler.write_scenario(ecosystem, temp_file)
            
            # Provide download button
            with open(temp_file, "rb") as file:
                st.download_button(
                    label="Download Scenario",
                    data=file,
                    file_name="mckinsey_scenario.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

def find_solutions_page():
    st.header("Find Solutions")
    
    # Add debug logging checkbox
    debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download Empty Template"):
            temp_file = "temp/template.xlsx"
            ExcelHandler.create_template(temp_file)
            with open(temp_file, "rb") as file:
                st.download_button(
                    label="Download Template",
                    data=file,
                    file_name="mckinsey_template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        uploaded_file = st.file_uploader("Upload Scenario", type="xlsx")
        
    if uploaded_file is not None:
        st.write("Processing uploaded file...")
        
        # Save uploaded file temporarily
        temp_path = "temp/uploaded_scenario.xlsx"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Validate format
        is_valid, errors = ExcelHandler.validate_excel_format(temp_path)
        if not is_valid:
            st.error("Invalid Excel format:")
            for error in errors:
                st.write(f"- {error}")
            return
        
        try:
            if debug_mode:
                st.write("Reading scenario from Excel...")
            ecosystem = ExcelHandler.read_scenario(temp_path)
            
            if debug_mode:
                st.write(f"Found {len(ecosystem.species)} species in scenario")
                st.write(f"Producers: {len(ecosystem.get_producers())}")
                st.write(f"Animals: {len(ecosystem.get_animals())}")
            
            if st.button("Generate Solutions"):
                debug_container = st.empty()
                
                with st.spinner("Generating solutions..."):
                    if debug_mode:
                        solutions = SolutionGenerator.generate_all_solutions(ecosystem, 
                                                                          debug_container=debug_container,
                                                                          debug_mode=True)
                        ranked_solutions = SolutionGenerator.rank_solutions(solutions, 
                                                                         debug_container=debug_container,
                                                                         debug_mode=True)
                    else:
                        solutions = SolutionGenerator.generate_all_solutions(ecosystem)
                        ranked_solutions = SolutionGenerator.rank_solutions(solutions)
                    
                    st.write(f"Found {len(ranked_solutions)} valid solutions")
                    
                    for i, (solution, score) in enumerate(ranked_solutions[:10]):
                        with st.expander(f"Solution {i+1} (Score: {score:.2f})"):
                            if debug_mode:
                                st.write("Solution Details:")
                                st.write(f"Producers: {len([s for s in solution if s.species_type == SpeciesType.PRODUCER])}")
                                st.write(f"Animals: {len([s for s in solution if s.species_type == SpeciesType.ANIMAL])}")
                            
                            df = pd.DataFrame([{
                                'ID': s.id,
                                'Name': s.name,
                                'Type': s.species_type.value,
                                'Calories Provided': s.calories_provided,
                                'Calories Needed': s.calories_needed,
                                'Bin': s.bin,
                                'Predators': ', '.join(s.predators),
                                'Prey': ', '.join(s.prey)
                            } for s in solution])
                            st.dataframe(df)
                            
                            if debug_mode:
                                # Display feeding relationships
                                st.write("Feeding Relationships:")
                                for species in solution:
                                    if species.species_type == SpeciesType.ANIMAL:
                                        st.write(f"{species.name} eats: {', '.join(species.prey)}")
                            
                            # Add solution download option
                            temp_solution_file = f"temp/solution_{i+1}.xlsx"
                            ExcelHandler.write_solution(solution, [], temp_solution_file)
                            with open(temp_solution_file, "rb") as file:
                                st.download_button(
                                    label=f"Download Solution {i+1}",
                                    data=file,
                                    file_name=f"solution_{i+1}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"download_solution_{i}"
                                )
                            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            if debug_mode:
                st.exception(e)

def check_solution_page():
    st.header("Check Solution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_scenario = st.file_uploader("Upload Scenario", type="xlsx", key="scenario")
    
    with col2:
        uploaded_solution = st.file_uploader("Upload Solution", type="xlsx", key="solution")
    
    if uploaded_scenario is not None and uploaded_solution is not None:
        # Save uploaded files temporarily
        scenario_path = "temp/check_scenario.xlsx"
        solution_path = "temp/check_solution.xlsx"
        
        with open(scenario_path, "wb") as f:
            f.write(uploaded_scenario.getvalue())
        with open(solution_path, "wb") as f:
            f.write(uploaded_solution.getvalue())
        
        try:
            ecosystem = ExcelHandler.read_scenario(scenario_path)
            solution = ExcelHandler.read_scenario(solution_path)
            
            if st.button("Validate Solution"):
                with st.spinner("Validating solution..."):
                    validator = SolutionValidator()
                    is_valid, errors = validator.validate_solution(ecosystem, solution.species)
                    
                    if is_valid:
                        st.success("Valid solution!")
                        simulation = FeedingSimulation(solution.species)
                        success, feeding_history = simulation.simulate_feeding_round()
                        
                        st.subheader("Feeding History")
                        df = pd.DataFrame(feeding_history)
                        st.dataframe(df)
                    else:
                        st.error("Invalid solution")
                        for error in errors:
                            st.write(f"- {error}")
                            
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")

if __name__ == "__main__":
    main()