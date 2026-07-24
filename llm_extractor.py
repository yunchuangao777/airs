from openai import OpenAI
import openai
from schema import CVInfo
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_cv_info(cv_text: str) -> CVInfo:

    prompt = f"""
        Extract candidate information from this CV.

        Important:
        - The candidate name is usually near the top of the CV.
        - Do not leave name empty if a personal name appears near the title or contact section.
        - Do not invent missing information.

        CV text:
        {cv_text[:20000]}
    """

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=prompt,
        text_format=CVInfo
    )

    return response.output_parsed