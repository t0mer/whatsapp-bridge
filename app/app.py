import io
import os
import sys
import json
from loguru import logger
from manish import MaNish
from manish.template import *
from fastapi import FastAPI, Request
from confighandler import ConfigHandler
from gmqtt.mqtt.constants import MQTTv311
from fastapi.responses import HTMLResponse
from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT
from fastapi.templating import Jinja2Templates


os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'C.UTF-8'
LOG_LEVEL = os.getenv("LOG_LEVEL")

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)



config = ConfigHandler().config
mqtt_config = MQTTConfig()
app = FastAPI()
mqtt_config.host = config.get("MQTT","mqtt.host")
mqtt_config.port = config.get("MQTT","mqtt.port")
mqtt_config.username = config.get("MQTT","mqtt.username")
mqtt_config.password = config.get("MQTT","mqtt.password")
mqtt_config.version = MQTTv311
fast_mqtt = FastMQTT(config=mqtt_config)
fast_mqtt.init_app(app)
templates = Jinja2Templates(directory="templates/")
webhook_base_url=config.get("Whatsapp","webhook.base_url")
manish = MaNish(config.get("Whatsapp","api.token"),  phone_number_id=str(config.get("Whatsapp","api.phone_id")))

@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    logger.debug("Connected to {}".format(mqtt_config.host))


@fast_mqtt.subscribe("whatsapp/send")
async def message_to_topic(client, topic, payload, qos, properties):
    try:
        payload = json.loads(payload.decode())
        send_message(payload["message"],payload["phone"],"","")
    except Exception as e:
        logger.error("oh snap something went wrong. "+ e)

@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    logger.debug("Disconnected from {}".format(mqtt_config.host))


@app.get(webhook_base_url, include_in_schema=False)
async def verify(request: Request):
    if request.query_params.get('hub.mode') == "subscribe" and request.query_params.get("hub.challenge"):
        if not request.query_params.get('hub.verify_token') == config.get("Whatsapp","webhook.token"): #os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return int(request.query_params.get('hub.challenge'))
    return "Hello world", 200


@app.get("/disclaimer", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse('disclaimer.html', context={'request': request})

@app.get("/send")
def send(phone: str= "", message: str = "",template:str = "", language: str = ""):
    return send_message(message,phone,template,language)

@app.post(webhook_base_url, include_in_schema=False)
async def webhook(request: Request):
    data = await request.json()
    changed_field = manish.changed_field(data)
    if changed_field == "messages":
        new_message = manish.get_mobile(data)
        if new_message:
            mobile = manish.get_mobile(data)
            name = manish.get_name(data)
            message_type = manish.get_message_type(data)
            if message_type == "text":
                message = manish.get_message(data)
                fast_mqtt.publish("whatsapp/received",'{"sender":"' + mobile + '","message":"' + message + '"}')
        else:
            delivery = manish.get_delivery(data)
            if delivery:
                print(f"Message : {delivery}")
    return "ok"


def send_message(message,recipient,template:str = "",language:str ="" ):
    try:
        logger.debug("Sending message to: {}".format(recipient))
        if not template or template == "":
            template=config.get("Whatsapp","api.template_name")
        if not language or language== "":
            language=config.get("Whatsapp","api.template_language") 

        if template:
            parameter = Parameter(type="text",text = message)
            body = Component(type="body",parameters=[parameter])
            manish.send_template(components=TemplateEncoder().encode([body]),recipient_id=recipient,template=template,lang=language)
            logger.debug("Message sent using template")
        else:
            manish.send_message(message=message,recipient_id=recipient)
            logger.debug("Message sent using text message")
        return "ok"
    except Exception as e:
        logger.error("Error sending message to: {}. {}".format(str(recipient),str(e)))
        return e
    

