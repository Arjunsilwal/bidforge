"""
Estimate Exporter Service: Formats and exports estimates to CSV and Excel.
"""
import io
from typing import List
import pandas as pd
from api.models import EstimateModel, LineItemModel


class EstimateExporterService:
    """Exports structured estimates into client-ready Excel and CSV files."""

    @staticmethod
    def to_dataframe(estimate: EstimateModel, line_items: List[LineItemModel]) -> pd.DataFrame:
        """Convert line items to clean presentation DataFrame."""
        rows = []
        for item in line_items:
            unit_price = item.overridden_unit_price if item.is_overridden else item.unit_price_expected
            ext_cost = round(unit_price * item.quantity, 2)

            rows.append({
                "Item Code": item.item_code,
                "Description": item.item_description,
                "Spec Section": item.matched_spec_section or "",
                "Quantity": item.quantity,
                "UOM": item.unit_of_measure,
                "Low Price ($)": item.unit_price_low,
                "Unit Price ($)": unit_price,
                "High Price ($)": item.unit_price_high,
                "Extended Total ($)": ext_cost,
                "Is Overridden": "Yes" if item.is_overridden else "No",
                "Justification": item.justification_text or "",
            })

        return pd.DataFrame(rows)

    def to_csv_bytes(self, estimate: EstimateModel, line_items: List[LineItemModel]) -> bytes:
        """Export as UTF-8 CSV bytes."""
        df = self.to_dataframe(estimate, line_items)
        return df.to_csv(index=False).encode("utf-8")

    def to_excel_bytes(self, estimate: EstimateModel, line_items: List[LineItemModel]) -> bytes:
        """Export as styled Excel workbook (.xlsx) bytes."""
        df = self.to_dataframe(estimate, line_items)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Draft Estimate", index=False)

        return output.getvalue()
