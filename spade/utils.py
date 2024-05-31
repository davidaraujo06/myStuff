from spade.message import Message
from spade.template import Template
import json

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
