# src/shared/llm_client.py

import json
import requests
from typing import Optional, Dict, Any
from loguru import logger
from config.settings import settings


class LLMClient:
    """Unified LLM client supporting Groq, Gemini, OpenAI, and Anthropic.

    Auto-picks the first available provider in this priority order:
        Groq → Gemini → OpenAI → Anthropic

    Groq is the recommended default: free tier, no credit card, no
    account verification issues.
    """

    # ---------- Gemini (Interactions API) ----------
    GEMINI_MODEL = "gemini-3.8-flash"
    GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"

    # ---------- Groq ----------
    GROQ_MODEL = "openai/gpt-oss-120b"

    def __init__(self, provider: Optional[str] = None):
        if provider is None:
            if getattr(settings, "GROQ_API_KEY", None):
                provider = "groq"
            elif getattr(settings, "GEMINI_API_KEY", None):
                provider = "gemini"
            elif getattr(settings, "OPENAI_API_KEY", None):
                provider = "openai"
            elif getattr(settings, "ANTHROPIC_API_KEY", None):
                provider = "anthropic"
            else:
                provider = "none"

        self.provider = provider
        self._client = None
        self._initialize()

    # ------------------------------------------------------------------ #
    #  INITIALIZATION
    # ------------------------------------------------------------------ #
    def _initialize(self):
        # ---------------- GROQ ---------------- #
        if self.provider == "groq":
            try:
                from groq import Groq
                key = (settings.GROQ_API_KEY or "").strip()
                if not key:
                    logger.error("GROQ_API_KEY is empty.")
                    self._client = None
                    return
                self._client = Groq(api_key=key)
                logger.info(f"LLM provider: Groq ({self.GROQ_MODEL})")
            except ImportError:
                logger.error("Groq SDK not installed. Run: pip install groq")
                self._client = None
            except Exception as e:
                logger.error(f"Groq init failed: {e}")
                self._client = None

        # ---------------- GEMINI (Interactions API) ---------------- #
        elif self.provider == "gemini":
            key = (settings.GEMINI_API_KEY or "").strip()
            if not key:
                logger.error("GEMINI_API_KEY is empty.")
                self._client = None
                return
            try:
                r = requests.post(
                    self.GEMINI_ENDPOINT,
                    headers={
                        "x-goog-api-key": key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.GEMINI_MODEL,
                        "input": "Reply with OK",
                    },
                    timeout=20,
                )
                if r.status_code == 200:
                    self._client = "rest"
                    logger.info(
                        f"LLM provider: Google Gemini (Interactions API, {self.GEMINI_MODEL})"
                    )
                else:
                    logger.error(f"Gemini test failed {r.status_code}: {r.text[:400]}")
                    self._client = None
            except Exception as e:
                logger.error(f"Gemini init failed: {e}")
                self._client = None

        # ---------------- OPENAI ---------------- #
        elif self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("LLM provider: OpenAI")
            except Exception as e:
                logger.error(f"OpenAI init failed: {e}")
                self._client = None

        # ---------------- ANTHROPIC ---------------- #
        elif self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                logger.info("LLM provider: Anthropic")
            except Exception as e:
                logger.error(f"Anthropic init failed: {e}")
                self._client = None

        # ---------------- NONE ---------------- #
        elif self.provider == "none":
            logger.warning(
                "No LLM API key found. LLM-based extraction disabled. "
                "Pattern-based extraction will still work."
            )
            self._client = None

        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    # ------------------------------------------------------------------ #
    #  COMPLETE
    # ------------------------------------------------------------------ #
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        if self._client is None:
            raise RuntimeError(
                "No LLM configured. Add GROQ_API_KEY (or another key) to .env."
            )

        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS

        try:
            # ---------------- GROQ ---------------- #
            if self.provider == "groq":
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                kwargs = {
                    "model": self.GROQ_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                response = self._client.chat.completions.create(**kwargs)
                return response.choices[0].message.content

            # ---------------- GEMINI (Interactions API) ---------------- #
            elif self.provider == "gemini":
                key = settings.GEMINI_API_KEY

                payload: Dict[str, Any] = {
                    "model": self.GEMINI_MODEL,
                    "input": prompt,
                }

                config: Dict[str, Any] = {}
                if system:
                    config["system_instruction"] = system
                if temperature is not None:
                    config["temperature"] = temperature
                if max_tokens:
                    config["max_output_tokens"] = max_tokens
                if json_mode:
                    config["response_mime_type"] = "application/json"
                if config:
                    payload["generation_config"] = config

                r = requests.post(
                    self.GEMINI_ENDPOINT,
                    headers={
                        "x-goog-api-key": key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=90,
                )

                if r.status_code != 200:
                    logger.error(f"Gemini error {r.status_code}: {r.text[:500]}")
                    r.raise_for_status()

                data = r.json()
                text = self._extract_gemini_text(data)
                if text is None:
                    logger.error(f"Could not find text in Gemini response: {data}")
                    raise ValueError("Malformed Gemini response")
                return text

            # ---------------- OPENAI ---------------- #
            elif self.provider == "openai":
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                kwargs = {
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                response = self._client.chat.completions.create(**kwargs)
                return response.choices[0].message.content

            # ---------------- ANTHROPIC ---------------- #
            elif self.provider == "anthropic":
                response = self._client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    system=system or "",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"LLM completion failed ({self.provider}): {e}")
            raise

    # ------------------------------------------------------------------ #
    #  GEMINI RESPONSE PARSER
    # ------------------------------------------------------------------ #
    def _extract_gemini_text(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract text from the Gemini Interactions API response."""
        # Fast path
        if "output_text" in data and isinstance(data["output_text"], str):
            return data["output_text"]

        # New format: steps → model_output → content → text
        for step in data.get("steps", []):
            if step.get("type") == "model_output":
                parts = []
                for block in step.get("content", []):
                    if block.get("type") == "text":
                        parts.append(block.get("text", ""))
                if parts:
                    return "".join(parts)

        # Old-style fallback
        for cand in data.get("candidates", []):
            parts = cand.get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
            if text:
                return text

        return None

    # ------------------------------------------------------------------ #
    #  COMPLETE JSON
    # ------------------------------------------------------------------ #
    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        response = self.complete(prompt, system, json_mode=True, **kwargs)

        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nResponse: {response[:500]}")
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            raise


# ---------------------------------------------------------------------- #
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client