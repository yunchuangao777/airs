from io import BytesIO
from pathlib import Path
from typing import Iterable

import pandas as pd

from utils.paths import UPLOAD_DIR


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
