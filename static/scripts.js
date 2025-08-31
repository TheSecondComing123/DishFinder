document.addEventListener('DOMContentLoaded', function () {
    // === Rating functionality (unchanged logic) ===
    document.querySelectorAll('.rating').forEach(ratingElement => {
        ratingElement.addEventListener('click', function () {
            const rating = this.dataset.rating;
            alert(`You rated this dish ${rating} stars!`);
        });
    });

    // === Tag filter functionality ===
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    const tagButtons = document.querySelectorAll('.tag-btn');
    const selectedTags = new Set(); // Maintain current tag state

    // Helper: normalize tag (trim + lowercase)
    const normalize = tag => tag.trim().toLowerCase();

    // Helper: apply tag button styles consistently
    function updateButtonState(button, active) {
        button.classList.toggle('active', active);
        button.classList.toggle('btn-success', active);
        button.classList.toggle('btn-outline-success', !active);
    }

    // Set button min-width on load (prevent width shift)
    tagButtons.forEach(button => {
        const width = button.offsetWidth;
        button.style.minWidth = width + 'px';
    });

    // Initialize selected tags from search input (if any)
    if (searchInput.value) {
        searchInput.value
            .split(',')
            .map(normalize)
            .filter(Boolean)
            .forEach(tag => {
                selectedTags.add(tag);

                tagButtons.forEach(button => {
                    if (normalize(button.dataset.tag) === tag) {
                        updateButtonState(button, true);
                    }
                });
            });
    }

    // Handle tag button click events
    tagButtons.forEach(button => {
        const tag = normalize(button.dataset.tag || '');

        button.addEventListener('click', function () {
            const isActive = this.classList.contains('active');

            // Update state and style
            if (isActive) {
                selectedTags.delete(tag);
                updateButtonState(this, false);
            } else {
                selectedTags.add(tag);
                updateButtonState(this, true);
            }

            // Sync search input with tag set
            searchInput.value = [...selectedTags].join(', ');
        });
    });
});
