import io

from src.aws.credentials import AWSCredentials
from src.model import MeshGenServerModel

credentials = AWSCredentials.from_json_file("../credentials.json")
model = MeshGenServerModel(credentials)
model.run()