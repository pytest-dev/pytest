# Troubleshooting Notes (Easy)

If the container bails immediately, check whether `sitecustomize.py` imported `alpha_cyclic`. Recursion errors usually mean both packages were imported eagerly.
