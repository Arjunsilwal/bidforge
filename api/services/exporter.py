"""
Estimate Exporter Service: Formats and exports estimates to CSV and Excel.
"""

import io

import pandas as pd

from api.models import EstimateModel, LineItemModel

# Leading characters Excel/LibreOffice interpret as the start of a formula. Text that
# reaches the export originates from uploaded BOQ files, so a crafted description like
# "=cmd|..." would otherwise execute when the exported sheet is opened (CSV injection).
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_cell(value: str | None) -> str:
    """Neutralize spreadsheet formula injection by prefixing risky cells with `'`."""
    if not value:
        return ""
    if value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


class EstimateExporterService:
    """Exports structured estimates into client-ready Excel and CSV files."""

    @staticmethod
    def to_dataframe(estimate: EstimateModel, line_items: list[LineItemModel]) -> pd.DataFrame:
        """Convert line items to clean presentation DataFrame."""
        rows = []
        for item in line_items:
            unit_price = item.effective_unit_price
            ext_cost = round(unit_price * item.quantity, 2)

            rows.append(
                {
                    "Item Code": _sanitize_cell(item.item_code),
                    "Description": _sanitize_cell(item.item_description),
                    "Spec Section": _sanitize_cell(item.matched_spec_section),
                    "Quantity": item.quantity,
                    "UOM": _sanitize_cell(item.unit_of_measure),
                    "Low Price ($)": item.unit_price_low,
                    "Unit Price ($)": unit_price,
                    "High Price ($)": item.unit_price_high,
                    "Extended Total ($)": ext_cost,
                    "Is Overridden": "Yes" if item.is_overridden else "No",
                    "Justification": _sanitize_cell(item.justification_text),
                }
            )

        return pd.DataFrame(rows)

    def to_csv_bytes(self, estimate: EstimateModel, line_items: list[LineItemModel]) -> bytes:
        """Export as UTF-8 CSV bytes."""
        df = self.to_dataframe(estimate, line_items)
        csv_text: str = df.to_csv(index=False)
        return csv_text.encode("utf-8")

    def to_excel_bytes(self, estimate: EstimateModel, line_items: list[LineItemModel]) -> bytes:
        """Export as styled Excel workbook (.xlsx) bytes."""
        df = self.to_dataframe(estimate, line_items)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Draft Estimate", index=False)

        return output.getvalue()
