from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from utils import *
import random
import asyncio

class DefeitoOntologia:
    DEFEITO = "defeito"

class ContadorDefeitosAgent2(Agent):
    class ContarDefeitosBehav(CyclicBehaviour):
        async def run(self):
            while True:
                total = 0
                nrDefeitos=0
                defeitos = random.randint(0, 1)  # Simula a contagem de defeitos
                sendMessage(self, self.agent.jid, self.agent.linha_producao, "performative", {"defeitos": (defeitos/total)*100}, DefeitoOntologia.DEFEITO)
                await asyncio.sleep(10)
                total += 1# Simula o tempo entre a passagem de rolhas
                nrDefeitos += defeitos

    async def setup(self):
        self.linha_producao = "linha2@jabbers.one"  # Linha de produção alvo
        self.add_behaviour(self.ContarDefeitosBehav())

