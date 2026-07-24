from openai import OpenAI
from schema import MatchResult
import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def match_candidate_to_job(candidate: dict, job: dict) -> MatchResult:
    prompt = f"""
        You are an HR screening assistant.

        Compare the candidate CV information with the job description.

        Scoring rule:
        - Score from 0 to 100.
        - 90-100: excellent match
        - 75-89: strong match
        - 60-74: possible match
        - 40-59: weak match
        - below 40: poor match

        Important:
        - Focus on required skills, responsibilities, experience, education, and industry relevance.
        - Do not invent candidate experience.
        - Missing required skills should reduce score.
        - Explain strengths and concerns clearly.

        Candidate JSON:
        {candidate}

        Job JSON:
        {job}
    """

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=prompt,
        text_format=MatchResult
    )

    result = response.output_parsed

    result.candidate_id = candidate.get("candidate_id")
    result.job_id = job.get("job_id")
    result.candidate_name = candidate.get("name")
    result.job_title = job.get("job_title")

    return result