import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Life Insurance Premium Calculator",
    page_icon="❤️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(to bottom right, #EFF6FF, #E0E7FF);
    }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_death_probabilities():
    """Load and parse the death probability CSV files"""
    try:
        # Load female data
        female_df = pd.read_csv('DeathProbsE_F_Alt2_TR2025.csv', skiprows=1)
        # Load male data
        male_df = pd.read_csv('DeathProbsE_M_Alt2_TR2025.csv', skiprows=1)
        
        # Get 2025 data (most recent)
        female_2025 = female_df[female_df['Year'] == 2025].iloc[0]
        male_2025 = male_df[male_df['Year'] == 2025].iloc[0]
        
        return {
            'female': female_2025,
            'male': male_2025
        }
    except Exception as e:
        st.error(f"Error loading death probability data: {e}")
        return None

def get_death_probability(data, age, gender):
    """Get death probability for a specific age and gender"""
    if data is None:
        return 0
    if gender=="male":
        gender_data = data['male']
    else:
        gender_data = data['female']
    prob = gender_data[str(age)]
    
    return prob if pd.notna(prob) else 0

def calculate_premium(age, gender, coverage_amount, term_length, smoker, health_rating, death_prob_data):
    """Calculate the monthly premium based on actuarial data"""
    if death_prob_data is None:
        return 0, 0
    
    # Health rating factors
    health_factors = {
        'Preferred Plus (Excellent)': 0.7,
        'Preferred (Good)': 1.0,
        'Standard (Average)': 1.4,
        'Substandard (Below Average)': 2.0
    }
    
    # Calculate expected present value of claims
    expected_claims = 0
    survival_probability = 1
    discount_rate = 0.03  # 3% discount rate
    cumulative_death_prob = 0
    
    for year in range(term_length):
        current_age = age + year
        death_prob = get_death_probability(death_prob_data, current_age, gender)
        
        # Adjust for smoking (smokers have roughly 2.5x mortality risk)
        if smoker:
            death_prob *= 2.5
        
        # Adjust for health rating
        death_prob *= health_factors[health_rating]
        
        # Probability of dying this year given survival to this point
        death_this_year = survival_probability * death_prob
        cumulative_death_prob += death_this_year
        
        # Present value of claim if death occurs this year
        discount_factor = (1 + discount_rate) ** (-(year + 0.5))
        expected_claims += death_this_year * coverage_amount * discount_factor
        
        # Update survival probability for next year
        survival_probability *= (1 - death_prob)
    
    # Add profit margin and expenses (typically 15-30% of expected claims)
    profit_margin = 1.25
    expense_loading = 100  # Fixed monthly expense
    
    # Calculate present value of annuity (monthly payments over term)
    monthly_discount_rate = (1 + discount_rate) ** (1/12) - 1
    num_payments = term_length * 12
    annuity_pv = (1 - (1 + monthly_discount_rate) ** (-num_payments)) / monthly_discount_rate
    
    # Monthly premium to cover expected claims plus profit
    monthly_premium = (expected_claims * profit_margin) / annuity_pv + expense_loading
    
    # Minimum $10/month
    monthly_premium = max(monthly_premium, 10)
    
    return monthly_premium, cumulative_death_prob * 100

def main():
    # Header
    st.markdown("<h1 style='text-align: center;'>❤️ Life Insurance Premium Calculator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280;'>Based on 2025 actuarial mortality tables</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Load death probability data
    death_prob_data = load_death_probabilities()
    
    if death_prob_data is None:
        st.error("Unable to load actuarial data. Please ensure the CSV files are in the same directory.")
        return
    
    # Create two columns for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("👤 Age", min_value=18, max_value=80, value=35, step=1)
        
        coverage_amount = st.selectbox(
            "💵 Coverage Amount",
            options=[100000, 250000, 500000, 750000, 1000000, 1500000, 2000000],
            index=2,
            format_func=lambda x: f"${x:,}"
        )
        
        health_rating = st.selectbox(
            "🏥 Health Rating",
            options=[
                'Preferred Plus (Excellent)',
                'Preferred (Good)',
                'Standard (Average)',
                'Substandard (Below Average)'
            ],
            index=1
        )
    
    with col2:
        gender = st.selectbox("Gender", options=['male', 'female'], format_func=lambda x: x.capitalize())
        
        term_length = st.selectbox(
            "📅 Term Length (Years)",
            options=[10, 15, 20, 25, 30],
            index=2
        )
        
        smoker = st.radio("🚬 Tobacco Use", options=['Non-Smoker', 'Smoker'], horizontal=True) == 'Smoker'
    
    # Calculate premium
    monthly_premium, cumulative_risk = calculate_premium(
        age, gender, coverage_amount, term_length, smoker, health_rating, death_prob_data
    )
    
    annual_premium = monthly_premium * 12
    total_cost = annual_premium * term_length
    
    # Display results
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #4F46E5;'>Your Estimated Premium</h2>", unsafe_allow_html=True)
    
    # Main premium display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Monthly Premium", f"${monthly_premium:.2f}")
    
    with col2:
        st.metric("Annual Premium", f"${annual_premium:.2f}")
    
    with col3:
        st.metric(f"Total Cost ({term_length} years)", f"${total_cost:,.0f}")
    
    # Risk analysis
    st.markdown("---")
    st.markdown("### 📊 Mortality Risk Analysis")
    
    risk_col1, risk_col2 = st.columns([2, 1])
    
    with risk_col1:
        st.info(f"""
        Based on actuarial tables, the cumulative probability of death over the {term_length}-year term 
        is **{cumulative_risk:.3f}%** for a {age}-year-old {gender} with your health profile.
        
        This means approximately **{round(cumulative_risk * 10)} out of 1,000** people with your 
        profile would be expected to pass away during the policy term.
        """)
    
    with risk_col2:
        st.metric("Cumulative Risk", f"{cumulative_risk:.3f}%")
        st.metric("Per 1,000 People", f"{round(cumulative_risk * 10)}")
    
    # Disclaimer
    st.markdown("---")
    st.warning("""
    **Note:** This calculator uses actual 2025 Social Security Administration mortality 
    tables to provide actuarially-based estimates. However, this is still an estimate only. 
    Actual premiums may vary based on additional factors including specific health conditions, 
    family history, occupation, hobbies, and the insurance company's underwriting guidelines. 
    Contact a licensed insurance agent for an accurate quote.
    """)

#if __name__ == "__main__":
#    main()

def get_insurance_inputs():
    """
    Prompts user for life insurance inputs and returns them for calculate_premium.
    """
    print("=== Life Insurance Premium Calculator ===\n")
    
    # Get basic information
    age = int(input("Enter age: "))
    
    print("\nEnter gender:")
    print("  1. Male")
    print("  2. Female")
    gender_choice = input("Select (1 or 2): ")
    gender = 'male' if gender_choice == "1" else 'female'
    
    coverage_amount = float(input("\nEnter coverage amount ($): "))
    term_length = int(input("Enter policy term length (years): "))
    
    print("\nAre you a smoker?")
    print("  1. Yes")
    print("  2. No")
    smoker_choice = input("Select (1 or 2): ")
    smoker = True if smoker_choice == "1" else False
    
    print("\nEnter health rating:")
    print("  1. Excellent")
    print("  2. Good")
    print("  3. Average")
    print("  4. Poor")
    health_choice = input("Select (1-4): ")
    health_ratings = {"1": "Excellent", "2": "Good", "3": "Average", "4": "Poor"}
    health_rating = health_ratings.get(health_choice, "Average")
    
    death_prob_data=get_death_probability(load_death_probabilities(),age, gender)
    death_prob_data
    print("\nInputs collected successfully!")
    
    return {
        'age': age,
        'gender': gender,
        'coverage_amount': coverage_amount,
        'term_length': term_length,
        'smoker': smoker,
        'health_rating': health_rating,
        'death_prob_data': death_prob_data
    }



    
def run_premium_calculator():
    """
    Main function to collect inputs and calculate premium.
    
    Parameters:
    - calculate_premium: The premium calculation function to use
    """
    # Get inputs from user
    inputs = get_insurance_inputs()
    
    # Calculate premium using the provided function
    premium = calculate_premium(
        age=inputs['age'],
        gender=inputs['gender'],
        coverage_amount=inputs['coverage_amount'],
        term_length=inputs['term_length'],
        smoker=inputs['smoker'],
        health_rating=inputs['health_rating'],
        death_prob_data=inputs['death_prob_data']
    )

run_premium_calculator()