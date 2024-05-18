from aws.credentials import AWSCredentials
from model import ObjectMeshGenModel

credentials = AWSCredentials.from_json_file("../credentials.json")
model = ObjectMeshGenModel(credentials)
model.run()