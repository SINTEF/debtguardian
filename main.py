"""
Project: Technical and Security Debt Analysis in GitHub Repositories
Program name: DebtGuardianAI
Author: Aleksander Aaboen and Sagar Sen
Date created: 12-03-2024
Copyright: (c) 2024 Sagar Sen and Aleksander Aaboen. All rights reserved.
Notes: This program analyzes commits in GitHub repositories to identify patterns that might indicate security debt. 
The analysis includes checking for hard-coded credentials, use of outdated libraries, and other common security debt indicators.
Contact: aleksander.aaboen@stinef.no,  sagar.sen@sintef.no
"""
import argparse
import logging
import os 

from settings import ROOT_DIR, DATA_DIR
from loggers import setup_logging, initialize_neptune
from utils.file_utils import initialize_file
from analysis.commit_analysis import analyze_commits
#from evaluation import evaluate_results
from evaluation.evaluate_results import evaluate_results
import config

def main(repo_url, model_type, eval_mode='file_level', ground_truth=None, resume=False, 
         commit=None, commit_list=None, begin_commit=None, end_commit=None):
    """
    The main function that runs the program for one commit, a list of commits, or a range of commits.

    :param repo_url: URL of the repo that needs to be analyzed
    :param model_type: Name of the model that will be used to perform the analysis
    :param eval_mode: Evaluation mode (file_level, multi_class, or line_level)
    :param ground_truth: Path to the ground truth file
    :param resume: Flag indicating whether to resume the analysis or not
    :param commit: Single commit hash to analyze
    :param commit_list: List of commit hashes for analysis
    :param begin_commit: Starting commit hash in a sequential range of commits
    :param end_commit: Ending commit hash in a sequential range of commits
    :return:
    """
    # Model type
    config.model_type = model_type
    logging.info(f"MODEL_TYPE has been set to: {model_type}")

    config.repo_url = repo_url
    logging.info(f"REPO_URL has been set to: {repo_url}")

    setup_logging()
    # Initialize Neptune run
    run = initialize_neptune()
    run["model"] = model_type
    run["repository"] = repo_url

    # If ground_truth is not provided by the user, set a default value
    if ground_truth is None:
        ground_truth_relative_path =  "Groundtruth_data/groundtruth_jxpath.json"
        ground_truth_file_path = os.path.join(DATA_DIR, ground_truth_relative_path)
        ground_truth = ground_truth_file_path
    else:
        ground_truth = os.path.join(DATA_DIR, ground_truth)

    # Initialize debts and debts_file once before processing the commits
    debts, debts_file = initialize_file(repo_url, model_type, resume)

    # Use Case 1: Single commit
    if commit:
        logging.info(f"Analyzing single commit: {commit}")
        analyze_commits(repo_url, commit, commit, model_type, debts, debts_file)
        run[f"commit/{commit}"] = "completed"

        # Evaluation for a single commit
        logging.info(f"Evaluating single commit: {commit}")
        metrics = evaluate_results(eval_mode, ground_truth, debts_file, commit_hash=commit, run=run)

    # Use Case 2: List of commits
    elif commit_list:
        for commit_hash in commit_list:
            logging.info(f"Analyzing commit: {commit_hash}")
            analyze_commits(repo_url, commit_hash, commit_hash, model_type, debts, debts_file)
            run[f"commit/{commit_hash}"] = "completed"

        # Evaluation for a list of commits
        logging.info("Evaluating list of commits.")
        metrics = evaluate_results(eval_mode, ground_truth, debts_file, commit_list=commit_list, run=run)

    # Use Case 3: Commit range (begin_commit to end_commit)
    elif begin_commit and end_commit:
        logging.info(f"Analyzing commit range: {begin_commit} to {end_commit}")

        # Analyze commits in the range
        analyze_commits(repo_url, begin_commit, end_commit, model_type, debts, debts_file)
        run[f"commit/{begin_commit}_to_{end_commit}"] = "completed"

        # Evaluation for the commit range using PyDriller to handle the range traversal
        logging.info(f"Evaluating commit range: {begin_commit} to {end_commit}")
        metrics = evaluate_results(eval_mode, ground_truth, debts_file, repo_url=repo_url, 
                                   begin_commit=begin_commit, end_commit=end_commit, run=run)

    else:
        raise ValueError("Please provide a valid commit, commit_list, or begin_commit and end_commit.")

    logging.info("Completed analysis and evaluation.")

    # Log the overall metrics to Neptune
    run["overall_metrics"] = metrics

    # Stop the Neptune run
    run.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a GitHub repository for technical debts.")
    parser.add_argument("repo_url", help="URL of the GitHub repository to analyze")
    parser.add_argument("model_type", help="Type of LLM model. Valid choices are OPENAI or a valid list of Ollama models")
    parser.add_argument("begin_commit", help="Start commit hash", nargs='?', default=None)
    parser.add_argument("end_commit", help="End commit hash", nargs='?', default=None)
    parser.add_argument("--commit", help="Analyze a single commit hash", default=None)
    parser.add_argument("--commit_list", help="List of commit hashes to analyze", nargs='*', default=None)
    parser.add_argument("--resume", action="store_true", help="Resume from the last saved state")
    args = parser.parse_args()

    # Model type
    config.model_type = args.model_type

    # Call the main function with the appropriate arguments
    main(repo_url=args.repo_url, 
         model_type=args.model_type, 
         begin_commit=args.begin_commit, 
         end_commit=args.end_commit, 
         commit=args.commit, 
         commit_list=args.commit_list, 
         resume=args.resume)
