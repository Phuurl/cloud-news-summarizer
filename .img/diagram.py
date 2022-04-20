from diagrams import Cluster, Diagram
from diagrams.azure.compute import FunctionApps
from diagrams.azure.storage import StorageAccounts, QueuesStorage, TableStorage
from diagrams.azure.ml import CognitiveServices
from diagrams.oci.monitoring import Alarm
from diagrams.saas.chat import Slack

with Diagram("cloud-news-summarizer", show=False, outformat="png"):
    with Cluster("{prefix}cloudnews\nStorage Account"):
        timer_queue = QueuesStorage("timerqueue\nQueue")
        timer_poison_queue = QueuesStorage("timerqueue-poison\nQueue")
        process_queue = QueuesStorage("processqueue\nQueue")
        process_poison_queue = QueuesStorage("processqueue-poison\nQueue")
        table = TableStorage("rsscheckpoint\nTable")

    timer = Alarm("30m schedule trigger")
    timer_func = FunctionApps("TimerTrigger\nFunction")
    rss = FunctionApps("RssPoller\nFunction")
    processor = FunctionApps("PostHandler\nFunction")
    failure = FunctionApps("FailureHandler\nFunction")

    cog = CognitiveServices("{prefix}-cloud-news-cognitive\nCognitive Service")
    slack = Slack("Slack notification")

    timer >> timer_func
    timer_func >> timer_queue
    timer_queue >> rss
    rss >> table
    rss << table
    rss >> process_queue
    rss >> timer_poison_queue
    process_queue >> processor
    processor >> process_poison_queue
    processor >> cog
    processor << cog
    process_poison_queue >> failure
    timer_poison_queue >> failure
    [processor, failure] >> slack
