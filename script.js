let sortAscending = true;

function isMobile() {
    return window.innerWidth <= 768;
}

function setView(view) {
    // On mobile, always force grid view
    if (isMobile()) {
        view = 'grid';
    }

    const tableContainer = document.getElementById('tableContainer');
    const gridContainer = document.getElementById('gridContainer');
    const listBtn = document.getElementById('listViewBtn');
    const gridBtn = document.getElementById('gridViewBtn');

    if (view === 'list') {
        tableContainer.classList.remove('hidden');
        gridContainer.classList.add('hidden');
        listBtn.classList.add('active');
        gridBtn.classList.remove('active');
    } else {
        tableContainer.classList.add('hidden');
        gridContainer.classList.remove('hidden');
        gridContainer.classList.add('active');
        listBtn.classList.remove('active');
        gridBtn.classList.add('active');
    }
}

// Auto-switch to grid view on mobile when page loads or resizes
function handleResize() {
    if (isMobile()) {
        setView('grid');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', handleResize);
window.addEventListener('resize', handleResize);

function toggleSortOrder() {
    sortAscending = !sortAscending;
    document.getElementById('sortOrderBtn').textContent = sortAscending ? '↑' : '↓';
    sortCoins();
}

function sortCoins() {
    const sortBy = document.getElementById('sortSelect').value;
    if (!sortBy) return;

    // Sort table rows
    const tbody = document.getElementById('tableBody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        let aVal = a.dataset[sortBy] || '';
        let bVal = b.dataset[sortBy] || '';

        // Numeric sort for year and value
        if (sortBy === 'year' || sortBy === 'value') {
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
            return sortAscending ? aVal - bVal : bVal - aVal;
        }

        // String sort for others - case insensitive
        aVal = aVal.toString().toLowerCase();
        bVal = bVal.toString().toLowerCase();

        if (aVal < bVal) return sortAscending ? -1 : 1;
        if (aVal > bVal) return sortAscending ? 1 : -1;
        return 0;
    });

    rows.forEach(row => tbody.appendChild(row));

    // Sort grid cards
    const gridContainer = document.getElementById('gridContainer');
    const cards = Array.from(gridContainer.querySelectorAll('.coin-card'));

    cards.sort((a, b) => {
        let aVal = a.dataset[sortBy] || '';
        let bVal = b.dataset[sortBy] || '';

        if (sortBy === 'year' || sortBy === 'value') {
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
            return sortAscending ? aVal - bVal : bVal - aVal;
        }

        // String sort for others - case insensitive
        aVal = aVal.toString().toLowerCase();
        bVal = bVal.toString().toLowerCase();

        if (aVal < bVal) return sortAscending ? -1 : 1;
        if (aVal > bVal) return sortAscending ? 1 : -1;
        return 0;
    });

    cards.forEach(card => gridContainer.appendChild(card));
}

