document.addEventListener('DOMContentLoaded', function () {
	// draw monthly chart
	const monthlyCtx = document.getElementById('monthlyChart');
	const yearlyCtx = document.getElementById('yearlyChart');

	function drawMonthly(data) {
		if (!monthlyCtx) return;
		const labels = data.labels;
		const pct = data.percentages;
		new Chart(monthlyCtx, {
			type: 'bar',
			data: {
				labels: labels,
				datasets: [{
					label: 'Completed habits (%)',
					data: pct,
					backgroundColor: 'rgba(37,99,235,0.8)'
				}]
			},
			options: {responsive:true, maintainAspectRatio: false, scales:{y:{beginAtZero:true, max:100}}}
		});
	}

	function drawYearly(data) {
		if (!yearlyCtx) return;
		const labels = data.months;
		const pct = data.percentages;
		new Chart(yearlyCtx, {
			type: 'line',
			data: {
				labels: labels,
				datasets: [{
					label: 'Monthly completion (%)',
					data: pct,
					borderColor: 'rgba(16,185,129,0.9)',
					backgroundColor: 'rgba(16,185,129,0.2)',
					fill: true,
					tension: 0.2
				}]
			},
			options: {responsive:true, maintainAspectRatio:false, scales:{y:{beginAtZero:true, max:100}}}
		});
	}

	fetch('/api/monthly-progress/').then(r=>r.json()).then(drawMonthly).catch(()=>{});
	fetch('/api/yearly-progress/').then(r=>r.json()).then(drawYearly).catch(()=>{});
});
