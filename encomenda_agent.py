from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from datetime import datetime, timedelta
import json

class EncomendaOntologia:
    ENCOMENDA = "encomenda"
    PRONTO = "pronto"

class EncomendaAgent(Agent):
    class WaitForReadyBehav(OneShotBehaviour):
        async def run(self):
            while True:
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == EncomendaOntologia.PRONTO:
                    self.agent.ready_agents.add(str(msg.sender))
                    print(f"Recebido pronto de {msg.sender}")
                    if len(self.agent.ready_agents) == 3:
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

            linhas_producao = ["linha1@jabbers.one", "linha2@jabbers.one", "linha3@jabbers.one"]

            for linha in linhas_producao:
                await self.send_encomenda(linha, encomendas)

        async def send_encomenda(self, linha_producao, encomenda):
            msg = Message(to=linha_producao)
            msg.set_metadata("performative", EncomendaOntologia.ENCOMENDA)
            msg.body = json.dumps(encomenda)
            await self.send(msg)

    async def setup(self):
        print(f"Encomenda agent {self.jid} inicializado.")
        self.ready_agents = set()
        self.add_behaviour(self.WaitForReadyBehav())