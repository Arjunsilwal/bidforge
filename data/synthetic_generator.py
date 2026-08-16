"""
Synthetic Bid Package Generator.
Generates realistic sample DOT / Civil Construction bill of quantities (CSV/Excel)
and paired spec documents for end-to-end testing, training baselines, and local demos.
"""

import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from data.schemas import BidPackage, CanonicalLineItem


class SyntheticBidPackageGenerator:
    """Generator for synthetic bid packages containing specifications and BOQ files."""

    # Heterogeneous template rows (strings, floats, and a quantity-range tuple), so the
    # value type is deliberately Any rather than a narrower union.
    SAMPLE_CATALOG: list[dict[str, Any]] = [
        {
            "code": "02010",
            "desc": "Mobilization and Demobilization",
            "uom": "LS",
            "base_price": 45000.0,
            "qty_range": (1, 1),
            "category": "General",
            "spec": "SECTION 00210 - MOBILIZATION",
        },
        {
            "code": "02100",
            "desc": "Clearing and Grubbing",
            "uom": "ACRE",
            "base_price": 4200.0,
            "qty_range": (2.0, 15.0),
            "category": "Earthwork",
            "spec": "SECTION 00320 - CLEARING AND GRUBBING",
        },
        {
            "code": "02200",
            "desc": "Roadway Excavation Unclassified",
            "uom": "CY",
            "base_price": 28.50,
            "qty_range": (500, 12000),
            "category": "Earthwork",
            "spec": "SECTION 00330 - EARTHWORK & EXCAVATION",
        },
        {
            "code": "02250",
            "desc": "Structure Excavation",
            "uom": "CY",
            "base_price": 45.00,
            "qty_range": (100, 2500),
            "category": "Earthwork",
            "spec": "SECTION 00330 - EARTHWORK & EXCAVATION",
        },
        {
            "code": "03050",
            "desc": "Aggregate Base Course 3/4-Inch Dense",
            "uom": "TON",
            "base_price": 32.00,
            "qty_range": (800, 15000),
            "category": "Base Course",
            "spec": "SECTION 00640 - AGGREGATE BASES",
        },
        {
            "code": "04010",
            "desc": "Asphalt Concrete Pavement Level 3 Superpave",
            "uom": "TON",
            "base_price": 95.00,
            "qty_range": (400, 8000),
            "category": "Paving",
            "spec": "SECTION 00745 - ASPHALT CONCRETE PAVEMENT",
        },
        {
            "code": "05020",
            "desc": "Structural Concrete Class 4000",
            "uom": "CY",
            "base_price": 850.00,
            "qty_range": (50, 600),
            "category": "Structures",
            "spec": "SECTION 00540 - REINFORCED CONCRETE",
        },
        {
            "code": "05100",
            "desc": "Reinforcing Steel Deformed Bars Grade 60",
            "uom": "LB",
            "base_price": 1.75,
            "qty_range": (5000, 80000),
            "category": "Structures",
            "spec": "SECTION 00530 - STEEL REINFORCEMENT",
        },
        {
            "code": "06010",
            "desc": "18-Inch Storm Sewer Pipe RCP Class IV",
            "uom": "LF",
            "base_price": 115.00,
            "qty_range": (200, 3000),
            "category": "Drainage",
            "spec": "SECTION 00445 - DRAINAGE PIPES & STRUCTURES",
        },
        {
            "code": "07010",
            "desc": "Guardrail Type 3-W Beam Galvanized",
            "uom": "LF",
            "base_price": 42.00,
            "qty_range": (300, 4500),
            "category": "Safety",
            "spec": "SECTION 00810 - GUARDRAILS",
        },
        {
            "code": "08010",
            "desc": "Thermoplastic Pavement Markings White 4-Inch",
            "uom": "LF",
            "base_price": 1.25,
            "qty_range": (1000, 25000),
            "category": "Traffic",
            "spec": "SECTION 00860 - PAVEMENT MARKINGS",
        },
        {
            "code": "09010",
            "desc": "Temporary Traffic Control and Flagging",
            "uom": "HR",
            "base_price": 68.00,
            "qty_range": (150, 1200),
            "category": "Traffic",
            "spec": "SECTION 00225 - TEMPORARY TRAFFIC CONTROL",
        },
    ]

    REGIONS = [
        "District 1 (Northwest)",
        "District 2 (Central)",
        "District 3 (Southwest)",
        "District 4 (Eastern)",
    ]

    def generate_bid_package(
        self,
        project_name: str = "US-101 Highway Realignment & Drainage Upgrade",
        item_count: int = 8,
        region: str | None = None,
        letting_date: date | None = None,
    ) -> BidPackage:
        """Create a randomized synthetic bid package."""
        if letting_date is None:
            letting_date = date.today() + timedelta(days=30)
        if region is None:
            region = random.choice(self.REGIONS)

        selected_templates = random.sample(
            self.SAMPLE_CATALOG, min(item_count, len(self.SAMPLE_CATALOG))
        )
        line_items: list[CanonicalLineItem] = []
        spec_chunks: list[str] = []

        for i, tmpl in enumerate(selected_templates, start=1):
            qty_min, qty_max = tmpl["qty_range"]
            qty = round(random.uniform(qty_min, qty_max), 2)
            if tmpl["uom"] in ["LS", "EA"]:
                qty = float(int(qty))

            item = CanonicalLineItem(
                item_id=f"ITEM-{i:03d}",
                item_code=tmpl["code"],
                item_description=tmpl["desc"],
                unit_of_measure=tmpl["uom"],
                quantity=qty,
                spec_section=tmpl["spec"],
                category=tmpl["category"],
            )
            line_items.append(item)

            chunk_text = (
                f"{tmpl['spec']}\n"
                f"Description: Execution and quality standards for {tmpl['desc']} (Code {tmpl['code']}). "
                f"All material must comply with State Standard Specifications for Road, Bridge, and Municipal Construction. "
                f"Measurement and payment shall be by {tmpl['uom']} installed and accepted in place."
            )
            spec_chunks.append(chunk_text)

        return BidPackage(
            package_id=f"PKG-{random.randint(10000, 99999)}",
            project_name=project_name,
            location_region=region,
            letting_target_date=letting_date,
            line_items=line_items,
            spec_chunks=spec_chunks,
        )

    def export_package_files(self, package: BidPackage, output_dir: Path) -> dict[str, Path]:
        """Save synthetic package as CSV and Text/Spec files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export BOQ to CSV
        boq_data = [
            {
                "item_id": item.item_id,
                "item_code": item.item_code,
                "description": item.item_description,
                "unit": item.unit_of_measure,
                "quantity": item.quantity,
                "spec_section": item.spec_section,
            }
            for item in package.line_items
        ]
        boq_df = pd.DataFrame(boq_data)
        csv_path = output_dir / f"{package.package_id}_boq.csv"
        boq_df.to_csv(csv_path, index=False)

        # Export Spec text
        spec_path = output_dir / f"{package.package_id}_specs.txt"
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(f"PROJECT SPECIFICATIONS: {package.project_name}\n")
            f.write(
                f"Region: {package.location_region} | Letting Date: {package.letting_target_date}\n\n"
            )
            for chunk in package.spec_chunks:
                f.write(chunk + "\n\n" + "-" * 60 + "\n\n")

        return {"boq_csv": csv_path, "specs_txt": spec_path}
