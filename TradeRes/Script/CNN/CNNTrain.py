from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import glob
import os
import pickle  
import tensorflow as tf

# Função para carregar e processar dados até a data especificada
def load_data_for_day(path_pattern, cols_to_transform, target_column, year, month, day, all_possible_cols=None):
    all_files = glob.glob(path_pattern)
    data = []
    target = []

    for file in all_files:
        print(f"Processando arquivo: {file}")
        df = pd.read_pickle(file)

        # Verificar se a coluna alvo está presente
        if target_column not in df.columns:
            raise KeyError(f"A coluna '{target_column}' não foi encontrada no arquivo {file}.")

        # Filtrar os dados para aquele dia específico
        df = df[(df['Year'] == year) & (df['Month'] == month) & (df['Day'] == day)]
        
        # Separar a coluna alvo
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
    
    return model

# Função para treinar o modelo diariamente de forma acumulativa
def train_model_daily_acumulativo(year, month, start_day, end_day, model_save_path):
    all_possible_cols = None

    for day in range(start_day, end_day + 1):
        print(f"\nTreinando com dados do dia {day}...")

        path_pattern = f'../PKLDataTeste/{year}/dfResultFinal_{year}_{month}.pkl'
        
        # Carregar dados do dia atual
        X, y = load_data_for_day(path_pattern, cols_to_transform, target_column, year, month, day, all_possible_cols)


        if all_possible_cols is None:
            all_possible_cols = X.columns


        # Escalar os dados
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1)).ravel()

        # Dividir em treino e validação
        X_train, X_val, y_train, y_val = train_test_split(X_scaled, y_scaled, train_size=0.7, random_state=42)

        # Ajustar forma dos dados para a CNN
        X_train_reshaped = np.expand_dims(X_train, axis=2)
        X_val_reshaped = np.expand_dims(X_val, axis=2)

        # Carregar modelo completo, incluindo otimizador
        if os.path.exists(model_save_path):
            model = tf.keras.models.load_model(model_save_path)  # Carregar modelo completo (com otimizador)
            print("Modelo completo carregado")
        else:
            model = build_model(input_shape=(X_train_reshaped.shape[1], 1))
            model.compile(optimizer='adam', loss='mean_squared_error')
            print("Novo modelo criado")


        # Treinar o modelo com os dados do dia atual (incrementalmente)
        model.fit(X_train_reshaped, y_train, epochs=2, batch_size=32, validation_data=(X_val_reshaped, y_val))
        
        # Salvar os pesos do modelo após o treino diário
        # Salvar modelo completo
        model.save(model_save_path)

        print(f"Modelo salvo em {model_save_path}")
            # Salvar os scalers e as colunas após o treinamento completo

        with open('./modelPKL/scaler_X.pkl', 'wb') as f:
            pickle.dump(scaler_X, f)

        with open('./modelPKL/scaler_y.pkl', 'wb') as f:
            pickle.dump(scaler_y, f)

        with open('./modelPKL/all_possible_cols.pkl', 'wb') as f:
            pickle.dump(all_possible_cols, f)

        print("Scalers e colunas possíveis salvos.")

# Definir colunas a serem transformadas e a coluna alvo
cols_to_transform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']
target_column = 'Bid Price'

# Inicializar scalers
scaler_X = StandardScaler()
scaler_y = StandardScaler()

# Treinamento diário acumulativo para o mês de janeiro
train_model_daily_acumulativo(year=2022, month=1, start_day=1, end_day=31, model_save_path='./modelPKL/monthly_model.keras')
