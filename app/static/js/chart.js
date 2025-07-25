const ctx = document.getElementById('summaryChart').getContext('2d');
const summaryChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Lattes', 'Coffees'],
    datasets: [{
      label: 'Drinks Made',
      data: [window.chartData.totalLattes, window.chartData.totalCoffees],
      backgroundColor: ['#8e44ad', '#3498db'],
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
