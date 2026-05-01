import pkgutil
import importlib


class PluginManager:

    def load_plugins(self):

        plugins = []
        package = "docai.plugins"

        try:
            base_module = importlib.import_module(package)
        except ModuleNotFoundError:
            print(f"[ERROR] Package not found: {package}")
            return []

        print(f"[DEBUG] Scanning plugins in: {list(base_module.__path__)}")

        for finder, name, ispkg in pkgutil.iter_modules(base_module.__path__):

            print(f"[DEBUG] Found: {name}, ispkg={ispkg}")

            try:
                # Try loading plugin module inside folder
                module = importlib.import_module(
                    f"{package}.{name}.plugin"
                )
            except ModuleNotFoundError as e:
                print(f"[WARN] Skipping {name}: plugin module not found ({e})")
                continue
            except Exception as e:
                print(f"[ERROR] Failed loading {name}: {e}")
                continue

            plugin_class = getattr(module, "Plugin", None)

            if not plugin_class:
                print(f"[WARN] No Plugin class in {name}")
                continue

            try:
                plugin = plugin_class()
                print(f"[INFO] Loaded plugin: {plugin.name}")
                plugins.append(plugin)
            except Exception as e:
                print(f"[ERROR] Failed to initialize plugin {name}: {e}")

        if not plugins:
            print("[WARN] No plugins loaded")

        return plugins