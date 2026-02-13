"""
Compliance Module - Web Ethics, Privacy Laws, and Data Protection
==================================================================
Generates legal compliance features based on:
- Detected data collection (auth, analytics, payments)
- Target jurisdiction (EU/GDPR, US/CCPA, global)
- App category and data sensitivity

Features:
- Cookie consent banner (GDPR/ePrivacy compliant)
- Privacy policy generator (based on data model)
- GDPR data rights (export, delete, consent tracking)
- CCPA compliance (Do Not Sell, opt-out)
- Terms of Service template
- Data retention policies
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum


class Jurisdiction(Enum):
    """Legal jurisdictions with different compliance requirements."""
    GLOBAL = "global"       # Minimal compliance (US baseline)
    EU = "eu"               # GDPR (strictest)
    US_CA = "us_ca"         # CCPA (California)
    US = "us"               # General US (minimal)
    UK = "uk"               # UK GDPR (post-Brexit)


class DataCategory(Enum):
    """Categories of personal data with different sensitivity levels."""
    NONE = "none"                   # No personal data
    BASIC = "basic"                 # Name, email
    SENSITIVE = "sensitive"         # Health, financial
    SPECIAL = "special"             # Race, religion, biometrics (GDPR Article 9)


@dataclass
class ComplianceRequirements:
    """What compliance features are needed for an app."""
    cookie_consent: bool = False        # Cookie banner needed
    privacy_policy: bool = False        # Privacy policy page
    terms_of_service: bool = False      # ToS page
    gdpr_rights: bool = False           # Export/delete data APIs
    ccpa_opt_out: bool = False          # Do Not Sell link
    consent_tracking: bool = False      # Store user consent in DB
    data_retention: bool = False        # Auto-delete old data
    age_verification: bool = False      # 13+ (COPPA) or 16+ (GDPR)
    ssl_required: bool = False          # HTTPS enforcement
    
    jurisdictions: Set[Jurisdiction] = field(default_factory=set)
    data_categories: Set[DataCategory] = field(default_factory=set)
    data_fields: List[str] = field(default_factory=list)
    
    def needs_compliance(self) -> bool:
        """Check if any compliance features are needed."""
        return any([
            self.cookie_consent, self.privacy_policy, self.gdpr_rights,
            self.ccpa_opt_out, self.consent_tracking, self.data_retention
        ])


# =============================================================================
# DETECTION PATTERNS
# =============================================================================

# Patterns that indicate personal data collection
PERSONAL_DATA_PATTERNS = {
    "auth": [
        r"\b(login|sign.?in|sign.?up|register|auth|user|account|password)\b",
        r"\b(profile|email|username|member)\b",
    ],
    "analytics": [
        r"\b(analytics|track|monitor|metric|statistic|visit|pageview)\b",
        r"\b(google.?analytics|gtag|ga4|mixpanel|amplitude|posthog)\b",
    ],
    "payment": [
        r"\b(payment|pay|checkout|credit.?card|stripe|paypal|billing)\b",
        r"\b(subscription|purchase|buy|cart|order)\b",
    ],
    "health": [
        r"\b(health|medical|patient|diagnosis|symptom|medication|prescription)\b",
        r"\b(fitness|workout|exercise|weight|bmi|calorie|heart.?rate)\b",
    ],
    "financial": [
        r"\b(bank|finance|budget|expense|income|salary|tax|invoice)\b",
        r"\b(investment|stock|portfolio|trading|crypto)\b",
    ],
    "location": [
        r"\b(location|gps|geolocation|map|address|nearby)\b",
    ],
    "children": [
        r"\b(kid|child|minor|school|student|education|learning)\b",
        r"\b(parent|family|age)\b",
    ],
}

# Patterns that indicate target regions
REGION_PATTERNS = {
    Jurisdiction.EU: [
        r"\b(eu|europe|european|gdpr|germany|france|spain|italy|netherlands)\b",
        r"\b(austria|belgium|czech|denmark|finland|greece|ireland|poland|portugal|sweden)\b",
    ],
    Jurisdiction.UK: [
        r"\b(uk|united.?kingdom|britain|british|england|scotland|wales)\b",
    ],
    Jurisdiction.US_CA: [
        r"\b(california|ccpa|cpra)\b",
    ],
    Jurisdiction.US: [
        r"\b(us|usa|united.?states|america|american)\b",
    ],
}


def detect_data_collection(description: str, model_fields: List[str] = None) -> ComplianceRequirements:
    """
    Analyze description and model fields to determine compliance needs.
    
    Args:
        description: Natural language app description
        model_fields: List of field names from domain models (e.g., ['email', 'password', 'name'])
    
    Returns:
        ComplianceRequirements with detected needs
    """
    desc_lower = description.lower()
    fields = [f.lower() for f in (model_fields or [])]
    combined = desc_lower + " " + " ".join(fields)
    
    req = ComplianceRequirements()
    
    # Detect data categories
    for category, patterns in PERSONAL_DATA_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                if category == "auth":
                    req.data_categories.add(DataCategory.BASIC)
                    req.privacy_policy = True
                elif category in ("health", "financial"):
                    req.data_categories.add(DataCategory.SENSITIVE)
                    req.privacy_policy = True
                    req.ssl_required = True
                elif category == "analytics":
                    req.cookie_consent = True
                elif category == "payment":
                    req.data_categories.add(DataCategory.SENSITIVE)
                    req.privacy_policy = True
                    req.terms_of_service = True
                    req.ssl_required = True
                elif category == "children":
                    req.age_verification = True
                break
    
    # Detect target regions
    for jurisdiction, patterns in REGION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                req.jurisdictions.add(jurisdiction)
                break
    
    # Apply jurisdiction-specific requirements
    if Jurisdiction.EU in req.jurisdictions or Jurisdiction.UK in req.jurisdictions:
        req.gdpr_rights = True
        req.consent_tracking = True
        if req.data_categories:
            req.cookie_consent = True
            req.privacy_policy = True
    
    if Jurisdiction.US_CA in req.jurisdictions:
        req.ccpa_opt_out = True
        req.privacy_policy = True
    
    # Store detected field names for privacy policy generation
    sensitive_fields = ["email", "password", "name", "phone", "address", "credit", 
                       "ssn", "dob", "birth", "age", "health", "medical", "salary"]
    req.data_fields = [f for f in fields if any(s in f for s in sensitive_fields)]
    
    return req


# =============================================================================
# SMART QUESTIONS FOR COMPLIANCE
# =============================================================================

def get_compliance_questions(description: str, model_fields: List[str] = None) -> List[dict]:
    """
    Generate smart questions about compliance needs.
    Only asks questions that can't be inferred from the description.
    
    Returns:
        List of question dicts compatible with smartq.py format
    """
    req = detect_data_collection(description, model_fields)
    questions = []
    
    # Only ask about jurisdiction if we detect personal data but no region
    if req.data_categories and not req.jurisdictions:
        questions.append({
            "id": "compliance_eu",
            "text": "Will users from the EU access this app?",
            "hint": "Requires GDPR compliance (cookie consent, data rights)",
            "category": "compliance",
            "inferred": None,  # Can't infer, must ask
        })
    
    # Only ask about analytics if not already detected
    if not req.cookie_consent and req.data_categories:
        questions.append({
            "id": "compliance_analytics",
            "text": "Will you use analytics or tracking?",
            "hint": "Requires cookie consent banner",
            "category": "compliance",
            "inferred": None,
        })
    
    return questions


def apply_compliance_answers(req: ComplianceRequirements, answers: Dict[str, bool]) -> ComplianceRequirements:
    """
    Update compliance requirements based on user answers.
    """
    if answers.get("compliance_eu"):
        req.jurisdictions.add(Jurisdiction.EU)
        req.gdpr_rights = True
        req.consent_tracking = True
        req.cookie_consent = True
        req.privacy_policy = True
    
    if answers.get("compliance_analytics"):
        req.cookie_consent = True
    
    return req


# =============================================================================
# CODE GENERATION - COOKIE CONSENT
# =============================================================================

def generate_cookie_consent_html() -> str:
    """Generate cookie consent banner HTML/CSS/JS."""
    return '''
<!-- Cookie Consent Banner -->
<div id="cookie-consent" class="cookie-banner" style="display:none">
    <div class="cookie-content">
        <p>We use cookies to improve your experience. By continuing, you agree to our 
        <a href="/privacy">Privacy Policy</a>.</p>
        <div class="cookie-buttons">
            <button onclick="acceptCookies()" class="btn-primary">Accept All</button>
            <button onclick="rejectCookies()" class="btn-secondary">Essential Only</button>
        </div>
    </div>
</div>

<style>
.cookie-banner {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--color-surface, #fff);
    border-top: 1px solid var(--color-border, #ddd);
    padding: 16px 24px;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    z-index: 9999;
}
.cookie-content {
    max-width: 900px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
}
.cookie-content p {
    margin: 0;
    font-size: 14px;
    color: var(--color-text-muted, #666);
}
.cookie-buttons {
    display: flex;
    gap: 10px;
}
@media (max-width: 600px) {
    .cookie-content { flex-direction: column; text-align: center; }
    .cookie-buttons { width: 100%; justify-content: center; }
}
</style>

<script>
// Cookie consent management
(function() {
    var consent = localStorage.getItem('cookie_consent');
    if (!consent) {
        document.getElementById('cookie-consent').style.display = 'block';
    } else if (consent === 'accepted') {
        loadAnalytics();
    }
})();

function acceptCookies() {
    localStorage.setItem('cookie_consent', 'accepted');
    localStorage.setItem('cookie_consent_date', new Date().toISOString());
    document.getElementById('cookie-consent').style.display = 'none';
    loadAnalytics();
}

function rejectCookies() {
    localStorage.setItem('cookie_consent', 'rejected');
    localStorage.setItem('cookie_consent_date', new Date().toISOString());
    document.getElementById('cookie-consent').style.display = 'none';
}

function loadAnalytics() {
    // Placeholder for analytics scripts
    // Add your Google Analytics, Mixpanel, etc. here
    console.log('Analytics loaded (consent granted)');
}
</script>
'''


def generate_cookie_consent_js() -> str:
    """Generate standalone JS for cookie consent (for apps that inject JS separately)."""
    return '''
// Cookie consent management
var cookieConsent = {
    check: function() {
        return localStorage.getItem('cookie_consent');
    },
    accept: function() {
        localStorage.setItem('cookie_consent', 'accepted');
        localStorage.setItem('cookie_consent_date', new Date().toISOString());
        this.hideBar();
        this.loadAnalytics();
    },
    reject: function() {
        localStorage.setItem('cookie_consent', 'rejected');
        localStorage.setItem('cookie_consent_date', new Date().toISOString());
        this.hideBar();
    },
    showBar: function() {
        var el = document.getElementById('cookie-consent');
        if (el) el.style.display = 'block';
    },
    hideBar: function() {
        var el = document.getElementById('cookie-consent');
        if (el) el.style.display = 'none';
    },
    loadAnalytics: function() {
        // Override this with your analytics loading code
        console.log('Analytics loaded');
    },
    init: function() {
        if (!this.check()) {
            this.showBar();
        } else if (this.check() === 'accepted') {
            this.loadAnalytics();
        }
    }
};
document.addEventListener('DOMContentLoaded', function() { cookieConsent.init(); });
'''


# =============================================================================
# CODE GENERATION - PRIVACY POLICY
# =============================================================================

def generate_privacy_policy_html(app_name: str, data_fields: List[str], 
                                  jurisdictions: Set[Jurisdiction]) -> str:
    """Generate a privacy policy page based on collected data and jurisdictions."""
    
    # Categorize data fields
    data_sections = []
    if any(f in str(data_fields) for f in ["email", "name", "username"]):
        data_sections.append(("Account Information", "Email address, username, and profile information"))
    if any(f in str(data_fields) for f in ["password"]):
        data_sections.append(("Security Data", "Encrypted passwords and authentication tokens"))
    if any(f in str(data_fields) for f in ["address", "phone", "location"]):
        data_sections.append(("Contact Information", "Address, phone number, or location data"))
    if any(f in str(data_fields) for f in ["health", "medical", "fitness", "weight"]):
        data_sections.append(("Health Data", "Health and fitness information you provide"))
    if any(f in str(data_fields) for f in ["payment", "credit", "card", "bank"]):
        data_sections.append(("Payment Information", "Payment details processed securely"))
    
    if not data_sections:
        data_sections.append(("Usage Data", "Information about how you use the app"))
    
    data_list = "\n".join([f"<li><strong>{cat}:</strong> {desc}</li>" for cat, desc in data_sections])
    
    # GDPR section
    gdpr_section = ""
    if Jurisdiction.EU in jurisdictions or Jurisdiction.UK in jurisdictions:
        gdpr_section = '''
<h2>Your Rights (GDPR)</h2>
<p>If you are in the EU/EEA or UK, you have the following rights:</p>
<ul>
    <li><strong>Access:</strong> Request a copy of your data (<a href="/api/me/export">Export Data</a>)</li>
    <li><strong>Rectification:</strong> Correct inaccurate data</li>
    <li><strong>Erasure:</strong> Delete your account and data (<a href="/api/me/delete">Delete Account</a>)</li>
    <li><strong>Portability:</strong> Receive your data in a portable format</li>
    <li><strong>Objection:</strong> Object to certain processing</li>
    <li><strong>Withdraw Consent:</strong> Withdraw consent at any time</li>
</ul>
'''
    
    # CCPA section
    ccpa_section = ""
    if Jurisdiction.US_CA in jurisdictions:
        ccpa_section = '''
<h2>California Privacy Rights (CCPA)</h2>
<p>If you are a California resident, you have the right to:</p>
<ul>
    <li>Know what personal information is collected</li>
    <li>Know if your data is sold or disclosed</li>
    <li>Say no to the sale of your data</li>
    <li>Access your personal information</li>
    <li>Request deletion of your data</li>
    <li>Not be discriminated against for exercising your rights</li>
</ul>
<p><strong>We do not sell your personal information.</strong></p>
'''
    
    return f'''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Privacy Policy - {app_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
               max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333; }}
        h1 {{ color: #111; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
        a {{ color: #0066cc; }}
        .updated {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <h1>Privacy Policy</h1>
    <p class="updated">Last updated: {__import__('datetime').date.today().isoformat()}</p>
    
    <h2>Information We Collect</h2>
    <p>We collect the following types of information:</p>
    <ul>
        {data_list}
    </ul>
    
    <h2>How We Use Your Information</h2>
    <p>We use your information to:</p>
    <ul>
        <li>Provide and improve our services</li>
        <li>Communicate with you about your account</li>
        <li>Ensure security and prevent fraud</li>
    </ul>
    
    <h2>Data Storage and Security</h2>
    <p>Your data is stored securely and protected with industry-standard encryption. 
    We retain your data only as long as necessary to provide our services.</p>
    
    <h2>Cookies</h2>
    <p>We use cookies for:</p>
    <ul>
        <li><strong>Essential cookies:</strong> Required for the app to function</li>
        <li><strong>Analytics cookies:</strong> Help us understand usage (with your consent)</li>
    </ul>
    <p>You can manage cookie preferences when you first visit the site.</p>
    
    {gdpr_section}
    {ccpa_section}
    
    <h2>Contact Us</h2>
    <p>For privacy inquiries, contact us at: [your-email@example.com]</p>
    
    <p><a href="/">&larr; Back to App</a></p>
</body>
</html>
'''


# =============================================================================
# CODE GENERATION - GDPR DATA RIGHTS APIs
# =============================================================================

def generate_gdpr_routes() -> str:
    """Generate Flask routes for GDPR data rights (export, delete)."""
    return '''
# =============================================================================
# GDPR Data Rights
# =============================================================================

@app.route('/api/me/export', methods=['GET'])
def export_my_data():
    """Export all user data (GDPR Article 20 - Data Portability)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Collect all user data
    export_data = {
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None,
        },
        'data': {}
    }
    
    # Add related data from all models
    # TODO: Dynamically add related model data based on foreign keys
    
    return jsonify(export_data)


@app.route('/api/me/delete', methods=['DELETE'])
def delete_my_account():
    """Delete user account and all data (GDPR Article 17 - Right to Erasure)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Delete all related data first (cascade)
    # TODO: Add cascade deletion for related models
    
    # Delete user
    db_session.delete(user)
    db_session.commit()
    
    # Clear session
    session.clear()
    
    return jsonify({'message': 'Account deleted successfully'})


@app.route('/api/consent', methods=['POST'])
def record_consent():
    """Record user consent for GDPR compliance."""
    data = request.get_json() or {}
    consent_type = data.get('type', 'cookies')  # cookies, marketing, analytics
    granted = data.get('granted', False)
    
    # Store in localStorage on client side, but also log server-side
    # This creates an audit trail for compliance
    consent_record = {
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'consent_type': consent_type,
        'granted': granted,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    # TODO: Store in consent_logs table
    app.logger.info(f"Consent recorded: {consent_record}")
    
    return jsonify({'message': 'Consent recorded', 'granted': granted})
'''


# =============================================================================
# CODE GENERATION - CCPA COMPLIANCE
# =============================================================================

def generate_ccpa_footer_html() -> str:
    """Generate CCPA-compliant footer with Do Not Sell link."""
    return '''
<footer class="legal-footer">
    <p>
        <a href="/privacy">Privacy Policy</a> &nbsp;|&nbsp;
        <a href="/terms">Terms of Service</a> &nbsp;|&nbsp;
        <a href="#" onclick="showDoNotSell()">Do Not Sell My Personal Information</a>
    </p>
</footer>

<script>
function showDoNotSell() {
    alert('We do not sell your personal information. For data requests, contact us at [email].');
}
</script>

<style>
.legal-footer {
    margin-top: 40px;
    padding: 20px;
    text-align: center;
    font-size: 13px;
    color: var(--color-text-muted, #888);
    border-top: 1px solid var(--color-border, #eee);
}
.legal-footer a {
    color: var(--color-text-muted, #888);
    text-decoration: none;
}
.legal-footer a:hover {
    text-decoration: underline;
}
</style>
'''


# =============================================================================
# MAIN INTEGRATION FUNCTION
# =============================================================================

def generate_compliance_features(app_name: str, description: str, 
                                  answers: Dict[str, bool],
                                  model_fields: List[str] = None) -> Dict[str, str]:
    """
    Generate all compliance features for an app.
    
    Args:
        app_name: Name of the app
        description: App description
        answers: User answers including compliance_eu, compliance_analytics
        model_fields: List of field names from domain models
    
    Returns:
        Dict of filename -> content for compliance files/code
    """
    # Detect initial requirements
    req = detect_data_collection(description, model_fields)
    
    # Apply user answers
    req = apply_compliance_answers(req, answers)
    
    result = {}
    
    # Cookie consent banner (injected into index.html)
    if req.cookie_consent:
        result['cookie_consent_html'] = generate_cookie_consent_html()
        result['cookie_consent_js'] = generate_cookie_consent_js()
    
    # Privacy policy page
    if req.privacy_policy:
        result['templates/privacy.html'] = generate_privacy_policy_html(
            app_name, req.data_fields, req.jurisdictions
        )
    
    # GDPR routes (injected into app.py)
    if req.gdpr_rights:
        result['gdpr_routes'] = generate_gdpr_routes()
    
    # CCPA footer
    if req.ccpa_opt_out:
        result['ccpa_footer_html'] = generate_ccpa_footer_html()
    
    return result


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Compliance Module Test")
    print("=" * 60)
    
    # Test detection
    test_cases = [
        ("a todo list app", []),
        ("a recipe app with user login", ["email", "password", "name"]),
        ("health tracking app for European users", ["weight", "calories", "email"]),
        ("e-commerce store with payments", ["email", "address", "credit_card"]),
        ("analytics dashboard for California businesses", ["email", "company"]),
    ]
    
    for desc, fields in test_cases:
        print(f"\n--- {desc} ---")
        req = detect_data_collection(desc, fields)
        print(f"  Cookie consent: {req.cookie_consent}")
        print(f"  Privacy policy: {req.privacy_policy}")
        print(f"  GDPR rights: {req.gdpr_rights}")
        print(f"  CCPA opt-out: {req.ccpa_opt_out}")
        print(f"  Jurisdictions: {[j.value for j in req.jurisdictions]}")
        print(f"  Data categories: {[d.value for d in req.data_categories]}")
    
    print("\n" + "=" * 60)
    print("Sample Cookie Consent Banner")
    print("=" * 60)
    print(generate_cookie_consent_html()[:500] + "...")
