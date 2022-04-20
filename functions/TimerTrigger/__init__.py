import logging
import os

import azure.functions as func
import azure.storage.queue as queue

# Optional environment variables
AWS_ENABLED = os.getenv("AWS_ENABLED", "0")
AZURE_ENABLED = os.getenv("AZURE_ENABLED", "0")

# Required environment variables
CONNECTION_STRING = os.environ["TABLE_SA_CONNECTION"]
QUEUE_NAME = os.environ["TIMER_QUEUE_NAME"]

AWS_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
AZURE_URL = "https://azurecomcdn.azureedge.net/en-gb/updates/feed/"
DELIMITER = "§"


def main(timer: func.TimerRequest) -> None:
    logging.info("AWS_ENABLED: {} AZURE_ENABLED: {}".format(AWS_ENABLED, AZURE_ENABLED))
    queue_client = queue.QueueClient.from_connection_string(CONNECTION_STRING, QUEUE_NAME,
                                                            message_encode_policy=queue.BinaryBase64EncodePolicy(),
                                                            message_decode_policy=queue.BinaryBase64DecodePolicy())

    if AWS_ENABLED == "1" or AWS_ENABLED.lower() == "true":
        queue_client.send_message(bytes("aws{}{}".format(DELIMITER, AWS_URL), "utf-8"))
        logging.info("Added `aws{}{}` to queue".format(DELIMITER, AWS_URL))
    if AZURE_ENABLED == "1" or AZURE_ENABLED.lower() == "true":
        queue_client.send_message(bytes("azure{}{}".format(DELIMITER, AZURE_URL), "utf-8"))
        logging.info("Added `azure{}{}` to queue".format(DELIMITER, AZURE_URL))
