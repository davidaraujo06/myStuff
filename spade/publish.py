from paho.mqtt import client as mqtt_client

class MQTTClientPublisher:
    def __init__(self, broker, port, username, password):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password

        # Configuração do cliente MQTT
        self.client = mqtt_client.Client()
        self.client.username_pw_set(username=self.username, password=self.password)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Publisher connected to MQTT Broker!")
        else:
            print(f"Failed to connect publisher, return code {rc}")

    def run(self):
        self.client.on_connect = self.on_connect
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def publish(self, topic, message):
        result = self.client.publish(topic, message)
        return result

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

# # Exemplo de uso
# if __name__ == "__main__":
#     mqtt_broker = '172.18.131.112'
#     mqtt_port = 1883
#     mqtt_user = 'corkai'
#     password = 'corkai123'

#     publisher = MQTTClientPublisher(mqtt_broker, mqtt_port, mqtt_user, password)
#     publisher.run()

#     topic = "/b1/stop/mqtt"
#     message = 1
#     result = publisher.publish(topic, message)

#     print(f"Published `{message}` to topic `{topic}` with result: {result}")
