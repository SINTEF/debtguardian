import logging
import os
from settings import ROOT_DIR
import guardrails as gd

def createGuard(code_changes, schema):
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
        #logging.info('The prompt: \n' + prompt)
        schema_path = os.path.join(ROOT_DIR, 'technical_schema', schema)
        logging.info("The path of the technical schema:" + str(schema_path))
        guard = gd.Guard.from_rail(schema_path)
        logging.info("Guard object created successfully")
        #logging.info(f"Guard base prompt: {guard.base_prompt}")
        return guard
    except Exception as e:
        logging.error("Error creating guard object: %s", str(e))
        raise





