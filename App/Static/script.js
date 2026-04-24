/* ── REQUESTS PAGE ─────────────────────────────────────────── */

let requestsSortState = {};

function sortRequestsTable(col) {
    const table = document.getElementById("requestsTable");
    if (!table) return;
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    requestsSortState[col] = !requestsSortState[col];
    const asc = requestsSortState[col];

    rows.sort((a, b) => {
        let A = a.cells[col].innerText.trim();
        let B = b.cells[col].innerText.trim();
        const numA = parseFloat(A);
        const numB = parseFloat(B);
        if (!isNaN(numA) && !isNaN(numB)) return asc ? numA - numB : numB - numA;
        return asc ? A.localeCompare(B) : B.localeCompare(A);
    });

    rows.forEach(r => tbody.appendChild(r));

    document.querySelectorAll("#requestsTable th.sortable .arrow").forEach(a => a.textContent = "↕");
    const active = document.querySelectorAll("#requestsTable th.sortable")[col - 2];
    if (active) active.querySelector(".arrow").textContent = asc ? "▲" : "▼";
}

function openAddModal() {
    document.getElementById("modalTitle").innerText = "New Request";
    document.getElementById("modalSubmitBtn").innerText = "Submit";
    document.getElementById("requestForm").action = "/requests/add";
    document.getElementById("modal").style.display = "flex";
}

function openUpdateModal(id, title, justification) {
    document.getElementById("modalTitle").innerText = "Update Request";
    document.getElementById("modalSubmitBtn").innerText = "Update";
    document.getElementById("requestForm").action = "/requests/update";
    document.getElementById("requestID").value = id;
    document.getElementById("requestTitle").value = title;
    document.getElementById("requestJustification").value = justification;
    document.getElementById("modal").style.display = "flex";
}

function closeModal() {
    document.getElementById("modal").style.display = "none";
}

function openActionModal(id) {
    document.getElementById("approveLink").href = "/requests/approve/" + id;
    document.getElementById("declineLink").href = "/requests/decline/" + id;
    document.getElementById("actionModal").style.display = "flex";
}

function closeActionModal() {
    document.getElementById("actionModal").style.display = "none";
}

function openDetailsModal(id) {
    document.getElementById("detailsContent").innerHTML =
        "<p>Items for request <strong>" + id + "</strong> will appear here.</p>";
    document.getElementById("detailsModal").style.display = "flex";
}

function closeDetailsModal() {
    document.getElementById("detailsModal").style.display = "none";
}

/* ── INVENTORY PAGE ────────────────────────────────────────── */

let inventorySortState = {};

function sortInventoryTable(col) {
    const table = document.getElementById("inventoryTable");
    if (!table) return;
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    inventorySortState[col] = !inventorySortState[col];
    const asc = inventorySortState[col];

    rows.sort((a, b) => {
        let A = a.cells[col].innerText.trim();
        let B = b.cells[col].innerText.trim();
        const numA = parseFloat(A);
        const numB = parseFloat(B);
        if (!isNaN(numA) && !isNaN(numB)) return asc ? numA - numB : numB - numA;
        return asc ? A.localeCompare(B) : B.localeCompare(A);
    });

    rows.forEach(r => tbody.appendChild(r));

    document.querySelectorAll("#inventoryTable th span.arrow").forEach(a => a.textContent = "↕");
    document.querySelectorAll("#inventoryTable th")[col].querySelector(".arrow").textContent = asc ? "▲" : "▼";
}

function searchTable() {
    const input = document.getElementById("searchInput");
    if (!input) return;
    const filter = input.value.toLowerCase();
    const table = document.getElementById("inventoryTable");
    const rows = table.getElementsByTagName("tr");
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        row.style.display = row.innerText.toLowerCase().includes(filter) ? "" : "none";
    }
}

function openAddItemModal() {
    document.getElementById("modalTitle").innerText = "Add Item";
    document.getElementById("modalSubmitBtn").innerText = "Add Item";
    document.getElementById("itemForm").action = "/inventory/add";
    document.getElementById("modal").style.display = "flex";
}

function openUpdateItemModal(id, name, description, quantity, photo) {
    document.getElementById("modalTitle").innerText = "Update Item";
    document.getElementById("modalSubmitBtn").innerText = "Update";
    document.getElementById("itemForm").action = "/inventory/update";
    document.getElementById("itemID").value = id;
    document.getElementById("itemName").value = name;
    document.getElementById("itemDescription").value = description;
    document.getElementById("itemquantity").value = quantity;
    document.getElementById("itemphoto").value = photo;
    document.getElementById("modal").style.display = "flex";
}

function closeItemModal() {
    document.getElementById("modal").style.display = "none";
}