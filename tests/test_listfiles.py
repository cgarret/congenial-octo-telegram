import importlib.util
import os
import types
import sys


class MockRequest:
    def __init__(self, value, props=None):
        self.Value = value
        self.Properties = props or {}


class MockEntity:
    def __init__(self, value):
        self.value = value
        self.properties = []

    def addProperty(self, name, displayName, propertyType, value):
        self.properties.append((name, displayName, propertyType, value))


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
        self.messages.append((message, messageType))


def load_module():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    path = os.path.join(base, "maltego", "maltego-trx", "maltego_trx.py")
    spec = importlib.util.spec_from_file_location("maltego_trx", path)
    module = importlib.util.module_from_spec(spec)

    # mock maltego_trx.transform.DiscoverableTransform used by the module
    pkg = types.ModuleType('maltego_trx')
    transform_mod = types.ModuleType('maltego_trx.transform')

    class DiscoverableTransform:
        pass

    transform_mod.DiscoverableTransform = DiscoverableTransform
    sys.modules['maltego_trx'] = pkg
    sys.modules['maltego_trx.transform'] = transform_mod

    spec.loader.exec_module(module)
    return module


def test_listfiles_nonrecursive(tmp_path):
    module = load_module()
    ListFiles = getattr(module, 'ListFiles')

    # create sample files
    f1 = tmp_path / "foo.txt"
    f2 = tmp_path / "bar.log"
    f1.write_text("a")
    f2.write_text("b")

    req = MockRequest(str(tmp_path))
    resp = MockResponse()

    # ensure recursion disabled via request
    req.Properties['recursive'] = False
    ListFiles.create_entities(req, resp)

    assert len(resp.entities) == 2
    values = {e.value for e in resp.entities}
    assert str(f1) in values and str(f2) in values


def test_listfiles_recursive(tmp_path):
    module = load_module()
    ListFiles = getattr(module, 'ListFiles')

    sub = tmp_path / "sub"
    sub.mkdir()
    f1 = tmp_path / "root.txt"
    f2 = sub / "nested.txt"
    f1.write_text("r")
    f2.write_text("n")

    req = MockRequest(str(tmp_path), props={'recursive': True})
    resp = MockResponse()

    ListFiles.create_entities(req, resp)

    # both files should be present when recursive
    values = {e.value for e in resp.entities}
    assert str(f1) in values and str(f2) in values
