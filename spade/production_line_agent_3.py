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
            rateLinha3 = 10
            melhorLinha = ""
            await asyncio.sleep(20)
            print(f"{self.agent.jid}: Aguardando Proposta...")
            msg = await self.receive(timeout=10)
            respondeJSON = json.loads(msg.body)
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
                await asyncio.sleep(20)
                print(f"{self.agent.jid}: Aguardando decisão final...")
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                    print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                    if json.loads(msg.body)["2ndbest"]=="linha3@jabbers.one":   
                        print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi o último")        

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebePropostaLinhas())
