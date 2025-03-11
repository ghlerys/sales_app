function inicializarGraficoVendasMes(vendasPorMes) {
    var ctx = document.getElementById('graficoVendasMes').getContext('2d');
    if (!ctx) {
        console.error("Canvas não encontrado!");
        return;
    }

    console.log("Inicializando gráfico com dados:", vendasPorMes);

    var graficoVendasMes = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
            datasets: [{
                label: 'Vendas Totais',
                data: vendasPorMes,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}