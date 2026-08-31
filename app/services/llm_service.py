import logging

import ollama


logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self, model: str = "llama3.2"):
        self.model = model

    def generate_answer(self, question: str, context: str) -> str:

        prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the information provided in the context.

Rules:
- Do not use outside knowledge.
- Do not make up or assume information.
- If the answer is not available in the context, say:
  "I could not find the answer in the provided documents."
- Give a clear and concise answer.

Context:
{context}

Question:
{question}

Answer:
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

            logger.info("LLM response generated successfully.")

            return answer

        except Exception as exc:
            logger.exception("LLM request failed.")

            raise RuntimeError(
                "Failed to generate an answer using the LLM."
            ) from exc