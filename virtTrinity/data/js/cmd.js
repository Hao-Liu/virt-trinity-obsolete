$(document).ready(function() {
    var arr = window.location.pathname.split("/");
    var cmd_name = arr[2];

    var updateCmd = function(cmd_name) {
        $.getJSON("/json/cmd-" + cmd_name, function(results) {
            console.log(results);
            $.map(results, function(result, result_key) {
                var li = $("<li/>", {
                    "class": "result " + result.exit_status,
                });

                var output_div = $("<div/>", {
                    "class": "output",
                })
                $("<pre/>", {
                    "class": "stdout",
                    text: result.stdout
                }).appendTo(output_div);
                $("<pre/>", {
                    "class": "stderr",
                    text: result.stderr
                }).appendTo(output_div);

                var cmdline_div = $("<div/>", {
                    "class": "cmdlines"
                });

                result.cmdlines.forEach(function(cmdline) {
                    $("<div/>", {
                        "class": "cmdline",
                        text: cmdline
                    }).appendTo(cmdline_div);
                });

                cmdline_div.appendTo(output_div);
                output_div.appendTo(li);

                li.appendTo("#cmd_results");
            });

            $(".result").unbind("click");
            $(".result").click(function() {
                $(this).find(".cmdlines").toggle("fast");
            });
        });

    };

    updateCmd(cmd_name);
});
