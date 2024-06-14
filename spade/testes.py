import asyncio
from datetime import datetime, timedelta

async def encomenda_prioritaria(clientes, posicao):
    print("aqui")
    prioridade_ordem = {"Alta": 1, "Media": 2, "Baixa": 3}
    
    print(clientes)
    # Ordena os clientes por prioridade e prazo de entrega
    clientes_ordenados = sorted(clientes.keys(), key=lambda cliente: (
        prioridade_ordem[clientes[cliente]["prioridade"]],
        datetime.strptime(clientes[cliente]["prazo_entrega"], '%Y-%m-%d')
    ))
    print(clientes_ordenados)
    
    # Retorna o cliente correspondente à posição desejada
    cliente_prioritario = clientes_ordenados[posicao - 1]
    print(clientes[cliente_prioritario])
    return clientes[cliente_prioritario]

# Iniciando a execução da função run()
data_atual = datetime.now()
encomendas = [
                {
                    "clientes": {
                        "Cliente A": {"tipo": "Granulado", "prioridade": "Alta", "quantidade": 100, "tempo_finalizacao": 120, "prazo_entrega": (data_atual + timedelta(days=5)).strftime('%Y-%m-%d')},
                        "Cliente B": {"tipo": "Micro-Granulado","prioridade": "Media", "quantidade": 50, "tempo_finalizacao": 240, "prazo_entrega": (data_atual + timedelta(days=10)).strftime('%Y-%m-%d')},
                        "Cliente C": {"tipo": "Granulado","prioridade": "Baixa", "quantidade": 200, "tempo_finalizacao": 420, "prazo_entrega": (data_atual + timedelta(days=15)).strftime('%Y-%m-%d')},
                        "Cliente D": {"tipo": "Micro-Granulado","prioridade": "Alta", "quantidade": 150, "tempo_finalizacao": 180, "prazo_entrega": (data_atual + timedelta(days=6)).strftime('%Y-%m-%d')},
                        "Cliente E": {"tipo": "Granulado","prioridade": "Media", "quantidade": 80, "tempo_finalizacao": 300, "prazo_entrega": (data_atual + timedelta(days=12)).strftime('%Y-%m-%d')}
                    },
                    "rateDefeitos": 10
                }
            ]
asyncio.run(encomenda_prioritaria(encomendas[0]["clientes"], 2))
