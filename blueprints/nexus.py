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
    
    # Generate main app
    app_code = f'''"""
{app_name} - Built with Blueprint NEXUS

Description: {description}
Blocks: {", ".join(block_ids)}
Monthly Cost: ~${costs["total_monthly"]:.2f}
Throughput: {perf["throughput_formatted"]}
"""

from flask import Flask, request, jsonify

app = Flask(__name__)
items = []

@app.route("/")
def home():
    return """<!DOCTYPE html>
<html>
<head>
    <title>{app_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); 
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
        button {{ background: #58a6ff; color: white; border: none; padding: 14px 28px; border-radius: 8px; 
                cursor: pointer; font-weight: 600; }}
        .items {{ list-style: none; }}
        .items li {{ padding: 15px; background: rgba(255,255,255,0.03); margin-bottom: 8px; border-radius: 8px;
                   display: flex; justify-content: space-between; }}
        .del {{ background: #f85149; padding: 8px 16px; border-radius: 6px; border: none; color: white; cursor: pointer; }}
        .warnings {{ background: rgba(248,81,73,0.1); border-left: 4px solid #f85149; padding: 15px; 
                    border-radius: 0 8px 8px 0; margin-bottom: 20px; }}
        .warning-item {{ font-size: 13px; margin: 8px 0; }}
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
                <input id="c" placeholder="Add item..." required>
                <button>Add</button>
            </form>
            <ul class="items" id="items"></ul>
        </div>
    </div>
    <script>
        const load = async () => {{
            const r = await fetch('/api/items');
            const d = await r.json();
            document.getElementById('items').innerHTML = d.items.map((x,i) => 
                `<li><span>${{x.content||x}}</span><button class="del" onclick="del(${{i}})">X</button></li>`).join('');
        }};
        document.getElementById('f').onsubmit = async e => {{
            e.preventDefault();
            await fetch('/api/items', {{method:'POST', headers:{{'Content-Type':'application/json'}}, 
                body: JSON.stringify({{content: document.getElementById('c').value}})}});
            document.getElementById('c').value = '';
            load();
        }};
        const del = async i => {{ await fetch(`/api/items/${{i}}`, {{method:'DELETE'}}); load(); }};
        load();
    </script>
</body>
</html>"""

@app.route("/api/items", methods=["GET"])
def list_items():
    return jsonify({{"items": items}})

@app.route("/api/items", methods=["POST"])
def add_item():
    items.append(request.json)
    return jsonify({{"success": True}})

@app.route("/api/items/<int:idx>", methods=["DELETE"])
def delete_item(idx):
    if 0 <= idx < len(items):
        items.pop(idx)
    return jsonify({{"success": True}})

if __name__ == "__main__":
    print("Starting {app_name}")
    print("Cost: ~${costs["total_monthly"]:.2f}/month")
    print("Throughput: {perf["throughput_formatted"]}")
    app.run(debug=True, port=5000)
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


def analyze_directory(dir_path: str) -> dict:
    """
    Analyze all Python files in a directory and merge into one architecture.
    """
    all_code = ""
    files_analyzed = []
    
    path = Path(dir_path)
    if not path.exists():
        return {"error": f"Directory not found: {dir_path}"}
    
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
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
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
        body = self.rfile.read(content_length).decode() if content_length else "{}"
        data = json.loads(body)
        
        if parsed.path == "/api/parse":
            description = data.get("description", "")
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())
    
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
                       placeholder="Describe your app: 'A todo app with auth and realtime sync'">
                <button class="nl-btn" onclick="parseNaturalLanguage()">Build →</button>
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
                    <h3>Describe What You Want</h3>
                    <p>Type a description in the search bar above, or drag blocks from the panel</p>
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
                Paste your Python code below, or enter a folder path to analyze an entire project.
            </p>
            <div style="margin-bottom: 15px;">
                <label style="font-size: 12px; color: var(--text-dim);">Folder Path (optional)</label>
                <input type="text" id="importPath" placeholder="C:\\path\\to\\your\\project" 
                       style="width: 100%; padding: 10px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--text); margin-top: 5px;">
            </div>
            <div style="margin-bottom: 15px;">
                <label style="font-size: 12px; color: var(--text-dim);">Or paste code directly</label>
                <textarea id="importCode" placeholder="from flask import Flask..." 
                          style="width: 100%; height: 200px; padding: 10px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-family: monospace; font-size: 12px; margin-top: 5px; resize: vertical;"></textarea>
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
        
        // THE KILLER FEATURE: Natural Language → Architecture
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
                
                // Show intent badges
                const intentsHtml = result.detected_intents.map(i => 
                    `<span class="intent-badge">${i}</span>`
                ).join('');
                
                toast(`Detected: ${result.detected_intents.join(', ')} (${Math.round(result.confidence * 100)}% confidence)`);
                
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
        }
        
        async function doImport() {
            const pathInput = document.getElementById('importPath').value.trim();
            const codeInput = document.getElementById('importCode').value.trim();
            
            if (!pathInput && !codeInput) {
                toast('Enter a path or paste code to analyze');
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
                
                if (result.error) {
                    toast(result.error);
                    return;
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
                
                // Show what was detected
                const detectedNames = result.detected_blocks
                    .filter(d => d.confidence >= 0.5)
                    .map(d => d.block_id.replace('_', ' '))
                    .join(', ');
                
                const fileInfo = result.file_count ? ` from ${result.file_count} files` : '';
                toast(`Detected${fileInfo}: ${detectedNames || 'no blocks'} (${result.summary})`);
                
                // Show evidence in modal
                if (result.detected_blocks.length > 0) {
                    let evidenceHtml = '<div style="font-size: 12px;">';
                    evidenceHtml += '<p style="margin-bottom: 10px;">Found these patterns in your code:</p>';
                    
                    for (const block of result.detected_blocks.slice(0, 5)) {
                        const confidence = Math.round(block.confidence * 100);
                        const color = confidence >= 80 ? 'var(--success)' : confidence >= 50 ? 'var(--warning)' : 'var(--text-dim)';
                        evidenceHtml += `<div style="margin-bottom: 8px;">`;
                        evidenceHtml += `<strong style="color: ${color}">${block.block_id}</strong> (${confidence}%)<br>`;
                        evidenceHtml += `<code style="font-size: 10px; color: var(--text-dim);">${block.evidence.slice(0,3).join(', ')}</code>`;
                        evidenceHtml += `</div>`;
                    }
                    
                    if (result.files_analyzed) {
                        evidenceHtml += `<div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid var(--border);">`;
                        evidenceHtml += `<strong>Files analyzed:</strong><br>`;
                        evidenceHtml += result.files_analyzed.slice(0, 10).map(f => `<code style="font-size: 10px;">${f}</code>`).join('<br>');
                        if (result.files_analyzed.length > 10) {
                            evidenceHtml += `<br><span style="color: var(--text-dim);">...and ${result.files_analyzed.length - 10} more</span>`;
                        }
                        evidenceHtml += `</div>`;
                    }
                    
                    evidenceHtml += '</div>';
                    showModal('Code Analysis Results', evidenceHtml);
                }
                
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
