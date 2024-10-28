import logging
import os
from settings import ROOT_DIR
import guardrails as gd

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
        logging.info('The prompt: \n' + prompt)
        schema_path = os.path.join(ROOT_DIR, 'technical_schema', 'Few-shot_p3_Java.xml')
        guard = gd.Guard.from_rail(schema_path)
        logging.debug("Guard object created successfully")
        return guard
    except Exception as e:
        logging.error("Error creating guard object: %s", str(e))
        raise





