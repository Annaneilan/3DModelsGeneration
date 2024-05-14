class MeshGenParams {
    constructor(
        perspective = true,
        textured = true,
        meshing = true
    ) {
        this.perspective = perspective;
        this.textured = textured;
        this.meshing = meshing;
    }
}

export { MeshGenParams };