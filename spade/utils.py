from spade.message import Message
from spade.template import Template
from datetime import datetime
from paho.mqtt import client as mqtt_client
import json, asyncio

async def sendMessage(self, sender, receiver, typeMessage, message_content, metadata):
    # Serializa o conteúdo da mensagem para JSON se não for uma string
    if not isinstance(message_content, str):
        message_body = json.dumps(message_content)
    else:
        message_body = message_content
    
    # Cria e configura o template para comparação
    template = Template()
    template.sender = str(sender)
    template.to = receiver
    template.body = message_body
    template.thread = "thread-id"
    template.metadata = {typeMessage: str(metadata)}

    # Cria e configura a mensagem
    msg = Message()
    msg.sender = str(sender)
    msg.to = receiver
    msg.body = message_body
    msg.thread = "thread-id"
    msg.set_metadata(typeMessage, str(metadata))

    assert template.match(msg)
    
    # Envia a mensagem
    await self.send(msg)
    print("Message sent!")

def carregarEncomendas(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def guardarEncomendas(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)     

async def encomenda_prioritaria(clientes, posicao):
    prioridade_ordem = {"Alta": 1, "Media": 2, "Baixa": 3}
    
    # Ordena os clientes por prioridade e prazo de entrega
    clientes_ordenados = sorted(clientes.keys(), key=lambda cliente: (
        prioridade_ordem[clientes[cliente]["prioridade"]],
        datetime.strptime(clientes[cliente]["prazo_entrega"], '%Y-%m-%d')
    ))
    
    # Retorna o cliente correspondente à posição desejada
    cliente_prioritario = clientes_ordenados[posicao - 1]

    data = carregarEncomendas("./encomendas.json")

    data["clientes"].pop(cliente_prioritario)
    guardarEncomendas("./encomendas.json", data)

    return clientes[cliente_prioritario]

async def atingiuLimite(nomeLinha1, nomeLinha2, percentagem_defeito,self, LinhaProducaoOntologia, encomendaFinal):
            
            await sendMessage(self, self.agent.jid, nomeLinha1, "performative", {"rate": "envia o teu rate"}, LinhaProducaoOntologia.PROPOSE)
            await asyncio.sleep(10)
            msgLinha1 = await self.receive(timeout=10)
            rateLinha1 = json.loads(msgLinha1.body)["rate"]
            await sendMessage(self, self.agent.jid, nomeLinha2, "performative", {"rate":  "envia o teu rate"}, LinhaProducaoOntologia.PROPOSE)
            await asyncio.sleep(10)
            msgLinha2 = await self.receive(timeout=10)
            rateLinha2 = json.loads(msgLinha2.body)["rate"]

            if percentagem_defeito > float(rateLinha1) or percentagem_defeito > float(rateLinha2) or percentagem_defeito > 0.0: 

                if float(rateLinha1) > float(rateLinha2):
                    await sendMessage(self, self.agent.jid, nomeLinha2, "performative", {"encomenda": encomendaFinal}, LinhaProducaoOntologia.INFORM)
                    await asyncio.sleep(10)
                    msgLinhaFinal = await self.receive(timeout=10) 
                    print(f"{self.agent.jid}: recebe encomenda")
                    print(msgLinhaFinal)
                    return json.loads(msgLinhaFinal.body)["encomenda"]
                elif float(rateLinha1) < float(rateLinha2):
                    await sendMessage(self, self.agent.jid, nomeLinha1, "performative", {"encomenda": encomendaFinal}, LinhaProducaoOntologia.INFORM)
                    await asyncio.sleep(10)
                    msgLinhaFinal = await self.receive(timeout=10) 
                    print(f"{self.agent.jid}: recebe encomenda")
                    print(msgLinhaFinal.body)
                    return json.loads(msgLinhaFinal.body)["encomenda"]
                else:
                    print("Nao houve troca pois as outras linhas tem este rate: " + str(nomeLinha1) + "-->" + str(rateLinha1) + "..." +  str(nomeLinha2) + "-->" + str(rateLinha2) + "\ne a " + f"{self.agent.jid}: linha que precisava de troca tem : "+ str(rateLinha2)) 
                    return 0

            else:
                print("Nao houve troca pois as outras linhas tem este rate: " + str(nomeLinha1) + "-->" + str(rateLinha1) + "..." +  str(nomeLinha2) + "-->" + str(rateLinha2) + "\ne a " + f"{self.agent.jid}: linha que precisava de troca tem : "+ str(rateLinha2)) 
                return 0
            # se for igual não faz nada        

async def recebePropostaTroca(self, LinhaProducaoOntologia, rateAtual, encomendaFinal, msgLinha):
    await sendMessage(self, self.agent.jid, str(msgLinha.sender), "performative", {"rate":  rateAtual}, LinhaProducaoOntologia.INFORM)
    
    await asyncio.sleep(25)
    #recebe mensagem de troca caso seja para ele
    msgLinhaFinal = await self.receive(timeout=10)
    if msgLinhaFinal:
        print(f"{self.agent.jid}: recebe encomenda")
        print(msgLinhaFinal.body)
        await sendMessage(self, self.agent.jid, str(msgLinhaFinal.sender), "performative", {"encomenda":  encomendaFinal}, LinhaProducaoOntologia.INFORM)
        return json.loads(msgLinhaFinal.body)["encomenda"]
    else:
        return 0
        #envia mensagem aos robos


# subscriber------------------------------------------------------------------       
 
mqtt_broker = 'localhost'
mqtt_port = 1883
mqtt_user = 'corkai'
password = 'corkai123'

def on_connect(client, userdata, flags, rc):
    print('on_connect')
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def on_message(client, userdata, msg):
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

def run():
    client = mqtt_client.Client()
    client.username_pw_set(username=mqtt_user, password=password)
    client.on_connect = on_connect
    client.connect(mqtt_broker, mqtt_port)
    client.on_message = on_message
    return client