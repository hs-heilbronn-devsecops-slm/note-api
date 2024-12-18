# -*- coding: utf-8 -*-
from uuid import uuid4
from typing import List, Optional
import os
from typing_extensions import Annotated
import logging
 

from fastapi import Depends, FastAPI
from starlette.responses import RedirectResponse
from .backends import Backend, RedisBackend, MemoryBackend, GCSBackend
from .model import Note, CreateNoteRequest

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_INSTANCE_ID, SERVICE_NAME, Resource

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from pythonjsonlogger import jsonlogger
from opentelemetry.instrumentation.logging import LoggingInstrumentor


app = FastAPI()

my_backend: Optional[Backend] = None

logger = logging.getLogger("TraceLogger")

LoggingInstrumentor().instrument()

#setup tracelogging
resource = Resource.create(attributes={
    # Use the PID as the service.instance.id to avoid duplicate timeseries
    # from different Gunicorn worker processes.
    SERVICE_INSTANCE_ID: f"worker-{os.getpid()}",
})

traceProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter())
traceProvider.add_span_processor(processor)
trace.set_tracer_provider(traceProvider)

reader = PeriodicExportingMetricReader(
    OTLPMetricExporter()
)
meterProvider = MeterProvider(metric_readers=[reader], resource=resource)
metrics.set_meter_provider(meterProvider)

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(message)s %(otelTraceID)s %(otelSpanID)s %(otelTraceSampled)s",
    rename_fields={
        "levelname": "severity",
        "asctime": "timestamp",
        "otelTraceID": "logging.googleapis.com/trace",
        "otelSpanID": "logging.googleapis.com/spanId",
        "otelTraceSampled": "logging.googleapis.com/trace_sampled",
        "test": "Testerino"
        },
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logHandler.setFormatter(formatter)
logging.basicConfig(
    level=logging.INFO,
    handlers=[logHandler],
)


FastAPIInstrumentor.instrument_app(app)


def get_backend() -> Backend:
    global my_backend  # pylint: disable=global-statement
    logger.info
    if my_backend is None:
        backend_type = os.getenv('BACKEND', 'memory')
        print(backend_type)
        if backend_type == 'redis':
            my_backend = RedisBackend()
        elif backend_type == 'gcs':
            my_backend = GCSBackend()
        else:
            my_backend = MemoryBackend()
    return my_backend


@app.get('/')
def redirect_to_notes() -> None:
    logger.info("Ich bin ein get root")
    return RedirectResponse(url='/notes')


@app.get('/notes')
def get_notes(backend: Annotated[Backend, Depends(get_backend)]) -> List[Note]:
    keys = backend.keys()
    logger.info("ich bin einhandle /multi request", extra={'subRequests': subRequests})
    Notes = []
    for key in keys:
        Notes.append(backend.get(key))
    return Notes


@app.get('/notes/{note_id}')
def get_note(note_id: str,
             backend: Annotated[Backend, Depends(get_backend)]) -> Note:
    logger.info("Ich bin ein get /notes/id mit id {note_id}")
    return backend.get(note_id)


@app.put('/notes/{note_id}')
def update_note(note_id: str,
                request: CreateNoteRequest,
                backend: Annotated[Backend, Depends(get_backend)]) -> None:
    logger.info("Ich bin ein put /notes/id mit id {note_id}")
    backend.set(note_id, request)


@app.post('/notes')
def create_note(request: CreateNoteRequest,
                backend: Annotated[Backend, Depends(get_backend)]) -> str:
    note_id = str(uuid4())
    backend.set(note_id, request)
    logger.info("Ich bin ein post /notes/id mit id {note_id}")
    return note_id

