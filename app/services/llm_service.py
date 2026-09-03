import logging

import ollama


logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self, model: str = "llama3.2"):
        self.model = model

    def generate_answer(
        self,
        question: str,
        context: str
    ) -> str:

        prompt = f"""
You are a strict document question-answering assistant.

Answer the user's question using ONLY the information provided in the
document context.

IMPORTANT RULES:

1. Answer ONLY what the user asked.
2. Do NOT provide a list of all related information unless the user
   explicitly asks for a list.
3. Identify the specific information in the context that answers the
   question.
4. Do not use outside knowledge.
5. Do not guess or make assumptions.
6. Do not convert, calculate, or reinterpret values unless the context
   explicitly provides that information.
7. Preserve the units exactly as written in the context.
8. If the context does not contain enough information to answer the
   specific question, say:
   "I could not find the answer in the provided documents."
9. Give a short, direct answer and be brief if the user asks for it.

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
                "Sending question to LLM: %s",
                question
            )

            response = ollama.generate(
                model=self.model,
                prompt=prompt
            )

            answer = response["response"].strip()

            logger.info(
                "LLM response generated successfully."
            )

            return answer

        except Exception as exc:

            logger.exception(
                "LLM request failed."
            )

            raise RuntimeError(
                "Failed to generate an answer using the LLM."
            ) from exc