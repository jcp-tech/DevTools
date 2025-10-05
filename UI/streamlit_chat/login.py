"""Deprecated entry point kept for backward compatibility."""
import streamlit as st

from app import main

st.warning("The login flow has moved into app.py. Redirecting you there…")
main()
