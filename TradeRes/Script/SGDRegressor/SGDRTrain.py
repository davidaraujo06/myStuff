import pandas as pd
import glob
import joblib
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from pathlib import Path
from sklearn.model_selection import train_test_split

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

# Definir colunas a serem transformadas e a coluna alvo
cols_to_transform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
target_column = 'Bid Price'

# Inicializar scalers e imputers
scaler_X = StandardScaler()
scaler_y = StandardScaler()
imputer_X = SimpleImputer(strategy='mean')
imputer_y = SimpleImputer(strategy='mean')

# Inicializar o modelo SGDRegressor
sgd_model = SGDRegressor()

# Carregar um lote inicial para determinar todas as possíveis colunas
initial_batch_path = glob.glob('../PKLDataTeste/2022/dfResultFinal_2022_*.pkl')[0]
initial_df = pd.read_pickle(initial_batch_path).iloc[:100000]
all_columns = pd.get_dummies(initial_df, columns=cols_to_transform).columns

# Criar a pasta se não existir
Path('./modelPKL').mkdir(parents=True, exist_ok=True)
# Salvar a lista de colunas usadas no treinamento
joblib.dump(all_columns, './modelPKL/all_columns.pkl')

# Processar dados de treinamento em lotes e treinar o modelo incrementalmente
print("Processando dados de treinamento...")
train_batches = load_and_process_files_in_batches('../PKLDataTeste/2022/dfResultFinal_2022_*.pkl', cols_to_transform, target_column, all_columns)

for X_train_batch, y_train_batch in train_batches:
    # Dividir o lote em treino e validação (70% treino, 30% validação)
    X_train, X_val, y_train, y_val = train_test_split(X_train_batch, y_train_batch, train_size=0.7, random_state=42)
    
    # Imputar valores ausentes
    X_train = imputer_X.fit_transform(X_train)
    y_train = imputer_y.fit_transform(y_train.values.reshape(-1, 1)).ravel()
    
    # Escalar os dados
    X_train_scaled = scaler_X.fit_transform(X_train)
    y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).ravel()

    # Treinar o modelo incrementalmente
    sgd_model.partial_fit(X_train_scaled, y_train_scaled)

# Salvar o modelo treinado, scalers e imputers
joblib.dump(sgd_model, './modelPKL/sgd_model.pkl')
joblib.dump(scaler_X, './modelPKL/scaler_X.pkl')
joblib.dump(scaler_y, './modelPKL/scaler_y.pkl')
joblib.dump(imputer_X, './modelPKL/imputer_X.pkl')
joblib.dump(imputer_y, './modelPKL/imputer_y.pkl')

print("Modelo treinado e salvo com sucesso.")