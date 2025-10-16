import math
import pandas as pd


def accumulated_annuity(periods, i, type):
  #accumulated annuity function
  if type == 1:
    return (math.pow(1 + i, periods) - 1) / i
  elif type == 2:
    return (math.pow(1 + i, periods) - 1) / (math.pow((1 - 1 / i), -1))
  else:
      return ()

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
        return None
def get_death_probability(data, age, gender='female'):
    """Get death probability for a specific age and gender.

    data can be:
      - a dict like {'female': Series, 'male': Series}
      - a pandas Series (one row where columns are ages or age strings)
      - a list/tuple/array indexed by age (0-based)

    Returns a float probability or 0 if not available.
    """
    if data is None:
        return 0.0

    # If a dict was passed, pick the gender-specific entry when available
    if isinstance(data, dict):

        # normalize gender key
        key = str(gender).lower()
        if key in data:
            data = data[key]
            #print("marker")
        else:
            # fallback to female then male, or None
            data = data.get('female') or data.get('male')

    prob = 0.0
    # If data is a pandas Series (e.g., a DataFrame row), try column lookup
    if isinstance(data, pd.Series):
        #print("marker 2")
        # column names in the CSV may be strings like '20' or integers
        for lookup in (str(age), int(age) if isinstance(age, (str, float)) and str(age).isdigit() else None, age):
            if lookup is None:
                #print("marker 3")
                continue
            try:
                if lookup in data.index:
                    val = data[lookup]
                    if pd.notna(val):
                        prob = float(val)
                        break
            except Exception:
                continue

    else:
        # For list/array/tuple-like data, attempt integer index
        try:
            idx = int(age)
            if idx >= 0 and idx < len(data):
                val = data[idx]
                if pd.notna(val):
                    prob = float(val)
        except Exception:
            # any failure falls through to returning 0.0
            prob = 0.0

    return prob







def calculate_prenium(current_age, payout_age, intrest, payout, gender='female'):
    '''
    

    Parameters
    ----------
    current_age : int/double
        age of client at maturation
    payout_age : int/double
        age when client recieves payout
    intrest : float
        annual effective interest
    payout : int
        payout ammount
    gender : TYPE, optional
        DESCRIPTION. The default is 'female'.

    Returns
    -------
    calculates prenium per given inputs.

    '''
    weighted_total_annuity = 0
    death_data = load_death_probabilities()
    # if death_data is None:
    #     death_data = sample_death_data
    #death_probabilities = death_data[gender] if isinstance(death_data, dict) else death_data
    
    #assume probability of age = 1
    prob_death_given_age_is_x= 0
    prob_death_and_age_is_x = 0
    prob_age_is_x = 1
    death_cdf=0
    prob_asset_exceeds_payout=0
    unweighted_annuity=0
    
    
    for evaluation_age in range(current_age, payout_age):
        prob_age_is_x = (1-prob_death_given_age_is_x)*prob_age_is_x
        prob_death_given_age_is_x = get_death_probability(death_data, evaluation_age, gender)
        if (evaluation_age < payout_age-1):
            prob_death_and_age_is_x = prob_age_is_x * prob_death_given_age_is_x
            #print(str(prob_death_and_age_is_x) + " for age " + str(evaluation_age))
        else:
            prob_death_and_age_is_x = prob_age_is_x
            #print(str(prob_death_and_age_is_x) + " survives period.")
        death_cdf+=prob_death_and_age_is_x
        weighted_total_annuity += accumulated_annuity(evaluation_age-current_age, intrest, 1) * prob_death_and_age_is_x

    print( "make sure this is 1: " + str(death_cdf))
    return (payout / weighted_total_annuity)




def calculate_risk_tolerance(prenium,payout,current_age,payout_age,intrest,gender):
    '''

    Parameters
    ----------
    prenium : insurance prenium
    payout : ammount of desired payout
    current_age : age at time of measurement
    payout_age : age 
    intrest : TYPE
        DESCRIPTION.
    gender : TYPE
        DESCRIPTION.

    Returns
    -------
    death_cdf : TYPE
        DESCRIPTION.

    '''
    death_cdf= 0
    prob_death_given_age_is_x= 0
    prob_death_and_age_is_x = 0
    prob_age_is_x = 1
    death_data=load_death_probabilities()
    for x in range(current_age,payout_age):
        
        
        prob_age_is_x=prob_age_is_x = (1-prob_death_given_age_is_x)*prob_age_is_x
        prob_death_given_age_is_x=get_death_probability(death_data, x, gender)
        prob_death_and_age_is_x = prob_age_is_x * prob_death_given_age_is_x
        death_cdf+=prob_death_and_age_is_x
        
        s= prenium*accumulated_annuity(x-current_age, intrest, 1)
        
        if( s > payout):
            return death_cdf

current_age =20
payout_age =60
intrest=.12
payout=100000
gender='male'

example_calculated_prenium=calculate_prenium(current_age,payout_age,intrest,payout,gender)


print(example_calculated_prenium)
print(example_calculated_prenium*accumulated_annuity( payout_age-current_age, intrest , 1))
print(calculate_risk_tolerance(example_calculated_prenium, payout, current_age, payout_age, intrest, gender))






