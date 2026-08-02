import json

from webui.api.main import app

with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)