from langchain_community.llms import Ollama
from openai import AzureOpenAI
import logging
import os
import config

def call_with_guardrails_ollama(prompt: str, *args, **kwargs):
    """
    Function that calls the large language model with the provided prompt.
    Args:
        prompt: Includes code changes, and structure from guardrails
        *args:
        **kwargs:

    Returns: The response from the large language model

    """

    logging.info("Calling AI Model with guardrails")
    
    # Get the model type from config
    model_type = config.model_type

    logging.info(f"Getting the model type from config: {model_type}")

    # Initialize Ollama
    ollama = Ollama(base_url='http://localhost:11434', model=model_type)
    # Get the response from Ollama
    response = ollama(prompt, *args, **kwargs)
    logging.debug("Beginning to extract JSON from response")

    # Extract JSON from the response
    return response

def call_with_guardrails_openai(prompt: str, *args, **kwargs):
    """
     Function that calls the open-ai GPT model with the provided prompt.
     Args:
         prompt: Includes code changes, and structure from guardrails
         *args:
         **kwargs:

     Returns: The response from the large language model

     """

    openai = AzureOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        api_version=os.getenv("OPENAI_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    )
    response = openai.chat.completions.create(
        model="gpt-4-32k",
        messages=[{"role": "user", "content": prompt}],
        *args,
        **kwargs
    )
    return response.choices[0].message.content

