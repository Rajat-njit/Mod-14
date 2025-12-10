import pkgutil
import app

# Auto-import every module inside `app.*`
for _, module_name, _ in pkgutil.walk_packages(app.__path__, "app."):
    __import__(module_name)
