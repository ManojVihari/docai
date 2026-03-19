import difflib
from email.mime import base
import os

from fastapi import APIRouter, BackgroundTasks,Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models.schema import AnalyzeRequest
from app.services.version_service import VersionService
from app.services.doc_service import process_routes
import markdown

router = APIRouter()
version_service = VersionService()
templates = Jinja2Templates(directory="app/ui/templates")


@router.post("/analyze")
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):

    background_tasks.add_task(
        process_routes,
        request.routes,
        request.commit,
        request.repository
    )

    return {
        "status": "processing_started"
    }

@router.get("/ui", response_class=HTMLResponse)
def ui_home(request: Request):

    import os

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    base = os.path.join(BASE_DIR, "docs")

    data = {}

    if os.path.exists(base):
        for repo in os.listdir(base):

            repo_path = os.path.join(base, repo)

            if os.path.isdir(repo_path):

                apis = []

            for api in os.listdir(repo_path):

                api_path = os.path.join(repo_path, api)

                if os.path.isdir(api_path):

                    versions = [
                        f for f in os.listdir(api_path)
                        if f.startswith("v") and f.endswith(".md")
                    ]

                    latest = max(
                        [int(v.replace("v", "").replace(".md", "")) for v in versions],
                        default=0
                    )

                    apis.append({
                        "name": api,
                        "latest_version": latest
                    })

            data[repo] = apis
    print("Loaded data:", data)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data
        }
    )

@router.get("/ui/{repo}/{api}", response_class=HTMLResponse)
def api_history(request: Request, repo: str, api: str):

    versions = version_service.get_versions(repo, api)

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "versions": versions
        }
    )


@router.get("/ui/{repo}/{api}/diff", response_class=HTMLResponse)
def api_diff(request: Request, repo: str, api: str, v1: int, v2: int):

    versions = version_service.get_versions(repo, api)
    v_map = {v["version"]: v for v in versions}

    if v1 not in v_map or v2 not in v_map:
        return HTMLResponse("Invalid versions", status_code=404)

    content1 = v_map[v1]["content"].splitlines()
    content2 = v_map[v2]["content"].splitlines()

    diff_table = difflib.HtmlDiff(wrapcolumn=80).make_table(
        content1,
        content2,
        fromdesc=f"v{v1}",
        todesc=f"v{v2}",
        context=True,
        numlines=3
    )

    return templates.TemplateResponse(
        "diff.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "diff": diff_table,
            "v1": v1,
            "v2": v2
        }
    )

@router.get("/ui/{repo}/{api}/view/{version}", response_class=HTMLResponse)
def view_doc(request: Request, repo: str, api: str, version: int):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(
        BASE_DIR,
        "docs",
        repo,
        api,
        f"v{version}.md"
    )

    if not os.path.exists(file_path):
        return HTMLResponse("Document not found", status_code=404)

    with open(file_path, "r") as f:
        md_content = f.read()

    html_content = markdown.markdown(
    md_content,
    extensions=["tables", "fenced_code"]
)

    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "version": version,
            "content": html_content
        }
    )