def parse_domain_allowlist(value: str) -> list:
    return [domain.strip().lower() for domain in value.split(",") if domain.strip()]
