document.addEventListener('DOMContentLoaded', function() {
    // Fade in the main content
    const main = document.querySelector('main');
    main.style.opacity = 0;
    
    setTimeout(() => {
        main.style.transition = 'opacity 0.5s ease';
        main.style.opacity = 1;
    }, 100);
    
    // Add smooth animation to all cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = 0;
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, 100 + (index * 100));
    });
    
    // Animate feature icons
    const icons = document.querySelectorAll('.feature-icon');
    icons.forEach((icon, index) => {
        setTimeout(() => {
            icon.style.opacity = '0';
            icon.style.opacity = '1';
            icon.style.transition = 'transform 0.5s ease';
            icon.style.transform = 'scale(1.2)';
            setTimeout(() => {
                icon.style.transform = 'scale(1)';
            }, 300);
        }, 500 + (index * 150));
    });

    // Initialize tooltips if Bootstrap is used
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    // Handle department selection for semester loading
    const departmentSelect = document.querySelector('select[name="department"]');
    const semesterSelect = document.querySelector('select[name="semester"]');
    
    if (departmentSelect && semesterSelect) {
        departmentSelect.addEventListener('change', function() {
            const departmentId = this.value;
            
            // Clear current semesters
            semesterSelect.innerHTML = '<option value="">Loading...</option>';
            
            // Fetch semesters for the selected department
            fetch(`/api/department/${departmentId}/semesters/`)
                .then(response => response.json())
                .then(data => {
                    semesterSelect.innerHTML = '';
                    
                    if (data.length === 0) {
                        semesterSelect.innerHTML = '<option value="">No semesters available</option>';
                    } else {
                        data.forEach(semester => {
                            const option = document.createElement('option');
                            option.value = semester.id;
                            option.textContent = `Semester ${semester.number}`;
                            semesterSelect.appendChild(option);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error fetching semesters:', error);
                    semesterSelect.innerHTML = '<option value="">Error loading semesters</option>';
                });
        });
    }

    // Resource search functionality
    const searchInput = document.getElementById('resource-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const resourceItems = document.querySelectorAll('.resource-item');
            
            resourceItems.forEach(item => {
                const title = item.querySelector('.card-title').textContent.toLowerCase();
                const description = item.querySelector('.card-text')?.textContent.toLowerCase() || '';
                
                if (title.includes(searchTerm) || description.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // Vote buttons handling
    const voteButtons = document.querySelectorAll('#upvote-btn, #downvote-btn');
    voteButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.dataset.resourceId) return;
            
            const voteType = this.id === 'upvote-btn' ? 'upvote' : 'downvote';
            const resourceId = this.dataset.resourceId;
            
            fetch(`/resources/${resourceId}/vote/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCSRFToken()
                },
                body: `vote_type=${voteType}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('upvote-count').textContent = data.upvotes;
                    document.getElementById('downvote-count').textContent = data.downvotes;
                }
            })
            .catch(error => {
                console.error('Error voting:', error);
            });
        });
    });

    // Enhance department cards if they exist
    const departmentCards = document.querySelectorAll('.department-card');
    if (departmentCards.length > 0) {
        departmentCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                const icon = this.querySelector('.dept-icon-container i');
                if (icon) {
                    icon.style.transition = 'transform 0.3s ease';
                    icon.style.transform = 'scale(1.2)';
                }
            });
            
            card.addEventListener('mouseleave', function() {
                const icon = this.querySelector('.dept-icon-container i');
                if (icon) {
                    icon.style.transform = 'scale(1)';
                }
            });
        });
    }

    // Helper function to get CSRF token
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
});
