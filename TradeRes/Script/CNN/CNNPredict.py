import numpy as np
import pandas as pd
import pickle
import tensorflow as tf

# Function to prepare the input data for prediction
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

    # Ensure all possible columns are present
    missingCols = set(allPossibleCols) - set(inputDummies.columns)
    for col in missingCols:
        inputDummies[col] = 0
    
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

# Example input values
year = 2023
month = 1
day = 2
hour = 8
biddingArea = "MI"
agent = "EGLE"
unit = "EGVD086"
technology = "Wind Onshore"
country = "ES"
capacity2030 = 22.516331
transactionType = "Sell"
offeredMatched = "C"
bidEnergy = 3.0

# Path to the trained model
modelPath = './modelPKL/monthlyModel.keras'

# Make the prediction
predictedPrice = predictPrice(year, month, day, hour, biddingArea, agent, unit, technology, country, capacity2030, transactionType, offeredMatched, bidEnergy, modelPath)

print(f"The predicted price is: {predictedPrice}")
