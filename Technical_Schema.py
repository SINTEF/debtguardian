from typing import List

from guardrails.validators import ValidChoices
from pydantic import BaseModel, Field

class TechnicalDebt(BaseModel):
    """
    Identified technical debts in the code snippet. Each technical debt is an instance of the TechnicalDebt class.
    """
    type: str = Field(
        description="What type of technical debt is identified in this code snippet?",
        validators=[
            ValidChoices(
                choices=[
                    'Nested flow statements',
                    'Duplicated string literals',
                    'Long method',
                    'Duplicated code blocks',
                    'Insufficient Logging of Exceptions',
                    'Improper Exception Handling',
                    'Poor Code Formatting',
                    'Commented out code',
                    'Inappropriate Handling of Floating-Point Operations',
                    'Insufficient Logging Mechanism',
                    'Too many lines in switch case',
                    'Long parameter list',
                    'Using old Classes Vector, hashtable, stack and stringBuffer',
                    'Empty methods',
                ],
                on_fail="reask"
            )
        ])
    symptom: str = Field(..., description="Technical debt in the code snippet.")
    affected_area: str = Field(...,
                               description="Provide the exact lines of code that contain the technical debt. Include "
                                           "the raw code snippet from the file without any summarization or "
                                           "modification.")
    suggested_repair: str = Field(..., description="Generate code to refactor or repair the technical debt")


class SecurityDebt(BaseModel):
    type: str = Field(
        description="What is the security debt in this code snippet?",
        validators=[
            ValidChoices(
                choices=[
                    'Hardcoded Secrets',
                    'Insecure Dependencies',
                    'Lack of Input Validation',
                    'Insufficient Error Handling',
                    'Inadequate Encryption',
                    'Improper Session Management',
                    'Insecure Default Settings',
                    'Lack of Principle of Least Privilege',
                    'Insecure Direct Object References',
                    'Cross-Site Request Forgery (CSRF)',
                    'Ignoring Security Warnings',
                    'Not Adhering to Secure Coding Standards'
                ],
            )
        ], on_fail="reask")
    symptom: str = Field(description="Security debt in the code snippet.")
    affected_area: str = Field(description="What are the code snippet with the security debt?")
    suggested_repair: str = Field(description="Generate code to refactor or repair the security debt")


class CodeInfo(BaseModel):
    """
    A model representing various aspects of a code snippet, including its functionality, size, and associated debts.

    This class is designed to encapsulate information about a code snippet, such as its purpose, the number of lines it contains,
    and any identified technical or security debts. It uses the Pydantic library for data validation and settings management.

    Attributes:
    - snippet_functionality (str): Describes the functionality of the code snippet.
    - number_of_lines (int): Indicates the total number of lines in the code snippet.
    - securityDebts (List[SecurityDebt]): A list of identified security debts in the code snippet. Each security debt is an instance of the SecurityDebt class.
    - technicalDebts (List[TechnicalDebt]): A list of identified technical debts in the code snippet. Each technical debt is an instance of the TechnicalDebt class.
    """
    snippet_functionality: str = Field(description="What is the functionality of this code snippet?")
    number_of_lines: int = Field(description="What is the number of lines of code in this code snippet?")
    securityDebts: List[SecurityDebt] = Field(
        description="Are there security debts in the code snippet? Each security debt should be classified into  "
                    "separate item in the list.")
    technicalDebts: List[TechnicalDebt] = Field(
        description="Are there technical debts in the code snippet? Each technical debt should be classified into  "
                    "separate item in the list.")
