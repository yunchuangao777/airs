import streamlit as st

from components.candidate_library import render_candidate_library
from components.cv_upload import render_cv_upload


def render_cv_management():
    render_cv_upload()
    st.divider()
    render_candidate_library()
