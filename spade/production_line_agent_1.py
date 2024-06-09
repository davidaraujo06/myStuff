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

# trocar para ciclyc e retirar o while
    class ProposeEncomendaBehav(OneShotBehaviour):
        async def run(self):
            data_atual = datetime.now()
            global encomendas
            encomendas = [
                {
                    "clientes": {
                        "Cliente A": {"prioridade": "Alta", "quantidade": 100, "tempo_finalizacao": 120, "prazo_entrega": (data_atual + timedelta(days=5)).strftime('%Y-%m-%d')},
                        "Cliente B": {"prioridade": "Media", "quantidade": 50, "tempo_finalizacao": 240, "prazo_entrega": (data_atual + timedelta(days=10)).strftime('%Y-%m-%d')},
                        "Cliente C": {"prioridade": "Baixa", "quantidade": 200, "tempo_finalizacao": 420, "prazo_entrega": (data_atual + timedelta(days=15)).strftime('%Y-%m-%d')},
                        "Cliente D": {"prioridade": "Alta", "quantidade": 150, "tempo_finalizacao": 180, "prazo_entrega": (data_atual + timedelta(days=6)).strftime('%Y-%m-%d')},
                        "Cliente E": {"prioridade": "Media", "quantidade": 80, "tempo_finalizacao": 300, "prazo_entrega": (data_atual + timedelta(days=12)).strftime('%Y-%m-%d')},
                    },
                    "rateDefeitos": 10
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
            await asyncio.sleep(10)
            print(f"{self.agent.jid}: Aguardando decisão da linha 2...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                if json.loads(msg.body)["best"]=="linha1@jabbers.one":
                    await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", encomendas, LinhaProducaoOntologia.PROPOSE)
                    self.agent.add_behaviour(self.agent.RecebeRespostaLinha3())
                else:
                    self.agent.add_behaviour(self.agent.RecebeDecisaoFinalLinha2())    

    class RecebeRespostaLinha3(OneShotBehaviour):
        async def run(self):
                await asyncio.sleep(10)
                print(f"{self.agent.jid}: Aguardando decisão da linha 3...")
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                    print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                    if json.loads(msg.body)["best"]=="linha3@jabbers.one":
                        await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", {"2ndbest": "linha1@jabbers.one"}, LinhaProducaoOntologia.INFORM)     
                        print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi a primeira")

    class RecebeDecisaoFinalLinha2(OneShotBehaviour):
        async def run(self):   
            await asyncio.sleep(30)
            print(f"{self.agent.jid}: Aguardando decisão final...")
            msg = await self.receive(timeout=10)
            if json.loads(msg.body)["2ndbest"]=="linha2@jabbers.one" and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:  
                print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")                     

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.ready_agents = set()
        self.add_behaviour(self.WaitForReadyBehav())
