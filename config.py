from dotenv import dotenv_values, load_dotenv


class Settings:
    def __init__(self, source: str = "env"):
        self.source = source
        self._secrets = self._load()

    def _load(self):
        if self.source == "env":
            load_dotenv()
            return dict(dotenv_values())
        elif self.source == "vault":
            # Placeholder for vault-based loading
            raise NotImplementedError("Vault integration not yet implemented.")
        else:
            raise ValueError(f"Unsupported secret source: {self.source}")

    def get(self, key: str, default=None):
        return self._secrets.get(key, default)

    def all(self):
        return self._secrets.copy()
