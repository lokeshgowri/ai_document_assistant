from app.services.llm_service import LLMService


llm = LLMService()

context = """
Employees are entitled to 20 days of annual leave per year.
Employees should submit leave requests through the HR portal.
"""

question = " "

answer = llm.generate_answer(
    question=question,
    context=context
)

print("QUESTION:")
print(question)

print("\nANSWER:")
print(answer)