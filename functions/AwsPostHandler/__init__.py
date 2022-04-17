import json
import logging
import os

import azure.functions as func
import requests
from bs4 import BeautifulSoup
import azure.ai.textanalytics as textanalytics
import azure.core.credentials as credentials

# Gather required environment variables
COGNITIVE_ENDPOINT = os.environ["COGNITIVE_ENDPOINT"]
COGNITIVE_KEY = os.environ["COGNITIVE_KEY"]
SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]


def create_client() -> textanalytics.TextAnalyticsClient:
    creds = credentials.AzureKeyCredential(COGNITIVE_KEY)
    client = textanalytics.TextAnalyticsClient(endpoint=COGNITIVE_ENDPOINT, credential=creds)
    return client


def main(msg: func.QueueMessage) -> None:
    message = msg.get_body().decode("utf-8")
    logging.info("Processing {}".format(message))

    entry = requests.get(message)
    if entry.status_code != 200:
        logging.error(entry.text)
        raise Exception("Non-200 response {} from target: {}".format(entry.status_code, message))

    soup = BeautifulSoup(entry.text, "html.parser")
    article_paragraphs = soup.find_all("div", class_="aws-text-box")
    article_title = soup.title.text

    article_text = ""
    for paragraph in article_paragraphs:
        article_text += (paragraph.text.replace("\n", "") + "\n")

    if article_text != "":
        summarise_client = create_client()
        poller = summarise_client.begin_analyze_actions(
            documents=[article_text],
            actions=[textanalytics.ExtractSummaryAction(max_sentance_count=3)])

        summarise_results = poller.result()
        for result in summarise_results:
            if result[0].is_error:
                logging.error("Summarisation error: code {}, message {}".format(result[0].code, result[0].message))
                raise Exception("Summarisation failure")
            else:
                logging.info("Summary:\n{}".format(" ".join([sentence.text for sentence in result[0].sentences])))
                slack_blocks = {
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*<{}|{}>*".format(message, article_title)
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": "\n".join([sentence.text for sentence in result[0].sentences])
                            }
                        }
                    ]
                }
                slack_response = requests.post(SLACK_WEBHOOK, json.dumps(slack_blocks))
                if slack_response.status_code != 200:
                    logging.warning("Non-200 from Slack: {} {}".format(slack_response.status_code, slack_response.text))
                    raise Exception("Failed to send to Slack")
    else:
        raise Exception("Failed to parse article")
