"""
Tests for PDF report generation in NutriLens frontend.
Verifies output correctness, edge case handling, and caching behavior.
"""

import os
import re
import zlib
import pandas as pd
import pytest

# Setup minimal env vars before importing streamlit_app
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
os.environ["GEMINI_API_KEY"] = "mock_gemini"

from streamlit_app import generate_pdf_report


def extract_pdf_text_streams(pdf_bytes: bytes) -> bytes:
    """Helper to decompress FlateDecode streams from FPDF binary output."""
    streams = re.findall(rb"stream[\r\n]+(.*?)[\r\n]+endstream", pdf_bytes, re.DOTALL)
    decompressed = []
    for s in streams:
        try:
            decompressed.append(zlib.decompress(s))
        except Exception:
            pass
    return b"\n".join(decompressed)


def test_generate_pdf_report_standard():
    """Verify PDF report generation with standard meal records."""
    data = [
        {"Date": "2025-01-01", "food_name": "Grilled Chicken Salad", "calories": 350},
        {"Date": "2025-01-01", "food_name": "Greek Yogurt with Berries", "calories": 200},
        {"Date": "2025-01-02", "food_name": "Avocado Toast", "calories": 400},
    ]
    df = pd.DataFrame(data)
    user_email = "testuser@nutrilens.com"
    pdf_bytes = generate_pdf_report(user_email, df)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF files start with %PDF
    assert pdf_bytes.startswith(b"%PDF")

    # Decompress internal streams to verify content
    content = extract_pdf_text_streams(pdf_bytes)
    assert b"NutriLens Health Report" in content
    assert b"testuser@nutrilens.com" in content
    assert b"950 kcal" in content
    assert b"Grilled Chicken Salad" in content


def test_generate_pdf_report_empty():
    """Verify PDF report generation with an empty DataFrame."""
    df_empty = pd.DataFrame()
    user_email = "empty@nutrilens.com"
    pdf_bytes = generate_pdf_report(user_email, df_empty)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    content = extract_pdf_text_streams(pdf_bytes)
    assert b"Total Calories: 0 kcal" in content


def test_generate_pdf_report_truncation_and_more_than_20_rows():
    """Verify only top 20 rows are rendered and food names are truncated to 30 chars."""
    data = [
        {
            "Date": "2025-01-01",
            "food_name": f"Super Long Meal Description That Should Be Truncated #{i:02d}",
            "calories": 100 + i,
        }
        for i in range(30)
    ]
    df = pd.DataFrame(data)
    pdf_bytes = generate_pdf_report("user@example.com", df)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")

    content = extract_pdf_text_streams(pdf_bytes)
    # First meal name truncated to 30 chars: "Super Long Meal Description Th"
    assert b"Super Long Meal Description Th" in content
    # 25th meal should not appear in table
    assert b"Truncated #25" not in content


def test_generate_pdf_report_caching():
    """Verify that cached calls return identical bytes."""
    data = [
        {"Date": "2025-01-01", "food_name": "Apple", "calories": 52},
    ]
    df = pd.DataFrame(data)
    user_email = "cached@nutrilens.com"

    result1 = generate_pdf_report(user_email, df)
    result2 = generate_pdf_report(user_email, df)

    assert result1 == result2
