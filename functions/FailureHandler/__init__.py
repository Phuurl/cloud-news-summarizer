import json
import logging
import os

import azure.functions as func
import requests

SLACK_FAILURE_WEBHOOK = os.environ["SLACK_FAILURE_WEBHOOK"]


def main(msg: func.QueueMessage) -> None:
    message = msg.get_body().decode("utf-8")
    logging.info("Processing {}".format(message))
    slack_payload = {"text": "Failed to process {}".format(message)}
    slack_response = requests.post(SLACK_FAILURE_WEBHOOK, json.dumps(slack_payload))
    if slack_response.status_code != 200:
        logging.error("Non-200 from Slack: {} {}".format(slack_response.status_code, slack_response.text))
        raise Exception("Failed to send to Slack")
