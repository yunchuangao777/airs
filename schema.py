from pydantic import BaseModel, Field
from typing import List, Optional

class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class Education(BaseModel):
    school: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[str] = None


class CVInfo(BaseModel):

    candidate_id: str
    source_filename: Optional[str] = None
    upload_time: Optional[str] = None

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

    summary: Optional[str] = None

    skills: List[str] = Field(default_factory=list)

    education: List[Education] = Field(default_factory=list)

    work_experience: List[Experience] = Field(default_factory=list)

    total_years_experience: Optional[float] = None

    raw_text: Optional[str] = None
    source_filepath: Optional[str] = None

class JobInfo(BaseModel):
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

    summary: Optional[str] = None

    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)

    required_experience_years: Optional[float] = None
    education_requirements: List[str] = Field(default_factory=list)

    responsibilities: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)

    source_filename: Optional[str] = None
    created_time: Optional[str] = None

class MatchResult(BaseModel):
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None

    candidate_name: Optional[str] = None
    job_title: Optional[str] = None

    score: float = 0.0

    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)

    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)

    recommendation: Optional[str] = None
    
class InterviewPrep(BaseModel):
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None

    candidate_name: Optional[str] = None
    job_title: Optional[str] = None

    candidate_summary: Optional[str] = None
    role_fit_summary: Optional[str] = None

    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)
    interview_focus_areas: List[str] = Field(default_factory=list)

    