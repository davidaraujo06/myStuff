import numpy as np
import pandas as pd
import pickle
import tensorflow as tf

# Função para preparar os dados de previsão
def prepare_input_data(year, month, day, hour, bidding_area, agent, unit, technology, country, capacity_2030, transaction_type, offered_matched, bid_energy, all_possible_cols):
    # Criar um DataFrame com os dados de entrada
    input_data = pd.DataFrame({
        'Year': [year],
        'Month': [month],
        'Day': [day],
        'Hour': [hour],
        'Bidding Area': [bidding_area],
        'Agent': [agent],
        'Unit': [unit],
        'Technology': [technology],
        'Country': [country],
        'Capacity 2030': [capacity_2030],
        'Transaction Type': [transaction_type],
        'Offered (O)/Matched (M)': [offered_matched],
        'Bid Energy': [bid_energy]
    })

    # Aplicar pd.get_dummies para as colunas categóricas
    input_dummies = pd.get_dummies(input_data, columns=['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)'])

    # Garantir que todas as colunas possíveis estejam presentes
    missing_cols = set(all_possible_cols) - set(input_dummies.columns)
    for col in missing_cols:
        input_dummies[col] = 0
    
    # Garantir que a ordem das colunas esteja correta
    input_dummies = input_dummies[all_possible_cols]

    return input_dummies

# Função para fazer previsões
def predict_price(year, month, day, hour, bidding_area, agent, unit, technology, country, capacity_2030, transaction_type, offered_matched, bid_energy, model_path):
    # Carregar os scalers e as colunas possíveis
    with open('./modelPKL/scaler_X.pkl', 'rb') as f:
        scaler_X = pickle.load(f)

    with open('./modelPKL/scaler_y.pkl', 'rb') as f:
        scaler_y = pickle.load(f)

    with open('./modelPKL/all_possible_cols.pkl', 'rb') as f:
        all_possible_cols = pickle.load(f)

    print("Scalers e colunas possíveis carregados.")

    # Preparar os dados de entrada
    input_data = prepare_input_data(year, month, day, hour, bidding_area, agent, unit, technology, country, capacity_2030, transaction_type, offered_matched, bid_energy, all_possible_cols)
    
    # Escalar os dados de entrada
    input_scaled = scaler_X.transform(input_data)

    # Ajustar a forma dos dados para o formato esperado pela CNN
    input_reshaped = np.expand_dims(input_scaled, axis=2)

    # Carregar o modelo treinado
    model = tf.keras.models.load_model(model_path)

    # Fazer a previsão
    prediction_scaled = model.predict(input_reshaped)

    # Reverter a escala da previsão
    prediction = scaler_y.inverse_transform(prediction_scaled.reshape(-1, 1))

    return prediction[0][0]

# Exemplo de valores de entrada
year = 2023
month = 1
day = 2
hour = 8
bidding_area = "MI"
agent = "EGLE"
unit = "EGVD086"
technology = "Wind Onshore"
country = "ES"
capacity_2030 = 22.516331
transaction_type = "Sell"
offered_matched = "C"
bid_energy = 3.0

# Caminho do modelo treinado
model_path = './modelPKL/monthly_model.keras'

# Fazer a previsão
preco_previsto = predict_price(year, month, day, hour, bidding_area, agent, unit, technology, country, capacity_2030, transaction_type, offered_matched, bid_energy, model_path)

print(f"O preço previsto é: {preco_previsto}")
