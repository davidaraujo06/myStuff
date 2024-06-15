from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from utils import *
import json, random, asyncio

class LinhaProducaoOntologia:
    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao2Agent(Agent):
    rateLinha2 = 0.0
    encomendaFinal = None
    encomendas = None
    class SetReadyBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", "pronto", LinhaProducaoOntologia.INFORM)

    class RecebePropostasLinha1(OneShotBehaviour):
        async def run(self):
            melhorLinha = ""
            await asyncio.sleep(5)
            print(f"{self.agent.jid}: Aguardando Proposta...")
            msg = await self.receive(timeout=10)
            respondeJSON = json.loads(msg.body)
            LinhaProducao2Agent.encomendas = respondeJSON[0]["clientes"]
            rateLinha1 = int(respondeJSON[0]["rateDefeitos"])
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                print("começa decisão ....")
                if LinhaProducao2Agent.rateLinha2 == rateLinha1:
                    linhas = ["linha1@jabbers.one", "linha2@jabbers.one"]
                    melhorLinha = random.choice(linhas)
                    print("aleatória ....")
                elif LinhaProducao2Agent.rateLinha2 < rateLinha1: 
                    melhorLinha = "linha2@jabbers.one"
                else:
                    melhorLinha = "linha1@jabbers.one"

            if melhorLinha == "linha1@jabbers.one":
                await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", {"best": "linha1@jabbers.one"}, LinhaProducaoOntologia.INFORM)
                self.agent.add_behaviour(self.agent.RecebeDecisaoFinalLinha1())
            else: 
                # enviar mensagem á linha 3
                await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", {"best": "linha2@jabbers.one"}, LinhaProducaoOntologia.INFORM)
                await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", [{"clientes": LinhaProducao2Agent.encomendas, "rateDefeitos":LinhaProducao2Agent.rateLinha2}], LinhaProducaoOntologia.PROPOSE)
                self.agent.add_behaviour(self.agent.RecebeRespostaLinha3())
                ##TODO: nota: linha 1 e dois vão enviar á linha 3, caso seja a 1 ou 2 a ganhar então a 3 informa a 1 (usar o msg.sender) e depois fala com a 2 para saber quem fica com o resto 
                # caso seja a 3 a ganhar então a tres fica com a maior e depois informa a 1 ou 2 a dizer que perderam e como a 1 e a 2 já se conforntaram ja sabem quem é pior ou melhor
                # ao fim disso ver melhor o caso dos rates e ter uma função sempre a cada 10 segundos a calcular a percentagem e ao fim disso ver mensagens trocadas com robos

    class RecebeDecisaoFinalLinha1(OneShotBehaviour):
        async def run(self):   
            await asyncio.sleep(15)
            msg = await self.receive(timeout=10)
            try:
                if json.loads(msg.body)["2ndbest"]=="linha1@jabbers.one" and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:  
                    print(f"{self.agent.jid}: Aguardando decisão final...")
                    LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 3)
                    print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos") 
                    self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 
                    
            except:
                melhorLinha = ""
                print(f"{self.agent.jid}: Aguardando Proposta...")
                respondeJSON = json.loads(msg.body)
                rateLinha3 = int(respondeJSON[0]["rateDefeitos"])
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                    print("começa decisão ....")
                    if LinhaProducao2Agent.rateLinha2 == rateLinha3:
                        linhas = ["linha1@jabbers.one", "linha2@jabbers.one"]
                        melhorLinha = random.choice(linhas)
                        print("aleatória ....")
                    elif LinhaProducao2Agent.rateLinha2 < rateLinha3: 
                        melhorLinha = "linha2@jabbers.one"
                    else:
                        melhorLinha = "linha3@jabbers.one"

                    if melhorLinha == "linha2@jabbers.one":
                        await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                        LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 2)
                        print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos")
                        self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 
                    else:
                        melhorLinha = "linha3@jabbers.one"
                        await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                        LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 3)
                        print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")   
                        self.agent.add_behaviour(self.agent.RecebePropostaDeTroca())       


    class RecebeRespostaLinha3(OneShotBehaviour):
            async def run(self):
                await asyncio.sleep(15)
                print(f"{self.agent.jid}: Aguardando decisão da linha 3...")
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                    print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                    if json.loads(msg.body)["best"]=="linha3@jabbers.one":
                        await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", {"2ndbest": "linha2@jabbers.one"}, LinhaProducaoOntologia.INFORM)     
                        LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 2)
                        print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                        self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 
                    else:
                        LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 1)
                        print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi a primeira")  
                        self.agent.add_behaviour(self.agent.RecebePropostaDeTroca())                   

    class RecebePropostaDeTroca(OneShotBehaviour):
            async def run(self):
                while True:
                    msgLinha = await self.receive(timeout=10)
                    if msgLinha and json.loads(msgLinha.body)["rate"] =="envia o teu rate" and msgLinha.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                        break
                    else:
                        await asyncio.sleep(5)

                await recebePropostaTroca(self, LinhaProducaoOntologia, LinhaProducao2Agent.rateLinha2, LinhaProducao2Agent.encomendaFinal, msgLinha)

    class ContaDefeitos(OneShotBehaviour):
        async def run(self):
            LinhaProducao2Agent.rateLinha2
            LinhaProducao2Agent.rateLinha2 = 0.0
            com_defeito = 0

            while LinhaProducao2Agent.encomendaFinal is None:
                await asyncio.sleep(10)

            await asyncio.sleep(15)
            tamahoEncomenda = LinhaProducao2Agent.encomendaFinal["quantidade"]
            for i in range(0, tamahoEncomenda): 
                defeito = random.randint(0, 1)
                if defeito == 1:
                    com_defeito += 1
                if com_defeito==0:
                    LinhaProducao2Agent.rateLinha2=0
                LinhaProducao2Agent.rateLinha2 = (com_defeito / (i+1)) * 100
                
                if LinhaProducao2Agent.rateLinha2 > 80.0:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  
                    await asyncio.sleep(300) 
            
                await asyncio.sleep(20)

    class AtingiuLimitePercentagem(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: atingiu limite de percentagem")
            await atingiuLimite("linha1@jabbers.one", "linha3@jabbers.one", LinhaProducao2Agent.rateLinha2,self, LinhaProducaoOntologia, LinhaProducao2Agent.encomendaFinal)            

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebePropostasLinha1())
        self.add_behaviour(self.ContaDefeitos())
