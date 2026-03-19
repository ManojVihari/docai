# import hashlib
# import json


# class SignatureService:

#     def generate(self, route):

#         """
#         Generates a stable signature for API contract.
#         Ignores business logic and LLM output.
#         """

#         contract = {
#             "method": route.method,
#             "path": route.path,

#             "parameters": sorted(
#                 [
#                     {
#                         "name": p.name,
#                         "type": p.type,
#                         "required": p.required
#                     }
#                     for p in route.parameters
#                 ],
#                 key=lambda x: x["name"]
#             ),

#             "status_codes": sorted(
#                 [
#                     {
#                         "code": s.code
#                     }
#                     for s in route.status_codes
#                 ],
#                 key=lambda x: x["code"]
#             )
#         }

#         contract_str = json.dumps(contract, sort_keys=True)

#         return hashlib.md5(contract_str.encode()).hexdigest()

import hashlib
import json


class SignatureService:

    def generate(self, route):

        contract = self._normalize(route)

        contract_str = json.dumps(contract, sort_keys=True)

        return hashlib.md5(contract_str.encode()).hexdigest()

    def _normalize(self, route):

        """
        Convert route object → stable dict
        without hardcoding field-by-field logic.
        """

        return {
            "method": route.method,
            "path": route.path,
            "parameters": sorted(
                [self._normalize_obj(p) for p in route.parameters],
                key=lambda x: x["name"]
            ),
            "status_codes": sorted(
                [self._normalize_obj(s) for s in route.status_codes],
                key=lambda x: x["code"]
            )
        }

    def _normalize_obj(self, obj):

        """
        Converts Pydantic object → dict
        safely and consistently.
        """

        if hasattr(obj, "dict"):
            data = obj.dict()
        else:
            data = obj.__dict__

        # Remove non-contract noise if needed
        return data