import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError


load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:

    def __init__(
        self,
        model: str = "gemini-3.6-flash"
    ):

        self.model = model

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured in the environment."
            )

        self.client = genai.Client(
            api_key=api_key
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

        try:

            logger.info(
                "Sending question to Gemini model: %s",
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

            raise RuntimeError(
                "Failed to generate an answer using Gemini."
            ) from exc

        except RuntimeError:
            raise

        except Exception as exc:

            logger.exception(
                "LLM request failed."
            )

            raise RuntimeError(
                "Failed to process the LLM request."
            ) from exc

