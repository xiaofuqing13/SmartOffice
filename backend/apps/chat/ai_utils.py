import yaml
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

def summarize_text_with_langchain(text_to_summarize):
    """
    Summarizes the given text using Langchain and OpenAI with LCEL.

    Args:
        text_to_summarize (str): The text to be summarized.

    Returns:
        str: The summarized text.
    """
    # Load AI settings from setting.yaml
    setting_path = os.path.join(os.path.dirname(__file__), '..', '..', 'setting.yaml')
    with open(setting_path, 'r', encoding='utf-8') as f:
        settings = yaml.safe_load(f)

    ai_settings = settings.get('ai', {})
    api_key = ai_settings.get('openai_api_key')
    api_base = ai_settings.get('openai_api_base')
    model_name = ai_settings.get('model')

    if not all([api_key, api_base, model_name]):
        raise ValueError("AI settings (openai_api_key, openai_api_base, model) are not fully configured in setting.yaml")

    # Initialize the ChatOpenAI model
    llm = ChatOpenAI(
        model_name=model_name,
        openai_api_key=api_key,
        openai_api_base=api_base,
        temperature=0.7,
    )

    # Create a prompt template
    prompt = ChatPromptTemplate.from_template(
        "请根据以下聊天记录，总结出核心要点。总结应简洁、清晰，并涵盖所有重要的讨论点和决定。\n\n聊天记录:\n\"{text}\"\n\n总结:"
    )
    
    # Initialize a simple string output parser
    output_parser = StrOutputParser()

    # Create the chain using LCEL
    chain = prompt | llm | output_parser

    # Invoke the chain to get the summary
    summary = chain.invoke({"text": text_to_summarize})

    return summary 