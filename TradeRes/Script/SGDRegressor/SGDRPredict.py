import pandas as pd
import joblib

# Função para prever o Bid Price
def predict_bid_price(year, month, day, hour, bidding_area, agent, unit, technology, country, capacity_2030, transaction_type, offered_matched, bid_energy):
    # Carregar o modelo e objetos necessários
    sgd_model = joblib.load('./modelPKL/sgd_model.pkl')
    scaler_X = joblib.load('./modelPKL/scaler_X.pkl')
    scaler_y = joblib.load('./modelPKL/scaler_y.pkl')
    imputer_X = joblib.load('./modelPKL/imputer_X.pkl')
    all_columns = joblib.load('./modelPKL/all_columns.pkl')  # Carregar as colunas do arquivo
    
    # Definir os valores de entrada em um DataFrame
    data = {
        'Year': [year],
        'Month': [month],
        'Day': [day],
        'Hour': [hour],
        'Bidding Area': [bidding_area],
        'Agent': [agent],
        'Unit': [unit],
        'Technology': [technology],
        'Country': [country],
        'Capacity_2030': [capacity_2030],
        'Transaction Type': [transaction_type],
        'Offered (O)/Matched (M)': [offered_matched],
        'Bid Energy': [bid_energy]
    }

    df = pd.DataFrame(data)

    # Definir as colunas a serem transformadas
    cols_to_transform = ['Bidding Area', 'Agent', 'Unit', 'Technology', 'Country', 'Transaction Type', 'Offered (O)/Matched (M)']

    # Fazer o get_dummies para as colunas categóricas
    df_dummies = pd.get_dummies(df, columns=cols_to_transform)

    # Garantir que as colunas no conjunto de previsão correspondam às colunas usadas no treino
    df_dummies = df_dummies.reindex(columns=all_columns, fill_value=0)

    # Verificar se a coluna 'Bid Price' está presente e removê-la
    if 'Bid Price' in df_dummies.columns:
        df_dummies = df_dummies.drop(columns=['Bid Price'])

    print(df_dummies)  # Para depuração

    # Separar as features (X)
    X_to_predict = df_dummies

    # Imputar valores faltantes
    X_to_predict = imputer_X.transform(X_to_predict)

    # Escalar os dados
    X_to_predict_scaled = scaler_X.transform(X_to_predict)

    # Fazer a previsão com o modelo
    y_pred_scaled = sgd_model.predict(X_to_predict_scaled)

    # Inverter a escala da previsão para o valor original do Bid Price
    y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()

    return y_pred[0]

# Exemplo de uso
if __name__ == "__main__":
    # Definir os parâmetros de entrada com base no exemplo fornecido
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

    # Prever o Bid Price
    bid_price_predicted = predict_bid_price(year, month, day, hour, bidding_area, agent, unit, technology, country, capacity_2030, transaction_type, offered_matched, bid_energy)

    print(f"Bid Price previsto: {bid_price_predicted}")
