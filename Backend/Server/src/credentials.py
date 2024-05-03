import json
from pathlib import Path
from typing import Union, Dict

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
    
    @staticmethod
    def from_json(json: dict) -> Union["AWSCredentials", None]:
        try:
            return AWSCredentials(
                access_key_id=json["AccessKeyId"],
                secret_access_key=json["SecretAccessKey"],
                session_token=json["SessionToken"]
            )
        except Exception as e:
            print(f"Failed to parse credentials from JSON: {e}")

        return None
    
    @staticmethod
    def from_json_file(path: Union[Path, str]) -> Union["AWSCredentials", None]:
        path = Path(path)
        
        # Veriffy file exists
        if not path.exists() or not path.is_file():
            print(f"No file: {path}")
            return None
        
        # Try: read & parse
        try:
            with open(path, "r") as file:
                file_content = file.read()
            return AWSCredentials.from_json(file_content)
        
        except Exception as e:
            print(f"Failed to parse credentials from file: {e}")
        
        return None