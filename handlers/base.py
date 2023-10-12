import json
from jsonpath_ng import jsonpath, parse

class BaseModel:
    def inovke_api(self):
        raise NotImplementedError("Not implemented in base model, make sure to override this method.")
    
    def load_mappings(self, schema_path):
        mappings = {}
        with open(schema_path, "r") as schema_file:
            mappings = json.load(schema_file)
        return (
            mappings["request"]["defaults"],
            mappings["request"]["mapping"],
            mappings["response"]["mapping"]
        )
    
    def form_request(self, params, defaults, mapping):
        for attrib, jpath in mapping.items():
            if attrib in params.keys():
                jsonpath_expr = parse(jpath)
                jsonpath_expr.update(defaults, params[attrib])
        return defaults

    def parse_response(self, res, mapping):
        ret = {}
        for attrib, jpath in mapping.items():
            jsonpath_expr = parse(jpath)
            results = jsonpath_expr.find(res)
            if results and len(results) > 0:
                ret[attrib] = results[0].value
        return ret