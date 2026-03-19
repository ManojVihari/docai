import pkgutil
import importlib


class PluginManager:

    def load_plugins(self):

        plugins = []

        package = "docai.plugins"

        for _, name, _ in pkgutil.iter_modules(
            importlib.import_module(package).__path__
        ):

            module = importlib.import_module(
                f"{package}.{name}.plugin"
            )

            plugin_class = getattr(module, "Plugin")

            plugin = plugin_class()

            print(f"Loaded plugin: {plugin.name}")

            plugins.append(plugin)

        return plugins