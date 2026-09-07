from app.services.text_cleaner import clean_text


raw_text = """
    
    
Company Leave Policy


Employees    are    entitled    to    20 days of annual leave per year.


Employees\tshould submit leave requests through the HR portal.


"""


cleaned_text = clean_text(raw_text)

print("RAW TEXT:")
print(repr(raw_text))

print("\nCLEANED TEXT:")
print(repr(cleaned_text))