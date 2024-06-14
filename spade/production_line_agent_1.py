from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from datetime import datetime, timedelta
from utils import *
import json, asyncio, random

class LinhaProducaoOntologia:
    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao1Agent(Agent):
    rateLinha1 = 0.0
    encomendaFinal = None
    encomendas = None
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
            LinhaProducao1Agent.encomendas = [
                {
                    "clientes": {
                        "Cliente A": {"tipo": "Granulado", "prioridade": "Alta", "quantidade": 100, "tempo_finalizacao": 120, "prazo_entrega": (data_atual + timedelta(days=5)).strftime('%Y-%m-%d')},
                        "Cliente B": {"tipo": "Micro-Granulado","prioridade": "Media", "quantidade": 50, "tempo_finalizacao": 240, "prazo_entrega": (data_atual + timedelta(days=10)).strftime('%Y-%m-%d')},
                        "Cliente C": {"tipo": "Granulado","prioridade": "Baixa", "quantidade": 200, "tempo_finalizacao": 420, "prazo_entrega": (data_atual + timedelta(days=15)).strftime('%Y-%m-%d')},
                        "Cliente D": {"tipo": "Micro-Granulado","prioridade": "Alta", "quantidade": 150, "tempo_finalizacao": 180, "prazo_entrega": (data_atual + timedelta(days=6)).strftime('%Y-%m-%d')},
                        "Cliente E": {"tipo": "Granulado","prioridade": "Media", "quantidade": 80, "tempo_finalizacao": 300, "prazo_entrega": (data_atual + timedelta(days=12)).strftime('%Y-%m-%d')}
                    },
                    "rateDefeitos": LinhaProducao1Agent.rateLinha1
                }
            ]

            # # Loop para verificar se há LinhaProducao1Agent.encomendas
            # while not LinhaProducao1Agent.encomendas:
            #     print("Aguardando LinhaProducao1Agent.encomendas...")
            #     await asyncio.sleep(900)  # Aguarda 15 minutos antes de verificar novamente

            print(f"{self.agent.jid}: Enviando mensagem de posposta...")
            await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", LinhaProducao1Agent.encomendas, LinhaProducaoOntologia.PROPOSE)  
            self.agent.add_behaviour(self.agent.RecebeRespostaLinha2())

    class RecebeRespostaLinha2(OneShotBehaviour):
        async def run(self):
            await asyncio.sleep(10)
            print(f"{self.agent.jid}: Aguardando decisão da linha 2...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                if json.loads(msg.body)["best"]=="linha1@jabbers.one":
                    await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", LinhaProducao1Agent.encomendas, LinhaProducaoOntologia.PROPOSE)
                    self.agent.add_behaviour(self.agent.RecebeRespostaLinha3())
                else:
                    self.agent.add_behaviour(self.agent.RecebeDecisaoFinalLinha2())    

    class RecebeRespostaLinha3(OneShotBehaviour):
        async def run(self):
                LinhaProducao1Agent.encomendaFinal
                await asyncio.sleep(10)
                print(f"{self.agent.jid}: Aguardando decisão da linha 3...")
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                    print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                    if json.loads(msg.body)["best"]=="linha3@jabbers.one":
                        await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", {"2ndbest": "linha1@jabbers.one"}, LinhaProducaoOntologia.INFORM) 
                        LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 2)
                        print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 1)
                        print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi a primeira")

    class RecebeDecisaoFinalLinha2(OneShotBehaviour):
        async def run(self):
            LinhaProducao1Agent.encomendaFinal   
            await asyncio.sleep(20)
            msg = await self.receive(timeout=10)
            try:
                if json.loads(msg.body)["2ndbest"]=="linha2@jabbers.one" and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:  
                    print(f"{self.agent.jid}: Aguardando decisão final...")
                    print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")
                    LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 3)
            except:
                melhorLinha = ""
                print(f"{self.agent.jid}: Aguardando Proposta...")
                respondeJSON = json.loads(msg.body)
                rateLinha3 = int(respondeJSON[0]["rateDefeitos"])
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                    print("começa decisão ....")
                    if LinhaProducao1Agent.rateLinha1 == rateLinha3:
                        linhas = ["linha1@jabbers.one", "linha3@jabbers.one"]
                        melhorLinha = random.choice(linhas)
                        print("aleatória ....")
                    elif LinhaProducao1Agent.rateLinha1 < rateLinha3: 
                        melhorLinha = "linha1@jabbers.one"
                    else:
                        melhorLinha = "linha3@jabbers.one"

                    if melhorLinha == "linha1@jabbers.one":
                        await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                        LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 2)
                        print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        melhorLinha = "linha3@jabbers.one"
                        await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                        LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 3)
                        print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")                         

    class AtingiuLimitePercentagem(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: atingiu limite de percentagem")
            print(LinhaProducao1Agent.rateLinha1)
            await atingiuLimite("linha2@jabbers.one", "linha3@jabbers.one", LinhaProducao1Agent.rateLinha1,self, LinhaProducaoOntologia, LinhaProducao1Agent.encomendaFinal)


    class ContaDefeitos(OneShotBehaviour):
        async def run(self):
            LinhaProducao1Agent.rateLinha1 = 0.0
            com_defeito = 0

            while LinhaProducao1Agent.encomendaFinal is None:
                await asyncio.sleep(10)

            await asyncio.sleep(15)
            tamahoEncomenda = LinhaProducao1Agent.encomendaFinal["quantidade"]
            for i in range(0, tamahoEncomenda): 
                defeito = random.randint(0, 1)
                if defeito == 1:
                    com_defeito += 1
                if com_defeito==0:
                    LinhaProducao1Agent.rateLinha1=0
                LinhaProducao1Agent.rateLinha1 = (com_defeito / (i+1)) * 100
                LinhaProducao1Agent.rateLinha1 = 85.0
                if LinhaProducao1Agent.rateLinha1 > 80.0:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  
                    await asyncio.sleep(300) 
            
                await asyncio.sleep(20)

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.ready_agents = set()
        self.add_behaviour(self.WaitForReadyBehav())
        self.add_behaviour(self.ContaDefeitos())
