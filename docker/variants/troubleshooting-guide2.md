# Troubleshooting Notes (Medium)

Use `pip show alpha-cyclic` and `pip show beta-cyclic` to inspect the `Requires` metadata; both insist on each other, so the resolver can never converge without manual intervention.
