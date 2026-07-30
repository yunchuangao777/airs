from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Experience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class Education(BaseModel):
    model_config = ConfigDict(extra="forbid")

    school: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[str] = None


class CVInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str | None = None
    cv_hash: str | None = None

    source_filename: str | None = None
    source_filepath: str | None = None
    upload_time: str | None = None
    raw_text: str | None = None

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None

    skills: list[str] = Field(
        default_factory=list
    )

    education: list[Education] = Field(
        default_factory=list
    )

    work_experience: list[Experience] = Field(
        default_factory=list
    )

    total_years_experience: float | None = None


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

class CandidateStatus(str, Enum):
    NONE = "none"
    APPLIED = "applied"
    REVIEW = "review"
    INTERVIEW = "interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class StatusHistoryItem(BaseModel):
    status: CandidateStatus
    changed_time: str
    note: Optional[str] = None


class ApplicationRecord(BaseModel):
    application_id: str

    candidate_id: str
    job_id: str

    status: CandidateStatus = CandidateStatus.NONE

    created_time: str
    updated_time: str

    notes: Optional[str] = None

    status_history: list[StatusHistoryItem] = Field(
        default_factory=list
    )    

class MatchResult(BaseModel):
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None

    candidate_name: Optional[str] = None
    job_title: Optional[str] = None

    match_method: str = "ai"
    score: float = 0.0

    skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    location_score: Optional[float] = None

    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)

    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)

    recommendation: Optional[str] = None