from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from utils import *
import json, random, asyncio

class LinhaProducaoOntologia:
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao3Agent(Agent):
    rateLinha3 = 0.0
    encomendaFinal = None
    encomendas = None
    stateBusy = False
    class SetReadyBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", "pronto", LinhaProducaoOntologia.INFORM)

    class RecebePropostaLinhas(OneShotBehaviour):
        async def run(self):
            melhorLinha = ""
            await asyncio.sleep(20)
            print(f"{self.agent.jid}: Aguardando Proposta...")
            msg = await self.receive(timeout=10)
            respondeJSON = json.loads(msg.body)
            LinhaProducao3Agent.encomendas = respondeJSON[0]["clientes"]
            rateLinha = int(respondeJSON[0]["rateDefeitos"])
            
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                print("começa decisão ....")
                if LinhaProducao3Agent.rateLinha3 == rateLinha:

                    linhas = [str(msg.sender), "linha2@jabbers.one"]
                    melhorLinha = random.choice(linhas)
                    print("aleatória ....")
                elif LinhaProducao3Agent.rateLinha3 < rateLinha:
                     
                    melhorLinha = "linha3@jabbers.one"
                else:
                    
                    melhorLinha = str(msg.sender)
            
            if melhorLinha == "linha3@jabbers.one":

                # envia para a linha sender a info e de seguida comunicar com os robos
                await sendMessage(self, self.agent.jid, str(msg.sender), "performative", {"best": "linha3@jabbers.one"}, LinhaProducaoOntologia.INFORM)
                if LinhaProducao3Agent.stateBusy == False:
                    LinhaProducao3Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao3Agent.encomendas, 1)
                    LinhaProducao3Agent.stateBusy = True
                    self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                    self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 
                    print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi o primeiro")  
            else: 

                # enviar mensagem sender a dizer que ganhou e de seguida verificar com a linha restante quem é melhor
                await sendMessage(self, self.agent.jid, str(msg.sender), "performative", {"best": str(msg.sender)}, LinhaProducaoOntologia.INFORM)

                if str(msg.sender) == "linha2@jabbers.one":
                    await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", [{"clientes": LinhaProducao3Agent.encomendas, "rateDefeitos":LinhaProducao3Agent.rateLinha3}], LinhaProducaoOntologia.PROPOSE)
                else:
                    await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", [{"clientes": LinhaProducao3Agent.encomendas, "rateDefeitos":LinhaProducao3Agent.rateLinha3}], LinhaProducaoOntologia.PROPOSE)
                
                self.agent.add_behaviour(self.agent.RecebeRespostaLinha())   

    class RecebeRespostaLinha(OneShotBehaviour):
            async def run(self):
                await asyncio.sleep(15)
                print(f"{self.agent.jid}: Aguardando decisão final...")
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                    print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                    if json.loads(msg.body)["2ndbest"]=="linha3@jabbers.one": 
                        if LinhaProducao3Agent.stateBusy == False:    
                            LinhaProducao3Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao3Agent.encomendas, 2) 
                            LinhaProducao3Agent.stateBusy = True
                            self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                            self.agent.add_behaviour(self.agent.RecebePropostaDeTroca())  
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        if LinhaProducao3Agent.stateBusy == False:
                            LinhaProducao3Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao3Agent.encomendas, 3)
                            LinhaProducao3Agent.stateBusy = True
                            self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                            self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 
                            print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi o último")        

    class RecebePropostaDeTroca(OneShotBehaviour):
            async def run(self):
                while True:
                    msgLinha = await self.receive(timeout=10)
                    if msgLinha and json.loads(msgLinha.body)["rate"] =="envia o teu rate" and msgLinha.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                        break
                    else:
                        await asyncio.sleep(5)

                await recebePropostaTroca(self, LinhaProducaoOntologia,  LinhaProducao3Agent.rateLinha3, LinhaProducao3Agent.encomendaFinal, msgLinha)

    class ContaDefeitos(OneShotBehaviour):
        async def run(self):
            LinhaProducao3Agent.rateLinha3 = 0.0

            await asyncio.sleep(15)
            tamahoEncomenda = LinhaProducao3Agent.encomendaFinal["quantidade"]
            while True:
                com_defeito = 0
                contagemTamanho = 1
                defeito = random.randint(0, 1)
                if defeito == 1:
                    com_defeito += 1
                if com_defeito==0:
                    LinhaProducao3Agent.rateLinha3=0
                LinhaProducao3Agent.rateLinha3 = (com_defeito / (contagemTamanho+1)) * 100
    
                if LinhaProducao3Agent.rateLinha3 > 80.0 and contagemTamanho>5:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  
                    await asyncio.sleep(300) 

                if (contagemTamanho - com_defeito) == tamahoEncomenda:
                    LinhaProducao3Agent.stateBusy = False
                    print(f"{self.agent.jid}: Acabou a encomenda")
                    #voltar a escolhar encomenda 
                    break
                contagemTamanho = contagemTamanho + 1
                await asyncio.sleep(20)

    class AtingiuLimitePercentagem(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: atingiu limite de percentagem")
            await atingiuLimite("linha1@jabbers.one", "linha2@jabbers.one", LinhaProducao3Agent.rateLinha3,self, LinhaProducaoOntologia, LinhaProducao3Agent.encomendaFinal)             

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebePropostaLinhas())
