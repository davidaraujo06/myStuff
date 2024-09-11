import pandas as pd
import glob
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import numpy as np

# Carregar o pipeline salvo
pipeline = joblib.load('./modelPKL/random_forest_pipeline.pkl')
all_columns = joblib.load('./modelPKL/all_columns.pkl')

# Função para carregar e processar arquivos em lotes
def load_and_process_files_in_batches(path_pattern, cols_to_transform, target_column, all_columns, batch_size=100000):
    all_files = glob.glob(path_pattern)
    for file in all_files:
        print(f"Processando arquivo: {file}")
        df = pd.read_pickle(file)
        for start in range(0, len(df), batch_size):
            chunk = df.iloc[start:start + batch_size]
            df_dummies = pd.get_dummies(chunk, columns=cols_to_transform)
            df_dummies = df_dummies.reindex(columns=all_columns, fill_value=0)
            X = df_dummies.drop(columns=[target_column])
            y = df_dummies[target_column]
            yield X, y

# Colunas a serem transformadas e coluna alvo
cols_to_transform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
target_column = 'Bid Price'

# Processar dados de teste em lotes e avaliar o modelo
print("Processando dados de teste...")
test_batches = load_and_process_files_in_batches('../PKLDataTeste/2023/dfResultFinal_2023_*.pkl', cols_to_transform, target_column, all_columns)

# Listas para armazenar as métricas de cada lote
mse_list = []
mae_list = []
rmse_list = []
r2_list = []

for X_test_batch, y_test_batch in test_batches:
    # Dividir o lote em treino e teste (70% treino, 30% teste)
    X_train_batch, X_test_batch, y_train_batch, y_test_batch = train_test_split(
        X_test_batch, y_test_batch, train_size=0.7, random_state=42
    )
    
    # Prever com o pipeline carregado (o pipeline já faz a imputação e o escalonamento)
    y_pred = pipeline.predict(X_test_batch)
    
    # Calcular as métricas
    mse = mean_squared_error(y_test_batch, y_pred)
    mae = mean_absolute_error(y_test_batch, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test_batch, y_pred)
    
    # Armazenar as métricas para o lote atual
    mse_list.append(mse)
    mae_list.append(mae)
    rmse_list.append(rmse)
    r2_list.append(r2)

# Calcular a média das métricas de todos os lotes
mean_mse = np.mean(mse_list)
mean_mae = np.mean(mae_list)
mean_rmse = np.mean(rmse_list)
mean_r2 = np.mean(r2_list)

# Imprimir as métricas finais
print(f"Mean Squared Error (MSE): {mean_mse:.4f}")
print(f"Mean Absolute Error (MAE): {mean_mae:.4f}")
print(f"Root Mean Squared Error (RMSE): {mean_rmse:.4f}")
print(f"R² Score: {mean_r2:.4f}")
