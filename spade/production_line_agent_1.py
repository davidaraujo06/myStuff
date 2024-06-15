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
    data_atual = datetime.now()
    rateLinha1 = 0.0
    encomendaFinal = None
    stateBusy = False
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
            
    class ProposeEncomendaBehav(OneShotBehaviour):
        async def run(self):
            with open("./encomendas.json", 'r') as file:
                listaClientes = json.load(file)

            LinhaProducao1Agent.encomendas = [
                        {
                            "clientes": listaClientes["clientes"],
                            "rateDefeitos": LinhaProducao1Agent.rateLinha1
                        }
            ]
            if LinhaProducao1Agent.encomendas[0]["clientes"]:
                print(f"{self.agent.jid}: Enviando mensagem de posposta...")
                await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", LinhaProducao1Agent.encomendas, LinhaProducaoOntologia.PROPOSE)  
                self.agent.add_behaviour(self.agent.RecebeRespostaLinha2())
            else:
                print("Acabaram as encomendas")    

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
                        if LinhaProducao1Agent.stateBusy == False:
                            LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 2)
                            LinhaProducao1Agent.stateBusy = True
                            self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                            self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 
                            print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        if LinhaProducao1Agent.stateBusy == False:
                            LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 1)
                            LinhaProducao1Agent.stateBusy = True
                            self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                            self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 
                            print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")
                            print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi a primeira")

    class RecebeDecisaoFinalLinha2(OneShotBehaviour):
        async def run(self):
            LinhaProducao1Agent.encomendaFinal   
            await asyncio.sleep(20)
            msg = await self.receive(timeout=10)
            try:
                if json.loads(msg.body)["2ndbest"]=="linha2@jabbers.one" and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:  
                    if LinhaProducao1Agent.stateBusy == False:
                        print(f"{self.agent.jid}: Aguardando decisão final...")
                        LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 3)
                        LinhaProducao1Agent.stateBusy = True
                        self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                        self.agent.add_behaviour(self.agent.RecebePropostaDeTroca())  
                        print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")
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
                        if LinhaProducao1Agent.stateBusy == False:
                            await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                            LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 2)
                            LinhaProducao1Agent.stateBusy = True
                            self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                            self.agent.add_behaviour(self.agent.RecebePropostaDeTroca())  
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        if LinhaProducao1Agent.stateBusy == False:
                            melhorLinha = "linha3@jabbers.one"
                            await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                            LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 3)
                            LinhaProducao1Agent.stateBusy = True
                            self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                            self.agent.add_behaviour(self.agent.RecebePropostaDeTroca())  
                            print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")                         

    class AtingiuLimitePercentagem(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: atingiu limite de percentagem")
            await atingiuLimite("linha2@jabbers.one", "linha3@jabbers.one", LinhaProducao1Agent.rateLinha1,self, LinhaProducaoOntologia, LinhaProducao1Agent.encomendaFinal)


    class ContaDefeitos(OneShotBehaviour):
        async def run(self):
            LinhaProducao1Agent.rateLinha1 = 0.0

            await asyncio.sleep(15)
            tamahoEncomenda = LinhaProducao1Agent.encomendaFinal["quantidade"]
            while True:
                com_defeito = 0
                contagemTamanho = 1
                defeito = random.randint(0, 1)
                if defeito == 1:
                    com_defeito += 1
                if com_defeito==0:
                    LinhaProducao1Agent.rateLinha1=0
                LinhaProducao1Agent.rateLinha1 = (com_defeito / (contagemTamanho+1)) * 100
    
                if LinhaProducao1Agent.rateLinha1 > 80.0 and contagemTamanho>5:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  
                    await asyncio.sleep(300) 

                if (contagemTamanho - com_defeito) == tamahoEncomenda:
                    LinhaProducao1Agent.stateBusy = False
                    print(f"{self.agent.jid}: Acabou a encomenda")
                    print(self.agent.add_behaviour(self.agent.ProposeEncomendaBehav()))
                    break
                contagemTamanho = contagemTamanho + 1
                await asyncio.sleep(20)

    class RecebePropostaDeTroca(OneShotBehaviour):
            async def run(self):
                while True:
                    msgLinha = await self.receive(timeout=10)
                    if msgLinha and json.loads(msgLinha.body)["rate"] =="envia o teu rate" and msgLinha.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                        break
                    else:
                        await asyncio.sleep(5)

                await recebePropostaTroca(self, LinhaProducaoOntologia, LinhaProducao1Agent.rateLinha1, LinhaProducao1Agent.encomendaFinal, msgLinha)            

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.ready_agents = set()
        self.add_behaviour(self.WaitForReadyBehav())
