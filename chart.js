fetch("/api/data")
  .then(response => response.json())
  .then(data => {
    const labels = data.map(item => item.created_at);
    const scores = data.map(item => item.mood_score);

    new Chart(document.getElementById("moodChart"), {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Mood Score",
          data: scores,
          borderColor: "blue",
          borderWidth: 2,
          fill: false,
          tension: 0.2
        }]
      }
    });
  });
