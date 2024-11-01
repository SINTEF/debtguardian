import json
from collections import defaultdict
from utils.file_utils import load_json

# Evaluation function discarding line-level detection and multi-class classification
# This version only checks if the file contains technical debt or not
def evaluate_file_level_detection(ground_truth_file_path, model_output_file_path, commit_list=None):
    """
    Evaluates file-level detection of technical debt.
    
    Parameters:
    - ground_truth_file_path: str, path to the ground truth JSON file.
    - model_output_file_path: str, path to the model output JSON file.
    - commit_list: list, optional, list of commit hashes to filter the evaluation. 
                   If None, evaluate on all commits.

    Returns:
    - dict: Evaluation metrics including precision, recall, F1-score, etc.
    """
    # Load the ground truth data
    ground_truth = load_json(ground_truth_file_path)
    
    # Process only the specified commit list if provided, else process the entire ground truth
    if commit_list is not None:
        #filtered_ground_truth = {commit: ground_truth.get(commit, []) for commit in commit_list}
        filtered_ground_truth = {commit: files for commit, files in ground_truth.items() if commit in commit_list}
    else:
        filtered_ground_truth = ground_truth

    # Initialize counts for overall metrics
    TP, FP, FN = 0, 0, 0

    # Ground truth debts stored by commit hash for easy lookup
    gt_files_with_debt = defaultdict(set)

    for commit, files in filtered_ground_truth.items():
        for file_info in files:
            # Ensure technicalDebts field is present in ground truth
            if 'technicalDebts' in file_info and file_info['technicalDebts']:
                gt_files_with_debt[commit].add(file_info['location'])

    # Load the model output
    model_output = load_json(model_output_file_path)

    # Process the model's output and ensure commit hash matches
    if commit_list is not None:
        #filtered_model_output = {commit: model_output.get(commit, []) for commit in commit_list}
        filtered_model_output = {commit: files for commit, files in model_output.items() if commit in commit_list}
    else:
        filtered_model_output = model_output

    for commit, files in filtered_model_output.items():
        if commit not in gt_files_with_debt:
            # The commit is not in ground truth, so all predictions for this commit are false positives
            for file_info in files:
                # Check if 'technicalDebts' exists and the file is flagged for debt
                if file_info.get('technicalDebts'):
                    FP += 1
            continue

        gt_files = gt_files_with_debt[commit]
        predicted_files_with_debt = set()

        # Check if the model correctly detected a technical debt in the file
        for file_info in files:
            # Handle cases where 'technicalDebts' might not be present in the model output
            if file_info.get('technicalDebts'):
                predicted_files_with_debt.add(file_info['location'])

        # Calculate TP, FP, FN
        for file_location in predicted_files_with_debt:
            if file_location in gt_files:
                TP += 1  # Correctly predicted a file containing technical debt
            else:
                FP += 1  # False positive (predicted debt in a file where there is none)

        # Count files with technical debt in the ground truth but not predicted
        for file_location in gt_files:
            if file_location not in predicted_files_with_debt:
                FN += 1  # False negative (missed detecting debt in a file)

    # If there are commits in the ground truth but not in the model output, count them as false negatives
    for commit in gt_files_with_debt:
        if commit not in filtered_model_output:
            FN += len(gt_files_with_debt[commit])

    # Calculate precision, recall, and F1-score
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = TP / (TP + FP + FN) if (TP + FP + FN) > 0 else 0

    return {
        "TP": TP,
        "FP": FP,
        "FN": FN,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "accuracy": accuracy
    }


if __name__ == "__main__":
    # Load ground truth and model output files
    ground_truth_file = "ground_truth.json"
    model_output_file = "model_output.json"
    
    # Optional: Specify a list of commit hashes to filter the evaluation
    commit_list = ["7b57bd3398d03c84b36567cf6c414e67a251d092", "ab34cd123ef5678906789ff456abcd12ef456789"] 
    
    # Evaluate the results at the file level (ignoring technical debt type and line detection)
    metrics = evaluate_file_level_detection(ground_truth_file, model_output_file, commit_list)
    
    # Print metrics
    for metric, value in metrics.items():
        print(f"{metric}: {value}")
