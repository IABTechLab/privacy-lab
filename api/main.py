"""
FastAPI REST API for Privacy Lab workflows.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import workflows

app = FastAPI(
    title="Privacy Lab API",
    description="REST API for privacy-enhancing technology workflows in digital advertising",
    version="1.0.0"
)

# Enable CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class Event(BaseModel):
    space_id: int
    email: str
    event_type: str
    campaign: str
    region: str
    opt_out: bool


class Conversion(BaseModel):
    space_id: int
    email: str
    event_type: str


class KAnonymityRequest(BaseModel):
    events: Optional[List[Event]] = None
    conversions: Optional[List[Conversion]] = None
    k: int = Field(default=10, ge=1, le=100, description="k-anonymity parameter")
    supp_level: int = Field(default=50, ge=0, le=100, description="Suppression level")
    use_sample_data: bool = Field(default=True, description="Use generated sample data")


class DifferentialPrivacyRequest(BaseModel):
    events: Optional[List[Event]] = None
    conversions: Optional[List[Conversion]] = None
    epsilon: float = Field(default=1.0, ge=0.1, le=10.0, description="Privacy loss parameter")
    split_evenly_over: int = Field(default=6, ge=1, le=20, description="Number of queries")
    use_sample_data: bool = Field(default=True, description="Use generated sample data")


class HomomorphicEncryptionRequest(BaseModel):
    events: Optional[List[Event]] = None
    conversions: Optional[List[Conversion]] = None
    use_sample_data: bool = Field(default=True, description="Use generated sample data")


class SampleDataRequest(BaseModel):
    num_events: int = Field(default=5000, ge=100, le=10000)
    num_conversions: int = Field(default=1000, ge=50, le=5000)
    seed: int = Field(default=123, ge=1)


# Helper function to convert request data to internal format
def convert_events(events: List[Event]):
    return [
        [e.space_id, e.email, e.event_type, e.campaign, e.region, e.opt_out]
        for e in events
    ]


def convert_conversions(conversions: List[Conversion]):
    return [
        [c.space_id, c.email, c.event_type]
        for c in conversions
    ]


@app.get("/")
def read_root():
    return {
        "message": "Privacy Lab API",
        "version": "1.0.0",
        "endpoints": {
            "k_anonymity": "/api/k-anonymity",
            "differential_privacy": "/api/differential-privacy",
            "homomorphic_encryption": "/api/homomorphic-encryption",
            "sample_data": "/api/sample-data"
        }
    }


@app.post("/api/sample-data")
def generate_sample_data(request: SampleDataRequest):
    """Generate sample engagement events and conversion data."""
    try:
        events, conversions, campaigns = workflows.generate_sample_data(
            num_events=request.num_events,
            num_conversions=request.num_conversions,
            seed=request.seed
        )

        return {
            "events": [
                {
                    "space_id": e[0],
                    "email": e[1],
                    "event_type": e[2],
                    "campaign": e[3],
                    "region": e[4],
                    "opt_out": e[5]
                }
                for e in events[:100]  # Limit to first 100 for response size
            ],
            "conversions": [
                {
                    "space_id": c[0],
                    "email": c[1],
                    "event_type": c[2]
                }
                for c in conversions[:100]  # Limit to first 100
            ],
            "metadata": {
                "total_events": len(events),
                "total_conversions": len(conversions),
                "campaigns": campaigns
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/k-anonymity")
def k_anonymity(request: KAnonymityRequest):
    """
    Apply k-anonymity to conversion data.

    Returns anonymized dataset where each record is indistinguishable
    from at least k-1 other records.
    """
    try:
        if request.use_sample_data:
            events, conversions, campaigns = workflows.generate_sample_data()
        else:
            if not request.events or not request.conversions:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide events and conversions or set use_sample_data=true"
                )
            events = convert_events(request.events)
            conversions = convert_conversions(request.conversions)

        result = workflows.k_anonymity_workflow(
            events,
            conversions,
            k=request.k,
            supp_level=request.supp_level
        )

        return {
            "parameters": {
                "k": request.k,
                "suppression_level": request.supp_level
            },
            "result": result,
            "metadata": {
                "total_records": len(result),
                "description": f"Dataset anonymized with k={request.k}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/differential-privacy")
def differential_privacy(request: DifferentialPrivacyRequest):
    """
    Apply differential privacy to conversion aggregates.

    Returns both non-private and differentially private counts
    for comparison.
    """
    try:
        if request.use_sample_data:
            events, conversions, campaigns = workflows.generate_sample_data()
        else:
            if not request.events or not request.conversions:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide events and conversions or set use_sample_data=true"
                )
            events = convert_events(request.events)
            conversions = convert_conversions(request.conversions)

        result = workflows.differential_privacy_workflow(
            events,
            conversions,
            epsilon=request.epsilon,
            split_evenly_over=request.split_evenly_over
        )

        return {
            "parameters": {
                "epsilon": request.epsilon,
                "split_evenly_over": request.split_evenly_over
            },
            "result": result,
            "metadata": {
                "description": f"Differentially private counts with ε={request.epsilon}",
                "privacy_guarantee": "Output satisfies ε-differential privacy"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/homomorphic-encryption")
def homomorphic_encryption(request: HomomorphicEncryptionRequest):
    """
    Apply homomorphic encryption to conversion data.

    Returns decrypted purchase counts computed on encrypted data.
    """
    try:
        if request.use_sample_data:
            events, conversions, campaigns = workflows.generate_sample_data()
        else:
            if not request.events or not request.conversions:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide events and conversions or set use_sample_data=true"
                )
            events = convert_events(request.events)
            conversions = convert_conversions(request.conversions)

        result = workflows.homomorphic_encryption_workflow(events, conversions)

        return {
            "result": result,
            "metadata": {
                "description": "Purchase counts computed on encrypted conversion data",
                "privacy_guarantee": "Computation performed without decrypting individual records"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
