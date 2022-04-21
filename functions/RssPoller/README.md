# RssPoller
Polls the RSS feed given by the `INPUT_QUEUE_NAME` to check for new articles. If any new articles are found, add them to the `PROCESS_QUEUE_NAME` queue for processing by the `PostHandler` function.

Stores the latest feed and article timestamp for each feed type in an Azure Storage Table `TABLE_NAME` to avoid duplication.

Expects an input from the queue message in the format `cloud§rssfeedurl` - eg `aws§https://aws.amazon.com/about-aws/whats-new/recent/feed/`