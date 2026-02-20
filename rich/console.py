class Console:
    def print(self, *args, **kwargs):
        # simple print to stdout for tests
        print(*args)

    def rule(self, title):
        print(f"--- {title} ---")
