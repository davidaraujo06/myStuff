import os
import glob
import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
import numpy as np

# Função para carregar e processar arquivos em lotes
def load_and_process_files_in_batches(path_pattern, cols_to_transform, target_column, all_columns, batch_size=100000):
    all_files = glob.glob(path_pattern)
    for file in all_files:
        print(f"Processando arquivo: {file}")
        df = pd.read_pickle(file)
        for start in range(0, len(df), batch_size):
            chunk = df.iloc[start:start + batch_size]
            # Tratamento de variáveis categóricas
            df_dummies = pd.get_dummies(chunk, columns=cols_to_transform)
            df_dummies = df_dummies.reindex(columns=all_columns, fill_value=0)
            X = df_dummies.drop(columns=[target_column])
            y = df_dummies[target_column]
            yield X, y

# Definir colunas a serem transformadas e a coluna alvo
cols_to_transform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
target_column = 'Bid Price'

# Criar a pasta se não existir para salvar o modelo
Path('./modelPKL').mkdir(parents=True, exist_ok=True)

# Carregar um lote inicial para determinar todas as possíveis colunas
initial_batch_path = glob.glob('../PKLDataTeste/2022/dfResultFinal_2022_*.pkl')[0]
initial_df = pd.read_pickle(initial_batch_path).iloc[:100000]
all_columns = pd.get_dummies(initial_df, columns=cols_to_transform).columns

# Salvar a lista de colunas usadas no treinamento
joblib.dump(all_columns, './modelPKL/all_columns.pkl')

# Inicializar pipeline de pré-processamento e o modelo RandomForestRegressor
pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler()),
    ('regressor', RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42))
])

# Função para avaliar o modelo com métricas apropriadas
def evaluate_model(model, X_val, y_val):
    y_pred = model.predict(X_val)
    mse = mean_squared_error(y_val, y_pred)
    rmse = np.sqrt(mse)
    return rmse
# Função para remover NaNs em y e os respectivos registros em X
def remove_nan_in_target(X, y):
    # Remover os registros onde y tem NaN
    valid_indices = ~y.isna()
    X_clean = X[valid_indices]
    y_clean = y[valid_indices]
    return X_clean, y_clean

# Processar dados de treinamento em lotes e treinar o modelo
print("Processando dados de treinamento...")
train_batches = load_and_process_files_in_batches('../PKLDataTeste/2022/dfResultFinal_2022_*.pkl', cols_to_transform, target_column, all_columns)

batch_count = 0
rmse_scores = []

for X_train_batch, y_train_batch in train_batches:
    batch_count += 1
    print(f"Treinando no lote {batch_count}...")

    # Remover NaNs em y
    X_train_batch, y_train_batch = remove_nan_in_target(X_train_batch, y_train_batch)

    # Verificar se há amostras suficientes após a remoção de NaNs
    if len(y_train_batch) == 0:
        print(f"O lote {batch_count} está vazio após a remoção de NaNs. Pulando...")
        continue

    # Dividir o lote em treino e validação (70% treino, 30% validação)
    X_train, X_val, y_train, y_val = train_test_split(X_train_batch, y_train_batch, train_size=0.7, random_state=42)
    
    # Treinar o modelo no lote atual
    pipeline.fit(X_train, y_train)

    # Avaliar o modelo no conjunto de validação
    rmse = evaluate_model(pipeline, X_val, y_val)
    rmse_scores.append(rmse)
    print(f"RMSE para o lote {batch_count}: {rmse:.4f}")
    
    # Opcional: Liberar memória para garantir que não sobrecarregue o sistema
    del X_train, X_val, y_train, y_val
    del X_train_batch, y_train_batch

# Salvar o modelo treinado, scalers e imputers
joblib.dump(pipeline, './modelPKL/random_forest_pipeline.pkl')

# Imprimir a avaliação geral
mean_rmse = np.mean(rmse_scores)
print(f"Treinamento concluído. RMSE médio: {mean_rmse:.4f}")