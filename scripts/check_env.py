import sys

packages = ['torch', 'torch_geometric', 'networkx', 'scipy', 'numpy', 'sklearn', 'pandas', 'fastapi']
for pkg in packages:
    try:
        m = __import__(pkg)
        v = getattr(m, '__version__', 'installed')
        print(f"{pkg}: {v}")
    except ImportError as e:
        print(f"{pkg}: NOT INSTALLED ({e})")

