# ProcessFailureHandler
Function to monitor the `-poison` Azure-generated dead-letter queue for processing failures (from the [PostHandler](../PostHandler) Function), and send them to Slack (with `SLACK_FAILURE_WEBHOOK`) when found.
