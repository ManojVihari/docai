import difflib
from email.mime import base
import os
import bs4
from urllib.parse import quote
from datetime import datetime
from typing import List
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models.schema import AnalyzeRequest
from app.services.version_service import VersionService
from app.services.qa_plan_service import QAPlanService
from app.services.doc_service import process_routes
from app.services.llm_service import summarize_changes, search_apis_rag, answer_question_based_on_docs
from app.services.qa_plan_generator import generate_full_qa_plan
from app.services.dependency_analyzer import get_impact_analysis, build_dependency_graph
from app.services.test_templates import (
    get_predefined_templates, list_templates, create_template, 
    get_template_recommendations, apply_templates_to_qa_plan
)
import markdown
from bs4 import BeautifulSoup

router = APIRouter()
version_service = VersionService()
qa_plan_service = QAPlanService()
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
    import json

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    base = os.path.join(BASE_DIR, "docs")

    data = {}

    if os.path.exists(base):

        for repo in os.listdir(base):

            # 🔥 skip hidden files like .DS_Store
            if repo.startswith("."):
                continue

            repo_path = os.path.join(base, repo)

            if not os.path.isdir(repo_path):
                continue

            apis = []

            for api in os.listdir(repo_path):

                # 🔥 skip hidden files again
                if api.startswith("."):
                    continue

                api_path = os.path.join(repo_path, api)

                if not os.path.isdir(api_path):
                    continue

                versions = [
                    f for f in os.listdir(api_path)
                    if f.startswith("v") and f.endswith(".md")
                ]

                if not versions:
                    continue  # 🔥 skip empty APIs

                latest = max(
                    [int(v.replace("v", "").replace(".md", "")) for v in versions],
                    default=0
                )

                apis.append({
                    "name": api,
                    "latest_version": latest
                })

            if apis:
                data[repo] = sorted(apis, key=lambda x: x["name"])

    print("FINAL DATA:", json.dumps(data, indent=2))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": dict(sorted(data.items()))
        }
    )

@router.get("/ui/all", response_class=HTMLResponse)
def ui_all_apis(request: Request):
    """Display all APIs from all repositories in a unified view"""
    
    import os
    import json

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    base = os.path.join(BASE_DIR, "docs")

    data = {}

    if os.path.exists(base):

        for repo in os.listdir(base):

            # 🔥 skip hidden files like .DS_Store
            if repo.startswith("."):
                continue

            repo_path = os.path.join(base, repo)

            if not os.path.isdir(repo_path):
                continue

            apis = []

            for api in os.listdir(repo_path):

                # 🔥 skip hidden files again
                if api.startswith("."):
                    continue

                api_path = os.path.join(repo_path, api)

                if not os.path.isdir(api_path):
                    continue

                versions = [
                    f for f in os.listdir(api_path)
                    if f.startswith("v") and f.endswith(".md")
                ]

                if not versions:
                    continue  # 🔥 skip empty APIs

                latest = max(
                    [int(v.replace("v", "").replace(".md", "")) for v in versions],
                    default=0
                )

                apis.append({
                    "name": api,
                    "latest_version": latest,
                    "versions": len(versions)
                })

            if apis:
                data[repo] = sorted(apis, key=lambda x: x["name"])

    print("ALL APIS DATA:", json.dumps(data, indent=2))

    return templates.TemplateResponse(
        "all_apis.html",
        {
            "request": request,
            "data": dict(sorted(data.items()))
        }
    )
# def api_history(request: Request, repo: str, api: str):

#     versions = version_service.get_versions(repo, api)

#     return templates.TemplateResponse(
#         "history.html",
#         {
#             "request": request,
#             "repo": repo,
#             "api": api,
#             "versions": versions,
#             "apis": version_service.get_apis(repo) 
#         }
#     )

def render_md(md_text):
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code"]
    )

def html_to_blocks(html):
    soup = BeautifulSoup(html, "html.parser")

    blocks = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li", "pre", "table"]):
        blocks.append(str(el))  # keep HTML intact

    return blocks

def generate_diff(content1, content2):
    import difflib

    diff = list(difflib.ndiff(content1, content2))

    rows = []
    left_line = 1
    right_line = 1

    buffer_removed = []

    i = 0
    while i < len(diff):
        tag = diff[i][:2]
        text = diff[i][2:]

        # SAME
        if tag == "  ":
            rows.append(("same", left_line, text, right_line, text))
            left_line += 1
            right_line += 1
            i += 1

        # REMOVED → store in buffer
        elif tag == "- ":
            buffer_removed.append((left_line, text))
            left_line += 1
            i += 1

        # ADDED → match with buffer
        elif tag == "+ ":
            if buffer_removed:
                lnum, old_text = buffer_removed.pop(0)

                # 🔥 word highlight
          # detect table diff
                if old_text.strip().startswith("<table") and text.strip().startswith("<table"):
                    old_h, new_h = highlight_table_diff(old_text, text)

                # normal text diff
                else:
                    old_h, new_h = highlight_words(old_text, text)

                rows.append(("change", lnum, old_h, right_line, new_h))
            else:
                rows.append(("add", "", "", right_line, text))

            right_line += 1
            i += 1

        else:
            i += 1

    # leftover removed lines
    for lnum, old_text in buffer_removed:
        rows.append(("remove", lnum, old_text, "", ""))

    return rows

def highlight_table_diff(old_html, new_html):
    old_soup = BeautifulSoup(old_html, "html.parser")
    new_soup = BeautifulSoup(new_html, "html.parser")

    old_cells = old_soup.find_all("td")
    new_cells = new_soup.find_all("td")

    for i in range(min(len(old_cells), len(new_cells))):
        old_text = old_cells[i].get_text(strip=True)
        new_text = new_cells[i].get_text(strip=True)

        if old_text != new_text:
            old_cells[i].string = ""
            new_cells[i].string = ""

            old_cells[i].append(
                BeautifulSoup(
                    f"<span class='bg-red-200 px-1 rounded'>{old_text}</span>",
                    "html.parser"
                )
            )

            new_cells[i].append(
                BeautifulSoup(
                    f"<span class='bg-green-200 px-1 rounded'>{new_text}</span>",
                    "html.parser"
                )
            )

    return str(old_soup), str(new_soup)

def highlight_words(old, new):
    import difflib

    result_old = []
    result_new = []

    diff = difflib.ndiff(old.split(), new.split())

    for d in diff:
        if d.startswith("- "):
            result_old.append(f"<span class='bg-red-200'>{d[2:]}</span>")
        elif d.startswith("+ "):
            result_new.append(f"<span class='bg-green-200'>{d[2:]}</span>")
        elif d.startswith("  "):
            word = d[2:]
            result_old.append(word)
            result_new.append(word)

    return " ".join(result_old), " ".join(result_new)

@router.get("/ui/{repo}/{api}/diff", response_class=HTMLResponse)
def api_diff(request: Request, repo: str, api: str, v1: int, v2: int):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    api_path = os.path.join(BASE_DIR, "docs", repo, api)

    # Check if both version files exist
    file_v1 = os.path.join(api_path, f"v{v1}.md")
    file_v2 = os.path.join(api_path, f"v{v2}.md")

    if not os.path.exists(file_v1) or not os.path.exists(file_v2):
        return HTMLResponse("Invalid versions", status_code=404)

    # Read both versions
    with open(file_v1, "r") as f:
        md1 = f.read()
    
    with open(file_v2, "r") as f:
        md2 = f.read()

    # Generate LLM summary of changes
    summary = summarize_changes(md1, md2, api)

    html1 = render_md(md1)
    html2 = render_md(md2)

    content1 = html_to_blocks(html1)
    content2 = html_to_blocks(html2)

    diff_rows = generate_diff(content1, content2)

    return templates.TemplateResponse(
        "diff.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "v1": v1,
            "v2": v2,
            "rows": diff_rows,
            "summary": summary
        }
    )

# @router.get("/ui/{repo}/{api}/diff", response_class=HTMLResponse)
# def api_diff(request: Request, repo: str, api: str, v1: int, v2: int):

#     versions = version_service.get_versions(repo, api)
#     v_map = {v["version"]: v for v in versions}

#     if v1 not in v_map or v2 not in v_map:
#         return HTMLResponse("Invalid versions", status_code=404)

#     def render_md(md_text):
#         return markdown.markdown(md_text, extensions=["tables", "fenced_code"])

#     def clean_html(html):
#         soup = BeautifulSoup(html, "html.parser")
#         return soup.get_text().splitlines()

#     html1 = render_md(v_map[v1]["content"])
#     html2 = render_md(v_map[v2]["content"])

#     content1 = clean_html(html1)
#     content2 = clean_html(html2)

#     diff_table = difflib.HtmlDiff(wrapcolumn=100).make_table(
#         content1,
#         content2,
#         fromdesc=f"v{v1}",
#         todesc=f"v{v2}",
#         context=True,
#         numlines=5
#     )

#     return templates.TemplateResponse(
#         "diff.html",
#         {
#             "request": request,
#             "repo": repo,
#             "api": api,
#             "v1": v1,
#             "v2": v2,
#             "diff": diff_table
#         }
#     )


@router.get("/ui/{repo}/{api}/view/{version}", response_class=HTMLResponse)
def view_doc(request: Request, repo: str, api: str, version: str):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(BASE_DIR, "docs", repo, api, f"v{version}.md")

    if not os.path.exists(file_path):
        return HTMLResponse("Document not found", status_code=404)

    with open(file_path, "r") as f:
        md_content = f.read()

    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "codehilite",
            "attr_list",
            "md_in_html"
        ]
    )

    html_content = md.convert(md_content)
    toc = getattr(md, 'toc', '')

    # Get all apis in this repo
    repo_path = os.path.join(BASE_DIR, "docs", repo)
    apis = []
    
    if os.path.exists(repo_path):
        for api_dir in os.listdir(repo_path):
            api_dir_path = os.path.join(repo_path, api_dir)
            if os.path.isdir(api_dir_path):
                api_versions = [
                    f for f in os.listdir(api_dir_path)
                    if f.startswith("v") and f.endswith(".md")
                ]
                if api_versions:
                    apis.append({"name": api_dir})

    apis = sorted(apis, key=lambda x: x["name"])

    # Get all repos
    base = os.path.join(BASE_DIR, "docs")
    repos = []
    if os.path.exists(base):
        for r in os.listdir(base):
            if not r.startswith(".") and os.path.isdir(os.path.join(base, r)):
                repos.append(r)
    repos = sorted(repos)

    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "version": version,
            "content": html_content,
            "toc": toc,
            "apis": apis,
            "repos": repos
        }
    )

@router.get("/ui/{repo}/{api}", response_class=HTMLResponse)
def view_latest(request: Request, repo: str, api: str):

    # Get latest version from docs directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    api_path = os.path.join(BASE_DIR, "docs", repo, api)

    if not os.path.exists(api_path):
        return HTMLResponse("API not found", status_code=404)

    # Get all versions
    versions = [
        f for f in os.listdir(api_path)
        if f.startswith("v") and f.endswith(".md")
    ]

    if not versions:
        return HTMLResponse("No versions found", status_code=404)

    # Get latest version number
    latest_version = max(
        [int(v.replace("v", "").replace(".md", "")) for v in versions],
        default=None
    )

    if latest_version is None:
        return HTMLResponse("No valid versions found", status_code=404)

    # Read latest version file
    latest_file = os.path.join(api_path, f"v{latest_version}.md")
    
    with open(latest_file, "r") as f:
        md_content = f.read()

    # Use advanced markdown rendering with extensions
    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "codehilite",
            "attr_list",
            "md_in_html"
        ]
    )
    
    html_content = md.convert(md_content)
    toc = getattr(md, 'toc', '')

    # Get all apis in this repo
    repo_path = os.path.join(BASE_DIR, "docs", repo)
    apis = []
    
    if os.path.exists(repo_path):
        for api_dir in os.listdir(repo_path):
            api_dir_path = os.path.join(repo_path, api_dir)
            if os.path.isdir(api_dir_path):
                api_versions = [
                    f for f in os.listdir(api_dir_path)
                    if f.startswith("v") and f.endswith(".md")
                ]
                if api_versions:
                    apis.append({
                        "name": api_dir,
                    })

    apis = sorted(apis, key=lambda x: x["name"])

    # Get all repos
    base = os.path.join(BASE_DIR, "docs")
    repos = []
    if os.path.exists(base):
        for r in os.listdir(base):
            if not r.startswith(".") and os.path.isdir(os.path.join(base, r)):
                repos.append(r)
    repos = sorted(repos)

    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "version": latest_version,
            "content": html_content,
            "toc": toc,
            "apis": apis,
            "repos": repos
        }
    )


@router.get("/ui/{repo}/{api}/history", response_class=HTMLResponse)
def api_versions(request: Request, repo: str, api: str):

    # Get versions from docs directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    api_path = os.path.join(BASE_DIR, "docs", repo, api)

    if not os.path.exists(api_path):
        return HTMLResponse("API not found", status_code=404)

    # Get all version files
    version_files = [
        f for f in os.listdir(api_path)
        if f.startswith("v") and f.endswith(".md")
    ]

    versions = []
    for version_file in version_files:
        try:
            version_num = int(version_file.replace("v", "").replace(".md", ""))
            versions.append({
                "version": version_num,
                "commit_hash": "N/A"  # Since we're reading from markdown files, no commit hash
            })
        except ValueError:
            continue

    # Sort by version number (ascending - oldest first)
    versions = sorted(versions, key=lambda x: x["version"])

    # Get all apis in this repo
    repo_path = os.path.join(BASE_DIR, "docs", repo)
    apis = []
    
    if os.path.exists(repo_path):
        for api_dir in os.listdir(repo_path):
            api_dir_path = os.path.join(repo_path, api_dir)
            if os.path.isdir(api_dir_path):
                api_versions = [
                    f for f in os.listdir(api_dir_path)
                    if f.startswith("v") and f.endswith(".md")
                ]
                if api_versions:
                    apis.append({
                        "name": api_dir,
                    })

    apis = sorted(apis, key=lambda x: x["name"])

    # Get all repos
    base = os.path.join(BASE_DIR, "docs")
    repos = []
    if os.path.exists(base):
        for r in os.listdir(base):
            if not r.startswith(".") and os.path.isdir(os.path.join(base, r)):
                repos.append(r)
    repos = sorted(repos)

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "versions": versions,
            "apis": apis,
            "repos": repos
        }
    )

@router.get("/ui/search", response_class=HTMLResponse)
def ui_search(request: Request):
    """Display the LLM search page"""
    return templates.TemplateResponse(
        "llm_search.html",
        {"request": request}
    )

@router.get("/ui/{repo}", response_class=HTMLResponse)
def repo_home(request: Request, repo: str):
    # Get APIs from docs directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    repo_path = os.path.join(BASE_DIR, "docs", repo)
    
    if not os.path.exists(repo_path):
        return HTMLResponse(f"Repository '{repo}' not found", status_code=404)
    
    # Get all APIs in this repo
    apis = []
    try:
        for api_dir in os.listdir(repo_path):
            if api_dir.startswith("."):
                continue
            api_dir_path = os.path.join(repo_path, api_dir)
            if os.path.isdir(api_dir_path):
                api_versions = [
                    f for f in os.listdir(api_dir_path)
                    if f.startswith("v") and f.endswith(".md")
                ]
                if api_versions:
                    apis.append(api_dir)
    except Exception as e:
        print(f"Error reading APIs from {repo_path}: {e}")
        return HTMLResponse(f"Error reading repository: {e}", status_code=500)
    
    if not apis:
        return HTMLResponse(f"No APIs found in repository '{repo}'", status_code=404)

    # Pick first API alphabetically
    first_api = sorted(apis)[0]

    # Redirect to latest view with proper URL encoding
    return RedirectResponse(url=f"/ui/{quote(repo, safe='')}/{quote(first_api, safe='')}")


@router.post("/api/search")
async def search_apis(request: Request):
    """
    Search APIs and answer user questions based on available documentation.
    Acts as a conversational KT provider/assistant.
    
    Request body:
    {
        "query": "user string query about APIs"
    }
    
    Returns:
    {
        "success": true/false,
        "answer": "Conversational answer based on docs or error message",
        "results": [{"repo": "...", "api": "...", "version": 1}],
        "matchedCount": number of matching APIs
    }
    """
    try:
        body = await request.json()
        query = body.get("query", "").strip()
        
        if not query:
            return JSONResponse(
                {
                    "success": False,
                    "error": "Query cannot be empty",
                    "answer": "Please enter a question or search term.",
                    "results": [],
                    "matchedCount": 0
                },
                status_code=400
            )
        
        # Search for matching APIs using LLM
        matching_apis = search_apis_rag(query)
        
        # Generate a conversational answer based on actual documentation
        answer_result = answer_question_based_on_docs(query, matching_apis)
        
        return JSONResponse({
            "success": answer_result["success"],
            "answer": answer_result["answer"] or answer_result["message"],
            "message": answer_result["message"],
            "results": matching_apis,
            "matchedCount": len(matching_apis)
        })
        
    except Exception as e:
        print(f"Error in search_apis: {e}")
        return JSONResponse(
            {
                "success": False,
                "error": str(e),
                "answer": "Something went wrong on our end. Please try again later.",
                "results": [],
                "matchedCount": 0
            },
            status_code=500
        )


@router.get("/ui/{repo}/{api}/qa-plan", response_class=HTMLResponse)
def qa_plan_view(request: Request, repo: str, api: str, v1: int = None, v2: int = None, force: bool = False):
    """
    Generate and display a comprehensive QA plan for an API.
    QA plans are cached to avoid regenerating on every page load.
    If v1 and v2 are provided, includes regression testing.
    
    Args:
        force: If True, bypass cache and regenerate QA plan
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    api_path = os.path.join(BASE_DIR, "docs", repo, api)
    
    if not os.path.exists(api_path):
        return HTMLResponse(f"API '{api}' not found in repository '{repo}'", status_code=404)
    
    # Get available versions
    versions = [
        int(f.replace("v", "").replace(".md", ""))
        for f in os.listdir(api_path)
        if f.startswith("v") and f.endswith(".md")
    ]
    
    if not versions:
        return HTMLResponse("No versions found for this API", status_code=404)
    
    # If v2 not provided, use latest version
    if v2 is None:
        v2 = max(versions)
    
    # If v1 not provided, use second-to-latest (for regression) or None
    if v1 is None and len(versions) > 1:
        versions_sorted = sorted(versions)
        v1 = versions_sorted[-2]  # second-to-latest
    
    # Check if QA plan is cached (unless force=True to bypass cache)
    cached_plan = None if force else qa_plan_service.get_qa_plan(repo, api, v2)
    
    if cached_plan:
        # Use cached plan
        qa_plan = cached_plan.get("plan", {})
        plan_generated_at = cached_plan.get("generated_at")
    else:
        # Generate new QA plan
        # Read version files
        file_v2 = os.path.join(api_path, f"v{v2}.md")
        if not os.path.exists(file_v2):
            return HTMLResponse(f"Version v{v2} not found", status_code=404)
        
        with open(file_v2, "r") as f:
            doc_v2 = f.read()
        
        # Read v1 if regression testing
        doc_v1 = None
        if v1:
            file_v1 = os.path.join(api_path, f"v{v1}.md")
            if os.path.exists(file_v1):
                with open(file_v1, "r") as f:
                    doc_v1 = f.read()
        
        # Generate QA plan
        qa_plan = generate_full_qa_plan(api, doc_v2, doc_v1)
        
        # Store the generated plan
        qa_plan_service.save_qa_plan(repo, api, v2, qa_plan)
        
        plan_generated_at = datetime.utcnow().isoformat()
    
    # Get all repos for navigation
    base = os.path.join(BASE_DIR, "docs")
    repos = []
    if os.path.exists(base):
        for r in os.listdir(base):
            if not r.startswith(".") and os.path.isdir(os.path.join(base, r)):
                repos.append(r)
    repos = sorted(repos)
    
    # Get all APIs in this repo
    repo_path = os.path.join(BASE_DIR, "docs", repo)
    apis = []
    if os.path.exists(repo_path):
        for api_dir in os.listdir(repo_path):
            api_dir_path = os.path.join(repo_path, api_dir)
            if os.path.isdir(api_dir_path):
                api_versions = [
                    f for f in os.listdir(api_dir_path)
                    if f.startswith("v") and f.endswith(".md")
                ]
                if api_versions:
                    apis.append({"name": api_dir})
    
    apis = sorted(apis, key=lambda x: x["name"])
    
    return templates.TemplateResponse(
        "qa_plan.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "v1": v1,
            "v2": v2,
            "qa_plan": qa_plan,
            "plan_generated_at": plan_generated_at,
            "is_cached": cached_plan is not None,
            "apis": apis,
            "repos": repos
        }
    )


@router.get("/api/qa-plan")
async def generate_qa_plan_api(repo: str, api: str, v1: int = None, v2: int = None, force: bool = False):
    """
    API endpoint to generate QA plan as JSON.
    Useful for integrating with CI/CD pipelines.
    
    Args:
        force: If True, bypass cache and regenerate QA plan
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    api_path = os.path.join(BASE_DIR, "docs", repo, api)
    
    if not os.path.exists(api_path):
        return JSONResponse(
            {"error": f"API '{api}' not found in repository '{repo}'"},
            status_code=404
        )
    
    # Get available versions
    versions = [
        int(f.replace("v", "").replace(".md", ""))
        for f in os.listdir(api_path)
        if f.startswith("v") and f.endswith(".md")
    ]
    
    if not versions:
        return JSONResponse(
            {"error": "No versions found for this API"},
            status_code=404
        )
    
    # If v2 not provided, use latest version
    if v2 is None:
        v2 = max(versions)
    
    # If v1 not provided, use second-to-latest (for regression) or None
    if v1 is None and len(versions) > 1:
        versions_sorted = sorted(versions)
        v1 = versions_sorted[-2]
    
    # Read version files
    file_v2 = os.path.join(api_path, f"v{v2}.md")
    if not os.path.exists(file_v2):
        return JSONResponse(
            {"error": f"Version v{v2} not found"},
            status_code=404
        )
    
    with open(file_v2, "r") as f:
        doc_v2 = f.read()
    
    # Read v1 if regression testing
    doc_v1 = None
    if v1:
        file_v1 = os.path.join(api_path, f"v{v1}.md")
        if os.path.exists(file_v1):
            with open(file_v1, "r") as f:
                doc_v1 = f.read()
    
    # Check cache (unless force=True)
    cached_plan = None if force else qa_plan_service.get_qa_plan(repo, api, v2)
    
    if cached_plan:
        qa_plan = cached_plan.get("plan", {})
    else:
        # Generate QA plan
        qa_plan = generate_full_qa_plan(api, doc_v2, doc_v1)
        # Save to cache
        qa_plan_service.save_qa_plan(repo, api, v2, qa_plan)
    
    return JSONResponse(qa_plan)


# ============================================================================
# DEPENDENCY ANALYSIS ENDPOINTS
# ============================================================================

@router.get("/api/dependency-graph")
async def get_dependency_graph_api(repo: str):
    """
    Get dependency graph for a repository showing API relationships.
    
    Query params:
        repo: Repository name
    """
    graph = build_dependency_graph(repo)
    return JSONResponse(graph)


@router.get("/api/impact-analysis")
async def get_impact_analysis_api(repo: str, api: str, v1: int, v2: int):
    """
    Get breaking change impact analysis for an API upgrade.
    
    Query params:
        repo: Repository name
        api: API name
        v1: Version 1
        v2: Version 2
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    api_path = os.path.join(BASE_DIR, "docs", repo, api)
    
    # Read version files
    file_v1 = os.path.join(api_path, f"v{v1}.md")
    file_v2 = os.path.join(api_path, f"v{v2}.md")
    
    v1_content = ""
    v2_content = ""
    
    if os.path.exists(file_v1):
        with open(file_v1, 'r') as f:
            v1_content = f.read()
    
    if os.path.exists(file_v2):
        with open(file_v2, 'r') as f:
            v2_content = f.read()
    
    impact = get_impact_analysis(repo, api, v1_content, v2_content)
    return JSONResponse(impact)


# ============================================================================
# TEST TEMPLATES ENDPOINTS
# ============================================================================

@router.get("/api/templates/predefined")
async def get_predefined_templates_api():
    """Get all predefined test templates."""
    templates = get_predefined_templates()
    return JSONResponse(templates)


@router.get("/api/templates/recommendations")
async def get_template_recommendations_api(api: str):
    """Get recommended templates for an API."""
    recommendations = get_template_recommendations(api)
    return JSONResponse(recommendations)


@router.get("/api/templates/list")
async def list_templates_api(repo: str, category: str = None):
    """
    List custom templates for a repository.
    
    Query params:
        repo: Repository name
        category: Optional category filter
    """
    templates = list_templates(repo, category)
    return JSONResponse(templates)


@router.post("/api/templates/create")
async def create_template_api(
    repo: str,
    name: str,
    category: str,
    description: str,
    test_cases: List[str]
):
    """
    Create a new custom test template.
    
    Body params:
        repo: Repository name
        name: Template name
        category: Test category
        description: Template description
        test_cases: List of test case descriptions
    """
    success = create_template(repo, name, category, description, test_cases)
    
    return JSONResponse({
        "success": success,
        "message": f"Template '{name}' created successfully" if success else "Failed to create template"
    })


@router.get("/ui/{repo}/{api}/dependencies", response_class=HTMLResponse)
def dependencies_view(request: Request, repo: str, api: str, v1: int = None, v2: int = None):
    """
    Display dependency analysis and impact graph for API changes.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    api_path = os.path.join(BASE_DIR, "docs", repo, api)
    
    if not os.path.exists(api_path):
        return HTMLResponse(f"API '{api}' not found in repository '{repo}'", status_code=404)
    
    # Get available versions
    versions = [
        int(f.replace("v", "").replace(".md", ""))
        for f in os.listdir(api_path)
        if f.startswith("v") and f.endswith(".md")
    ]
    
    if not versions:
        return HTMLResponse("No versions found for this API", status_code=404)
    
    # If v2 not provided, use latest version
    if v2 is None:
        v2 = max(versions)
    
    # If v1 not provided, use second-to-latest
    if v1 is None and len(versions) > 1:
        versions_sorted = sorted(versions)
        v1 = versions_sorted[-2]
    
    # Read version files
    file_v1 = os.path.join(api_path, f"v{v1}.md") if v1 else None
    file_v2 = os.path.join(api_path, f"v{v2}.md")
    
    v1_content = ""
    if file_v1 and os.path.exists(file_v1):
        with open(file_v1, 'r') as f:
            v1_content = f.read()
    
    with open(file_v2, 'r') as f:
        v2_content = f.read()
    
    # Get impact analysis
    impact_data = get_impact_analysis(repo, api, v1_content, v2_content)
    
    # Get all repos for navigation
    base = os.path.join(BASE_DIR, "docs")
    repos = []
    if os.path.exists(base):
        for r in os.listdir(base):
            if not r.startswith(".") and os.path.isdir(os.path.join(base, r)):
                repos.append(r)
    repos = sorted(repos)
    
    # Get all APIs in this repo
    repo_path = os.path.join(BASE_DIR, "docs", repo)
    apis = []
    if os.path.exists(repo_path):
        for api_dir in os.listdir(repo_path):
            api_dir_path = os.path.join(repo_path, api_dir)
            if os.path.isdir(api_dir_path):
                api_versions = [
                    f for f in os.listdir(api_dir_path)
                    if f.startswith("v") and f.endswith(".md")
                ]
                if api_versions:
                    apis.append({"name": api_dir})
    
    apis = sorted(apis, key=lambda x: x["name"])
    
    return templates.TemplateResponse(
        "dependencies.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "v1": v1,
            "v2": v2,
            "impact_data": impact_data,
            "apis": apis,
            "repos": repos
        }
    )


@router.get("/ui/{repo}/{api}/templates", response_class=HTMLResponse)
def templates_view(request: Request, repo: str, api: str):
    """
    Display and manage test templates for an API.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    api_path = os.path.join(BASE_DIR, "docs", repo, api)
    
    if not os.path.exists(api_path):
        return HTMLResponse(f"API '{api}' not found in repository '{repo}'", status_code=404)
    
    # Get recommended templates
    recommendations = get_template_recommendations(api)
    
    # Get custom templates for this repo
    custom_templates = list_templates(repo)
    
    # Get predefined templates
    predefined = get_predefined_templates()
    
    # Get all repos for navigation
    base = os.path.join(BASE_DIR, "docs")
    repos = []
    if os.path.exists(base):
        for r in os.listdir(base):
            if not r.startswith(".") and os.path.isdir(os.path.join(base, r)):
                repos.append(r)
    repos = sorted(repos)
    
    # Get all APIs in this repo
    repo_path = os.path.join(BASE_DIR, "docs", repo)
    apis = []
    if os.path.exists(repo_path):
        for api_dir in os.listdir(repo_path):
            api_dir_path = os.path.join(repo_path, api_dir)
            if os.path.isdir(api_dir_path):
                api_versions = [
                    f for f in os.listdir(api_dir_path)
                    if f.startswith("v") and f.endswith(".md")
                ]
                if api_versions:
                    apis.append({"name": api_dir})
    
    apis = sorted(apis, key=lambda x: x["name"])
    
    return templates.TemplateResponse(
        "templates.html",
        {
            "request": request,
            "repo": repo,
            "api": api,
            "recommendations": recommendations,
            "custom_templates": custom_templates,
            "predefined_templates": predefined,
            "apis": apis,
            "repos": repos
        }
    )