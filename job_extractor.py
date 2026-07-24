import uuid
from datetime import datetime
from openai import OpenAI

from schema import JobInfo


client = OpenAI()


def extract_job_info(job_text: str, source_filename: str | None = None) -> JobInfo:
    prompt = f"""
Extract structured job description information.

Rules:
- Do not invent missing information.
- Separate required skills from preferred skills when possible.
- Extract responsibilities and requirements clearly.
- Return only information supported by the job description.

Job description:
{job_text[:20000]}
"""

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=prompt,
        text_format=JobInfo
    )

    job = response.output_parsed

    job.job_id = str(uuid.uuid4())
    job.source_filename = source_filename
    job.created_time = datetime.now().isoformat(timespec="seconds")

    return job