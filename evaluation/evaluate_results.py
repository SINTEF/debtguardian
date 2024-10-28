import logging
from pydriller import Repository
from loggers import log_metrics_to_neptune
from evaluation import evaluate_file_level_detection, evaluate_type_classification, evaluate_with_line_detection

def evaluate_results(mode, ground_truth, model_output, repo_url=None, commit_list=None, commit_hash=None, begin_commit=None, end_commit=None, run=None, iou_threshold=0.5, log_to_neptune=True):
    """
    General evaluation function that calls different evaluation methods based on the mode.

    Parameters:
    - mode: str, the type of evaluation to perform ("file_level", "multi_class", "line_level")
    - ground_truth: path, the ground truth data
    - model_output: path, the model output data
    - commit_list: list, optional, list of commit hashes for evaluation
    - commit_hash: str, optional, single commit hash to filter the evaluation
    - iou_threshold: float, optional, IoU threshold for line-level evaluation (default: 0.5)
    - run: Neptune run object, optional, if logging metrics to Neptune

    Returns:
    - dict: Aggregated evaluation results if commit_list is provided, else results for a single commit or range.
    """
    logging.info("Evaluation started.")
    logging.info("Mode: %s", mode)

    # Case 1: Single commit 
    if commit_hash:
        logging.info(f"Evaluating single commit: {commit_hash}")
        metrics = evaluate_single_commit(mode, ground_truth, model_output, commit_hash, iou_threshold)
        # Log metrics
        for metric, value in metrics.items():
            logging.info(f"{metric}: {value}")
        # Log results
        if run is not None and log_to_neptune:
            log_metrics_to_neptune(run, mode, metrics)

        return metrics

    # Case 2: List of commits
    elif commit_list:
        logging.info("Evaluating list of commits.")
        return evaluate_commit_list(mode, ground_truth, model_output, commit_list, run, iou_threshold, log_to_neptune)

    # Case 3: Commit range (begin_commit to end_commit)
    elif begin_commit and end_commit and repo_url:
        logging.info(f"Evaluating commit range: {begin_commit} to {end_commit}")

        # Use PyDriller to traverse commits in the specified range
        commit_range = []
        for commit in Repository(repo_url, from_commit=begin_commit, to_commit=end_commit).traverse_commits():
            commit_range.append(commit.hash)

        if not commit_range:
            raise ValueError(f"No commits found in the range from {begin_commit} to {end_commit}")

        # Evaluate the commits in the range
        return evaluate_commit_list(mode, ground_truth, model_output, commit_range, run, iou_threshold, log_to_neptune)
    else:
        raise ValueError("Please provide a valid commit, commit_list, or a commit range (begin_commit, end_commit).")


def evaluate_single_commit(mode, ground_truth, model_output, commit_hash, iou_threshold):
    """
    Helper function to evaluate a single commit.
    """
    if mode == "file_level":
        return evaluate_file_level_detection(ground_truth, model_output, commit_hash)
    elif mode == "multi_class":
        return evaluate_type_classification(ground_truth, model_output, commit_hash)
    elif mode == "line_level":
        return evaluate_with_line_detection(ground_truth, model_output, commit_hash, iou_threshold)
    else:
        raise ValueError("Invalid mode. Choose from 'file_level', 'multi_class', or 'line_level'.")


def evaluate_commit_list(mode, ground_truth, model_output, commit_list, run, iou_threshold, log_to_neptune):
    """
    Helper function to evaluate a list of commits.
    """
    aggregated_metrics = {}
    sum_metrics = {'TP': 0, 'FP': 0, 'FN': 0}

    # Loop through each commit and accumulate metrics
    for commit in commit_list:
        logging.info(f"Evaluating commit: {commit}")
        metrics = evaluate_single_commit(mode, ground_truth, model_output, commit, iou_threshold)

        # Log metrics for the current commit
        for metric, value in metrics.items():
            logging.info(f"{metric}: {value}")

        # Check if metrics is a dictionary with nested class results (multi-class case)
        if isinstance(value, dict):
            # Aggregate for each class
            for class_name, class_metrics in value.items():
                if class_name not in aggregated_metrics:
                    aggregated_metrics[class_name] = {'TP': 0, 'FP': 0, 'FN': 0}

                aggregated_metrics[class_name]['TP'] += class_metrics.get('TP', 0)
                aggregated_metrics[class_name]['FP'] += class_metrics.get('FP', 0)
                aggregated_metrics[class_name]['FN'] += class_metrics.get('FN', 0)

            # Sum TP, FP, FN for the whole commit list (if multi-class, sum by each class)
            for class_metrics in value.values():
                sum_metrics['TP'] += class_metrics.get('TP', 0)
                sum_metrics['FP'] += class_metrics.get('FP', 0)
                sum_metrics['FN'] += class_metrics.get('FN', 0)

        else:
            # Scalar metrics (like in file-level mode)
            for key, value in metrics.items():
                aggregated_metrics[key] = aggregated_metrics.get(key, 0) + value

            # Sum TP, FP, FN for the whole commit list
            sum_metrics['TP'] += metrics.get('TP', 0)
            sum_metrics['FP'] += metrics.get('FP', 0)
            sum_metrics['FN'] += metrics.get('FN', 0)

        # Log individual commit metrics to Neptune (optional)
        if run is not None and log_to_neptune:
            log_metrics_to_neptune(run, f"{mode}/commit/{commit}", metrics)

    # Calculate average for non-sum metrics
    num_commits = len(commit_list)
    for key in aggregated_metrics:
        if key not in sum_metrics:  # Only average metrics that are not TP, FP, FN
            aggregated_metrics[key] /= num_commits

    # Combine summed metrics into the final aggregated results
    aggregated_metrics.update(sum_metrics)

    # Log aggregated results to Neptune
    if run is not None and log_to_neptune:
        log_metrics_to_neptune(run, f"{mode}_aggregated", aggregated_metrics)

    logging.info("Aggregated metrics calculated for commit list or range.")
    return aggregated_metrics
