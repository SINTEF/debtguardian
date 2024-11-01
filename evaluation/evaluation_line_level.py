import json
from collections import defaultdict
from utils.string_utils import normalize_debt_type
from utils.file_utils import load_json

# Function to check if two technical debts match based on their type
def debts_match_with_line_level(debt1, debt2, line_tolerance):
    return (normalize_debt_type(debt1['type']) == normalize_debt_type(debt2['type']) and 
            abs(debt1['lines']['start_line'] - debt2['lines']['start_line']) <= line_tolerance and
            abs(debt1['lines']['end_line'] - debt2['lines']['end_line']) <= line_tolerance)

# Function to calculate Intersection over Union (IoU) between predicted and ground truth lines
def calculate_iou(pred_lines, gt_lines):
    pred_set = set(range(pred_lines['start_line'], pred_lines['end_line'] + 1))
    gt_set = set(range(gt_lines['start_line'], gt_lines['end_line'] + 1))
    intersection = len(pred_set.intersection(gt_set))
    union = len(pred_set.union(gt_set))
    return intersection / union if union > 0 else 0

# Evaluation function considering both multi-class classification and line-level detection
def evaluate_with_line_detection(ground_truth_file_path, model_output_file_path, commit_list=None, iou_threshold=0.5, line_tolerance=2):

    # Load the ground truth data
    ground_truth = load_json(ground_truth_file_path)
    # Load the model output
    model_output = load_json(model_output_file_path)

    # Filter based on commit_list if provided
    if commit_list is not None:
        ground_truth = {commit: files for commit, files in ground_truth.items() if commit in commit_list}
        model_output = {commit: files for commit, files in model_output.items() if commit in commit_list}

    # Initialize counts for overall metrics
    TP, FP, FN = 0, 0, 0
    exact_match_count = 0  # For Exact Match Ratio
    total_iou = 0  # For IoU (Line-level)
    total_covered_lines = 0  # For Line Coverage Score
    total_ground_truth_lines = 0  # For Line Coverage Score

    category_metrics = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0})

    # Ground truth debts stored by commit hash for easy lookup
    gt_by_commit = defaultdict(list)
    for commit, files in ground_truth.items():
        for file_info in files:
            location = file_info['location']
            for debt in file_info['technicalDebts']:
                for area in debt['locations']:
                    gt_by_commit[commit].append({
                        'location': location,
                        'type': debt['type'],
                        'lines': area
                    })
                    total_ground_truth_lines += 1  # Count all ground truth lines

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
                # Try to match each predicted debt with the ground truth based on both type and line-level detection
                matched = False
                for i, gt_debt in enumerate(gt_debts):
                    if i in matched_indices:
                        continue  # Skip already matched ground truth debt
                    if gt_debt['location'] == location and debts_match_with_line_level(gt_debt, pred_debt, line_tolerance):
                        # Compare line-level IoU for the detected area
                        for pred_area in pred_debt['affected_area']:
                            iou = calculate_iou(pred_area, gt_debt['lines'])
                            if iou >= iou_threshold:  # IoU threshold for line-level detection
                                TP += 1
                                category_metrics[normalize_debt_type(gt_debt['type'])]['TP'] += 1
                                matched_indices.add(i)
                                matched = True
                                total_iou += iou  # Add IoU for matched debts
                                if pred_area == gt_debt['lines']:
                                    exact_match_count += 1  # Count exact matches
                                total_covered_lines += 1  # Count the number of covered lines
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
    average_precision_values = []  # For mAP calculation
    for debt_type, counts in category_metrics.items():
        precision = counts['TP'] / (counts['TP'] + counts['FP']) if counts['TP'] + counts['FP'] > 0 else 0
        recall = counts['TP'] / (counts['TP'] + counts['FN']) if counts['TP'] + counts['FN'] > 0 else 0
        f1_score = (2 * precision * recall) / (precision + recall) if precision + recall > 0 else 0
        per_category_metrics[debt_type] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }
        average_precision_values.append(precision)  # Collect precision for mAP

    # Calculate overall metrics
    overall_precision = TP / (TP + FP) if TP + FP > 0 else 0
    overall_recall = TP / (TP + FN) if TP + FN > 0 else 0
    overall_f1_score = (2 * overall_precision * overall_recall) / (overall_precision + overall_recall) if overall_precision + overall_recall > 0 else 0
    overall_accuracy = TP / (TP + FP + FN) if TP + FP + FN > 0 else 0

    # Exact Match Ratio (EMR)
    emr = exact_match_count / (TP + FP) if (TP + FP) > 0 else 0

    # IoU (Line-level)
    average_iou = total_iou / TP if TP > 0 else 0

    # Line Coverage Score
    line_coverage_score = total_covered_lines / total_ground_truth_lines if total_ground_truth_lines > 0 else 0

    # Mean Average Precision (mAP)
    mAP = sum(average_precision_values) / len(average_precision_values) if len(average_precision_values) > 0 else 0

    return {
        "TP": TP,
        "FP": FP,
        "FN": FN,
        "precision": overall_precision,
        "recall": overall_recall,
        "f1_score": overall_f1_score,
        "accuracy": overall_accuracy,
        "emr": emr, # Exact Match Ratio
        "average_iou": average_iou, # Line-level
        "line_coverage_score": line_coverage_score,
        "mAP": mAP, # Mean Average Precision 
        "per_category_metrics": per_category_metrics
    }


if __name__ == "__main__":
    # Load ground truth and model output files
    ground_truth_file = "ground_truth.json"
    model_output_file = "model_output.json"
    
    # Evaluate the results considering both type and line-level detection, and an optional commit list
    commit_list = ["commit_hash1", "commit_hash2"]  # Replace with actual commit hashes or set to None for full evaluation
    metrics = evaluate_with_line_detection(ground_truth_file, model_output_file, commit_list, iou_threshold=0.5, line_tolerance=2)
    
    # Print metrics
    for metric, value in metrics.items():
        if metric != "Per Category Metrics":
            print(f"{metric}: {value}")
        else:
            print("\nPer Category Metrics:")
            for category, cat_metrics in value.items():
                print(f"  {category}: {cat_metrics}")
