$(document).ready(function() {
    var chart = new CanvasJS.Chart("chartContainer", {
        title:{
            fontSize: 40,
            text:"virsh command result statistics"
        },
        axisX:{
            interval: 1,
            labelFontSize: 14,
            lineThickness: 0
        },
        axisY2:{
            labelFontSize: 14,
            valueFormatString: "0",
            lineThickness: 0                
        },
        toolTip: {
            shared: true
        },
        legend:{
            fontSize: 15,
            verticalAlign: "top",
            horizontalAlign: "center"
        }
    });

    var updateInterval = 1000;

    var updateChart = function() {
        $.getJSON("/json/stats", function(stats) {
            stats.forEach(function(stat) {
                stat.click = function(e) {
                    window.location.href = "/cmdlist/" + e.dataPoint.label;
                };
            })
            chart.options.data = stats;
            chart.render();
        });
    };
    updateChart();
    setInterval(function(){updateChart()}, updateInterval);
});
