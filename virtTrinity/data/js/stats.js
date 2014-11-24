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

    var updateInterval = 10000;
    var color_map = {
        "success": "#99ff00",
        "failure": "#cc0000",
        "timeout": "#ffcc00",
    };

    var updateChart = function() {
        $.getJSON("/json/stats", function(stats) {
            var data = [];
            ['success', 'failure', 'timeout'].forEach(function(exit_status){
                status_data = {
                    "type": "stackedBar",
                    "showInLegend": true,
                    "name": exit_status,
                    "axisYType": "secondary",
                    "color": color_map[exit_status],
                    "dataPoints": [],
                };
                stats.forEach(function(stat) {
                    status_data.dataPoints.push({
                        "label": stat[0],
                        "y": stat[1][exit_status],
                    });
                });
                status_data.click = function(e) {
                    window.location.href = "/cmdlist/" + e.dataPoint.label;
                };
                data.push(status_data);
            });
            var ncols = data[0].dataPoints.length;
            $("#chartContainer").height(150 + ncols * 25);
            chart.options.data = data;
            chart.render();
        });
    };
    updateChart();
    setInterval(function(){updateChart()}, updateInterval);
});
