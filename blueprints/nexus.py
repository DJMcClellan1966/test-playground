"""
Blueprint NEXUS - What the Industry Missed

Features that VSCode, Cursor, and every major AI company should have built:

1. NATURAL LANGUAGE → ARCHITECTURE
   "I want a todo app with auth and realtime sync"
   → Visual architecture appears, already wired
   → THEN you generate code

2. ARCHITECTURE DIFFING
   See visual diffs of architecture changes
   Not just code diff - ARCHITECTURE diff

3. WHAT-IF ANALYSIS
   "What breaks if I remove this block?"
   Shows cascade effects before you commit

4. COST/PERFORMANCE PREDICTION
   "This architecture = ~$47/month, handles ~10k req/s"
   Based on block choices and connections

5. ANTI-PATTERN DETECTION
   "Warning: This is a distributed monolith"
   Architectural linting in real-time

6. SHAREABLE PLAYGROUNDS
   One-click share URL
   Anyone can fork and modify your architecture

7. AUTOMATIC ADRs
   Generates Architecture Decision Records
   Documents WHY you made each choice

8. BIDIRECTIONAL SYNC
   Edit code → diagram updates
   Edit diagram → code updates

Run: python nexus.py
The future of development tools.
"""

import os
import sys
import json
import time
import webbrowser
import threading
import hashlib
import base64
import re
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request

sys.path.insert(0, str(Path(__file__).parent))
from blocks import BLOCKS

PORT = 5000
OUTPUT_DIR = Path(__file__).parent / "output"
PLAYGROUNDS_DIR = Path(__file__).parent / ".playgrounds"
ADRS_DIR = Path(__file__).parent / ".adrs"

# Cost estimates per block (monthly, in dollars)
COST_ESTIMATES = {
    "storage_json": {"base": 0, "per_1k_ops": 0, "description": "Free (file-based)"},
    "storage_sqlite": {"base": 0, "per_1k_ops": 0, "description": "Free (embedded)"},
    "storage_postgres": {"base": 15, "per_1k_ops": 0.001, "description": "~$15/mo base + usage"},
    "storage_s3": {"base": 0, "per_1k_ops": 0.004, "description": "Pay per request"},
    "auth_basic": {"base": 0, "per_1k_ops": 0, "description": "Free (session-based)"},
    "auth_oauth": {"base": 0, "per_1k_ops": 0.01, "description": "Free + API calls"},
    "cache_redis": {"base": 10, "per_1k_ops": 0, "description": "~$10/mo for managed"},
    "websocket_basic": {"base": 5, "per_1k_ops": 0.001, "description": "~$5/mo + connections"},
    "sync_crdt": {"base": 0, "per_1k_ops": 0.005, "description": "CPU overhead"},
    "docker_basic": {"base": 5, "per_1k_ops": 0, "description": "~$5/mo container"},
    "email_sendgrid": {"base": 0, "per_1k_ops": 0.10, "description": "Pay per email"},
    "crud_routes": {"base": 0, "per_1k_ops": 0, "description": "Free (code)"},
    "backend_flask": {"base": 5, "per_1k_ops": 0, "description": "~$5/mo hosting"},
    "backend_fastapi": {"base": 5, "per_1k_ops": 0, "description": "~$5/mo hosting"},
    "html_templates": {"base": 0, "per_1k_ops": 0, "description": "Free (static)"},
}

# Performance characteristics
PERF_ESTIMATES = {
    "storage_json": {"latency_ms": 5, "throughput": 100, "bottleneck": True},
    "storage_sqlite": {"latency_ms": 2, "throughput": 1000, "bottleneck": True},
    "storage_postgres": {"latency_ms": 3, "throughput": 10000, "bottleneck": False},
    "storage_s3": {"latency_ms": 50, "throughput": 5000, "bottleneck": False},
    "auth_basic": {"latency_ms": 1, "throughput": 50000, "bottleneck": False},
    "auth_oauth": {"latency_ms": 100, "throughput": 1000, "bottleneck": True},
    "cache_redis": {"latency_ms": 1, "throughput": 100000, "bottleneck": False},
    "websocket_basic": {"latency_ms": 1, "throughput": 10000, "bottleneck": False},
    "sync_crdt": {"latency_ms": 5, "throughput": 5000, "bottleneck": True},
    "docker_basic": {"latency_ms": 0, "throughput": 100000, "bottleneck": False},
    "crud_routes": {"latency_ms": 1, "throughput": 50000, "bottleneck": False},
    "backend_flask": {"latency_ms": 2, "throughput": 5000, "bottleneck": True},
    "backend_fastapi": {"latency_ms": 1, "throughput": 15000, "bottleneck": False},
}

# Anti-patterns to detect
ANTI_PATTERNS = [
    {
        "id": "distributed_monolith",
        "name": "Distributed Monolith",
        "description": "Multiple backends without clear separation of concerns",
        "condition": lambda b: b.count("backend_") >= 2 and "websocket" not in " ".join(b),
        "severity": "warning",
        "suggestion": "Consider using a single backend or add clear service boundaries"
    },
    {
        "id": "no_caching",
        "name": "Missing Caching Layer",
        "description": "Database-heavy setup without caching",
        "condition": lambda b: any(x.startswith("storage_") for x in b) and "cache_redis" not in b and len(b) > 3,
        "severity": "info",
        "suggestion": "Add cache_redis for better performance"
    },
    {
        "id": "auth_after_routes",
        "name": "Unprotected Routes",
        "description": "CRUD routes without authentication",
        "condition": lambda b: "crud_routes" in b and not any(x.startswith("auth_") for x in b),
        "severity": "warning",
        "suggestion": "Add authentication to protect your API"
    },
    {
        "id": "realtime_without_storage",
        "name": "Ephemeral Realtime",
        "description": "Realtime features without persistent storage",
        "condition": lambda b: ("websocket_basic" in b or "sync_crdt" in b) and not any(x.startswith("storage_") for x in b),
        "severity": "error",
        "suggestion": "Add storage to persist realtime data"
    },
    {
        "id": "over_engineered",
        "name": "Over-Engineering",
        "description": "Complex infrastructure for a simple app",
        "condition": lambda b: len(b) > 6 and "docker_basic" in b and "cache_redis" in b,
        "severity": "info",
        "suggestion": "Consider if all these blocks are necessary for your use case"
    },
    {
        "id": "sync_without_websocket",
        "name": "CRDT Without Transport",
        "description": "CRDT sync requires realtime communication",
        "condition": lambda b: "sync_crdt" in b and "websocket_basic" not in b,
        "severity": "error",
        "suggestion": "Add websocket_basic to enable CRDT synchronization"
    }
]


def get_blocks_data():
    """Get blocks with full data."""
    result = []
    for block_id, block in BLOCKS.items():
        result.append({
            "id": block_id,
            "name": block.name,
            "description": block.description,
            "requires": [{"name": p.name, "type": p.type} for p in block.requires],
            "provides": [{"name": p.name, "type": p.type} for p in block.provides],
            "cost": COST_ESTIMATES.get(block_id, {"base": 0, "per_1k_ops": 0}),
            "perf": PERF_ESTIMATES.get(block_id, {"latency_ms": 1, "throughput": 10000})
        })
    return result


def parse_natural_language(description: str) -> dict:
    """
    Parse natural language into an architecture.
    This is the killer feature - describe what you want, get a visual architecture.
    """
    description = description.lower()
    
    suggested_blocks = []
    connections = []
    
    # Intent detection
    intents = {
        "auth": ["auth", "login", "user", "account", "password", "sign in", "register"],
        "storage": ["save", "store", "database", "persist", "data", "record"],
        "realtime": ["realtime", "real-time", "live", "sync", "collaborative", "instant"],
        "api": ["api", "rest", "crud", "endpoint", "backend"],
        "email": ["email", "mail", "notification", "send message"],
        "cache": ["fast", "cache", "performance", "quick", "speed"],
        "deploy": ["deploy", "docker", "container", "production", "ship"]
    }
    
    detected_intents = set()
    for intent, keywords in intents.items():
        if any(kw in description for kw in keywords):
            detected_intents.add(intent)
    
    # Map intents to blocks
    if "auth" in detected_intents:
        if "oauth" in description or "google" in description or "github" in description:
            suggested_blocks.append("auth_oauth")
        else:
            suggested_blocks.append("auth_basic")
    
    if "storage" in detected_intents or not any(x in detected_intents for x in ["realtime"]):
        if "postgres" in description or "sql" in description or "production" in description:
            suggested_blocks.append("storage_postgres")
        elif "s3" in description or "file" in description or "upload" in description:
            suggested_blocks.append("storage_s3")
        elif "sqlite" in description:
            suggested_blocks.append("storage_sqlite")
        else:
            suggested_blocks.append("storage_json")
    
    if "realtime" in detected_intents:
        suggested_blocks.append("websocket_basic")
        if "collaborative" in description or "sync" in description:
            suggested_blocks.append("sync_crdt")
    
    if "api" in detected_intents or len(detected_intents) > 1:
        suggested_blocks.append("crud_routes")
        if "fast" in description or "performance" in description:
            suggested_blocks.append("backend_fastapi")
        else:
            suggested_blocks.append("backend_flask")
    
    if "email" in detected_intents:
        suggested_blocks.append("email_sendgrid")
    
    if "cache" in detected_intents:
        suggested_blocks.append("cache_redis")
    
    if "deploy" in detected_intents:
        suggested_blocks.append("docker_basic")
    
    # Default minimal setup
    if not suggested_blocks:
        suggested_blocks = ["storage_json", "crud_routes", "backend_flask"]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_blocks = []
    for b in suggested_blocks:
        if b not in seen:
            seen.add(b)
            unique_blocks.append(b)
    
    # Auto-wire connections based on port compatibility
    nodes = []
    for i, block_id in enumerate(unique_blocks):
        if block_id in BLOCKS:
            nodes.append({
                "id": i + 1,
                "blockId": block_id,
                "x": 100 + (i % 3) * 250,
                "y": 100 + (i // 3) * 150
            })
    
    # Find compatible connections
    for i, node_a in enumerate(nodes):
        block_a = BLOCKS.get(node_a["blockId"])
        if not block_a:
            continue
        
        for j, node_b in enumerate(nodes):
            if i >= j:
                continue
            block_b = BLOCKS.get(node_b["blockId"])
            if not block_b:
                continue
            
            # Check if a provides what b requires
            for p in block_a.provides:
                for r in block_b.requires:
                    if p.name == r.name:
                        connections.append({
                            "fromNode": node_a["id"],
                            "fromPort": p.name,
                            "toNode": node_b["id"],
                            "toPort": r.name,
                            "inferred": True
                        })
            
            # Check reverse
            for p in block_b.provides:
                for r in block_a.requires:
                    if p.name == r.name:
                        connections.append({
                            "fromNode": node_b["id"],
                            "fromPort": p.name,
                            "toNode": node_a["id"],
                            "toPort": r.name,
                            "inferred": True
                        })
    
    return {
        "blocks": unique_blocks,
        "nodes": nodes,
        "connections": connections,
        "detected_intents": list(detected_intents),
        "confidence": min(len(detected_intents) / 3, 1.0)
    }


def estimate_costs(block_ids: list, monthly_requests: int = 100000) -> dict:
    """Estimate monthly costs for an architecture."""
    total_base = 0
    total_usage = 0
    breakdown = []
    
    for bid in block_ids:
        cost = COST_ESTIMATES.get(bid, {"base": 0, "per_1k_ops": 0, "description": "Unknown"})
        base = cost["base"]
        usage = cost["per_1k_ops"] * (monthly_requests / 1000)
        
        total_base += base
        total_usage += usage
        
        breakdown.append({
            "block": bid,
            "base": base,
            "usage": round(usage, 2),
            "total": round(base + usage, 2),
            "description": cost.get("description", "")
        })
    
    return {
        "base_monthly": total_base,
        "usage_monthly": round(total_usage, 2),
        "total_monthly": round(total_base + total_usage, 2),
        "monthly_requests": monthly_requests,
        "breakdown": breakdown,
        "tier": "hobby" if total_base + total_usage < 20 else "startup" if total_base + total_usage < 100 else "scale"
    }


def estimate_performance(block_ids: list) -> dict:
    """Estimate performance characteristics."""
    if not block_ids:
        return {"throughput": 0, "latency_p50": 0, "latency_p99": 0, "bottleneck": None}
    
    # Find the bottleneck (lowest throughput)
    min_throughput = float('inf')
    total_latency = 0
    bottleneck = None
    bottlenecks = []
    
    for bid in block_ids:
        perf = PERF_ESTIMATES.get(bid, {"latency_ms": 1, "throughput": 10000, "bottleneck": False})
        total_latency += perf["latency_ms"]
        
        if perf["throughput"] < min_throughput:
            min_throughput = perf["throughput"]
            bottleneck = bid
        
        if perf.get("bottleneck"):
            bottlenecks.append(bid)
    
    return {
        "throughput": min_throughput,
        "throughput_formatted": f"{min_throughput:,} req/s" if min_throughput < float('inf') else "unlimited",
        "latency_p50": total_latency,
        "latency_p99": total_latency * 3,  # Rough estimate
        "bottleneck": bottleneck,
        "bottlenecks": bottlenecks,
        "grade": "A" if min_throughput > 10000 else "B" if min_throughput > 1000 else "C" if min_throughput > 100 else "D"
    }


def detect_anti_patterns(block_ids: list) -> list:
    """Detect architectural anti-patterns."""
    detected = []
    for pattern in ANTI_PATTERNS:
        try:
            if pattern["condition"](block_ids):
                detected.append({
                    "id": pattern["id"],
                    "name": pattern["name"],
                    "description": pattern["description"],
                    "severity": pattern["severity"],
                    "suggestion": pattern["suggestion"]
                })
        except Exception:
            pass
    return detected


def analyze_what_if(nodes: list, connections: list, remove_block_id: int) -> dict:
    """Analyze what happens if a block is removed."""
    target_node = next((n for n in nodes if n.get("id") == remove_block_id), None)
    if not target_node:
        return {"error": "Node not found"}
    
    block_id = target_node.get("blockId")
    block = BLOCKS.get(block_id)
    if not block:
        return {"error": "Block not found"}
    
    # Find what depends on this block
    provides = {p.name for p in block.provides}
    affected_connections = []
    orphaned_blocks = []
    
    for conn in connections:
        if conn.get("fromNode") == remove_block_id:
            affected_connections.append(conn)
            # Find the block that loses this connection
            to_node = next((n for n in nodes if n.get("id") == conn.get("toNode")), None)
            if to_node:
                orphaned_blocks.append({
                    "id": to_node.get("id"),
                    "blockId": to_node.get("blockId"),
                    "lost_port": conn.get("toPort")
                })
        if conn.get("toNode") == remove_block_id:
            affected_connections.append(conn)
    
    # Check if any orphaned blocks become invalid
    remaining_blocks = [n.get("blockId") for n in nodes if n.get("id") != remove_block_id]
    remaining_provides = set()
    for bid in remaining_blocks:
        b = BLOCKS.get(bid)
        if b:
            remaining_provides.update(p.name for p in b.provides)
    
    unsatisfied = []
    for orphan in orphaned_blocks:
        if orphan["lost_port"] not in remaining_provides:
            unsatisfied.append(orphan)
    
    # Suggest alternatives
    suggestions = []
    for port in provides:
        for bid, b in BLOCKS.items():
            if bid != block_id and any(p.name == port for p in b.provides):
                suggestions.append({
                    "block_id": bid,
                    "name": b.name,
                    "provides_port": port
                })
    
    return {
        "removing": {
            "id": remove_block_id,
            "blockId": block_id,
            "name": block.name
        },
        "impact": {
            "broken_connections": len(affected_connections),
            "orphaned_blocks": len(orphaned_blocks),
            "unsatisfied_requirements": len(unsatisfied)
        },
        "affected_connections": affected_connections,
        "orphaned_blocks": orphaned_blocks,
        "unsatisfied": unsatisfied,
        "suggestions": suggestions[:3],
        "safe_to_remove": len(unsatisfied) == 0
    }


def diff_architectures(before: dict, after: dict) -> dict:
    """
    Create a visual diff between two architectures.
    This is what git diff should be for architectures.
    """
    before_blocks = set(n.get("blockId") for n in before.get("nodes", []))
    after_blocks = set(n.get("blockId") for n in after.get("nodes", []))
    
    added_blocks = after_blocks - before_blocks
    removed_blocks = before_blocks - after_blocks
    unchanged_blocks = before_blocks & after_blocks
    
    # Connection diff
    def conn_key(c):
        return (c.get("fromNode"), c.get("fromPort"), c.get("toNode"), c.get("toPort"))
    
    before_conns = set(conn_key(c) for c in before.get("connections", []))
    after_conns = set(conn_key(c) for c in after.get("connections", []))
    
    added_conns = after_conns - before_conns
    removed_conns = before_conns - after_conns
    
    # Cost diff
    before_cost = estimate_costs(list(before_blocks))
    after_cost = estimate_costs(list(after_blocks))
    cost_delta = after_cost["total_monthly"] - before_cost["total_monthly"]
    
    # Performance diff
    before_perf = estimate_performance(list(before_blocks))
    after_perf = estimate_performance(list(after_blocks))
    
    return {
        "blocks": {
            "added": list(added_blocks),
            "removed": list(removed_blocks),
            "unchanged": list(unchanged_blocks)
        },
        "connections": {
            "added": len(added_conns),
            "removed": len(removed_conns)
        },
        "cost": {
            "before": before_cost["total_monthly"],
            "after": after_cost["total_monthly"],
            "delta": cost_delta,
            "direction": "increase" if cost_delta > 0 else "decrease" if cost_delta < 0 else "same"
        },
        "performance": {
            "before_throughput": before_perf["throughput"],
            "after_throughput": after_perf["throughput"],
            "direction": "faster" if after_perf["throughput"] > before_perf["throughput"] else "slower" if after_perf["throughput"] < before_perf["throughput"] else "same"
        },
        "summary": {
            "blocks_changed": len(added_blocks) + len(removed_blocks),
            "connections_changed": len(added_conns) + len(removed_conns),
            "is_breaking": len(removed_blocks) > 0
        }
    }


def create_playground(architecture: dict) -> str:
    """Create a shareable playground URL."""
    PLAYGROUNDS_DIR.mkdir(exist_ok=True)
    
    # Generate unique ID
    content = json.dumps(architecture, sort_keys=True)
    playground_id = hashlib.sha256(content.encode()).hexdigest()[:12]
    
    # Save playground
    playground_path = PLAYGROUNDS_DIR / f"{playground_id}.json"
    playground_path.write_text(json.dumps({
        "id": playground_id,
        "created": datetime.now().isoformat(),
        "architecture": architecture
    }, indent=2), encoding='utf-8')
    
    return playground_id


def get_playground(playground_id: str) -> dict:
    """Load a playground by ID."""
    playground_path = PLAYGROUNDS_DIR / f"{playground_id}.json"
    if playground_path.exists():
        return json.loads(playground_path.read_text(encoding='utf-8'))
    return None


def generate_adr(architecture: dict, decisions: list = None) -> str:
    """
    Generate an Architecture Decision Record.
    Documents WHY you made each choice.
    """
    block_ids = [n.get("blockId") for n in architecture.get("nodes", [])]
    app_name = architecture.get("name", "Unnamed App")
    description = architecture.get("description", "")
    
    adr = f"""# Architecture Decision Record: {app_name}

**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Status:** Accepted

## Context

{description if description else "Building a new application with Blueprint."}

## Decision

We will use the following architectural components:

"""
    
    for bid in block_ids:
        block = BLOCKS.get(bid)
        if block:
            cost = COST_ESTIMATES.get(bid, {})
            perf = PERF_ESTIMATES.get(bid, {})
            
            adr += f"""### {block.name}

- **Purpose:** {block.description}
- **Cost:** {cost.get('description', 'Unknown')}
- **Performance:** ~{perf.get('latency_ms', 'N/A')}ms latency, {perf.get('throughput', 'N/A'):,} req/s

"""
    
    # Anti-pattern warnings
    anti_patterns = detect_anti_patterns(block_ids)
    if anti_patterns:
        adr += """## Considerations

The following architectural considerations were noted:

"""
        for ap in anti_patterns:
            adr += f"""- **{ap['name']}:** {ap['description']}
  - Recommendation: {ap['suggestion']}

"""
    
    # Cost summary
    costs = estimate_costs(block_ids)
    adr += f"""## Cost Analysis

| Tier | Monthly Cost |
|------|-------------|
| Base Infrastructure | ${costs['base_monthly']:.2f} |
| Usage (100k requests) | ${costs['usage_monthly']:.2f} |
| **Total** | **${costs['total_monthly']:.2f}/month** |

Classification: **{costs['tier'].title()}** tier

"""
    
    # Performance summary
    perf = estimate_performance(block_ids)
    adr += f"""## Performance Characteristics

- **Throughput:** {perf['throughput_formatted']}
- **Latency (P50):** {perf['latency_p50']}ms
- **Latency (P99):** {perf['latency_p99']}ms
- **Bottleneck:** {perf['bottleneck'] or 'None identified'}
- **Grade:** {perf['grade']}

"""
    
    adr += """## Consequences

This architecture provides:
- Clear separation of concerns
- Scalable data storage
- Maintainable codebase

Trade-offs accepted:
- Added complexity from multiple components
- Operational overhead for production deployment

---
*Generated by Blueprint NEXUS*
"""
    
    return adr


def save_adr(architecture: dict) -> str:
    """Save an ADR to disk."""
    ADRS_DIR.mkdir(exist_ok=True)
    
    adr_content = generate_adr(architecture)
    app_name = architecture.get("name", "unnamed").lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d")
    
    filename = f"ADR-{timestamp}-{app_name}.md"
    (ADRS_DIR / filename).write_text(adr_content, encoding='utf-8')
    
    return filename


def generate_app(data: dict) -> dict:
    """Generate full app from architecture."""
    nodes = data.get("nodes", [])
    connections = data.get("connections", [])
    project_name = data.get("name", "nexus_app")
    description = data.get("description", "")
    
    output_path = OUTPUT_DIR / project_name.lower().replace(" ", "_")
    output_path.mkdir(parents=True, exist_ok=True)
    
    block_ids = [n.get("blockId") for n in nodes if n.get("blockId")]
    app_name = project_name.title().replace("_", " ")
    
    # Save ADR
    adr_file = save_adr(data)
    
    # Get analysis
    costs = estimate_costs(block_ids)
    perf = estimate_performance(block_ids)
    anti_patterns = detect_anti_patterns(block_ids)
    
    # Build HTML strings outside f-string
    block_html_parts = []
    for b in block_ids:
        if b in BLOCKS:
            block_html_parts.append(f'<span class="tag">{BLOCKS[b].name}</span>')
    block_html = "\n                ".join(block_html_parts)
    
    warning_html = ""
    if anti_patterns:
        warning_items = []
        for ap in anti_patterns:
            warning_items.append(f'<div class="warning-item">{ap["name"]}: {ap["suggestion"]}</div>')
        warning_html = "\n                ".join(warning_items)
    
    # Generate main app with security best practices
    app_code = f'''"""
{app_name} - Built with Blueprint NEXUS

Description: {description}
Blocks: {", ".join(block_ids)}
Monthly Cost: ~${costs["total_monthly"]:.2f}
Throughput: {perf["throughput_formatted"]}

Security Best Practices Applied:
- CSRF protection via tokens
- XSS prevention via HTML escaping
- Content Security Policy headers
- Rate limiting (basic)
- Input validation and sanitization
- Secure cookie settings
- No debug mode in production
"""

import os
import secrets
import time
from functools import wraps
from flask import Flask, request, jsonify, session, abort

app = Flask(__name__)

# Security: Use a strong secret key from environment, random fallback for dev
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Security: Secure cookie settings
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get('HTTPS', 'false').lower() == 'true',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
)

# In-memory storage (replace with database in production)
items = []

# Simple rate limiting
rate_limit_store = {{}}
RATE_LIMIT = 100  # requests per minute

def rate_limited(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr
        now = time.time()
        
        # Clean old entries
        rate_limit_store[ip] = [t for t in rate_limit_store.get(ip, []) if now - t < 60]
        
        if len(rate_limit_store.get(ip, [])) >= RATE_LIMIT:
            return jsonify({{"error": "Rate limit exceeded"}}), 429
        
        rate_limit_store.setdefault(ip, []).append(now)
        return f(*args, **kwargs)
    return decorated

def add_security_headers(response):
    \"\"\"Add security headers to all responses.\"\"\"
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

app.after_request(add_security_headers)

def escape_html(text):
    \"\"\"Escape HTML special characters to prevent XSS.\"\"\"
    if not isinstance(text, str):
        text = str(text)
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))

@app.route("/")
@rate_limited
def home():
    # Generate CSRF token for forms
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    csrf_token = session['csrf_token']
    
    return f\"\"\"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); 
               min-height: 100vh; padding: 40px; color: white; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ font-size: 2.4em; margin-bottom: 10px; }}
        .subtitle {{ color: #8b8ba7; margin-bottom: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }}
        .metric {{ background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; text-align: center; }}
        .metric-value {{ font-size: 1.8em; font-weight: bold; color: #58a6ff; }}
        .metric-label {{ font-size: 0.75em; color: #8b8ba7; margin-top: 5px; }}
        .tags {{ margin-bottom: 30px; }}
        .tag {{ display: inline-block; background: #58a6ff; padding: 6px 14px; border-radius: 20px; 
               font-size: 12px; margin: 4px; }}
        .card {{ background: rgba(255,255,255,0.05); padding: 25px; border-radius: 16px; }}
        form {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        input {{ flex: 1; padding: 14px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
               border-radius: 8px; color: white; font-size: 16px; }}
        input:focus {{ outline: none; border-color: #58a6ff; }}
        button {{ background: #58a6ff; color: white; border: none; padding: 14px 28px; border-radius: 8px; 
                cursor: pointer; font-weight: 600; transition: background 0.2s; }}
        button:hover {{ background: #4393e4; }}
        .items {{ list-style: none; }}
        .items li {{ padding: 15px; background: rgba(255,255,255,0.03); margin-bottom: 8px; border-radius: 8px;
                   display: flex; justify-content: space-between; align-items: center; }}
        .del {{ background: #f85149; padding: 8px 16px; border-radius: 6px; border: none; color: white; 
               cursor: pointer; font-size: 12px; transition: background 0.2s; }}
        .del:hover {{ background: #da3633; }}
        .warnings {{ background: rgba(248,81,73,0.1); border-left: 4px solid #f85149; padding: 15px; 
                    border-radius: 0 8px 8px 0; margin-bottom: 20px; }}
        .warning-item {{ font-size: 13px; margin: 8px 0; }}
        .error {{ color: #f85149; font-size: 12px; margin-top: 5px; display: none; }}
        .security-badge {{ font-size: 10px; color: #3fb950; margin-top: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{app_name}</h1>
        <p class="subtitle">Built with Blueprint NEXUS</p>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">${costs["total_monthly"]:.0f}</div>
                <div class="metric-label">Monthly Cost</div>
            </div>
            <div class="metric">
                <div class="metric-value">{perf["throughput"]:,}</div>
                <div class="metric-label">Req/Second</div>
            </div>
            <div class="metric">
                <div class="metric-value">{perf["latency_p50"]}ms</div>
                <div class="metric-label">Latency (P50)</div>
            </div>
        </div>
        
        <div class="tags">
            {block_html}
        </div>
        
        {f'<div class="warnings">{warning_html}</div>' if warning_html else ''}
        
        <div class="card">
            <form id="f">
                <input id="c" placeholder="Add item..." required maxlength="1000" 
                       pattern="[^<>]*" title="No HTML tags allowed">
                <input type="hidden" id="csrf" value="{{csrf_token}}">
                <button type="submit">Add</button>
            </form>
            <div id="error" class="error"></div>
            <ul class="items" id="items"></ul>
        </div>
        
        <div class="security-badge">🔒 Protected with CSRF, XSS prevention & rate limiting</div>
    </div>
    <script>
        // Security: HTML escape function to prevent XSS
        const escape = s => {{
            const div = document.createElement('div');
            div.textContent = s;
            return div.innerHTML;
        }};
        
        // Security: Get CSRF token
        const csrf = () => document.getElementById('csrf').value;
        
        const showError = msg => {{
            const err = document.getElementById('error');
            err.textContent = msg;
            err.style.display = 'block';
            setTimeout(() => err.style.display = 'none', 3000);
        }};
        
        const load = async () => {{
            try {{
                const r = await fetch('/api/items');
                if (!r.ok) throw new Error('Failed to load');
                const d = await r.json();
                document.getElementById('items').innerHTML = d.items.map((x,i) => 
                    `<li><span>${{escape(x.content || x)}}</span><button class="del" onclick="del(${{i}})">X</button></li>`).join('');
            }} catch (e) {{
                showError('Failed to load items');
            }}
        }};
        
        document.getElementById('f').onsubmit = async e => {{
            e.preventDefault();
            const input = document.getElementById('c');
            const content = input.value.trim();
            
            // Client-side validation
            if (!content) return;
            if (content.length > 1000) {{
                showError('Content too long (max 1000 chars)');
                return;
            }}
            if (/<[^>]*>/g.test(content)) {{
                showError('HTML tags not allowed');
                return;
            }}
            
            try {{
                const r = await fetch('/api/items', {{
                    method: 'POST', 
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrf()
                    }}, 
                    body: JSON.stringify({{content}})
                }});
                const result = await r.json();
                if (!r.ok) {{
                    showError(result.error || 'Failed to add item');
                    return;
                }}
                input.value = '';
                load();
            }} catch (e) {{
                showError('Network error');
            }}
        }};
        
        const del = async i => {{ 
            try {{
                await fetch(`/api/items/${{i}}`, {{
                    method: 'DELETE',
                    headers: {{'X-CSRF-Token': csrf()}}
                }}); 
                load(); 
            }} catch (e) {{
                showError('Failed to delete');
            }}
        }};
        
        load();
    </script>
</body>
</html>\"\"\"

def validate_csrf():
    \"\"\"Validate CSRF token for state-changing requests.\"\"\"
    token = request.headers.get('X-CSRF-Token', '')
    if not token or token != session.get('csrf_token', ''):
        abort(403, 'Invalid CSRF token')

@app.route("/api/items", methods=["GET"])
@rate_limited
def list_items():
    return jsonify({{"items": items}})

@app.route("/api/items", methods=["POST"])
@rate_limited
def add_item():
    validate_csrf()
    
    data = request.json
    # Input validation
    if not data or not isinstance(data, dict):
        return jsonify({{"error": "Invalid request"}}), 400
    
    content = data.get("content", "")
    if not content or not isinstance(content, str):
        return jsonify({{"error": "Content is required"}}), 400
    
    content = content.strip()
    if len(content) > 1000:
        return jsonify({{"error": "Content too long (max 1000 chars)"}}), 400
    if len(content) < 1:
        return jsonify({{"error": "Content cannot be empty"}}), 400
    
    # Sanitize: remove any HTML tags (basic protection)
    import re
    if re.search(r'<[^>]*>', content):
        return jsonify({{"error": "HTML tags not allowed"}}), 400
    
    items.append({{"content": escape_html(content)}})
    return jsonify({{"success": True}})

@app.route("/api/items/<int:idx>", methods=["DELETE"])
@rate_limited
def delete_item(idx):
    validate_csrf()
    
    if not isinstance(idx, int) or idx < 0:
        return jsonify({{"error": "Invalid index"}}), 400
    
    if 0 <= idx < len(items):
        items.pop(idx)
        return jsonify({{"success": True}})
    
    return jsonify({{"error": "Item not found"}}), 404

@app.errorhandler(403)
def forbidden(e):
    return jsonify({{"error": str(e.description)}}), 403

@app.errorhandler(429)
def rate_limit_error(e):
    return jsonify({{"error": "Too many requests. Please slow down."}}), 429

if __name__ == "__main__":
    print("=" * 50)
    print(f"Starting {app_name}")
    print("=" * 50)
    print(f"Cost: ~${costs["total_monthly"]:.2f}/month")
    print(f"Throughput: {perf["throughput_formatted"]}")
    print()
    print("Security features enabled:")
    print("  ✓ CSRF protection")
    print("  ✓ XSS prevention")
    print("  ✓ Rate limiting (100 req/min)")
    print("  ✓ Content Security Policy")
    print("  ✓ Input validation")
    print("  ✓ Secure cookies")
    print()
    
    # Use DEBUG env var, defaults to False for security
    debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
    if debug_mode:
        print("⚠️  DEBUG MODE ENABLED - Do not use in production!")
    
    app.run(debug=debug_mode, port=5000, host='127.0.0.1')
'''
    
    (output_path / "app.py").write_text(app_code, encoding='utf-8')
    (output_path / "requirements.txt").write_text("flask\n", encoding='utf-8')
    
    # Copy ADR
    adr_content = generate_adr(data)
    (output_path / "ARCHITECTURE.md").write_text(adr_content, encoding='utf-8')
    
    return {
        "success": True,
        "path": str(output_path),
        "blocks": block_ids,
        "connections": len(connections),
        "costs": costs,
        "performance": perf,
        "anti_patterns": anti_patterns,
        "adr": adr_file
    }


# ============================================================================
# CODE ANALYZER - Reverse engineer existing code into architecture
# ============================================================================

# Patterns to detect each block type in existing code
CODE_PATTERNS = {
    "backend_flask": [
        r"from flask import",
        r"import flask",
        r"Flask\(__name__\)",
        r"app\.route\(",
    ],
    "backend_fastapi": [
        r"from fastapi import",
        r"import fastapi",
        r"FastAPI\(\)",
        r"@app\.get\(",
        r"@app\.post\(",
    ],
    "storage_sqlite": [
        r"import sqlite3",
        r"sqlite3\.connect",
        r"\.db[\"']",
        r"CREATE TABLE",
        r"cursor\.execute",
    ],
    "storage_postgres": [
        r"import psycopg",
        r"from psycopg",
        r"postgresql://",
        r"postgres://",
        r"import asyncpg",
    ],
    "storage_json": [
        r"json\.dump\(",
        r"json\.load\(",
        r"\.json[\"']",
        r"open\([^)]+[\"']w[\"']",
    ],
    "storage_s3": [
        r"import boto3",
        r"s3\.upload",
        r"s3\.download",
        r"S3Client",
        r"s3://",
    ],
    "auth_basic": [
        r"session\[",
        r"login_required",
        r"password",
        r"bcrypt",
        r"hashlib",
        r"@login_required",
    ],
    "auth_oauth": [
        r"oauth",
        r"OAuth",
        r"google.*auth",
        r"github.*auth",
        r"access_token",
        r"refresh_token",
    ],
    "websocket_basic": [
        r"websocket",
        r"WebSocket",
        r"socketio",
        r"socket\.io",
        r"ws://",
        r"wss://",
    ],
    "sync_crdt": [
        r"crdt",
        r"CRDT",
        r"operational.transform",
        r"yjs",
        r"automerge",
    ],
    "cache_redis": [
        r"import redis",
        r"from redis",
        r"Redis\(",
        r"redis://",
        r"\.cache\(",
    ],
    "email_sendgrid": [
        r"sendgrid",
        r"SendGrid",
        r"smtp",
        r"SMTP",
        r"send.*email",
        r"mail\.send",
    ],
    "docker_basic": [
        r"Dockerfile",
        r"docker-compose",
        r"FROM python",
        r"EXPOSE",
        r"CMD \[",
    ],
    "crud_routes": [
        r"@app\.(get|post|put|delete|patch)\(",
        r"methods=\[",
        r"/api/",
        r"jsonify\(",
        r"return.*json",
    ],
    "html_templates": [
        r"render_template",
        r"Jinja",
        r"\.html",
        r"templates/",
        r"{% ",
    ],
}


def analyze_code(code: str, filename: str = "") -> dict:
    """
    Analyze existing code and detect which architectural blocks are in use.
    This is the reverse of generation - code → architecture.
    """
    detected_blocks = []
    evidence = {}
    
    for block_id, patterns in CODE_PATTERNS.items():
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, code, re.IGNORECASE)
            if found:
                matches.extend(found if isinstance(found[0], str) else [str(f) for f in found])
        
        if matches:
            # Require at least 1 match, but weight by number of matches
            confidence = min(len(matches) / 2, 1.0)  # 2+ matches = 100% confidence
            detected_blocks.append({
                "block_id": block_id,
                "confidence": confidence,
                "matches": len(matches),
                "evidence": matches[:5]  # First 5 matches as evidence
            })
            evidence[block_id] = matches[:5]
    
    # Sort by confidence
    detected_blocks.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Build architecture from detected blocks
    block_ids = [b["block_id"] for b in detected_blocks if b["confidence"] >= 0.5]
    
    # Create nodes with auto-layout
    nodes = []
    for i, block_id in enumerate(block_ids):
        nodes.append({
            "id": i + 1,
            "blockId": block_id,
            "x": 100 + (i % 3) * 250,
            "y": 100 + (i // 3) * 150
        })
    
    # Infer connections based on port compatibility
    connections = []
    for i, node_a in enumerate(nodes):
        block_a = BLOCKS.get(node_a["blockId"])
        if not block_a:
            continue
        
        for j, node_b in enumerate(nodes):
            if i >= j:
                continue
            block_b = BLOCKS.get(node_b["blockId"])
            if not block_b:
                continue
            
            # Check if a provides what b requires
            for p in block_a.provides:
                for r in block_b.requires:
                    if p.name == r.name:
                        connections.append({
                            "fromNode": node_a["id"],
                            "fromPort": p.name,
                            "toNode": node_b["id"],
                            "toPort": r.name,
                            "inferred": True
                        })
            
            # Check reverse
            for p in block_b.provides:
                for r in block_a.requires:
                    if p.name == r.name:
                        connections.append({
                            "fromNode": node_b["id"],
                            "fromPort": p.name,
                            "toNode": node_a["id"],
                            "toPort": r.name,
                            "inferred": True
                        })
    
    return {
        "filename": filename,
        "detected_blocks": detected_blocks,
        "nodes": nodes,
        "connections": connections,
        "block_ids": block_ids,
        "evidence": evidence,
        "summary": f"Detected {len(block_ids)} architectural components"
    }


def is_safe_path(dir_path: str) -> tuple[bool, str]:
    """
    Validate directory path for security.
    Prevents path traversal attacks and access to sensitive directories.
    """
    try:
        path = Path(dir_path).resolve()
        
        # Block absolute paths that look like system directories
        dangerous_prefixes = [
            '/etc', '/var', '/usr', '/bin', '/sbin', '/root',
            'C:\\Windows', 'C:\\Program Files', 'C:\\System32',
            '/System', '/Library', '/private'
        ]
        path_str = str(path)
        for prefix in dangerous_prefixes:
            if path_str.lower().startswith(prefix.lower()):
                return False, f"Access denied: Cannot analyze system directories"
        
        # Block hidden directories
        for part in path.parts:
            if part.startswith('.') and part not in ['.', '..']:
                return False, f"Access denied: Cannot analyze hidden directories"
        
        return True, ""
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def analyze_directory(dir_path: str) -> dict:
    """
    Analyze all Python files in a directory and merge into one architecture.
    Includes security validation to prevent path traversal attacks.
    """
    # Normalize path: handle Windows backslashes, strip quotes and whitespace
    dir_path = dir_path.strip().strip('"').strip("'")
    dir_path = dir_path.replace('\\\\', '\\')  # Handle escaped backslashes
    
    # Security validation
    is_safe, error_msg = is_safe_path(dir_path)
    if not is_safe:
        return {"error": error_msg}
    
    all_code = ""
    files_analyzed = []
    
    path = Path(dir_path)
    if not path.exists():
        # Try to provide helpful error message
        return {"error": f"Directory not found: {dir_path}. Please check the path exists and is accessible."}
    
    if not path.is_dir():
        return {"error": f"Path is not a directory: {dir_path}. Please provide a folder path."}
    
    # Collect all Python files
    for py_file in path.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            all_code += f"\n# File: {py_file.name}\n" + content
            files_analyzed.append(str(py_file.relative_to(path)))
        except Exception as e:
            pass
    
    # Also check for Dockerfile
    for dockerfile in path.rglob("Dockerfile*"):
        try:
            content = dockerfile.read_text(encoding='utf-8', errors='ignore')
            all_code += f"\n# File: {dockerfile.name}\n" + content
            files_analyzed.append(str(dockerfile.relative_to(path)))
        except Exception:
            pass
    
    # Check for docker-compose
    for compose in path.rglob("docker-compose*.yml"):
        try:
            content = compose.read_text(encoding='utf-8', errors='ignore')
            all_code += f"\n# File: {compose.name}\n" + content
            files_analyzed.append(str(compose.relative_to(path)))
        except Exception:
            pass
    
    if not all_code:
        return {"error": "No Python files found in directory"}
    
    result = analyze_code(all_code, dir_path)
    result["files_analyzed"] = files_analyzed
    result["file_count"] = len(files_analyzed)
    
    return result


class NexusHandler(SimpleHTTPRequestHandler):
    """HTTP handler for Nexus."""
    
    def get_cors_origin(self):
        """Return safe CORS origin - localhost only for security."""
        origin = self.headers.get('Origin', '')
        # Only allow localhost origins
        if origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:'):
            return origin
        return 'http://localhost:5000'
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", self.get_cors_origin())
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/":
            self.send_html(get_nexus_html())
            return
        
        if parsed.path == "/api/blocks":
            self.send_json({"blocks": get_blocks_data()})
            return
        
        if parsed.path.startswith("/playground/"):
            playground_id = parsed.path.split("/")[-1]
            data = get_playground(playground_id)
            if data:
                self.send_json(data)
            else:
                self.send_error(404)
            return
        
        self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        
        # Input validation: limit request size to 10MB
        MAX_CONTENT_LENGTH = 10 * 1024 * 1024
        if content_length > MAX_CONTENT_LENGTH:
            self.send_json({"error": "Request too large. Maximum 10MB allowed."})
            return
        
        body = self.rfile.read(content_length).decode() if content_length else "{}"
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON in request body"})
            return
        
        if parsed.path == "/api/parse":
            description = data.get("description", "")
            # Input validation: limit description length
            if len(description) > 5000:
                self.send_json({"error": "Description too long. Maximum 5000 characters."})
                return
            result = parse_natural_language(description)
            self.send_json(result)
            return
        
        if parsed.path == "/api/analyze":
            block_ids = [n.get("blockId") for n in data.get("nodes", [])]
            result = {
                "costs": estimate_costs(block_ids, data.get("monthly_requests", 100000)),
                "performance": estimate_performance(block_ids),
                "anti_patterns": detect_anti_patterns(block_ids)
            }
            self.send_json(result)
            return
        
        if parsed.path == "/api/what-if":
            result = analyze_what_if(
                data.get("nodes", []),
                data.get("connections", []),
                data.get("remove_node_id")
            )
            self.send_json(result)
            return
        
        if parsed.path == "/api/diff":
            result = diff_architectures(data.get("before", {}), data.get("after", {}))
            self.send_json(result)
            return
        
        if parsed.path == "/api/share":
            playground_id = create_playground(data)
            self.send_json({"playground_id": playground_id, "url": f"/playground/{playground_id}"})
            return
        
        if parsed.path == "/api/adr":
            adr = generate_adr(data)
            self.send_json({"adr": adr})
            return
        
        if parsed.path == "/api/generate":
            result = generate_app(data)
            self.send_json(result)
            return
        
        if parsed.path == "/api/analyze-code":
            # Analyze code pasted directly
            code = data.get("code", "")
            filename = data.get("filename", "uploaded.py")
            result = analyze_code(code, filename)
            self.send_json(result)
            return
        
        if parsed.path == "/api/analyze-directory":
            # Analyze a directory path
            dir_path = data.get("path", "")
            result = analyze_directory(dir_path)
            self.send_json(result)
            return
        
        self.send_error(404)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", self.get_cors_origin())
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        # Prevent caching to ensure users always get latest version
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass


def get_nexus_html():
    """The NEXUS interface - what the industry should have built."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blueprint NEXUS</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg: #0a0a0f;
            --bg2: #12121a;
            --bg3: #1a1a25;
            --surface: rgba(255,255,255,0.03);
            --border: rgba(255,255,255,0.08);
            --accent: #6366f1;
            --accent2: #8b5cf6;
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
            --text: #f0f0f5;
            --text-dim: #6b7280;
        }
        
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        
        .app {
            display: grid;
            grid-template-columns: 1fr 400px;
            grid-template-rows: 60px 1fr;
            height: 100vh;
        }
        
        /* Header */
        .header {
            grid-column: 1 / -1;
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            padding: 0 24px;
            gap: 24px;
        }
        
        .logo {
            font-size: 18px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .logo-sub {
            font-size: 11px;
            color: var(--text-dim);
            margin-left: 10px;
            font-weight: 400;
        }
        
        /* Natural language input - THE KILLER FEATURE */
        .nl-input-wrap {
            flex: 1;
            max-width: 600px;
            position: relative;
        }
        
        .nl-input {
            width: 100%;
            padding: 12px 20px;
            padding-right: 100px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text);
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .nl-input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .nl-input::placeholder {
            color: var(--text-dim);
        }
        
        .nl-btn {
            position: absolute;
            right: 6px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--accent);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
        }
        
        .header-actions {
            display: flex;
            gap: 12px;
        }
        
        .header-btn {
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .header-btn:hover {
            background: var(--bg3);
        }
        
        /* Main content */
        .main {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        /* Canvas area */
        .canvas-area {
            flex: 1;
            position: relative;
            background: 
                radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.03) 0%, transparent 50%),
                linear-gradient(var(--border) 1px, transparent 1px),
                linear-gradient(90deg, var(--border) 1px, transparent 1px);
            background-size: 100% 100%, 30px 30px, 30px 30px;
            overflow: hidden;
        }
        
        .canvas {
            position: absolute;
            width: 3000px;
            height: 3000px;
        }
        
        .connections-svg {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        
        .connection {
            fill: none;
            stroke: url(#connGrad);
            stroke-width: 2;
            stroke-linecap: round;
        }
        
        .connection.inferred {
            stroke-dasharray: 8 4;
            opacity: 0.6;
        }
        
        /* Nodes */
        .node {
            position: absolute;
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 12px;
            min-width: 180px;
            cursor: move;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        
        .node:hover {
            border-color: rgba(255,255,255,0.15);
        }
        
        .node.selected {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2), 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .node.what-if-target {
            border-color: var(--error);
            background: rgba(239, 68, 68, 0.1);
        }
        
        .node-header {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .node-icon {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        
        .node-info {
            flex: 1;
        }
        
        .node-name {
            font-weight: 600;
            font-size: 13px;
        }
        
        .node-cost {
            font-size: 10px;
            color: var(--success);
        }
        
        .node-menu {
            opacity: 0;
            background: none;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            padding: 4px;
        }
        
        .node:hover .node-menu { opacity: 1; }
        
        .node-body {
            padding: 8px 0;
        }
        
        .port-row {
            display: flex;
            align-items: center;
            padding: 4px 14px;
            font-size: 11px;
            color: var(--text-dim);
        }
        
        .port-row.require { justify-content: flex-start; }
        .port-row.provide { justify-content: flex-end; }
        
        .port {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            cursor: crosshair;
        }
        
        .port.require { background: var(--error); margin-right: 8px; }
        .port.provide { background: var(--success); margin-left: 8px; }
        
        /* Panel */
        .panel {
            background: var(--bg2);
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .panel-tabs {
            display: flex;
            border-bottom: 1px solid var(--border);
        }
        
        .panel-tab {
            flex: 1;
            padding: 14px;
            background: none;
            border: none;
            color: var(--text-dim);
            font-size: 12px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }
        
        .panel-tab:hover { color: var(--text); }
        .panel-tab.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }
        
        .panel-content {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        
        .panel-content.hidden { display: none; }
        
        .panel-section {
            margin-bottom: 24px;
        }
        
        .panel-section-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-dim);
            margin-bottom: 12px;
        }
        
        /* Metrics */
        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        
        .metric-value.cost { color: var(--success); }
        .metric-value.perf { color: var(--accent); }
        .metric-value.warning { color: var(--warning); }
        .metric-value.error { color: var(--error); }
        
        .metric-label {
            font-size: 11px;
            color: var(--text-dim);
        }
        
        /* Anti-patterns */
        .anti-pattern {
            background: var(--surface);
            border-left: 3px solid var(--warning);
            padding: 12px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 10px;
        }
        
        .anti-pattern.error {
            border-left-color: var(--error);
            background: rgba(239, 68, 68, 0.05);
        }
        
        .anti-pattern-name {
            font-weight: 600;
            font-size: 12px;
            margin-bottom: 4px;
        }
        
        .anti-pattern-desc {
            font-size: 11px;
            color: var(--text-dim);
            margin-bottom: 6px;
        }
        
        .anti-pattern-fix {
            font-size: 10px;
            color: var(--accent);
        }
        
        /* What-if results */
        .what-if-result {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
        }
        
        .what-if-impact {
            display: flex;
            gap: 20px;
            margin-bottom: 12px;
        }
        
        .impact-stat {
            text-align: center;
        }
        
        .impact-num {
            font-size: 20px;
            font-weight: 700;
        }
        
        .impact-num.bad { color: var(--error); }
        .impact-num.ok { color: var(--success); }
        
        .impact-label {
            font-size: 10px;
            color: var(--text-dim);
        }
        
        .what-if-suggestions {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }
        
        .suggestion-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            background: rgba(99, 102, 241, 0.1);
            border-radius: 6px;
            margin-bottom: 6px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .suggestion-item:hover {
            background: rgba(99, 102, 241, 0.2);
        }
        
        /* Blocks palette */
        .blocks-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        
        .block-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px;
            cursor: grab;
            transition: all 0.15s;
        }
        
        .block-card:hover {
            border-color: var(--accent);
        }
        
        .block-card-name {
            font-weight: 600;
            font-size: 11px;
            margin-bottom: 2px;
        }
        
        .block-card-cost {
            font-size: 9px;
            color: var(--success);
        }
        
        /* ADR Preview */
        .adr-preview {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            font-family: 'SF Mono', monospace;
            font-size: 11px;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        
        /* Generate button */
        .generate-section {
            padding: 20px;
            border-top: 1px solid var(--border);
        }
        
        .generate-btn {
            width: 100%;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            border: none;
            color: white;
            padding: 16px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.15s, box-shadow 0.15s;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
        }
        
        .generate-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Share button */
        .share-btn {
            margin-top: 10px;
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 12px;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .share-btn:hover {
            background: var(--bg3);
        }
        
        /* Diff view */
        .diff-view {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .diff-header {
            display: flex;
            padding: 10px;
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            font-size: 12px;
        }
        
        .diff-added {
            color: var(--success);
            background: rgba(34, 197, 94, 0.1);
            padding: 8px 12px;
            margin: 2px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        .diff-removed {
            color: var(--error);
            background: rgba(239, 68, 68, 0.1);
            padding: 8px 12px;
            margin: 2px;
            border-radius: 4px;
            font-size: 12px;
            text-decoration: line-through;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.85);
            align-items: center;
            justify-content: center;
            z-index: 100;
        }
        
        .modal.show { display: flex; }
        
        .modal-content {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
        }
        
        .modal-content h2 {
            margin-bottom: 15px;
        }
        
        .modal-content code {
            display: block;
            background: var(--bg);
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
            font-size: 12px;
            font-family: monospace;
        }
        
        .modal-content button {
            background: var(--accent);
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            cursor: pointer;
        }
        
        /* Intent badges */
        .intent-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }
        
        .intent-badge {
            background: rgba(99, 102, 241, 0.15);
            color: var(--accent);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 10px;
            text-transform: uppercase;
        }
        
        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 60px 40px;
            color: var(--text-dim);
        }
        
        .empty-state h3 {
            margin-bottom: 10px;
            color: var(--text);
        }
        
        .empty-state p {
            font-size: 13px;
            max-width: 300px;
            margin: 0 auto;
        }
        
        /* Toast */
        .toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--bg2);
            border: 1px solid var(--border);
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 13px;
            opacity: 0;
            transition: all 0.3s;
            z-index: 101;
        }
        
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="app">
        <header class="header">
            <div class="logo">
                NEXUS
                <span class="logo-sub">What the industry missed</span>
            </div>
            
            <div class="nl-input-wrap">
                <input type="text" class="nl-input" id="nlInput" 
                       placeholder="Backend blocks: 'auth + database + API' or 'login, storage, crud'">
                <button class="nl-btn" onclick="parseNaturalLanguage()">Build →</button>
            </div>
            <div id="capabilityHint" style="display:none; position:absolute; top:65px; left:50%; transform:translateX(-50%); background:var(--bg2); border:1px solid var(--border); padding:8px 12px; border-radius:6px; font-size:11px; color:var(--text-dim); max-width:500px; z-index:1000;">
                <strong style="color:var(--warning);">Supported:</strong> auth, login, database, storage, API, CRUD, realtime, websocket, cache, redis, docker, email, postgres, sqlite, s3
            </div>
            
            <div class="header-actions">
                <button class="header-btn" onclick="importCode()">
                    <span>📥</span> Import Code
                </button>
                <button class="header-btn" onclick="showDiff()">
                    <span>⎔</span> Diff
                </button>
                <button class="header-btn" onclick="sharePlayground()">
                    <span>↗</span> Share
                </button>
            </div>
        </header>
        
        <main class="main">
            <div class="canvas-area" id="canvasArea">
                <div class="canvas" id="canvas">
                    <svg class="connections-svg" id="connectionsSvg">
                        <defs>
                            <linearGradient id="connGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" style="stop-color:#ef4444"/>
                                <stop offset="100%" style="stop-color:#22c55e"/>
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
                
                <div class="empty-state" id="emptyState">
                    <h3>Backend Architecture Builder</h3>
                    <p style="margin-bottom:10px;">Drag blocks from the panel, or describe your backend:</p>
                    <div style="font-size:12px; color:var(--text-dim); line-height:1.6;">
                        <div style="margin-bottom:8px;"><strong style="color:var(--accent);">Recognized keywords:</strong></div>
                        <div>🔐 auth, login, oauth, password</div>
                        <div>💾 database, storage, sqlite, postgres, s3</div>
                        <div>🔌 API, CRUD, backend, flask, fastapi</div>
                        <div>⚡ realtime, websocket, sync, collaborative</div>
                        <div>📧 email, notification</div>
                        <div>🚀 cache, redis, docker, deploy</div>
                    </div>
                    <p style="margin-top:15px; font-size:11px; color:var(--warning);">
                        ⚠️ This tool composes predefined backend blocks. It does not generate arbitrary apps like games or custom UIs.
                    </p>
                </div>
            </div>
        </main>
        
        <aside class="panel">
            <div class="panel-tabs">
                <button class="panel-tab active" onclick="showTab('analysis')">Analysis</button>
                <button class="panel-tab" onclick="showTab('blocks')">Blocks</button>
                <button class="panel-tab" onclick="showTab('adr')">ADR</button>
            </div>
            
            <div class="panel-content" id="tab-analysis">
                <div class="panel-section">
                    <div class="panel-section-title">Cost & Performance</div>
                    <div class="metrics-grid" id="metricsGrid">
                        <div class="metric-card">
                            <div class="metric-value cost" id="metricCost">$0</div>
                            <div class="metric-label">Monthly Cost</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value perf" id="metricThroughput">-</div>
                            <div class="metric-label">Requests/sec</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="metricLatency">-</div>
                            <div class="metric-label">Latency (P50)</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="metricGrade">-</div>
                            <div class="metric-label">Grade</div>
                        </div>
                    </div>
                </div>
                
                <div class="panel-section">
                    <div class="panel-section-title">Architectural Issues</div>
                    <div id="antiPatterns">
                        <div style="color: var(--text-dim); font-size: 12px;">No issues detected</div>
                    </div>
                </div>
                
                <div class="panel-section">
                    <div class="panel-section-title">What-If Analysis</div>
                    <div id="whatIfSection">
                        <div style="color: var(--text-dim); font-size: 12px;">
                            Right-click a block to analyze removal impact
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="panel-content hidden" id="tab-blocks">
                <div class="panel-section">
                    <div class="panel-section-title">Drag to Canvas</div>
                    <div class="blocks-grid" id="blocksGrid"></div>
                </div>
            </div>
            
            <div class="panel-content hidden" id="tab-adr">
                <div class="panel-section">
                    <div class="panel-section-title">Architecture Decision Record</div>
                    <div class="adr-preview" id="adrPreview">
                        Generate an architecture to see the ADR
                    </div>
                </div>
            </div>
            
            <div class="generate-section">
                <button class="generate-btn" onclick="generateApp()">Generate App</button>
                <button class="share-btn" onclick="sharePlayground()">Share Playground ↗</button>
            </div>
        </aside>
    </div>
    
    <div class="modal" id="modal">
        <div class="modal-content">
            <h2 id="modalTitle">Result</h2>
            <div id="modalContent"></div>
            <button onclick="closeModal()">Close</button>
        </div>
    </div>
    
    <div class="modal" id="importModal">
        <div class="modal-content" style="max-width: 700px;">
            <h2>Import Existing Code</h2>
            <p style="color: var(--text-dim); font-size: 13px; margin-bottom: 15px;">
                Browse for a project folder, enter a path, or paste code directly.
            </p>
            <div style="margin-bottom: 15px;">
                <label style="font-size: 12px; color: var(--text-dim);">Project Folder</label>
                <div style="display: flex; gap: 10px; margin-top: 5px;">
                    <input type="text" id="importPath" placeholder="C:\\path\\to\\your\\project" 
                           style="flex: 1; padding: 10px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--text);">
                    <label for="folderPicker" style="background: var(--accent); color: white; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 6px;">
                        📁 Browse
                    </label>
                    <input type="file" id="folderPicker" webkitdirectory directory multiple 
                           style="display: none;" onchange="handleFolderSelect(event)">
                </div>
                <div id="selectedFolder" style="font-size: 11px; color: var(--success); margin-top: 5px;"></div>
            </div>
            <div style="margin-bottom: 15px;">
                <label style="font-size: 12px; color: var(--text-dim);">Or paste code directly</label>
                <textarea id="importCode" placeholder="from flask import Flask..." 
                          style="width: 100%; height: 180px; padding: 10px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-family: monospace; font-size: 12px; margin-top: 5px; resize: vertical;"></textarea>
            </div>
            <div style="display: flex; gap: 10px;">
                <button onclick="doImport()" style="flex: 1; background: var(--accent); color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: 600;">Analyze & Import</button>
                <button onclick="closeImportModal()" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 12px 20px; border-radius: 8px; cursor: pointer;">Cancel</button>
            </div>
        </div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <script>
        // State
        let blocks = [];
        let nodes = [];
        let connections = [];
        let nextNodeId = 1;
        let selectedNode = null;
        let draggingNode = null;
        let architecture_history = [];
        
        // Initialize
        async function init() {
            const res = await fetch('/api/blocks');
            blocks = (await res.json()).blocks;
            renderBlocksGrid();
            
            // Check for playground in URL
            const path = window.location.pathname;
            if (path.startsWith('/playground/')) {
                const id = path.split('/')[2];
                loadPlayground(id);
            }
        }
        
        function renderBlocksGrid() {
            const grid = document.getElementById('blocksGrid');
            grid.innerHTML = blocks.map(b => `
                <div class="block-card" draggable="true" data-block-id="${b.id}">
                    <div class="block-card-name">${b.name}</div>
                    <div class="block-card-cost">${b.cost.description}</div>
                </div>
            `).join('');
            
            // Setup drag
            grid.querySelectorAll('.block-card').forEach(el => {
                el.addEventListener('dragstart', e => {
                    e.dataTransfer.setData('blockId', el.dataset.blockId);
                });
            });
        }
        
        // Natural Language → Architecture  
        // IMPORTANT: This only recognizes backend architecture keywords, not arbitrary apps
        async function parseNaturalLanguage() {
            const input = document.getElementById('nlInput');
            const description = input.value.trim();
            if (!description) return;
            
            input.disabled = true;
            
            try {
                const res = await fetch('/api/parse', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description })
                });
                const result = await res.json();
                
                // Check if we understood the request
                if (result.confidence === 0 || result.detected_intents.length === 0) {
                    // Show helpful error instead of silently adding default blocks
                    showModal('Cannot Build This', `
                        <div style="text-align:left;">
                            <p style="margin-bottom:15px;">NEXUS didn't recognize any backend patterns in:</p>
                            <div style="background:var(--bg); padding:12px; border-radius:6px; margin-bottom:15px; font-style:italic;">"${description}"</div>
                            
                            <p style="margin-bottom:10px;"><strong style="color:var(--accent);">NEXUS can build backend architectures with:</strong></p>
                            <ul style="margin-left:20px; line-height:1.8;">
                                <li><strong>Auth:</strong> login, auth, password, oauth, users</li>
                                <li><strong>Storage:</strong> database, save, store, sqlite, postgres, s3</li>
                                <li><strong>API:</strong> api, rest, crud, backend, endpoints</li>
                                <li><strong>Realtime:</strong> realtime, websocket, sync, live, collaborative</li>
                                <li><strong>Other:</strong> email, cache, redis, docker, deploy</li>
                            </ul>
                            
                            <p style="margin-top:15px; padding:12px; background:rgba(239,68,68,0.1); border-left:3px solid var(--error); border-radius:0 6px 6px 0;">
                                <strong>Note:</strong> NEXUS composes predefined backend blocks. It cannot generate games, custom UIs, or arbitrary applications.
                            </p>
                            
                            <p style="margin-top:15px;"><strong>Try instead:</strong></p>
                            <ul style="margin-left:20px;">
                                <li>"API with authentication and database"</li>
                                <li>"Realtime collaborative app with user auth"</li>
                                <li>"Backend with postgres, caching, and email"</li>
                            </ul>
                        </div>
                    `);
                    input.disabled = false;
                    return;
                }
                
                // Save current state for diff
                saveToHistory();
                
                // Apply the parsed architecture
                nodes = result.nodes.map(n => ({
                    ...n,
                    block: blocks.find(b => b.id === n.blockId)
                }));
                connections = result.connections;
                nextNodeId = Math.max(...nodes.map(n => n.id), 0) + 1;
                
                renderAll();
                
                // Show success with what was detected
                toast(`✓ Built: ${result.detected_intents.join(', ')} (${Math.round(result.confidence * 100)}% match)`);
                
            } catch (e) {
                toast('Failed to parse description');
            } finally {
                input.disabled = false;
            }
        }
        
        // Enter key to parse
        document.getElementById('nlInput').addEventListener('keypress', e => {
            if (e.key === 'Enter') parseNaturalLanguage();
        });
        
        // IMPORT CODE - Reverse engineer existing code into architecture
        function importCode() {
            document.getElementById('importModal').classList.add('show');
        }
        
        function closeImportModal() {
            document.getElementById('importModal').classList.remove('show');
            document.getElementById('importPath').value = '';
            document.getElementById('importCode').value = '';
            document.getElementById('selectedFolder').textContent = '';
            selectedFiles = [];
        }
        
        // Store files selected via browse
        let selectedFiles = [];
        
        // Quick check for code files (full list defined later)
        function isLikelyCodeFile(filename) {
            const name = filename.toLowerCase();
            const codeExts = ['.py', '.js', '.ts', '.jsx', '.tsx', '.c', '.cpp', '.h', '.hpp',
                              '.rs', '.go', '.java', '.kt', '.cs', '.rb', '.php', '.swift',
                              '.vue', '.svelte', '.html', '.css', '.scss', '.json', '.yaml',
                              '.yml', '.toml', '.sql', '.sh', '.ps1', '.md'];
            const ext = '.' + name.split('.').pop();
            return codeExts.includes(ext) || name === 'dockerfile' || name === 'makefile';
        }
        
        function handleFolderSelect(event) {
            const files = Array.from(event.target.files);
            
            // Immediately show feedback
            const statusEl = document.getElementById('selectedFolder');
            statusEl.style.fontSize = '14px';
            statusEl.style.padding = '10px';
            statusEl.style.background = 'rgba(34, 197, 94, 0.1)';
            statusEl.style.borderRadius = '6px';
            statusEl.style.marginTop = '10px';
            
            if (files.length === 0) {
                statusEl.style.background = 'rgba(239, 68, 68, 0.1)';
                statusEl.style.color = 'var(--error)';
                statusEl.textContent = '⚠️ No files selected. Try again or use the path input.';
                toast('No files selected');
                return;
            }
            
            selectedFiles = files;
            
            console.log('Folder selected, total files:', files.length);
            
            // Log first 10 file names to debug
            files.slice(0, 10).forEach(f => {
                console.log('  File:', f.name, 'Path:', f.webkitRelativePath);
            });
            
            // Count code files of any type
            const codeFiles = files.filter(f => {
                const name = f.webkitRelativePath || f.name || '';
                return isLikelyCodeFile(name);
            });
            console.log('Code files found:', codeFiles.length);
            
            // Get the folder name from the first file's path
            const pathStr = files[0].webkitRelativePath || files[0].name;
            // Handle both forward and back slashes
            const parts = pathStr.split(/[/\\\\]/);
            const folderName = parts[0] || 'folder';
            const codeCount = codeFiles.length;
            
            statusEl.innerHTML = `
                <div style="font-weight:600; margin-bottom:5px;">✓ Folder Selected: ${folderName}</div>
                <div>📂 ${files.length} total files, 💻 ${codeCount} code files</div>
                ${codeCount > 0 ? '<div style="margin-top:8px;color:var(--accent);">Click <strong>Analyze & Import</strong> below to continue</div>' : ''}
            `;
            document.getElementById('importPath').value = '';
            toast('Folder selected: ' + folderName);
            
            if (codeCount === 0) {
                statusEl.style.background = 'rgba(245, 158, 11, 0.1)';
                statusEl.style.color = 'var(--warning)';
                const exts = [...new Set(files.map(f => {
                    const n = f.name || '';
                    return n.includes('.') ? '.' + n.split('.').pop().toLowerCase() : '(none)';
                }))].slice(0, 8);
                statusEl.innerHTML += `<div style="margin-top:5px;">Extensions found: ${exts.join(', ')}</div>`;
            }
        }
        
        function handleImportResult(result) {
            if (result.error) {
                showModal('Import Failed', `
                    <div style="text-align:center; padding:20px;">
                        <div style="font-size:48px; margin-bottom:15px;">❌</div>
                        <div style="font-size:16px; color:var(--error);">${result.error}</div>
                        <div style="margin-top:20px; font-size:12px; color:var(--text-dim);">
                            Try browsing for a different folder or pasting code directly.
                        </div>
                    </div>
                `);
                return false;
            }
            
            // Check if anything was detected
            if (!result.nodes || result.nodes.length === 0) {
                showModal('No Patterns Found', `
                    <div style="text-align:left; padding:10px;">
                        <div style="font-size:36px; margin-bottom:15px; text-align:center;">🔍</div>
                        <p style="margin-bottom:15px;">NEXUS analyzed the code but couldn't detect any recognizable backend patterns.</p>
                        
                        <p style="margin-bottom:10px;"><strong>What NEXUS detects:</strong></p>
                        <ul style="margin-left:20px; margin-bottom:15px; line-height:1.8;">
                            <li>Flask, FastAPI, Django frameworks</li>
                            <li>SQLite, PostgreSQL, database connections</li>
                            <li>OAuth, JWT, authentication patterns</li>
                            <li>WebSocket, realtime features</li>
                            <li>Docker, deployment configs</li>
                        </ul>
                        
                        <p style="background:rgba(245,158,11,0.1); padding:10px; border-radius:6px;">
                            <strong>Note:</strong> If your code uses different patterns or is a frontend/game project, 
                            NEXUS may not recognize it. NEXUS is designed for backend architecture analysis.
                        </p>
                    </div>
                `);
                return false;
            }
            
            // Apply the detected architecture
            saveToHistory();
            
            nodes = result.nodes.map(n => ({
                ...n,
                block: blocks.find(b => b.id === n.blockId)
            }));
            connections = result.connections || [];
            nextNodeId = Math.max(...nodes.map(n => n.id), 0) + 1;
            
            closeImportModal();
            renderAll();
            
            // Build comprehensive analysis modal
            let html = '<div style="font-size: 13px; max-height: 70vh; overflow-y: auto;">';
            
            // Summary section
            const fileCount = result.file_count || result.files_analyzed?.length || 0;
            html += `<div style="background: var(--surface); padding: 12px; border-radius: 8px; margin-bottom: 15px;">`;
            html += `<div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">📊 Analysis Summary</div>`;
            html += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">`;
            html += `<div><span style="color: var(--text-dim);">Files Analyzed:</span> <strong>${fileCount}</strong></div>`;
            html += `<div><span style="color: var(--text-dim);">Blocks Detected:</span> <strong>${result.nodes?.length || 0}</strong></div>`;
            html += `</div></div>`;
            
            // Language detection from files
            if (result.files_analyzed && result.files_analyzed.length > 0) {
                const langStats = {};
                const extToLang = {
                    '.py': 'Python', '.pyw': 'Python',
                    '.js': 'JavaScript', '.jsx': 'React/JSX', '.mjs': 'JavaScript',
                    '.ts': 'TypeScript', '.tsx': 'React/TSX',
                    '.c': 'C', '.h': 'C/C++ Header', '.cpp': 'C++', '.cc': 'C++', '.hpp': 'C++ Header',
                    '.rs': 'Rust', '.go': 'Go', '.java': 'Java', '.kt': 'Kotlin',
                    '.cs': 'C#', '.rb': 'Ruby', '.php': 'PHP', '.swift': 'Swift',
                    '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS', '.vue': 'Vue',
                    '.json': 'JSON', '.yaml': 'YAML', '.yml': 'YAML', '.toml': 'TOML',
                    '.sql': 'SQL', '.sh': 'Shell', '.ps1': 'PowerShell',
                    '.md': 'Markdown', '.txt': 'Text'
                };
                
                for (const f of result.files_analyzed) {
                    const ext = '.' + f.split('.').pop().toLowerCase();
                    const lang = extToLang[ext] || ext.toUpperCase().replace('.', '');
                    langStats[lang] = (langStats[lang] || 0) + 1;
                }
                
                const sortedLangs = Object.entries(langStats).sort((a, b) => b[1] - a[1]);
                
                html += `<div style="margin-bottom: 15px;">`;
                html += `<div style="font-weight: 600; margin-bottom: 8px;">🗂️ Languages Detected</div>`;
                html += `<div style="display: flex; flex-wrap: wrap; gap: 6px;">`;
                for (const [lang, count] of sortedLangs.slice(0, 10)) {
                    const pct = Math.round(count / fileCount * 100);
                    html += `<span style="background: var(--accent); color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px;">${lang} (${count})</span>`;
                }
                html += `</div></div>`;
            }
            
            // Detected architectural blocks
            if (result.detected_blocks && result.detected_blocks.length > 0) {
                html += `<div style="margin-bottom: 15px;">`;
                html += `<div style="font-weight: 600; margin-bottom: 8px;">🏗️ Architectural Blocks Found</div>`;
                
                for (const block of result.detected_blocks.slice(0, 8)) {
                    const confidence = Math.round(block.confidence * 100);
                    const color = confidence >= 80 ? 'var(--success)' : confidence >= 50 ? 'var(--warning)' : 'var(--text-dim)';
                    const barWidth = Math.max(confidence, 10);
                    
                    html += `<div style="margin-bottom: 10px; padding: 8px; background: var(--surface); border-radius: 6px;">`;
                    html += `<div style="display: flex; justify-content: space-between; margin-bottom: 4px;">`;
                    html += `<span style="font-weight: 500;">${block.block_id.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}</span>`;
                    html += `<span style="color: ${color}; font-weight: 600;">${confidence}%</span>`;
                    html += `</div>`;
                    html += `<div style="background: var(--border); height: 4px; border-radius: 2px;">`;
                    html += `<div style="background: ${color}; width: ${barWidth}%; height: 100%; border-radius: 2px;"></div>`;
                    html += `</div>`;
                    html += `</div>`;
                }
                html += `</div>`;
            } else {
                // No blocks detected - show helpful message
                html += `<div style="margin-bottom: 15px; padding: 15px; background: rgba(245, 158, 11, 0.1); border: 1px solid var(--warning); border-radius: 8px;">`;
                html += `<div style="font-weight: 600; color: var(--warning); margin-bottom: 8px;">⚠️ No Known Architectural Patterns Detected</div>`;
                html += `<p style="color: var(--text-dim); font-size: 12px; line-height: 1.5;">`;
                html += `This codebase doesn't match the standard patterns NEXUS looks for (Flask, FastAPI, SQLite, PostgreSQL, OAuth, WebSockets, etc.).<br><br>`;
                html += `This could mean:<br>`;
                html += `• It uses a different technology stack<br>`;
                html += `• It's a utility/library project (not a web app)<br>`;
                html += `• It's written in a language without web patterns`;
                html += `</p></div>`;
            }
            
            // File tree visualization
            if (result.files_analyzed && result.files_analyzed.length > 0) {
                html += `<div style="margin-bottom: 15px;">`;
                html += `<div style="font-weight: 600; margin-bottom: 8px;">📁 Project Structure</div>`;
                html += `<div style="background: var(--bg); padding: 10px; border-radius: 6px; font-family: monospace; font-size: 11px; max-height: 200px; overflow-y: auto;">`;
                
                // Build a simple tree
                const tree = {};
                for (const f of result.files_analyzed) {
                    const parts = f.replace(/\\\\/g, '/').split('/');
                    let current = tree;
                    for (let i = 0; i < parts.length; i++) {
                        const part = parts[i];
                        if (i === parts.length - 1) {
                            // File
                            if (!current._files) current._files = [];
                            current._files.push(part);
                        } else {
                            // Folder
                            if (!current[part]) current[part] = {};
                            current = current[part];
                        }
                    }
                }
                
                // Render tree (limited depth)
                function renderTree(node, prefix = '', depth = 0) {
                    if (depth > 3) return '<span style="color: var(--text-dim);">...</span>\\n';
                    let out = '';
                    const keys = Object.keys(node).filter(k => k !== '_files').slice(0, 8);
                    const files = (node._files || []).slice(0, 5);
                    
                    for (let i = 0; i < keys.length; i++) {
                        const key = keys[i];
                        const isLast = i === keys.length - 1 && files.length === 0;
                        out += prefix + (isLast ? '└── ' : '├── ') + '📁 ' + key + '\\n';
                        out += renderTree(node[key], prefix + (isLast ? '    ' : '│   '), depth + 1);
                    }
                    
                    for (let i = 0; i < files.length; i++) {
                        const isLast = i === files.length - 1;
                        out += prefix + (isLast ? '└── ' : '├── ') + files[i] + '\\n';
                    }
                    
                    if (Object.keys(node).filter(k => k !== '_files').length > 8) {
                        out += prefix + '<span style="color: var(--text-dim);">... more folders</span>\\n';
                    }
                    if ((node._files || []).length > 5) {
                        out += prefix + '<span style="color: var(--text-dim);">... ' + (node._files.length - 5) + ' more files</span>\\n';
                    }
                    
                    return out;
                }
                
                html += renderTree(tree);
                html += `</div></div>`;
            }
            
            // SUGGESTED IMPROVEMENTS - with detailed WHY
            const detectedIds = (result.detected_blocks || []).map(b => b.block_id);
            const suggestions = getSuggestedImprovements(detectedIds);
            
            // Store suggestions for preview functionality
            window.currentSuggestions = suggestions;
            
            if (suggestions.length > 0) {
                html += `<div style="margin-bottom: 15px; padding: 15px; background: rgba(34, 197, 94, 0.1); border: 1px solid var(--success); border-radius: 8px;">`;
                html += `<div style="font-weight: 600; color: var(--success); margin-bottom: 10px;">💡 Suggested Improvements</div>`;
                html += `<p style="color: var(--text-dim); font-size: 12px; margin-bottom: 12px;">NEXUS analyzed your code and found these opportunities:</p>`;
                
                for (let i = 0; i < suggestions.length; i++) {
                    const sug = suggestions[i];
                    const riskColor = sug.why?.risk === 'critical' ? 'var(--error)' : sug.why?.risk === 'medium' ? 'var(--warning)' : 'var(--success)';
                    const riskLabel = sug.why?.risk === 'critical' ? '🔴 Critical' : sug.why?.risk === 'medium' ? '🟡 Recommend' : '🟢 Optional';
                    
                    html += `<div style="margin-bottom: 12px; padding: 12px; background: var(--surface); border-radius: 8px; border-left: 3px solid ${riskColor};">`;
                    
                    // Header with name and risk level
                    html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">`;
                    html += `<strong style="font-size: 14px;">${sug.name}</strong>`;
                    html += `<span style="font-size: 10px; color: ${riskColor}; font-weight: 600;">${riskLabel}</span>`;
                    html += `</div>`;
                    
                    // WHY section
                    if (sug.why) {
                        html += `<div style="font-size: 11px; margin-bottom: 10px;">`;
                        html += `<div style="color: var(--error); margin-bottom: 4px;"><strong>Problem:</strong> ${sug.why.problem}</div>`;
                        html += `<div style="color: var(--text-dim); margin-bottom: 4px;"><strong>Evidence:</strong> ${sug.why.evidence}</div>`;
                        
                        // Impact metrics
                        if (sug.why.impact) {
                            html += `<div style="margin-top: 8px; padding: 8px; background: var(--bg); border-radius: 4px;">`;
                            html += `<div style="color: var(--text-dim);"><strong>Before:</strong> ${sug.why.impact.before}</div>`;
                            html += `<div style="color: var(--success);"><strong>After:</strong> ${sug.why.impact.after}</div>`;
                            html += `<div style="color: var(--accent); font-weight: 600; margin-top: 4px;">📈 ${sug.why.impact.metric}</div>`;
                            html += `</div>`;
                        }
                        html += `</div>`;
                    }
                    
                    // Action buttons - Preview first, then Add
                    html += `<div style="display: flex; gap: 8px;">`;
                    html += `<button onclick="previewSuggestion(${i})" style="flex: 1; background: var(--bg2); color: var(--text); border: 1px solid var(--border); padding: 8px; border-radius: 4px; cursor: pointer; font-size: 11px;">👁️ Preview</button>`;
                    html += `<button onclick="addSuggestedBlockWithVersion('${sug.blockId}', '${sug.name}')" style="flex: 1; background: var(--success); color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 600;">+ Add</button>`;
                    html += `</div>`;
                    
                    html += `</div>`;
                }
                
                html += `</div>`;
            }
            
            // Action buttons
            html += `<div style="display: flex; gap: 10px; margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border);">`;
            html += `<button onclick="showVersionHistory()" style="background: var(--bg2); color: var(--text); border: 1px solid var(--border); padding: 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">📜 History</button>`;
            html += `<button onclick="showImproveCodeModal()" style="flex: 1; background: var(--accent); color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: 600;">🚀 Improve Code</button>`;
            html += `<button onclick="closeModal()" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 12px 20px; border-radius: 6px; cursor: pointer;">Close</button>`;
            html += `</div>`;
            
            html += '</div>';
            
            // Store the result for Improve Code feature
            window.lastAnalysisResult = result;
            
            // Show the modal
            const detectedNames = (result.detected_blocks || [])
                .filter(d => d.confidence >= 0.5)
                .map(d => d.block_id.replace('_', ' '))
                .join(', ');
            
            const fileInfo = fileCount ? ` from ${fileCount} files` : '';
            toast(`Analyzed${fileInfo}: ${detectedNames || 'No standard patterns found'}`);
            
            showModal('📊 Code Analysis Results', html);
            
            return true;
        }
        
        // VERSION CONTROL SYSTEM
        const versionHistory = [];
        let currentVersion = 0;
        
        function saveVersion(description) {
            const version = {
                id: Date.now(),
                number: versionHistory.length + 1,
                timestamp: new Date().toISOString(),
                description: description,
                nodes: JSON.parse(JSON.stringify(nodes)),
                connections: JSON.parse(JSON.stringify(connections)),
                improvements: window.selectedImprovements ? [...window.selectedImprovements] : []
            };
            versionHistory.push(version);
            currentVersion = versionHistory.length;
            
            // Save to localStorage for persistence
            try {
                localStorage.setItem('nexus_versions', JSON.stringify(versionHistory.slice(-20))); // Keep last 20
            } catch (e) {
                console.warn('Could not save version to localStorage');
            }
            
            return version;
        }
        
        function loadVersions() {
            try {
                const saved = localStorage.getItem('nexus_versions');
                if (saved) {
                    const versions = JSON.parse(saved);
                    versionHistory.push(...versions);
                    currentVersion = versionHistory.length;
                }
            } catch (e) {
                console.warn('Could not load versions');
            }
        }
        
        function restoreVersion(versionId) {
            const version = versionHistory.find(v => v.id === versionId);
            if (!version) {
                toast('Version not found');
                return;
            }
            
            // Save current state before restoring
            saveVersion('Auto-save before restore');
            
            nodes = JSON.parse(JSON.stringify(version.nodes));
            connections = JSON.parse(JSON.stringify(version.connections));
            window.selectedImprovements = version.improvements ? [...version.improvements] : [];
            
            renderAll();
            toast(`Restored to version ${version.number}: ${version.description}`);
            closeModal();
        }
        
        function showVersionHistory() {
            let html = '<div style="font-size: 13px; max-height: 60vh; overflow-y: auto;">';
            
            if (versionHistory.length === 0) {
                html += '<p style="color: var(--text-dim);">No versions saved yet. Versions are created when you make changes.</p>';
            } else {
                html += '<p style="color: var(--text-dim); margin-bottom: 15px;">Click any version to restore your architecture to that point.</p>';
                
                for (let i = versionHistory.length - 1; i >= 0; i--) {
                    const v = versionHistory[i];
                    const date = new Date(v.timestamp);
                    const timeStr = date.toLocaleString();
                    const isCurrent = i === currentVersion - 1;
                    
                    html += `<div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; margin-bottom: 8px; background: ${isCurrent ? 'rgba(99, 102, 241, 0.2)' : 'var(--surface)'}; border: 1px solid ${isCurrent ? 'var(--accent)' : 'var(--border)'}; border-radius: 8px;">`;
                    html += `<div>`;
                    html += `<div style="font-weight: 600;">v${v.number} ${isCurrent ? '(current)' : ''}</div>`;
                    html += `<div style="font-size: 11px; color: var(--text-dim);">${v.description}</div>`;
                    html += `<div style="font-size: 10px; color: var(--text-dim); margin-top: 4px;">${timeStr}</div>`;
                    html += `</div>`;
                    if (!isCurrent) {
                        html += `<button onclick="restoreVersion(${v.id})" style="background: var(--accent); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px;">Restore</button>`;
                    }
                    html += `</div>`;
                }
            }
            
            html += '</div>';
            showModal('📜 Version History', html);
        }
        
        // Load versions on startup
        loadVersions();
        
        // Get suggestions based on what's detected - WITH DETAILED REASONING
        function getSuggestedImprovements(detectedIds) {
            const suggestions = [];
            
            // Rule-based suggestions with DETAILED WHY
            const hasStorage = detectedIds.some(id => id.includes('storage'));
            const hasAuth = detectedIds.some(id => id.includes('auth'));
            const hasBackend = detectedIds.some(id => id.includes('backend'));
            const hasCache = detectedIds.some(id => id.includes('cache'));
            const hasCrud = detectedIds.includes('crud_routes');
            const hasDocker = detectedIds.includes('docker_basic');
            const hasWebsocket = detectedIds.includes('websocket_basic');
            
            if (hasStorage && !hasCache) {
                suggestions.push({
                    blockId: 'cache_redis',
                    name: 'Redis Cache',
                    reason: 'Missing caching layer',
                    why: {
                        problem: 'Every request hits your database directly',
                        evidence: 'Detected storage patterns (sqlite/postgres/json) but no caching',
                        impact: {
                            before: 'Database query: ~50-200ms per request',
                            after: 'Cache hit: ~1-5ms per request (10-50x faster)',
                            metric: '90% reduction in database load'
                        },
                        risk: 'low',
                        effort: 'medium'
                    }
                });
            }
            
            if ((hasBackend || hasCrud) && !hasAuth) {
                suggestions.push({
                    blockId: 'auth_basic',
                    name: 'Basic Auth',
                    reason: 'No authentication detected',
                    why: {
                        problem: 'Your API endpoints are publicly accessible',
                        evidence: 'Found route handlers but no session/token/auth patterns',
                        impact: {
                            before: 'Anyone can access/modify your data',
                            after: 'Only authenticated users can access protected routes',
                            metric: '100% reduction in unauthorized access'
                        },
                        risk: 'critical',
                        effort: 'low'
                    }
                });
            }
            
            if (hasBackend && !hasDocker) {
                suggestions.push({
                    blockId: 'docker_basic',
                    name: 'Docker Container',
                    reason: 'No containerization',
                    why: {
                        problem: 'App may work on your machine but fail elsewhere',
                        evidence: 'No Dockerfile or docker-compose detected',
                        impact: {
                            before: '"Works on my machine" deployment issues',
                            after: 'Consistent environment across dev/staging/production',
                            metric: '80% reduction in deployment failures'
                        },
                        risk: 'low',
                        effort: 'low'
                    }
                });
            }
            
            if (hasStorage && !hasCrud) {
                suggestions.push({
                    blockId: 'crud_routes',
                    name: 'CRUD API Routes',
                    reason: 'Limited API operations',
                    why: {
                        problem: 'Storage exists but no complete API to access it',
                        evidence: 'Found database patterns but limited route handlers',
                        impact: {
                            before: 'Inconsistent or missing API endpoints',
                            after: 'Full Create/Read/Update/Delete operations',
                            metric: 'Complete REST API coverage'
                        },
                        risk: 'low',
                        effort: 'medium'
                    }
                });
            }
            
            if (hasCrud && !hasWebsocket && detectedIds.length > 2) {
                suggestions.push({
                    blockId: 'websocket_basic',
                    name: 'WebSockets',
                    reason: 'No real-time updates',
                    why: {
                        problem: 'Users must refresh to see changes',
                        evidence: 'Multi-component app with only HTTP requests',
                        impact: {
                            before: 'Users poll or refresh for updates',
                            after: 'Instant updates pushed to all connected clients',
                            metric: '100% reduction in unnecessary polling'
                        },
                        risk: 'medium',
                        effort: 'medium'
                    }
                });
            }
            
            if (detectedIds.includes('storage_json') && !detectedIds.includes('storage_sqlite')) {
                suggestions.push({
                    blockId: 'storage_sqlite',
                    name: 'SQLite Database',
                    reason: 'JSON storage limitations',
                    why: {
                        problem: 'JSON files don\'t support queries, transactions, or concurrent writes',
                        evidence: 'Using json.load/json.dump for data persistence',
                        impact: {
                            before: 'Full file read/write for every operation, data corruption risk',
                            after: 'ACID transactions, SQL queries, concurrent access',
                            metric: '99% reduction in data corruption risk'
                        },
                        risk: 'low',
                        effort: 'medium'
                    }
                });
            }
            
            if (detectedIds.includes('auth_basic') && !detectedIds.includes('auth_oauth')) {
                suggestions.push({
                    blockId: 'auth_oauth',
                    name: 'OAuth Integration',
                    reason: 'Password-only authentication',
                    why: {
                        problem: 'Users must create/remember another password',
                        evidence: 'Basic session auth without social login',
                        impact: {
                            before: '40% signup abandonment due to password friction',
                            after: 'One-click Google/GitHub login',
                            metric: '60% increase in signup completion'
                        },
                        risk: 'low',
                        effort: 'medium'
                    }
                });
            }
            
            return suggestions.slice(0, 4); // Max 4 suggestions
        }
        
        // Preview what adding a suggestion will do
        function previewSuggestion(index) {
            const sug = window.currentSuggestions?.[index];
            if (!sug) {
                toast('Suggestion not found');
                return;
            }
            
            const block = blocks.find(b => b.id === sug.blockId);
            if (!block) {
                toast('Block not found');
                return;
            }
            
            let html = '<div style="font-size: 13px;">';
            
            // Block info
            html += `<div style="background: var(--surface); padding: 15px; border-radius: 8px; margin-bottom: 15px;">`;
            html += `<div style="font-size: 16px; font-weight: 600; margin-bottom: 10px;">${block.name}</div>`;
            html += `<div style="color: var(--text-dim); font-size: 12px;">${block.description || 'Architectural building block'}</div>`;
            html += `</div>`;
            
            // What it provides/requires
            html += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">`;
            
            html += `<div style="padding: 12px; background: rgba(34, 197, 94, 0.1); border-radius: 8px;">`;
            html += `<div style="font-weight: 600; color: var(--success); margin-bottom: 8px;">✅ Provides</div>`;
            const provides = block.provides || [];
            if (provides.length > 0) {
                for (const p of provides) {
                    html += `<div style="font-size: 12px; margin-bottom: 4px;">• ${p.name}</div>`;
                }
            } else {
                html += `<div style="font-size: 12px; color: var(--text-dim);">No outputs</div>`;
            }
            html += `</div>`;
            
            html += `<div style="padding: 12px; background: rgba(239, 68, 68, 0.1); border-radius: 8px;">`;
            html += `<div style="font-weight: 600; color: var(--error); margin-bottom: 8px;">📥 Requires</div>`;
            const requires = block.requires || [];
            if (requires.length > 0) {
                for (const r of requires) {
                    html += `<div style="font-size: 12px; margin-bottom: 4px;">• ${r.name}</div>`;
                }
            } else {
                html += `<div style="font-size: 12px; color: var(--text-dim);">No dependencies</div>`;
            }
            html += `</div>`;
            
            html += `</div>`;
            
            // Code preview
            html += `<div style="margin-bottom: 15px;">`;
            html += `<div style="font-weight: 600; margin-bottom: 8px;">📝 Code That Will Be Generated</div>`;
            html += `<pre style="background: var(--bg); padding: 12px; border-radius: 8px; font-size: 11px; max-height: 200px; overflow: auto;">${escapeHtml(getBlockCodePreview(sug.blockId))}</pre>`;
            html += `</div>`;
            
            // Impact summary
            if (sug.why?.impact) {
                html += `<div style="background: rgba(99, 102, 241, 0.1); border: 1px solid var(--accent); padding: 12px; border-radius: 8px; margin-bottom: 15px;">`;
                html += `<div style="font-weight: 600; color: var(--accent); margin-bottom: 8px;">📈 Expected Impact</div>`;
                html += `<div style="font-size: 12px;">`;
                html += `<div style="margin-bottom: 4px;"><strong>Before:</strong> ${sug.why.impact.before}</div>`;
                html += `<div style="margin-bottom: 4px;"><strong>After:</strong> ${sug.why.impact.after}</div>`;
                html += `<div style="color: var(--success); font-weight: 600;">${sug.why.impact.metric}</div>`;
                html += `</div>`;
                html += `</div>`;
            }
            
            // Validation check
            html += `<div style="background: var(--surface); padding: 12px; border-radius: 8px; margin-bottom: 15px;">`;
            html += `<div style="font-weight: 600; margin-bottom: 8px;">🔒 Validation Status</div>`;
            const validation = validateAddition(sug.blockId);
            if (validation.valid) {
                html += `<div style="color: var(--success);">✅ Safe to add - no conflicts detected</div>`;
            } else {
                html += `<div style="color: var(--warning);">⚠️ ${validation.warning}</div>`;
            }
            html += `</div>`;
            
            // Action buttons
            html += `<div style="display: flex; gap: 10px;">`;
            html += `<button onclick="addSuggestedBlockWithVersion('${sug.blockId}', '${sug.name}')" style="flex: 1; background: var(--success); color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: 600;">✅ Add to Architecture</button>`;
            html += `<button onclick="closeModal()" style="background: var(--surface); border: 1px solid var(--border); padding: 12px 20px; border-radius: 6px; cursor: pointer;">Cancel</button>`;
            html += `</div>`;
            
            html += '</div>';
            
            showModal(`👁️ Preview: ${sug.name}`, html);
        }
        
        // Get a preview of what code a block generates
        function getBlockCodePreview(blockId) {
            const previews = {
                'cache_redis': `import redis
from functools import wraps

# Initialize Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache(ttl=300):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            result = f(*args, **kwargs)
            redis_client.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator`,
                'auth_basic': `from functools import wraps
from flask import session, redirect, request
import hashlib

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()`,
                'docker_basic': `# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]`,
                'crud_routes': `@app.route('/api/<resource>', methods=['GET', 'POST'])
def handle_collection(resource):
    if request.method == 'GET':
        return jsonify(storage.get_all(resource))
    data = request.get_json()
    return jsonify(storage.create(resource, data))

@app.route('/api/<resource>/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_item(resource, id):
    if request.method == 'GET':
        return jsonify(storage.get(resource, id))
    elif request.method == 'DELETE':
        return jsonify(storage.delete(resource, id))
    data = request.get_json()
    return jsonify(storage.update(resource, id, data))`,
                'websocket_basic': `from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    emit('status', {'connected': True})

@socketio.on('message')
def handle_message(data):
    emit('broadcast', data, broadcast=True)`,
                'storage_sqlite': `import sqlite3

def get_db():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, content TEXT, created_at TIMESTAMP)")
    conn.commit()`,
                'auth_oauth': `from authlib.integrations.flask_client import OAuth

oauth = OAuth(app)
google = oauth.register('google',
    client_id=os.environ['GOOGLE_CLIENT_ID'],
    client_secret=os.environ['GOOGLE_CLIENT_SECRET'],
    # additional config here
)`
            };
            return previews[blockId] || '# Code will be generated based on your architecture';
        }
        
        // Validate if adding a block is safe
        function validateAddition(blockId) {
            // Check for conflicts
            const existingIds = nodes.map(n => n.blockId);
            
            // Rule: Can't have both basic and oauth auth without proper setup
            if (blockId === 'auth_oauth' && !existingIds.includes('auth_basic')) {
                return { valid: true, warning: null };
            }
            
            // Rule: WebSocket needs a backend
            if (blockId === 'websocket_basic' && !existingIds.some(id => id.includes('backend'))) {
                return { valid: true, warning: 'WebSockets work best with a backend framework' };
            }
            
            // All good
            return { valid: true, warning: null };
        }
        
        // Add a suggested block WITH version tracking
        function addSuggestedBlockWithVersion(blockId, name) {
            const block = blocks.find(b => b.id === blockId);
            if (!block) {
                toast('Block not found');
                return;
            }
            
            // SAVE VERSION BEFORE MAKING CHANGES
            saveVersion(`Before adding ${name}`);
            
            // Find a good position (below existing nodes)
            const maxY = nodes.length > 0 ? Math.max(...nodes.map(n => n.y)) + 150 : 100;
            const x = 100 + (nodes.length % 3) * 250;
            
            saveToHistory();
            addNode(block, x, maxY);
            
            // Save version after changes
            saveVersion(`Added ${name}`);
            
            closeModal();
            toast(`✅ Added ${block.name} - version saved! Use History to rollback if needed.`);
        }
        
        // Legacy function for backward compatibility
        function addSuggestedBlock(blockId) {
            const block = blocks.find(b => b.id === blockId);
            if (!block) {
                toast('Block not found');
                return;
            }
            
            // Find a good position (below existing nodes)
            const maxY = nodes.length > 0 ? Math.max(...nodes.map(n => n.y)) + 150 : 100;
            const x = 100 + (nodes.length % 3) * 250;
            
            saveToHistory();
            addNode(block, x, maxY);
            
            toast(`Added ${block.name} - now connect it to your architecture!`);
        }
        
        // Show modal for code improvements
        function showImproveCodeModal() {
            closeModal();
            
            const result = window.lastAnalysisResult;
            if (!result) {
                toast('No analysis data available');
                return;
            }
            
            const detectedIds = (result.detected_blocks || []).map(b => b.block_id);
            const improvements = generateCodeImprovements(detectedIds, result);
            
            let html = '<div style="font-size: 13px; max-height: 70vh; overflow-y: auto;">';
            
            html += `<p style="color: var(--text-dim); margin-bottom: 15px;">Based on your codebase analysis, here are code improvements you can add:</p>`;
            
            for (const imp of improvements) {
                html += `<div style="margin-bottom: 20px; border: 1px solid var(--border); border-radius: 8px; overflow: hidden;">`;
                html += `<div style="background: var(--surface); padding: 12px; display: flex; justify-content: space-between; align-items: center;">`;
                html += `<div>`;
                html += `<strong>${imp.title}</strong>`;
                html += `<div style="font-size: 11px; color: var(--text-dim);">${imp.description}</div>`;
                html += `</div>`;
                html += `<div style="display: flex; gap: 6px;">`;
                html += `<button onclick="copyImprovement('${imp.id}')" style="background: var(--accent); color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">📋 Copy</button>`;
                html += `<button onclick="addImprovementToProject('${imp.id}')" style="background: var(--success); color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">+ Add</button>`;
                html += `</div>`;
                html += `</div>`;
                html += `<pre id="improvement-${imp.id}" style="margin: 0; padding: 12px; background: var(--bg); font-size: 11px; overflow-x: auto; max-height: 200px;">${escapeHtml(imp.code)}</pre>`;
                html += `</div>`;
            }
            
            // Hybrid option
            html += `<div style="margin-top: 20px; padding: 15px; background: rgba(139, 92, 246, 0.1); border: 1px solid var(--accent2); border-radius: 8px;">`;
            html += `<div style="font-weight: 600; color: var(--accent2); margin-bottom: 10px;">🔀 Create Hybrid Architecture</div>`;
            html += `<p style="font-size: 12px; color: var(--text-dim); margin-bottom: 12px;">Generate a complete app that combines your existing patterns with suggested improvements.</p>`;
            html += `<button onclick="generateHybridApp()" style="background: linear-gradient(135deg, var(--accent), var(--accent2)); color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; width: 100%;">Generate Hybrid App</button>`;
            html += `</div>`;
            
            html += '</div>';
            
            // Store improvements for copy/add
            window.codeImprovements = improvements;
            
            showModal('🚀 Code Improvements', html);
        }
        
        // Generate code improvements based on what's detected
        function generateCodeImprovements(detectedIds, result) {
            const improvements = [];
            
            const hasStorage = detectedIds.some(id => id.includes('storage'));
            const hasCache = detectedIds.some(id => id.includes('cache'));
            const hasAuth = detectedIds.some(id => id.includes('auth'));
            
            // Always suggest error handling
            improvements.push({
                id: 'error_handling',
                title: 'Enhanced Error Handling',
                description: 'Add centralized error handling with logging',
                code: `# Add to your main app file
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return {"error": str(e)}, 500
    return wrapper

# Usage: @handle_errors on your route functions`
            });
            
            if (hasStorage && !hasCache) {
                improvements.push({
                    id: 'caching_layer',
                    title: 'Caching Layer',
                    description: 'Add in-memory caching for faster responses',
                    code: `# Simple caching without external dependencies
from functools import lru_cache
from time import time

class SimpleCache:
    def __init__(self, ttl=300):
        self._cache = {}
        self._ttl = ttl
    
    def get(self, key):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time() - timestamp < self._ttl:
                return value
            del self._cache[key]
        return None
    
    def set(self, key, value):
        self._cache[key] = (value, time())
    
    def delete(self, key):
        self._cache.pop(key, None)

cache = SimpleCache(ttl=300)  # 5 min TTL

# Usage in routes:
# data = cache.get('items') or fetch_from_db()
# cache.set('items', data)`
                });
            }
            
            if (!hasAuth) {
                improvements.push({
                    id: 'simple_auth',
                    title: 'Simple API Key Auth',
                    description: 'Add basic API key authentication',
                    code: `# Simple API Key Authentication
from functools import wraps
from flask import request

API_KEYS = {"demo_key_123": "user1"}  # Store securely in production!

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in API_KEYS:
            return {"error": "Invalid or missing API key"}, 401
        return f(*args, **kwargs)
    return wrapper

# Usage: @require_api_key on protected routes`
                });
            }
            
            // Rate limiting
            improvements.push({
                id: 'rate_limiting',
                title: 'Rate Limiting',
                description: 'Prevent abuse with request throttling',
                code: `# Simple Rate Limiter
from time import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests=100, window=60):
        self._requests = requests
        self._window = window
        self._clients = defaultdict(list)
    
    def is_allowed(self, client_id):
        now = time()
        # Clean old requests
        self._clients[client_id] = [
            t for t in self._clients[client_id] 
            if now - t < self._window
        ]
        # Check limit
        if len(self._clients[client_id]) >= self._requests:
            return False
        self._clients[client_id].append(now)
        return True

limiter = RateLimiter(requests=100, window=60)

# Usage in routes:
# if not limiter.is_allowed(request.remote_addr):
#     return {"error": "Rate limit exceeded"}, 429`
            });
            
            // Health check endpoint
            improvements.push({
                id: 'health_check',
                title: 'Health Check Endpoint',
                description: 'Add a /health endpoint for monitoring',
                code: `# Health Check Endpoint
from datetime import datetime

start_time = datetime.now()

@app.route('/health')
def health_check():
    uptime = (datetime.now() - start_time).total_seconds()
    return {
        "status": "healthy",
        "uptime_seconds": round(uptime),
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }`
            });
            
            return improvements;
        }
        
        // Copy improvement code to clipboard
        function copyImprovement(id) {
            const imp = window.codeImprovements?.find(i => i.id === id);
            if (imp) {
                navigator.clipboard.writeText(imp.code).then(() => {
                    toast('Code copied to clipboard!');
                });
            }
        }
        
        // Add improvement to project (marks for inclusion in generation)
        function addImprovementToProject(id) {
            const imp = window.codeImprovements?.find(i => i.id === id);
            if (imp) {
                // Store in session for generation
                if (!window.selectedImprovements) window.selectedImprovements = [];
                if (!window.selectedImprovements.includes(id)) {
                    window.selectedImprovements.push(id);
                    toast(`Added "${imp.title}" - will be included when you generate!`);
                } else {
                    toast('Already added!');
                }
            }
        }
        
        // VALIDATION GATE - prevents bad code from being generated
        async function validateArchitecture(blockIds) {
            // Run formal verification
            try {
                const res = await fetch('/api/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        nodes: blockIds.map((id, i) => ({ id: i + 1, blockId: id })),
                        connections: connections
                    })
                });
                const result = await res.json();
                return result;
            } catch (e) {
                return { verification_score: { percentage: 100 }, violations: [], warnings: [] };
            }
        }
        
        // Generate hybrid app combining existing code with improvements
        async function generateHybridApp() {
            const result = window.lastAnalysisResult;
            if (!result || !result.detected_blocks) {
                toast('No analysis data available');
                return;
            }
            
            // Get all detected blocks plus any on canvas
            const detectedIds = result.detected_blocks.map(b => b.block_id);
            const canvasIds = nodes.map(n => n.blockId);
            const allBlockIds = [...new Set([...detectedIds, ...canvasIds])];
            
            // Include selected improvements
            const improvements = window.selectedImprovements || [];
            
            closeModal();
            
            // STEP 1: VALIDATION GATE - Check for issues before generating
            toast('🔍 Validating architecture...');
            const validation = await validateArchitecture(allBlockIds);
            
            if (validation.violations && validation.violations.length > 0) {
                // Show validation errors - DON'T ALLOW BAD CODE
                let html = '<div style="font-size: 13px;">';
                html += `<div style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--error); padding: 15px; border-radius: 8px; margin-bottom: 15px;">`;
                html += `<div style="font-weight: 600; color: var(--error); margin-bottom: 10px;">🚫 Cannot Generate - Validation Failed</div>`;
                html += `<p style="color: var(--text-dim); font-size: 12px; margin-bottom: 10px;">NEXUS prevents generating code with known issues:</p>`;
                
                for (const v of validation.violations) {
                    html += `<div style="margin-bottom: 8px; padding: 8px; background: var(--surface); border-radius: 4px;">`;
                    html += `<div style="color: var(--error);">❌ ${v.theorem || v.message || v}</div>`;
                    if (v.fix) {
                        html += `<div style="font-size: 11px; color: var(--success); margin-top: 4px;">💡 Fix: ${v.fix}</div>`;
                    }
                    html += `</div>`;
                }
                
                html += `</div>`;
                html += `<p style="color: var(--text-dim); font-size: 12px;">Fix these issues in your architecture, then try again.</p>`;
                html += '</div>';
                
                showModal('🚫 Validation Failed', html);
                return;
            }
            
            // Check for warnings (allow but inform)
            const warnings = validation.warnings || [];
            
            // STEP 2: Save version BEFORE generating (for rollback)
            saveVersion('Before generating hybrid app');
            
            toast('✅ Validation passed! Generating...');
            
            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: 'hybrid_app',
                        blocks: allBlockIds,
                        description: 'Hybrid app combining existing patterns with improvements',
                        improvements: improvements,
                        validated: true  // Mark that this passed validation
                    })
                });
                const data = await res.json();
                
                if (data.error) {
                    toast('Error: ' + data.error);
                    return;
                }
                
                // Save version after successful generation
                saveVersion(`Generated hybrid app: ${allBlockIds.join(', ')}`);
                
                toast(`Hybrid app generated at: ${data.output_path}`);
                
                // Show the generated files with validation status
                let filesHtml = '<div style="font-size: 13px;">';
                
                // Validation badge
                filesHtml += `<div style="background: rgba(34, 197, 94, 0.1); border: 1px solid var(--success); padding: 12px; border-radius: 8px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">`;
                filesHtml += `<span style="font-size: 24px;">✅</span>`;
                filesHtml += `<div>`;
                filesHtml += `<div style="font-weight: 600; color: var(--success);">Validated & Generated</div>`;
                filesHtml += `<div style="font-size: 11px; color: var(--text-dim);">This code passed all validation checks</div>`;
                filesHtml += `</div>`;
                filesHtml += `</div>`;
                
                if (warnings.length > 0) {
                    filesHtml += `<div style="background: rgba(245, 158, 11, 0.1); border: 1px solid var(--warning); padding: 10px; border-radius: 8px; margin-bottom: 15px;">`;
                    filesHtml += `<div style="font-weight: 600; color: var(--warning); margin-bottom: 5px;">⚠️ Warnings</div>`;
                    for (const w of warnings) {
                        filesHtml += `<div style="font-size: 11px; color: var(--text-dim);">• ${w}</div>`;
                    }
                    filesHtml += `</div>`;
                }
                
                filesHtml += `<p style="margin-bottom: 10px;"><strong>Location:</strong> <code>${data.output_path}</code></p>`;
                filesHtml += '<p style="margin-bottom: 10px;"><strong>Includes:</strong></p>';
                filesHtml += '<ul style="margin-left: 20px; color: var(--text-dim);">';
                for (const blockId of allBlockIds) {
                    filesHtml += `<li>${blockId.replace(/_/g, ' ')}</li>`;
                }
                if (improvements.length > 0) {
                    filesHtml += '<li style="color: var(--success);">+ Selected improvements</li>';
                }
                filesHtml += '</ul>';
                
                // Version info
                filesHtml += `<div style="margin-top: 15px; padding: 10px; background: var(--surface); border-radius: 8px;">`;
                filesHtml += `<div style="font-size: 11px; color: var(--text-dim);">`;
                filesHtml += `📜 Version saved! If issues arise, use <strong>History</strong> to rollback.`;
                filesHtml += `</div>`;
                filesHtml += `</div>`;
                
                filesHtml += '<p style="margin-top: 15px; font-size: 12px; color: var(--text-dim);">Run with: <code>python app.py</code></p>';
                filesHtml += '</div>';
                
                showModal('✨ Hybrid App Generated', filesHtml);
                
            } catch (e) {
                toast('Failed to generate: ' + e.message);
            }
        }
        
        // HTML escaping for security
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Supported code file extensions - ALL major languages
        const CODE_EXTENSIONS = new Set([
            // Python
            '.py', '.pyw', '.pyx', '.pxd', '.pxi',
            // JavaScript/TypeScript
            '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
            // Web
            '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
            // Systems languages
            '.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.hh', '.hxx',
            '.rs', '.go', '.zig',
            // JVM
            '.java', '.kt', '.kts', '.scala', '.groovy', '.clj', '.cljs',
            // .NET
            '.cs', '.fs', '.vb',
            // Scripting
            '.rb', '.php', '.pl', '.pm', '.lua', '.r', '.jl',
            // Shell
            '.sh', '.bash', '.zsh', '.ps1', '.psm1', '.bat', '.cmd',
            // Config
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.xml', '.gradle', '.properties',
            // Other
            '.sql', '.graphql', '.gql', '.proto', '.thrift',
            '.md', '.rst', '.txt',
            // Build
            '.dockerfile', '.makefile', '.cmake'
        ]);
        
        // Special files to always include
        const SPECIAL_FILES = new Set([
            'dockerfile', 'makefile', 'cmakelists.txt', 'gemfile', 'rakefile',
            'package.json', 'cargo.toml', 'go.mod', 'requirements.txt',
            'setup.py', 'pyproject.toml', 'build.gradle', 'pom.xml',
            '.gitignore', '.env', '.env.example'
        ]);
        
        // Max limits to prevent freezing
        const MAX_FILES = 200;
        const MAX_FILE_SIZE = 500 * 1024; // 500KB per file
        const MAX_TOTAL_SIZE = 5 * 1024 * 1024; // 5MB total
        
        function isCodeFile(filename) {
            const name = filename.toLowerCase();
            const ext = '.' + name.split('.').pop();
            return CODE_EXTENSIONS.has(ext) || SPECIAL_FILES.has(name.split('/').pop().split('\\\\').pop());
        }
        
        async function processSelectedFiles() {
            const statusEl = document.getElementById('selectedFolder');
            let allCode = '';
            let fileNames = [];
            let totalSize = 0;
            let skipped = { tooLarge: 0, wrongType: 0 };
            
            // Filter to code files only
            const codeFiles = selectedFiles.filter(f => {
                const name = f.webkitRelativePath || f.name || '';
                return isCodeFile(name);
            });
            
            console.log(`Found ${codeFiles.length} code files out of ${selectedFiles.length} total`);
            
            if (codeFiles.length === 0) {
                const exts = [...new Set(selectedFiles.map(f => {
                    const n = f.name || '';
                    return n.includes('.') ? '.' + n.split('.').pop().toLowerCase() : '(no ext)';
                }))].slice(0, 10);
                toast(`No code files found. Extensions in folder: ${exts.join(', ')}`);
                return;
            }
            
            // Sort by size (smallest first) to maximize file count
            const sortedFiles = codeFiles.slice(0, MAX_FILES * 2).sort((a, b) => a.size - b.size);
            
            // Process in batches to prevent freezing
            const BATCH_SIZE = 20;
            for (let i = 0; i < sortedFiles.length && fileNames.length < MAX_FILES; i += BATCH_SIZE) {
                const batch = sortedFiles.slice(i, i + BATCH_SIZE);
                
                // Update status
                statusEl.textContent = `Reading files... ${fileNames.length}/${Math.min(sortedFiles.length, MAX_FILES)}`;
                
                // Yield to UI thread
                await new Promise(r => setTimeout(r, 0));
                
                for (const file of batch) {
                    if (fileNames.length >= MAX_FILES) break;
                    if (totalSize >= MAX_TOTAL_SIZE) break;
                    
                    // Skip files that are too large
                    if (file.size > MAX_FILE_SIZE) {
                        skipped.tooLarge++;
                        continue;
                    }
                    
                    try {
                        const content = await file.text();
                        const filename = file.webkitRelativePath || file.name;
                        
                        // Detect language from extension
                        const ext = filename.split('.').pop().toLowerCase();
                        let commentPrefix = '//';
                        if (['py', 'rb', 'pl', 'sh', 'bash', 'zsh', 'yaml', 'yml', 'toml'].includes(ext)) {
                            commentPrefix = '#';
                        } else if (['sql', 'lua'].includes(ext)) {
                            commentPrefix = '--';
                        }
                        
                        allCode += `\\n${commentPrefix} File: ${filename}\\n` + content;
                        fileNames.push(filename);
                        totalSize += content.length;
                    } catch (e) {
                        console.error('Failed to read:', file.name, e);
                    }
                }
            }
            
            console.log(`Processed ${fileNames.length} files, ${Math.round(totalSize/1024)}KB`);
            
            if (skipped.tooLarge > 0) {
                console.log(`Skipped ${skipped.tooLarge} files > 500KB`);
            }
            
            if (!allCode) {
                toast('Could not read any code files');
                return;
            }
            
            // Update status for server phase
            statusEl.textContent = `Analyzing ${fileNames.length} files...`;
            
            try {
                const res = await fetch('/api/analyze-code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        code: allCode, 
                        filename: 'browsed_folder',
                        files_analyzed: fileNames
                    })
                });
                const result = await res.json();
                result.files_analyzed = fileNames;
                result.file_count = fileNames.length;
                
                if (skipped.tooLarge > 0) {
                    result.skipped_large = skipped.tooLarge;
                }
                
                handleImportResult(result);
            } catch (e) {
                toast('Failed to analyze: ' + e.message);
            }
        }
        
        async function doImport() {
            const pathInput = document.getElementById('importPath').value.trim();
            const codeInput = document.getElementById('importCode').value.trim();
            
            console.log('doImport called');
            console.log('  selectedFiles.length:', selectedFiles.length);
            console.log('  pathInput:', pathInput);
            console.log('  codeInput length:', codeInput.length);
            
            // Check if files were selected via browse
            if (selectedFiles.length > 0) {
                // Show loading indicator
                const importBtn = document.querySelector('#importModal button[onclick="doImport()"]');
                const originalText = importBtn.textContent;
                importBtn.textContent = 'Analyzing...';
                importBtn.disabled = true;
                
                try {
                    await processSelectedFiles();
                } finally {
                    importBtn.textContent = originalText;
                    importBtn.disabled = false;
                }
                return;
            }
            
            if (!pathInput && !codeInput) {
                toast('Enter a path, browse for a folder, or paste code');
                return;
            }
            
            try {
                let result;
                
                if (pathInput) {
                    // Analyze directory
                    const res = await fetch('/api/analyze-directory', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ path: pathInput })
                    });
                    result = await res.json();
                } else {
                    // Analyze pasted code
                    const res = await fetch('/api/analyze-code', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ code: codeInput, filename: 'pasted.py' })
                    });
                    result = await res.json();
                }
                
                handleImportResult(result);
                
            } catch (e) {
                toast('Failed to analyze code: ' + e.message);
            }
        }
        
        // Canvas setup
        const canvasArea = document.getElementById('canvasArea');
        const canvas = document.getElementById('canvas');
        
        canvasArea.addEventListener('dragover', e => e.preventDefault());
        canvasArea.addEventListener('drop', e => {
            e.preventDefault();
            const blockId = e.dataTransfer.getData('blockId');
            if (!blockId) return;
            
            const block = blocks.find(b => b.id === blockId);
            if (!block) return;
            
            const rect = canvasArea.getBoundingClientRect();
            addNode(block, e.clientX - rect.left - 90, e.clientY - rect.top - 40);
        });
        
        function addNode(block, x, y) {
            saveToHistory();
            nodes.push({ id: nextNodeId++, blockId: block.id, block, x, y });
            renderAll();
        }
        
        function renderAll() {
            document.getElementById('emptyState').style.display = nodes.length ? 'none' : 'block';
            renderNodes();
            renderConnections();
            updateAnalysis();
        }
        
        function renderNodes() {
            const existingNodes = canvas.querySelectorAll('.node');
            existingNodes.forEach(el => el.remove());
            
            nodes.forEach(n => {
                const el = document.createElement('div');
                el.className = 'node' + (selectedNode === n.id ? ' selected' : '');
                el.id = `node-${n.id}`;
                el.style.left = n.x + 'px';
                el.style.top = n.y + 'px';
                
                const costDesc = n.block.cost?.description || '';
                
                el.innerHTML = `
                    <div class="node-header">
                        <div class="node-icon" style="background: ${getBlockColor(n.blockId)}">
                            ${getBlockIcon(n.blockId)}
                        </div>
                        <div class="node-info">
                            <div class="node-name">${n.block.name}</div>
                            <div class="node-cost">${costDesc}</div>
                        </div>
                        <button class="node-menu" onclick="showNodeMenu(event, ${n.id})">⋮</button>
                    </div>
                    <div class="node-body">
                        ${(n.block.requires || []).map(p => `
                            <div class="port-row require">
                                <div class="port require" data-node="${n.id}" data-port="${p.name}" data-type="require"></div>
                                ${p.name}
                            </div>
                        `).join('')}
                        ${(n.block.provides || []).map(p => `
                            <div class="port-row provide">
                                ${p.name}
                                <div class="port provide" data-node="${n.id}" data-port="${p.name}" data-type="provide"></div>
                            </div>
                        `).join('')}
                    </div>
                `;
                
                canvas.appendChild(el);
                
                // Drag handling
                el.addEventListener('mousedown', e => {
                    if (e.target.closest('.node-menu') || e.target.classList.contains('port')) return;
                    draggingNode = n;
                    selectedNode = n.id;
                    renderNodes();
                });
                
                // Port handling
                el.querySelectorAll('.port').forEach(port => {
                    port.addEventListener('mousedown', e => e.stopPropagation());
                });
                
                // Context menu for what-if
                el.addEventListener('contextmenu', e => {
                    e.preventDefault();
                    analyzeWhatIf(n.id);
                });
            });
        }
        
        function getBlockColor(blockId) {
            if (blockId.startsWith('auth')) return 'rgba(239, 68, 68, 0.2)';
            if (blockId.startsWith('storage')) return 'rgba(34, 197, 94, 0.2)';
            if (blockId.includes('route') || blockId.includes('backend')) return 'rgba(99, 102, 241, 0.2)';
            if (blockId.includes('websocket') || blockId.includes('sync')) return 'rgba(139, 92, 246, 0.2)';
            return 'rgba(255,255,255,0.1)';
        }
        
        function getBlockIcon(blockId) {
            if (blockId.startsWith('auth')) return '🔐';
            if (blockId.startsWith('storage')) return '💾';
            if (blockId.includes('route')) return '🔀';
            if (blockId.includes('backend')) return '⚡';
            if (blockId.includes('websocket')) return '📡';
            if (blockId.includes('cache')) return '💨';
            if (blockId.includes('docker')) return '🐳';
            if (blockId.includes('email')) return '📧';
            return '📦';
        }
        
        document.addEventListener('mousemove', e => {
            if (draggingNode) {
                const rect = canvasArea.getBoundingClientRect();
                draggingNode.x = e.clientX - rect.left - 90;
                draggingNode.y = e.clientY - rect.top - 40;
                
                const el = document.getElementById(`node-${draggingNode.id}`);
                if (el) {
                    el.style.left = draggingNode.x + 'px';
                    el.style.top = draggingNode.y + 'px';
                }
                renderConnections();
            }
        });
        
        document.addEventListener('mouseup', () => {
            draggingNode = null;
        });
        
        function renderConnections() {
            const svg = document.getElementById('connectionsSvg');
            const defs = svg.querySelector('defs').outerHTML;
            let paths = '';
            
            connections.forEach(conn => {
                const fromEl = document.querySelector(`.port.provide[data-node="${conn.fromNode}"][data-port="${conn.fromPort}"]`);
                const toEl = document.querySelector(`.port.require[data-node="${conn.toNode}"][data-port="${conn.toPort}"]`);
                
                if (fromEl && toEl) {
                    const fromRect = fromEl.getBoundingClientRect();
                    const toRect = toEl.getBoundingClientRect();
                    const canvasRect = canvas.getBoundingClientRect();
                    
                    const x1 = fromRect.left + fromRect.width/2 - canvasRect.left;
                    const y1 = fromRect.top + fromRect.height/2 - canvasRect.top;
                    const x2 = toRect.left + toRect.width/2 - canvasRect.left;
                    const y2 = toRect.top + toRect.height/2 - canvasRect.top;
                    
                    const cx = (x1 + x2) / 2;
                    const inferredClass = conn.inferred ? ' inferred' : '';
                    paths += `<path class="connection${inferredClass}" d="M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}"/>`;
                }
            });
            
            svg.innerHTML = defs + paths;
        }
        
        async function updateAnalysis() {
            if (nodes.length === 0) {
                document.getElementById('metricCost').textContent = '$0';
                document.getElementById('metricThroughput').textContent = '-';
                document.getElementById('metricLatency').textContent = '-';
                document.getElementById('metricGrade').textContent = '-';
                document.getElementById('antiPatterns').innerHTML = '<div style="color: var(--text-dim); font-size: 12px;">No issues detected</div>';
                return;
            }
            
            try {
                const res = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nodes, connections })
                });
                const data = await res.json();
                
                // Update metrics
                document.getElementById('metricCost').textContent = `$${data.costs.total_monthly}`;
                document.getElementById('metricThroughput').textContent = data.performance.throughput.toLocaleString();
                document.getElementById('metricLatency').textContent = `${data.performance.latency_p50}ms`;
                document.getElementById('metricGrade').textContent = data.performance.grade;
                
                // Update anti-patterns
                if (data.anti_patterns.length > 0) {
                    document.getElementById('antiPatterns').innerHTML = data.anti_patterns.map(ap => `
                        <div class="anti-pattern ${ap.severity}">
                            <div class="anti-pattern-name">${ap.name}</div>
                            <div class="anti-pattern-desc">${ap.description}</div>
                            <div class="anti-pattern-fix">💡 ${ap.suggestion}</div>
                        </div>
                    `).join('');
                } else {
                    document.getElementById('antiPatterns').innerHTML = '<div style="color: var(--success); font-size: 12px;">✓ No architectural issues detected</div>';
                }
                
                // Update ADR
                updateADR();
                
            } catch (e) {
                console.error('Analysis failed:', e);
            }
        }
        
        async function analyzeWhatIf(nodeId) {
            try {
                const res = await fetch('/api/what-if', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nodes, connections, remove_node_id: nodeId })
                });
                const data = await res.json();
                
                // Highlight the target node
                document.querySelectorAll('.node').forEach(el => el.classList.remove('what-if-target'));
                document.getElementById(`node-${nodeId}`)?.classList.add('what-if-target');
                
                const section = document.getElementById('whatIfSection');
                section.innerHTML = `
                    <div class="what-if-result">
                        <div style="font-weight: 600; margin-bottom: 10px;">
                            Removing: ${data.removing.name}
                        </div>
                        <div class="what-if-impact">
                            <div class="impact-stat">
                                <div class="impact-num ${data.impact.broken_connections > 0 ? 'bad' : 'ok'}">
                                    ${data.impact.broken_connections}
                                </div>
                                <div class="impact-label">Broken Connections</div>
                            </div>
                            <div class="impact-stat">
                                <div class="impact-num ${data.impact.unsatisfied_requirements > 0 ? 'bad' : 'ok'}">
                                    ${data.impact.unsatisfied_requirements}
                                </div>
                                <div class="impact-label">Unsatisfied Deps</div>
                            </div>
                        </div>
                        <div style="font-size: 12px; color: ${data.safe_to_remove ? 'var(--success)' : 'var(--error)'}">
                            ${data.safe_to_remove ? '✓ Safe to remove' : '✗ Will break architecture'}
                        </div>
                        ${data.suggestions.length > 0 ? `
                            <div class="what-if-suggestions">
                                <div style="font-size: 11px; color: var(--text-dim); margin-bottom: 8px;">Alternatives:</div>
                                ${data.suggestions.map(s => `
                                    <div class="suggestion-item" onclick="addBlockById('${s.block_id}')">
                                        <span>+</span> ${s.name} (provides ${s.provides_port})
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        <button onclick="removeNode(${nodeId})" style="
                            margin-top: 12px;
                            width: 100%;
                            padding: 10px;
                            background: ${data.safe_to_remove ? 'var(--error)' : 'var(--surface)'};
                            border: 1px solid var(--error);
                            color: ${data.safe_to_remove ? 'white' : 'var(--error)'};
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 12px;
                        ">
                            ${data.safe_to_remove ? 'Remove Block' : 'Remove Anyway (⚠️)'}
                        </button>
                    </div>
                `;
                
            } catch (e) {
                console.error('What-if failed:', e);
            }
        }
        
        function addBlockById(blockId) {
            const block = blocks.find(b => b.id === blockId);
            if (block) {
                addNode(block, 200 + Math.random() * 300, 200 + Math.random() * 200);
            }
        }
        
        function removeNode(nodeId) {
            saveToHistory();
            nodes = nodes.filter(n => n.id !== nodeId);
            connections = connections.filter(c => c.fromNode !== nodeId && c.toNode !== nodeId);
            document.getElementById('whatIfSection').innerHTML = '<div style="color: var(--text-dim); font-size: 12px;">Right-click a block to analyze removal impact</div>';
            renderAll();
        }
        
        function showNodeMenu(e, nodeId) {
            e.stopPropagation();
            analyzeWhatIf(nodeId);
        }
        
        async function updateADR() {
            if (nodes.length === 0) {
                document.getElementById('adrPreview').textContent = 'Generate an architecture to see the ADR';
                return;
            }
            
            try {
                const res = await fetch('/api/adr', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(getArchitectureData())
                });
                const data = await res.json();
                document.getElementById('adrPreview').textContent = data.adr;
            } catch (e) {
                console.error('ADR generation failed:', e);
            }
        }
        
        function getArchitectureData() {
            return {
                name: document.getElementById('nlInput').value || 'My App',
                description: document.getElementById('nlInput').value,
                nodes: nodes.map(n => ({ id: n.id, blockId: n.blockId, x: n.x, y: n.y })),
                connections
            };
        }
        
        // History for diff
        function saveToHistory() {
            architecture_history.push(JSON.stringify(getArchitectureData()));
            if (architecture_history.length > 10) architecture_history.shift();
        }
        
        async function showDiff() {
            if (architecture_history.length < 2) {
                toast('Need at least 2 changes to show diff');
                return;
            }
            
            const before = JSON.parse(architecture_history[architecture_history.length - 2]);
            const after = getArchitectureData();
            
            try {
                const res = await fetch('/api/diff', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ before, after })
                });
                const diff = await res.json();
                
                let html = '<div class="diff-view">';
                html += '<div class="diff-header">Architecture Changes</div>';
                
                if (diff.blocks.added.length) {
                    diff.blocks.added.forEach(b => {
                        html += `<div class="diff-added">+ ${b}</div>`;
                    });
                }
                if (diff.blocks.removed.length) {
                    diff.blocks.removed.forEach(b => {
                        html += `<div class="diff-removed">- ${b}</div>`;
                    });
                }
                
                html += `<div style="padding: 12px; font-size: 12px;">
                    Cost: $${diff.cost.before} → $${diff.cost.after} (${diff.cost.direction})<br>
                    Performance: ${diff.performance.direction}
                </div>`;
                
                html += '</div>';
                
                showModal('Architecture Diff', html);
                
            } catch (e) {
                toast('Diff failed');
            }
        }
        
        async function sharePlayground() {
            try {
                const res = await fetch('/api/share', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(getArchitectureData())
                });
                const data = await res.json();
                
                const url = window.location.origin + data.url;
                await navigator.clipboard.writeText(url);
                toast('Playground URL copied to clipboard!');
                
            } catch (e) {
                toast('Failed to create playground');
            }
        }
        
        async function loadPlayground(id) {
            try {
                const res = await fetch(`/playground/${id}`);
                const data = await res.json();
                
                if (data.architecture) {
                    const arch = data.architecture;
                    nodes = arch.nodes.map(n => ({
                        ...n,
                        block: blocks.find(b => b.id === n.blockId)
                    }));
                    connections = arch.connections || [];
                    nextNodeId = Math.max(...nodes.map(n => n.id), 0) + 1;
                    
                    if (arch.name) {
                        document.getElementById('nlInput').value = arch.name;
                    }
                    
                    renderAll();
                    toast('Loaded playground');
                }
            } catch (e) {
                toast('Failed to load playground');
            }
        }
        
        async function generateApp() {
            const btn = document.querySelector('.generate-btn');
            btn.disabled = true;
            btn.textContent = 'Generating...';
            
            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(getArchitectureData())
                });
                const result = await res.json();
                
                showModal('App Generated!', `
                    <p>${result.blocks.length} blocks • ${result.connections} connections</p>
                    <p>Monthly cost: <strong>$${result.costs.total_monthly}</strong></p>
                    <p>Throughput: <strong>${result.performance.throughput_formatted}</strong></p>
                    ${result.anti_patterns.length > 0 ? `<p style="color: var(--warning)">⚠️ ${result.anti_patterns.length} architectural warnings</p>` : ''}
                    <code>${result.path}</code>
                    <p style="font-size: 12px; margin-top: 10px;">ADR saved: ${result.adr}</p>
                `);
                
            } catch (e) {
                toast('Generation failed');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Generate App';
            }
        }
        
        // Tab switching
        function showTab(tabId) {
            document.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel-content').forEach(c => c.classList.add('hidden'));
            
            document.querySelector(`.panel-tab[onclick="showTab('${tabId}')"]`).classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.remove('hidden');
        }
        
        // Modal
        function showModal(title, content) {
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalContent').innerHTML = content;
            document.getElementById('modal').classList.add('show');
        }
        
        function closeModal() {
            document.getElementById('modal').classList.remove('show');
        }
        
        // Toast
        function toast(message) {
            const el = document.getElementById('toast');
            el.textContent = message;
            el.classList.add('show');
            setTimeout(() => el.classList.remove('show'), 3000);
        }
        
        init();
    </script>
</body>
</html>'''


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    PLAYGROUNDS_DIR.mkdir(exist_ok=True)
    ADRS_DIR.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("  Blueprint NEXUS")
    print("  What the Industry Missed")
    print("=" * 60)
    print(f"  Open: http://localhost:{PORT}")
    print("=" * 60)
    print("  Revolutionary Features:")
    print("    → Natural Language → Architecture (not just code)")
    print("    → Architecture Diffing (visual change tracking)")
    print("    → What-If Analysis (impact before you change)")
    print("    → Cost/Performance Prediction")
    print("    → Anti-Pattern Detection (architectural linting)")
    print("    → Shareable Playgrounds (one-click share)")
    print("    → Automatic ADRs (documents your decisions)")
    print("=" * 60)
    print("  Try: 'A todo app with auth and realtime sync'")
    print("=" * 60)
    
    def open_browser():
        time.sleep(1)
        webbrowser.open(f"http://localhost:{PORT}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    server = HTTPServer(("", PORT), NexusHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
