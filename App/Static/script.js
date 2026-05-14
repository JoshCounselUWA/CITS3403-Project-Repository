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
        
        let A = a.cells[col].dataset.sort ?? a.cells[col].innerText.trim();
        let B = b.cells[col].dataset.sort ?? b.cells[col].innerText.trim();

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
    document.getElementById("requestForm").reset();
    updateDateInputColours();
    resetItemPicker();
    document.getElementById("modal").style.display = "flex";
}

function openUpdateModal(id, title, justification, eventDateStart, eventDateEnd, returnDate) {
    document.getElementById("modalTitle").innerText = "Update Request";
    document.getElementById("modalSubmitBtn").innerText = "Update";
    document.getElementById("requestForm").action = "/requests/" + id;
    document.getElementById("requestID").value = id;
    document.getElementById("requestTitle").value = title;
    document.getElementById("requestJustification").value = justification;

    const eventDateStartField = document.getElementById("eventDateStart");
    const eventDateEndField = document.getElementById("eventDateEnd");
    const returnDateField = document.getElementById("returnDate");

    if (eventDateStartField) eventDateStartField.value = eventDateStart || "";
    if (eventDateEndField) eventDateEndField.value = eventDateEnd || "";
    if (returnDateField) returnDateField.value = returnDate || "";
    updateDateInputColours();

    resetItemPicker();

    fetch('/requests/items/' + id)
        .then(r => r.json())
        .then(data => {
            data.items.forEach(item => {
                pickedItems[item.itemID] = {
                    name: item.itemName,
                    quantity: item.quantity,
                    available: item.itemquantity
                };
            });
            renderPickedItems();
            syncItemsJSON();
        });

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
    const content = document.getElementById("detailsContent");
    content.innerHTML = "<p style='color:rgba(255,255,255,0.5);'>Loading...</p>";
    document.getElementById("detailsModal").style.display = "flex";

    fetch('/requests/items/' + id)
        .then(r => r.json())
        .then(data => {
            if (data.items.length === 0) {
                content.innerHTML = "<p style='color:rgba(255,255,255,0.4);'>No items on this request.</p>";
                return;
            }
            content.innerHTML = `
                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr>
                            <th style="text-align:left; padding:6px 8px; color:rgba(255,255,255,0.6); font-size:0.8rem; border-bottom:1px solid rgba(255,255,255,0.1);">Item</th>
                            <th style="text-align:right; padding:6px 8px; color:rgba(255,255,255,0.6); font-size:0.8rem; border-bottom:1px solid rgba(255,255,255,0.1);">Qty Requested</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.items.map(item => `
                            <tr>
                                <td style="padding:6px 8px; color:white; font-size:0.9rem;">${item.itemName}</td>
                                <td style="padding:6px 8px; color:white; font-size:0.9rem; text-align:right;">${item.quantity}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(() => {
            content.innerHTML = "<p style='color:rgba(255,100,100,0.7);'>Failed to load items.</p>";
        });
}

function closeDetailsModal() {
    document.getElementById("detailsModal").style.display = "none";
}

/* ── ITEM PICKER (for request modal) ──────────────────────── */

let allInventoryItems = [];
let pickedItems = {};

async function loadInventoryItems() {
    try {
        const res = await fetch('/inventory/json');
        const data = await res.json();
        allInventoryItems = data.items;
    } catch (e) {
        console.error("Failed to load inventory items:", e);
    }
}

function filterItemDropdown() {
    const query = document.getElementById("itemSearch").value.toLowerCase();
    const dropdown = document.getElementById("itemDropdown");

    if (!query) {
        dropdown.style.display = "none";
        return;
    }

    const matches = allInventoryItems.filter(i =>
        i.itemName.toLowerCase().includes(query) && !pickedItems[i.itemID]
    );

    if (matches.length === 0) {
        dropdown.innerHTML = "<div style='padding:8px 10px; color:rgba(255,255,255,0.4); font-size:0.85rem;'>No items found.</div>";
        dropdown.style.display = "block";
        return;
    }

    dropdown.innerHTML = matches.map(i => {
    const available = Number(i.itemquantity);
    const isOutOfStock = available <= 0;
    const safeName = i.itemName.replace(/'/g, "\\'");

    return `
        <div
            ${isOutOfStock ? "" : `onclick="pickItem(${i.itemID}, '${safeName}', ${available})"`}
            style="
                padding:8px 10px;
                cursor:${isOutOfStock ? "not-allowed" : "pointer"};
                color:${isOutOfStock ? "rgba(255,255,255,0.35)" : "white"};
                border-bottom:1px solid rgba(255,255,255,0.07);
            "
            ${isOutOfStock ? "" : "onmouseover=\"this.style.background='rgba(56,189,248,0.1)'\""}
            ${isOutOfStock ? "" : "onmouseout=\"this.style.background='transparent'\""}
        >
            ${i.itemName}
            <span style="opacity:0.5; font-size:0.8rem;">
                ${isOutOfStock ? "(Out of stock)" : `(${available} available)`}
            </span>
        </div>
    `;
}).join('');

    dropdown.style.display = "block";
}

function pickItem(id, name, available) {
    available = Number(available);

    if (available <= 0) {
        return;
    }

    pickedItems[id] = { name, quantity: 1, available };
    document.getElementById("itemSearch").value = "";
    document.getElementById("itemDropdown").style.display = "none";
    renderPickedItems();
    syncItemsJSON();
}

function removePickedItem(id) {
    delete pickedItems[id];
    renderPickedItems();
    syncItemsJSON();
}

function updatePickedQty(id, qty) {
    if (pickedItems[id]) {
        pickedItems[id].quantity = Math.max(1, parseInt(qty) || 1);
        syncItemsJSON();
    }
}

function renderPickedItems() {
    const container = document.getElementById("pickedItems");
    if (!container) return;

    if (Object.keys(pickedItems).length === 0) {
        container.innerHTML = '<p style="color:rgba(255,255,255,0.3); font-size:0.85rem; margin:4px 0;">No items added yet.</p>';
        return;
    }

    container.innerHTML = Object.entries(pickedItems).map(([id, item]) => `
        <div style="display:flex; align-items:center; gap:8px; background:rgba(255,255,255,0.04);
                    padding:6px 10px; border-radius:6px; border:1px solid rgba(255,255,255,0.08);">
            <span style="flex:1; color:white; font-size:0.9rem;">${item.name}</span>
            <span style="color:rgba(255,255,255,0.35); font-size:0.78rem;">max ${item.available}</span>
            <input type="number" min="1" max="${item.available}" value="${item.quantity}"
                   onchange="updatePickedQty(${id}, this.value)"
                   style="width:60px; padding:3px 6px; background:rgba(255,255,255,0.05);
                          color:white; border:1px solid rgba(255,255,255,0.2); border-radius:4px; text-align:center;">
            <button type="button" onclick="removePickedItem(${id})"
                    style="background:transparent; color:rgba(255,100,100,0.8);
                           border:none; font-size:1.1rem; cursor:pointer; line-height:1;">✕</button>
        </div>
    `).join('');
}

function syncItemsJSON() {
    const items = Object.entries(pickedItems).map(([id, item]) => ({
        itemID: parseInt(id),
        quantity: item.quantity
    }));
    const field = document.getElementById("itemsJSON");
    if (field) field.value = JSON.stringify(items);
}

function resetItemPicker() {
    pickedItems = {};
    const search = document.getElementById("itemSearch");
    const dropdown = document.getElementById("itemDropdown");
    if (search) search.value = "";
    if (dropdown) dropdown.style.display = "none";
    renderPickedItems();
    syncItemsJSON();
}

// close dropdown when clicking outside
document.addEventListener("click", function (e) {
    const dropdown = document.getElementById("itemDropdown");
    const search = document.getElementById("itemSearch");
    if (dropdown && search && !search.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = "none";
    }
});

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
        
        let A = a.cells[col].dataset.sort ?? a.cells[col].innerText.trim();
        let B = b.cells[col].dataset.sort ?? b.cells[col].innerText.trim();

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
    document.getElementById("itemForm").reset();
    document.getElementById("modal").style.display = "flex";
}

function openUpdateItemModal(id, name, description, quantity, photo, deptID) {
    document.getElementById("modalTitle").innerText = "Update Item";
    document.getElementById("modalSubmitBtn").innerText = "Update";
    document.getElementById("itemForm").action = "/inventory/" + id;
    document.getElementById("itemID").value = id;
    document.getElementById("itemName").value = name;
    document.getElementById("itemDescription").value = description;
    document.getElementById("itemquantity").value = quantity;
    document.getElementById("itemphoto").value = photo;

    //set dropdown
    const deptSelect = document.getElementById("departmentID");
    if (deptSelect && deptID) {
        deptSelect.value = deptID;
    }

    document.getElementById("modal").style.display = "flex";
}

function closeItemModal() {
    document.getElementById("modal").style.display = "none";
}

// load inventory items into memory if on the requests page
if (document.getElementById("requestsTable")) {
    loadInventoryItems();
}


function updateDateInputColours() {
    document.querySelectorAll('input[type="datetime-local"]').forEach(input => {
        if (input.value) {
            input.classList.add("has-value");
        } else {
            input.classList.remove("has-value");
        }
    });
}

/* ── DASHBOARD PAGE ────────────────────────────────────────── */

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const header = section.previousElementSibling;
    const toggle = header.querySelector('.section-toggle');

    if (section.style.display === 'none') {
        section.style.display = 'block';
        header.classList.remove('collapsed');
        toggle.style.transform = 'rotate(0deg)';
    } else {
        section.style.display = 'none';
        header.classList.add('collapsed');
        toggle.style.transform = 'rotate(-90deg)';
    }
}

document.addEventListener("input", function (e) {
    if (e.target.matches('input[type="datetime-local"]')) {
        updateDateInputColours();
    }
});

document.addEventListener("DOMContentLoaded", updateDateInputColours);


function getCurrentDateTimeLocal() {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
}

const requestForm = document.getElementById("requestForm");

if (requestForm) {
    requestForm.addEventListener("submit", function () {
        const eventDateStartField = document.getElementById("eventDateStart");

        if (eventDateStartField && !eventDateStartField.value) {
            eventDateStartField.value = getCurrentDateTimeLocal();
        }

        updateDateInputColours();
    });
}

//Department Modal

function openAddDepartmentModal() {
    document.getElementById("departmentForm").reset();
    document.getElementById("departmentModal").style.display = "flex";
}

function closeDepartmentModal() {
    document.getElementById("departmentModal").style.display = "none";
}

function openUpdateDepartmentModal(id, name) {
    document.getElementById("updateDepartmentID").value = id;
    document.getElementById("updateDepartmentName").value = name;

    document.getElementById("updateDepartmentForm").action = "/appsettings/departments/update/" + id;

    document.getElementById("updateDepartmentModal").style.display = "flex";
}

function closeUpdateDepartmentModal() {
    document.getElementById("updateDepartmentModal").style.display = "none";
}

/* ── APP SETTINGS SORTING ───────────────────────────────── */

// generic sorter used for both tables
function sortSimpleTable(tableId, col) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    // store direction per column
    if (!table.sortState) table.sortState = {};
    table.sortState[col] = !table.sortState[col];
    const asc = table.sortState[col];

    rows.sort((a, b) => {
        
        let A = a.cells[col].dataset.sort ?? a.cells[col].innerText.trim();
        let B = b.cells[col].dataset.sort ?? b.cells[col].innerText.trim();


        const numA = parseFloat(A);
        const numB = parseFloat(B);

        if (!isNaN(numA) && !isNaN(numB)) {
            return asc ? numA - numB : numB - numA;
        }

        return asc ? A.localeCompare(B) : B.localeCompare(A);
    });

    rows.forEach(r => tbody.appendChild(r));

    // reset arrows
    const arrows = table.querySelectorAll("th span.arrow");
    arrows.forEach(a => a.textContent = "↕");

    // set active arrow
    const header = table.querySelectorAll("th")[col];
    const arrow = header?.querySelector(".arrow");
    if (arrow) {
        arrow.textContent = asc ? "▲" : "▼";
    }
}


// wrappers (match your onclick calls)

function sortUsersTable(col) {
    sortSimpleTable("usersTable", col);
}

function sortDepartmentsTable(col) {
    sortSimpleTable("departmentsTable", col);
}

function bindFileInput() {
    const fileInput = document.getElementById("itemphoto_file");
    const urlInput = document.getElementById("itemphoto");
    const fileNameDisplay = document.getElementById("fileName");

    if (!fileInput || !urlInput) return;

    fileInput.addEventListener("change", function () {
        const file = this.files[0];

        if (!file) {
            urlInput.value = "";
            if (fileNameDisplay) fileNameDisplay.textContent = "";
            return;
        }

        // create preview url
        const tempUrl = URL.createObjectURL(file);

        // update url field
        urlInput.value = tempUrl;

        // add filename display here
        if (fileNameDisplay) {
            fileNameDisplay.textContent = file.name;
        }
    });
}

// run once on page load
document.addEventListener("DOMContentLoaded", bindFileInput);

