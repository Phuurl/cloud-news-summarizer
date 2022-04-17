# cloud-news-summarizer
An Azure Function and associated resources that takes RSS feeds of cloud news (eg _AWS What's New_), generates a 3-sentence summary with Azure's Text Analytics, and sends the summary to Slack (with a link to the original post).

The Function polls the relevant RSS feeds every 30 minutes.

It is expected that both the Function and the Language Cognitive Services usage will fall within the free tier on Azure, or have very low cost (cents per month). Other resource usage is negligible and will likely also be free. For additional pricing information, see
- [Functions pricing](https://azure.microsoft.com/en-us/pricing/details/functions/)
- [Language Cognitive Services pricing](https://azure.microsoft.com/en-gb/pricing/details/cognitive-services/language-service/)

## Architecture
![Architecture diagram](./.img/cloud-news-summarizer.png)

## Usage / Deployment
Supporting resources are maintained in IaC with Pulumi. 
1. Head to the [pulumi/](./pulumi) directory and follow the instructions to deploy that stack.
2. Deploy the Azure Functions in the [functions/](./functions) directory using either the Functions CLI, or the VS Code extension, choosing the `python3.9` runtime. Ensure that you set the required Applications Settings as detailed below in the deployed Function App resource.
   - Note: If you deployed the Functions before setting the below config in the Function App, you may need to redeploy the functions for it to take effect

The following Application Settings are required to be present on the deployed Function App:
- `TABLE_SA_CONNECTION`: connection string for storage account created in Pulumi - _available in your Storage Account resource in the Portal_
- `TABLE_NAME`: table name within storage account - _listed as a Pulumi output_
- `ENVIRONMENT`: table row key - _string to differentiate multiple deployments, can be anything alphanumeric, eg `prod`_
- `QUEUE_NAME`: queue name within storage account - _listed as a Pulumi output_
- `COGNITIVE_ENDPOINT`: endpoint URL (including `https://`) for the cognitive services resource - _listed as a Pulumi output_
- `COGNITIVE_KEY`: key for the cognitive services resource - _available in your Language resource in the Portal_
- `SLACK_WEBHOOK`: webhook URL for sending to Slack - _see the [Slack docs](https://api.slack.com/messaging/webhooks) if you aren't sure_
- `SLACK_FAILURE_WEBHOOK`: webhook URL for processing failure alerts to Slack - _can be the same or different to the normal Slack webhook (ie optionally send failures to a different channel)_

## Current feeds supported
Now:
- AWS What's New (https://aws.amazon.com/about-aws/whats-new/recent/feed/)

Next:
- Azure Updates (https://azurecomcdn.azureedge.net/en-gb/updates/feed/)
