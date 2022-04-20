# AwsPostHandler
Uses BeautifulSoup to parse AWS news posts picked up from the `QUEUE_NAME` stroage queue, sends the main post content to Azure's text summarization service, and posts the result to Slack (with `SLACK_WEBHOOK`).

Expects an input from the queue message in the format `cloud§articleurl`.