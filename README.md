# Whatsapp-bridge
Whatsapp-bridge is a lightweight application written in python and FastAPI-MQTT. 
I created WhatsApp-bridge to have the ability to send WhatsApp notifications easily from any application or IoT platform using MQTT topics or HTTP calls and without needing to write an extension for every application or device in the network.
To maintain the ability to combine MQTT and Web server, I’m using the [FastAPI-MQTT](https://sabuhish.github.io/fastapi-mqtt/).

## Features
- Send text message.
- Send template message.
- Send messages using REST API call or MQTT topic publising.
- Receive message from whatsapp and forward it om MQTT.

## Components and Frameworks used in Voicy
* [Loguru](https://pypi.org/project/loguru/)
* [configparser](https://pypi.org/project/configparser/)
* [FastAPI-MQTT](https://sabuhish.github.io/fastapi-mqtt/).
* [heyoo](https://github.com/Neurotech-HQ/heyoo) - Unofficial python wrapper to [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)