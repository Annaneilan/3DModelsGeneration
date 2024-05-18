
class DataKey:

    @staticmethod
    def image(project_id: str) -> str:
        return f"{project_id}/image.png"
    
    @staticmethod
    def mesh(
        project_id: str,
        perspective: bool= True,
        textured: bool = True
    ) -> str:
        mesh_dir = "perspective" if perspective else "object"
        mesh_file = "textured" if textured else "mesh"
        return f"{project_id}/{mesh_dir}/{mesh_file}.zip"