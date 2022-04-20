# TimerFailureHandler
Seemingly Azure doesn't allow a Function to have multiple triggers. Therefore, this Function is an exact dupe (symlinked) of [ProcessFailureHandler/](../ProcessFailureHandler), but subscribed to the `timerqueue-poison` queue instead.

Function to monitor the `-poison` Azure-generated dead-letter queue for timer processing failures (from the [RssPoller](../RssPoller) Function), and send them to Slack (with `SLACK_FAILURE_WEBHOOK`) when found.
