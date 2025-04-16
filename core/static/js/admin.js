document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('ventasChart').getContext('2d');
  
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie'],
        datasets: [{
          label: 'Ventas diarias',
          data: [1200, 1900, 3000, 2500, 4000],
          backgroundColor: 'rgba(54, 162, 235, 0.6)'
        }]
      },
      options: {
        plugins: {
          title: {
            display: true,
            text: 'Ventas Semanales'
          }
        }
      }
    });
  });