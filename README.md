# DebtGuardian

<img src="assets/logo_DebtGuardianAI.png" alt="debtguardian Logo" width="200"/>


**DebtGuardian** is a sophisticated AI-powered tool engineered to identify and mitigate technical and security debts in repositories on GitHub. The system leverages a Large Language Model (LLM) along with a third-party package called Guardrails-AI for its operation. Guardrails-AI plays a crucial role in standardizing the output from the LLM, guaranteeing that consistent and comprehensive details are provided for every instance of technical debt detected.

The workflow of DebtGuardian is both efficient and comprehensive. Initially, it scans GitHub repositories to gather modified source code, which is then fed into a carefully structured prompt that guides the LLM in its analysis. This prompt is crafted to ensure the most accurate identification of technical and security debts. If the initial attempt doesn't yield satisfactory results, DebtGuardian dynamically refines and resubmits the prompt to the LLM, engaging in an iterative process to enhance accuracy and detail in its findings.

Supporting a range of models from OpenAI and [Ollama supported models](https://ollama.com/library), DebtGuardian offers users the flexibility to choose the most suitable model for their specific needs. This adaptability, combined with the tool's rigorous workflow of scanning, analyzing, and iteratively refining queries to the LLM, positions DebtGuardian as a vital asset for developers aiming to maintain high standards of code quality and security in their GitHub projects.

## Pre-requisites
- `!pip install pydriller`
- `!pip install requests`
- `!pip install openai==1.6.1`
- `!pip install langchain-community`
- `!pip install pygments`
- `!pip install pydantic==2.4.0`
- `!apt-get install -y graphviz openjdk-11-jre-headless`
- `!pip install guardrails-ai==0.4.1`
- `!pip install typing rich`
- `!pip install tiktoken`
- `Python 3.9+`


## Usage

Begin by installing all the Pre-requisites. 

> pip install -r requirements.txt

> sudo apt-get install -y graphviz openjdk-11-jre-headless


### Usage of OPENAI

Set OpenAI environment variable

export OPENAI_API_KEY='your_api_key_here'


Update OpenAI engine information in main.py. It's currently set to our OpenAI running on our Azure deployment

- engineName="jaipetefort"
- openai.api_type = "azure"
- openai.api_base = "https://03.openai.azure.com/"
- openai.api_version = "2023-07-01-preview"


Command to find technical and security debts

>python3 main.py GitHub-Repo-Address Start-Commit-Hash End-Commit-Hash OPENAI


### Usage of Ollama Models


Start the Ollama instance on your computer with default port  (11434). 

This can be done using the terminal command:

> ollama serve

After this you will need to download the Model you would like to use. A list of valid models is available here: https://ollama.com/library

The model can be downloaded with this command:
> ollama pull model_name

After the model is downloaded you can execute the **DebtGuardian**

>python3 main.py GitHub-Repo-Address Start-Commit-Hash End-Commit-Hash model_name


## Output

The program generates <GitHub Repo>_debts_<model_name>.json

Here is an example snippet for debts found in a GitHub Repo:

```json
"bbcd50c734902901cc54c61e5e03038ebe6ffebf": {
    "snippet_functionality": "This code snippet is used to authenticate a user with the Tripletex API using consumer and employee tokens. It creates a session token that is valid for one hour from the current time.",
    "number_of_lines": 26,
    "securityDebts": [
        {
            "type": "Hardcoded Secrets",
            "symptom": "The code snippet uses hardcoded values for authentication.",
            "affected_area": "Lines 20-21",
            "suggested_repair": "Use environment variables or a secure configuration file to store sensitive information such as tokens."
        },
        {
            "type": "Improper Session Management",
            "symptom": "The session token is set to expire after one hour without any mechanism for renewal or invalidation.",
            "affected_area": "Line 18",
            "suggested_repair": "Implement a mechanism to renew or invalidate the session token as needed."
        }
    ],
    "technicalDebts": [
        {
            "type": "Error/Exception Handling",
            "symptom": "The code does not handle potential exceptions that may be thrown by the Tripletex API.",
            "affected_area": "Lines 15-23",
            "suggested_repair": "Wrap the API calls in a try-catch block and handle potential exceptions appropriately."
        },
        {
            "type": "Hard-coded Values",
            "symptom": "The username is hardcoded to '0'.",
            "affected_area": "Line 22",
            "suggested_repair": "Avoid hardcoding values. Use a variable or constant instead."
        }
    ],
    "location": "example/java-gradle/order/src/main/java/no/tripletex/example/order/Example.java",
    "repository": "https://github.com/Tripletex/tripletex-api2.git"
}
```


## DebtGuardian Seminar Presentation
For additional details on DebtGuardian's functionality and its underlying architecture, please refer to the provided url. This resource explains how DebtGuardian leverages Large Language Models to detect technical debt in source code (in Norwegian).

Generativ KI: Utvikling og samfunnspåvirkning :  [Utforsking av bruken av store språkmodeller i deteksjonen av teknisk gjeld i programvareutvikling](https://www.youtube.com/live/fLZGCKw06LE?si=4DFquPM-vsesAlVI&t=13682)

## Support
For questions, issues, or assistance with DebtGuardian, please create an Issue in the GitHub Repository.

