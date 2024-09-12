import pandas as pd
import numpy as np
import glob
import os
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf

# Função para carregar e processar dados
def load_data_until_date(path_pattern, cols_to_transform, target_column, year, month, day, all_possible_cols=None):
    all_files = glob.glob(path_pattern)
    data = []
    target = []

    for file in all_files:
        print(f"Processando arquivo: {file}")
        df = pd.read_pickle(file)

        # Verificar se a coluna alvo está presente
        if target_column not in df.columns:
            raise KeyError(f"A coluna '{target_column}' não foi encontrada no arquivo {file}.")

        # Filtrar os dados até o dia especificado
        df = df[(df['Year'] == year) & (df['Month'] == month) & (df['Day'] <= day)]
        
        # Separar a coluna alvo ANTES de aplicar pd.get_dummies
        y = df[target_column]
        X = df.drop(columns=[target_column])

        # Aplicar a transformação para variáveis dummy
        X_dummies = pd.get_dummies(X, columns=cols_to_transform)

        # Garantir que todos os dias tenham as mesmas colunas
        if all_possible_cols is not None:
            missing_cols = set(all_possible_cols) - set(X_dummies.columns)
            for col in missing_cols:
                X_dummies[col] = 0
            X_dummies = X_dummies[all_possible_cols]

        if X_dummies.isna().any().any() or y.isna().any():
            X_dummies.fillna(0.0, inplace=True)
            y.fillna(0.0, inplace=True)

        data.append(X_dummies)
        target.append(y)

    if data:  # Verificar se há dados
        X_all = pd.concat(data, ignore_index=True)
        y_all = pd.concat(target, ignore_index=True)
    else:
        raise ValueError("Nenhum dado foi carregado após o filtro. Verifique os critérios.")

    return X_all, y_all

# Definir colunas a serem transformadas e a coluna alvo
cols_to_transform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
target_column = 'Bid Price'

# Inicializar scalers
scaler_X = StandardScaler()
scaler_y = StandardScaler()

# Função para criar o modelo
def build_model(input_shape):
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape),
        tf.keras.layers.MaxPooling1D(pool_size=2),
        tf.keras.layers.Conv1D(filters=128, kernel_size=3, activation='relu'),
        tf.keras.layers.MaxPooling1D(pool_size=2),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.5), 
        tf.keras.layers.Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# Função para treinar o modelo diariamente de forma acumulativa
def train_model_daily_acumulativo(year, month, start_day, end_day, model_save_path):
    all_possible_cols = None
    X_accumulated = []  # Para acumular os dados de entrada
    y_accumulated = []  # Para acumular os dados de saída

    for day in range(start_day, end_day + 1):
        print(f"\nTreinando com dados até o dia {day}...")

        path_pattern = f'../PKLDataTeste/{year}/dfResultFinal_{year}_{month}.pkl'
        
        # Carregar dados até o dia atual
        X, y = load_data_until_date(path_pattern, cols_to_transform, target_column, year, month, day, all_possible_cols)

        if all_possible_cols is None:
            all_possible_cols = X.columns

        # Acumular os dados ao longo dos dias
        X_accumulated.append(X)
        y_accumulated.append(y)

        # Concatenar dados acumulados
        X_concat = pd.concat(X_accumulated, ignore_index=True)
        y_concat = pd.concat(y_accumulated, ignore_index=True)

        # Escalar os dados
        X_scaled = scaler_X.fit_transform(X_concat)
        y_scaled = scaler_y.fit_transform(y_concat.values.reshape(-1, 1)).ravel()

        # Dividir em treino e validação
        X_train, X_val, y_train, y_val = train_test_split(X_scaled, y_scaled, train_size=0.7, random_state=42)

        # Ajustar forma dos dados para a CNN
        X_train_reshaped = np.expand_dims(X_train, axis=2)
        X_val_reshaped = np.expand_dims(X_val, axis=2)

        # Criar ou carregar o modelo
        if os.path.exists(model_save_path):
            try:
                model = tf.keras.models.load_model(model_save_path)
                print("Modelo carregado")
                
                # Verificar compatibilidade da entrada
                if model.input_shape[1] != X_train_reshaped.shape[1]:
                    print("A forma de entrada mudou. Reconstruindo o modelo...")
                    model = build_model(input_shape=(X_train_reshaped.shape[1], 1))

            except ValueError as e:
                print(f"Erro ao carregar o modelo: {e}")
                model = build_model(input_shape=(X_train_reshaped.shape[1], 1))
                print("Modelo criado")
        else:
            model = build_model(input_shape=(X_train_reshaped.shape[1], 1))
            print("Modelo criado")
        
        # Treinar o modelo
        model.fit(X_train_reshaped, y_train, epochs=2, batch_size=32, validation_data=(X_val_reshaped, y_val))
        
        # Salvar o modelo
        model.save(model_save_path)
        print(f"Modelo salvo em {model_save_path}")

# Treinamento diário acumulativo para o mês de janeiro
train_model_daily_acumulativo(year=2022, month=1, start_day=1, end_day=31, model_save_path='./modelPKL/monthly_model.keras')
