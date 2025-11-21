"""
trait_hub.py
Flexible trait translation hub with plug-in mapping support.
"""
import importlib.util
import os
import glob

class TraitHub:
    def __init__(self, plugin_dir='trait_plugins'):
        self.mappings = {}
        self.load_plugins(plugin_dir)

    def load_plugins(self, plugin_dir):
        # Load all Python plugin files in the directory
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        import importlib.util
        for plugin_path in glob.glob(os.path.join(plugin_dir, '*.py')):
            if os.path.basename(plugin_path) == '__init__.py':
                continue  # Skip __init__.py
            module_name = os.path.splitext(os.path.basename(plugin_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'TRAIT_MAP'):
                self.mappings.update(module.TRAIT_MAP)

    def translate(self, traits: dict):
        results = []
        for k, v in traits.items():
            label, desc = self.mappings.get(k, (k, 'No description available.'))
            results.append({
                'trait': k,
                'label': label,
                'description': desc,
                'value': v
            })
        return results

    def print_translation(self, traits: dict):
        translations = self.translate(traits)
        for t in translations:
            print(f"{t['label']} ({t['trait']}): {t['value']} — {t['description']}")

# Example usage
if __name__ == "__main__":
    hub = TraitHub()
    sample_traits = {
        'cpu_usage': 87.2,
        'memory_kb': 2048,
        'speed': 120.5,
        'custom_metric': 42
    }
    hub.print_translation(sample_traits)
