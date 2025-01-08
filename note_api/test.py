
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter


otlp_exporter = CloudTraceSpanExporter(
    project_id='hs-heilbronn-devsecops',
)


print("hallo i mog net")