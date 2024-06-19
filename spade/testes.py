from paho.mqtt import client as mqtt_client

mqtt_broker = '172.18.131.112'
mqtt_port = 1883
mqtt_user = 'corkai'
password = 'corkai123'

getlijkh = ""

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe("/b1/defect_found/mqtt")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    getlijkh = msg.payload.decode()
    print(getlijkh)

def run():
    client = mqtt_client.Client()
    client.username_pw_set(username=mqtt_user, password=password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_broker, mqtt_port)
    client.loop_start()

    return client

def publish_to_mqtt(topic, message, client):
    result = client.publish(topic, message)
    return result

def subscribe(client):
    return client.subscribe("/b1/defect_found/mqtt")

if __name__ == "__main__":
    client = run()
    topic = "/b1/defect_found/mqtt"
    message = "Hello MQTT!"
    result = publish_to_mqtt(topic, message, client)
    #result = subscribe(client)

    print(f"Published `{message}` to topic `{topic}` with result: {result}")
