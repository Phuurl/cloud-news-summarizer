from diagrams import Cluster, Diagram
from diagrams.azure.compute import FunctionApps
from diagrams.azure.storage import StorageAccounts, QueuesStorage, TableStorage
from diagrams.azure.ml import CognitiveServices
from diagrams.oci.monitoring import Alarm
from diagrams.saas.chat import Slack

with Diagram("cloud-news-summarizer", show=False, outformat="png"):
    with Cluster("{prefix}cloudnews\nStorage Account"):
        queue = QueuesStorage("processqueue\nQueue")
        poison_queue = QueuesStorage("processqueue-poison\nQueue")
        table = TableStorage("rsscheckpoint\nTable")

    timer = Alarm("30m schedule trigger")
    rss = FunctionApps("AwsRssChecker\nFunction")
    processor = FunctionApps("AwsPostHandler\nFunction")
    failure = FunctionApps("FailureHandler\nFunction")

    cog = CognitiveServices("{prefix}-cloud-news-cognitive\nCognitive Service")
    slack = Slack("Slack notification")

    timer >> rss
    rss >> table
    rss << table
    rss >> queue
    queue >> processor
    processor >> poison_queue
    processor >> cog
    processor << cog
    poison_queue >> failure
    [processor, failure] >> slack
