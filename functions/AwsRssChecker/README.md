# AwsRssChecker
Polls the _AWS What's New_ RSS feed on a regular interval (30-minute timer by default) to check for new articles. If any found, add them to the `QUEUE_NAME` queue for processing by the `AwsPostHandler` function.

Stores the last successful check timestamp in an Azure Storage Table `TABLE_NAME` to avoid duplication.