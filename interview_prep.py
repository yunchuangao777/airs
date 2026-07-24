from openai import OpenAI
from schema import InterviewPrep
import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_interview_prep(
    candidate: dict,
    job: dict,
    match_result: dict | None = None
) -> InterviewPrep:

    prompt = f"""
        You are an experienced hiring manager.

        Generate an interview preparation summary based on the candidate profile,
        job description, and optional matching result.

        Return:
        1. Candidate summary
        2. Role-fit summary
        3. Key strengths
        4. Key concerns
        5. Interview focus areas

        Rules:
        - Do not invent experience not shown in the candidate profile.
        - Be concise but useful for an interviewer.
        - Focus on what should be validated during interview.
        - If match_result is provided, use it as supporting evidence, but do not blindly copy it.

        Candidate JSON:
        {candidate}

        Job JSON:
        {job}

        Match Result JSON:
        {match_result}
    """

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=prompt,
        text_format=InterviewPrep
    )

    prep = response.output_parsed

    prep.candidate_id = candidate.get("candidate_id")
    prep.job_id = job.get("job_id")
    prep.candidate_name = candidate.get("name")
    prep.job_title = job.get("job_title")

    return prep