function load_cmd(cmd_name) {
    $.getJSON("/json/keys-" + cmd_name, function(json_results) {
        $("#cmd-container").empty();
        json_results.forEach(function(result) {
            var li = $("<li/>", {
                "class": "result " + result.exit_status,
            });

            var output_div = $("<div/>", {
                "class": "output",
                "text": result.count
            });
            $("<pre/>", {
                "class": "stdout",
                text: result.sub_stdout
            }).appendTo(output_div);
            $("<pre/>", {
                "class": "stderr",
                text: result.sub_stderr
            }).appendTo(output_div);

            var cmdline_div = $("<div/>", {
                "class": "cmdlines"
            });
            cmdline_div.appendTo(output_div);
            output_div.appendTo(li);
            li.click(function() {
                $.getJSON("/json/lines-" + result.key, function(cmdlines) {
                    li.find(".cmdlines").empty();
                    cmdlines.forEach(function(cmdline) {
                        var cmd_div = $("<div/>", {
                            "class": "cmdline",
                            text: cmdline[0]
                        });
                        cmd_div.appendTo(li.find(".cmdlines"));
                    });
                    li.find(".cmdlines").toggle("fast");
                });
            });

            li.appendTo("#cmd-container");
        });
    });
}

$(function() {
    $.getJSON("/json/stats", function(cmds) {
        var data = [];
        cmds.forEach(function(cmd) {
            var name = cmd[0];
            var label = $("<div/>", {
                "class": "label",
                "text": name,
            });

            var total = 0;
            for (var e in cmd[1]) {
                total += cmd[1][e];
            }
            var success_ratio = cmd[1]['success'] / total;

            var color = 'hsl(' +
                        Math.round(120 * success_ratio) +
                        ', 100%, 30%)';

            var grid = $("<div/>", {
                "class": "item",
                "height": 24,
            });

            grid.click(function() {
                load_cmd(name);
            });
            grid.css("background", color);
            grid.css("width", "20%");
            label.appendTo(grid);

            grid.appendTo("#grid-container");
        });

        var wall = new freewall("#grid-container");
        wall.reset({
            animate: true,
            gutterX: 2,
            gutterY: 2,
            cellW: 120,
            cellH: 24,
            delay: 3,
            selector: '.item',
            onResize: function() {
                wall.refresh($(window).width() * 0.4 - 30, $(window).height() - 30);
            }
        });
        wall.fitWidth();
    });
});
