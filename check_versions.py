import importlib

# List all libraries you use
packages = [
    "streamlit",
    "pydeck",
    "pandas",
    "geopandas",
    "shapely",
    "joblib",
    "scikit-learn",
    "numpy",
    "json",
]

print("📦 Checking installed package versions...\n")

for pkg in packages:
    try:
        module = importlib.import_module(pkg)
        version = getattr(module, "__version__", "unknown")
        print(f"{pkg:<15} {version}")
    except ModuleNotFoundError:
        print(f"{pkg:<15} ❌ Not installed")
    except Exception as e:
        print(f"{pkg:<15} ⚠️ Error: {e}")

print("\n✅ Done.")
