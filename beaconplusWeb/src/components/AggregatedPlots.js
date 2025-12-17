import React, { useState, useCallback } from "react";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })
// import {PlotParams} from 'react-plotly.js';
//----------------------------------------------------------------------------//

var col_no = 30

//----------------------------------------------------------------------------//

export function AggregatedPlots({ summaryResults, filterUnknowns }) {
    return (
        <>
        {summaryResults ? 
            summaryResults.map((r) => (
                <>
                {r["concepts"].length > 0 && (
                    <AggregatedStackedPlot agg={r} filterUnknowns={filterUnknowns} />
                )
                }
                </>
            )
        ) : (
            ""
        )}
        </>
    )
}

//----------------------------------------------------------------------------//

function AggregatedStackedPlot({ agg, filterUnknowns, filterOthers }) {

    var keyedFirst = {}
    var secondKeys = {}
    var agg_l = agg["label"]

    filterOthers = true

    agg["distribution"].forEach(function (v) {
        // console.log(Object.keys(v))
        // console.log(v["conceptValues"])
        let cvs = v["conceptValues"];
        let c = v["count"]
        if (cvs.length == 0) {
            cvs = [{"id": "undefined", "label": "undefined"}];
        }
        let k1 = cvs[0]["id"];
        let l1 = cvs[0]["label"] ? cvs[0]["label"] : k1;
        var k2 = "undefined";
        let l2 = "undefined";
        if (cvs.length > 1) {
            k2 = cvs[1]["id"];
            l2 = k2
            if (cvs[1]["label"]) {
                l2 = cvs[1]["label"];
            }
        }
        if (! (k1 in keyedFirst) ) {
            keyedFirst[k1] = {"sum": 0, "label": l1};
        }
        if (! secondKeys[k2]) {
            secondKeys[k2] = l2;
        }
        keyedFirst[k1][k2] = {"key": k2, "count": c, "label": l2};
        keyedFirst[k1]["sum"] += c;
    });

    var removed_count = 0

    // Filter unknowns and undefineds prototyping WIP
    if (filterUnknowns == true) {
        if (Object.keys(keyedFirst).includes('undefined')) {
            removed_count += keyedFirst["undefined"]["sum"]
            delete keyedFirst["undefined"]
        }
    }

    if (filterUnknowns == true) {
        if (Object.keys(keyedFirst).includes('unknown')) {
            removed_count += keyedFirst["unknown"]["sum"]
            delete keyedFirst["unknown"]
        }
    }

    if (filterOthers == true) {
        if (Object.keys(keyedFirst).includes('other')) {
            removed_count += keyedFirst["other"]["sum"]
            delete keyedFirst["other"]
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
        "other": {sum: 0, label: "other"}
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
                }
            }
        }
    }

    if (other_count > 0) {
        if (filterOthers == true) {
            removed_count += other_count
            other_count = 0
        } else {
            dist.push(["other", others["other"]])
            console.log("Adding other...")
        }
    }

    if (removed_count > 0) {
        agg_l += ` (${removed_count} missing/others removed)`
    }

    if (other_count > max_y * 1.25) {
        max_y = other_count * 0.9
    }


    var tracesData = [];
    Object.keys(secondKeys).sort().forEach(function (s) {
        var thisTrace = {type: "bar", name: secondKeys[s], key: s, x: [], y: [], hovertext: []};
        for (const [first, seconds] of dist) {
            if (seconds[s]) {
                thisTrace.y.push(seconds[s]["count"]);
                thisTrace.x.push(first);
                if (dist.length > 1) {
                    let lab = `${seconds[s]["label"]}: ${seconds[s]["count"]}`;
                    lab += ` of ${seconds["sum"]}`;
                    thisTrace.hovertext.push(lab);
                }
            }
        }
        tracesData.push(thisTrace);
    })


    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    var outer_w = boundingRect.width

    return (
        <>
            {dist.length > 0 ? (
                <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
                   <>
                   {/*The following has to be defined - avoiding here the incomplete pie definitions */}
                   {dist.length <= 8 && tracesData.length == 1 ? (
                        <SimplePlotlyPie
                            tracesData={tracesData} outer_w={outer_w} title={agg_l}
                        />
                    ) : (
                        <StackedPlotlyBar
                            tracesData={tracesData} outer_w={outer_w} title={agg_l}
                        />
                    )}
                   </>
                </div>
            ) : (
                <></>
            )
            }
        </>
    );

}

//----------------------------------------------------------------------------//
//----------------------------------------------------------------------------//
//----------------------------------------------------------------------------//


function SimplePlotlyPie({ tracesData, outer_w, title}) { //, title
    let pieData = {
        type: "pie",
        hole: .4,
        values: tracesData[0]["y"],
        labels: tracesData[0]["x"],
    }
    return (
      <Plot
        data={[pieData]}
        layout={ {width: outer_w, height: 400, title: {text: title}} }
      />
    );
}

//----------------------------------------------------------------------------//

function StackedPlotlyBar({ tracesData, outer_w, title}) { //, title
    return (
      <Plot
        data={tracesData}
        layout={ {barmode: 'stack', width: outer_w, height: 240, title: {text: title}} }
      />
    );
}

