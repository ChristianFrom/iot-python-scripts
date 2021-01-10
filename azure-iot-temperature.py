import time
import json
import threading

from sense_hat import SenseHat
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse

sense = SenseHat()
CONNECTION_STRING = "HostName=RaspberryPi-IoT-CF.azure-devices.net;" \
                    "DeviceId=Raspberry_Pi;" \
                    "SharedAccessKey=EneaFPzhb40dv4v3XBy6f/8DP+BIVC6U5G6vM/G/Bkg="
DEBUG = False


def iothub_client_init():
    # Create an IoT Hub client
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    return client


def device_method_listener(device_client):
    global DEBUG
    while True:
        method_request = device_client.receive_method_request()
        print(
            "\nMethod callback called with:\nmethodName = {method_name}\nDebug Mode = {payload}".format(
                method_name=method_request.name,
                payload=method_request.payload
            )
        )
        if method_request.name == "SetDebugMode":
            try:
                if "True" in method_request.payload:
                    DEBUG = True
                else:
                    DEBUG = False
            except ValueError:
                response_payload = {"Response": "Invalid parameter"}
                response_status = 400
            else:
                response_payload = {"Response": "Executed direct method {method_name} and Debug Mode = {debug}".format(
                    method_name=method_request.name, debug=DEBUG
                )
                }
                response_status = 200
        else:
            response_payload = {"Response": "Direct method {} not defined".format(method_request.name)}
            response_status = 404

        method_response = MethodResponse(method_request.request_id, response_status, payload=response_payload)
        device_client.send_method_response(method_response)


def iothub_client_telemetry_run():
    try:
        client = iothub_client_init()
        print("IoT Hub device sending messages, press Ctrl-C to exit")

        # Start a thread to listen
        device_method_thread = threading.Thread(target=device_method_listener, args=(client,))
        device_method_thread.daemon = True
        device_method_thread.start()

        while True:
            # Build the message.
            time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
            if DEBUG:
                temp_reading = round(sense.get_temperature(), 1) + 10
            else:
                temp_reading = round(sense.get_temperature(), 1)
            sensor_location = "Hjem"
            sensor_group = "Kontor"
            if temp_reading > 30:
                alarm_triggered = True
            else:
                alarm_triggered = False
            alarm_acknowledged = False

            telemetry_data_point = {
                "timeStamp": time_stamp,
                "temperature": temp_reading,
                "sensorLocation": sensor_location,
                "sensorGroup": sensor_group,
                "alarmTriggered": alarm_triggered,
                "alarmAcknowledged": alarm_acknowledged
            }

            json_msg = json.dumps(telemetry_data_point)
            message = Message(json_msg)

            # Send the message.
            print("Sending message: {}".format(message))
            client.send_message(message)
            print("Message successfully sent")
            time.sleep(10)

    except KeyboardInterrupt:
        print("IoT Hub Client stopped")


if __name__ == '__main__':
    print("Azure IoT Hub")
    print("Press Ctrl-C to exit")
    iothub_client_telemetry_run()
