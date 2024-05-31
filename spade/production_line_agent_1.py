from spade import agent, behaviour
from utils import *
import json 

class LinhaProducaoOntologia:
    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"

class LinhaProducao1Agent(agent.Agent):
    class RecebeEncomendaBehav(behaviour.OneShotBehaviour):
        async def run(self):
            global ENCOMENDAS
            print(f"{self.agent.jid}: Aguardando encomenda...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.REQUEST:
                ENCOMENDAS = json.loads(msg.body)
                print(f"{self.agent.jid}: Recebeu encomenda: {ENCOMENDAS}")
                self.agent.encomendas = ENCOMENDAS
                self.agent.add_behaviour(self.agent.ProposeEncomendaBehav())

    class SetReadyBehav(behaviour.OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            await sendMessage(self, self.agent.jid, "encomenda@jabbers.one", "performative", "pronto", LinhaProducaoOntologia.INFORM)

    class ProposeEncomendaBehav(behaviour.OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de posposta...")
            await sendMessage(self, self.agent.jid, "linha2@jabbers.one", "performative", "100", LinhaProducaoOntologia.PROPOSE)  

    class RecebeRespostaLinha2(behaviour.OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Aguardando decisão da linha 2...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.INFORM:
                print(f"{self.agent.jid}: Recebeu a seguinte decisão:  \n{msg.body}")     

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.encomendas = []
        self.encomenda_escolhida = None
        self.linhas_producao = ["linha1@jabbers.one", "linha2@jabbers.one"]
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebeEncomendaBehav())
