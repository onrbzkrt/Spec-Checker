"""Create (or update) the 'Part Register' list on the SharePoint site. Safe to run repeatedly.

Usage:  python -m scripts.provision
"""
from __future__ import annotations

from spec_checker.config import Settings
from spec_checker.graph import GraphClient
from spec_checker.schema import PART_REGISTER_COLUMNS


def main() -> None:
    settings = Settings.from_env()
    graph = GraphClient(settings.tenant_id, settings.client_id, settings.client_secret)

    site = graph.get_site(settings.site_host, settings.site_path)
    print(f"Site: {site['displayName']}  ({site['webUrl']})")

    existing = graph.find_list(site["id"], settings.register_list)
    if existing is None:
        created = graph.create_list(site["id"], settings.register_list, PART_REGISTER_COLUMNS)
        print(f"Created list '{settings.register_list}' with {len(PART_REGISTER_COLUMNS)} columns")
        print(f"Open it: {created['webUrl']}")
        return

    have = {col["name"] for col in graph.list_columns(site["id"], existing["id"])}
    missing = [col for col in PART_REGISTER_COLUMNS if col["name"] not in have]
    for col in missing:
        graph.add_column(site["id"], existing["id"], col)
        print(f"  + added column {col['name']}")
    print(f"List '{settings.register_list}' already exists; {len(missing)} column(s) added")
    print(f"Open it: {existing['webUrl']}")


if __name__ == "__main__":
    main()
