from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade import message
import json

class RobotAgent2(Agent):
    async def setup(self):
        print(f"Robot Agent {self.jid} is ready.")
        self.production_lines = ["linha1@jabbers.one", "linha2@jabbers.one", "linha3@jabbers.one"]  # Lista de JIDs das linhas de produção
        self.ready_msgs = [message.Message(to=linha) for linha in self.production_lines]
        for msg in self.ready_msgs:
            msg.body = "pronto"
        self.add_behaviour(self.NotifyProductionLineBehaviour())
        self.add_behaviour(self.ReceiveOrderBehaviour())

    class NotifyProductionLineBehaviour(OneShotBehaviour):
        async def run(self):
            for msg in self.agent.ready_msgs:
                await self.send(msg)

    class ReceiveOrderBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # Aguarda a mensagem de encomenda
            if msg:
                order = json.loads(msg.body)
                print(f"Robot {self.agent.jid} received order: {order}")