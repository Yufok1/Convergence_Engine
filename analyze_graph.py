import json

# Load the graph API response
try:
    with open('c:/Users/Jeff Towers/.cursor/projects/f-Amoeba-Convergence-Engine/agent-tools/3d3118bc-ed07-463c-9a9b-2d2ee3269d34.txt', 'r') as f:
        content = f.read()

    # Try to parse as JSON
    try:
        data = json.loads(content)
        print('=== CAUSATION GRAPH ANALYSIS ===')
        print(f'Graph Keys: {list(data.keys())}')

        if 'nodes' in data:
            nodes = data['nodes']
            print(f'Nodes: {len(nodes)}')

            # Analyze node types
            components = {}
            for node in nodes:
                comp = node.get('component', 'unknown')
                components[comp] = components.get(comp, 0) + 1

            print('\nNode Components:')
            for comp, count in sorted(components.items(), key=lambda x: x[1], reverse=True):
                print(f'  {comp}: {count}')

        if 'links' in data:
            links = data['links']
            print(f'Links: {len(links)}')

            # Analyze link types
            link_types = {}
            for link in links:
                link_type = link.get('type', 'unknown')
                link_types[link_type] = link_types.get(link_type, 0) + 1

            print('\nLink Types:')
            for link_type, count in sorted(link_types.items(), key=lambda x: x[1], reverse=True):
                print(f'  {link_type}: {count}')

        # Show sample nodes
        if 'nodes' in data and data['nodes']:
            print('\nSample Nodes:')
            for node in data['nodes'][:5]:
                print(f'  ID: {node.get("id", "?")[:20]} | Component: {node.get("component", "?")} | Type: {node.get("event_type", "?")}')

        # Show sample links
        if 'links' in data and data['links']:
            print('\nSample Links:')
            for link in data['links'][:5]:
                source = link.get('source', '?')
                target = link.get('target', '?')
                link_type = link.get('type', '?')
                print(f'  {source[:15]} -> {target[:15]} ({link_type})')

    except json.JSONDecodeError:
        print('Response is not JSON. First 500 chars:')
        print(content[:500])

except Exception as e:
    print(f'Error: {e}')
