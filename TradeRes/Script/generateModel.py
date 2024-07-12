import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

# Carregar o arquivo pickle de 2022
pickle_file_2022 = './PKLData/dfResultFinal2022.pkl'
df_2022 = pd.read_pickle(pickle_file_2022)

# Carregar o arquivo pickle de 2023
pickle_file_2023 = './PKLData/dfResultFinal2023.pkl'
df_2023 = pd.read_pickle(pickle_file_2023)

# Transformar as colunas especificadas em dummies para 2022 e 2023
cols_to_transform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Capacity_2030', 'Transaction Type', 'Offered (O)/Matched (M)']
df_2022_dummies = pd.get_dummies(df_2022, columns=cols_to_transform)
df_2023_dummies = pd.get_dummies(df_2023, columns=cols_to_transform)

# Garantir que ambos os DataFrames têm as mesmas colunas
df_2022_dummies, df_2023_dummies = df_2022_dummies.align(df_2023_dummies, join='left', axis=1, fill_value=0)

# Definir a variável alvo (y) e as características (X)
# Supondo que a variável alvo seja chamada de 'PricePT' (substitua pelo nome real)
target_column = 'Bid Price'
X_train = df_2022_dummies.drop(columns=[target_column])
y_train = df_2022_dummies[target_column]
X_test = df_2023_dummies.drop(columns=[target_column])
y_test = df_2023_dummies[target_column]

# Normalizar os dados
scaler_X = StandardScaler()
scaler_y = StandardScaler()

X_train_scaled = scaler_X.fit_transform(X_train)
X_test_scaled = scaler_X.transform(X_test)
y_train_scaled = scaler_y.fit_transform(y_train.values.reshape(-1, 1)).ravel()
y_test_scaled = scaler_y.transform(y_test.values.reshape(-1, 1)).ravel()

# Treinar o modelo SVR
svr_model = SVR()
svr_model.fit(X_train_scaled, y_train_scaled)

# Fazer previsões
y_pred_scaled = svr_model.predict(X_test_scaled)
y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()

# Avaliar o modelo
mse = mean_squared_error(y_test, y_pred)
print(f'Mean Squared Error: {mse}')

# Exibir algumas previsões
print("\nPrevisões vs Valores Reais:")
print(pd.DataFrame({'Real': y_test, 'Previsto': y_pred}).head())
