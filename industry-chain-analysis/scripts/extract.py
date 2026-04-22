import json
import logging
import argparse

# mock data extraction script for industry chain knowledge
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def fetch_industry_data(target_name: str) -> dict:
    """
    Simulates fetching industry chain data (Upstream, Midstream, Downstream)
    from a financial database or Knowledge Graph API.
    """
    logging.info(f"Fetching industry chain data for: {target_name}")
    
    # Mock return data
    mock_data = {
        "target": target_name,
        "upstream": [
            {"subcategory": "Raw Materials", "companies": ["Corp A", "Corp B"]},
            {"subcategory": "Equipment", "companies": ["Corp C"]}
        ],
        "midstream": [
            {"subcategory": "Core Manufacturing", "companies": [target_name] if "Corp" in target_name else ["Corp D", "Corp E"]},
        ],
        "downstream": [
            {"subcategory": "Consumer Electronics", "companies": ["Brand X", "Brand Y"]},
            {"subcategory": "Automotive", "companies": ["Brand Z"]}
        ]
    }
    return mock_data

def generate_mermaid(data: dict) -> str:
    """
    Generates a simple Mermaid graph based on the fetched data.
    """
    lines = ["graph LR"]
    lines.append("  subgraph Upstream")
    for idx, item in enumerate(data['upstream']):
        lines.append(f"    U{idx}[{item['subcategory']}]")
    lines.append("  end")
    
    lines.append("  subgraph Midstream")
    for idx, item in enumerate(data['midstream']):
        lines.append(f"    M{idx}[{item['subcategory']}]")
    lines.append("  end")
    
    lines.append("  subgraph Downstream")
    for idx, item in enumerate(data['downstream']):
        lines.append(f"    D{idx}[{item['subcategory']}]")
    lines.append("  end")
    
    # connections
    lines.append("  U0 --> M0")
    lines.append("  M0 --> D0")
    lines.append("  M0 --> D1")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Extract industry chain data.")
    parser.add_argument("--target", type=str, required=True, help="Industry or Company name")
    args = parser.parse_args()
    
    data = fetch_industry_data(args.target)
    mermaid_graph = generate_mermaid(data)
    
    output = {
        "raw_data": data,
        "mermaid_syntax": mermaid_graph
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
