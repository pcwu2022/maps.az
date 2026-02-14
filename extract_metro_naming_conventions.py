import pandas as pd
import pycountry

# Read the metro names raw data
df = pd.read_csv('data_processing/metro_names_raw.csv')

# Define the naming convention columns
naming_conventions = ['Metro', 'Underground', 'U-Bahn', 'Subway', 'Rail Transit', 'MRT', 'Other']

# Group by country and count TRUE values for each naming convention
country_naming_counts = {}

for country in df['Country'].unique():
    country_data = df[df['Country'] == country]
    
    # Count TRUE values for each naming convention
    convention_counts = {}
    for convention in naming_conventions:
        count = (country_data[convention] == True).sum()
        if count > 0:
            convention_counts[convention] = count
    
    # Find the majority naming convention
    if convention_counts:
        majority_convention = max(convention_counts, key=convention_counts.get)
        country_naming_counts[country] = majority_convention

# Create result dataframe
results = []
for country, convention in country_naming_counts.items():
    # Get ISO code using pycountry
    try:
        iso_code = pycountry.countries.search_fuzzy(country)[0].alpha_3
    except:
        # Handle special cases or countries not found
        iso_code = None
    
    results.append({
        'country': country,
        'country_ISO': iso_code,
        'value': convention
    })

result_df = pd.DataFrame(results)

# Save to CSV
result_df.to_csv('outputs/metro_naming_conventions.csv', index=False)

print(f"Extracted {len(result_df)} countries with their majority metro naming conventions")
print("\nPreview:")
print(result_df.head(10))
