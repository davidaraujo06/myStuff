import json
from datetime import datetime, timedelta
import asyncio

# Função para carregar encomendas do arquivo JSON
def carregar_encomendas(filename):
    with open(filename, 'r') as file:
        return json.load(file)

# Função para salvar encomendas no arquivo JSON
def salvar_encomendas(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Função assíncrona para obter e remover a encomenda prioritária
async def encomenda_prioritaria(filename, posicao):
    # Carrega os dados dos clientes
    data = carregar_encomendas(filename)
    clientes = data["clientes"]
    
    prioridade_ordem = {"Alta": 1, "Media": 2, "Baixa": 3}
    
    # Ordena os clientes por prioridade e prazo de entrega
    clientes_ordenados = sorted(clientes.keys(), key=lambda cliente: (
        prioridade_ordem[clientes[cliente]["prioridade"]],
        datetime.strptime(clientes[cliente]["prazo_entrega"], '%Y-%m-%d')
    ))
    
    # Imprime a lista de clientes antes da remoção
    print("Clientes antes da remoção:", list(clientes.keys()))
    
    # Seleciona o cliente correspondente à posição desejada
    cliente_prioritario = clientes_ordenados[posicao - 1]
    encomenda_prioritaria = clientes.pop(cliente_prioritario)
    
    # Salva as alterações no arquivo JSON
    salvar_encomendas(filename, data)
    
    # Imprime a lista de clientes após a remoção
    print("Clientes após a remoção:", list(clientes.keys()))
    
    return encomenda_prioritaria

# Função para verificar se uma encomenda foi removida
def verificar_remocao(filename, cliente):
    data = carregar_encomendas(filename)
    return cliente not in data["clientes"]

# Exemplo de uso da função assíncrona
async def main():
    filename = 'encomendas.json'
    posicao = 1  # Posição desejada
    encomenda = await encomenda_prioritaria(filename, posicao)
    print(f"Encomenda prioritária: {encomenda}")
    
    # Verifica se a encomenda foi removida
    cliente_removido = list(encomenda.keys())[0]
    if verificar_remocao(filename, cliente_removido):
        print(f"Encomenda do cliente '{cliente_removido}' foi removida com sucesso.")
    else:
        print(f"Falha ao remover a encomenda do cliente '{cliente_removido}'.")

# Executa o exemplo
if __name__ == "__main__":
    asyncio.run(main())
