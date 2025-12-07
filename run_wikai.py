#!/usr/bin/env python3
"""
📚 WIKAI Standalone Launcher

Run the WIKAI Commons Browser independently, without the full Convergence Engine.

Usage:
    python run_wikai.py [--port PORT]

Access at: http://localhost:5000/wikai
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(description='Run WIKAI Commons Browser')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    print("=" * 60)
    print("📚 WIKAI - The Wikipedia for Artificial Intelligence")
    print("=" * 60)
    print()
    
    # Check for existing patterns
    from wikai import WIKAILibrarian
    librarian = WIKAILibrarian()
    patterns = librarian.query()
    
    print(f"📊 Commons Status:")
    print(f"   Patterns: {len(patterns)}")
    print(f"   Axioms:   {sum(1 for p in patterns if p.axiom)}")
    print()
    
    if patterns:
        print("🦋 Recent Patterns:")
        for p in patterns[:5]:
            print(f"   • {p.id}: {p.name}")
        print()
    
    # Create minimal Flask app for standalone mode
    from flask import Flask, redirect
    app = Flask(__name__)
    
    # Register WIKAI routes
    from wikai.web_ui import register_wikai_routes
    register_wikai_routes(app)
    
    # Redirect root to WIKAI
    @app.route('/')
    def index():
        return redirect('/wikai')
    
    print(f"🌐 Starting WIKAI server on port {args.port}...")
    print(f"   Open: http://localhost:{args.port}/wikai")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        app.run(
            host='0.0.0.0',
            port=args.port,
            debug=args.debug,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n📚 WIKAI server stopped.")


if __name__ == '__main__':
    main()
