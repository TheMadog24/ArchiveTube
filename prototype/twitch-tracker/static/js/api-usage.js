
document.addEventListener("DOMContentLoaded", () => {
    let endpointChart = null;
    let historyChart = null;

    let endpointChartMouseX = 0;
    let endpointChartMouseY = 0;

    const periodSelector = document.getElementById("usage-period");
    const endpointPeriodSelector = document.getElementById("endpoint-usage-period");
    const lineStyleButtons = document.querySelectorAll(".line-style-button");

    let lineStyle = "curved";

    lineStyleButtons.forEach(button => {
        button.addEventListener("click", () => {
            lineStyle = button.dataset.lineStyle;

            lineStyleButtons.forEach(item => {
                item.classList.toggle("active", item === button);
            });

            loadHistoryUsage();
        });
    });

    const endpointCanvas = document.getElementById("usage-endpoint-chart");
    const historyCanvas = document.getElementById("usage-history-chart");

    if (endpointCanvas) {
        endpointCanvas.addEventListener("mousemove", event => {
            const rect = endpointCanvas.getBoundingClientRect();

            endpointChartMouseX = event.clientX - rect.left;
            endpointChartMouseY = event.clientY - rect.top;
        });
    }

    const endpointColors = {
        users: "#3B82F6",
        streams: "#10B981",
        games: "#F59E0B",
        channels: "#8B5CF6",
        videos: "#EC4899",
        eventsub_subscriptions: "#06B6D4",
        other: "#F97316"
    };

    async function loadEndpointUsage() {
        try {
            const period = endpointPeriodSelector
                ? endpointPeriodSelector.value
                : "24h";

            const response = await fetch(
                `/api/usage/endpoints?period=${encodeURIComponent(period)}`
            );

            if (!response.ok) {
                throw new Error("Failed to load endpoint usage.");
            }

            const endpoints = await response.json();

            const legend = document.getElementById("endpoint-usage-legend");

            if (legend) {
                const totalRequests = endpoints.reduce(
                    (sum, item) => sum + item.total_requests,
                    0
                );

                legend.innerHTML = endpoints.map(item => {
                    const percentage = totalRequests > 0
                        ? (item.total_requests / totalRequests * 100).toFixed(1)
                        : "0.0";

                    const color = endpointColors[item.endpoint] || "#94A3B8";

                    return `
                    <div class="endpoint-legend-item">
                        <span class="endpoint-legend-name" style="color: ${color};">
                            ${item.endpoint}
                        </span>

                        <span class="endpoint-legend-value">
                            <span class="endpoint-count" data-target="${item.total_requests}">0</span> requests
                        </span>

                        <span class="endpoint-legend-percentage" style="color: ${color};">
                            <span class="endpoint-percentage" data-target="${percentage}">0.0</span>%
                        </span>
                    </div>
                    `;
                }).join("");

                animateEndpointNumbers();
            }

            if (!endpointCanvas) {
                return;
            }

            if (endpointChart) {
                endpointChart.destroy();
            }

            const totalRequests = endpoints.reduce(
                (sum, item) => sum + item.total_requests,
                0
            );

            const datasets = endpoints.map((item, index) => ({
                label: item.endpoint,
                data: [item.total_requests],
                backgroundColor: endpointColors[item.endpoint] || "#94A3B8",
                borderWidth: 0,

                borderRadius: {
                    topLeft: index === 0 ? 16 : 0,
                    bottomLeft: index === 0 ? 16 : 0,
                    topRight: index === endpoints.length - 1 ? 16 : 0,
                    bottomRight: index === endpoints.length - 1 ? 16 : 0
                },

                borderSkipped: false,
                barThickness: 30,
                maxBarThickness: 30,
                endpointDetails: item
            }));

            endpointChart = new Chart(endpointCanvas, {
                type: "bar",
                data: {
                    labels: ["API Requests"],
                    datasets: datasets
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            stacked: true,
                            display: false,
                            beginAtZero: true,
                            max: totalRequests
                        },
                        y: {
                            stacked: true,
                            display: false
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: false,

                            external: function (context) {
                                const { chart, tooltip } = context;

                                let tooltipEl = document.getElementById("endpoint-chart-tooltip");

                                if (!tooltipEl) {
                                    tooltipEl = document.createElement("div");
                                    tooltipEl.id = "endpoint-chart-tooltip";
                                    tooltipEl.className = "endpoint-chart-tooltip";

                                    document.body.appendChild(tooltipEl);
                                }

                                if (tooltip.opacity === 0) {
                                    tooltipEl.style.opacity = 0;
                                    return;
                                }

                                if (tooltip.body) {
                                    const item = tooltip.dataPoints[0].dataset.endpointDetails;

                                    const percentage = totalRequests > 0
                                        ? (item.total_requests / totalRequests * 100).toFixed(1)
                                        : "0.0";

                                    const averageDuration = item.total_requests > 0
                                        ? (item.total_duration_ms / item.total_requests).toFixed(1)
                                        : 0;

                                    tooltipEl.innerHTML = `
                                    <div class="endpoint-tooltip-title">
                                    API Request Breakdown
                                    </div>
                                    <div>${item.endpoint}: ${item.total_requests} requests (${percentage}%)</div>
                                    <div>Successful: ${item.successful_requests}</div>
                                    <div>Failed: ${item.failed_requests}</div>
                                    <div>Average response: ${averageDuration} ms</div>
                                    <div>Maximum response: ${item.max_duration_ms} ms</div>
                                    `;
                                }

                                const rect = chart.canvas.getBoundingClientRect();

                                const mouseX = rect.left + window.scrollX + endpointChartMouseX;
                                const mouseY = rect.top + window.scrollY + endpointChartMouseY;

                                const tooltipWidth = tooltipEl.offsetWidth;
                                const tooltipHeight = tooltipEl.offsetHeight;

                                const margin = 12;

                                // Keep the tooltip inside the visible page width.
                                let left = mouseX;

                                if (left + tooltipWidth / 2 > window.scrollX + window.innerWidth - margin) {
                                    left = window.scrollX + window.innerWidth - margin - tooltipWidth / 2;
                                }

                                if (left - tooltipWidth / 2 < window.scrollX + margin) {
                                    left = window.scrollX + margin + tooltipWidth / 2;
                                }

                                // Position above the cursor, unless there isn't enough room.
                                let top = mouseY - 12;

                                if (top - tooltipHeight < window.scrollY + margin) {
                                    top = mouseY + tooltipHeight + 12;
                                }

                                tooltipEl.style.opacity = 1;
                                tooltipEl.style.left = `${left}px`;
                                tooltipEl.style.top = `${top}px`;
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error("Error loading endpoint usage:", error);
        }
    }

    function animateEndpointNumbers() {
        const duration = 1200;
        const startTime = performance.now();

        const counts = document.querySelectorAll(".endpoint-count");
        const percentages = document.querySelectorAll(".endpoint-percentage");

        function updateNumbers(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Smoothly ease out near the end.
            const easedProgress = 1 - Math.pow(1 - progress, 4);

            counts.forEach(element => {
                const target = Number(element.dataset.target);
                const current = Math.round(target * easedProgress);

                element.textContent = current.toLocaleString();
            });

            percentages.forEach(element => {
                const target = Number(element.dataset.target);
                const current = target * easedProgress;

                element.textContent = current.toFixed(1);
            });

            if (progress < 1) {
                requestAnimationFrame(updateNumbers);
            }
        }

        requestAnimationFrame(updateNumbers);
    }


    async function loadHistoryUsage() {
        try {
            const period = periodSelector ? periodSelector.value : "24h";

            const [historyResponse, endpointResponse] = await Promise.all([
                fetch(`/api/usage/history?period=${encodeURIComponent(period)}`),
                fetch(`/api/usage/endpoints?period=${encodeURIComponent(period)}`)
            ]);

            if (!historyResponse.ok || !endpointResponse.ok) {
                throw new Error("Failed to load API usage history.");
            }

            const [history, endpoints] = await Promise.all([
                historyResponse.json(),
                endpointResponse.json()
            ]);

            if (!historyCanvas) {
                return;
            }

            const labels = history.map(item => item.period);

            const datasets = endpoints.map(endpoint => ({
                label: endpoint.endpoint,
                data: labels.map(period => {
                    return endpoint.endpoint;
                }),
                borderColor: endpointColors[endpoint.endpoint] || "#94A3B8",
                backgroundColor: "transparent",
                borderWidth: 2,
                tension: lineStyle === "curved" ? 0.25 : 0,
                pointRadius: 2,
                pointHoverRadius: 6,
                spanGaps: true
            }));

            const endpointHistories = await Promise.all(
                endpoints.map(async endpoint => {
                    const response = await fetch(
                        `/api/usage/history?period=${encodeURIComponent(period)}&endpoint=${encodeURIComponent(endpoint.endpoint)}`
                    );

                    if (!response.ok) {
                        throw new Error(`Failed to load ${endpoint.endpoint} history.`);
                    }

                    return {
                        endpoint: endpoint.endpoint,
                        history: await response.json()
                    };
                })
            );

            endpointHistories.forEach(item => {
                const dataset = datasets.find(
                    entry => entry.label === item.endpoint
                );

                const values = new Map(
                    item.history.map(row => [row.period, row.total_requests])
                );

                dataset.data = labels.map(label => values.get(label) ?? null);
            });

            datasets.push({
                label: "Total",
                data: history.map(item => item.total_requests),
                borderColor: "transparent",
                backgroundColor: document.documentElement.getAttribute("data-theme") === "light"
                    ? "rgba(59, 130, 246, 0.18)"
                    : "rgba(229, 231, 235, 0.15)",
                borderWidth: 0,
                fill: "origin",
                tension: lineStyle === "curved" ? 0.25 : 0,
                pointRadius: 0,
                pointHoverRadius: 5
            });

            if (historyChart) {
                historyChart.destroy();
            }

            historyChart = new Chart(historyCanvas, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: "index"
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: "Time (UTC)",
                                color: getComputedStyle(document.documentElement)
                                    .getPropertyValue("--text-secondary").trim()
                            },
                            grid: {
                                color: document.documentElement.getAttribute("data-theme") === "light"
                                    ? "rgba(60, 60, 70, 0.35)"
                                    : "rgba(220, 220, 230, 0.30)",
                                lineWidth: 1.5
                            },
                            ticks: {
                                color: getComputedStyle(document.documentElement)
                                    .getPropertyValue("--text-secondary").trim(),

                                font: {
                                    size: 14
                                }
                            },
                        },
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: "Requests",
                                color: getComputedStyle(document.documentElement)
                                    .getPropertyValue("--text-secondary").trim()
                            },
                            ticks: {
                                precision: 0,
                                color: getComputedStyle(document.documentElement)
                                    .getPropertyValue("--text-secondary").trim()
                            },
                            grid: {
                                color: document.documentElement.getAttribute("data-theme") === "light"
                                    ? "rgba(60, 60, 70, 0.40)"
                                    : "rgba(220, 220, 230, 0.35)",
                                lineWidth: 1.5
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true
                        },
                        tooltip: {
                            callbacks: {
                                label: context =>
                                    `${context.dataset.label}: ${context.parsed.y ?? 0} requests`
                            }
                        },
                        zoom: {
                            pan: {
                                enabled: true,
                                mode: "x"
                            },
                            zoom: {
                                wheel: {
                                    enabled: true
                                },
                                pinch: {
                                    enabled: true
                                },
                                mode: "x"
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error("Error loading API usage history:", error);
        }
    }


    async function loadUsageCharts() {
        await Promise.all([
            loadEndpointUsage(),
            loadHistoryUsage()
        ]);
    }

    if (periodSelector) {
        periodSelector.addEventListener("change", loadUsageCharts);
    }

    if (endpointPeriodSelector) {
        endpointPeriodSelector.addEventListener("change", () => {
            loadEndpointUsage();
        });
    }

    document.addEventListener("themeChanged", () => {
        loadUsageCharts();
    });

    const zoomInButton = document.getElementById("usage-zoom-in");
    const zoomOutButton = document.getElementById("usage-zoom-out");
    const zoomResetButton = document.getElementById("usage-zoom-reset");

    if (zoomInButton) {
        zoomInButton.addEventListener("click", () => {
            historyChart?.zoom(1.2);
        });
    }

    if (zoomOutButton) {
        zoomOutButton.addEventListener("click", () => {
            historyChart?.zoom(0.8);
        });
    }

    if (zoomResetButton) {
        zoomResetButton.addEventListener("click", () => {
            historyChart?.resetZoom();
        });
    }

    loadUsageCharts();
});
