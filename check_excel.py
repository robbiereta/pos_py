import pandas as pd

# Read Excel file
df = pd.read_excel('prods.xlsx')

# Print columns
print("\nColumns:")
print("-" * 50)
print(df.columns.tolist())

# Print first few rows
print("\nFirst few rows:")
print("-" * 50)
print(df.head())
