from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from pathlib import Path
import pandas as pd
import numpy as np
import tensorflow as tf
import pickle, calendar, os, glob

# Function to load and process data up to the specified date
def loadDataForDay(pathPattern, colsToTransform, targetColumn, year, month, day, allPossibleCols=None):
    allFiles = glob.glob(pathPattern)
    data = []
    target = []

    for file in allFiles:
        print(f"Processing file: {file}")
        df = pd.read_pickle(file)

        # Check if the target column is present
        if targetColumn not in df.columns:
            raise KeyError(f"Column '{targetColumn}' not found in file {file}.")

        # Filter data for the specific day
        df = df[(df['Year'] == year) & (df['Month'] == month) & (df['Day'] == day)]
        
        # Separate target column
        y = df[targetColumn]
        x = df.drop(columns=[targetColumn])

        # Apply dummy transformation
        xDummies = pd.get_dummies(x, columns=colsToTransform)

        # Ensure all days have the same columns
        if allPossibleCols is not None:
            missingCols = set(allPossibleCols) - set(xDummies.columns)
            for col in missingCols:
                xDummies[col] = 0
            xDummies = xDummies[allPossibleCols]

        if xDummies.isna().any().any() or y.isna().any():
            xDummies.fillna(0.0, inplace=True)
            y.fillna(0.0, inplace=True)

        data.append(xDummies)
        target.append(y)

    if data:  # Check if there is data
        xAll = pd.concat(data, ignore_index=True)
        yAll = pd.concat(target, ignore_index=True)
    else:
        raise ValueError("No data loaded after filtering. Check the criteria.")

    return xAll, yAll

# Function to build the model
def buildModel(inputShape):
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=inputShape),
        tf.keras.layers.MaxPooling1D(pool_size=2),
        tf.keras.layers.Conv1D(filters=128, kernel_size=3, activation='relu'),
        tf.keras.layers.MaxPooling1D(pool_size=2),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.5), 
        tf.keras.layers.Dense(1)
    ])
    
    return model

# #TODO: sugestão de melhoria
# def buildModel(inputShape):
#     model = tf.keras.models.Sequential([
#         tf.keras.layers.Conv1D(filters=64, kernel_size=5, activation='relu', input_shape=inputShape),
#         tf.keras.layers.BatchNormalization(),
#         tf.keras.layers.MaxPooling1D(pool_size=2),
#         tf.keras.layers.Conv1D(filters=128, kernel_size=5, activation='relu'),
#         tf.keras.layers.BatchNormalization(),
#         tf.keras.layers.MaxPooling1D(pool_size=2),
#         tf.keras.layers.Flatten(),
#         tf.keras.layers.Dense(128, activation='relu'),
#         tf.keras.layers.Dropout(0.5), 
#         tf.keras.layers.Dense(1)
#     ])
#     model.compile(optimizer='adam', loss='mean_squared_error')
#     return model


# Function to train the model daily in an incremental manner
def trainModelDailyIncremental(year, month, startDay, endDay, pathPattern, modelSavePath):
    allPossibleCols = None

    for day in range(startDay, endDay + 1):
        print(f"\nTraining with data from day {day}...")
        
        # Load data for the current day
        x, y = loadDataForDay(pathPattern, colsToTransform, targetColumn, year, month, day, allPossibleCols)

        if allPossibleCols is None:
            allPossibleCols = x.columns

        # Scale the data
        xScaled = scalerX.fit_transform(x)
        yScaled = scalerY.fit_transform(y.values.reshape(-1, 1)).ravel()

        # Split into training and validation sets
        xTrain, xVal, yTrain, yVal = train_test_split(xScaled, yScaled, train_size=0.7, random_state=42)

        # Reshape data for CNN
        xTrainReshaped = np.expand_dims(xTrain, axis=2)
        xValReshaped = np.expand_dims(xVal, axis=2)

        # Load complete model, including optimizer
        if os.path.exists(modelSavePath):
            model = tf.keras.models.load_model(modelSavePath)  # Load complete model (with optimizer)
            print("Complete model loaded")
        else:
            model = buildModel(inputShape=(xTrainReshaped.shape[1], 1))
            model.compile(optimizer='adam', loss='mean_squared_error')
            print("New model created")

        # Train the model with current day's data (incrementally)
        model.fit(xTrainReshaped, yTrain, epochs=2, batch_size=32, validation_data=(xValReshaped, yVal))
        
        # #TODO: sugestão de melhoria
        # early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)
        # model.fit(xTrainReshaped, yTrain, epochs=10, batch_size=32, validation_data=(xValReshaped, yVal), callbacks=[early_stopping])

                
        # Save model weights after daily training
        # Save complete model
        model.save(modelSavePath)

        print(f"Model saved to {modelSavePath}")
        # Save scalers and columns after complete training

        with open('./modelPKL/scalerX.pkl', 'wb') as f:
            pickle.dump(scalerX, f)

        with open('./modelPKL/scalerY.pkl', 'wb') as f:
            pickle.dump(scalerY, f)

        with open('./modelPKL/allPossibleCols.pkl', 'wb') as f:
            pickle.dump(allPossibleCols, f)

        print("Scalers and possible columns saved.")

# Define columns to be transformed and the target column
colsToTransform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
targetColumn = 'Bid Price'

# Initialize scalers
scalerX = StandardScaler()
scalerY = StandardScaler()

Path('./modelPKL').mkdir(parents=True, exist_ok=True)

# Daily incremental training for January
trainModelDailyIncremental(year=2022, month=1, startDay=1, endDay=31, pathPattern='./PKLData/2022/dfResultFinal_2022_01.pkl', modelSavePath='./modelPKL/monthlyModel.keras')

# # Function to train the model daily incrementally for a specific year
# def trainModelForYear(basePath, modelSaveBasePath, year):
#     print(f"\nTraining for year {year}...")
    
#     for month in range(1, 13):  # Months from January to December
#         # Get the number of days in the month
#         _, numDays = calendar.monthrange(year, month)
        
#         for day in range(1, numDays + 1):
#             print(f"\nTraining with data from {year}-{month:02d}-{day:02d}...")
            
#             pathPattern = f'{basePath}/{year}/dfResultFinal_{year}_{month:02d}.pkl'
#             modelSavePath = f'{modelSaveBasePath}/{year}_{month:02d}Model.keras'
            
#             # Train the model incrementally for the current day
#             trainModelDailyIncremental(year=year, month=month, startDay=day, endDay=day, pathPattern=pathPattern, modelSavePath=modelSavePath)

# # Define base path to data and model save path
# basePath = '../PKLData'
# modelSaveBasePath = './modelPKL'
# yearToTrain = 2022  # Specify the year to train

# # Train the model for the specified year
# trainModelForYear(basePath, modelSaveBasePath, yearToTrain)
