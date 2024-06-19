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
    stateBusy = False
    class SetReadyBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", "pronto", LinhaProducaoOntologia.INFORM)

    class RecebePropostasLinha1(OneShotBehaviour):
        async def run(self):
            while True:
                try: 
                    msg = await self.receive(timeout=10)
                    respondeJSON = json.loads(msg.body)
                    LinhaProducao2Agent.encomendas = respondeJSON[0]["clientes"]
                    rateLinha2 = int(respondeJSON[0]["rateDefeitos"])
                    if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                            break
                    else:
                            await asyncio.sleep(5)
                except:
                     await asyncio.sleep(5)            
            melhorLinha = ""
            print(f"{self.agent.jid}: Aguardando Proposta...")
            print("começa decisão ....")
            if LinhaProducao2Agent.rateLinha2 == rateLinha2:
                linhas = ["linha1@jabbers.one", "linha2@jabbers.one"]
                melhorLinha = random.choice(linhas)
                print("aleatória ....")
            elif LinhaProducao2Agent.rateLinha2 < rateLinha2: 
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

    class RecebeDecisaoFinalLinha1(OneShotBehaviour):
        async def run(self):   
            await asyncio.sleep(15)
            msg = await self.receive(timeout=10)
            try:
                if json.loads(msg.body)["2ndbest"]=="linha1@jabbers.one" and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:  
                    if LinhaProducao2Agent.stateBusy == False:
                        print(f"{self.agent.jid}: Aguardando decisão final...")
                        LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 3)
                        LinhaProducao2Agent.stateBusy = True
                        print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos") 
                        print(LinhaProducao2Agent.encomendaFinal)
                        self.agent.add_behaviour(self.agent.IniciaEncomenda())
                    
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
                        if LinhaProducao2Agent.stateBusy == False:
                            LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 2)
                            LinhaProducao2Agent.stateBusy = True
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos")
                            print(LinhaProducao2Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda())
                    else:
                        melhorLinha = "linha3@jabbers.one"
                        await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                        if LinhaProducao2Agent.stateBusy == False:
                            LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 3)
                            LinhaProducao2Agent.stateBusy = True
                            print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos") 
                            print(LinhaProducao2Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda())   


    class RecebeRespostaLinha3(OneShotBehaviour):
            async def run(self):
                await asyncio.sleep(15)
                print(f"{self.agent.jid}: Aguardando decisão da linha 3...")
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                    print(f"{self.agent.jid}: Recebeu a seguinte decisão:  {msg.body}")  
                    if json.loads(msg.body)["best"]=="linha3@jabbers.one":
                        await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", {"2ndbest": "linha2@jabbers.one"}, LinhaProducaoOntologia.INFORM)     
                        if LinhaProducao2Agent.stateBusy == False:
                            LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 2)
                            LinhaProducao2Agent.stateBusy = True
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                            print(LinhaProducao2Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda())
                    else: 
                        if LinhaProducao2Agent.stateBusy == False:
                            LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 1)
                            LinhaProducao2Agent.stateBusy = True
                            print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi a primeira")  
                            print(LinhaProducao2Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda())                
    
    class IniciaEncomenda(OneShotBehaviour):
        async def run(self):
            self.agent.add_behaviour(self.agent.ContaDefeitos())
            self.agent.add_behaviour(self.agent.RecebePropostasLinha1()) 

    class RecebePropostaDeTroca(OneShotBehaviour):
            async def run(self):
                while True:
                    msgLinha = await self.receive(timeout=10)
                    if msgLinha and json.loads(msgLinha.body)["rate"] =="envia o teu rate" and msgLinha.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                        break
                    else:
                        await asyncio.sleep(5)

                result = await recebePropostaTroca(self, LinhaProducaoOntologia, LinhaProducao2Agent.rateLinha2, LinhaProducao2Agent.encomendaFinal, msgLinha)
                if result == 0:
                    self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                    self.agent.add_behaviour(self.agent.IniciaRecebePropostaNovo()) 
                else:    
                    LinhaProducao2Agent.encomendaFinal = result
                    self.agent.add_behaviour(self.agent.ContaDefeitos())
                    self.agent.add_behaviour(self.agent.IniciaRecebePropostaNovo()) 

    class IniciaRecebePropostaNovo(OneShotBehaviour):
            async def run(self):
                asyncio.sleep(5)
                self.agent.add_behaviour(self.agent.RecebePropostaDeTroca())                     

    class ContaDefeitos(OneShotBehaviour):
        async def run(self):
            #TODO: Esperar pela decisão que posso iniciar a contagem, se for diferente de 0 então siga
            LinhaProducao2Agent.rateLinha2 = 0.0

            await asyncio.sleep(15)
            tamahoEncomenda = LinhaProducao2Agent.encomendaFinal["quantidade"]
            com_defeito = 0
            contagemTamanho = 1
            while True:
                defeito = random.randint(0, 1)
                if defeito == 1:
                    com_defeito += 1
                if com_defeito==0:
                    LinhaProducao2Agent.rateLinha2=0
                LinhaProducao2Agent.rateLinha2 = (com_defeito / (contagemTamanho+1)) * 100
    
                if LinhaProducao2Agent.rateLinha2 > 80.0 and contagemTamanho>5:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  
                    

                if (contagemTamanho - com_defeito) == tamahoEncomenda:
                    LinhaProducao2Agent.stateBusy = False
                    print(f"{self.agent.jid}: Acabou a encomenda")
                    await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", {"terminou": True}, LinhaProducaoOntologia.INFORM)
                    #voltar a escolhar encomenda 
                    break
                contagemTamanho = contagemTamanho + 1
                await asyncio.sleep(20)

    class AtingiuLimitePercentagem(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: atingiu limite de percentagem")
            result = await atingiuLimite("linha1@jabbers.one", "linha3@jabbers.one", LinhaProducao2Agent.rateLinha2,self, LinhaProducaoOntologia, LinhaProducao2Agent.encomendaFinal)    
            if result == 0:
                self.agent.add_behaviour(self.agent.ContaDefeitos()) 
            else:    
                LinhaProducao2Agent.encomendaFinal = result
                self.agent.add_behaviour(self.agent.ContaDefeitos())            

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebePropostasLinha1())
        self.add_behaviour(self.RecebePropostaDeTroca()) 
