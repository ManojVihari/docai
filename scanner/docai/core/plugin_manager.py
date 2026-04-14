import pkgutil
import importlib


class PluginManager:

    def load_plugins(self):

        plugins = []

        package = "docai.plugins"
        for _, name, ispkg in pkgutil.iter_modules(
            importlib.import_module(package).__path__
        ):

            # ✅ ONLY process folders (plugins), skip files like base_plugin.py
            if not ispkg:
                continue

            try:
                module = importlib.import_module(
                    f"{package}.{name}.plugin"
                )
            except ModuleNotFoundError:
                continue

            plugin_class = getattr(module, "Plugin", None)

            if not plugin_class:
                continue

            plugin = plugin_class()

            print(f"Loaded plugin: {plugin.name}")

            plugins.append(plugin)

        return plugins