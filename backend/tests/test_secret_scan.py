from scripts.secret_scan import find_secret_findings


def test_secret_scan_detects_real_supabase_secret_like_value():
    secret = "sb_" + "secret_" + "abcdefghijklmnopqrstuvwxyz1234567890"
    findings = find_secret_findings(
        "backend.py",
        f"SUPABASE_SECRET_KEY={secret}\n",
    )

    assert findings
    assert findings[0].kind == "supabase_secret_key"


def test_secret_scan_ignores_placeholders_and_public_publishable_key():
    text = "\n".join(
        [
            "SUPABASE_SECRET_KEY=",
            "SUPABASE_PUBLISHABLE_KEY=sb_publishable_abcdefghijklmnopqrstuvwxyz1234567890",
            "DATABASE_URL=postgresql://user:password@host:5432/db",
        ]
    )

    assert find_secret_findings(".env.example", text) == []


def test_secret_scan_flags_real_secret_like_value_in_env_example():
    secret = "sb_" + "secret_" + "abcdefghijklmnopqrstuvwxyz1234567890"
    findings = find_secret_findings(
        ".env.example",
        f"SUPABASE_SECRET_KEY={secret}\n",
    )

    assert findings
    assert findings[0].kind == "supabase_secret_key"


def test_secret_scan_flags_real_postgres_password_even_when_line_mentions_password():
    database_url = "postgresql://app_user:" + "real-db-secret" + "@db.example.com:5432/app"
    findings = find_secret_findings(
        "README.md",
        f"DATABASE_PASSWORD_URL={database_url}\n",
    )

    assert findings
    assert findings[0].kind == "postgres_password_url"
