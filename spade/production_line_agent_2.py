from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from utils import *
import json, random, asyncio

class LinhaProducaoOntologia:
    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao2Agent(Agent):

    class SetReadyBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", "pronto", LinhaProducaoOntologia.INFORM)

    class RecebePropostasLinha1(OneShotBehaviour):
        async def run(self):
            rate = 10
            melhorLinha = ""
            await asyncio.sleep(5)
            print(f"{self.agent.jid}: Aguardando Proposta...")
            msg = await self.receive(timeout=10)
            respondeJSON = json.loads(msg.body)
            rateLinha2 = int(respondeJSON[0]["rateDefeitos"])
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PROPOSE:
                print("começa decisão ....")
                if rate == rateLinha2:
                    linhas = ["linha1@jabbers.one", "linha2@jabbers.one"]
                    melhorLinha = random.choice(linhas)
                    print("aleatória ....")
                elif rate > rateLinha2: 
                    melhorLinha = "linha2@jabbers.one"

                else:
                    melhorLinha = "linha1@jabbers.one"
                print(melhorLinha)
            if melhorLinha == "linha1@jabbers.one":
                await sendMessage(self, self.agent.jid, "linha1@jabbers.one", "performative", {"best": "linha1@jabbers.one"}, LinhaProducaoOntologia.INFORM)
            else: 
                # enviar mensagem á linha 3
                await sendMessage(self, self.agent.jid, "linha3@jabbers.one", "performative", [], LinhaProducaoOntologia.INFORM)

                ##TODO: nota: linha 1 e dois vão enviar á linha 3, caso seja a 1 ou 2 a ganhar então a 3 informa a 1 (usar o msg.sender) e depois fala com a 2 para saber quem fica com o resto 
                # caso seja a 3 a ganhar então a tres fica com a maior e depois informa a 1 ou 2 a dizer que perderam e como a 1 e a 2 já se conforntaram ja sabem quem é pior ou melhor
                # ao fim disso ver melhor o caso dos rates e ter uma função sempre a cada 10 segundos a calcular a percentagem e ao fim disso ver mensagens trocadas com robos

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebePropostasLinha1())
