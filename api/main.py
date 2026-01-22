"""
FastAPI REST API for Privacy Lab workflows.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
import workflows
import os
import csv
import io
import zipfile
import jwt
from dotenv import load_dotenv
from gcs_storage import GCSStorage

# Load environment variables from .env file if it exists
# This is useful for local development
# In production (Cloud Functions), environment variables are set in the function configuration
load_dotenv()

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

# JWT Security
security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Decode JWT token and extract user_id from payload.
    No signature verification is performed - token is just decoded.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        str: User ID from JWT token
        
    Raises:
        HTTPException: If token is invalid or missing user_id
    """
    token = credentials.credentials
    
    try:
        # Decode token without verification (verify=False)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Extract user ID from user.id (nested in user object)
        user_obj = payload.get("user", {})
        user_id = user_obj.get("id") if isinstance(user_obj, dict) else None
        
        if not user_id:
            raise HTTPException(status_code=401, detail="user.id not found in token")
        
        return str(user_id)
    except jwt.DecodeError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token decoding failed: {str(e)}")


# Initialize GCS Storage (will raise error if GCS_BUCKET_NAME not set)
try:
    gcs_storage = GCSStorage()
    print(f"[INFO] GCS Storage initialized successfully. Bucket: {gcs_storage.bucket_name}")
except Exception as e:
    print(f"[WARN] GCS Storage initialization failed: {e}")
    print(f"[WARN] File uploads to GCS will be skipped. Set GCS_BUCKET_NAME and ENCRYPTION_KEY environment variables.")
    gcs_storage = None



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

def normalize_events(rows):
    """Convert event rows (list of strings) to correct types."""
    normalized = []
    for r in rows:
        try:
            space_id = int(r[0])
            email = r[1]
            event_type = r[2]
            campaign = r[3]
            region = r[4]
            opt_out = r[5].strip().lower() in ("true", "1", "yes")
            normalized.append([space_id, email, event_type, campaign, region, opt_out])
        except Exception as e:
            print(f"[WARN] Skipping bad event row: {r} ({e})")
    return normalized


def normalize_conversions(rows):
    """Convert conversion rows (list of strings) to correct types."""
    normalized = []
    for r in rows:
        try:
            space_id = int(r[0])
            email = r[1]
            event_type = r[2]
            normalized.append([space_id, email, event_type])
        except Exception as e:
            print(f"[WARN] Skipping bad conversion row: {r} ({e})")
    return normalized

def parse_csv(file: UploadFile):
    """Parse uploaded CSV file into a list of lists (skip header row)."""
    try:
        content = file.file.read().decode("utf-8").strip()
        reader = csv.reader(io.StringIO(content))
        rows = [row for row in reader if any(row)]
        
        if not rows:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        header = rows[0]
        data_rows = rows[1:]  # ✅ skip header

        # Sanity check on column count
        print(f"[DEBUG] Parsed CSV '{file.filename}': header={header}, first_row_len={len(data_rows[0]) if data_rows else 0}")

        return header, data_rows
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

def convert_conversions(conversions: List[Conversion]):
    return [
        [c.space_id, c.email, c.event_type]
        for c in conversions
    ]

def resolve_notebook_path(*subpaths):
    """
    Resolve a path to the notebook directory that works both locally and inside Docker.
    Tries both ./notebook/... and ../notebook/... based on what's available.
    """
    base_dir = os.path.dirname(__file__)

    # Try Docker path first (/app/notebook)
    docker_path = os.path.abspath(os.path.join(base_dir, "notebook", *subpaths))
    if os.path.exists(docker_path):
        return docker_path

    # Fallback for local development (../notebook)
    local_path = os.path.abspath(os.path.join(base_dir, "..", "notebook", *subpaths))
    if os.path.exists(local_path):
        return local_path

    # Return docker-style path if neither exists (for error reporting)
    return docker_path

@app.get("/")
def read_root():
    return {
        "message": "Privacy Lab API",
        "version": "1.0.0",
        "endpoints": {
            "k_anonymity": "/api/k-anonymity",
            "differential_privacy": "/api/differential-privacy",
            "homomorphic_encryption": "/api/homomorphic-encryption",
            "sample_data": "/api/sample-data",
            "sample_data_info": "/api/sample-data-info?method={k-anonymity|differential}",
            "download_templates": "/api/download-templates"
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
async def k_anonymity(
    request: Request,
    events: UploadFile = File(None),
    conversions: UploadFile = File(None),
    k: int = Form(default=10),
    supp_level: int = Form(default=50),
    use_sample_data: bool = Form(default=False),
    user_id: str = Depends(verify_token)
):
    """Apply k-anonymity workflow with CSV uploads."""
    try:
        if use_sample_data:
            events_data, conversions_data, campaigns = workflows.generate_sample_data()
        else:
            if not events or not conversions:
                raise HTTPException(status_code=400, detail="Both events and conversions CSV files are required.")

            # Store files in GCS before processing
            if gcs_storage:
                try:
                    print(f"[INFO] Storing files in GCS for user_id: {user_id}")
                    # Read file content
                    events.file.seek(0)
                    events_content = await events.read()
                    conversions.file.seek(0)
                    conversions_content = await conversions.read()
                    
                    # Upload to GCS
                    events_path = gcs_storage.upload_file(
                        user_id=user_id,
                        file_content=events_content,
                        file_type="events",
                        original_filename=events.filename
                    )
                    print(f"[INFO] Events file uploaded to: {events_path}")
                    
                    conversions_path = gcs_storage.upload_file(
                        user_id=user_id,
                        file_content=conversions_content,
                        file_type="conversions",
                        original_filename=conversions.filename
                    )
                    print(f"[INFO] Conversions file uploaded to: {conversions_path}")
                    
                    # Reset file pointers for parsing
                    events.file.seek(0)
                    conversions.file.seek(0)
                except Exception as e:
                    print(f"[ERROR] Failed to store files in GCS: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue with processing even if storage fails
            else:
                print(f"[WARN] GCS storage not available, skipping file upload")

            _, events_rows = parse_csv(events)
            _, conversions_rows = parse_csv(conversions)

            if not all(len(r) == 6 for r in events_rows):
                raise HTTPException(status_code=400, detail="Events CSV must have 6 columns")
            if not all(len(r) == 3 for r in conversions_rows):
                raise HTTPException(status_code=400, detail="Conversions CSV must have 3 columns")

            events_data = normalize_events(events_rows)
            conversions_data = normalize_conversions(conversions_rows)
            print("event", events_data)
            print("conversion", conversions_data)
        if not events_data or not conversions_data:
            raise HTTPException(status_code=400, detail="Parsed CSVs have no valid data rows")

        # now call workflow
        result = workflows.k_anonymity_workflow(events_data, conversions_data, k=k, supp_level=supp_level)

        return {
            "parameters": {"k": k, "suppression_level": supp_level},
            "result": result,
            "metadata": {"total_records": len(result)}
        }

    except Exception as e:
        print("Error occurred in k-anonymity workflow:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/differential-privacy")
async def differential_privacy(
    request: Request,
    events: UploadFile = File(None),
    conversions: UploadFile = File(None),
    epsilon: float = Form(default=1.0),
    split_evenly_over: int = Form(default=6),
    use_sample_data: bool = Form(default=False),
    user_id: str = Depends(verify_token)
):
    """
    Apply differential privacy to conversion aggregates.

    Returns both non-private and differentially private counts
    for comparison.
    """
    try:
        if use_sample_data:
            events_data, conversions_data, campaigns = workflows.generate_sample_data()
        else:
            if not events or not conversions:
                raise HTTPException(status_code=400, detail="Both events and conversions CSV files are required.")

            # Store files in GCS before processing
            if gcs_storage:
                try:
                    print(f"[INFO] Storing files in GCS for user_id: {user_id}")
                    # Read file content
                    events.file.seek(0)
                    events_content = await events.read()
                    conversions.file.seek(0)
                    conversions_content = await conversions.read()
                    
                    # Upload to GCS
                    events_path = gcs_storage.upload_file(
                        user_id=user_id,
                        file_content=events_content,
                        file_type="events",
                        original_filename=events.filename
                    )
                    print(f"[INFO] Events file uploaded to: {events_path}")
                    
                    conversions_path = gcs_storage.upload_file(
                        user_id=user_id,
                        file_content=conversions_content,
                        file_type="conversions",
                        original_filename=conversions.filename
                    )
                    print(f"[INFO] Conversions file uploaded to: {conversions_path}")
                    
                    # Reset file pointers for parsing
                    events.file.seek(0)
                    conversions.file.seek(0)
                except Exception as e:
                    print(f"[ERROR] Failed to store files in GCS: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue with processing even if storage fails
            else:
                print(f"[WARN] GCS storage not available, skipping file upload")

            _, events_rows = parse_csv(events)
            _, conversions_rows = parse_csv(conversions)

            if not all(len(r) == 6 for r in events_rows):
                raise HTTPException(status_code=400, detail="Events CSV must have 6 columns")
            if not all(len(r) == 3 for r in conversions_rows):
                raise HTTPException(status_code=400, detail="Conversions CSV must have 3 columns")

            events_data = normalize_events(events_rows)
            conversions_data = normalize_conversions(conversions_rows)

        if not events_data or not conversions_data:
            raise HTTPException(status_code=400, detail="Parsed CSVs have no valid data rows")

        result = workflows.differential_privacy_workflow(
            events_data,
            conversions_data,
            epsilon=epsilon,
            split_evenly_over=split_evenly_over
        )

        return {
            "parameters": {
                "epsilon": epsilon,
                "split_evenly_over": split_evenly_over
            },
            "result": result,
            "metadata": {
                "description": f"Differentially private counts with ε={epsilon}",
                "privacy_guarantee": "Output satisfies ε-differential privacy"
            }
        }
    except Exception as e:
        print("Error occurred in differential-privacy workflow:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/homomorphic-encryption")
async def homomorphic_encryption(
    request: Request,
    events: UploadFile = File(None),
    conversions: UploadFile = File(None),
    use_sample_data: bool = Form(default=False),
    user_id: str = Depends(verify_token)
):
    """
    Apply homomorphic encryption to conversion data.

    Returns decrypted purchase counts computed on encrypted data.
    """
    try:
        if use_sample_data:
            events_data, conversions_data, campaigns = workflows.generate_sample_data()
        else:
            if not events or not conversions:
                raise HTTPException(status_code=400, detail="Both events and conversions CSV files are required.")

            # Store files in GCS before processing
            if gcs_storage:
                try:
                    print(f"[INFO] Storing files in GCS for user_id: {user_id}")
                    # Read file content
                    events.file.seek(0)
                    events_content = await events.read()
                    conversions.file.seek(0)
                    conversions_content = await conversions.read()
                    
                    # Upload to GCS
                    events_path = gcs_storage.upload_file(
                        user_id=user_id,
                        file_content=events_content,
                        file_type="events",
                        original_filename=events.filename
                    )
                    print(f"[INFO] Events file uploaded to: {events_path}")
                    
                    conversions_path = gcs_storage.upload_file(
                        user_id=user_id,
                        file_content=conversions_content,
                        file_type="conversions",
                        original_filename=conversions.filename
                    )
                    print(f"[INFO] Conversions file uploaded to: {conversions_path}")
                    
                    # Reset file pointers for parsing
                    events.file.seek(0)
                    conversions.file.seek(0)
                except Exception as e:
                    print(f"[ERROR] Failed to store files in GCS: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue with processing even if storage fails
            else:
                print(f"[WARN] GCS storage not available, skipping file upload")

            _, events_rows = parse_csv(events)
            _, conversions_rows = parse_csv(conversions)

            if not all(len(r) == 6 for r in events_rows):
                raise HTTPException(status_code=400, detail="Events CSV must have 6 columns")
            if not all(len(r) == 3 for r in conversions_rows):
                raise HTTPException(status_code=400, detail="Conversions CSV must have 3 columns")

            events_data = normalize_events(events_rows)
            conversions_data = normalize_conversions(conversions_rows)

        if not events_data or not conversions_data:
            raise HTTPException(status_code=400, detail="Parsed CSVs have no valid data rows")

        result = workflows.homomorphic_encryption_workflow(events_data, conversions_data)

        return {
            "result": result,
            "metadata": {
                "description": "Purchase counts computed on encrypted conversion data",
                "privacy_guarantee": "Computation performed without decrypting individual records"
            }
        }
    except Exception as e:
        print("Error occurred in homomorphic-encryption workflow:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sample-data-info", response_class=HTMLResponse)
def get_sample_data_info(method: str):
    """
    Get HTML documentation for privacy-enhancing technologies.
    
    Args:
        method: The privacy method to get information for ("k-anonymity" or "differential")
    
    Returns:
        HTML content explaining the selected method
    """
    try:
        # Validate the method parameter
        if method not in ["k-anonymity", "differential-privacy"]:
            raise HTTPException(
                status_code=400, 
                detail="Method parameter must be either 'k-anonymity' or 'differential-privacy'"
            )
        
        # Resolve the correct HTML file based on method
        if method == "k-anonymity":
            html_file_path = resolve_notebook_path("k-anonymity.html")
        else:
            html_file_path = resolve_notebook_path("differential-privacy.html")
        
        # Verify the file exists
        if not os.path.exists(html_file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Documentation file not found: {html_file_path}"
            )

        # Return the file content
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Notebook file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/api/walkthrough", response_class=JSONResponse)
def get_walkthrough_info(method: str):
    """
    Returns an array of HTML slides for walkthrough UI carousel.
    Each slide corresponds to an HTML file in the relevant walkthrough folder.
    """

    # Validate method
    if method not in ["k-anonymity", "differential-privacy"]:
        raise HTTPException(
            status_code=400,
            detail="Method parameter must be either 'k-anonymity' or 'differential-privacy'",
        )

    try:
        # ✅ Works in both Docker and local setups
        walkthrough_dir = resolve_notebook_path("walkthroughs", method)

        if not os.path.exists(walkthrough_dir):
            raise HTTPException(status_code=404, detail=f"Walkthrough folder not found: {walkthrough_dir}")

        # Collect all .html files (each file = 1 slide)
        html_files = [
            os.path.join(walkthrough_dir, f)
            for f in os.listdir(walkthrough_dir)
            if f.endswith(".html")
        ]

        if not html_files:
            raise HTTPException(status_code=404, detail="No walkthrough slides found.")

        # Sort files naturally (slide1.html, slide2.html, ...)
        html_files.sort(key=lambda f: f.lower())

        slides: List[str] = []
        for file_path in html_files:
            with open(file_path, "r", encoding="utf-8") as f:
                slides.append(f.read())

        return JSONResponse(content={"slides": slides})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/api/user/files")
async def get_user_files(user_id: str = Depends(verify_token)):
    """
    Get list of files stored for the authenticated user.
    
    Returns:
        JSON response with list of file metadata
    """
    try:
        print(f"[INFO] Listing files for user_id: {user_id}")
        if not gcs_storage:
            print(f"[WARN] GCS storage not configured for user_id: {user_id}")
            return {
                "files": [],
                "message": "GCS storage not configured"
            }
        
        files = gcs_storage.list_user_files(user_id)
        print(f"[INFO] Found {len(files)} files for user_id: {user_id}")
        
        return {
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        print(f"[ERROR] Error listing user files for user_id {user_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@app.get("/api/download-templates")
def download_templates():
    """
    Download a ZIP file containing CSV templates for events and conversions.
    
    These templates can be used for all three algorithms:
    - k-anonymity
    - differential-privacy
    - homomorphic-encryption
    
    Returns:
        ZIP file containing:
        - events.csv: Template with 6 columns (space_id, email, event_type, campaign, region, opt_out)
        - conversions.csv: Template with 3 columns (space_id, email, event_type)
    """
    try:
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Create events.csv template
            events_csv = io.StringIO()
            events_writer = csv.writer(events_csv)
            events_writer.writerow(['space_id', 'email', 'event_type', 'campaign', 'region', 'opt_out'])
            # Add example rows
            events_writer.writerow([1, 'user1@example.com', 'click', 'Red', 'NA', 'false'])
            events_writer.writerow([1, 'user2@example.com', 'click', 'Blue', 'EMEA', 'true'])
            events_writer.writerow([1, 'user3@example.com', 'view', 'Green', 'APAC', 'false'])
            zip_file.writestr('events.csv', events_csv.getvalue())
            
            # Create conversions.csv template
            conversions_csv = io.StringIO()
            conversions_writer = csv.writer(conversions_csv)
            conversions_writer.writerow(['space_id', 'email', 'event_type'])
            # Add example rows
            conversions_writer.writerow([1, 'user1@example.com', 'Purchase'])
            conversions_writer.writerow([1, 'user2@example.com', 'Subscription'])
            conversions_writer.writerow([1, 'user3@example.com', 'Purchase'])
            zip_file.writestr('conversions.csv', conversions_csv.getvalue())
        
        zip_buffer.seek(0)
        
        # Return ZIP file as downloadable response
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=privacy-lab-templates.zip"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating templates: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
