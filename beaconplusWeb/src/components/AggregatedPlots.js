import React, { useState, useCallback } from "react";
import {
    VictoryChart,
    VictoryLabel,
    VictoryAxis,
    VictoryBar,
    VictoryStack,
    VictoryTheme,
    VictoryTooltip,
    // VictoryZoomContainer
} from 'victory';

//----------------------------------------------------------------------------//


var col_no = 25

// const barStyle = {
//   data: {
//     fill: "#c43a31",
//     fillOpacity: 0.4,
//     stroke: "#c43a31",
//     strokeWidth: 2,
//   },
//   labels: {
//     fontSize: 12,
//     fill: "#c43a31",
//   },
// }


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
        let cvs = v["conceptValues"];
        let c = v["count"]
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
    for (const [first, seconds] of sortedEntries) {
        i += 1
        if (i <= col_no) {
            dist.push([first, seconds])
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

    var barData = [];

    Object.keys(secondKeys).sort().forEach(function (s) {
        var thisBar = [];
        for (const [first, seconds] of dist) {
            var barField = { "collabel": first, "count": 0, "label": "" };
            if (seconds[s]) {
                barField["count"] = seconds[s]["count"];
                barField["label"] = `${seconds[s]["label"]} (${seconds[s]["count"]} of ${seconds["sum"]})`;
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
            <StackedBarChart
                bar_data={barData} col_no={dist.length} outer_w={outer_w} title={agg_l}
            />
        </div>
    );

}

//----------------------------------------------------------------------------//

function StackedBarChart({ bar_data, col_no, outer_w, title}) {

    const padd_l = 70
    const padd_r = 30
    const padd_t = 30
    const padd_b = 120
    const plot_h = 250

    // const padd = outer_w / col_no

    return(
        <VictoryChart
            domain={{ x: [0.5, col_no + 0.5] }}
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
                        labelComponent={<VictoryTooltip />}
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
                style={{}}
            />
        </VictoryChart>
    )
}
//----------------------------------------------------------------------------//

// function AggregatedPlot({ agg, filterUnknowns }) {
//     var dist_all = agg["distribution"].map(item => ({
//       id: item.conceptValues[0].id,
//       label: `${item.conceptValues[0].label} (${item.conceptValues[0].id}, ${item.count})`,
//       count: item.count
//     }))

//     var agg_l = agg["label"]

//     dist_all = agg["sorted"] ? dist_all : dist_all.sort((a, b) => a.count < b.count ? 1 : -1)

//     var dist = []
//     var other = {
//         id: "other",
//         label: "other...",
//         count: 0
//     }

//     var i = 0
//     dist_all.forEach(function (item) {
//         i += 1
//         if (i < col_no) {
//             dist.push(item)
//         } else {
//             other["count"] += item["count"]
//         }
//     });

//     if (other["count"] > 0) {
//         other["label"] += " (" + other.count +")"
//         dist.push(other)
//     }

//     if (filterUnknowns == true) {
//         var lb = dist.length
//         dist = dist.filter(item => item.id !== "unknown")
//         var la = dist.length
//         if (lb != la) {
//             agg_l += " (unknowns removed)"
//         }
//      }

//     const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
//     const containerRef = useCallback((node) => {
//         if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
//     }, []);

//     var c = dist.length
//     if (c < 1) {
//         c = 0
//     }

//     // TODO: 
//     var outer_w = boundingRect.width

//     const padd = outer_w / c

//     return (
//         <>
//         {dist && dist.length > 1 && (
//         <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
//             <VictoryChart
//                 domainPadding={{ x: padd }}
//                 height={plot_h}
//                 width={outer_w}
//                 theme={VictoryTheme.material}
//                 padding={{left: padd_l, top: padd_t, right: padd_r, bottom: padd_b}}
//               >
//                 <VictoryLabel         
//                     text={agg_l}         
//                     textAnchor="middle"
//                     x={outer_w * 0.5}        
//                     y={padd_t - 15}
//                 />
//                 <VictoryBar
//                     data={dist}
//                     x="id"         
//                     y="count"
//                     theme={VictoryTheme.clean}
//                     labelComponent={<VictoryTooltip />}
//                     labels={({ label }) => label}
//                     style={barStyle}
//                 />
//                 <VictoryAxis
//                     crossAxis 
//                     style={{
//                       tickLabels: { angle: -60, textAnchor: "end" },
//                     }}
//                 />
//                 <VictoryAxis
//                     dependentAxis 
//                     style={{}}
//                 />
//             </VictoryChart>
//         </div>

//         )}
//         </>
//     );
// }
