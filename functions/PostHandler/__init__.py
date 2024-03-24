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

# Optional environment variables
AWS_SLACK_WEBHOOK = os.getenv("AWS_SLACK_WEBHOOK", "")
AZURE_SLACK_WEBHOOK = os.getenv("AZURE_SLACK_WEBHOOK", "")

DELIMITER = "§"


def aws_article_text(soup: BeautifulSoup) -> dict:
    article_title = soup.title.text
    article_paragraphs = soup.find_all("div", class_="aws-text-box")

    article_text = ""
    for p in article_paragraphs:
        article_text += (p.text.replace("\n", "") + "\n")

    return {"title": article_title, "text": article_text}


def azure_article_text(soup: BeautifulSoup) -> dict:
    article_title = soup.title.text.split("|")
    article_div = soup.find("div", class_="row-divided")
    article_p = article_div.find_all("p")

    article_text = ""
    for p in article_p:
        article_text += (p.text.replace("\n", "") + "\n")

    return {"title": article_title[0], "text": article_text}


def create_client() -> textanalytics.TextAnalyticsClient:
    creds = credentials.AzureKeyCredential(COGNITIVE_KEY)
    client = textanalytics.TextAnalyticsClient(endpoint=COGNITIVE_ENDPOINT, credential=creds)
    return client


# Expects message in format `cloudname§feedurl`
def main(msg: func.QueueMessage) -> None:
    message = msg.get_body().decode("utf-8")
    parsed_message = message.split(DELIMITER)
    logging.info("Processing {}".format(message))
    cloud = parsed_message[0]
    article_url = parsed_message[1]

    entry = requests.get(article_url)
    if entry.status_code != 200:
        logging.error(entry.text)
        raise Exception("Non-200 response {} from target: {}".format(entry.status_code, article_url))

    soup = BeautifulSoup(entry.text, "html.parser")
    if cloud == "aws":
        if AWS_SLACK_WEBHOOK == "":
            raise Exception("{} article, but AWS_SLACK_WEBHOOK unset". format(cloud))
        article = aws_article_text(soup)
    elif cloud == "azure":
        if AZURE_SLACK_WEBHOOK == "":
            raise Exception("{} article, but AZURE_SLACK_WEBHOOK unset". format(cloud))
        article = azure_article_text(soup)
    else:
        logging.error("Unexpected cloud: {}".format(cloud))
        raise NotImplementedError

    if article["text"] != "":
        summarise_client = create_client()
        poller = summarise_client.begin_analyze_actions(
            documents=[article["text"]],
            actions=[textanalytics.ExtractiveSummaryAction(max_sentance_count=3)])

        summarise_results = poller.result()
        for result in summarise_results:
            if result[0].is_error:
                logging.error("Summarization error: code {}, message {}".format(result[0].code, result[0].message))
                raise Exception("Summarization failure")
            else:
                logging.info("Summary:\n{}".format(" ".join([sentence.text for sentence in result[0].sentences])))
                slack_blocks = {
                    "text": article["title"],
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*<{}|{}>*".format(article_url, article["title"])
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
                if cloud == "aws":
                    slack_response = requests.post(AWS_SLACK_WEBHOOK, json.dumps(slack_blocks))
                elif cloud == "azure":
                    slack_response = requests.post(AZURE_SLACK_WEBHOOK, json.dumps(slack_blocks))

                if slack_response.status_code != 200:
                    logging.warning("Non-200 from Slack: {} {}".format(slack_response.status_code, slack_response.text))
                    raise Exception("Failed to send to Slack")
    else:
        raise Exception("Failed to parse article")
