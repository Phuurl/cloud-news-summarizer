# TimerTrigger
Triggers on a timer, checks which cloud feeds are enabled based on the `AWS_ENABLED` and `AZURE_ENABLED` environment variables, and adds the appropriate messages to the `timerqueue` queue for processing by the [RssPoller](../RssPoller) Function.