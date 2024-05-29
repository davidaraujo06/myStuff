from spade import agent, message, behaviour
import json

class LinhaProducaoOntologia:
    PRONTO = "pronto"
    ENCOMENDA = "encomenda"
    DISCUSSAO = "discussao"
    RESOLUCAO = "resolucao"
    CONFIRMACAO = "confirmacao"


class LinhaProducao1Agent(agent.Agent):
    class RecebeEncomendaBehav(behaviour.OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.ENCOMENDA:
                encomendas = json.loads(msg.body)
                print(f"Linha de Produção {self.agent.jid} recebeu encomenda: {encomendas}")
                self.agent.encomendas = encomendas
                self.agent.add_behaviour(self.agent.DiscussaoEncomendasBehav())

    class SetReadyBehav(behaviour.OneShotBehaviour):
        async def run(self):
            ready_msg = message.Message(to="encomenda@jabbers.one")
            ready_msg.set_metadata("performative", LinhaProducaoOntologia.PRONTO)
            await self.send(ready_msg)

    class DiscussaoEncomendasBehav(behaviour.OneShotBehaviour):
        async def run(self):
            if not self.agent.encomendas:
                print(f"{self.agent.jid}: Sem encomendas para discutir.")
                return

            print(f"{self.agent.jid}: Iniciando discussão de encomendas...")
            for linha in self.agent.linhas_producao:
                if linha != self.agent.jid:
                    discussao_msg = message.Message(to=linha)
                    discussao_msg.set_metadata("performative", LinhaProducaoOntologia.DISCUSSAO)
                    discussao_msg.body = json.dumps(self.agent.encomendas)
                    print(f"{self.agent.jid}: Enviando discussão para {linha}")
                    await self.send(discussao_msg)

            resolucao_msgs = []
            while len(resolucao_msgs) < len(self.agent.linhas_producao) - 1:
                msg = await self.receive(timeout=10)
                if msg and msg.metadata["performative"] == LinhaProducaoOntologia.RESOLUCAO:
                    resolucao_msgs.append(json.loads(msg.body))
                    print(f"{self.agent.jid}: Recebeu resolução de {msg.sender}: {msg.body}")

            resolucoes = resolucao_msgs + [self.agent.encomendas]
            self.agent.encomenda_escolhida = sorted(resolucoes, key=lambda e: e['prioridade'])[0]
            print(f"{self.agent.jid}: Encomenda escolhida: {self.agent.encomenda_escolhida}")

    class WaitForReadyBehav(behaviour.OneShotBehaviour):
        async def run(self):
            while True:
                ready_msgs = []
                for _ in range(3):  # Espera por mensagens de prontidão de cada linha de produção
                    msg = await self.receive(timeout=10)
                    if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PRONTO:
                        ready_msgs.append(msg)
                
                if len(ready_msgs) == 3:  # Verifica se todas as linhas de produção estão prontas
                    for robo in ["robo1@jabbers.one", "robo2@jabbers.one"]:
                        msg = message.Message(to=robo)
                        msg.set_metadata("performative", "alguma_performativa")  # Substitua "alguma_performativa" pela performativa apropriada
                        msg.body = json.dumps({'kjh':0})
                        await self.send(msg)
                    break     


    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.encomendas = []
        self.encomenda_escolhida = None
        self.linhas_producao = ["linha2@jabbers.one", "linha3@jabbers.one"]
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebeEncomendaBehav())