from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade import message
import json

class RobotAgent(Agent):
    class NotifyProductionLineBehaviour(OneShotBehaviour):
        async def run(self):
            for msg in self.agent.ready_msgs:
                await self.send(msg)

    class ReceiveOrderBehaviour(CyclicBehaviour):
        async def run(self):
            if not self.agent.available:
                return
            msg = await self.receive(timeout=10)  # Aguarda a mensagem de encomenda
            if msg:
                content = json.loads(msg.body)
                task_type = content["task_type"] # Tipo de mensagem
                order = content["order"]
                print(f"Robot {self.agent.jid} received {task_type}: {order}")

                # Inicia o processo de votação
                self.agent.task_type = task_type
                self.agent.order = order
                self.agent.votes = [self.agent.jid]  # Adiciona o próprio voto
                next_robot = self.agent.robots[(self.agent.robots.index(self.agent.jid) + 1) % len(self.agent.robots)]
                vote_msg = message.Message(to=next_robot)
                vote_msg.body = json.dumps({"task_type": task_type, "order": order, "votes": self.agent.votes})
                await self.send(vote_msg)

    class ReceiveVoteBehaviour(CyclicBehaviour):
        async def run(self):
            if not self.agent.available:
                return
            msg = await self.receive(timeout=10)  # Aguarda a mensagem de voto
            if msg:
                vote = json.loads(msg.body)
                print(f"Robot {self.agent.jid} received votes: {vote}")

                # Adiciona o próprio voto
                vote["votes"].append(self.agent.jid)
                
                # Verifica se todos os votos foram recebidos
                if len(vote["votes"]) == len(self.agent.robots):
                    # Decisão tomada, envia mensagem para todos os robôs
                    available_robots = [r for r in self.agent.robots if self.agent.jid != r]
                    decision = min(available_robots)  # Seleciona o robô com menor JID disponível
                    self.agent.decision = decision
                    print(f"Robot {self.agent.jid} decision: {decision}")
                    for robot in self.agent.robots:
                        decision_msg = message.Message(to=robot)
                        decision_msg.body = json.dumps({"decision": decision})
                        await self.send(decision_msg)
                else:
                    # Repassa a votação para o próximo robô
                    next_robot = self.agent.robots[(self.agent.robots.index(self.agent.jid) + 1) % len(self.agent.robots)]
                    vote_msg = message.Message(to=next_robot)
                    vote_msg.body = json.dumps(vote)
                    await self.send(vote_msg)

    class InformDecisionBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # Aguarda a mensagem de decisão
            if msg:
                decision = json.loads(msg.body)
                print(f"Robot {self.agent.jid} informed of decision: {decision}")

                if decision["decision"] == self.agent.jid:
                    # Robô foi escolhido para realizar a tarefa
                    self.agent.available = False  # Marca o robô como indisponível
                    order = self.agent.order
                    task_type = self.agent.task_type
                    delivery_msg = message.Message(to=order["line"])
                    delivery_msg.body = json.dumps({"delivery": order})
                    await self.send(delivery_msg)
                    print(f"Robot {self.agent.jid} is handling {task_type}: {order}")

                    # Simula a tarefa e marca o robô como disponível novamente após a tarefa
                    self.agent.add_behaviour(self.agent.CompleteTaskBehaviour())

    class CompleteTaskBehaviour(OneShotBehaviour):
        async def run(self):
            # Simula o tempo da tarefa
            await self.sleep(5)
            print(f"Robot {self.agent.jid} has completed the task.")
            self.agent.available = True  # Marca o robô como disponível novamente

    async def setup(self):
        print(f"Robot Agent {self.jid} is ready.")
        self.production_lines = ["linha1@jabbers.one", "linha2@jabbers.one", "linha3@jabbers.one"]  
        self.robots = ["robot1@jabbers.one", "robot2@jabbers.one"]  # Lista de JIDs dos robôs
        self.ready_msgs = [message.Message(to=linha) for linha in self.production_lines]
        for msg in self.ready_msgs:
            msg.body = "pronto"
        self.available = True  # Indica se o robô está disponível para novas encomendas
        self.add_behaviour(self.NotifyProductionLineBehaviour())
        self.add_behaviour(self.ReceiveOrderBehaviour())
        self.add_behaviour(self.ReceiveVoteBehaviour())
        self.add_behaviour(self.InformDecisionBehaviour())
    
