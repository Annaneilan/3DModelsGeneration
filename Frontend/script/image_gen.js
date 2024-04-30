class ImageGenView {
    constructor(
        model,
        delegate
    ) {
        // Ref
        this.model = model;
        this.delegate = delegate;

        this.setupUI();
        this.setupControls();

        this.subscribeToModel();

        console.log("ImageGenView initialized");
    }
    
    setupUI() {
        this.generatedImage = document.getElementById('generated-photo');
        this.generateImageButton = document.getElementById('generate-image');
    }

    setupControls() {
        this.generateImageButton.addEventListener(
            'click',
            () => { this.delegate.requestImageGen() }
        );
    }

    subscribeToModel() {
        this.model.data.addListener('onImageWillChange', () => { this.updateGeneratedImage });
    }

    // Update UI
    updateGeneratedImage() {
        this.generatedImage.src = model.image;
    }

    // Getters
    getImagePromptPositive() {
        return document.getElementById('input-description').value;
    }

    getImagePromptNegative() {
        return document.getElementById('without-description').value;
    }
}

class ImageGenController {
    constructor(model) {
        this.model = model;
        this.view = new ImageGenView(model, this);

        console.log("ImageGenController initialized");
    }

    requestImageGen() {
        console.log(this.view);

        // Request data
        const promptData = {
            prompt: this.view.getImagePromptPositive(),
            negative_prompt: this.view.getImagePromptNegative()
        }
        this.model.requestImageGen(promptData);
    }
}

export { ImageGenController, ImageGenView };