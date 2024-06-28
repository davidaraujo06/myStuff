import pandas as pd

# Carregar os dados do primeiro CSV, pulando as primeiras 2 linhas que não são necessárias
curvaPrecos = pd.read_csv('./data/curva_pbc_uof_20220301.1', sep=';', encoding='latin1', skiprows=2)

# Carregar os dados do segundo CSV, pulando a primeira linha e adicionando nomonth das colunas
precoMercado = pd.read_csv('./data/marginalpdbcpt_20220301.1', sep=';', encoding='latin1', skiprows=1, header=None)

# Caminho para o arquivo XLSX
units = './data/units-info.xlsx'

units = pd.read_excel(units, engine='openpyxl') 

def formatateData12(curvaPrecos, precoMercado):

    precoMercado.columns = ['year', 'month', 'day', 'hour', 'price_PT', 'price_ES', 'extra']

    # Remover a coluna extra
    precoMercado = precoMercado.drop(columns=['extra'])

    # Remover linhas que contenham caracteres inválidos (como '*')
    precoMercado = precoMercado[precoMercado['year'] != '*']

    # Preencher valores faltantes na coluna 'hour' do primeiro CSV com 0 (ou qualquer valor padrão apropriado)
    curvaPrecos['Hora'] = curvaPrecos['Hora'].fillna(0)

    # Converter a coluna 'hour' para inteiro
    curvaPrecos['Hora'] = curvaPrecos['Hora'].astype(int)

    # Converter as colunas de data e hour do primeiro CSV para um formato adequado
    curvaPrecos['Fecha'] = pd.to_datetime(curvaPrecos['Fecha'], format='%d/%m/%Y')
    curvaPrecos['datetime'] = curvaPrecos['Fecha'] + pd.to_timedelta(curvaPrecos['Hora'] - 1, unit='h')

    # Converter as colunas de year, month, day e hour do segundo CSV para um formato adequado
    precoMercado['datetime'] = pd.to_datetime(precoMercado[['year', 'month', 'day']]) + pd.to_timedelta(precoMercado['hour'] - 1, unit='h')

    return curvaPrecos, precoMercado


curvaPrecos, precoMercado = formatateData12(curvaPrecos, precoMercado)
#createFirstCSV
firsCsv = pd.merge(curvaPrecos, precoMercado, on='datetime', how='inner')

def formatateData13(firsCsv):

    # Remover as colunas 'year', 'month', 'day', 'hour', 'datetime' e 'Unnamed: 8' do DataFrame final
    firsCsv = firsCsv.drop(columns=['year', 'month', 'day', 'hour', 'datetime', 'Unnamed: 8'])

    # Renomear a coluna 'unidad' para 'Unit'
    firsCsv.rename(columns={
        'Hora': 'Hour',
        'Fecha': 'Date',
        'Unidad': 'Unit',
        'Tipo Oferta': 'Offer Type',
        'Energía Compra/Venta': 'Energy Buy/Sell',
        'Precio Compra/Venta': 'Price Buy/Sell',
        'Ofertada (O)/Casada (C)': 'Offered (O)/Matched (M)'
    }, inplace=True)

    return firsCsv, units

firsCsv, units = formatateData13(firsCsv)

df_resultado_final = pd.merge(firsCsv, units, on= 'Unit', how='inner')

# Salvar o DataFrame final em um novo CSV
df_resultado_final.to_csv('resultado_final_completo.csv', index=False, sep=';', encoding='latin1')
