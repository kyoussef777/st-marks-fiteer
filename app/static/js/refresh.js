function refreshOrders() {
  fetch('/in_progress')
    .then(response => response.text())
    .then(html => {
      document.querySelector('.pending-orders').innerHTML = `
        <h3>In Progress Orders</h3>
        ${html}
      `;
    })
    .catch(err => console.error('Error refreshing orders:', err));
}

document.addEventListener('DOMContentLoaded', () => {
  refreshOrders(); // optional: initial load
  setInterval(refreshOrders, 5000); // refresh every 5 seconds
});
