$(document).ready(function() {
    var end_idx = 0;
    var page_count = 50;

    var updateLog = function(idx, count) {
        $.getJSON("json/log-" + idx + "-" + count, function(results) {
            results.forEach(function(result) {
                var li = $("<div/>", {
                    "class": "result " + result.exit_status,
                });

                $("<div/>", {
                    "class": "cmdline",
                    "text": result.cmdline
                }).appendTo(li);

                var stdout_div = $("<div/>", {
                    "class": "stdout",
                })
                $("<pre/>", {
                    text: result.stdout
                }).appendTo(stdout_div);
                stdout_div.appendTo(li);

                var stderr_div = $("<div/>", {
                    "class": "stderr",
                })
                $("<pre/>", {
                    text: result.stderr
                }).appendTo(stderr_div);
                stderr_div.appendTo(li);

                li.appendTo("#results");
            });

            $(".result").unbind("click");
            $(".result").click(function() {
                $(this).find(".stdout").toggle("fast");
                $(this).find(".stderr").toggle("fast");
            });
        });

    }

    $(window).scroll(function() {
        if($(window).scrollTop() == $(document).height() - $(window).height()) {
            updateLog(end_idx, page_count);
            end_idx += page_count;
        }
    });

    updateLog(end_idx, page_count);
});
