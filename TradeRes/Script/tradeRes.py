import pandas as pd
import re
import os
from datetime import datetime

# Caminhos para os diretórios
market_price_dir = './market_price_2022'  # Diretório com arquivos CSV de preços de mercado
curve_price_dir = './curve_price_2022'  # Diretório com subpastas 1 a 12 contendo os arquivos CSV de curva de preço

# Caminho para o arquivo XLSX de unidades
units_path = './data/units-info.xlsx'
units = pd.read_excel(units_path, engine='openpyxl') 

def load_and_process_csv(file_path, columns, date_format='%Y%m%d'):
    # Carregar o CSV
    df = pd.read_csv(file_path, sep=';', encoding='latin1', skiprows=2 if 'curva_pbc_uof' in file_path else 1, header=None)
    
    # Adicionar colunas
    df.columns = columns
    
    # Filtrar colunas e linhas específicas
    if 'curva_pbc_uof' in file_path:
        df = df.drop(columns=['Unnamed: 8'])
        df['Hora'] = df['Hora'].fillna(0).astype(int)
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')
        df['datetime'] = df['Fecha'] + pd.to_timedelta(df['Hora'] - 1, unit='h')
    else:
        df = df.drop(columns=['extra'])
        df = df[df['Year'] != '*']
        df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day']]) + pd.to_timedelta(df['Hour'] - 1, unit='h')

    return df

def convert_to_float(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        value = re.sub(r'[^\d.-]', '', value)
    return pd.to_numeric(value, errors='coerce')

columns_market_price = ['Year', 'Month', 'Day', 'Hour', 'PricePT', 'PriceES', 'extra']
columns_curve_price = ['Pais', 'Fecha', 'Unidad', 'Tipo Oferta', 'Energía Compra/Venta', 'Precio Compra/Venta', 'Ofertada (O)/Casada (C)', 'Hora']

# Iterar sobre os meses (de 1 a 12)
all_data = []

for month in range(1, 13):
    # Iterar sobre os dias do mês (de 1 a 31)
    for day in range(1, 32):
        try:
            date_str = f'{2022}{month:02d}{day:02d}'
            market_file = os.path.join(market_price_dir, f'marginalpdbcpt_{date_str}.1')
            curve_file = os.path.join(curve_price_dir, str(month), f'curva_pbc_uof_{date_str}.1')

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

                first_csv = first_csv.drop(columns=['Hora', 'Date', 'Offer Type', 'datetime'])

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

                all_data.append(df_result_final)

        except Exception as e:
            print(f'Error processing {date_str}: {str(e)}')

# Concatenate all DataFrames
final_df = pd.concat(all_data, ignore_index=True)

# Save the final DataFrame to a pickle file
pickle_file = 'df_result_final_2022.pkl'
final_df.to_pickle(pickle_file)

print(f"DataFrame saved to {pickle_file}")
