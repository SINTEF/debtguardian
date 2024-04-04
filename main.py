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

import guardrails as gd
from langchain_community.llms import Ollama
from pydriller import Repository
from rich import print
import logging

from Helpers import url_to_filename, should_skip_commit, print_bar, is_source_code, enumerate_file, \
    print_file_analysis_start
from Technical_Schema import CodeInfo


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
