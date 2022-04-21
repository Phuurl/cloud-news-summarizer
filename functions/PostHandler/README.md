# AwsPostHandler
Uses BeautifulSoup to parse news posts picked up from the `PROCESS_QUEUE_NAME` storage queue, sends the main post content to Azure's text summarization service, and posts the result to Slack (with the `{CLOUD}_SLACK_WEBHOOK` environment variable).

Expects an input from the queue message in the format `cloud§articleurl`.

Currently supports:
- AWS articles: https://aws.amazon.com/new/
- Azure articles: https://azure.microsoft.com/en-gb/updates/