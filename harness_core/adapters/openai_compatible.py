# -*- coding: utf-8 -*-
"""OpenAI-compatible adapter for local Ollama / compatible endpoints.

Does not send private memory automatically. Caller decides what to include.
No API key required for local Ollama.

`chat_with_usage` exposes provider-reported token usage so callers can record it
in a local audit trail. `chat` keeps the simple string-returning interface.
"""
import json
import urllib.request


class OpenAICompatibleAdapter:
    def __init__(self, base_url="http://127.0.0.1:11434/v1", model="qwen2.5:7b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _post_chat(self, messages, temperature=0.7, max_tokens=1024):
        payload = {"model": self.model, "messages": messages, "temperature": temperature,
                   "max_tokens": max_tokens, "stream": False}
        req = urllib.request.Request(self.base_url + "/chat/completions",
                                     data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))

    def chat_with_usage(self, messages, temperature=0.7, max_tokens=1024):
        data = self._post_chat(messages, temperature=temperature, max_tokens=max_tokens)
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage") or {}
        return content, {
            "provider": "openai_compatible",
            "model": self.model,
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
            "raw_usage": usage,
        }

    def chat(self, messages, temperature=0.7, max_tokens=1024):
        return self.chat_with_usage(messages, temperature=temperature, max_tokens=max_tokens)[0]

    def completion(self, prompt, **kwargs):
        return self.chat([{"role": "user", "content": prompt}], **kwargs)
