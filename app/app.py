import io
import os
import sys
import json
import requests
from loguru import logger
from heyoo import WhatsApp
from fastapi import FastAPI, Request
from confighandler import ConfigHandler
from gmqtt.mqtt.constants import MQTTv311
from fastapi.responses import HTMLResponse
from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT
from fastapi.templating import Jinja2Templates


# os.environ['PYTHONIOENCODING'] = 'utf-8'
# os.environ['LANG'] = 'C.UTF-8'
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

messenger = WhatsApp(config.get("Whatsapp","api.token"),  phone_number_id=str(config.get("Whatsapp","api.phone_id")))

@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    logger.debug("Connected to {}".format(mqtt_config.host))


@fast_mqtt.subscribe("whatsapp/send")
async def message_to_topic(client, topic, payload, qos, properties):
    try:
        payload = json.loads(payload.decode())
        send_message(payload["message"],payload["recipient"])
    except Exception as e:
        logger.error("oh snap something went wrong. "+ e)
@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    logger.debug("Disconnected from {}".format(mqtt_config.host))

@fast_mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print("subscribed", client, mid, qos, properties)


@app.get("/")
async def verify(request: Request):
    logger.warning(request.query_params.get('hub.mode'))
    if request.query_params.get('hub.mode') == "subscribe" and request.query_params.get("hub.challenge"):
        if not request.query_params.get('hub.verify_token') == config.get("Whatsapp","webhook.token"): #os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return int(request.query_params.get('hub.challenge'))
    return "Hello world", 200


@app.get("/disclaimer", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('disclaimer.html', context={'request': request})



@app.post('/', include_in_schema=False)
async def webhook(request: Request):
    data = await request.json()
    
    logger.info("Received webhook data: {}".format(data))
    changed_field = messenger.changed_field(data)
    if changed_field == "messages":
        new_message = messenger.get_mobile(data)
        if new_message:
            mobile = messenger.get_mobile(data)
            name = messenger.get_name(data)
            message_type = messenger.get_message_type(data)
            logger.info(
                f"New Message; sender:{mobile} name:{name} type:{message_type}"
            )
            if message_type == "text":
                message = messenger.get_message(data)
                name = messenger.get_name(data)
                logger.info(message)

                fast_mqtt.publish("whatsapp/get",'{"sender":"' + mobile + '","message":"' + message + '"}')
                # messenger.send_message(f"Hi {name}, nice to connect with you", mobile)

            elif message_type == "interactive":
                message_response = messenger.get_interactive_response(data)
                intractive_type = message_response.get("type")
                message_id = message_response[intractive_type]["id"]
                message_text = message_response[intractive_type]["title"]
                logger.info(f"Interactive Message; {message_id}: {message_text}")

            elif message_type == "location":
                message_location = messenger.get_location(data)
                message_latitude = message_location["latitude"]
                message_longitude = message_location["longitude"]
                logger.info("Location: %s, %s", message_latitude, message_longitude)

            elif message_type == "image":
                image = messenger.get_image(data)
                image_id, mime_type = image["id"], image["mime_type"]
                image_url = messenger.query_media_url(image_id)
                image_filename = messenger.download_media(image_url, mime_type)
                print(f"{mobile} sent image {image_filename}")
                logger.info(f"{mobile} sent image {image_filename}")

            elif message_type == "video":
                video = messenger.get_video(data)
                video_id, mime_type = video["id"], video["mime_type"]
                video_url = messenger.query_media_url(video_id)
                video_filename = messenger.download_media(video_url, mime_type)
                print(f"{mobile} sent video {video_filename}")
                logger.info(f"{mobile} sent video {video_filename}")

            elif message_type == "audio":
                audio = messenger.get_audio(data)
                audio_id, mime_type = audio["id"], audio["mime_type"]
                audio_url = messenger.query_media_url(audio_id)
                audio_filename = messenger.download_media(audio_url, mime_type)
                print(f"{mobile} sent audio {audio_filename}")
                logger.info(f"{mobile} sent audio {audio_filename}")

            elif message_type == "file":
                file = messenger.get_file(data)
                file_id, mime_type = file["id"], file["mime_type"]
                file_url = messenger.query_media_url(file_id)
                file_filename = messenger.download_media(file_url, mime_type)
                print(f"{mobile} sent file {file_filename}")
                logger.info(f"{mobile} sent file {file_filename}")
            else:
                print(f"{mobile} sent {message_type} ")
                print(data)
        else:
            delivery = messenger.get_delivery(data)
            if delivery:
                print(f"Message : {delivery}")
            else:
                print("No new message")
    return "ok"





def send_message(message,recipient):
    messenger.send_message(message, recipient)
    