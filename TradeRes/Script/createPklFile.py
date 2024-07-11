import os
import pandas as pd
import re
import calendar
from concurrent.futures import ThreadPoolExecutor, as_completed

# Paths to directories
curvePriceDir = './data/priceCurves' 
marketPriceDir = './data/marketPrice'  
unitsPath = './data/units-info.xlsx'

# Load the units data
units = pd.read_excel(unitsPath, engine='openpyxl')

def loadAndProcessCSV(filePath):
    try:
        if 'curva_pbc_uof' in filePath:
            df = pd.read_csv(filePath, sep=';', encoding='latin1', skiprows=2)
        else:
            df = pd.read_csv(filePath, sep=';', encoding='latin1', skiprows=1, header=None)  
            df.columns = ['Year', 'Month', 'Day', 'Hour', 'PricePT', 'PriceES', 'extra'] 

        if 'curva_pbc_uof' in filePath:
            df['Hora'] = df['Hora'].fillna(0).astype(int)
            df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')
            df['datetime'] = df['Fecha'] + pd.to_timedelta(df['Hora'] - 1, unit='h')
        else:
            df = df.drop(columns=['extra'])
            df = df[df['Year'] != '*']
            df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day']]) + pd.to_timedelta(df['Hour'] - 1, unit='h')

        return df

    except Exception as e:
        print(f"Error processing file '{filePath}': {e}")
        return None


# Function to clean and convert number strings to floats
def convertToFloat(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        value = re.sub(r'[^\d.-]', '', value)
    return pd.to_numeric(value, errors='coerce')

# Function to merge data for a given date
def processDate(year, month, day):
    try:
        dateStr = f'{year}{month:02d}{day:02d}'
        marketFile = marketPriceDir + "/" + str(year) + f'/marginalpdbcpt_{dateStr}.1'
        curveFile = curvePriceDir + "/" + str(year) +  "/" + f'{month:02d}' +  f'/curva_pbc_uof_{dateStr}.1'

        print(f"Iniciating process for this date: {year}-{month:02d}-{day:02d}")

        if os.path.exists(marketFile) and os.path.exists(curveFile):

            marketPrice = loadAndProcessCSV(marketFile)
            curvePrice = loadAndProcessCSV(curveFile)

            if marketPrice is None or curvePrice is None:
                print(f"Failed to load data for date {year}-{month:02d}-{day:02d}")
                return None

            firstCSV = pd.merge(curvePrice, marketPrice, on='datetime', how='inner')
            firstCSV.rename(columns={
                'Pais': 'Bidding Area',
                'Fecha': 'Date',
                'Unidad': 'Unit',
                'Tipo Oferta': 'Offer Type',
                'Energía Compra/Venta': 'Bid Energy',
                'Precio Compra/Venta': 'Bid Price',
                'Ofertada (O)/Casada (C)': 'Offered (O)/Matched (M)'
            }, inplace=True)

            firstCSV = firstCSV.drop(columns=['Hora', 'Date', 'Offer Type', 'datetime', 'Unnamed: 8'])

            dfResultFinal = pd.merge(firstCSV, units, on='Unit', how='left')

            new_order = ['Year', 'Month', 'Day', 'Hour', 'Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Capacity_2030', 'Transaction Type', 'Offered (O)/Matched (M)', 'Bid Energy', 'Bid Price', 'PricePT', 'PriceES']
            
            dfResultFinal = dfResultFinal[new_order]

            columnsToInt = ['Year', 'Month', 'Day', 'Hour']
            columnsToString = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
            columnsToFloat = ['Capacity_2030', 'Bid Energy', 'Bid Price', 'PricePT', 'PriceES']

            for column in columnsToInt:
                dfResultFinal[column] = dfResultFinal[column].astype(int)

            for column in columnsToString:
                dfResultFinal[column] = dfResultFinal[column].astype(str)

            for column in columnsToFloat:
                dfResultFinal[column] = dfResultFinal[column].apply(convertToFloat)

            dfResultFinal = dfResultFinal.fillna('nan')
            print(f"Processed data for date {year}-{month:02d}-{day:02d}")
            return dfResultFinal
        else:
            print(f"Files not found for date {year}-{month:02d}-{day:02d}")
            return None

    except Exception as e:
        print(f"Error processing date {year}-{month:02d}-{day:02d}: {e}")
        return None

# Function to count the number of year subdirectories
def countYearSubdirectories(directory):
    return len([name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))])

# Function to get the set of year subdirectories
def getYearSubdirectories(directory):
    return {int(name) for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))}

# Function to get the number of days in a month
def getDaysInMonth(year, month):
    return calendar.monthrange(year, month)[1]

marketYears = getYearSubdirectories(marketPriceDir)
curveYears = getYearSubdirectories(curvePriceDir)
marketFilesCount = countYearSubdirectories(marketPriceDir)
curveFilesCount = countYearSubdirectories(curvePriceDir)

if marketYears != curveYears:
    raise ValueError(f"The year subdirectories in {marketPriceDir} and {curvePriceDir} are not equal. Market years: {marketYears}, Curve years: {curveYears}")

if marketFilesCount != curveFilesCount:
    raise ValueError(f"The number of files in {marketPriceDir} ({marketFilesCount}) and {curvePriceDir} ({curveFilesCount}) are not equal.")

try:
    allData = {}
    years = sorted(int(year) for year in marketYears)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {year: [] for year in years}
        for year in years:
            if year in marketYears:
                for month in range(1, 13):
                    daysInMonth = getDaysInMonth(year, month)
                    for day in range(1, daysInMonth + 1):
                        futures[year].append(executor.submit(processDate, year, month, day))

        for year in years:
            allData[year] = []
            for future in as_completed(futures[year]):
                result = future.result()
                if result is not None:
                    allData[year].append(result)

    for year, data in allData.items():
        if data:
            finalDF = pd.concat(data, ignore_index=True)
            finalDF = finalDF.sort_values(by=['Year', 'Month', 'Day', 'Hour'])
            pickleFile = f'./PKLData/dfResultFinal{year}.pkl'
            finalDF.to_pickle(pickleFile)
            print(f"DataFrame {year} saved to {pickleFile}")

except Exception as e:
    print("Major Error: "+ str(e))
