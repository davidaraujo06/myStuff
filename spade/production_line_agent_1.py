from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from datetime import datetime
from utils import *
from subscriber import MQTTClientSubscriber
from publish import MQTTClientPublisher
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

    mqtt_broker = '172.18.131.112'
    mqtt_port = 1883
    mqtt_user = 'corkai'
    password = 'corkai123'
    topicDetect = "/b1/defect_found/mqtt"
    topicOrder = "/b1/cork_type/mqtt"  
    topicStop = "/b1/stop/mqtt"  
    
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
                #dar tempo de todas as linhas comunicarem e escolherem as encomendas
                await asyncio.sleep(60)
            else:
                print("Acabaram as encomendas")    

    class RecebeRespostaLinha2(OneShotBehaviour):
        async def run(self):
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
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())  
                            LinhaProducao1Agent.stateBusy = True
                            print(LinhaProducao1Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda()) 
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        if LinhaProducao1Agent.stateBusy == False:
                            LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 1)
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())  
                            LinhaProducao1Agent.stateBusy = True
                            print(LinhaProducao1Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda())
                            print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi a primeira")

    class RecebeDecisaoFinalLinha2(OneShotBehaviour):
        async def run(self):
            LinhaProducao1Agent.encomendaFinal   
            await asyncio.sleep(15)
            msg = await self.receive(timeout=10)
            try:
                if json.loads(msg.body)["2ndbest"]=="linha2@jabbers.one" and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:  
                    if LinhaProducao1Agent.stateBusy == False:
                        print(f"{self.agent.jid}: Aguardando decisão final...")
                        LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 3)
                        self.agent.add_behaviour(self.agent.EnviaEncomendaROS())  
                        LinhaProducao1Agent.stateBusy = True
                        print(LinhaProducao1Agent.encomendaFinal)
                        self.agent.add_behaviour(self.agent.IniciaEncomenda())
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
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())  
                            LinhaProducao1Agent.stateBusy = True
                            print(LinhaProducao1Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda()) 
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        if LinhaProducao1Agent.stateBusy == False:
                            melhorLinha = "linha3@jabbers.one"
                            await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                            LinhaProducao1Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao1Agent.encomendas[0]["clientes"], 3)
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())  
                            LinhaProducao1Agent.stateBusy = True
                            print(LinhaProducao1Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda()) 
                            print(f"{self.agent.jid}: sou a pior linha e enviar mensagem a robos")     

    class IniciaEncomenda(OneShotBehaviour):
        async def run(self):
            self.agent.add_behaviour(self.agent.ContaDefeitos())
            self.agent.add_behaviour(self.agent.RecebeFinalEncomenda()) 

    class AtingiuLimitePercentagem(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: atingiu limite de percentagem")
            result = await atingiuLimite("linha2@jabbers.one", "linha3@jabbers.one", LinhaProducao1Agent.rateLinha1,self, LinhaProducaoOntologia, LinhaProducao1Agent.encomendaFinal)
            if result == 0:
                self.agent.add_behaviour(self.agent.ContaDefeitos()) 
            else:    
                LinhaProducao1Agent.encomendaFinal = result
                self.agent.add_behaviour(self.agent.ContaDefeitos()) 


    class ContaDefeitos(OneShotBehaviour):
        async def run(self):

            mqtt_client_instance = MQTTClientSubscriber(LinhaProducao1Agent.mqtt_broker , LinhaProducao1Agent.mqtt_port, LinhaProducao1Agent.mqtt_user, LinhaProducao1Agent.password, LinhaProducao1Agent.topicDetect)
            mqtt_client_instance.run()

            while True:
                last_payload = mqtt_client_instance.get_last_payload()
                valores = last_payload.split('/')
                valor1 = int(valores[0])
                valor2 = int(valores[1])
                
                if (valor1 + valor2) >= 1:
                    print(f"{self.agent.jid}: inicia contagem de defeito")
                    break
            
            LinhaProducao1Agent.rateLinha1 = 0.0

            await asyncio.sleep(15)
            tamahoEncomenda = LinhaProducao1Agent.encomendaFinal["quantidade"]
            defeito = 0
            contagemTamanho = 0
            while True:
                last_payload = mqtt_client_instance.get_last_payload()
                valores = last_payload.split('/')
                defeito = int(valores[0])
                semDefeito = int(valores[1])
                contagemTamanho = defeito + semDefeito
                if defeito==0:
                    LinhaProducao1Agent.rateLinha1=0
                LinhaProducao1Agent.rateLinha1 = (defeito / contagemTamanho) * 100   
                
                if LinhaProducao1Agent.rateLinha1 > 80.0 and contagemTamanho>5:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  

                if (contagemTamanho - defeito) == tamahoEncomenda:
                    mqtt_client_instance.client.loop_stop()
                    mqtt_client_instance.client.disconnect()
                    LinhaProducao1Agent.stateBusy = False

                    publisher = MQTTClientPublisher(LinhaProducao1Agent.mqtt_broker , LinhaProducao1Agent.mqtt_port, LinhaProducao1Agent.mqtt_user, LinhaProducao1Agent.password)
                    publisher.run()

                    message = True
                    publisher.publish(LinhaProducao1Agent.topicStop, message)
                    publisher.client.loop_stop()
                    publisher.client.disconnect()

                    print(f"{self.agent.jid}: Acabou a encomenda")
                    self.agent.add_behaviour(self.agent.ProposeEncomendaBehav())
                    break

    class RecebePropostaDeTroca(OneShotBehaviour):
            async def run(self):
                while True:
                    msgLinha = await self.receive(timeout=10)
                    if msgLinha and json.loads(msgLinha.body)["rate"] =="envia o teu rate" and msgLinha.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                        break
                    else:
                        await asyncio.sleep(5)

                result = await recebePropostaTroca(self, LinhaProducaoOntologia, LinhaProducao1Agent.rateLinha1, LinhaProducao1Agent.encomendaFinal, msgLinha)
                if result == 0:
                    self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                    self.agent.add_behaviour(self.agent.IniciaRecebePropostaNovo()) 
                else:    
                    LinhaProducao1Agent.encomendaFinal = result
                    self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                    self.agent.add_behaviour(self.agent.IniciaRecebePropostaNovo())  

    class IniciaRecebePropostaNovo(OneShotBehaviour):
            async def run(self):
                asyncio.sleep(5)
                self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 
                
    class RecebeFinalEncomenda(CyclicBehaviour):
            async def run(self):
                while True:
                    msgLinha = await self.receive(timeout=10)
                    if msgLinha and json.loads(msgLinha.body)["terminou"] == True and msgLinha.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                        break
                    else:
                        await asyncio.sleep(5)

                #caso não dê para acionar este behaviour porque pode estar a correr
                while True:
                    try:
                        self.agent.add_behaviour(self.agent.ProposeEncomendaBehav())  
                        break
                    except:  
                        await asyncio.sleep(1)  

    
    class EnviaEncomendaROS(CyclicBehaviour):   
        async def run(self):
            publisher = MQTTClientPublisher(LinhaProducao1Agent.mqtt_broker , LinhaProducao1Agent.mqtt_port, LinhaProducao1Agent.mqtt_user, LinhaProducao1Agent.password)
            publisher.run()
            print(str(LinhaProducao1Agent.encomendaFinal["tipo"]))
            message = str(LinhaProducao1Agent.encomendaFinal["tipo"])
            publisher.publish(LinhaProducao1Agent.topicOrder, message)
            publisher.client.loop_stop()
            publisher.client.disconnect()                 
                     

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.ready_agents = set()
        self.add_behaviour(self.WaitForReadyBehav())
        self.add_behaviour(self.RecebePropostaDeTroca()) 
