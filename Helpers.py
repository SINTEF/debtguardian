import re
import textwrap
import logging
import os

def is_source_code(filename):
    logging.debug("Checking if %s is a source code file", filename)

    """
    Determine if a given filename corresponds to a source code file.

    This function checks the file extension against a predefined list of common
    source code file extensions. It's a simple way to guess if a file is a source code file.

    Args:
    - filename (str): The name of the file to check.

    Returns:
    - bool: True if the file extension matches a known source code extension, False otherwise.
    """

    try:
        # A basic list of source code extensions; can be expanded based on requirements
        source_code_extensions = [
            '.c', '.cpp', '.h', '.java', '.py', '.js', '.php',
            '.cs', '.rb', '.go', '.rs', '.ts', '.m', '.swift',
            '.f', '.f90', '.perl', '.sh', '.bash'
        ]

        # Extract the extension and check if it's in our list
        _, ext = os.path.splitext(filename)
        result = ext in source_code_extensions
        logging.debug("File %s is source code: %s", filename, result)
        return result
    except Exception as e:
        logging.error("Error in is_source_code for file %s: %s", filename, str(e))
        raise


def print_bar(length=200, char='█'):
    """
    Print a horizontal bar with a given length and character.

    :param length: Length of the bar to be printed
    :param char: Character to use for printing the bar
    """
    print(char * length)


def wrap_text(text, width=200):
    """
    Wrap the given text to the specified width.

    :param text: Text to wrap
    :param width: Width at which to wrap the text
    :return: Wrapped text
    """
    return textwrap.fill(text, width)


def url_to_filename(url):
    """
    converts the GitHub url to a valid file name
    Args:
        url: Url to the GitHub repository

    Returns: a sanitized file name

    """

    filename = re.sub(r'[\\/*?"<>|:]', '_', url)
    return filename


def enumerate_file(code_content: str):
    """
    The function will enumerate the file containing code

    This will help the LLM in determining which line contains technical debt
    Args:
        code_content: The code content that needs to be enumerated

    Returns: The enumerated file containing code.

    """
    lines = code_content.split('\n')
    enumerated_string = ""

    for index, line in enumerate(lines, start=1):
        enumerated_string += f"{index}. {line}\n"

    enumerated_string = enumerated_string.rstrip('\n')
    return enumerated_string


def extract_json(response: str):
    """
    The function will extract the json response that is given from the language model
    :param response: from the large language model
    :return: only the JSON response from the large language model
    """
    start = response.find('{')
    end = response.rfind('}') + 1
    json_data = response[start:end]
    return json_data

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

def print_bar():
    """
    Function that will print a process bar
    :return:
    """
    print("=" * 40)


def print_file_analysis_start(commit_hash):
    """
    Function that will print a bar and what file that it is analysing.

    :param commit_hash: of the commit that is being analyzed
    :return:
    """
    print_bar()
    print(f"\nAnalyzing {commit_hash}\n")
