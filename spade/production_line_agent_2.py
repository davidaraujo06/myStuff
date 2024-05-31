from spade import agent, behaviour
from utils import *
import json, random, asyncio

class LinhaProducaoOntologia:
    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao2Agent(agent.Agent):
    class RecebeEncomendaBehav(behaviour.OneShotBehaviour):
        async def run(self):
            global ENCOMENDAS
            print(f"{self.agent.jid}: Aguardando encomenda...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.REQUEST:
                ENCOMENDAS = json.loads(msg.body)
                print(f"{self.agent.jid}: Recebeu encomenda: {ENCOMENDAS}")

    class SetReadyBehav(behaviour.OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            await sendMessage(self, self.agent.jid, "encomenda@jabbers.one", "performative", "pronto", LinhaProducaoOntologia.INFORM)

    class RecebePropostasLinha1(behaviour.OneShotBehaviour):
        async def run(self):
            rate = 80
            melhorLinha = ""
            await asyncio.sleep(20)
            print(f"{self.agent.jid}: Aguardando Proposta...")
            msg = await self.receive(timeout=10)
            print(msg)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                print("começa decisão ....")
                if rate == int(msg.body):
                    melhorLinha = random.choice(self.linhas_producao)
                    print("aleatória ....")
                elif rate > int(msg.body): 
                    melhorLinha = "linha2@jabbers.one"
                    print(melhorLinha)
                else:
                    print(melhorLinha)

            if melhorLinha == "linha1@jabbers.one":
                await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", f"{self.agent.jid} sou a pior linha devido ao meu rate ser :" + str(rate) + " < que o rate da linha1: "+ str(msg.body)+ " e por isso fico com a seguinte encomenda: "+ f"{ENCOMENDAS[1]} e tu ficas com a melhor", LinhaProducaoOntologia.INFORM)
            else: 
                await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", f"{self.agent.jid} sou a melhor linha devido ao meu rate ser :" + str(rate) + " > que o rate da linha2: "+ str(msg.body)+ " e por isso fico com a seguinte encomenda: "+ f"{ENCOMENDAS[0]} e tu ficas com a segunda melhor", LinhaProducaoOntologia.INFORM)

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.encomendas = []
        self.encomenda_escolhida = None
        self.linhas_producao = ["linha1@jabbers.one", "linha2@jabbers.one"]
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebeEncomendaBehav())
        self.add_behaviour(self.RecebePropostasLinha1())