#!/usr/bin/env python3
"""
Generate a professional HTML guide for a single product.
Reads product.json + main.py to auto-detect endpoints and create documentation.

Usage: python3 generate_single_guide.py <product-directory>
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def find_main_py(product_dir):
    """Find the main FastAPI file."""
    candidates = [
        os.path.join(product_dir, "main.py"),
        os.path.join(product_dir, "backend", "main.py"),
        os.path.join(product_dir, "src", "main.py"),
        os.path.join(product_dir, "app", "main.py"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def extract_endpoints(main_py_path):
    """Extract FastAPI endpoints from main.py."""
    if not main_py_path:
        return []
    
    with open(main_py_path) as f:
        content = f.read()
    
    # Match @app.get("/path"), @app.post("/path"), etc.
    pattern = r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)
    
    endpoints = []
    for method, path in matches:
        # Try to find the function docstring
        func_pattern = rf'@app\.{method}\(["\']{ re.escape(path) }["\'].*?\)\s*(?:async\s+)?def\s+\w+\([^)]*\)(?:\s*->.*?)?\s*:\s*(?:"""(.*?)""")?'
        func_match = re.search(func_pattern, content, re.DOTALL)
        doc = func_match.group(1).strip().split('\n')[0] if func_match and func_match.group(1) else f"{method.upper()} {path}"
        
        endpoints.append({
            "method": method.upper(),
            "path": path,
            "description": doc,
        })
    
    return endpoints


def extract_env_vars(product_dir):
    """Extract env vars from .env.example."""
    env_file = os.path.join(product_dir, ".env.example")
    if not os.path.exists(env_file):
        return []
    
    vars = []
    with open(env_file) as f:
        comment = ""
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                comment = line.lstrip("# ").strip()
            elif "=" in line:
                key, value = line.split("=", 1)
                vars.append((key.strip(), comment or key.strip(), value.strip()))
                comment = ""
    return vars


def generate_guide(product_dir):
    """Generate the complete HTML guide."""
    product_dir = str(product_dir)
    
    # Load product.json
    with open(os.path.join(product_dir, "product.json")) as f:
        product = json.load(f)
    
    name = product["name"]
    desc = product["description"]
    price = product.get("price", 0)
    category = product.get("category", "automation")
    version = product.get("version", "1.0.0")
    features = product.get("features", [])
    tags = product.get("tags", [])
    slug = os.path.basename(product_dir)
    
    # Auto-detect
    main_py = find_main_py(product_dir)
    endpoints = extract_endpoints(main_py)
    env_vars = extract_env_vars(product_dir)
    
    # Determine tech stack
    tech = []
    if os.path.exists(os.path.join(product_dir, "requirements.txt")):
        with open(os.path.join(product_dir, "requirements.txt")) as f:
            req_content = f.read().lower()
        if "fastapi" in req_content: tech.append("FastAPI")
        if "openai" in req_content: tech.append("OpenAI")
        if "flask" in req_content: tech.append("Flask")
        if "django" in req_content: tech.append("Django")
        if "sqlalchemy" in req_content: tech.append("SQLAlchemy")
        if "redis" in req_content: tech.append("Redis")
        if "celery" in req_content: tech.append("Celery")
        tech.insert(0, "Python")
    if os.path.exists(os.path.join(product_dir, "package.json")):
        tech.append("Node.js")
    if os.path.exists(os.path.join(product_dir, "Dockerfile")):
        tech.append("Docker")
    if not tech:
        tech = ["Python", "Docker"]
    
    # Build HTML
    tech_badges = " ".join(f'<span class="badge">{t}</span>' for t in tech)
    tag_badges = " ".join(f'<span class="tag">{t}</span>' for t in tags)
    
    features_html = "\n".join(f"<li>{f}</li>" for f in features) if features else "<li>See README.md for full feature list</li>"
    
    env_rows = "\n".join(
        f'<tr><td><code>{k}</code></td><td>{d}</td><td><code>{v}</code></td></tr>'
        for k, d, v in env_vars
    ) if env_vars else '<tr><td colspan="3">See .env.example for all variables</td></tr>'
    
    endpoint_html = ""
    for ep in endpoints:
        endpoint_html += f"""
        <div class="endpoint">
            <span class="method method-{ep['method'].lower()}">{ep['method']}</span>
            <code>{ep['path']}</code>
            <p>{ep['description']}</p>
            <pre><code>curl -X {ep['method']} http://localhost:8000{ep['path']} \\
  -H "Content-Type: application/json"</code></pre>
        </div>
"""
    
    if not endpoint_html:
        endpoint_html = """
        <div class="endpoint">
            <p>This product uses n8n workflows. Import the workflow.json into your n8n instance.</p>
            <pre><code># Import via n8n CLI
n8n import:workflow --input=src/workflow.json

# Or use the n8n UI: Settings → Import Workflow</code></pre>
        </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} — Setup Guide</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; line-height: 1.7; color: #1a1a2e; background: #fafbfc; }}
        .cover {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 40px; text-align: center; }}
        .cover h1 {{ font-size: 2.8rem; margin-bottom: 10px; }}
        .cover .tagline {{ font-size: 1.3rem; opacity: 0.9; margin-bottom: 20px; }}
        .cover .price {{ font-size: 1.5rem; background: rgba(255,255,255,0.2); display: inline-block; padding: 8px 24px; border-radius: 30px; }}
        .cover .meta {{ margin-top: 20px; opacity: 0.7; font-size: 0.9rem; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        h2 {{ color: #667eea; font-size: 1.8rem; margin: 50px 0 20px; padding-bottom: 10px; border-bottom: 2px solid #e8ecf1; }}
        h3 {{ color: #333; font-size: 1.3rem; margin: 30px 0 15px; }}
        p {{ margin-bottom: 15px; color: #444; }}
        ul {{ margin: 10px 0 20px 25px; }}
        li {{ margin: 5px 0; }}
        .step {{ background: white; border: 1px solid #e8ecf1; border-radius: 12px; padding: 25px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
        .step-num {{ background: #667eea; color: white; width: 36px; height: 36px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; }}
        .step h3 {{ display: inline; vertical-align: middle; margin: 0; }}
        code {{ background: #f0f2f5; padding: 2px 8px; border-radius: 4px; font-family: 'Fira Code', 'Consolas', monospace; font-size: 0.9em; }}
        pre {{ background: #1a1a2e; color: #e8ecf1; padding: 20px; border-radius: 10px; overflow-x: auto; margin: 15px 0; }}
        pre code {{ background: none; padding: 0; color: inherit; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #667eea; color: white; padding: 12px 16px; text-align: left; }}
        td {{ padding: 12px 16px; border-bottom: 1px solid #e8ecf1; }}
        tr:hover td {{ background: #f8f9ff; }}
        .badge {{ display: inline-block; background: #e3f2fd; color: #1565c0; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; margin: 2px; }}
        .tag {{ display: inline-block; background: #f3e5f5; color: #7b1fa2; padding: 3px 10px; border-radius: 15px; font-size: 0.8rem; margin: 2px; }}
        .endpoint {{ background: #f8f9ff; border: 1px solid #e0e4ff; border-radius: 10px; padding: 20px; margin: 15px 0; }}
        .method {{ display: inline-block; padding: 3px 10px; border-radius: 5px; font-weight: bold; font-size: 0.85rem; color: white; margin-right: 8px; }}
        .method-get {{ background: #4caf50; }}
        .method-post {{ background: #2196f3; }}
        .method-put {{ background: #ff9800; }}
        .method-delete {{ background: #f44336; }}
        .method-patch {{ background: #9c27b0; }}
        .tip {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
        .warning {{ background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
        .toc {{ background: white; border: 1px solid #e8ecf1; border-radius: 12px; padding: 25px; margin: 30px 0; }}
        .toc a {{ color: #667eea; text-decoration: none; display: block; padding: 5px 0; }}
        .toc a:hover {{ text-decoration: underline; }}
        .footer {{ text-align: center; padding: 40px; color: #888; font-size: 0.9rem; border-top: 1px solid #e8ecf1; margin-top: 60px; }}
        @media print {{ .cover {{ padding: 60px 20px; }} }}
        @media (max-width: 600px) {{ .cover h1 {{ font-size: 2rem; }} }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>{name}</h1>
        <p class="tagline">{desc[:150]}</p>
        <span class="price">${price}</span>
        <p class="meta">v{version} • Setup Guide • {datetime.now().strftime("%B %Y")} • MyWork-AI</p>
    </div>
    <div class="container">
        <div class="toc">
            <h3>📖 Table of Contents</h3>
            <a href="#overview">1. Overview</a>
            <a href="#quickstart">2. Quick Start (5 minutes)</a>
            <a href="#config">3. Configuration</a>
            <a href="#api">4. API Reference</a>
            <a href="#docker">5. Docker Deployment</a>
            <a href="#troubleshooting">6. Troubleshooting</a>
        </div>

        <h2 id="overview">1. Overview</h2>
        <p>{desc}</p>
        <h3>Tech Stack</h3>
        <p>{tech_badges}</p>
        <h3>Features</h3>
        <ul>{features_html}</ul>
        <h3>Tags</h3>
        <p>{tag_badges}</p>

        <h2 id="quickstart">2. Quick Start</h2>
        <div class="step">
            <span class="step-num">1</span><h3>Extract the package</h3>
            <pre><code>tar -xzf {slug}.tar.gz
cd {slug}/</code></pre>
        </div>
        <div class="step">
            <span class="step-num">2</span><h3>Configure environment</h3>
            <pre><code>cp .env.example .env
# Edit .env with your API keys
nano .env</code></pre>
        </div>
        <div class="step">
            <span class="step-num">3</span><h3>Run setup</h3>
            <pre><code>chmod +x setup.sh
./setup.sh</code></pre>
        </div>
        <div class="step">
            <span class="step-num">4</span><h3>Verify</h3>
            <pre><code>curl http://localhost:8000/
# Interactive docs: http://localhost:8000/docs</code></pre>
        </div>
        <div class="tip">💡 <strong>Tip:</strong> Open <code>http://localhost:8000/docs</code> for the interactive Swagger UI.</div>

        <h2 id="config">3. Configuration</h2>
        <table>
            <tr><th>Variable</th><th>Description</th><th>Default</th></tr>
            {env_rows}
        </table>

        <h2 id="api">4. API Reference</h2>
        {endpoint_html}

        <h2 id="docker">5. Docker Deployment</h2>
        <div class="step">
            <span class="step-num">1</span><h3>Build</h3>
            <pre><code>docker build -t {slug} .</code></pre>
        </div>
        <div class="step">
            <span class="step-num">2</span><h3>Run</h3>
            <pre><code>docker run -d --name {slug} --env-file .env -p 8000:8000 {slug}</code></pre>
        </div>

        <h2 id="troubleshooting">6. Troubleshooting</h2>
        <div class="warning">⚠️ <strong>"Module not found":</strong> Run <code>./setup.sh</code> or <code>pip install -r requirements.txt</code></div>
        <div class="warning">⚠️ <strong>"API key not set":</strong> Check your <code>.env</code> file</div>
        <div class="warning">⚠️ <strong>Port in use:</strong> Change PORT in <code>.env</code> or run <code>lsof -i :8000</code></div>
        <h3>Support</h3>
        <p>Email: <a href="mailto:support@mywork-ai.dev">support@mywork-ai.dev</a></p>
    </div>
    <div class="footer">
        <p>© 2026 MyWork-AI • <a href="https://mywork-ai.dev">mywork-ai.dev</a></p>
        <p>Thank you for your purchase! 🚀</p>
    </div>
</body>
</html>"""
    
    return html


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_single_guide.py <product-directory>")
        sys.exit(1)
    
    product_dir = sys.argv[1]
    
    if not os.path.exists(os.path.join(product_dir, "product.json")):
        print(f"Error: {product_dir}/product.json not found")
        sys.exit(1)
    
    html = generate_guide(product_dir)
    
    docs_dir = os.path.join(product_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    output_path = os.path.join(docs_dir, "guide.html")
    with open(output_path, "w") as f:
        f.write(html)
    
    print(f"✅ Generated: {output_path}")
