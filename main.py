import streamlit as st
import pandas as pd
import os
from species import Species, SpeciesType, Ecosystem
from generator import ScenarioGenerator, SolutionGenerator
from validator import SolutionValidator
from ecosystem import FeedingSimulation
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
    
    # Debug mode toggle
    debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)
    
    if choice == "Generate Scenario":
        generate_scenario_page(debug_mode)
    elif choice == "Find Solutions":
        find_solutions_page(debug_mode)
    else:
        check_solution_page(debug_mode)

def generate_scenario_page(debug_mode):
    st.header("Generate New Scenario")
    
    if st.button("Generate New Scenario"):
        with st.spinner("Generating scenario..."):
            generator = ScenarioGenerator()
            ecosystem = generator.generate_scenario()
            
            if debug_mode:
                st.write("Scenario Details:")
                for bin_id in BINS:
                    stats = ecosystem.get_bin_statistics(bin_id)
                    st.write(f"\nBin {bin_id}:")
                    st.write(f"- Total species: {stats['total_species']}")
                    st.write(f"- Producers: {stats['producers']}")
                    st.write(f"- Animals: {stats['animals']}")
                    st.write(f"- Total calories: {stats['total_calories']}")
            
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

def find_solutions_page(debug_mode):
    st.header("Find Solutions")
    
    col1, col2, col3 = st.columns(3)
    
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
        
    with col3:
        selected_bin = st.selectbox("Select Bin", ["All"] + BINS)
        
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
            ecosystem = ExcelHandler.read_scenario(temp_path)
            
            # Display bin analysis
            if debug_mode:
                st.write("\nBin Analysis:")
                ranked_bins = [(bin_id, ecosystem.get_bin_calories(bin_id)) 
                             for bin_id in BINS]
                ranked_bins.sort(key=lambda x: x[1], reverse=True)
                
                for bin_id, calories in ranked_bins:
                    st.write(f"\nBin {bin_id} (Total Producer Calories: {calories}):")
                    stats = ecosystem.get_bin_statistics(bin_id)
                    st.write(f"- Producers: {stats['producers']}")
                    st.write(f"- Animals: {stats['animals']}")
            
            if st.button("Generate Solutions"):
                debug_container = st.empty()
                
                with st.spinner("Generating solutions..."):
                    if selected_bin == "All":
                        solutions = SolutionGenerator.generate_all_solutions(
                            ecosystem, 
                            debug_container if debug_mode else None,
                            debug_mode
                        )
                    else:
                        solutions = SolutionGenerator.generate_bin_solutions(
                            ecosystem,
                            selected_bin,
                            debug_container if debug_mode else None,
                            debug_mode
                        )
                    
                    if solutions:
                        ranked_solutions = SolutionGenerator.rank_solutions(
                            solutions,
                            debug_container if debug_mode else None,
                            debug_mode
                        )
                        
                        st.write(f"Found {len(ranked_solutions)} valid solutions")
                        
                        for i, (solution, score) in enumerate(ranked_solutions[:10]):
                            with st.expander(f"Solution {i+1} (Score: {score:.2f})"):
                                selected_bin = solution[0].bin
                                st.write(f"Selected Bin: {selected_bin}")
                                
                                if debug_mode:
                                    st.write(f"Solution Species IDs: {[s.id for s in solution]}")
                                    st.write("Species Composition:")
                                    st.write(f"- Producers: {len([s for s in solution if s.species_type == SpeciesType.PRODUCER])}")
                                    st.write(f"- Animals: {len([s for s in solution if s.species_type == SpeciesType.ANIMAL])}")
                                
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
                                    st.write("\nFeeding Relationships:")
                                    for species in solution:
                                        if species.species_type == SpeciesType.ANIMAL:
                                            st.write(f"{species.name} eats: {', '.join([next(s.name for s in solution if s.id == prey_id) for prey_id in species.prey])}")
                                
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
                    else:
                        st.warning("No valid solutions found")
                        if debug_mode:
                            st.write("Try analyzing a different bin or checking the relationship constraints.")
                        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            if debug_mode:
                st.exception(e)

def check_solution_page(debug_mode):
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
                    validator = SolutionValidator(st if debug_mode else None, debug_mode)
                    is_valid, errors = validator.validate_solution(ecosystem, solution.species)
                    
                    if is_valid:
                        st.success("Valid solution!")
                        simulation = FeedingSimulation(solution.species, st if debug_mode else None, debug_mode)
                        success, feeding_history = simulation.simulate_feeding_round()
                        
                        st.subheader("Feeding History")
                        df = pd.DataFrame(feeding_history)
                        st.dataframe(df)
                        
                        if debug_mode:
                            stats = simulation.get_feeding_stats()
                            st.write("\nFeeding Statistics:")
                            st.write(f"- Total calories consumed: {stats['total_calories_consumed']}")
                            st.write(f"- Average consumption: {stats['average_consumption']:.2f}")
                            st.write(f"- Total feeding interactions: {stats['feeding_interactions']}")
                            
                            st.write("\nSpecies Details:")
                            for species in solution.species:
                                feeding_summary = simulation.get_species_feeding_summary(species.id)
                                st.write(f"\n{species.name}:")
                                st.write(f"- Calories consumed as predator: {feeding_summary['consumed_as_predator']}")
                                st.write(f"- Calories consumed as prey: {feeding_summary['consumed_as_prey']}")
                                st.write(f"- Remaining calories: {feeding_summary['remaining_calories']}")
                    else:
                        st.error("Invalid solution")
                        for error in errors:
                            st.write(f"- {error}")
                            
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
            if debug_mode:
                st.exception(e)

if __name__ == "__main__":
    main()