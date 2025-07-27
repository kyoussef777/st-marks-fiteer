document.addEventListener('DOMContentLoaded', () => {
  const ctx = document.getElementById('summaryChart').getContext('2d');
  
  // Get dynamic drink data
  const drinkCounts = window.chartData.drinkCounts || {};
  const labels = Object.keys(drinkCounts);
  const data = Object.values(drinkCounts);
  
  // Generate colors for each drink type
  const colors = [
    '#8e44ad', '#3498db', '#e74c3c', '#f39c12', '#2ecc71', 
    '#9b59b6', '#1abc9c', '#34495e', '#e67e22', '#95a5a6'
  ];
  
  const summaryChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Drinks Made',
        data: data,
        backgroundColor: colors.slice(0, labels.length),
        borderRadius: 5
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: 'Drinks Breakdown',
          font: { size: 16 }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0 }
        }
      }
    }
  });
});
