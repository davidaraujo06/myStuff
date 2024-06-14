from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from utils import *
import json, random, asyncio

class LinhaProducaoOntologia:
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao3Agent(Agent):
    class SetReadyBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", "pronto", LinhaProducaoOntologia.INFORM)

    class RecebePropostaLinhas(OneShotBehaviour):
        async def run(self):
            global encomendaFinal
            rateLinha3 = 10
            global encomendas
            melhorLinha = ""
            await asyncio.sleep(20)
            print(f"{self.agent.jid}: Aguardando Proposta...")
            msg = await self.receive(timeout=10)
            respondeJSON = json.loads(msg.body)
            encomendas = respondeJSON[0]["clientes"]
            rateLinha = int(respondeJSON[0]["rateDefeitos"])
            
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                print("começa decisão ....")
                if rateLinha3 == rateLinha:

                    linhas = [str(msg.sender), "linha2@jabbers.one"]
                    melhorLinha = random.choice(linhas)
                    print("aleatória ....")
                elif rateLinha3 < rateLinha:
                     
                    melhorLinha = "linha3@jabbers.one"
                else:
                    
                    melhorLinha = str(msg.sender)
            
            if melhorLinha == "linha3@jabbers.one":

                # envia para a linha sender a info e de seguida comunicar com os robos
                await sendMessage(self, self.agent.jid, str(msg.sender), "performative", {"best": "linha3@jabbers.one"}, LinhaProducaoOntologia.INFORM)
                encomendaFinal = await encomenda_prioritaria(encomendas, 1)
                print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi o primeiro")  
            else: 

                # enviar mensagem sender a dizer que ganhou e de seguida verificar com a linha restante quem é melhor
                await sendMessage(self, self.agent.jid, str(msg.sender), "performative", {"best": str(msg.sender)}, LinhaProducaoOntologia.INFORM)

                if str(msg.sender) == "linha2@jabbers.one":
                    await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", [{"clientes": respondeJSON[0]["clientes"], "rateDefeitos":rateLinha3}], LinhaProducaoOntologia.PROPOSE)
                else:
                    await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", [{"clientes": respondeJSON[0]["clientes"], "rateDefeitos":rateLinha3}], LinhaProducaoOntologia.PROPOSE)
                
                self.agent.add_behaviour(self.agent.RecebeRespostaLinha())   

    class RecebeRespostaLinha(OneShotBehaviour):
            async def run(self):
                global encomendaFinal
                await asyncio.sleep(15)
                print(f"{self.agent.jid}: Aguardando decisão final...")
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                    print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                    if json.loads(msg.body)["2ndbest"]=="linha3@jabbers.one": 
                        encomendaFinal = await encomenda_prioritaria(encomendas, 2)  
                        print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        encomendaFinal = await encomenda_prioritaria(encomendas, 3)
                        print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi o último")        

    class ContaDefeitos(OneShotBehaviour):
        async def run(self):
            global percentagem_defeito
            percentagem_defeito = 0.0
            com_defeito = 0

            while encomendaFinal is None:
                await asyncio.sleep(10)

            tamahoEncomenda = encomendaFinal["quantidade"]
            for i in range(0, tamahoEncomenda): 
                defeito = random.randint(0, 1)
                if defeito == 1:
                    com_defeito += 1
                if com_defeito==0:
                    percentagem_defeito=0
                percentagem_defeito = (com_defeito / (i+1)) * 100
                percentagem_defeito = 85.0
                if percentagem_defeito > 80.0:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  
                    await asyncio.sleep(300) 
            
                await asyncio.sleep(20)

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebePropostaLinhas())
        #self.add_behaviour(self.ContaDefeitos())
