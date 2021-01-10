# importere libraries
import paho.mqtt.client as paho
import ssl
import time
import json
from sense_hat import SenseHat

sense = SenseHat()
connflag = False
debug = False


def on_connect(client, userdata, flags, rc):  # Metode for at forbinde
    global connflag
    print("Connected to AWS")
    connflag = True
    print("Connection returned result: " + str(rc))  # Printer en return code.


def on_message(client, userdata, msg):  # Metode til at sende beskeder
    global debug
    if "Debug On" in str(msg.payload.decode("utf-8")):
        debug = True
        print("Debug Mode is now turned on. 10 degrees is added to the temperature.")
    elif "Debug Off" in str(msg.payload.decode("utf-8")):
        debug = False
        print("Debug Mode is now turned off. Temperature is now normal.")


# def on_log(client, userdata, level, buf):
#    print(msg.topic+" "+str(msg.payload))

mqttc = paho.Client()
# create an mqtt client object
# attach call back function
mqttc.on_connect = on_connect
# attach on_connect function written in the
# mqtt class, (which will be invoked whenever
# mqtt client gets connected with the broker)
# is attached with the on_connect function
# written by you.

mqttc.on_message = on_message  # assign on_message func
# attach on_message function written inside
# mqtt class (which will be invoked whenever
# mqtt client gets a message) with the on_message
# function written by you

#### Parametre for at kunne forbinde til AWS ####
awshost = "a182hxk2qb3hby-ats.iot.us-west-2.amazonaws.com"  # Endpoint
awsport = 8883  # Port no.
clientId = "RaspberryPi"  # Thing_Name
thingName = "RaspberryPi"  # Thing_Name
caPath = "certs/root-CA.crt"  # Amazon's certificate from Third party
certPath = "certs/RaspberryPi.cert.pem"  # <Thing_Name>.cert.pem.crt. Thing certifikat fra Amazon
keyPath = "certs/RaspberryPi.private.key"  # <Thing_Name>.private.key Thing private key fra Amazon

mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2,
              ciphers=None)  # Certifikat og private key for at skabe en sikker forbindelse.

mqttc.connect(awshost, awsport, keepalive=60)  # Forbind til AWS server
mqttc.subscribe("TemperatureSensorTopicDebug")  # Subscribe til denne topic,
# bliver brugt til at bestemme om enheden er i debug mode eller ej

mqttc.loop_start()  # Starter en thread i baggrunden og looper metoderne.

while 1:
    time.sleep(10)
    if connflag:
        time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
        if debug:
            temp_reading = round(sense.get_temperature(), 1) + 10
        else:
            temp_reading = round(sense.get_temperature(), 1)
        sensor_location = "Hjem"
        sensor_group = "Køkken"
        if temp_reading > 30:
            alarm_triggered = True
        else:
            alarm_triggered = False
        alarm_acknowledged = False

        if debug:
            telemetry_data_point = {
                "timeStamp": time_stamp,
                "temperature": temp_reading,
                "sensorLocation": sensor_location,
                "sensorGroup": sensor_group,
                "alarmTriggered": alarm_triggered,
                "alarmAcknowledged": alarm_acknowledged,
                "debugOn": debug
            }
        else:
            telemetry_data_point = {
                "timeStamp": time_stamp,
                "temperature": temp_reading,
                "sensorLocation": sensor_location,
                "sensorGroup": sensor_group,
                "alarmTriggered": alarm_triggered,
                "alarmAcknowledged": alarm_acknowledged
            }

        json_msg = json.dumps(telemetry_data_point) # Konverter til JSON
        mqttc.publish("TemperatureSensorTopic", json_msg, 1)  # topic: temperature # Publishing Temperature values
        print("msg sent: temperature " + "%.2f" % temp_reading + " Debug on: " + str(
            debug))  # Print sent temperature msg on console
    else:
        print("waiting for connection...")
