import pandas as pd
import re
import os

# Load data from the first CSV, skipping the first 2 unnecessary rows
curva_precos = pd.read_csv('./data/curva_pbc_uof_20220301.1', sep=';', encoding='latin1', skiprows=2)

# Load data from the second CSV, skipping the first row and adding column names
preco_mercado = pd.read_csv('./data/marginalpdbcpt_20220301.1', sep=';', encoding='latin1', skiprows=1, header=None)

# Path to the XLSX file
units = './data/units-info.xlsx'

units = pd.read_excel(units, engine='openpyxl') 

def format_data_12(curva_precos, preco_mercado):
    # Rename columns in the second CSV
    preco_mercado.columns = ['Year', 'Month', 'Day', 'Hour', 'PricePT', 'PriceES', 'extra']

    # Remove the 'extra' column
    preco_mercado = preco_mercado.drop(columns=['extra'])

    # Remove rows containing invalid characters (like '*')
    preco_mercado = preco_mercado[preco_mercado['Year'] != '*']

    # Fill missing values in the 'Hour' column of the first CSV with 0 (or any appropriate default value)
    curva_precos['Hora'] = curva_precos['Hora'].fillna(0)

    # Convert the 'Hour' column to integer
    curva_precos['Hora'] = curva_precos['Hora'].astype(int)

    # Convert date and hour columns from the first CSV to an appropriate format
    curva_precos['Fecha'] = pd.to_datetime(curva_precos['Fecha'], format='%d/%m/%Y')
    curva_precos['datetime'] = curva_precos['Fecha'] + pd.to_timedelta(curva_precos['Hora'] - 1, unit='h')

    # Convert year, month, day, and hour columns from the second CSV to an appropriate format
    preco_mercado['datetime'] = pd.to_datetime(preco_mercado[['Year', 'Month', 'Day']]) + pd.to_timedelta(preco_mercado['Hour'] - 1, unit='h')

    return curva_precos, preco_mercado

curva_precos, preco_mercado = format_data_12(curva_precos, preco_mercado)

# Create first CSV
first_csv = pd.merge(curva_precos, preco_mercado, on='datetime', how='inner')

def format_data_13(first_csv):
    # Rename columns in the merged DataFrame
    first_csv.rename(columns={
        'Pais': 'Bidding Area',
        'Fecha': 'Date',
        'Unidad': 'Unit',
        'Tipo Oferta': 'Offer Type',
        'Energía Compra/Venta': 'Bid Energy',
        'Precio Compra/Venta': 'Bid Price',
        'Ofertada (O)/Casada (C)': 'Offered (O)/Matched (M)'
    }, inplace=True)

    # Remove columns 'Hora', 'Date', 'Offer Type', 'datetime', and 'Unnamed: 8' from the final DataFrame
    first_csv = first_csv.drop(columns=['Hora', 'Date', 'Offer Type', 'datetime', 'Unnamed: 8'])

    return first_csv, units

first_csv, units = format_data_13(first_csv)

# Merge with 'units' DataFrame on 'Unit' column
df_result_final = pd.merge(first_csv, units, on='Unit', how='inner')

# Define new order for columns
new_order = ['Year', 'Month', 'Day', 'Hour', 'Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Capacity_2030', 'Transaction Type', 'Offered (O)/Matched (M)', 'Bid Energy', 'Bid Price', 'PricePT', 'PriceES']

# Reorder columns
df_result_final = df_result_final[new_order]

# Function to clean and convert number strings to floats
def convert_to_float(value):
    if isinstance(value, str):
        # Replace decimal comma with dot
        value = value.replace(',', '.')

        # Use regular expression to remove non-numeric characters except decimal point
        value = re.sub(r'[^\d.-]', '', value)

    # Convert to float
    return pd.to_numeric(value, errors='coerce')

# Columns to convert
columns_to_int = ['Year', 'Month', 'Day', 'Hour']
columns_to_string = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
columns_to_float = ['Capacity_2030', 'Bid Energy', 'Bid Price', 'PricePT', 'PriceES']

# Apply specific conversions
for column in columns_to_int:
    df_result_final[column] = df_result_final[column].astype(int)

for column in columns_to_string:
    df_result_final[column] = df_result_final[column].astype(str)

for column in columns_to_float:
    df_result_final[column] = df_result_final[column].apply(convert_to_float)

# Save the final DataFrame to a new CSV file
df_result_final.to_csv('resultado_final_completo.csv', index=False, sep=';', encoding='latin1')

# Save DataFrame to a pickle file
pickle_file = 'df_resultado_final.pkl'
df_result_final.to_pickle(pickle_file)

print(f"DataFrame saved to {pickle_file}")
