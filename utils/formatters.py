def format_education(education: list[dict]) -> str:
    if not education:
        return ""

    items: list[str] = []

    for item in education:
        degree = item.get("degree") or ""
        major = item.get("major") or ""
        school = item.get("school") or ""
        graduation_year = item.get("graduation_year") or ""

        qualification = " ".join(
            part for part in [degree, major] if part
        )

        text = " | ".join(
            part
            for part in [qualification, school, graduation_year]
            if part
        )

        if text:
            items.append(text)

    return "; ".join(items)


def format_skills(skills: list[str], max_items: int = 8) -> str:
    if not skills:
        return ""

    visible_skills = skills[:max_items]
    result = ", ".join(visible_skills)

    remaining = len(skills) - max_items
    if remaining > 0:
        result += f" (+{remaining} more)"

    return result


def format_experience_years(value) -> str:
    if value is None:
        return ""

    try:
        number = float(value)
        return str(int(number)) if number.is_integer() else f"{number:.1f}"
    except (TypeError, ValueError):
        return str(value)
