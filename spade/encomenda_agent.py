from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from datetime import datetime, timedelta
from utils import *
import asyncio

class EncomendaOntologia:
    REQUEST = "request"
    INFORM = "inform"

class EncomendaAgent(Agent):
    class WaitForReadyBehav(OneShotBehaviour):
        async def run(self):
            while True:
                msg = await self.receive(timeout=10)
                if msg.body=="pronto" and msg.metadata["performative"] == EncomendaOntologia.INFORM:
                    self.agent.ready_agents.add(str(msg.sender))
                    print(f"Recebido pronto de {msg.sender}")
                    if len(self.agent.ready_agents) == 2:
                        self.agent.add_behaviour(self.agent.SendEncomendaBehav())
                        break


    class SendEncomendaBehav(OneShotBehaviour):

        async def run(self):
            data_atual = datetime.now()

            encomendas = [
                {"cliente": "Cliente A", "prioridade": "Alta", "quantidade": 100, "tempo_finalizacao": 120, "prazo_entrega": (data_atual + timedelta(days=5)).strftime('%Y-%m-%d')},
                {"cliente": "Cliente B", "prioridade": "Media", "quantidade": 50, "tempo_finalizacao": 240, "prazo_entrega": (data_atual + timedelta(days=10)).strftime('%Y-%m-%d')},
                {"cliente": "Cliente C", "prioridade": "Baixa", "quantidade": 200, "tempo_finalizacao": 420, "prazo_entrega": (data_atual + timedelta(days=15)).strftime('%Y-%m-%d')},
                {"cliente": "Cliente D", "prioridade": "Alta", "quantidade": 150, "tempo_finalizacao": 180, "prazo_entrega": (data_atual + timedelta(days=6)).strftime('%Y-%m-%d')},
                {"cliente": "Cliente E", "prioridade": "Media", "quantidade": 80, "tempo_finalizacao": 300, "prazo_entrega": (data_atual + timedelta(days=12)).strftime('%Y-%m-%d')}
            ]

            linhas_producao = ["linha1@jabbers.one", "linha2@jabbers.one"]

            # Enviar mensagens para as linhas de produção quando houver encomendas
            for linha in linhas_producao:
                await sendMessage(self, self.agent.jid, linha, "performative", encomendas, EncomendaOntologia.REQUEST)

            encomendas.clear() 
            # Loop para verificar se há encomendas
            while not encomendas:
                print("Aguardando encomendas...")
                await asyncio.sleep(900)  # Aguarda 15 minutos antes de verificar novamente


    async def setup(self):
        print(f"Encomenda agent {self.jid} inicializado.")
        self.ready_agents = set()
        self.add_behaviour(self.WaitForReadyBehav())