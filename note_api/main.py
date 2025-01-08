# -*- coding: utf-8 -*-
from uuid import uuid4
from typing import List, Optional
import os
from typing_extensions import Annotated

from fastapi import Depends, FastAPI
from starlette.responses import RedirectResponse
from .backends import Backend, RedisBackend, MemoryBackend, GCSBackend
from .model import Note, CreateNoteRequest

 
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import get_tracer


app = FastAPI()

my_backend: Optional[Backend] = None


def get_backend() -> Backend:
    global my_backend  # pylint: disable=global-statement
    if my_backend is None:
        backend_type = getenv('BACKEND', 'memory')
        print(backend_type)
        if backend_type == 'redis':
            my_backend = RedisBackend()
        elif backend_type == 'gcs':
            my_backend = GCSBackend()
        else:
            my_backend = MemoryBackend()
    return my_backend



def get_backend() -> Backend:
    global my_backend  # pylint: disable=global-statement
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
    return RedirectResponse(url='/notes')


@app.get('/notes')
def get_notes(backend: Annotated[Backend, Depends(get_backend)]) -> List[Note]:
    keys = backend.keys()
    Notes = []
    for key in keys:
        Notes.append(backend.get(key))

    with tracer.start_as_current_span("get-span-lol") as span:
            span.add_event("get-all-notes-event")
    return Notes


@app.get('/notes/{note_id}')
def get_note(note_id: str,
             backend: Annotated[Backend, Depends(get_backend)]) -> Note:
    
    with tracer.start_as_current_span("get-note-trace") as getTrace:
        getTrace.add_event("Hier ist deine note")
        getTrace.set_attribute("id",note_id);
        getTrace.set_attribute("comment", "hilfe ich bin immer noch in der gloud gefangen")
    
    return backend.get(note_id)

@app.put('/notes/{note_id}')
def update_note(note_id: str,
                request: CreateNoteRequest,
                backend: Annotated[Backend, Depends(get_backend)]) -> None:
    backend.set(note_id, request)
    with tracer.start_as_current_span("put-put-put") as putTrace:
        putTrace.add_event("Machst du eh nicht lol")
        putTrace.set_attribute("id",note_id);
        putTrace.set_attribute("comment", "hilfe ich bin in der gloud gefangen")


@app.post('/notes')
def create_note(request: CreateNoteRequest,
                backend: Annotated[Backend, Depends(get_backend)]) -> str:
    note_id = str(uuid4())
    backend.set(note_id, request)
    return note_id


def configure_tracer():
    # Tracer-Provider einrichten
    provider = TracerProvider()
    trace.set_tracer_provider(provider)

    # Exporter einrichten (z. B. OTLP)
    otlp_exporter = OTLPSpanExporter(endpoint="https://cloudtrace.googleapis.com")

    # BatchSpanProcessor einrichten
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)


configure_tracer()

tracer = get_tracer(__name__)


FastAPIInstrumentor.instrument_app(app)

