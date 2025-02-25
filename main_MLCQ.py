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
import datetime
from pathlib import Path

from settings import ROOT_DIR, DATA_DIR, LOG_DIR
#from loggers import setup_logging, initialize_neptune
from utils.file_utils import initialize_file_for_all_repos
from analysis.commit_analysis import analyze_commits_mlcq, analyze_modifications_mlcq
#from evaluation import evaluate_results
from evaluation.evaluate_results import evaluate_results
from utils.mlcq_dataset_utils import extract_unique_repo_commits, extract_repo_commits_from_file
#import config


def main(model_type, eval_mode='file_level', ground_truth=None, resume=False, schema='Few-shot_p4_Java_MLCQ.xml'):
    """
    Iterates over multiple repositories and their associated commit lists, calling the main function for each.

    :param repo_commit_dict: Dictionary where keys are repository URLs and values are lists of commit hashes
    :param model_type: Name of the model that will be used to perform the analysis
    :param eval_mode: Evaluation mode (file_level, multi_class, or line_level)
    :param ground_truth: Path to the ground truth file
    :param resume: Flag indicating whether to resume the analysis or not
    :param schema: Schema configuration file
    """
    # Model type
    #config.model_type = model_type
    #logging.info(f"MODEL_TYPE has been set to: {model_type}")

    #config.repo_url = repo_url
    #logging.info(f"REPO_URL has been set to: {repo_url}")

    #config.schema = schema
    #logging.info(f"Schema has been set to: {schema}")

    #setup_logging()
    # Initialize Neptune run
    #run = initialize_neptune()
    #run["model"] = model_type
    #run["repository"] = repo_url
    #run["schema"] = schema

    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    
    # Generate the log file name based on current timestamp
    now_time = datetime.datetime.now()
    date_str = now_time.strftime('%Y%m%d%H%M%S')
    log_file_name = f'{date_str}.log'
    
    # Full log file path
    app_log_file_path = os.path.join(LOG_DIR, log_file_name)
    
    # Configure the logging settings
    logging.basicConfig(filename=app_log_file_path,
                        filemode='a',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S',
                        level=logging.INFO,
                        force=True)
    logging.info("Logging setup complete.")  # Test log message

    # If ground_truth is not provided by the user, set a default value
    if ground_truth is None:
        ground_truth_relative_path =  "Groundtruth_data/groundtruth_jxpath.json"
        ground_truth_file_path = os.path.join(DATA_DIR, ground_truth_relative_path)
        ground_truth = ground_truth_file_path
    else:
        ground_truth = os.path.join(DATA_DIR, ground_truth)

    # Initialize a SINGLE debt tracking file for all repositories
    debts, debts_file = initialize_file_for_all_repos(schema, model_type, resume)
    
    repo_commit_dict = extract_unique_repo_commits(ground_truth)

    for repo_url, commit_list in repo_commit_dict.items():
        logging.info(f"Processing repository: {repo_url} with {len(commit_list)} commits.")
        
        # Call the original main function for each repository
        iterate_main(
            repo_url=repo_url,
            model_type=model_type,
            eval_mode=eval_mode,
            ground_truth=ground_truth,
            resume=resume,
            schema=schema,
            commit_list=commit_list,  # Passing commit list for processing
            debts=debts,  # Shared dictionary for all repos
            debts_file=debts_file  # Shared file path
        )


def iterate_main(repo_url, model_type, eval_mode='file_level', ground_truth=None, resume=False, schema='One-shot_p5_CS.xml',
         commit=None, commit_list=None, begin_commit=None, end_commit=None, debts=None, debts_file=None):
    """
    The main function that runs the program for one commit, a list of commits, or a range of commits.
    """

    # Load relevant files from ground truth
    relevant_files = extract_unique_repo_commits(ground_truth).get(repo_url, {})

    # Use Case 1: Single commit
    if commit:
        logging.info(f"Analyzing single commit...")
        analyze_commits_mlcq(repo_url, commit, commit, model_type, debts, debts_file, schema, relevant_files)

    # Use Case 2: List of commits
    elif commit_list:
        for commit_hash in commit_list:
            logging.info(f"Analyzing commit list...")
            analyze_commits_mlcq(repo_url, commit_hash, commit_hash, model_type, debts, debts_file, schema, relevant_files)

    # Use Case 3: Commit range (begin_commit to end_commit)
    elif begin_commit and end_commit:
        logging.info(f"Analyzing commit range...")
        analyze_commits_mlcq(repo_url, begin_commit, end_commit, model_type, debts, debts_file, schema, relevant_files)

    else:
        raise ValueError("Please provide a valid commit, commit_list, or begin_commit and end_commit.")

    logging.info("Completed analysis.")

# def main(model_type, eval_mode='file_level', ground_truth=None, resume=False, schema='Few-shot_p4_Java_MLCQ.xml'):

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Analyze a GitHub repository for technical debts.")
    
    # Required positional arguments
    #parser.add_argument("repo_url", help="URL of the GitHub repository to analyze")
    parser.add_argument("model_type", help="Type of LLM model. Valid choices are OPENAI or a valid list of Ollama models")

    # Optional parameters
    parser.add_argument("--schema", help="Type of prompt schema.", default='One-shot_p5_CS.xml')
    parser.add_argument("--eval_mode", help="Evaluation mode (e.g., file_level, multi_class, or line_level)", default='file_level')
    parser.add_argument("--ground_truth", help="Path to the ground truth file", default=None)
    parser.add_argument("--resume", action="store_true", help="Resume from the last saved state")
    
    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with the appropriate arguments
    main( 
        model_type=args.model_type, 
        schema=args.schema,
        eval_mode=args.eval_mode,
        ground_truth=args.ground_truth,
        resume=args.resume
    )
