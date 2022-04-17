import datetime
import logging
import os
import time
from typing import Union

import azure.data.tables as tables
import azure.functions as func
import azure.storage.queue as queue
import feedparser

FEED_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"

# Gather required environment variables
CONNECTION_STRING = os.environ["TABLE_SA_CONNECTION"]
TABLE_NAME = os.environ["TABLE_NAME"]
QUEUE_NAME = os.environ["QUEUE_NAME"]
ENVIRONMENT = os.environ["ENVIRONMENT"]


def get_checkpoint(connection_string: str, table_name: str, partition_key: str, row_key: str) -> Union[int, None]:
    try:
        table_service = tables.TableServiceClient.from_connection_string(connection_string)
        table_client = table_service.get_table_client(table_name)
        checkpoint = table_client.get_entity(partition_key=partition_key, row_key=row_key)
        return int(checkpoint["ts"])
    except Exception as e:
        logging.warning("Exception getting checkpoint: {}".format(e))
        return None


def set_checkpoint(connection_string: str, table_name: str, partition_key: str, row_key: str) -> None:
    try:
        table_service = tables.TableServiceClient.from_connection_string(connection_string)
        table_client = table_service.get_table_client(table_name)
        checkpoint_out = {
            "PartitionKey": partition_key,
            "RowKey": row_key,
            "ts": str(int(time.time()))
        }
        table_client.upsert_entity(checkpoint_out)
    except Exception as e:
        logging.warning("Exception setting checkpoint: {}".format(e))


def get_rss(url: str, last_run: time.struct_time) -> Union[feedparser.FeedParserDict, None]:
    feed = feedparser.parse(url)
    try:
        if feed.feed.published_parsed > last_run:
            return feed
        else:
            logging.info("Feed not updated since last check")
            return None
    except Exception as e:
        logging.warning("Exception checking feed publish timestamp: {}".format(e))
        return feed


def process_entry(entry: feedparser.util.FeedParserDict, last_run: time.struct_time,
                  queue_client: queue.QueueClient) -> None:
    logging.info(type(queue_client))
    if entry.published_parsed > last_run:
        logging.info("New entry: {} {}".format(entry.title, entry.link))
        queue_client.send_message(bytes(entry.link, "utf-8"))
        logging.info("Added {} to queue".format(entry.link))


def main(timer: func.TimerRequest) -> None:
    checkpoint = get_checkpoint(CONNECTION_STRING, TABLE_NAME, "aws", ENVIRONMENT)
    if checkpoint is not None:
        logging.info("Using {} as checkpoint".format(checkpoint))
        feed = get_rss(FEED_URL, time.gmtime(checkpoint))
    else:
        logging.info("No checkpoint - using current time minus 30m")
        feed = get_rss(FEED_URL, time.gmtime(time.time() - (30 * 60)))

    if feed is not None:
        queue_client = queue.QueueClient.from_connection_string(CONNECTION_STRING, QUEUE_NAME,
                                                                message_encode_policy=queue.BinaryBase64EncodePolicy(),
                                                                message_decode_policy=queue.BinaryBase64DecodePolicy())
        for entry in feed.entries:
            process_entry(entry, time.gmtime(checkpoint), queue_client)

    set_checkpoint(CONNECTION_STRING, TABLE_NAME, "aws", ENVIRONMENT)
