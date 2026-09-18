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
        context: str,
        conversation_history: str | None = None,
        memories: list[dict] | None = None
    ) -> str:
        formatted_history = self._format_conversation_history(
            conversation_history
            )

        prompt = f"""
You are a strict document question-answering assistant.

Your job is to answer the user's question using the provided
document context and conversation history.

IMPORTANT RULES:

1. Answer ONLY the specific current user question.

2. Use DOCUMENT CONTEXT as the ONLY source of truth for
   document-related facts.

3. Use CONVERSATION HISTORY only to understand references,
   follow-up questions, and what the user is referring to.

4. Do NOT use outside knowledge.

5. Do NOT invent facts.

6. Do NOT assume information that is not supported by
   DOCUMENT CONTEXT.

7. For a follow-up question, first determine what the
   current question is asking in relation to the previous
   conversation.

8. Do NOT simply repeat the answer given to the previous
   question.

9. If the current question asks about what happens next,
   what to do afterwards, who to inform, where to report,
   or a subsequent step, look specifically for that
   subsequent instruction in DOCUMENT CONTEXT.

10. When multiple document sections are provided, choose
    the section that directly answers the CURRENT question,
    rather than automatically repeating information from
    the previous question.

11. If the document directly answers the current question,
    provide a short direct answer.

12. If the document contains related information but does
    not explicitly answer the exact question, clearly state
    that the document does not explicitly specify the answer,
    and mention only relevant information that is actually
    stated.

13. If DOCUMENT CONTEXT contains no relevant information
    at all, respond EXACTLY with:

    "I could not find the answer in the provided documents."

14. Do not use LONG-TERM MEMORIES as a source of document
    facts.

15. Keep the answer short and direct.

16. Do not repeatedly use phrases such as "According to the
    document", "The document states", or "The policy states".
    Answer naturally.

CONVERSATION HISTORY:
---------------------
{formatted_history}
---------------------

LONG-TERM MEMORIES:
-------------------
{self._format_memories(memories)}
-------------------

DOCUMENT CONTEXT:
-----------------
{context}
-----------------

CURRENT USER QUESTION:
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
    def generate_memory(self, prompt: str) -> str:

        if self.provider == "gemini":
            return self._generate_with_gemini(prompt)
        
        if self.provider == "ollama":
            return self._generate_with_ollama(prompt)

        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _format_conversation_history(
            self,
            conversation_history
            ) -> str:
        if not conversation_history:
            return "No previous conversation."
        formatted_messages = []
        for message in conversation_history:
            if isinstance(message, dict):
                role = message.get("role", "")
                content = (message.get("content") or "").strip()
            else:
                role = getattr(message, "role", "")
                content = (getattr(message, "content", "") or "").strip()
            if not content:
                continue
            if role == "user":
                formatted_messages.append(
                    f"User: {content}"
                    )
            elif role == "assistant":
                formatted_messages.append(
                    f"Assistant: {content}"
                    )
        if not formatted_messages:
            return "No previous conversation."
        return "\n".join(formatted_messages)

    def _format_memories(
            self,
            memories: list[dict] | None
            ) -> str:
        if not memories:
            return "No long-term memories."

        formatted_memories = []
        for memory in memories:
            memory_text = memory.get("memory")
            if memory_text:
                formatted_memories.append(
                    f"- {memory_text}"
                    )
        if not formatted_memories:
            return "No long-term memories."
        return "\n".join(formatted_memories)

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
                    "stream": False,
                    "options": {
                        "temperature": 0,
                        "seed": 42
                    }
                },
                timeout=(10, 180)  # (connect timeout, read timeout)
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