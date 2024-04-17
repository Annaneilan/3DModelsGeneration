document.addEventListener('DOMContentLoaded', function() {
    const inputPhoto = document.getElementById('input-photo');
    const generatedPhoto = document.getElementById('generated-photo');

    inputPhoto.addEventListener('change', function() {
        const file = this.files[0];

        if (file) {
            const reader = new FileReader();

            reader.onload = function(e) {
                generatedPhoto.src = e.target.result;
            };

            reader.readAsDataURL(file);
        } else {
            generatedPhoto.src = 'placeholder.jpg'; 
        }
    });
});


document.addEventListener('DOMContentLoaded', function () {
    const downloadBtn = document.getElementById('download-photo');
    const generatedPhoto = document.getElementById('generated-photo');

    downloadBtn.addEventListener('click', function () {
        const url = generatedPhoto.src;
        const a = document.createElement('a');
        a.href = url;
        a.download = 'image.jpg';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
});

function requestImageGen() {
    // Const
    const url = "http://192.168.0.7:25565"

    // Get input elements
    const posPromptInput = document.getElementById('input-description')
    const negPromptInput = document.getElementById('without-description')

    // Request data
    const promptData = {
        prompt: posPromptInput.value,
        negative_prompt: negPromptInput.value
    }

    // Send request
    fetch(url + '/image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(promptData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('HTTP error! Status: ${response.status}');
        }
        return response.blob(); // Process the response as Blob
    })
    .then(blob => {
        const imageUrl = URL.createObjectURL(blob);
        const imgElement = document.getElementById('generated-photo');
        imgElement.src = imageUrl;
    })
    .catch(error => {
        console.error('Error fetching the image:', error);
    });
}
