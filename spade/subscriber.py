from paho.mqtt import client as mqtt_client

class MQTTClientSubscriber:
    def __init__(self, broker, port, username, password, topic):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.last_payload = "0/0"

        # Configuração do cliente MQTT
        self.client = mqtt_client.Client()
        self.client.username_pw_set(username=self.username, password=self.password)
        self.client.user_data_set(self.topic)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.topic)  # Usar o tópico diretamente
            print(f"Subscribed to topic: {self.topic}")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        self.last_payload = msg.payload.decode()

    def run(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()  # Use loop_start para rodar o loop em segundo plano

    def get_last_payload(self):
        return self.last_payload

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
