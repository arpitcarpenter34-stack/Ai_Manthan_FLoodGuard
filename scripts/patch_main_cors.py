from pathlib import Path

target_file = Path("E:/ai-manthan/hydro_guard_indore/backend/main.py")
content = target_file.read_text(encoding="utf-8")

old_snippet = '''# Cross-Origin Resource Sharing (CORS) for Streamlit frontend and external consumers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

new_snippet = '''# Environment-based Cross-Origin Resource Sharing (CORS) configuration
allow_creds = "*" not in config.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

old_snippet_crlf = old_snippet.replace("\n", "\r\n")
new_snippet_crlf = new_snippet.replace("\n", "\r\n")

if old_snippet_crlf in content:
    content = content.replace(old_snippet_crlf, new_snippet_crlf, 1)
    target_file.write_text(content, encoding="utf-8")
    print("Successfully patched backend/main.py CORS (CRLF)")
elif old_snippet in content:
    content = content.replace(old_snippet, new_snippet, 1)
    target_file.write_text(content, encoding="utf-8")
    print("Successfully patched backend/main.py CORS (LF)")
else:
    print("Could not find old_snippet in backend/main.py")
