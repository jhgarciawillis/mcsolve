import streamlit as st
import pandas as pd
from pathlib import Path
from core.species import Ecosystem
from core.generator import ScenarioGenerator, SolutionGenerator
from core.validator import SolutionValidator
from utils.excel_handler import ExcelHandler

st.set_page_config(
    page_title="McKinsey Solve Game Helper",
    page_icon="🌿",
    layout="wide"
)

def main():
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
        generator = ScenarioGenerator()
        ecosystem = generator.generate_scenario()
        
        # Save to temporary file
        temp_file = "temp_scenario.xlsx"
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
    
    uploaded_file = st.file_uploader("Upload Scenario", type="xlsx")
    if uploaded_file is not None:
        ecosystem = ExcelHandler.read_scenario(uploaded_file)
        
        if st.button("Generate Solutions"):
            solutions = SolutionGenerator.generate_all_solutions(ecosystem)
            ranked_solutions = SolutionGenerator.rank_solutions(solutions)
            
            st.write(f"Found {len(ranked_solutions)} valid solutions")
            
            for i, (solution, score) in enumerate(ranked_solutions[:10]):
                st.subheader(f"Solution {i+1} (Score: {score:.2f})")
                df = pd.DataFrame([{
                    'ID': s.id,
                    'Name': s.name,
                    'Type': s.species_type.value,
                    'Calories Provided': s.calories_provided,
                    'Calories Needed': s.calories_needed,
                    'Bin': s.bin
                } for s in solution])
                st.dataframe(df)

def check_solution_page():
    st.header("Check Solution")
    
    uploaded_scenario = st.file_uploader("Upload Scenario", type="xlsx", key="scenario")
    uploaded_solution = st.file_uploader("Upload Solution", type="xlsx", key="solution")
    
    if uploaded_scenario is not None and uploaded_solution is not None:
        ecosystem = ExcelHandler.read_scenario(uploaded_scenario)
        solution = ExcelHandler.read_scenario(uploaded_solution)
        
        if st.button("Validate Solution"):
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

if __name__ == "__main__":
    main()