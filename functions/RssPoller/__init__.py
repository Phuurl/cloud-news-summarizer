import logging
import os
import time
from typing import Union

import azure.data.tables as tables
import azure.functions as func
import azure.storage.queue as queue
import feedparser

# Gather required environment variables
CONNECTION_STRING = os.environ["TABLE_SA_CONNECTION"]
TABLE_NAME = os.environ["TABLE_NAME"]
QUEUE_NAME = os.environ["PROCESS_QUEUE_NAME"]
ENVIRONMENT = os.environ["ENVIRONMENT"]

FEED_CHECKPOINT_KEY = "latest-feed"
ARTICLE_CHECKPOINT_KEY = "latest-article"
DELIMITER = "§"


def get_checkpoint(connection_string: str, table_name: str, partition_key: str, row_key: str) -> Union[float, None]:
    try:
        table_service = tables.TableServiceClient.from_connection_string(connection_string)
        table_client = table_service.get_table_client(table_name)
        checkpoint = table_client.get_entity(partition_key=partition_key, row_key=row_key)
        return float(checkpoint["ts"])
    except Exception as e:
        logging.warning("Exception getting checkpoint: {}".format(e))
        return None


def set_checkpoint(connection_string: str, table_name: str, partition_key: str, row_key: str, ts: float) -> None:
    try:
        table_service = tables.TableServiceClient.from_connection_string(connection_string)
        table_client = table_service.get_table_client(table_name)
        checkpoint_out = {
            "PartitionKey": partition_key,
            "RowKey": row_key,
            "ts": str(ts)
        }
        table_client.upsert_entity(checkpoint_out)
    except Exception as e:
        logging.warning("Exception setting checkpoint: {}".format(e))


def get_rss(url: str, cloud: str, last_run: time.struct_time) -> Union[feedparser.FeedParserDict, None]:
    feed = feedparser.parse(url)
    if cloud == "aws":
        try:
            if feed.feed.published_parsed > last_run:
                return feed
            else:
                logging.info("Feed not updated since last check")
                return None
        except Exception as e:
            logging.warning("Exception checking {} feed publish timestamp: {}".format(cloud, e))
            return feed
    elif cloud == "azure":
        try:
            if feed.feed.updated_parsed > last_run:
                return feed
            else:
                logging.info("Feed not updated since last check")
                return None
        except Exception as e:
            logging.warning("Exception checking {} feed publish timestamp: {}".format(cloud, e))
            return feed
    else:
        raise NotImplementedError("unexpected cloud: {}".format(cloud))


def process_entry(entry: feedparser.util.FeedParserDict, cloud: str, last_run: time.struct_time,
                  queue_client: queue.QueueClient) -> None:
    if entry.published_parsed > last_run:
        logging.info("New entry: {} {} {}".format(entry.title, entry.link, time.mktime(entry.published_parsed)))
        queue_client.send_message(bytes("{}{}{}".format(cloud, DELIMITER, entry.link), "utf-8"))
        logging.info("Added `{}{}{}` to queue".format(cloud, DELIMITER, entry.link))


# Expects message in format `cloudname§feedurl`
def main(msg: func.QueueMessage) -> None:
    message = msg.get_body().decode("utf-8")
    parsed_message = message.split(DELIMITER)
    logging.info("Processing {}".format(message))
    cloud = parsed_message[0]
    feed_url = parsed_message[1]

    feed_checkpoint = get_checkpoint(CONNECTION_STRING, TABLE_NAME, "{}-{}".format(cloud, FEED_CHECKPOINT_KEY),
                                     ENVIRONMENT)
    article_checkpoint = get_checkpoint(CONNECTION_STRING, TABLE_NAME, "{}-{}".format(cloud, ARTICLE_CHECKPOINT_KEY),
                                        ENVIRONMENT)

    if feed_checkpoint is not None:
        logging.info("Using {} as FEED checkpoint".format(feed_checkpoint))
        feed = get_rss(feed_url, cloud, time.gmtime(feed_checkpoint))
    else:
        logging.info("No FEED checkpoint - using current time minus 30m")
        feed = get_rss(feed_url, cloud, time.gmtime(time.time() - (30 * 60)))

    if feed is not None:
        if article_checkpoint is not None:
            logging.info("Using {} as ARTICLE checkpoint".format(article_checkpoint))
        else:
            logging.info("No ARTICLE checkpoint - using current time minus 120m")

        queue_client = queue.QueueClient.from_connection_string(CONNECTION_STRING, QUEUE_NAME,
                                                                message_encode_policy=queue.BinaryBase64EncodePolicy(),
                                                                message_decode_policy=queue.BinaryBase64DecodePolicy())
        latest_article = time.localtime(0)
        for entry in feed.entries:
            if article_checkpoint is not None:
                process_entry(entry, cloud, time.gmtime(article_checkpoint), queue_client)
            else:
                process_entry(entry, cloud, time.gmtime(time.time() - (120 * 60)), queue_client)
            if entry.published_parsed > latest_article:
                latest_article = entry.published_parsed

        set_checkpoint(CONNECTION_STRING, TABLE_NAME, "{}-{}".format(cloud, ARTICLE_CHECKPOINT_KEY), ENVIRONMENT,
                       time.mktime(latest_article))
        if cloud == "aws":
            set_checkpoint(CONNECTION_STRING, TABLE_NAME, "{}-{}".format(cloud, FEED_CHECKPOINT_KEY), ENVIRONMENT,
                           time.mktime(feed.feed.published_parsed))
        elif cloud == "azure":
            set_checkpoint(CONNECTION_STRING, TABLE_NAME, "{}-{}".format(cloud, FEED_CHECKPOINT_KEY), ENVIRONMENT,
                           time.mktime(feed.feed.updated_parsed))
        # Anything else would have thrown an exception in get_rss()
