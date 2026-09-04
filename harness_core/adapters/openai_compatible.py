# -*- coding: utf-8 -*-
"""OpenAI-compatible adapter for local Ollama / compatible endpoints.

Does not send private memory automatically. Caller decides what to include.
No API key required for local Ollama.
"""
import json
import urllib.request


class OpenAICompatibleAdapter:
    def __init__(self, base_url="http://127.0.0.1:11434/v1", model="qwen2.5:7b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, messages, temperature=0.7, max_tokens=1024):
        payload = {"model": self.model, "messages": messages, "temperature": temperature,
                   "max_tokens": max_tokens, "stream": False}
        req = urllib.request.Request(self.base_url + "/chat/completions",
                                     data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    def completion(self, prompt, **kwargs):
        return self.chat([{"role": "user", "content": prompt}], **kwargs)
