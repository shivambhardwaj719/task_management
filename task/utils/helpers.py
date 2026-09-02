import json


def parse_json_body(request):
    if request.body:
        try:
            return json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return None
    return {}
