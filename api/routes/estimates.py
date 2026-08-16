"""
Estimates API Routes: Upload, Process, Review, Override, and Export.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import EstimateModel, LineItemModel, SpecChunkModel
from api.schemas import (
    EstimateDetailResponse,
    EstimateSummaryResponse,
    LineItemOverrideRequest,
    LineItemResponse,
)
from api.services.estimator import EstimatorService
from api.services.exporter import EstimateExporterService
from api.services.ingestion import IngestionService
from data.synthetic_generator import SyntheticBidPackageGenerator

router = APIRouter(prefix="/api/v1/estimates", tags=["Estimates"])

ingestion_svc = IngestionService()
estimator_svc = EstimatorService()
exporter_svc = EstimateExporterService()
synthetic_gen = SyntheticBidPackageGenerator()


@router.post("/upload", response_model=EstimateDetailResponse)
async def upload_bid_package(
    project_name: str = Form(...),
    location_region: str = Form("Default Region"),
    boq_file: UploadFile = File(..., description="Bill of Quantities CSV or Excel file"),
    spec_file: UploadFile | None = File(None, description="Optional Spec PDF or TXT file"),
    db: Session = Depends(get_db),
):
    """Upload and process a bid package (BOQ + Spec document)."""
    # 1. Parse BOQ
    boq_bytes = await boq_file.read()
    try:
        line_items = ingestion_svc.parse_boq(boq_bytes, boq_file.filename or "boq.csv")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse BOQ file: {e}") from e

    # 2. Parse Spec if provided
    spec_chunks: list[str] = []
    if spec_file is not None:
        spec_bytes = await spec_file.read()
        try:
            spec_chunks = ingestion_svc.parse_spec_document(
                spec_bytes, spec_file.filename or "spec.pdf"
            )
        except Exception as e:
            print(f"Warning: Spec parsing fallback: {e}")

    # 3. Create Estimate record
    estimate_id = f"EST-{uuid.uuid4().hex[:8].upper()}"
    estimate = EstimateModel(
        id=estimate_id,
        project_name=project_name,
        location_region=location_region,
        status="processing",
    )
    db.add(estimate)
    db.flush()

    # Save spec chunks
    for chunk in spec_chunks:
        chunk_model = SpecChunkModel(
            id=f"CHK-{uuid.uuid4().hex[:8].upper()}",
            estimate_id=estimate.id,
            chunk_text=chunk,
        )
        db.add(chunk_model)

    # 4. Generate Predictions & Estimations
    db_items = estimator_svc.generate_estimate(estimate, line_items, spec_chunks)
    for itm in db_items:
        db.add(itm)

    db.commit()
    db.refresh(estimate)

    return _build_detail_response(estimate)


@router.post("/synthetic", response_model=EstimateDetailResponse)
def create_synthetic_estimate(
    project_name: str = "US-101 Highway Realignment & Drainage Demo",
    region: str = "District 1 (Northwest)",
    item_count: int = 8,
    db: Session = Depends(get_db),
):
    """Instant demo endpoint: Generates a realistic synthetic bid package and processes it."""
    pkg = synthetic_gen.generate_bid_package(
        project_name=project_name,
        item_count=item_count,
        region=region,
    )

    estimate_id = f"EST-{uuid.uuid4().hex[:8].upper()}"
    estimate = EstimateModel(
        id=estimate_id,
        project_name=pkg.project_name,
        location_region=pkg.location_region,
        status="processing",
    )
    db.add(estimate)
    db.flush()

    # Save synthetic spec chunks
    for chunk in pkg.spec_chunks:
        db.add(
            SpecChunkModel(
                id=f"CHK-{uuid.uuid4().hex[:8].upper()}", estimate_id=estimate.id, chunk_text=chunk
            )
        )

    # Generate predictions
    db_items = estimator_svc.generate_estimate(estimate, pkg.line_items, pkg.spec_chunks)
    for itm in db_items:
        db.add(itm)

    db.commit()
    db.refresh(estimate)
    return _build_detail_response(estimate)


@router.get("", response_model=list[EstimateSummaryResponse])
def list_estimates(db: Session = Depends(get_db)):
    """List all created estimates."""
    estimates = db.query(EstimateModel).order_by(EstimateModel.created_at.desc()).all()
    return [
        EstimateSummaryResponse(
            id=est.id,
            project_name=est.project_name,
            location_region=est.location_region,
            status=est.status,
            total_cost_low=est.total_cost_low,
            total_cost_expected=est.total_cost_expected,
            total_cost_high=est.total_cost_high,
            line_item_count=len(est.line_items),
            created_at=est.created_at,
            updated_at=est.updated_at,
        )
        for est in estimates
    ]


@router.get("/{estimate_id}", response_model=EstimateDetailResponse)
def get_estimate(estimate_id: str, db: Session = Depends(get_db)):
    """Get full details of an estimate with all line items."""
    estimate = db.query(EstimateModel).filter(EstimateModel.id == estimate_id).first()
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return _build_detail_response(estimate)


@router.patch("/{estimate_id}/line-items/{item_id}", response_model=LineItemResponse)
def override_line_item_price(
    estimate_id: str,
    item_id: str,
    override: LineItemOverrideRequest,
    db: Session = Depends(get_db),
):
    """Human-in-the-loop: Override unit price for an individual line item."""
    item = (
        db.query(LineItemModel)
        .filter(
            LineItemModel.id == item_id,
            LineItemModel.estimate_id == estimate_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")

    item.is_overridden = True
    item.overridden_unit_price = override.overridden_unit_price
    item.extended_cost = round(override.overridden_unit_price * item.quantity, 2)

    # Recalculate estimate total
    estimate = item.estimate
    total_exp = sum(it.effective_unit_price * it.quantity for it in estimate.line_items)
    estimate.total_cost_expected = round(total_exp, 2)

    db.commit()
    db.refresh(item)
    return item


@router.post("/{estimate_id}/approve", response_model=EstimateSummaryResponse)
def approve_estimate(estimate_id: str, db: Session = Depends(get_db)):
    """Mark an estimate as approved."""
    estimate = db.query(EstimateModel).filter(EstimateModel.id == estimate_id).first()
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    estimate.status = "approved"
    db.commit()
    db.refresh(estimate)
    return EstimateSummaryResponse(
        id=estimate.id,
        project_name=estimate.project_name,
        location_region=estimate.location_region,
        status=estimate.status,
        total_cost_low=estimate.total_cost_low,
        total_cost_expected=estimate.total_cost_expected,
        total_cost_high=estimate.total_cost_high,
        line_item_count=len(estimate.line_items),
        created_at=estimate.created_at,
        updated_at=estimate.updated_at,
    )


@router.get("/{estimate_id}/export/csv")
def export_estimate_csv(estimate_id: str, db: Session = Depends(get_db)):
    """Download estimate as CSV file."""
    estimate = db.query(EstimateModel).filter(EstimateModel.id == estimate_id).first()
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")

    csv_data = exporter_svc.to_csv_bytes(estimate, estimate.line_items)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={estimate.id}_estimate.csv"},
    )


@router.get("/{estimate_id}/export/excel")
def export_estimate_excel(estimate_id: str, db: Session = Depends(get_db)):
    """Download estimate as Excel workbook."""
    estimate = db.query(EstimateModel).filter(EstimateModel.id == estimate_id).first()
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")

    excel_data = exporter_svc.to_excel_bytes(estimate, estimate.line_items)
    return Response(
        content=excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={estimate.id}_estimate.xlsx"},
    )


def _build_detail_response(estimate: EstimateModel) -> EstimateDetailResponse:
    """Helper to convert ORM model to Pydantic Detail Response."""
    items = [
        LineItemResponse(
            id=it.id,
            item_code=it.item_code,
            item_description=it.item_description,
            unit_of_measure=it.unit_of_measure,
            quantity=it.quantity,
            unit_price_low=it.unit_price_low,
            unit_price_expected=it.effective_unit_price,
            unit_price_high=it.unit_price_high,
            extended_cost=it.extended_cost,
            is_overridden=it.is_overridden,
            overridden_unit_price=it.overridden_unit_price,
            matched_spec_section=it.matched_spec_section,
            justification_text=it.justification_text,
            comparable_bids=it.comparable_bids or [],
        )
        for it in estimate.line_items
    ]

    return EstimateDetailResponse(
        id=estimate.id,
        project_name=estimate.project_name,
        location_region=estimate.location_region,
        status=estimate.status,
        total_cost_low=estimate.total_cost_low,
        total_cost_expected=estimate.total_cost_expected,
        total_cost_high=estimate.total_cost_high,
        line_item_count=len(items),
        created_at=estimate.created_at,
        updated_at=estimate.updated_at,
        line_items=items,
    )
