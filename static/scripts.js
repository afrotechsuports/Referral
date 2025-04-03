// Toggle invited users details
function toggleDetails(element) {
    const details = element.nextElementSibling;
    details.classList.toggle('show');
}

// Sort table by points
function sortTable(columnIndex) {
    const table = document.getElementById("referralTable");
    let rows, switching = true, i, shouldSwitch, dir = "desc", switchcount = 0;
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            const x = rows[i].getElementsByTagName("TD")[columnIndex];
            const y = rows[i + 1].getElementsByTagName("TD")[columnIndex];
            const xValue = parseInt(x.innerHTML);
            const yValue = parseInt(y.innerHTML);
            if (dir === "asc") {
                if (xValue > yValue) {
                    shouldSwitch = true;
                    break;
                }
            } else if (dir === "desc") {
                if (xValue < yValue) {
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount++;
        } else {
            if (switchcount === 0 && dir === "desc") {
                dir = "asc";
                switching = true;
            }
        }
    }
    const th = table.getElementsByTagName("TH")[columnIndex];
    th.innerHTML = th.innerHTML.replace(" ▲", "").replace(" ▼", "");
    th.innerHTML += dir === "asc" ? " ▲" : " ▼";
}

// Select all checkboxes
function toggleSelectAll() {
    const selectAll = document.getElementById("selectAll");
    const checkboxes = document.getElementsByName("selected_users");
    for (let checkbox of checkboxes) {
        checkbox.checked = selectAll.checked;
    }
}