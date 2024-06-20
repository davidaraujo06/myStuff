from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from utils import *
from subscriber import MQTTClientSubscriber
from publish import MQTTClientPublisher
import json, random, asyncio

class LinhaProducaoOntologia:
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao3Agent(Agent):
    rateLinha3 = 0.0
    encomendaFinal = None
    encomendas = None
    stateBusy = False

    mqtt_broker = '192.168.137.202'
    mqtt_port = 1883
    mqtt_user = 'corkai'
    password = 'corkai123'
    topicDetect = "/b3/defect_found/mqtt"
    topicOrder = "/b3/cork_type/mqtt"  
    topicStop = "/b3/stop/mqtt"  
    
    class SetReadyBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", "pronto", LinhaProducaoOntologia.INFORM)

    class RecebePropostaLinhas(OneShotBehaviour):
        async def run(self):
            while True:
                try: 
                    msg = await self.receive(timeout=10)
                    respondeJSON = json.loads(msg.body)
                    LinhaProducao3Agent.encomendas = respondeJSON[0]["clientes"]
                    rateLinha = int(respondeJSON[0]["rateDefeitos"])
                    
                    if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                            break
                    else:
                            await asyncio.sleep(5)
                except:
                     await asyncio.sleep(5)

            melhorLinha = ""
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
                    self.agent.add_behaviour(self.agent.EnviaEncomendaROS())  
                    LinhaProducao3Agent.stateBusy = True
                    print(LinhaProducao3Agent.encomendaFinal)
                    self.agent.add_behaviour(self.agent.IniciaEncomenda()) 
                    print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi o primeiro")  
            else: 

                # enviar mensagem sender a dizer que ganhou e de seguida verificar com a linha restante quem é melhor
                await sendMessage(self, self.agent.jid, str(msg.sender), "performative", {"best": str(msg.sender)}, LinhaProducaoOntologia.INFORM)
                
                if str(msg.sender) == "linha2@jabbers.one":
                    await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", [{"clientes": LinhaProducao3Agent.encomendas, "rateDefeitos":LinhaProducao3Agent.rateLinha3}], LinhaProducaoOntologia.PROPOSE)

                else:
                    await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", [{"clientes": LinhaProducao3Agent.encomendas, "rateDefeitos":LinhaProducao3Agent.rateLinha3}], LinhaProducaoOntologia.PROPOSE)
                
                self.agent.add_behaviour(self.agent.RecebeRespostaLinha())   

    class IniciaNovo(OneShotBehaviour):
        async def run(self):
            self.agent.add_behaviour(self.agent.RecebePropostaLinhas())

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
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())  
                            LinhaProducao3Agent.stateBusy = True
                            print(LinhaProducao3Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda()) 
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                    else:
                        if LinhaProducao3Agent.stateBusy == False:
                            LinhaProducao3Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao3Agent.encomendas, 3)
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())  
                            LinhaProducao3Agent.stateBusy = True
                            print(LinhaProducao3Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda()) 
                            print(f"{self.agent.jid}: envia mensagem aos robos a dizer que foi o último")  

    class IniciaEncomenda(OneShotBehaviour):
        async def run(self):
            self.agent.add_behaviour(self.agent.ContaDefeitos())
            self.agent.add_behaviour(self.agent.RecebePropostaLinhas())                               

    class RecebePropostaDeTroca(OneShotBehaviour):
            async def run(self):
                while True:
                    msgLinha = await self.receive(timeout=10)
                    if msgLinha and json.loads(msgLinha.body)["rate"] =="envia o teu rate" and msgLinha.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                        break
                    else:
                        await asyncio.sleep(5)

                result = await recebePropostaTroca(self, LinhaProducaoOntologia,  LinhaProducao3Agent.rateLinha3, LinhaProducao3Agent.encomendaFinal, msgLinha)
                if result == 0:
                    self.agent.add_behaviour(self.agent.ContaDefeitos()) 
                    self.agent.add_behaviour(self.agent.IniciaRecebePropostaNovo()) 
                else:    
                    LinhaProducao3Agent.encomendaFinal = result
                    LinhaProducao3Agent.encomendaFinal = result
                    publisher = MQTTClientPublisher(LinhaProducao3Agent.mqtt_broker , LinhaProducao3Agent.mqtt_port, LinhaProducao3Agent.mqtt_user, LinhaProducao3Agent.password)
                    publisher.run()

                    message = int(1)
                    publisher.publish(LinhaProducao3Agent.topicStop, message)
                    publisher.client.loop_stop()
                    publisher.client.disconnect()
                    self.agent.add_behaviour(self.agent.EnviaEncomendaROS())
                    self.agent.add_behaviour(self.agent.ContaDefeitos())
                    self.agent.add_behaviour(self.agent.IniciaRecebePropostaNovo())  

    class IniciaRecebePropostaNovo(OneShotBehaviour):
            async def run(self):
                asyncio.sleep(5)
                self.agent.add_behaviour(self.agent.RecebePropostaDeTroca()) 

    class ContaDefeitos(OneShotBehaviour):
        async def run(self):
            mqtt_client_instance = MQTTClientSubscriber(LinhaProducao3Agent.mqtt_broker , LinhaProducao3Agent.mqtt_port, LinhaProducao3Agent.mqtt_user, LinhaProducao3Agent.password, LinhaProducao3Agent.topicDetect)
            mqtt_client_instance.run()

            while True:
                last_payload = mqtt_client_instance.get_last_payload()
                valores = last_payload.split('/')
                valor1 = int(valores[0])
                valor2 = int(valores[1])
                
                if (valor1 + valor2) >= 1:
                    print(f"{self.agent.jid}: inicia contagem de defeito")
                    break
            
            LinhaProducao3Agent.rateLinha3 = 0.0

            tamahoEncomenda = LinhaProducao3Agent.encomendaFinal["quantidade"]
            defeito = 0
            contagemTamanho = 0
            while True:
                last_payload = mqtt_client_instance.get_last_payload()
                valores = last_payload.split('/')
                defeito = int(valores[0])
                semDefeito = int(valores[1])
                contagemTamanho = defeito + semDefeito
                if defeito==0:
                    LinhaProducao3Agent.rateLinha3=0
                LinhaProducao3Agent.rateLinha3 = (defeito / (contagemTamanho+1)) * 100
    
                if LinhaProducao3Agent.rateLinha3 > 80.0 and contagemTamanho>5:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  
                    
                print(f"{self.agent.jid}: " + str(defeito) + "..." + str(semDefeito) + "..." + contagemTamanho + "..."  + str(LinhaProducao3Agent.rateLinha3))
                if semDefeito == tamahoEncomenda:
                    mqtt_client_instance.client.loop_stop()
                    mqtt_client_instance.client.disconnect()
                    LinhaProducao3Agent.stateBusy = False
                    publisher = MQTTClientPublisher(LinhaProducao3Agent.mqtt_broker , LinhaProducao3Agent.mqtt_port, LinhaProducao3Agent.mqtt_user, LinhaProducao3Agent.password)
                    publisher.run()

                    message = int(1)
                    publisher.publish(LinhaProducao3Agent.topicStop, message)
                    publisher.client.loop_stop()
                    publisher.client.disconnect()
                    print(f"{self.agent.jid}: Acabou a encomenda")
                    await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", {"terminou": True}, LinhaProducaoOntologia.INFORM)
                    #voltar a escolhar encomenda 
                    break

    class AtingiuLimitePercentagem(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: atingiu limite de percentagem")
            result=  await atingiuLimite("linha1@jabbers.one", "linha2@jabbers.one", LinhaProducao3Agent.rateLinha3,self, LinhaProducaoOntologia, LinhaProducao3Agent.encomendaFinal)  
            if result == 0:
                self.agent.add_behaviour(self.agent.ContaDefeitos()) 
            else:    
                LinhaProducao3Agent.encomendaFinal = result
                publisher = MQTTClientPublisher(LinhaProducao3Agent.mqtt_broker , LinhaProducao3Agent.mqtt_port, LinhaProducao3Agent.mqtt_user, LinhaProducao3Agent.password)
                publisher.run()
                message = int(1)
                publisher.publish(LinhaProducao3Agent.topicStop, message)
                publisher.client.loop_stop()
                publisher.client.disconnect()
                self.agent.add_behaviour(self.agent.EnviaEncomendaROS())
                self.agent.add_behaviour(self.agent.ContaDefeitos())  

    class EnviaEncomendaROS(OneShotBehaviour):   
        async def run(self):
            publisher = MQTTClientPublisher(LinhaProducao3Agent.mqtt_broker , LinhaProducao3Agent.mqtt_port, LinhaProducao3Agent.mqtt_user, LinhaProducao3Agent.password)
            publisher.run()
    
            message = str(LinhaProducao3Agent.encomendaFinal["tipo"])
            publisher.publish(LinhaProducao3Agent.topicOrder, message)
            publisher.client.loop_stop()
            publisher.client.disconnect()                    

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebePropostaLinhas())
