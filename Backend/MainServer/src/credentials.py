class AWSCredentials:
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: str
    ) -> None:
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.session_token = session_token