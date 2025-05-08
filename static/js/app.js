const ctx = document.getElementById('goldChart').getContext('2d');
let chart;

async function fetchChartData(range = 'day') {
    try {
        const res = await fetch(`/api/chart_data?range=${range}`);
        if (!res.ok) throw new Error('Lỗi tải dữ liệu biểu đồ');
        
        const data = await res.json();
        if (!data.labels || !data.datasets) {
            throw new Error('Dữ liệu không hợp lệ');
        }

        // Xóa biểu đồ cũ và tạo biểu đồ mới
        if (chart) chart.destroy();
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: data.datasets
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' },
                    title: {
                        display: true,
                        text: `Giá vàng theo ${range}`
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: { display: true, text: 'Giá (VNĐ)' }
                    }
                }
            }
        });
    } catch (error) {
        console.error(error);
        alert('Không thể tải dữ liệu biểu đồ. Vui lòng thử lại sau.');
    }
}

// Thêm chức năng hiển thị bảng so sánh
async function fetchPriceComparison(range = 'day') {
    try {
        const res = await fetch(`/api/chart_data?range=${range}`);
        if (!res.ok) throw new Error('Lỗi tải dữ liệu bảng giá');

        const data = await res.json();
        if (!data.labels || !data.datasets) {
            throw new Error('Dữ liệu không hợp lệ');
        }

        const tableBody = document.getElementById('priceComparisonTable');
        tableBody.innerHTML = ''; // Clear table before adding new data

        data.labels.forEach((label, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${label}</td>
                <td>${data.datasets[0].data[index] || '-'}</td>
                <td>${data.datasets[1].data[index] || '-'}</td>
                <td>${data.datasets[2].data[index] || '-'}</td>
                <td>${data.datasets[3].data[index] || '-'}</td>
                <td>${data.datasets[4].data[index] || '-'}</td>
                <td>${data.datasets[5].data[index] || '-'}</td>
            `;
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error(error);
        const tableBody = document.getElementById('priceComparisonTable');
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center">Không thể tải dữ liệu bảng giá. Vui lòng thử lại sau.</td></tr>`;
    }
}

document.getElementById('range').addEventListener('change', (e) => {
    const range = e.target.value;
    fetchChartData(range);
    fetchPriceComparison(range);
});

// Tải dữ liệu lần đầu
fetchChartData();
fetchPriceComparison(); // Hiển thị bảng so sánh khi load trang
