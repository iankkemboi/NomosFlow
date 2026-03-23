from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.churn_score import ChurnScore
from app.models.customer import Customer
from app.models.partner import Partner
from app.schemas.churn_score import ChurnScoreResponse, ChurnScoreWithCustomer
from app.services.churn_scorer import score_customer, simple_score_customer
from app.services.gemini_quota import GeminiQuotaExceededError, quota_status

router = APIRouter()


@router.get("/scores", response_model=List[ChurnScoreWithCustomer])
def get_churn_scores(
    risk_level: Optional[str] = Query(None),
    partner_id: Optional[UUID] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    subq = (
        db.query(
            ChurnScore.customer_id,
            ChurnScore.id,
        )
        .distinct(ChurnScore.customer_id)
        .order_by(ChurnScore.customer_id, ChurnScore.scored_at.desc())
        .subquery()
    )

    query = (
        db.query(ChurnScore, Customer, Partner)
        .join(subq, ChurnScore.id == subq.c.id)
        .join(Customer, ChurnScore.customer_id == Customer.id)
        .join(Partner, Customer.partner_id == Partner.id)
    )
    if risk_level:
        query = query.filter(ChurnScore.risk_level == risk_level)
    if partner_id:
        query = query.filter(Customer.partner_id == partner_id)

    rows = query.order_by(ChurnScore.score.desc()).limit(limit).all()
    result = []
    for score, customer, partner in rows:
        data = ChurnScoreWithCustomer.model_validate(score)
        data.customer_name = customer.name
        data.partner_name = partner.name
        data.device_type = customer.device_type
        data.contract_status = customer.contract_status
        result.append(data)
    return result


@router.post("/score-all")
def score_all_customers(
    use_ai: bool = Query(False, description="Use Gemini AI (slower, uses quota)"),
    partner_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Customer)
    if partner_id:
        query = query.filter(Customer.partner_id == partner_id)
    customers = query.all()

    scored = 0
    errors = []
    for customer in customers:
        try:
            if use_ai:
                score_customer(str(customer.id), db)
            else:
                simple_score_customer(customer, db)
            scored += 1
        except GeminiQuotaExceededError as exc:
            # Return partial results + quota state instead of aborting with a raw 429
            return JSONResponse(
                status_code=429,
                content={
                    "error": "ai_quota_exceeded",
                    "message": str(exc),
                    "status": "partial",
                    "scored": scored,
                    "errors": errors,
                    "quota": quota_status(),
                },
            )
        except Exception as e:
            errors.append({"customer_id": str(customer.id), "error": str(e)})

    return {"status": "completed", "scored": scored, "errors": errors}


@router.post("/score/{customer_id}", response_model=ChurnScoreResponse)
def score_single_customer(
    customer_id: UUID,
    use_ai: bool = Query(False),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if use_ai:
        return score_customer(str(customer_id), db)
    return simple_score_customer(customer, db)
