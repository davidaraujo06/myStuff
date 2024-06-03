from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from utils import *
import json 

class LinhaProducaoOntologia:
    PRONTO = "pronto"
    ENCOMENDA = "encomenda"
    DISCUSSAO = "discussao"
    PROPOSTA = "proposta"
    AGREE = "agree"

class LinhaProducao3Agent(Agent):
    class RecebeEncomendaBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Aguardando encomenda...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.ENCOMENDA:
                encomendas = json.loads(msg.body)
                print(f"{self.agent.jid}: Recebeu encomenda: {encomendas}")
                self.agent.encomendas = encomendas
                self.agent.add_behaviour(self.agent.PrimeiraRodadaDiscussaoBehav())

    class SetReadyBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Enviando mensagem de pronto...")
            ready_msg = message.Message(to="encomenda@jabbers.one")
            ready_msg.set_metadata("performative", LinhaProducaoOntologia.PRONTO)
            await self.send(ready_msg)

    class PrimeiraRodadaDiscussaoBehav(CyclicBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Iniciando primeira rodada de discussão de encomendas...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.DISCUSSAO:
                # Faz uma proposta para uma linha aleatória (exceto a própria)
                linha_destino = random.choice([linha for linha in self.agent.linhas_producao if linha != self.agent.jid])
                proposta_msg = message.Message(to=linha_destino)
                proposta_msg.set_metadata("performative", LinhaProducaoOntologia.PROPOSTA)
                proposta_msg.body = json.dumps(self.agent.encomendas)
                print(f"{self.agent.jid}: Fazendo proposta para {linha_destino}")
                await self.send(proposta_msg)

                resposta = await self.receive(timeout=10)
                if resposta and resposta.metadata["performative"] == LinhaProducaoOntologia.AGREE:
                    # Se a proposta for aceita, avança para a segunda rodada com a linha aceitante
                    print(f"{self.agent.jid}: Proposta aceita. Avançando para a segunda rodada.")
                    self.agent.add_behaviour(self.agent.SegundaRodadaDiscussaoBehav())

    class SegundaRodadaDiscussaoBehav(CyclicBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Iniciando segunda rodada de discussão de encomendas...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.DISCUSSAO:
                # Faz uma proposta para a próxima linha
                proposta_msg = message.Message(to=self.agent.linhas_producao[2])
                proposta_msg.set_metadata("performative", LinhaProducaoOntologia.PROPOSTA)
                proposta_msg.body = json.dumps(self.agent.encomendas)
                print(f"{self.agent.jid}: Fazendo proposta para {self.agent.linhas_producao[2]}")
                await self.send(proposta_msg)

                resposta = await self.receive(timeout=10)
                if resposta and resposta.metadata["performative"] == LinhaProducaoOntologia.AGREE:
                    # Se a proposta for aceita, avança para a terceira rodada com a linha aceitante
                    print(f"{self.agent.jid}: Proposta aceita. Avançando para a terceira rodada.")
                    self.agent.add_behaviour(self.agent.TerceiraRodadaDiscussaoBehav())

    class TerceiraRodadaDiscussaoBehav(CyclicBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Iniciando terceira rodada de discussão de encomendas...")
            msg = await self.receive(timeout=10)
            if msg and msg.metadata["performative"] == LinhaProducaoOntologia.DISCUSSAO:
                # Envia uma mensagem de confirmação para a linha aceitante
                confirmacao_msg = message.Message(to=msg.sender)
                confirmacao_msg.set_metadata("performative", LinhaProducaoOntologia.CONFIRMACAO)
                confirmacao_msg.body = json.dumps(self.agent.encomendas)
                print(f"{self.agent.jid}: Enviando confirmação para {msg.sender}")
                await self.send(confirmacao_msg)

    class WaitForReadyBehav(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid}: Aguardando todas as linhas de produção ficarem prontas...")
            while True:
                ready_msgs = []
                for _ in range(3):  # Espera por mensagens de prontidão de cada linha de produção
                    msg = await self.receive(timeout=10)
                    if msg and msg.metadata["performative"] == LinhaProducaoOntologia.PRONTO:
                        ready_msgs.append(msg)
                        print(f"{self.agent.jid}: Recebeu prontidão de {msg.sender}")

                if len(ready_msgs) == 3:  # Verifica se todas as linhas de produção estão prontas
                    print(f"{self.agent.jid}: Todas as linhas de produção estão prontas.")
                    for robo in ["robo1@jabbers.one", "robo2@jabbers.one"]:
                        msg = message.Message(to=robo)
                        msg.set_metadata("performative", "alguma_performativa")  # Substitua "alguma_performativa" pela performativa apropriada
                        msg.body = json.dumps({'kjh': 0})
                        await self.send(msg)
                    break

    async def setup(self):
        print(f"Linha de produção {self.jid} inicializada.")
        self.add_behaviour(self.SetReadyBehav())
        self.add_behaviour(self.RecebeEncomendaBehav())
        self.encomendas = []
        self.encomenda_escolhida = None
        self.linhas_producao = ["linha1@jabbers.one", "linha2@jabbers.one", "linha3@jabbers.one"]
