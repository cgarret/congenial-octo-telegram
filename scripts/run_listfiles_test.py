"""Small test harness to exercise ListFiles.create_entities.

Creates a temporary directory with sample files, loads the transform module
by path, and runs the transform with mocked `request`/`response` objects.
"""
import os
import tempfile
import json
import importlib.util
import sys
import types


def load_listfiles_module():
    # derive project root relative to this script to avoid hard-coded drives
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    path = os.path.join(project_root, "maltego", "maltego-trx", "maltego_trx.py")

    # provide a minimal mock of the `maltego_trx.transform` package used by the transform
    if 'maltego_trx' not in sys.modules:
        pkg = types.ModuleType('maltego_trx')
        transform_mod = types.ModuleType('maltego_trx.transform')

        class DiscoverableTransform:
            pass

        transform_mod.DiscoverableTransform = DiscoverableTransform
        sys.modules['maltego_trx'] = pkg
        sys.modules['maltego_trx.transform'] = transform_mod
    spec = importlib.util.spec_from_file_location("maltego_trx", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MockRequest:
    def __init__(self, value):
        self.Value = value


class MockEntity:
    def __init__(self, value):
        self.value = value
        self.properties = []

    def addProperty(self, name, displayName, propertyType, value):
        self.properties.append({
            "name": name,
            "displayName": displayName,
            "type": propertyType,
            "value": value,
        })


class MockResponse:
    def __init__(self):
        self.entities = []
        self.messages = []

    def addEntity(self, entityType, value):
        ent = MockEntity(value)
        ent.entityType = entityType
        self.entities.append(ent)
        return ent

    def addUIMessage(self, message, messageType=None):
        self.messages.append({"message": message, "type": messageType})


def main():
    # create temp dir and files
    with tempfile.TemporaryDirectory() as td:
        f1 = os.path.join(td, "a.txt")
        f2 = os.path.join(td, "b.log")
        with open(f1, "w") as fh:
            fh.write("hello")
        with open(f2, "w") as fh:
            fh.write("world")

        module = load_listfiles_module()
        ListFiles = getattr(module, "ListFiles")

        req = MockRequest(td)
        resp = MockResponse()

        ListFiles.create_entities(req, resp)

        out = {
            "entities": [
                {"type": e.entityType, "value": e.value, "properties": e.properties}
                for e in resp.entities
            ],
            "messages": resp.messages,
        }

        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
