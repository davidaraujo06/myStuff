import numpy as np
import pandas as pd
import pickle
import tensorflow as tf

def prepareInputData(year, month, day, hour, biddingArea, agent, unit, technology, country, capacity2030, transactionType, offeredMatched, bidEnergy, allPossibleCols):
    # Create a DataFrame with the input data
    inputData = pd.DataFrame({
        'Year': [year],
        'Month': [month],
        'Day': [day],
        'Hour': [hour],
        'Bidding Area': [biddingArea],
        'Agent': [agent],
        'Unit': [unit],
        'Technology': [technology],
        'Country': [country],
        'Capacity 2030': [capacity2030],
        'Transaction Type': [transactionType],
        'Offered (O)/Matched (M)': [offeredMatched],
        'Bid Energy': [bidEnergy]
    })

    # Apply pd.get_dummies for categorical columns
    inputDummies = pd.get_dummies(inputData, columns=['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)'])

    # Find missing columns and convert to list
    missingCols = list(set(allPossibleCols) - set(inputDummies.columns))
    
    # Create a DataFrame for missing columns with all zero values
    missingColsDf = pd.DataFrame(0, index=np.arange(len(inputDummies)), columns=missingCols)

    # Concatenate the DataFrame with missing columns to the input data
    inputDummies = pd.concat([inputDummies, missingColsDf], axis=1)

    # Ensure column order is correct
    inputDummies = inputDummies[allPossibleCols]

    return inputDummies



# Function to make predictions
def predictPrice(year, month, day, hour, biddingArea, agent, unit, technology, country, capacity2030, transactionType, offeredMatched, bidEnergy, modelPath):
    # Load scalers and possible columns
    with open('./modelPKL/scalerX.pkl', 'rb') as f:
        scalerX = pickle.load(f)

    with open('./modelPKL/scalerY.pkl', 'rb') as f:
        scalerY = pickle.load(f)

    with open('./modelPKL/allPossibleCols.pkl', 'rb') as f:
        allPossibleCols = pickle.load(f)

    print("Scalers and possible columns loaded.")

    # Prepare the input data
    inputData = prepareInputData(year, month, day, hour, biddingArea, agent, unit, technology, country, capacity2030, transactionType, offeredMatched, bidEnergy, allPossibleCols)
    
    # Scale the input data
    inputScaled = scalerX.transform(inputData)

    # Reshape the data to the expected format for the CNN
    inputReshaped = np.expand_dims(inputScaled, axis=2)

    # Load the trained model
    model = tf.keras.models.load_model(modelPath)

    # Make the prediction
    predictionScaled = model.predict(inputReshaped)

    # Inverse transform the prediction
    prediction = scalerY.inverse_transform(predictionScaled.reshape(-1, 1))

    return prediction[0][0]

import pandas as pd

# Caminho para o ficheiro pickle
file_path = '../PKLData/2023/dfResultFinal_2023_1.pkl'

# Ler o ficheiro pickle
df = pd.read_pickle(file_path)


# Definir o número máximo de linhas a exibir
pd.set_option('display.max_rows', 50)  # Aqui definiu 100, você pode mudar para o número desejado

# Exibir o DataFrame inteiro ou até o limite estabelecido
print(df)


# Example input values
year = 2023
month = 1
day = 31
hour = 24
biddingArea = "MI"
agent = "ENGNE"
unit = "ENGNG02"
technology = "Others non-renewable"
country = "PT"
capacity2030 = 25.188821
transactionType = "Sell"
offeredMatched = "C"
bidEnergy = 3.5

# Path to the trained model
modelPath = './modelPKL/2022_01Model.keras'

# Make the prediction
predictedPrice = predictPrice(year, month, day, hour, biddingArea, agent, unit, technology, country, capacity2030, transactionType, offeredMatched, bidEnergy, modelPath)

print(f"The predicted price is: {predictedPrice}")
