from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import json
import asyncio

class DefeitoOntologia:
    DEFEITO = "defeito"

class ContadorDefeitosAgent3(Agent):
    class ContarDefeitosBehav(CyclicBehaviour):
        async def run(self):
            while True:
                defeitos = random.randint(0, 1)  # Simula a contagem de defeitos
                defeito_msg = Message(to=self.agent.linha_producao)
                defeito_msg.set_metadata("performative", DefeitoOntologia.DEFEITO)
                defeito_msg.body = json.dumps({"defeitos": defeitos})
                await self.send(defeito_msg)
                await asyncio.sleep(10)  # Simula o tempo entre a passagem de rolhas

    async def setup(self):
        self.linha_producao = "linha3@jabbers.one"  # Linha de produção alvo
        self.add_behaviour(self.ContarDefeitosBehav())

