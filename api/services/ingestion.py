"""
Ingestion Service: Parsing Spec Documents (PDF/Text) and BOQ (CSV/Excel).
"""
import io
import re
from typing import List, Tuple
import pandas as pd
from data.schemas import CanonicalLineItem
from data.dot_parser import DOTBidTabParser


class IngestionService:
    """Service to parse raw uploaded spec and BOQ files into canonical structures."""

    def __init__(self):
        self.parser = DOTBidTabParser()

    def parse_boq(self, file_bytes: bytes, filename: str) -> List[CanonicalLineItem]:
        """Parse uploaded CSV or Excel file into a list of CanonicalLineItems."""
        buffer = io.BytesIO(file_bytes)
        if filename.endswith(".csv"):
            df = pd.read_csv(buffer)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(buffer)
        else:
            raise ValueError("Only CSV or Excel (.xlsx, .xls) BOQ files are supported.")

        standardized = self.parser._standardize_columns(df)
        clean_df = self.parser._clean_data(standardized)

        line_items: List[CanonicalLineItem] = []
        for idx, row in clean_df.iterrows():
            item_id = str(row.get("item_id", f"LINE-{idx+1:03d}"))
            line_items.append(
                CanonicalLineItem(
                    item_id=item_id,
                    item_code=str(row["item_code"]),
                    item_description=str(row.get("item_description", "No description provided")),
                    unit_of_measure=str(row.get("unit_of_measure", "EA")),
                    quantity=float(row["quantity"]),
                    spec_section=str(row.get("spec_section", "")) if pd.notna(row.get("spec_section")) else None,
                )
            )

        return line_items

    def parse_spec_document(self, file_bytes: bytes, filename: str) -> List[str]:
        """
        Extract text chunks from uploaded Spec PDF or Text file.
        Uses pdfplumber or pypdf if available, with graceful plaintext fallback.
        """
        if filename.endswith(".pdf"):
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            except Exception:
                # Fallback to plain string decode or pypdf
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
                except Exception:
                    full_text = file_bytes.decode("utf-8", errors="ignore")
        else:
            full_text = file_bytes.decode("utf-8", errors="ignore")

        # Split text into logical section chunks
        chunks = self._chunk_spec_text(full_text)
        return chunks

    def _chunk_spec_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text by Section headers or paragraph blocks."""
        sections = re.split(r"(SECTION\s+\d+.*)", text, flags=re.IGNORECASE)
        chunks = []
        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                chunk = sections[i] + "\n" + (sections[i + 1] if i + 1 < len(sections) else "")
                chunks.append(chunk.strip())
        else:
            # Fallback paragraph chunking
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            chunks = paragraphs if paragraphs else [text[:max_chunk_size]]
        return chunks
