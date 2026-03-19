# from fastapi import FastAPI, Request
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates

# from services.diff_analyzer import DiffAnalyzer
# from services.ast_extractor import ASTRouteExtractor
# from services.doc_generator import APIDocGenerator
# from services.markdown_writer import MarkdownWriter
# from services.markdown_builder import MarkdownBuilder
# from services.version_service import VersionService
# from services.diff_service import DiffService

# from git import Repo
# import json
# import difflib

# app = FastAPI()
# templates = Jinja2Templates(directory="templates")

# # Initialize services
# diff_analyzer = DiffAnalyzer(repo_path="sample_repo")
# ast_extractor = ASTRouteExtractor()
# doc_generator = APIDocGenerator()
# markdown_builder = MarkdownBuilder()
# writer = MarkdownWriter(file_path="docs/api_docs.md")
# version_service = VersionService()
# diff_service = DiffService()
# repo = Repo("sample_repo")


# @app.get("/")
# def root():
#     return {
#         "status": "Doc AI running (AST + Deterministic + Versioned UI)"
#     }


# # ---------------------------------------
# # ANALYZE + SAVE VERSION
# # ---------------------------------------

# @app.post("/analyze")
# def analyze():

#     changed_files = diff_analyzer.get_changed_python_files()

#     if not changed_files:
#         return {"message": "No changed Python files detected."}

#     results = []

#     for file in changed_files:

#         full_path = f"sample_repo/{file}"
#         routes = ast_extractor.extract_routes_from_file(full_path)

#         if not routes:
#             continue

#         for route in routes:

#             # LLM generates explanation JSON
#             explanation_raw = doc_generator.generate_explanation(
#                 route["source_code"]
#             )

#             try:
#                 llm_sections = json.loads(explanation_raw)
#             except Exception:
#                 return {
#                     "error": "LLM did not return valid JSON.",
#                     "raw_response": explanation_raw
#                 }

#             # Deterministic markdown generation
#             documentation = markdown_builder.build(
#                 route_data=route,
#                 llm_sections=llm_sections
#             )

#             # Write to markdown file
#             writer.write_or_replace(documentation)

#             # Save version to DB
#             commit_hash = repo.head.commit.hexsha

#             version_service.save_version(
#                 api_name=route["function_name"],
#                 commit_hash=commit_hash,
#                 content=documentation
#             )

#             results.append({
#                 "file": file,
#                 "api": route["function_name"]
#             })

#     if not results:
#         return {"message": "No API routes detected in changed files."}

#     return {
#         "status": "Documentation generated and version stored",
#         "details": results
#     }


# # ---------------------------------------
# # UI - API LIST
# # ---------------------------------------

# @app.get("/ui", response_class=HTMLResponse)
# def ui_home(request: Request):

#     apis = version_service.get_all_api_names()

#     return templates.TemplateResponse(
#         "index.html",
#         {
#             "request": request,
#             "apis": apis
#         }
#     )


# # ---------------------------------------
# # UI - VERSION HISTORY
# # ---------------------------------------

# @app.get("/ui/{api_name}", response_class=HTMLResponse)
# def api_history(request: Request, api_name: str):

#     versions = version_service.get_versions(api_name)

#     return templates.TemplateResponse(
#         "history.html",
#         {
#             "request": request,
#             "api_name": api_name,
#             "versions": versions
#         }
#     )


# # ---------------------------------------
# # UI - DIFF VIEW
# # ---------------------------------------

# @app.get("/ui/{api_name}/diff/{v1}/{v2}", response_class=HTMLResponse)
# def api_diff(request: Request, api_name: str, v1: int, v2: int):

#     versions = version_service.get_versions(api_name)

#     version_dict = {v.version: v for v in versions}

#     if v1 not in version_dict or v2 not in version_dict:
#         return HTMLResponse("Invalid version numbers", status_code=404)

#     content1 = version_dict[v1].content.splitlines()
#     content2 = version_dict[v2].content.splitlines()

#     diff_html = difflib.HtmlDiff().make_file(
#         content1,
#         content2,
#         fromdesc=f"Version {v1}",
#         todesc=f"Version {v2}"
#     )

#     return HTMLResponse(diff_html)
