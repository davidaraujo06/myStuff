import pandas as pd
import glob
import joblib
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

# Carregar o modelo e os objetos necessários
linear_model = joblib.load('./modelPKL/linear_model.pkl')
scaler_X = joblib.load('./modelPKL/scaler_X.pkl')
imputer_X = joblib.load('./modelPKL/imputer_X.pkl')
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

cols_to_transform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
target_column = 'Bid Price'

# Processar dados de teste em lotes e avaliar o modelo
print("Processando dados de teste...")
test_batches = load_and_process_files_in_batches('../PKLDataTeste/2023/dfResultFinal_2023_*.pkl', cols_to_transform, target_column, all_columns)

mse_list = []

for X_test_batch, y_test_batch in test_batches:
    # Dividir o lote em treino e teste (70% treino, 30% teste)
    X_train_batch, X_test_batch, y_train_batch, y_test_batch = train_test_split(
        X_test_batch, y_test_batch, train_size=0.7, random_state=42
    )
    
    # Imputar valores ausentes
    X_test_batch = imputer_X.transform(X_test_batch)
    
    # Escalonar os dados
    X_test_scaled = scaler_X.transform(X_test_batch)
    
    # Prever e calcular o MSE para o lote
    y_pred = linear_model.predict(X_test_scaled)
    mse = mean_squared_error(y_test_batch, y_pred)
    mse_list.append(mse)

# Calcular e imprimir o MSE médio para todos os lotes de teste
mean_mse = sum(mse_list) / len(mse_list)
print(f"Mean Squared Error: {mean_mse}")
