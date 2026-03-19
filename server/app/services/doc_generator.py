import requests


class APIDocGenerator:

    def __init__(self, model="mistral"):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"

    def generate_explanation(self, function_source):

        prompt = f"""
You are an API documentation assistant.

Based on the following API function, generate:

1. A concise overview (2-3 sentences).
2. Business logic explanation.
3. Change impact explanation.

Return in JSON format:

{{
  "overview": "...",
  "business_logic": "...",
  "change_impact": "..."
}}

Function:

{function_source}
"""

        response = requests.post(
            self.ollama_url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )

        return response.json()["response"]
