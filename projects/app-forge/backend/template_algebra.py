"""
Template Algebra - Composable Micro-Templates

Universal patterns that appear across ALL domains:
- A "cell" in biology, a "cell" in a spreadsheet, a "cell" in a phone network
- All share: containment, state, communication, lifecycle

This creates an LLM-like combinatorial space WITHOUT:
- Hallucination (all combinations are valid by construction)
- Cloud APIs (100% local)
- Neural networks (explicit algebraic rules)

Architecture:
  Atoms (micro-templates) + Operators (combine/merge/extend) = Molecules (complex apps)

Universal Patterns (appear in EVERY domain):
  1. CONTAINER - Things that hold other things
  2. RELATIONSHIP - Connections between things
  3. STATE - Conditions that change over time
  4. FLOW - Movement/transformation of things
  5. HIERARCHY - Nesting/ownership structures
  6. NETWORK - Graph of interconnections
"""

import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from enum import Enum


# =============================================================================
# Universal Patterns - The 6 Meta-Templates
# =============================================================================

class UniversalPattern(Enum):
    """The 6 patterns that appear in every domain."""
    CONTAINER = "container"      # Things that hold other things
    RELATIONSHIP = "relationship" # Connections between things  
    STATE = "state"              # Conditions that change
    FLOW = "flow"                # Movement/transformation
    HIERARCHY = "hierarchy"      # Nesting/ownership
    NETWORK = "network"          # Graph of connections


# =============================================================================
# Micro-Templates (Atoms)
# =============================================================================

@dataclass
class MicroTemplate:
    """A small, focused template for a specific pattern."""
    id: str
    name: str
    pattern: UniversalPattern
    description: str
    
    # What fields this template adds
    fields: List[Dict[str, Any]] = field(default_factory=list)
    
    # What operations this template enables
    operations: List[str] = field(default_factory=list)
    
    # What other templates this requires
    requires: List[str] = field(default_factory=list)
    
    # What templates this conflicts with
    conflicts: List[str] = field(default_factory=list)
    
    # Code snippets this template contributes
    snippets: Dict[str, str] = field(default_factory=dict)
    
    # Keywords that suggest this template
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'pattern': self.pattern.value,
            'description': self.description,
            'fields': self.fields,
            'operations': self.operations,
            'requires': self.requires,
            'conflicts': self.conflicts,
        }


# =============================================================================
# Built-in Micro-Templates
# =============================================================================

MICRO_TEMPLATES: Dict[str, MicroTemplate] = {}

def register_template(template: MicroTemplate):
    """Register a micro-template."""
    MICRO_TEMPLATES[template.id] = template
    return template

# --- CONTAINER patterns ---

register_template(MicroTemplate(
    id="has_items",
    name="Has Items",
    pattern=UniversalPattern.CONTAINER,
    description="A thing that contains a list of other things",
    fields=[
        {"name": "items", "type": "list", "item_type": "reference"}
    ],
    operations=["add_item", "remove_item", "list_items", "count_items"],
    keywords=["collection", "items", "contain", "has", "with", "multiple", "many"],
))

register_template(MicroTemplate(
    id="has_content",
    name="Has Content",
    pattern=UniversalPattern.CONTAINER,
    description="A thing with text/body content",
    fields=[
        {"name": "content", "type": "text"},
        {"name": "content_type", "type": "string", "default": "text/plain"}
    ],
    operations=["get_content", "set_content", "append_content"],
    keywords=["content", "body", "text", "description", "details", "notes"],
))

register_template(MicroTemplate(
    id="has_metadata",
    name="Has Metadata",
    pattern=UniversalPattern.CONTAINER,
    description="A thing with key-value metadata",
    fields=[
        {"name": "metadata", "type": "json", "default": "{}"}
    ],
    operations=["get_meta", "set_meta", "list_meta"],
    keywords=["metadata", "properties", "attributes", "extra", "custom"],
))

# --- RELATIONSHIP patterns ---

register_template(MicroTemplate(
    id="has_owner",
    name="Has Owner",
    pattern=UniversalPattern.RELATIONSHIP,
    description="A thing owned by a user/entity",
    fields=[
        {"name": "owner_id", "type": "integer", "required": True},
        {"name": "owner_type", "type": "string", "default": "user"}
    ],
    operations=["get_owner", "transfer_ownership", "list_by_owner"],
    requires=["user_entity"],
    keywords=["my", "owner", "belongs", "personal", "private"],
))

register_template(MicroTemplate(
    id="has_parent",
    name="Has Parent",
    pattern=UniversalPattern.RELATIONSHIP,
    description="A thing with a parent reference (tree structure)",
    fields=[
        {"name": "parent_id", "type": "integer", "nullable": True}
    ],
    operations=["get_parent", "set_parent", "get_children", "get_ancestors"],
    keywords=["parent", "child", "nested", "subfolder", "reply", "thread"],
))

register_template(MicroTemplate(
    id="has_tags",
    name="Has Tags",
    pattern=UniversalPattern.RELATIONSHIP,
    description="A thing with multiple tags/labels",
    fields=[
        {"name": "tags", "type": "list", "item_type": "string"}
    ],
    operations=["add_tag", "remove_tag", "list_tags", "find_by_tag"],
    keywords=["tag", "label", "category", "group", "classify"],
))

register_template(MicroTemplate(
    id="has_links",
    name="Has Links",
    pattern=UniversalPattern.RELATIONSHIP,
    description="A thing that links to other things (many-to-many)",
    fields=[
        {"name": "links", "type": "list", "item_type": "reference"}
    ],
    operations=["add_link", "remove_link", "get_linked", "find_connections"],
    keywords=["link", "connect", "relate", "associate", "reference"],
))

# --- STATE patterns ---

register_template(MicroTemplate(
    id="has_status",
    name="Has Status",
    pattern=UniversalPattern.STATE,
    description="A thing with a status/state field",
    fields=[
        {"name": "status", "type": "enum", "values": ["pending", "active", "completed", "archived"]}
    ],
    operations=["set_status", "filter_by_status", "transition_status"],
    keywords=["status", "state", "progress", "done", "complete", "active"],
))

register_template(MicroTemplate(
    id="has_lifecycle",
    name="Has Lifecycle",
    pattern=UniversalPattern.STATE,
    description="A thing with creation/update timestamps",
    fields=[
        {"name": "created_at", "type": "datetime", "auto": True},
        {"name": "updated_at", "type": "datetime", "auto": True}
    ],
    operations=["get_created", "get_updated", "sort_by_date"],
    keywords=["created", "updated", "when", "date", "time", "recent"],
))

register_template(MicroTemplate(
    id="has_version",
    name="Has Version",
    pattern=UniversalPattern.STATE,
    description="A thing with version history",
    fields=[
        {"name": "version", "type": "integer", "default": 1},
        {"name": "previous_version_id", "type": "integer", "nullable": True}
    ],
    operations=["increment_version", "get_history", "rollback"],
    keywords=["version", "versioned", "revision", "history", "undo", "rollback", "changelog", "track changes"],
))

register_template(MicroTemplate(
    id="is_deletable",
    name="Soft Delete",
    pattern=UniversalPattern.STATE,
    description="A thing that can be soft-deleted",
    fields=[
        {"name": "deleted_at", "type": "datetime", "nullable": True}
    ],
    operations=["soft_delete", "restore", "list_deleted", "purge"],
    keywords=["delete", "remove", "trash", "archive", "restore"],
))

# --- FLOW patterns ---

register_template(MicroTemplate(
    id="has_workflow",
    name="Has Workflow",
    pattern=UniversalPattern.FLOW,
    description="A thing that moves through stages",
    fields=[
        {"name": "stage", "type": "string", "default": "start"},
        {"name": "stage_history", "type": "json", "default": "[]"}
    ],
    operations=["advance_stage", "get_stage_history", "can_transition"],
    requires=["has_status"],
    keywords=["workflow", "process", "pipeline", "stage", "step"],
))

register_template(MicroTemplate(
    id="is_orderable",
    name="Is Orderable",
    pattern=UniversalPattern.FLOW,
    description="A thing with a position in a sequence",
    fields=[
        {"name": "position", "type": "integer", "default": 0}
    ],
    operations=["move_up", "move_down", "reorder", "get_sorted"],
    keywords=["order", "sort", "position", "rank", "priority", "sequence"],
))

register_template(MicroTemplate(
    id="is_schedulable",
    name="Is Schedulable",
    pattern=UniversalPattern.FLOW,
    description="A thing with scheduled dates",
    fields=[
        {"name": "scheduled_at", "type": "datetime", "nullable": True},
        {"name": "due_at", "type": "datetime", "nullable": True}
    ],
    operations=["schedule", "get_upcoming", "get_overdue", "reschedule"],
    keywords=["schedule", "due", "deadline", "calendar", "plan", "when"],
))

# --- HIERARCHY patterns ---

register_template(MicroTemplate(
    id="is_nested",
    name="Is Nested",
    pattern=UniversalPattern.HIERARCHY,
    description="A thing that can contain copies of itself",
    fields=[
        {"name": "parent_id", "type": "self_reference", "nullable": True},
        {"name": "depth", "type": "integer", "default": 0}
    ],
    operations=["get_children", "get_ancestors", "get_tree", "move_to"],
    keywords=["folder", "category", "nested", "tree", "hierarchy"],
))

register_template(MicroTemplate(
    id="has_path",
    name="Has Path",
    pattern=UniversalPattern.HIERARCHY,
    description="A thing with a filesystem-like path",
    fields=[
        {"name": "path", "type": "string", "unique": True},
        {"name": "slug", "type": "string"}
    ],
    operations=["get_by_path", "rename_path", "list_children_paths"],
    keywords=["path", "url", "slug", "directory", "folder"],
))

# --- NETWORK patterns ---

register_template(MicroTemplate(
    id="has_followers",
    name="Has Followers",
    pattern=UniversalPattern.NETWORK,
    description="A thing that can be followed by users",
    fields=[
        {"name": "follower_count", "type": "integer", "default": 0}
    ],
    operations=["follow", "unfollow", "get_followers", "get_following"],
    keywords=["follow", "followers", "following", "subscribe", "watch", "fan", "audience", "social"],
))

register_template(MicroTemplate(
    id="is_rateable",
    name="Is Rateable",
    pattern=UniversalPattern.NETWORK,
    description="A thing that can be rated/scored",
    fields=[
        {"name": "rating_sum", "type": "float", "default": 0},
        {"name": "rating_count", "type": "integer", "default": 0},
        {"name": "avg_rating", "type": "float", "computed": True}
    ],
    operations=["rate", "get_rating", "top_rated", "unrate"],
    keywords=["rate", "rating", "star", "score", "review", "quality"],
))

register_template(MicroTemplate(
    id="is_likeable",
    name="Is Likeable",
    pattern=UniversalPattern.NETWORK,
    description="A thing that can be liked/upvoted",
    fields=[
        {"name": "like_count", "type": "integer", "default": 0}
    ],
    operations=["like", "unlike", "get_likers", "most_liked"],
    keywords=["like", "likes", "upvote", "favorite", "heart", "love", "bookmark", "thumb"],
))

register_template(MicroTemplate(
    id="is_commentable",
    name="Is Commentable",
    pattern=UniversalPattern.NETWORK,
    description="A thing that can have comments",
    fields=[
        {"name": "comment_count", "type": "integer", "default": 0},
        {"name": "comments_enabled", "type": "boolean", "default": True}
    ],
    operations=["add_comment", "get_comments", "delete_comment"],
    requires=["has_owner"],
    keywords=["comment", "comments", "feedback", "discussion", "reply", "respond", "blog"],
))

register_template(MicroTemplate(
    id="is_shareable",
    name="Is Shareable",
    pattern=UniversalPattern.NETWORK,
    description="A thing that can be shared with others",
    fields=[
        {"name": "share_count", "type": "integer", "default": 0},
        {"name": "visibility", "type": "enum", "values": ["private", "shared", "public"]}
    ],
    operations=["share_with", "unshare", "get_shared_with", "make_public"],
    keywords=["share", "shares", "sharing", "public", "private", "visibility", "access", "network"],
))

# --- NEW: SPECIALIZED patterns ---

register_template(MicroTemplate(
    id="has_price",
    name="Has Price",
    pattern=UniversalPattern.CONTAINER,
    description="A thing with monetary value",
    fields=[
        {"name": "price", "type": "decimal", "required": True},
        {"name": "currency", "type": "string", "default": "USD"},
        {"name": "discount", "type": "decimal", "nullable": True}
    ],
    operations=["set_price", "apply_discount", "get_final_price", "convert_currency"],
    keywords=["price", "cost", "fee", "charge", "pay", "buy", "sell", "dollar", "money", "billing"],
))

register_template(MicroTemplate(
    id="has_quantity",
    name="Has Quantity",
    pattern=UniversalPattern.CONTAINER,
    description="A thing with a countable amount",
    fields=[
        {"name": "quantity", "type": "integer", "default": 1},
        {"name": "unit", "type": "string", "nullable": True}
    ],
    operations=["increment", "decrement", "set_quantity", "check_stock"],
    keywords=["quantity", "amount", "count", "stock", "inventory", "items", "units"],
))

register_template(MicroTemplate(
    id="has_location",
    name="Has Location",
    pattern=UniversalPattern.CONTAINER,
    description="A thing with geographical coordinates",
    fields=[
        {"name": "latitude", "type": "float", "nullable": True},
        {"name": "longitude", "type": "float", "nullable": True},
        {"name": "address", "type": "string", "nullable": True}
    ],
    operations=["set_location", "get_nearby", "calculate_distance", "geocode"],
    keywords=["location", "address", "map", "geo", "place", "where", "coordinates", "nearby"],
))

register_template(MicroTemplate(
    id="has_duration",
    name="Has Duration",
    pattern=UniversalPattern.FLOW,
    description="A thing with start and end times",
    fields=[
        {"name": "start_time", "type": "datetime", "required": True},
        {"name": "end_time", "type": "datetime", "nullable": True},
        {"name": "duration_minutes", "type": "integer", "computed": True}
    ],
    operations=["set_duration", "extend", "get_remaining", "is_active"],
    keywords=["duration", "time", "start", "end", "length", "span", "period", "session"],
))

register_template(MicroTemplate(
    id="has_attachment",
    name="Has Attachment",
    pattern=UniversalPattern.CONTAINER,
    description="A thing with file attachments",
    fields=[
        {"name": "attachments", "type": "json", "default": "[]"},
        {"name": "max_attachments", "type": "integer", "default": 10}
    ],
    operations=["attach", "detach", "list_attachments", "download"],
    keywords=["attach", "file", "upload", "document", "image", "media", "photo"],
))

register_template(MicroTemplate(
    id="is_recurring",
    name="Is Recurring",
    pattern=UniversalPattern.FLOW,
    description="A thing that repeats on a schedule",
    fields=[
        {"name": "recurrence_rule", "type": "string", "nullable": True},
        {"name": "next_occurrence", "type": "datetime", "nullable": True}
    ],
    operations=["set_recurrence", "get_next", "skip_occurrence", "end_recurrence"],
    keywords=["recurring", "repeat", "daily", "weekly", "monthly", "schedule", "routine"],
))

register_template(MicroTemplate(
    id="has_priority",
    name="Has Priority",
    pattern=UniversalPattern.STATE,
    description="A thing with importance level",
    fields=[
        {"name": "priority", "type": "enum", "values": ["low", "medium", "high", "urgent"]}
    ],
    operations=["set_priority", "filter_by_priority", "sort_by_priority"],
    keywords=["priority", "importance", "urgent", "critical", "high", "low", "medium"],
))

# --- SEARCH/FILTER patterns ---

register_template(MicroTemplate(
    id="is_searchable",
    name="Is Searchable",
    pattern=UniversalPattern.CONTAINER,
    description="A thing with full-text search capability",
    fields=[
        {"name": "search_text", "type": "text", "computed": True}
    ],
    operations=["search", "autocomplete", "highlight_matches"],
    keywords=["search", "find", "lookup", "query", "filter"],
))

register_template(MicroTemplate(
    id="has_title",
    name="Has Title",
    pattern=UniversalPattern.CONTAINER,
    description="A thing with a name/title",
    fields=[
        {"name": "title", "type": "string", "required": True},
        {"name": "subtitle", "type": "string", "nullable": True}
    ],
    operations=["rename", "search_by_title"],
    keywords=["name", "title", "called", "named"],
))


# =============================================================================
# Enterprise Micro-Templates
# =============================================================================

register_template(MicroTemplate(
    id="has_roles",
    name="Has Roles (RBAC)",
    pattern=UniversalPattern.RELATIONSHIP,
    description="Role-based access control with permissions",
    fields=[
        {"name": "role", "type": "enum", "values": ["admin", "editor", "viewer", "guest"]},
        {"name": "permissions", "type": "json", "default": "[]"}
    ],
    operations=["assign_role", "check_permission", "list_by_role", "revoke_role"],
    requires=["has_owner"],
    keywords=["role", "permission", "admin", "editor", "viewer", "access", "rbac", "authorize"],
))

register_template(MicroTemplate(
    id="has_file_upload",
    name="Has File Upload",
    pattern=UniversalPattern.CONTAINER,
    description="Support for file uploads with storage",
    fields=[
        {"name": "file_path", "type": "string", "nullable": True},
        {"name": "file_name", "type": "string", "nullable": True},
        {"name": "file_size", "type": "integer", "nullable": True},
        {"name": "file_type", "type": "string", "nullable": True}
    ],
    operations=["upload_file", "download_file", "delete_file", "list_files"],
    keywords=["upload", "file", "download", "attachment", "document", "pdf", "image", "photo"],
))

register_template(MicroTemplate(
    id="has_email_notify",
    name="Has Email Notifications",
    pattern=UniversalPattern.FLOW,
    description="Email notification capabilities",
    fields=[
        {"name": "email_sent_at", "type": "datetime", "nullable": True},
        {"name": "email_status", "type": "enum", "values": ["pending", "sent", "failed"]}
    ],
    operations=["send_email", "queue_email", "get_email_history"],
    keywords=["email", "notify", "notification", "alert", "send", "mail", "message"],
))

register_template(MicroTemplate(
    id="has_background_job",
    name="Has Background Jobs",
    pattern=UniversalPattern.FLOW,
    description="Async background task processing",
    fields=[
        {"name": "job_id", "type": "string", "nullable": True},
        {"name": "job_status", "type": "enum", "values": ["queued", "running", "completed", "failed"]},
        {"name": "job_result", "type": "json", "nullable": True}
    ],
    operations=["queue_job", "get_job_status", "cancel_job", "retry_job"],
    keywords=["background", "async", "job", "task", "queue", "worker", "process", "celery"],
))

register_template(MicroTemplate(
    id="has_audit_log",
    name="Has Audit Log",
    pattern=UniversalPattern.STATE,
    description="Track all changes with audit trail",
    fields=[
        {"name": "audit_log", "type": "json", "default": "[]"},
        {"name": "last_modified_by", "type": "integer", "nullable": True}
    ],
    operations=["log_change", "get_audit_trail", "revert_to"],
    requires=["has_owner"],
    keywords=["audit", "log", "history", "track", "change", "who", "compliance"],
))

register_template(MicroTemplate(
    id="has_api_key",
    name="Has API Key Auth",
    pattern=UniversalPattern.RELATIONSHIP,
    description="API key authentication for external access",
    fields=[
        {"name": "api_key", "type": "string", "unique": True},
        {"name": "api_key_created", "type": "datetime", "nullable": True},
        {"name": "api_rate_limit", "type": "integer", "default": 1000}
    ],
    operations=["generate_api_key", "revoke_api_key", "check_api_key", "get_usage"],
    keywords=["api", "key", "token", "integration", "external", "webhook", "rest"],
))

register_template(MicroTemplate(
    id="has_multi_tenant",
    name="Multi-Tenant",
    pattern=UniversalPattern.HIERARCHY,
    description="Multi-tenant data isolation",
    fields=[
        {"name": "tenant_id", "type": "integer", "required": True},
        {"name": "tenant_name", "type": "string", "nullable": True}
    ],
    operations=["filter_by_tenant", "switch_tenant", "list_tenants"],
    keywords=["tenant", "organization", "company", "workspace", "team", "multi-tenant", "saas"],
))

register_template(MicroTemplate(
    id="has_soft_delete",
    name="Soft Delete",
    pattern=UniversalPattern.STATE,
    description="Soft delete with restore capability",
    fields=[
        {"name": "is_deleted", "type": "boolean", "default": False},
        {"name": "deleted_at", "type": "datetime", "nullable": True},
        {"name": "deleted_by", "type": "integer", "nullable": True}
    ],
    operations=["soft_delete", "restore", "purge", "list_deleted"],
    keywords=["delete", "trash", "archive", "restore", "undo", "recycle"],
))


# =============================================================================
# Template Composition Engine
# =============================================================================

@dataclass
class ComposedTemplate:
    """A template composed from multiple micro-templates."""
    name: str
    base_entity: str
    templates: List[str]  # IDs of micro-templates
    
    # Merged from all templates
    all_fields: List[Dict] = field(default_factory=list)
    all_operations: List[str] = field(default_factory=list)
    
    # Resolution info
    conflicts_resolved: List[str] = field(default_factory=list)
    dependencies_added: List[str] = field(default_factory=list)


class TemplateAlgebra:
    """
    Combines micro-templates using algebraic operations.
    
    Operations:
      + (merge): Combine two templates, merging fields
      - (remove): Remove a template's features
      & (intersect): Keep only shared features
      | (union): Include all features from both
    """
    
    def __init__(self):
        self.templates = MICRO_TEMPLATES
        self.compositions: Dict[str, ComposedTemplate] = {}
        self.user_templates: Dict[str, MicroTemplate] = {}
    
    def detect_templates(self, description: str) -> List[str]:
        """Detect which micro-templates apply to a description."""
        text = description.lower()
        matches = []
        
        for tid, template in self.templates.items():
            score = 0
            for keyword in template.keywords:
                if re.search(rf'\b{keyword}\b', text):
                    score += 1
            if score > 0:
                matches.append((tid, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: -x[1])
        return [m[0] for m in matches]
    
    def compose(self, entity_name: str, template_ids: List[str]) -> ComposedTemplate:
        """Compose multiple micro-templates into one."""
        all_fields = []
        all_operations = []
        all_requires = set()
        all_conflicts = set()
        field_names_seen = set()
        
        # First pass: collect all requirements and conflicts
        for tid in template_ids:
            if tid not in self.templates:
                continue
            template = self.templates[tid]
            all_requires.update(template.requires)
            all_conflicts.update(template.conflicts)
        
        # Add required templates
        dependencies_added = []
        for req in all_requires:
            if req not in template_ids and req in self.templates:
                dependencies_added.append(req)
        
        full_template_ids = list(template_ids) + dependencies_added
        
        # Check for conflicts
        conflicts_resolved = []
        for tid in full_template_ids[:]:
            if tid in all_conflicts:
                conflicts_resolved.append(f"Removed {tid} due to conflict")
                full_template_ids.remove(tid)
        
        # Second pass: merge fields and operations
        for tid in full_template_ids:
            if tid not in self.templates:
                continue
            template = self.templates[tid]
            
            # Merge fields (skip duplicates by name)
            for field in template.fields:
                if field['name'] not in field_names_seen:
                    all_fields.append(field)
                    field_names_seen.add(field['name'])
            
            # Merge operations (unique)
            for op in template.operations:
                if op not in all_operations:
                    all_operations.append(op)
        
        composed = ComposedTemplate(
            name=entity_name,
            base_entity=entity_name,
            templates=full_template_ids,
            all_fields=all_fields,
            all_operations=all_operations,
            conflicts_resolved=conflicts_resolved,
            dependencies_added=dependencies_added,
        )
        
        self.compositions[entity_name] = composed
        return composed
    
    def suggest_templates(self, description: str, current: List[str]) -> List[Tuple[str, str]]:
        """Suggest additional templates that would complement current ones."""
        suggestions = []
        
        # Patterns that commonly go together
        COMMON_PAIRS = {
            "has_owner": ["is_shareable", "has_lifecycle"],
            "has_items": ["is_orderable", "has_tags"],
            "has_status": ["has_workflow", "has_lifecycle"],
            "is_rateable": ["is_commentable", "has_owner"],
            "has_content": ["is_searchable", "has_version"],
            "is_nested": ["has_path", "is_orderable"],
        }
        
        for tid in current:
            if tid in COMMON_PAIRS:
                for suggestion in COMMON_PAIRS[tid]:
                    if suggestion not in current and suggestion in self.templates:
                        suggestions.append((
                            suggestion, 
                            f"Often used with {self.templates[tid].name}"
                        ))
        
        # Remove duplicates
        seen = set()
        unique_suggestions = []
        for s, reason in suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append((s, reason))
        
        return unique_suggestions
    
    def add_user_template(self, template: MicroTemplate):
        """Add a user-defined micro-template."""
        self.user_templates[template.id] = template
        self.templates[template.id] = template
    
    def save_composition(self, name: str, path: Path = None):
        """Save a composition for reuse."""
        if name not in self.compositions:
            return
        
        composition = self.compositions[name]
        data = {
            'name': composition.name,
            'base_entity': composition.base_entity,
            'templates': composition.templates,
            'fields': composition.all_fields,
            'operations': composition.all_operations,
        }
        
        if path is None:
            path = Path(__file__).parent / 'data' / 'compositions'
        path.mkdir(parents=True, exist_ok=True)
        
        with open(path / f'{name}.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_composition(self, name: str, path: Path = None) -> Optional[ComposedTemplate]:
        """Load a saved composition."""
        if path is None:
            path = Path(__file__).parent / 'data' / 'compositions'
        
        filepath = path / f'{name}.json'
        if not filepath.exists():
            return None
        
        with open(filepath) as f:
            data = json.load(f)
        
        composed = ComposedTemplate(
            name=data['name'],
            base_entity=data['base_entity'],
            templates=data['templates'],
            all_fields=data['fields'],
            all_operations=data['operations'],
        )
        self.compositions[name] = composed
        return composed
    
    def generate_model_code(self, composition: ComposedTemplate, framework: str = "flask") -> str:
        """Generate Python model code from a composition."""
        lines = [
            f"# Auto-generated model: {composition.name}",
            f"# Templates: {', '.join(composition.templates)}",
            "",
        ]
        
        if framework == "flask":
            lines.extend([
                "from flask_sqlalchemy import SQLAlchemy",
                "from datetime import datetime",
                "",
                "db = SQLAlchemy()",
                "",
                f"class {composition.name}(db.Model):",
                f"    __tablename__ = '{composition.name.lower()}s'",
                "    id = db.Column(db.Integer, primary_key=True)",
            ])
            
            for field in composition.all_fields:
                col_type = self._field_to_sqlalchemy(field)
                nullable = field.get('nullable', True)
                default = field.get('default')
                
                if default is not None:
                    if isinstance(default, str):
                        lines.append(f"    {field['name']} = db.Column({col_type}, default='{default}')")
                    else:
                        lines.append(f"    {field['name']} = db.Column({col_type}, default={default})")
                elif field.get('auto'):
                    lines.append(f"    {field['name']} = db.Column({col_type}, default=datetime.utcnow)")
                else:
                    lines.append(f"    {field['name']} = db.Column({col_type}, nullable={nullable})")
        
        return '\n'.join(lines)
    
    def _field_to_sqlalchemy(self, field: Dict) -> str:
        """Convert field type to SQLAlchemy column type."""
        type_map = {
            'string': 'db.String(255)',
            'text': 'db.Text',
            'integer': 'db.Integer',
            'float': 'db.Float',
            'boolean': 'db.Boolean',
            'datetime': 'db.DateTime',
            'json': 'db.JSON',
            'list': 'db.JSON',  # Store lists as JSON
            'enum': 'db.String(50)',
            'reference': 'db.Integer',
            'self_reference': 'db.Integer',
        }
        return type_map.get(field['type'], 'db.String(255)')
    
    def generate_api_code(self, composition: ComposedTemplate) -> str:
        """Generate Flask API routes from a composition."""
        entity = composition.name.lower()
        Entity = composition.name
        
        routes = [
            f"# Auto-generated API routes for {Entity}",
            f"# Operations: {', '.join(composition.all_operations[:10])}...",
            "",
            f"@app.route('/api/{entity}s', methods=['GET'])",
            f"def list_{entity}s():",
            f"    items = {Entity}.query.all()",
            f"    return jsonify([item.to_dict() for item in items])",
            "",
            f"@app.route('/api/{entity}s', methods=['POST'])",
            f"def create_{entity}():",
            f"    data = request.json",
            f"    item = {Entity}(**data)",
            f"    db.session.add(item)",
            f"    db.session.commit()",
            f"    return jsonify(item.to_dict()), 201",
        ]
        
        # Add operation-specific routes
        for op in composition.all_operations:
            if op == 'search':
                routes.extend([
                    "",
                    f"@app.route('/api/{entity}s/search', methods=['GET'])",
                    f"def search_{entity}s():",
                    f"    q = request.args.get('q', '')",
                    f"    items = {Entity}.query.filter({Entity}.title.ilike(f'%{{q}}%')).all()",
                    f"    return jsonify([item.to_dict() for item in items])",
                ])
            elif op == 'rate':
                routes.extend([
                    "",
                    f"@app.route('/api/{entity}s/<int:id>/rate', methods=['POST'])",
                    f"def rate_{entity}(id):",
                    f"    item = {Entity}.query.get_or_404(id)",
                    f"    rating = request.json.get('rating', 0)",
                    f"    item.rating_sum += rating",
                    f"    item.rating_count += 1",
                    f"    db.session.commit()",
                    f"    return jsonify(item.to_dict())",
                ])
        
        return '\n'.join(routes)


# =============================================================================
# Discovery Engine - Find new template combinations
# =============================================================================

class TemplateDiscovery:
    """
    Discovers new useful template combinations.
    Like an LLM exploring latent space, but:
    - No hallucination (all combinations are valid)
    - All local (no cloud)
    - Explainable (you can see exactly what templates combined)
    """
    
    def __init__(self, algebra: TemplateAlgebra):
        self.algebra = algebra
        self.successful_combos: List[Tuple[List[str], float]] = []
    
    def explore_combinations(self, base_templates: List[str], depth: int = 2) -> List[List[str]]:
        """Generate all valid combinations up to depth."""
        from itertools import combinations
        
        all_templates = list(self.algebra.templates.keys())
        candidates = []
        
        # Start with base, then add 1-2 more templates
        for r in range(1, min(depth + 1, len(all_templates))):
            for combo in combinations(all_templates, r):
                full_combo = list(set(base_templates + list(combo)))
                if self._is_valid_combo(full_combo):
                    candidates.append(full_combo)
        
        return candidates
    
    def _is_valid_combo(self, template_ids: List[str]) -> bool:
        """Check if a combination is valid (no unresolved conflicts)."""
        all_conflicts = set()
        all_ids = set(template_ids)
        
        for tid in template_ids:
            if tid in self.algebra.templates:
                template = self.algebra.templates[tid]
                for conflict in template.conflicts:
                    if conflict in all_ids:
                        return False
        
        return True
    
    def score_combination(self, template_ids: List[str], description: str) -> float:
        """Score how well a combination matches a description."""
        text = description.lower()
        score = 0.0
        
        for tid in template_ids:
            if tid in self.algebra.templates:
                template = self.algebra.templates[tid]
                for keyword in template.keywords:
                    if keyword in text:
                        score += 1.0
        
        # Normalize by number of templates (prefer simpler solutions)
        return score / (len(template_ids) ** 0.5) if template_ids else 0
    
    def find_best_combination(self, description: str, max_templates: int = 6) -> Tuple[List[str], float]:
        """Find the best template combination for a description."""
        detected = self.algebra.detect_templates(description)
        
        if not detected:
            return [], 0.0
        
        best_combo = detected[:max_templates]
        best_score = self.score_combination(best_combo, description)
        
        # Try adding complementary templates
        for suggested, _ in self.algebra.suggest_templates(description, detected[:3]):
            candidate = detected[:max_templates-1] + [suggested]
            score = self.score_combination(candidate, description)
            if score > best_score:
                best_combo = candidate
                best_score = score
        
        return best_combo, best_score
    
    def learn_from_success(self, template_ids: List[str], rating: float):
        """Learn from user feedback on a combination."""
        self.successful_combos.append((template_ids, rating))
        
        # If highly rated, consider making this a new template
        if rating >= 4.0:
            # Record successful pattern
            pass
    
    def get_pattern_insights(self) -> Dict[str, Any]:
        """Analyze successful combinations for patterns."""
        if not self.successful_combos:
            return {}
        
        # Count template co-occurrences
        co_occurrences = {}
        for combo, score in self.successful_combos:
            if score >= 3.0:
                for t1 in combo:
                    for t2 in combo:
                        if t1 < t2:
                            key = f"{t1}+{t2}"
                            co_occurrences[key] = co_occurrences.get(key, 0) + 1
        
        # Find most successful pairs
        top_pairs = sorted(co_occurrences.items(), key=lambda x: -x[1])[:10]
        
        return {
            'total_combinations_tried': len(self.successful_combos),
            'top_template_pairs': top_pairs,
            'avg_score': sum(s for _, s in self.successful_combos) / len(self.successful_combos),
        }


# =============================================================================
# Module API
# =============================================================================

algebra = TemplateAlgebra()
discovery = TemplateDiscovery(algebra)


def detect_patterns(description: str) -> List[str]:
    """Detect applicable micro-templates from description."""
    return algebra.detect_templates(description)


def compose(entity_name: str, template_ids: List[str]) -> ComposedTemplate:
    """Compose multiple templates into one."""
    return algebra.compose(entity_name, template_ids)


def auto_compose(description: str, entity_name: str = None) -> ComposedTemplate:
    """Automatically compose templates from a description."""
    template_ids, score = discovery.find_best_combination(description)
    
    if entity_name is None:
        # Extract entity name from description
        words = re.findall(r'\b[a-z]+\b', description.lower())
        entity_name = words[0].capitalize() if words else "Entity"
    
    return compose(entity_name, template_ids)


def list_templates() -> List[Dict]:
    """List all available micro-templates."""
    return [t.to_dict() for t in MICRO_TEMPLATES.values()]


def get_template(template_id: str) -> Optional[MicroTemplate]:
    """Get a specific template."""
    return MICRO_TEMPLATES.get(template_id)


# =============================================================================
# Test
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("TEMPLATE ALGEBRA TEST")
    print("=" * 60)
    
    test_descriptions = [
        "a recipe collection where I can rate and tag recipes",
        "a todo list with due dates and priorities",
        "a blog with comments and likes",
        "a file manager with folders and search",
        "a social network with followers and shares",
    ]
    
    for desc in test_descriptions:
        print(f"\n--- {desc} ---")
        
        # Detect templates
        detected = detect_patterns(desc)
        print(f"Detected templates: {detected[:6]}")
        
        # Auto-compose
        comp = auto_compose(desc)
        print(f"Composed: {comp.name}")
        print(f"  Templates: {comp.templates}")
        print(f"  Fields: {[f['name'] for f in comp.all_fields]}")
        print(f"  Operations: {comp.all_operations[:5]}...")
        
        # Suggest more
        suggestions = algebra.suggest_templates(desc, detected[:3])
        if suggestions:
            print(f"  Suggestions: {suggestions[:3]}")
    
    print("\n" + "=" * 60)
    print("AVAILABLE MICRO-TEMPLATES")
    print("=" * 60)
    
    by_pattern = {}
    for t in MICRO_TEMPLATES.values():
        p = t.pattern.value
        if p not in by_pattern:
            by_pattern[p] = []
        by_pattern[p].append(t.id)
    
    for pattern, templates in by_pattern.items():
        print(f"\n{pattern.upper()}: {templates}")
