/**
 * Types Page JavaScript
 * Handles type cards animations and expand/collapse functionality
 */

// Add smooth animations
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.type-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Handle expand/collapse functionality
    const expandButtons = document.querySelectorAll('.expand-btn');
    expandButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            toggleExpand(button);
        });
    });
});

function toggleExpand(button) {
    const section = button.dataset.section;
    const typeNum = button.dataset.type;
    const list = button.closest('.preview-list');
    const hiddenItems = list.querySelectorAll('.hidden-item');
    const expandText = button.querySelector('.expand-text');
    const collapseText = button.querySelector('.collapse-text');
    
    const isExpanded = expandText.style.display === 'none';
    
    hiddenItems.forEach(item => {
        if (isExpanded) {
            // Collapse
            item.style.display = 'none';
        } else {
            // Expand
            item.style.display = 'block';
        }
    });
    
    // Toggle button text
    if (isExpanded) {
        expandText.style.display = 'inline';
        collapseText.style.display = 'none';
    } else {
        expandText.style.display = 'none';
        collapseText.style.display = 'inline';
    }
}
