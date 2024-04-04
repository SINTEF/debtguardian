"""
Project: Technical and Security Debt Analysis in GitHub Repositories
Program name: DebtGuardianAI
Author: Aleksander Aaboen and Sagar Sen
Date created: 12-03-2024
Copyright: (c) 2024 Sagar Sen and Aleksander Aaboen. All rights reserved.
Notes: This program analyzes commits in GitHub repositories to identify patterns that might indicate security debt. The analysis includes checking for hard-coded credentials, use of outdated libraries, and other common security debt indicators.
Contact: aleksander.aaboen@stinef.no,  sagar.sen@sintef.no
"""
import argparse
import json
import os
import re
import textwrap
from typing import List
import logging

import guardrails as gd
from langchain_community.llms import Ollama
from guardrails.validators import ValidChoices
from pydantic import BaseModel, Field
from pydriller import Repository
from rich import print


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


def createGuard(code_changes):
    """
    Creates the guard that will be used to validate and structure the output of the  large language model
    Args:
        code_changes: The code changes that is fetched from GitHub

    Returns: The guard

    """
    logging.info("Creating guard object for code changes")
    try:
        prompt = """Given the following code snippet, please extract a dictionary that contains the technical debt in the code. 
        Validate if these technical debts actually exist.

        ${code_changes} <!-- (2)! -->

        ${gr.complete_json_suffix_v2} <!-- (3)! -->
        """
        guard = gd.Guard.from_pydantic(output_class=CodeInfo, prompt=prompt)
        logging.debug("Guard object created successfully")
        return guard
    except Exception as e:
        logging.error("Error creating guard object: %s", str(e))
        raise


def call_with_guardrails_ollama(prompt: str, *args, **kwargs):
    """
    Function that calls the large language model with the provided prompt.
    Args:
        prompt: Includes code changes, and structure from guardrails
        *args:
        **kwargs:

    Returns: The response from the large language model

    """

    logging.info("Calling AI Model with guardrails")
    # Initialize Ollama
    ollama = Ollama(base_url='http://localhost:11434', model=MODEL_TYPE)
    # Get the response from Ollama
    response = ollama(prompt, *args, **kwargs)
    logging.debug("Beginning to extract JSON from response")

    # Extract JSON from the response
    return response


def call_with_guardrails_openai(prompt: str, *args, **kwargs):
    """
     Function that calls the open-ai GPT model with the provided prompt.
     Args:
         prompt: Includes code changes, and structure from guardrails
         *args:
         **kwargs:

     Returns: The response from the large language model

     """
    from openai import AzureOpenAI

    openai = AzureOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        api_version=os.getenv("OPENAI_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    )
    response = openai.chat.completions.create(
        model="gpt-4-32k",
        messages=[{"role": "user", "content": prompt}],
        *args,
        **kwargs
    )
    return response.choices[0].message.content


def debtDetect(code_changes, guard, model_type):
    """
    Function that wraps the guard around the LLM call.
    This will make sure that the output will be validated and structured.
    Args:
        model_type:
        code_changes: Changes from the code changes that is fetched from GitHub
        guard: That will be used to validate and structure the output of the large language model.

    Returns: The validated output that the guard has checked and verified

    """
    logging.info("Detecting debts in code changes")

    try:
        call_llm = call_with_guardrails_openai if model_type == 'OPENAI' else call_with_guardrails_ollama

        res = guard(
            call_llm,
            prompt_params={"code_changes": code_changes},
            num_reasks=5,
            temperature=0.3,
        )
        logging.debug("Debt detection completed")

        return res.validated_output

    except Exception as e:
        if "token limit exceeded" in str(e).lower():
            logging.warning("Error: Token limit exceeded in debtDetect")
        else:
            logging.error("Error in debtDetect: %s", str(e))
        raise


def is_source_code(filename):
    logging.debug("Checking if %s is a source code file", filename)

    """
    Determine if a given filename corresponds to a source code file.

    This function checks the file extension against a predefined list of common
    source code file extensions. It's a simple way to guess if a file is a source code file.

    Args:
    - filename (str): The name of the file to check.

    Returns:
    - bool: True if the file extension matches a known source code extension, False otherwise.
    """

    try:
        # A basic list of source code extensions; can be expanded based on requirements
        source_code_extensions = [
            '.c', '.cpp', '.h', '.java', '.py', '.js', '.php',
            '.cs', '.rb', '.go', '.rs', '.ts', '.m', '.swift',
            '.f', '.f90', '.perl', '.sh', '.bash'
        ]

        # Extract the extension and check if it's in our list
        _, ext = os.path.splitext(filename)
        result = ext in source_code_extensions
        logging.debug("File %s is source code: %s", filename, result)
        return result
    except Exception as e:
        logging.error("Error in is_source_code for file %s: %s", filename, str(e))
        raise


def print_bar(length=200, char='█'):
    """
    Print a horizontal bar with a given length and character.

    :param length: Length of the bar to be printed
    :param char: Character to use for printing the bar
    """
    print(char * length)


def wrap_text(text, width=200):
    """
    Wrap the given text to the specified width.

    :param text: Text to wrap
    :param width: Width at which to wrap the text
    :return: Wrapped text
    """
    return textwrap.fill(text, width)


def url_to_filename(url):
    """
    converts the GitHub url to a valid file name
    Args:
        url: Url to the GitHub repository

    Returns: a sanitized file name

    """

    filename = re.sub(r'[\\/*?"<>|:]', '_', url)
    return filename


def enumerate_file(code_content: str):
    """
    The function will enumerate the file containing code

    This will help the LLM in determining which line contains technical debt
    Args:
        code_content: The code content that needs to be enumerated

    Returns: The enumerated file containing code.

    """
    lines = code_content.split('\n')
    enumerated_string = ""

    for index, line in enumerate(lines, start=1):
        enumerated_string += f"{index}. {line}\n"

    enumerated_string = enumerated_string.rstrip('\n')
    return enumerated_string


def extract_json(response: str):
    """
    The function will extract the json response that is given from the language model
    :param response: from the large language model
    :return: only the JSON response from the large language model
    """
    start = response.find('{')
    end = response.rfind('}') + 1
    json_data = response[start:end]
    return json_data


def initialize_file(repo_url, model_type, resume=False):
    """
    The function will open or create the file that the data is being saved into
    :param repo_url: The url for the GitHub repository
    :param model_type: The model type used for the analysis
    :param resume: flagging whether to resume the analysis after a commit
    :return:
        debts: The content of previous analysis
        debts_file: The file containing the debts for the analysis
    """
    logging.info("Starting analysis for repo: %s", repo_url)
    debts_file = url_to_filename(repo_url) + f'_debts_{model_type}.json'
    debts = {}

    if resume and os.path.exists(debts_file):
        logging.info("Resuming scan with file: %s", debts_file)
        with open(debts_file, 'r') as file:
            debts = json.load(file)
    else:
        with open(debts_file, 'w') as file:
            json.dump({}, file)

    return debts, debts_file


def analyze_commits(repo_url, begin_commit, end_commit, model_type, debts, debts_file):
    """
    The function will iterate through the commits and fetch the changed content from the previous commit.

    :param repo_url: The URL of the repo to analyze
    :param begin_commit: The commit-hash where the analysis will begin
    :param end_commit: The commit-hash where the analysis will stop
    :param model_type: The model type used for the analysis
    :param debts: the content of previous analysis
    :param debts_file: the file containing the debts for the analysis
    :return:
    """
    commit_count = 0
    for commit in Repository(repo_url, from_commit=begin_commit, to_commit=end_commit).traverse_commits():
        logging.info("Analyzing commit: %s", commit.hash)
        commit_count += 1

        if should_skip_commit(commit, debts):
            continue

        print_commit_analysis_start(commit, commit_count, repo_url)
        analyze_modifications(commit, debts, debts_file, repo_url, model_type)


def should_skip_commit(commit, debts):
    """
    Function that will determine if the system should skip the commits if it has already been analysed for a
    previous session

    :param commit: The commit hash that will be analysed
    :param debts: Content of the debts that already has been analysed
    :return: The condition to skip or not skip the commit
    """
    if commit.hash in debts and debts[commit.hash]:
        logging.info("Skipping commit: %s", commit.hash)
        return True
    return False


def print_commit_analysis_start(commit, commit_count, repo_url):
    """
    Function that will print where in the process the system is.

    This is to easier keep track of the analysis and debugging

    :param commit: The commit hash that will be analysed
    :param commit_count: The number of commits that has been analysed
    :param repo_url: The URL of the repo to analyze
    :return:
    """
    print_bar()
    print(f"\nAnalyzing Commit: {commit.hash} in {repo_url}\n")
    print(f"\nStarting on Commit no: {commit_count}\n")


def print_bar():
    """
    Function that will print a process bar
    :return:
    """
    print("=" * 40)


def analyze_modifications(commit, debts, debts_file, repo_url, model_type):
    """
    The function will go thorugh each commit in the repo and analyze.

    The analysis will create a Guard and

    :param commit: The commit-hash that will be analysed
    :param debts: The content of the debts that already has been analysed
    :param debts_file: The file where the debts are stored
    :param repo_url: The URL of the repo to analyze
    :param model_type: The model type used to analyze the commit
    :return:
    """
    for modification in commit.modified_files:
        if not modification.source_code or not is_source_code(modification.new_path):
            continue

        logging.debug("Analyzing file: %s", modification.new_path)
        enumerated_content = enumerate_file(modification.source_code)
        print_file_analysis_start(modification.new_path)

        guard = createGuard(enumerated_content)
        debt = debtDetect(enumerated_content, guard, model_type)

        if debt:
            update_debts_and_save(debt, debts, commit, debts_file, modification.new_path, repo_url)


def print_file_analysis_start(commit_hash):
    """
    Function that will print a bar and what file that it is analysing.

    :param commit_hash: of the commit that is being analyzed
    :return:
    """
    print_bar()
    print(f"\nAnalyzing {commit_hash}\n")


def update_debts_and_save(debt, debts, commit, debts_file, file_path, repo_url):
    """
    Function that will update and save the response from the LLM.

    :param debt: The new debt object that has been identified by the llm
    :param debts: The content of the previous debts that has been identified by the llm
    :param commit: The commit-hash of the commit that newly has been identified by the llm
    :param debts_file: The file where the debts are stored
    :param file_path: The file path where the debts are stored
    :param repo_url: URL of the repo that is being analysed
    :return:
    """
    logging.info("Debt identified in file: %s", file_path)
    debt["location"] = file_path
    debt["repository"] = repo_url
    print(json.dumps(debt, indent=4))

    if commit.hash not in debts:
        debts[commit.hash] = []
    debts[commit.hash].append(debt)

    with open(debts_file, 'w') as file:
        print("Saving to Debts JSON...")
        json.dump(debts, file, indent=4)


def main(repo_url, begin_commit, end_commit, model_type, resume=False):
    """
    The main function of the system that runs the program.

    :param repo_url: URL of the repo that needs to be analysed
    :param begin_commit: Commit-hash that indicates where the analysis will start
    :param end_commit: Commit-hash that indicates where the analysis will end
    :param model_type: Name of model that will be used to perform the analysis
    :param resume: Flag indicating whether to resume the analysis or not
    :return:
    """
    debts, debts_file = initialize_file(repo_url, model_type, resume)
    analyze_commits(repo_url, begin_commit, end_commit, model_type, debts, debts_file)
    logging.info("Completed analysis for repo: %s", repo_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a GitHub repository for technical debts.")
    parser.add_argument("repo_url", help="URL of the GitHub repository to analyze")
    parser.add_argument("begin_commit", help="Start commit hash")
    parser.add_argument("end_commit", help="End commit hash")
    parser.add_argument("model_type", help="Type of LLM model. Valid choices OPENAI or valid list of Ollama models")

    parser.add_argument("--resume", action="store_true", help="Resume from the last saved state")
    args = parser.parse_args()

    # Model type
    global MODEL_TYPE
    MODEL_TYPE = args.model_type

    main(args.repo_url, args.begin_commit, args.end_commit, args.model_type, args.resume)
