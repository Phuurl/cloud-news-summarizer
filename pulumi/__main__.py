"""An Azure RM Python Pulumi program"""

import pulumi
import pulumi_azure_native as azure

config = pulumi.Config()
prefix = config.require("prefix")


resource_group = azure.resources.ResourceGroup("rg",
    resource_group_name="{}-cloud-news-summarizer".format(prefix))

account = azure.storage.StorageAccount("table-sa",
    resource_group_name=resource_group.name,
    sku=azure.storage.SkuArgs(
        name=azure.storage.SkuName.STANDARD_ZRS,
    ),
    kind=azure.storage.Kind.STORAGE_V2,
    account_name="{}cloudnews".format(prefix))

checkpoint_table = azure.storage.Table("checkpoint-table",
    account_name=account.name,
    resource_group_name=resource_group.name,
    table_name="rsscheckpoint")

process_queue = azure.storage.Queue("process-queue",
    account_name=account.name,
    resource_group_name=resource_group.name,
    queue_name="processqueue")

cognitive_account = azure.cognitiveservices.Account("cognitive-account",
    account_name="{}-cloud-news-cognitive".format(prefix),
    kind="TextAnalytics",
    resource_group_name=resource_group.name,
    sku=azure.cognitiveservices.SkuArgs(name="S"))

pulumi.export("rg-name", resource_group.name)
pulumi.export("sa-name", account.name)
pulumi.export("table-name", checkpoint_table.name)
pulumi.export("queue-name", process_queue.name)
pulumi.export("cognitive-name", cognitive_account.name)
cognitive_endpoint = pulumi.Output.all(resource_group.name, cognitive_account.name)\
    .apply(lambda args: azure.cognitiveservices.get_account(resource_group_name=args[0], account_name=args[1]))\
    .apply(lambda properties: properties.properties.endpoint)
pulumi.export("cognitive-endpoint", cognitive_endpoint)
