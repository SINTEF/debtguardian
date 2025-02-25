
import logging
import json
#import config
from .model_interface import call_with_guardrails_ollama
import guardrails as gd

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
    # Get the model type from config
    #model_type = config.model_type
    logging.info("with %s", model_type)
    """
    try:
        call_llm = call_with_guardrails_openai if model_type == 'OPENAI' else call_with_guardrails_ollama
        
        res = guard(
            call_llm,
            prompt_params = {"code_changes": code_changes},
            num_reasks = 5,
            temperature = 0,
        )
        logging.debug("Debt detection completed")
        #logging.info(f"Raw LLM output: {res.raw_llm_output}")
        #logging.info(f"Validated output: {res.validated_output}")
        
        return res.validated_output
    """
    try:
        res = guard(
            lambda prompt, *args, **kwargs: call_with_guardrails_ollama(prompt, model_type=model_type, *args, **kwargs),
            prompt_params={"code_changes": code_changes},
            num_reasks=5,
            temperature=0,
        )
        logging.debug("Debt detection completed")
        
        return res.validated_output

    except Exception as e:
        if "token limit exceeded" in str(e).lower():
            logging.warning("Error: Token limit exceeded in debtDetect")
        else:
            logging.error("Error in debtDetect: %s", str(e))
        raise


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
    #print(json.dumps(debt, indent=4))

    if commit.hash not in debts:
        debts[commit.hash] = []
    debts[commit.hash].append(debt)

    with open(debts_file, 'w') as file:
        logging.info("Saving to Debts JSON...")
        json.dump(debts, file, indent=4)
