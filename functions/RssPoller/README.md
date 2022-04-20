# RssPoller
Polls the input RSS feed on a regular interval (30-minute timer by default) to check for new articles. If any found, add them to the `QUEUE_NAME` queue for processing by the `PostHandler` function.

Stores the last successful check timestamp in an Azure Storage Table `TABLE_NAME` to avoid duplication.

Expects an input from the queue message in the format `cloud§feedurl` - eg `aws§https://aws.amazon.com/about-aws/whats-new/recent/feed/`