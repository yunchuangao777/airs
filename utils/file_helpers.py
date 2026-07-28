from io import BytesIO
from pathlib import Path
from typing import Iterable

import pandas as pd

from utils.paths import UPLOAD_DIR
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def save_uploaded_files(uploaded_files: Iterable) -> list[Path]:
    saved_paths: list[Path] = []

    for uploaded_file in uploaded_files:
        file_path = UPLOAD_DIR / uploaded_file.name

        with open(file_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        saved_paths.append(file_path)

    return saved_paths


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Candidates",
        )

    return output.getvalue()

def candidates_to_pdf_bytes(
    candidates: list[dict],
    candidate_rows: dict[str, dict],
) -> bytes:
    """
    Generate a PDF report containing one profile per candidate.

    candidate_rows maps candidate_id to the corresponding filtered
    candidate-table row, including match information.
    """
    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Candidate Report",
        author="In-Recruit",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CandidateTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=19,
        leading=23,
        spaceAfter=12,
    )

    section_style = ParagraphStyle(
        "CandidateSection",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#166534"),
        spaceBefore=10,
        spaceAfter=6,
    )

    normal_style = ParagraphStyle(
        "CandidateNormal",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        spaceAfter=5,
    )

    small_style = ParagraphStyle(
        "CandidateSmall",
        parent=normal_style,
        fontSize=8.5,
        leading=11,
    )

    story = []

    for candidate_index, candidate in enumerate(candidates):
        candidate_id = candidate.get("candidate_id") or ""
        row = candidate_rows.get(candidate_id, {})

        candidate_name = (
            candidate.get("name")
            or "Unknown Candidate"
        )

        story.append(
            Paragraph(
                escape(candidate_name),
                title_style,
            )
        )

        basic_data = [
            [
                Paragraph("<b>Email</b>", small_style),
                Paragraph(
                    escape(
                        str(
                            candidate.get("email")
                            or "Not available"
                        )
                    ),
                    small_style,
                ),
                Paragraph("<b>Phone</b>", small_style),
                Paragraph(
                    escape(
                        str(
                            candidate.get("phone")
                            or "Not available"
                        )
                    ),
                    small_style,
                ),
            ],
            [
                Paragraph("<b>Location</b>", small_style),
                Paragraph(
                    escape(
                        str(
                            candidate.get("location")
                            or "Not available"
                        )
                    ),
                    small_style,
                ),
                Paragraph("<b>Experience</b>", small_style),
                Paragraph(
                    escape(
                        (
                            f"{candidate.get('total_years_experience')} years"
                            if candidate.get(
                                "total_years_experience"
                            )
                            is not None
                            else "Not available"
                        )
                    ),
                    small_style,
                ),
            ],
            [
                Paragraph("<b>Best matched job</b>", small_style),
                Paragraph(
                    escape(
                        str(
                            row.get("Best Matched Job")
                            or "Not matched"
                        )
                    ),
                    small_style,
                ),
                Paragraph("<b>Best score</b>", small_style),
                Paragraph(
                    escape(
                        (
                            str(row.get("Best Match Score"))
                            if row.get("Best Match Score")
                            is not None
                            else "Not available"
                        )
                    ),
                    small_style,
                ),
            ],
        ]

        basic_table = Table(
            basic_data,
            colWidths=[
                29 * mm,
                55 * mm,
                29 * mm,
                55 * mm,
            ],
        )

        basic_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor("#F0FDF4"),
                    ),
                    (
                        "BACKGROUND",
                        (2, 0),
                        (2, -1),
                        colors.HexColor("#F0FDF4"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#D1D5DB"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(basic_table)
        story.append(Spacer(1, 8))

        summary = candidate.get("summary")

        if summary:
            story.append(
                Paragraph(
                    "Professional Summary",
                    section_style,
                )
            )
            story.append(
                Paragraph(
                    escape(str(summary)),
                    normal_style,
                )
            )

        skills = candidate.get("skills", [])

        story.append(
            Paragraph(
                "Skills",
                section_style,
            )
        )

        if skills:
            story.append(
                Paragraph(
                    escape(
                        ", ".join(
                            str(skill)
                            for skill in skills
                        )
                    ),
                    normal_style,
                )
            )
        else:
            story.append(
                Paragraph(
                    "No skills recorded.",
                    normal_style,
                )
            )

        education = candidate.get("education", [])

        story.append(
            Paragraph(
                "Education",
                section_style,
            )
        )

        if education:
            for item in education:
                education_parts = [
                    item.get("degree"),
                    item.get("major"),
                    item.get("school"),
                    item.get("graduation_year"),
                ]

                education_text = " | ".join(
                    str(value)
                    for value in education_parts
                    if value
                )

                story.append(
                    Paragraph(
                        f"- {escape(education_text)}",
                        normal_style,
                    )
                )
        else:
            story.append(
                Paragraph(
                    "No education information recorded.",
                    normal_style,
                )
            )

        work_experience = candidate.get(
            "work_experience",
            [],
        )

        story.append(
            Paragraph(
                "Work Experience",
                section_style,
            )
        )

        if work_experience:
            for experience in work_experience:
                position = (
                    experience.get("title")
                    or "Unknown position"
                )
                company = (
                    experience.get("company")
                    or "Unknown company"
                )

                date_parts = [
                    experience.get("start_date"),
                    experience.get("end_date"),
                ]

                date_text = " to ".join(
                    str(value)
                    for value in date_parts
                    if value
                )

                heading = (
                    f"<b>{escape(str(position))}</b>"
                    f" - {escape(str(company))}"
                )

                if date_text:
                    heading += (
                        f" ({escape(date_text)})"
                    )

                story.append(
                    Paragraph(
                        heading,
                        normal_style,
                    )
                )

                description = experience.get(
                    "description"
                )

                if description:
                    story.append(
                        Paragraph(
                            escape(str(description)),
                            small_style,
                        )
                    )
        else:
            story.append(
                Paragraph(
                    "No work experience recorded.",
                    normal_style,
                )
            )

        matched_jobs = row.get("Matched Jobs")

        if matched_jobs:
            story.append(
                Paragraph(
                    "Job Matching",
                    section_style,
                )
            )
            story.append(
                Paragraph(
                    (
                        "<b>Matched jobs:</b> "
                        f"{escape(str(matched_jobs))}"
                    ),
                    normal_style,
                )
            )

        source_filename = candidate.get(
            "source_filename"
        )

        if source_filename:
            story.append(
                Spacer(1, 8)
            )
            story.append(
                Paragraph(
                    (
                        "<b>Source file:</b> "
                        f"{escape(str(source_filename))}"
                    ),
                    small_style,
                )
            )

        if candidate_index < len(candidates) - 1:
            story.append(PageBreak())

    if not story:
        story.append(
            Paragraph(
                "No candidates were selected.",
                normal_style,
            )
        )

    document.build(story)

    output.seek(0)
    return output.getvalue()