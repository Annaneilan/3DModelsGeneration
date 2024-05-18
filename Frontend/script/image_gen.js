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
        this.image = document.getElementById("generated-image");
        this.generateImageButton = document.getElementById("bt-generate-image");
        this.uploadImageButton = document.getElementById("bt-upload-image");
        this.downloadImageButton = document.getElementById("bt-download-image");
    }

    setupControls() {
        this.generateImageButton.addEventListener(
            'click',
            () => { this.delegate.requestImageGen(); }
        );
        this.uploadImageButton.addEventListener(
            'change',
            () => { this.delegate.uploadImageFromFile(); }
        );
        this.downloadImageButton.addEventListener(
            'click',
            () => { this.delegate.downloadImage(); }
        );
    }

    subscribeToModel() {
        this.model.data.addListener(
            'onImageDidChange',
            () => { this.updateImage(); }
        );
        this.model.addListener(
            'onImageRequestFailed',
            () => { this.activateGenerateButton(); }
        )
    }

    // Update UI
    updateImage() {
        console.log("[ImageGenView:updateImage]");
        this.image.src = this.model.data.image;
        this.activateGenerateButton();
    }

    activateGenerateButton() {
        this.generateImageButton.disabled = false;
        this.generateImageButton.innerHTML = "Generate Image";
    }

    deactivateGenerateButton() {
        this.generateImageButton.disabled = true;
        this.generateImageButton.innerHTML = `
        <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
        <span role="status">Loading...</span>
        `;
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

        console.log("[ImageGenController:constructor]");
    }

    requestImageGen() {
        console.log("[ImageGenController:requestImageGen]")
        
        // Deactivate button
        this.view.deactivateGenerateButton();
        
        // Request data
        const promptData = {
            prompt: this.view.getImagePromptPositive(),
            negative_prompt: this.view.getImagePromptNegative()
        }
        this.model.requestImageGen(promptData);
    }

    uploadImageFromFile() {
        console.log("[ImageGenController:uploadImageFromFile]")

        const file = this.view.uploadImageButton.files[0];

        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                // Set own image
                this.model.data.setImage(e.target.result);
                this.model.data.projectId = null;
            }
            reader.readAsDataURL(file);

        } else {
            this.model.resetImage();
        }
    }

    downloadImage() {
        console.log("[ImageGenController:downloadImage]")

        if (!this.model.data.image) {
            console.log("[ImageGenController:downloadImage] no image to download");
            return;
        }

        const a = document.createElement('a');
        a.href = this.model.data.image;
        a.download = 'image.jpg';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
}

export { ImageGenController, ImageGenView };