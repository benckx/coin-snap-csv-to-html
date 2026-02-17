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
document.addEventListener('DOMContentLoaded', function() {
    handleResize();
    populateFilters();
});
window.addEventListener('resize', handleResize);

function populateFilters() {
    // Get all unique issuers from the data
    const tableRows = document.querySelectorAll('#tableBody tr');
    const issuers = new Set();

    tableRows.forEach(row => {
        const issuer = row.dataset.issuer;

        if (issuer && issuer.trim()) {
            issuers.add(issuer);
        }
    });

    // Populate issuer filter
    const issuerFilter = document.getElementById('issuerFilter');
    const sortedIssuers = Array.from(issuers).sort((a, b) => a.localeCompare(b));
    sortedIssuers.forEach(issuer => {
        const option = document.createElement('option');
        option.value = issuer;
        option.textContent = issuer;
        issuerFilter.appendChild(option);
    });

    // Initial population of denomination filter (all denominations)
    updateDenominationFilter();
}

function updateDenominationFilter() {
    const issuerFilter = document.getElementById('issuerFilter').value;
    const denominationFilter = document.getElementById('denominationFilter');
    const currentValue = denominationFilter.value; // Remember current selection

    // Clear existing options except "All"
    denominationFilter.innerHTML = '<option value="">All</option>';

    // Get denominations based on selected issuer and count occurrences
    const tableRows = document.querySelectorAll('#tableBody tr');
    const denominationCounts = new Map();

    tableRows.forEach(row => {
        const issuer = row.dataset.issuer;
        const denomination = row.dataset.denomination;

        // If an issuer is selected, only include denominations from that issuer
        if ((!issuerFilter || issuer === issuerFilter) && denomination && denomination.trim()) {
            denominationCounts.set(denomination, (denominationCounts.get(denomination) || 0) + 1);
        }
    });

    // Populate denomination filter with counts
    const sortedDenominations = Array.from(denominationCounts.keys()).sort((a, b) => a.localeCompare(b));
    sortedDenominations.forEach(denomination => {
        const count = denominationCounts.get(denomination);
        const option = document.createElement('option');
        option.value = denomination;
        option.textContent = `${denomination} (${count})`;
        denominationFilter.appendChild(option);
    });

    // Restore previous selection if it still exists, otherwise reset to "All"
    if (currentValue && denominationCounts.has(currentValue)) {
        denominationFilter.value = currentValue;
    } else {
        denominationFilter.value = ''; // Reset to "All" if current selection doesn't exist
    }
}

function filterCoins() {
    const issuerFilter = document.getElementById('issuerFilter').value.toLowerCase();

    // Update denomination filter options based on selected issuer
    updateDenominationFilter();

    // Get denomination filter value AFTER updating (it may have been reset)
    const denominationFilter = document.getElementById('denominationFilter').value.toLowerCase();

    // Filter table rows
    const tableRows = document.querySelectorAll('#tableBody tr');
    tableRows.forEach(row => {
        const issuer = (row.dataset.issuer || '').toLowerCase();
        const denomination = (row.dataset.denomination || '').toLowerCase();

        const issuerMatch = !issuerFilter || issuer === issuerFilter;
        const denominationMatch = !denominationFilter || denomination === denominationFilter;

        if (issuerMatch && denominationMatch) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });

    // Filter grid cards
    const gridCards = document.querySelectorAll('#gridContainer .coin-card');
    gridCards.forEach(card => {
        const issuer = (card.dataset.issuer || '').toLowerCase();
        const denomination = (card.dataset.denomination || '').toLowerCase();

        const issuerMatch = !issuerFilter || issuer === issuerFilter;
        const denominationMatch = !denominationFilter || denomination === denominationFilter;

        if (issuerMatch && denominationMatch) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

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
