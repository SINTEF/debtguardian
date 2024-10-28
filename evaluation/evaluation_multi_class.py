import json
from collections import defaultdict

# Function to load JSON files
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Function to normalize debt types (case insensitive)
def normalize_debt_type(debt_type):
    return debt_type.strip().lower()

# Function to check if two technical debts match based on their type and file location (ignoring line-level info)
def debts_match_type_only(debt1, debt2):
    return debt1['type'] == debt2['type']  # Match only by type, ignoring line-level info

# Evaluation function for multi-class classification (ignoring line-level detection)
def evaluate_type_classification(ground_truth_file_path, model_output_file_path, commit_list=None):
    """
    Evaluates multi-class classification for technical debts.

    Parameters:
    - ground_truth: dict, the ground truth data.
    - model_output: dict, the model output data.
    - commit_list: list, optional, a list of commit hashes to filter the evaluation.

    Returns:
    - dict: Evaluation results.
    """
    #Load the grounth truth data
    ground_truth = load_json(ground_truth_file_path)
    #Load the model output
    model_output = load_json(model_output_file_path)

    # If commit_list is provided, filter the ground_truth and model_output accordingly
    if commit_list is not None:
        ground_truth = {commit: files for commit, files in ground_truth.items() if commit in commit_list}
        model_output = {commit: files for commit, files in model_output.items() if commit in commit_list}

    # Initialize counts for overall metrics
    TP, FP, FN = 0, 0, 0
    category_metrics = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0})

    # Ground truth debts stored by commit hash and debt type for easy lookup
    gt_by_commit = defaultdict(list)

    for commit, files in ground_truth.items():
        for file_info in files:
            location = file_info['location']
            for debt in file_info['technicalDebts']:
                gt_by_commit[commit].append({
                    'location': location,
                    'type': debt['type']
                })

    # Process the model's output and ensure commit hash matches
    for commit, files in model_output.items():
        if commit not in gt_by_commit:
            # The commit is not in ground truth (considered as FP)
            for file_info in files:
                for pred_debt in file_info['technicalDebts']:
                    FP += 1
                    category_metrics[normalize_debt_type(pred_debt['type'])]['FP'] += 1
            continue

        gt_debts = gt_by_commit[commit]
        matched_indices = set()

        for file_info in files:
            location = file_info['location']
            for pred_debt in file_info['technicalDebts']:
                # Try to match each predicted debt with the ground truth (ignoring line-level details)
                matched = False
                for i, gt_debt in enumerate(gt_debts):
                    if i in matched_indices:
                        continue  # Skip already matched ground truth debt
                    if gt_debt['location'] == location and debts_match_type_only(gt_debt, pred_debt):
                        TP += 1
                        category_metrics[normalize_debt_type(gt_debt['type'])]['TP'] += 1
                        matched_indices.add(i)
                        matched = True
                        break
                if not matched:
                    FP += 1
                    category_metrics[normalize_debt_type(pred_debt['type'])]['FP'] += 1

        # Any remaining ground truth debts are false negatives
        FN += len(gt_debts) - len(matched_indices)
        for i in range(len(gt_debts)):
            if i not in matched_indices:
                category_metrics[normalize_debt_type(gt_debts[i]['type'])]['FN'] += 1

    # If there are commits in the ground truth but not in the model output, count them as false negatives
    for commit in gt_by_commit:
        if commit not in model_output:
            FN += len(gt_by_commit[commit])
            for debt in gt_by_commit[commit]:
                category_metrics[normalize_debt_type(debt['type'])]['FN'] += 1

    # Calculate precision, recall, and F1-score for each category
    per_category_metrics = {}
    for debt_type, counts in category_metrics.items():
        precision = counts['TP'] / (counts['TP'] + counts['FP']) if counts['TP'] + counts['FP'] > 0 else 0
        recall = counts['TP'] / (counts['TP'] + counts['FN']) if counts['TP'] + counts['FN'] > 0 else 0
        f1_score = (2 * precision * recall) / (precision + recall) if precision + recall > 0 else 0
        per_category_metrics[debt_type] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }

    # Calculate overall metrics
    overall_precision = TP / (TP + FP) if TP + FP > 0 else 0
    overall_recall = TP / (TP + FN) if TP + FN > 0 else 0
    overall_f1_score = (2 * overall_precision * overall_recall) / (overall_precision + overall_recall) if overall_precision + overall_recall > 0 else 0
    overall_accuracy = TP / (TP + FP + FN) if TP + FP + FN > 0 else 0

    return {
        "TP": TP,
        "FP": FP,
        "FN": FN,
        "precision": overall_precision,
        "recall": overall_recall,
        "f1_score": overall_f1_score,
        "accuracy": overall_accuracy,
        "per_category_metrics": per_category_metrics
    }

# evaluation_results = evaluate_type_classification('ground_truth.json', 'model_output.json')
# print(json.dumps(evaluation_results, indent=4))