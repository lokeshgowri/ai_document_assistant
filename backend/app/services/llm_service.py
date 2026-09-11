import logging

from google import genai
from google.genai.errors import APIError

from app.config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    LLM_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_LLM_MODEL,
)


logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self):

        self.provider = LLM_PROVIDER

        if self.provider == "gemini":

            if not GEMINI_API_KEY:
                raise RuntimeError(
                    "GEMINI_API_KEY is not configured."
                )

            self.model = LLM_MODEL

            self.client = genai.Client(
                api_key=GEMINI_API_KEY
            )

            logger.info(
                "LLM provider initialized: Gemini (%s)",
                self.model
            )

        elif self.provider == "ollama":

            self.model = OLLAMA_LLM_MODEL
            self.base_url = OLLAMA_BASE_URL

            logger.info(
                "LLM provider initialized: Ollama (%s)",
                self.model
            )

        else:

            raise RuntimeError(
                f"Unsupported LLM provider: {self.provider}"
            )

    def generate_answer(
        self,
        question: str,
        context: str
    ) -> str:

        prompt = f"""
You are a strict document question-answering assistant.

Your job is to answer the user's question using ONLY information
contained in the provided document context.

IMPORTANT RULES:

1. Answer ONLY the specific question asked by the user.

2. Do NOT provide additional related information unless the user
   explicitly asks for it.

3. Use ONLY facts explicitly stated in the document context.

4. Do NOT use outside knowledge.

5. Do NOT guess, assume, or infer information that is not explicitly
   supported by the document context.

6. Do NOT calculate, convert, or reinterpret values unless the
   document explicitly provides the required information.

7. Preserve numbers and units exactly as they appear in the document.

8. If the document context does not contain enough information to
   answer the question, respond EXACTLY with:

"I could not find the answer in the provided documents."

9. If the retrieved context is unrelated to the question, respond
   with the same no-answer message.

10. Keep the answer short and direct.

DOCUMENT CONTEXT:
-----------------
{context}
-----------------

USER QUESTION:
{question}

ANSWER:
"""

        if self.provider == "gemini":

            return self._generate_with_gemini(prompt)

        elif self.provider == "ollama":

            return self._generate_with_ollama(prompt)

        else:

            raise RuntimeError(
                f"Unsupported LLM provider: {self.provider}"
            )

    def _generate_with_gemini(
        self,
        prompt: str
    ) -> str:

        try:

            logger.info(
                "Sending request to Gemini model: %s",
                self.model
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            answer = response.text.strip()

            logger.info(
                "Gemini response generated successfully."
            )

            return answer

        except APIError as exc:

            logger.exception(
                "Gemini API request failed."
            )

            error_message = str(exc).lower()

            if (
                "429" in error_message
                or "resource_exhausted" in error_message
                or "quota exceeded" in error_message
                or "quotaexceeded" in error_message
            ):

                raise RuntimeError(
                    "Gemini API quota has been exceeded. "
                    "Please try again later or check your "
                    "Gemini API quota and billing settings."
                ) from exc

            raise RuntimeError(
                "Failed to generate an answer using Gemini."
            ) from exc

        except RuntimeError:

            raise

        except Exception as exc:

            logger.exception(
                "Gemini LLM request failed."
            )

            raise RuntimeError(
                "Failed to process the Gemini LLM request."
            ) from exc

    def _generate_with_ollama(
        self,
        prompt: str
    ) -> str:

        try:

            import requests

            logger.info(
                "Sending request to Ollama model: %s",
                self.model
            )

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )

            response.raise_for_status()

            data = response.json()

            answer = data.get("response", "").strip()

            if not answer:
                raise RuntimeError(
                    "Ollama returned an empty response."
                )

            logger.info(
                "Ollama response generated successfully."
            )

            return answer

        except RuntimeError:

            raise

        except requests.exceptions.RequestException as exc:

            logger.exception(
                "Ollama API request failed."
            )

            raise RuntimeError(
                "Failed to connect to Ollama. "
                "Make sure Ollama is running."
            ) from exc

        except Exception as exc:

            logger.exception(
                "Ollama LLM request failed."
            )

            raise RuntimeError(
                "Failed to process the Ollama LLM request."
            ) from exc