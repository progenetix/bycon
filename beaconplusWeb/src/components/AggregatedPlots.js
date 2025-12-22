import React, { useState, useCallback } from "react";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })
// import {PlotParams} from 'react-plotly.js';
//----------------------------------------------------------------------------//

var col_no = 20

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
    var secondKeys = {} // second dimension `id: label`, e.g. for traces
    var agg_l = agg["label"]
    var presorted = agg["sorted"] ? true : false

    filterOthers = false //true

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
            keyedFirst[k1] = {id: k1, label: l1, sum: 0, items: {}};
        }
        if (! secondKeys[k2]) {
            secondKeys[k2] = l2;
        }
        keyedFirst[k1]["items"][k2] = {"key": k2, "count": c, "label": l2};
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
      return keyedFirst[key];
    });

    // Sort the array based on the "sum" key in the second element
    sortedEntries = presorted ? sortedEntries : sortedEntries.sort((a, b) => a.sum < b.sum ? 1 : -1)

    var dist = [];
    var other_count = 0
    var others = {
        "other": {sum: 0, label: "other", items: {}}
    }
    Object.keys(secondKeys).forEach(function (s) {
        console.log(s)
        others["other"]["items"][s] = { "count": 0, "label": secondKeys[s] }
    })

    var i = 0
    var max_y = 0
    for (const seconds of sortedEntries) {
        // console.log(seconds)
        i += 1
        if (i <= col_no) {
            dist.push(seconds)
            if (seconds["sum"] > max_y) {
                max_y = seconds["sum"]
            }
        } else {
            other_count += seconds["sum"]
            for (const s of Object.keys(secondKeys)) {
                if (seconds[s]) {
                    others["other"]["items"][s]["count"] += seconds["items"][s]["count"];
                    others["other"]["sum"] += seconds["items"][s]["count"];
                }
            }
        }
    }

    if (other_count > 0) {
        if (filterOthers == true) {
            removed_count += other_count
            other_count = 0
        } else {
            dist.push(others["other"])
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
        // console.log(s)
        var thisTrace = {type: "bar", name: secondKeys[s], key: s, x: [], y: [], hovertext: []};
        for (const seconds of dist) {
            console.log(seconds)
            if (seconds["items"][s]) {
                thisTrace.y.push(seconds["items"][s]["count"]);
                thisTrace.x.push(seconds["id"]);
                if (dist.length > 1) {
                    let lab = `${seconds["items"][s]["label"]}: ${seconds["items"][s]["count"]}`;
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
                   {dist.length <= 8 && tracesData.length < 2 && !presorted ? (
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

 // 

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
        layout={
            {
                barmode: 'stack',
                width: outer_w,
                height: 240,
                title: {text: title},
                yaxis2: {
                    side: 'right'
                }
            }
        }
      />
    );
}

