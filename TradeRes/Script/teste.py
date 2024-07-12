import pandas as pd

# Carregar o arquivo pickle de 2023
df2023 = pd.read_pickle('./PKLData/dfResultFinal2023.pkl')
print(df2023)
print(type(df2023.iloc[33801898]['Agent']))

# Remover linhas com valores ausentes do DataFrame df2023
df2023 = df2023.dropna()
# Imprimir o DataFrame resultante
print(df2023)

# Salvar o DataFrame resultante em um arquivo CSV
df2023.to_excel('df2023_cleaned.xlsx', index=False)

print("criado")