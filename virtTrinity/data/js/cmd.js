$(document).ready(function() {
    var arr = window.location.pathname.split("/");
    var show_type = arr[1];
    var cmd_name = arr[2];

    var updateCmdList = function(cmd_name) {
        $.getJSON("/json/cmd-" + cmd_name, function(json_results) {
            var keys = {};
            json_results.forEach(function(result) {
                if (!(result.key in keys))
                    keys[result.key] = [];
                keys[result.key].push(result);
            });

            $.map(keys, function(results, key) {
                var li = $("<li/>", {
                    "class": "result " + results[0].exit_status,
                });

                var output_div = $("<div/>", {
                    "class": "output",
                })
                $("<pre/>", {
                    "class": "stdout",
                    text: results[0].sub_stdout
                }).appendTo(output_div);
                $("<pre/>", {
                    "class": "stderr",
                    text: results[0].sub_stderr
                }).appendTo(output_div);

                var cmdline_div = $("<div/>", {
                    "class": "cmdlines"
                });

                results.forEach(function(result) {
                    $("<div/>", {
                        "class": "cmdline",
                        text: result.cmdline
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

    var updateCmdGraph = function(cmd_name) {
        var similarity = function(str1, str2) {
            var distArray = levenshteinenator(str1, str2);
            var dist = distArray[ distArray.length - 1 ][ distArray[ distArray.length - 1 ].length - 1 ] * 1.0;
            return 1.0 - dist / (Math.max(str1.length, str2.length));
        };


        $.getJSON("/json/cmd-" + cmd_name, function(json_results) {
            var graph = {
                "nodes": [{
                    "name": "root",
                    "group": "root",
                    "father": null,
                    "idx": 0,
                    "size": 5,
                }],
                "links": [],
            };

            var keys = [];
            json_results.forEach(function(result) {
                if ($.inArray(result.key, keys) === -1)
                    keys.push(result.key);
            });

            var trimmed_keys = [];
            keys.forEach(function(key) {
                trimmed_keys.push(key.replace(/\$\{.*?\}/g, ""));
            });

            for(var i=0; i<trimmed_keys.length; i++) {
                var key = trimmed_keys[i];
                var found = false;
                var match = null;
                graph.nodes.forEach(function(node) {
                    if (node.name === "root" || node.name === "node") {
                        return true;
                    }
                    var sim = similarity(node.name, key);
                    if (sim > 0.9) {
                        match = node;
                        found = true;
                        return false;
                    }
                });
                if (found) {
                    if (match.father === 0) {
                        graph.nodes.push({
                            "name": "node",
                            "group": "node",
                            "father": 0,
                            "idx": graph.nodes.length,
                            "size": 5,
                        });
                        match.father = graph.nodes.length - 1;
                    }
                    graph.nodes.push({
                        "name": key,
                        "group": "result",
                        "father": match.father,
                        "idx": graph.nodes.length,
                        "size": 5,
                    });
                }
                else {
                    graph.nodes.push({
                        "name": key,
                        "group": "result",
                        "father": 0,
                        "idx": graph.nodes.length,
                        "size": 5,
                    });
                }
            }

            json_results.forEach(function(result) {
                father_node = null;
                max_sim = 0;
                graph.nodes.forEach(function(node) {
                    if (node.group === "result") {
                        sim = similarity(node.name, result.key); /* Change this */
                        if (sim > max_sim) {
                            max_sim = sim;
                            father_node = node;
                        }
                    }
                });
                /*
                graph.nodes.push({
                    "name": result.cmdline,
                    "group": "cmdline",
                    "father": father_node.idx,
                    "idx": graph.nodes.length,
                });*/
                father_node.size += 1;
            });

            graph.nodes.forEach(function(node) {
                if (node.father !== null) {
                    graph.links.push({
                        "source": node.idx,
                        "target": node.father,
                    });
                }
            });
            /*

            for(var i=0; i<json_results.length; i++) {
                for(var j=0; j<i; j++) {
                    value = similarity(
                        json_results[i].stderr.join("\n"),
                        json_results[j].stderr.join("\n")
                    );
                    if (value < 0.01) {
                        graph.links.push({
                            "source": i,
                            "target": j,
                            "value": value,
                        });
                    }
                }
            }*/

            var width = 960,
                height = 800;

            var color = d3.scale.category20();

            var force = d3.layout.force()
                .charge(-120)
                .linkDistance(100)
                .size([width, height]);

            var svg = d3.select("#sb-site").append("svg")
                .attr("width", width)
                .attr("height", height);

            force
                .nodes(graph.nodes)
                .links(graph.links)
                .start();

            var link = svg.selectAll(".link")
                .data(graph.links)
                .enter().append("line")
                .attr("class", "link")
                .style("stroke-width", function(d) { return Math.sqrt(d.value); });

            var node = svg.selectAll(".node")
                .data(graph.nodes)
                .enter().append("circle")
                .attr("class", "node")
                .attr("r", function(d) { return Math.log(d.size) * 10; })
                .style("fill", function(d) { return color(d.group); })
                .call(force.drag);

            node.append("title")
                .text(function(d) { return d.name; });

            link.append("title")
                .text(function(d) { return d.value; });

            force.on("tick", function() {
                link.attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node.attr("cx", function(d) { return d.x; })
                    .attr("cy", function(d) { return d.y; });
            });
        });
    };

    if (show_type == "cmdlist") {
        updateCmdList(cmd_name);
    }
    else if (show_type == "cmdgraph") {
        updateCmdGraph(cmd_name);
    }

});
