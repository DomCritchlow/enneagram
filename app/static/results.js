/**
 * Results Page JavaScript
 * Handles animations, spider chart visualization, and print functionality
 */

// Global variables that will be populated by the template
let scores = {};
let topType = 1;

// Add smooth animations and initialize functionality
document.addEventListener('DOMContentLoaded', () => {
    // Load chart data from data attributes (CSP compliant)
    const chartDataElement = document.getElementById('chartData');
    if (chartDataElement) {
        try {
            const scoresData = JSON.parse(chartDataElement.getAttribute('data-scores'));
            const topTypeData = parseInt(chartDataElement.getAttribute('data-top-type'));
            setChartData(scoresData, topTypeData);
        } catch (error) {
            console.error('Error loading chart data:', error);
        }
    }
    
    // Smooth card animations
    const cards = document.querySelectorAll('.results-card, .privacy-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 150);
    });
    
    // Initialize chart
    drawSpiderChart();
});

function setChartData(scoresData, topTypeData) {
    scores = scoresData;
    topType = topTypeData;
}

function drawSpiderChart() {
    const maxScore = Math.max(...Object.values(scores));
    
    const chartElement = document.getElementById('spiderChart');
    if (!chartElement || !scores) return;
    
    // Responsive sizing
    const isMobile = window.innerWidth <= 768;
    const size = isMobile ? 250 : 300;
    const center = size / 2;
    const maxRadius = size * 0.4;
    
    // Create SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    
    const centerX = center;
    const centerY = center;
    
    // Draw background circles (grid)
    for (let i = 1; i <= 5; i++) {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', centerX);
        circle.setAttribute('cy', centerY);
        circle.setAttribute('r', (maxRadius / 5) * i);
        circle.setAttribute('fill', 'none');
        circle.setAttribute('stroke', '#e0e0e0');
        circle.setAttribute('stroke-width', '1');
        svg.appendChild(circle);
    }
    
    // Draw axes and labels
    const angleStep = (2 * Math.PI) / 9;
    for (let i = 1; i <= 9; i++) {
        const angle = angleStep * (i - 1) - Math.PI / 2; // Start from top
        const x2 = centerX + maxRadius * Math.cos(angle);
        const y2 = centerY + maxRadius * Math.sin(angle);
        
        // Draw axis line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', centerX);
        line.setAttribute('y1', centerY);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', '#e0e0e0');
        line.setAttribute('stroke-width', '1');
        svg.appendChild(line);
        
        // Add type number label
        const labelX = centerX + (maxRadius + 20) * Math.cos(angle);
        const labelY = centerY + (maxRadius + 20) * Math.sin(angle);
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', labelX);
        text.setAttribute('y', labelY);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-size', '14');
        text.setAttribute('font-weight', i === topType ? 'bold' : 'normal');
        text.setAttribute('fill', i === topType ? '#6366f1' : '#666');
        text.textContent = i;
        svg.appendChild(text);
    }
    
    // Draw data polygon
    const points = [];
    for (let i = 1; i <= 9; i++) {
        const angle = angleStep * (i - 1) - Math.PI / 2;
        const score = scores[i] || 0;
        const radius = (score / maxScore) * maxRadius;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        points.push(`${x},${y}`);
    }
    
    const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', points.join(' '));
    polygon.setAttribute('fill', 'rgba(99, 102, 241, 0.2)');
    polygon.setAttribute('stroke', '#6366f1');
    polygon.setAttribute('stroke-width', '2');
    svg.appendChild(polygon);
    
    // Add score dots
    for (let i = 1; i <= 9; i++) {
        const angle = angleStep * (i - 1) - Math.PI / 2;
        const score = scores[i] || 0;
        const radius = (score / maxScore) * maxRadius;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', x);
        circle.setAttribute('cy', y);
        circle.setAttribute('r', i === topType ? '6' : '4');
        circle.setAttribute('fill', i === topType ? '#6366f1' : '#ffffff');
        circle.setAttribute('stroke', '#6366f1');
        circle.setAttribute('stroke-width', '2');
        svg.appendChild(circle);
    }
    
    chartElement.appendChild(svg);
}

