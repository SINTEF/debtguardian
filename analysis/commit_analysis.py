from pydriller import Repository
from rich import print
import datetime
import logging
import json


from utils.file_utils import url_to_filename, is_source_code, enumerate_file
from utils.logging_utils import print_commit_analysis_start, print_file_analysis_start
from analysis.guardrails_handler import createGuard
from analysis.debt_detection import debtDetect, update_debts_and_save

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

