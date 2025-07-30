function refreshOrders() {
  fetch('/in_progress')
    .then(response => response.text())
    .then(html => {
      const ordersContent = document.querySelector('.orders-content');
      if (ordersContent) {
        ordersContent.innerHTML = html;
      } else {
        // Fallback for legacy design
        const pendingOrders = document.querySelector('.pending-orders');
        if (pendingOrders) {
          pendingOrders.innerHTML = `
            <h3>In Progress Orders</h3>
            ${html}
          `;
        }
      }
    })
    .catch(err => console.error('Error refreshing orders:', err));
}

document.addEventListener('DOMContentLoaded', () => {
  refreshOrders(); // optional: initial load
  setInterval(refreshOrders, 5000); // refresh every 5 seconds
});
