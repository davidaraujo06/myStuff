from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from utils import *
from subscriber import MQTTClientSubscriber
from publish import MQTTClientPublisher
import json, random, asyncio

class LinhaProducaoOntologia:
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao2Agent(Agent):
    rateLinha2 = 0.0
    encomendaFinal = None
    encomendas = None
    stateBusy = False
    
    mqtt_broker = '192.168.137.202'
    mqtt_port = 1883
    mqtt_user = 'corkai'
    password = 'corkai123'
    topicDetect = "/b2/defect_found/mqtt"
    topicOrder = "/b2/cork_type/mqtt"  
    topicStop = "/b2/stop/mqtt"  

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
                        self.agent.add_behaviour(self.agent.EnviaEncomendaROS())
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
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())
                            LinhaProducao2Agent.stateBusy = True
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos")
                            print(LinhaProducao2Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda())
                    else:
                        melhorLinha = "linha3@jabbers.one"
                        await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", {"2ndbest": melhorLinha}, LinhaProducaoOntologia.INFORM)
                        if LinhaProducao2Agent.stateBusy == False:
                            LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 3)
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())
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
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())
                            LinhaProducao2Agent.stateBusy = True
                            print(f"{self.agent.jid}: fica com a 2nd melhor encomenda e envia aos robos") 
                            print(LinhaProducao2Agent.encomendaFinal)
                            self.agent.add_behaviour(self.agent.IniciaEncomenda())
                    else: 
                        if LinhaProducao2Agent.stateBusy == False:
                            LinhaProducao2Agent.encomendaFinal = await encomenda_prioritaria(LinhaProducao2Agent.encomendas, 1)
                            self.agent.add_behaviour(self.agent.EnviaEncomendaROS())
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
                    publisher = MQTTClientPublisher(LinhaProducao2Agent.mqtt_broker , LinhaProducao2Agent.mqtt_port, LinhaProducao2Agent.mqtt_user, LinhaProducao2Agent.password)
                    publisher.run()

                    message = int(1)
                    publisher.publish(LinhaProducao2Agent.topicStop, message)
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
            mqtt_client_instance = MQTTClientSubscriber(LinhaProducao2Agent.mqtt_broker , LinhaProducao2Agent.mqtt_port, LinhaProducao2Agent.mqtt_user, LinhaProducao2Agent.password, LinhaProducao2Agent.topicDetect, "0/0")
            mqtt_client_instance.run()

            while True:
                last_payload = mqtt_client_instance.get_last_payload()
                valores = last_payload.split('/')
                valor1 = int(valores[0])
                valor2 = int(valores[1])
                
                if (valor1 + valor2) >= 1:
                    print(f"{self.agent.jid}: inicia contagem de defeito")
                    break
            LinhaProducao2Agent.rateLinha2 = 0.0

            tamahoEncomenda = LinhaProducao2Agent.encomendaFinal["quantidade"]
            defeito = 0
            contagemTamanho = 0
            while True:
                last_payload = mqtt_client_instance.get_last_payload()
                valores = last_payload.split('/')
                defeito = int(valores[0])
                semDefeito = int(valores[1])
                defeito = random.randint(0, 1)
                contagemTamanho = defeito + semDefeito
                if defeito==0:
                    LinhaProducao2Agent.rateLinha2=0
                LinhaProducao2Agent.rateLinha2 = (defeito / contagemTamanho) * 100
    
                if LinhaProducao2Agent.rateLinha2 > 80.0 and contagemTamanho>5:
                    self.agent.add_behaviour(self.agent.AtingiuLimitePercentagem())  
                    
                print(f"{self.agent.jid}: " + str(defeito) + "..." + str(semDefeito) + "..." +  str(contagemTamanho) + "..."  + str(LinhaProducao2Agent.rateLinha2))
                if semDefeito == tamahoEncomenda:
                    mqtt_client_instance.client.loop_stop()
                    mqtt_client_instance.client.disconnect()
                    LinhaProducao2Agent.stateBusy = False

                    publisher = MQTTClientPublisher(LinhaProducao2Agent.mqtt_broker , LinhaProducao2Agent.mqtt_port, LinhaProducao2Agent.mqtt_user, LinhaProducao2Agent.password)
                    publisher.run()

                    message = int(1)
                    publisher.publish(LinhaProducao2Agent.topicStop, message)
                    publisher.client.loop_stop()
                    publisher.client.disconnect()
                    print(f"{self.agent.jid}: Acabou a encomenda")
                    await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", {"terminou": True}, LinhaProducaoOntologia.INFORM)
                    #voltar a escolhar encomenda 
                    break

    class AtingiuLimitePercentagem(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: atingiu limite de percentagem")
            result = await atingiuLimite("linha1@jabbers.one", "linha3@jabbers.one", LinhaProducao2Agent.rateLinha2,self, LinhaProducaoOntologia, LinhaProducao2Agent.encomendaFinal)    
            if result == 0:
                self.agent.add_behaviour(self.agent.ContaDefeitos()) 
            else:    
                LinhaProducao2Agent.encomendaFinal = result
                publisher = MQTTClientPublisher(LinhaProducao2Agent.mqtt_broker , LinhaProducao2Agent.mqtt_port, LinhaProducao2Agent.mqtt_user, LinhaProducao2Agent.password)
                publisher.run()
                message = int(1)
                publisher.publish(LinhaProducao2Agent.topicStop, message)
                publisher.client.loop_stop()
                publisher.client.disconnect()
                self.agent.add_behaviour(self.agent.EnviaEncomendaROS())
                self.agent.add_behaviour(self.agent.ContaDefeitos())

    class EnviaEncomendaROS(OneShotBehaviour):   
        async def run(self):
            publisher = MQTTClientPublisher(LinhaProducao2Agent.mqtt_broker , LinhaProducao2Agent.mqtt_port, LinhaProducao2Agent.mqtt_user, LinhaProducao2Agent.password)
            publisher.run()
    
            message = str(LinhaProducao2Agent.encomendaFinal["tipo"])
            publisher.publish(LinhaProducao2Agent.topicOrder, message)
            publisher.client.loop_stop()
            publisher.client.disconnect()                               

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebePropostasLinha1())
        self.add_behaviour(self.RecebePropostaDeTroca()) 
