import React, { useState, useCallback } from "react";
import {
    VictoryChart,
    // VictoryContainer,
    VictoryLabel,
    VictoryAxis,
    VictoryBar,
    // VictoryPie,
    VictoryStack,
    VictoryTheme,
    VictoryTooltip,
    // VictoryZoomContainer
} from 'victory';

//----------------------------------------------------------------------------//

var col_no = 30

//----------------------------------------------------------------------------//

export function AggregatedPlots({ summaryResults, filterUnknowns }) {
    return (
        <>
        {summaryResults ? (
            summaryResults.map((r) => (
                <>
                {r["concepts"].length > 0 && (
                    <AggregatedStackedPlot agg={r} filterUnknowns={filterUnknowns} />
                )
                }
                </>
                )
            )
        ) : (
            ""
        )}
        </>
    )
}

//----------------------------------------------------------------------------//

function AggregatedStackedPlot({ agg, filterUnknowns }) {

    var keyedFirst = {}
    var secondKeys = {}
    var agg_l = agg["label"]

    agg["distribution"].forEach(function (v) {
        console.log(Object.keys(v))
        console.log(v["conceptValues"])
        let cvs = v["conceptValues"];
        let c = v["count"]
        if (cvs.length == 0) {
            cvs = [{"id": "undefined", "label": "undefined"}];
        }
        let k1 = cvs[0]["id"];
        let l1 = cvs[0]["label"];
        var k2 = "undefined";
        let l2 = "undefined";
        var lab = l1
        if (cvs.length > 1) {
            k2 = cvs[1]["id"];
            l2 = k2
            if (cvs[1]["label"]) {
                l2 = cvs[1]["label"];
            }
            lab = `${l1} & ${l2}`
        }
        if (! (k1 in keyedFirst) ) {
            keyedFirst[k1] = {"sum": 0};
        }
        if (! secondKeys[k2]) {
            secondKeys[k2] = l2;
        }
        keyedFirst[k1][k2] = {"count": c, "label": lab};
        keyedFirst[k1]["sum"] += c;
    });

    if (filterUnknowns == true) {
        var lb = keyedFirst.length
        delete keyedFirst["unknown"]
        var la = keyedFirst.length
        if (lb != la) {
            agg_l += " (unknowns removed)"
        }
     }

    // Create items array
    var sortedEntries = Object.keys(keyedFirst).map(function(key) {
      return [key, keyedFirst[key]];
    });

    // Sort the array based on the second element
    sortedEntries = agg["sorted"] ? sortedEntries : sortedEntries.sort((a, b) => a[1].sum < b[1].sum ? 1 : -1)

    var dist = [];
    var other_count = 0
    var others = {
        "other": {"sum": 0}
    }
    Object.keys(secondKeys).forEach(function (s) {
        others["other"][s] = { "count": 0, "label": secondKeys[s] }
    })

    var i = 0
    var max_y = 0
    for (const [first, seconds] of sortedEntries) {
        i += 1
        if (i <= col_no) {
            dist.push([first, seconds])
            if (seconds["sum"] > max_y) {
                max_y = seconds["sum"]
            }
        } else {
            other_count += seconds["sum"]
            for (const s of Object.keys(secondKeys)) {
                if (seconds[s]) {
                    others["other"][s]["count"] += seconds[s]["count"];
                    others["other"]["sum"] += seconds[s]["count"];
                    others["other"][s]["label"] = `other & ${secondKeys[s]}`;
                }
            }
        }
    }

    if (other_count > 0) {
        dist.push(["other", others["other"]])
        console.log("Adding other...")
    }

    if (other_count > max_y * 1.25) {
        max_y = other_count * 0.9
    }

    var barData = [];

    Object.keys(secondKeys).sort().forEach(function (s) {
        var thisBar = [];
        for (const [first, seconds] of dist) {
            var barField = { "collabel": first, "count": 0, "label": "" };
            if (seconds[s]) {
                barField["count"] = seconds[s]["count"];
                barField["label"] = `${seconds[s]["label"]}: ${seconds[s]["count"]}`;
                if (agg["concepts"].length > 1) {
                    barField["label"] += ` of ${seconds["sum"]}`;
                }
            }
            thisBar.push(barField)
        }
        barData.push(thisBar);
    })

    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    var outer_w = boundingRect.width

    return (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
{/*            {dist.length <= 5 ? (
                <SimplePieChart
                    bar_data={barData} col_no={dist.length} outer_w={outer_w} title={agg_l}
                />
            ) : (
*/}                <StackedBarChart
                    bar_data={barData} col_no={dist.length} outer_w={outer_w} max_y={max_y} title={agg_l}
                />
            {/*)}*/}
        </div>
    );

}

//----------------------------------------------------------------------------//

// function SimplePieChart({ bar_data, outer_w}) { //, title

//     return(

//                 <VictoryPie
//                     theme={VictoryTheme.material}
//                     radius={outer_w * 0.05}
//                     height={outer_w * 0.2}
//                     width={outer_w * 0.2}
//                     style={{ labels: { fontSize: 6} }}
//                     // width={10}
//                     // innerRadius={30}
//                     // outerRadius={40}
//                     data={bar_data[0]}
//                     x="collabel"         
//                     y="count"
//                 />
//     )
// }


//----------------------------------------------------------------------------//

function StackedBarChart({ bar_data, col_no, outer_w, max_y, title}) {

    const padd_l = 70
    const padd_r = 30
    const padd_t = 30
    const padd_b = 120
    const plot_h = 250

    // const padd = outer_w / col_no

    return(
        <VictoryChart
            domain={{ x: [0.5, col_no + 0.5], y: [0, max_y * 1.1] }}
            height={plot_h}
            width={outer_w}
            theme={VictoryTheme.material}
            padding={{left: padd_l, top: padd_t, right: padd_r, bottom: padd_b}}
          >
            <VictoryLabel         
                text={title}         
                textAnchor="middle"
                x={outer_w * 0.5}        
                y={padd_t - 15}
            />
            <VictoryStack
                colorScale={"qualitative"}
            >
                {bar_data.map((data, i) => (
                    <VictoryBar
                        key={i}
                        data={data}
                        x="collabel"         
                        y="count"
                        labelComponent={<VictoryTooltip  />}
                    />
                ))}
            </VictoryStack>
            <VictoryAxis
                crossAxis 
                style={{
                  tickLabels: { angle: -60, textAnchor: "end" },
                }}
            />
            <VictoryAxis
                dependentAxis 
                style={{
                  axis: {
                    stroke: "transparent",
                  },
                  tickLabels: {
                    fontSize: 8,
                  },
                  grid: {
                    stroke: "#d9d9d9",
                    size: 5,
                  },
                }}
            />
        </VictoryChart>
    )
}
