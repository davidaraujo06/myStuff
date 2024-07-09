import os
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Paths to directories
curve_price_dir = './data/curvasPreco'  # Directory with curve price CSV files (2022 and 2023)
market_price_dir = './data/mercadoDiario'  # Directory with market price CSV files (2022 and 2023)
units_path = './data/units-info.xlsx'

# Load the units data
units = pd.read_excel(units_path, engine='openpyxl')

# Define columns for market price and curve price
columns_market_price = ['Year', 'Month', 'Day', 'Hour', 'PricePT', 'PriceES', 'extra']
columns_curve_price = ['Pais', 'Fecha', 'Unidad', 'Tipo Oferta', 'Energía Compra/Venta', 'Precio Compra/Venta', 'Ofertada (O)/Casada (C)', 'Hora']

# Function to load and process CSV files
def load_and_process_csv(file_path, columns, date_format='%Y%m%d'):
    skiprows = 2 if 'curva_pbc_uof' in file_path else 1
    df = pd.read_csv(file_path, sep=';', encoding='latin1', skiprows=skiprows, header=None)
    df.columns = columns

    if 'curva_pbc_uof' in file_path:
        df = df.drop(columns=['Unnamed: 8'], errors='ignore')
        df['Hora'] = df['Hora'].fillna(0).astype(int)
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')
        df['datetime'] = df['Fecha'] + pd.to_timedelta(df['Hora'] - 1, unit='h')
    else:
        df = df.drop(columns=['extra'], errors='ignore')
        df = df[df['Year'] != '*']
        df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day']]) + pd.to_timedelta(df['Hour'] - 1, unit='h')

    return df

# Function to merge data for a given date
def process_date(year, month, day):
    date_str = f'{year}{month:02d}{day:02d}'
    market_file = os.path.join(market_price_dir, str(year), f'marginalpdbcpt_{date_str}.1')
    curve_file = os.path.join(curve_price_dir, str(year), str(month), f'curva_pbc_uof_{date_str}.1')

    if os.path.exists(market_file) and os.path.exists(curve_file):
        market_price = load_and_process_csv(market_file, columns_market_price)
        curve_price = load_and_process_csv(curve_file, columns_curve_price)

        first_csv = pd.merge(curve_price, market_price, on='datetime', how='inner')
        first_csv.rename(columns={
            'Pais': 'Bidding Area',
            'Fecha': 'Date',
            'Unidad': 'Unit',
            'Tipo Oferta': 'Offer Type',
            'Energía Compra/Venta': 'Bid Energy',
            'Precio Compra/Venta': 'Bid Price',
            'Ofertada (O)/Casada (C)': 'Offered (O)/Matched (M)'
        }, inplace=True)

        first_csv = first_csv.drop(columns=['Hora', 'Date', 'Offer Type', 'datetime'], errors='ignore')

        df_result_final = pd.merge(first_csv, units, on='Unit', how='inner')

        columns_to_int = ['Year', 'Month', 'Day', 'Hour']
        columns_to_string = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
        columns_to_float = ['Capacity_2030', 'Bid Energy', 'Bid Price', 'PricePT', 'PriceES']

        for column in columns_to_int:
            df_result_final[column] = df_result_final[column].astype(int)

        for column in columns_to_string:
            df_result_final[column] = df_result_final[column].astype(str)

        for column in columns_to_float:
            df_result_final[column] = df_result_final[column].apply(convert_to_float)

        return df_result_final
    return None

# Function to clean and convert number strings to floats
def convert_to_float(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        value = re.sub(r'[^\d.-]', '', value)
    return pd.to_numeric(value, errors='coerce')

# Main function to process all dates using threading
def main():
    all_data = []
    years = [2022, 2023]
    days_in_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for year in years:
            for month in range(1, 13):
                for day in range(1, days_in_month[month] + 1):
                    futures.append(executor.submit(process_date, year, month, day))

        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                all_data.append(result)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        pickle_file = 'df_result_final_2022_2023.pkl'
        final_df.to_pickle(pickle_file)
        print(f"DataFrame saved to {pickle_file}")

if __name__ == '__main__':
    main()
