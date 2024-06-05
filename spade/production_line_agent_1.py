from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from datetime import datetime, timedelta
from utils import *
import json, asyncio

class LinhaProducaoOntologia:
    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao1Agent(Agent):

    class WaitForReadyBehav(OneShotBehaviour):
        async def run(self):
            while True:
                msg = await self.receive(timeout=10)
                if msg.body=="pronto" and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                    self.agent.ready_agents.add(str(msg.sender))
                    print(f"Recebido pronto de {msg.sender}")
                    if len(self.agent.ready_agents) == 2:
                        self.agent.add_behaviour(self.agent.ProposeEncomendaBehav())
                        break


    class ProposeEncomendaBehav(OneShotBehaviour):
        async def run(self):
            data_atual = datetime.now()

            encomendas = [
                {
                    "clientes": {
                        "Cliente A": {"prioridade": "Alta", "quantidade": 100, "tempo_finalizacao": 120, "prazo_entrega": (data_atual + timedelta(days=5)).strftime('%Y-%m-%d')},
                        "Cliente B": {"prioridade": "Media", "quantidade": 50, "tempo_finalizacao": 240, "prazo_entrega": (data_atual + timedelta(days=10)).strftime('%Y-%m-%d')},
                        "Cliente C": {"prioridade": "Baixa", "quantidade": 200, "tempo_finalizacao": 420, "prazo_entrega": (data_atual + timedelta(days=15)).strftime('%Y-%m-%d')},
                        "Cliente D": {"prioridade": "Alta", "quantidade": 150, "tempo_finalizacao": 180, "prazo_entrega": (data_atual + timedelta(days=6)).strftime('%Y-%m-%d')},
                        "Cliente E": {"prioridade": "Media", "quantidade": 80, "tempo_finalizacao": 300, "prazo_entrega": (data_atual + timedelta(days=12)).strftime('%Y-%m-%d')},
                    },
                    "rateDefeitos": 100
                }
            ]

            # # Loop para verificar se há encomendas
            # while not encomendas:
            #     print("Aguardando encomendas...")
            #     await asyncio.sleep(900)  # Aguarda 15 minutos antes de verificar novamente

            print(f"{self.agent.jid}: Enviando mensagem de posposta...")
            await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", encomendas, LinhaProducaoOntologia.PROPOSE)  
            self.agent.add_behaviour(self.agent.RecebeRespostaLinha2())

    class RecebeRespostaLinha2(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Aguardando decisão da linha 2...")
            await asyncio.sleep(10)
            msg = await self.receive(timeout=20)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                print(f"{self.agent.jid}: Recebeu a seguinte decisão:  \n{msg.body}")  
                if json.loads(msg.body)["best"]=="linha1@jabbers.one":
                    print("enviar mensagem á linha 3")


    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.ready_agents = set()
        self.add_behaviour(self.WaitForReadyBehav())
