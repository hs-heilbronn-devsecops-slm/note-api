from note_api.model import CreateNoteRequest, Note
from note_api.backends import MemoryBackend
from note_api.main import create_note, get_note, get_notes
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import NoOpTracerProvider

#In Unittests sollten keine Traces an die Produktivumgebung gesendet werden.
#Da keine anderen Umgebungen definiert sind werden Traces "deaktiviert"
@pytest.fixture(scope="session", autouse=True)
def disable_opentelemetry():
    trace.set_tracer_provider(NoOpTracerProvider);

def test_save_and_get_item():
    backend = MemoryBackend()
    id = create_note(CreateNoteRequest(
        title='Test Note',
        description='Demo Note',
    ), backend)
    assert get_note(id, backend) == Note(title='Test Note', description='Demo Note', id=id)


def test_save_and_get_items():
    backend = MemoryBackend()
    create_note(CreateNoteRequest(
        title='Test Note',
        description='Demo Note',
    ), backend)
    create_note(CreateNoteRequest(
        title='Test Note 2',
        description='Demo Note 2',
    ), backend)
    notes = get_notes(backend)
    assert len(notes) == 2