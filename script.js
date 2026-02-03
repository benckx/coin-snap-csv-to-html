let sortAscending = true;

function setView(view) {
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

        // String sort for others
        return sortAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
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

        return sortAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });

    cards.forEach(card => gridContainer.appendChild(card));
}

