import React, { useState, useCallback } from "react";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })
// import {PlotParams} from 'react-plotly.js';
//----------------------------------------------------------------------------//

var col_no = 20

//----------------------------------------------------------------------------//

export function AggregatedPlots({ summaryResults, filterUnknowns }) {

    const filterOthers = false //true

    return (
        <>
        {summaryResults ? 
            summaryResults.map((r) => (
                <>
                {r["concepts"].length > 0 && (
                    <AggregationPlot
                        agg={r}
                        filterUnknowns={filterUnknowns}
                        filterOthers={filterOthers}
                    />
                )}
                </>
            )
        ) : (
            ""
        )}
        </>
    )
}

//----------------------------------------------------------------------------//

function AggregationPlot({ agg, filterUnknowns, filterOthers }) {

    let {tracesData, agg_l, presorted} = MakeTraces({ agg, filterUnknowns, filterOthers });

    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    var outer_w = boundingRect.width

    return (
        <>
            {tracesData[0].x.length > 0 ? (
                <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
                   <>
                   {/*The following has to be defined - avoiding here the incomplete pie definitions */}
                   {tracesData[0].x.length <= 8 && tracesData.length < 2 && !presorted ? (
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

function MakeTraces({ agg, filterUnknowns, filterOthers }) {

    var keyedProps = []
    var keyedFirsts = {}
    var keyedSeconds = {} // second dimension `id: label`, e.g. for traces
    var agg_l = agg["label"]
    var tracesData = []

    let presorted = agg["sorted"] ? true : false

    // getting all keys and generating the sums for sorting
    // very verbose for 1 or 2 dimensions only - can be optimized later
    agg["distribution"].forEach(function (v) {
        let cvs = v["conceptValues"];
        let c = v["count"]
        cvs.forEach(function (cv, index) {
            ! keyedProps[index] ? keyedProps[index] = {} : keyedProps
            let k = cv["id"];
            let l = cv["label"] ? cv["label"] : k;
            if (! (k in keyedProps[index]) ) {
                keyedProps[index][k] = {id: k, label: l, sum: c};
            } else {
                keyedProps[index][k]["sum"] += c;
            }
        });
    });

    // console.log(keyedProps)

    // sorting & limiting the first dimension
    var sortedFirsts = Object.keys(keyedProps[0]).map(function(key) {
      return keyedProps[0][key];
    });

    // Sort the array based on the "sum" key in the second element
    sortedFirsts = presorted ? sortedFirsts : sortedFirsts.sort((a, b) => a.sum < b.sum ? 1 : -1);

    var other = sortedFirsts.find(obj => obj.id === 'other') ? sortedFirsts.find(obj => obj.id === 'other') : {id: "other", label: "other", sum: 0};
    var otherIds = []
    // console.log("...other before", other);

    sortedFirsts = sortedFirsts.filter(object => {
        return object.id !== "other";
    });

    var filteredFirsts = []
    i = 0
    for (const first of sortedFirsts) {
        i += 1
        if (i <= col_no) {
            filteredFirsts.push(first)
        } else {
            other["sum"] += first["sum"]
            otherIds.push(first["id"])
        }
    }
    if (other["sum"] > 0) {
        filteredFirsts.push(other)
    }

    // ====================================================================== //

    // Early return if only single dimension
    if (keyedProps.length == 1) {
        console.log(`single dimension for "${agg_l}"`)
        var xs = [];
        var ys = [];
        var hos = [];
        for (const first of filteredFirsts) {
            xs.push(first["id"]);
            ys.push(first["sum"]);
            hos.push(`${first["label"]}: ${first["sum"]}`);
        }
        tracesData.push({type: "bar", name: agg_l, x: xs, y: ys, hovertext: hos});
        console.log("..tracesData", tracesData);
        return ({tracesData, agg_l, presorted})
    }

    // ====================================================================== //


    // sorting & limiting the first dimension
    var sortedSeconds = Object.keys(keyedProps[1]).map(function(key) {
      return keyedProps[1][key];
    });

    sortedSeconds = sortedSeconds.sort((a, b) => a.sum < b.sum ? 1 : -1);
    
    for (const first of filteredFirsts) {
        let id1 = filteredFirsts["id"]
        let lab1 = filteredFirsts["label"]
        let thisTrace = {type: "bar", name: lab1, x: [], y: [], hovertext: []}



        for (const second of sortedSeconds) {
            let id2 = sortedSeconds["id"]


        }
    }



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
        if (! (k1 in keyedFirsts) ) {
            keyedFirsts[k1] = {id: k1, label: l1, sum: 0, items: {}};
        }
        if (! keyedSeconds[k2]) {
            keyedSeconds[k2] = l2;
        }
        keyedFirsts[k1]["items"][k2] = {"key": k2, "count": c, "label": l2};
        keyedFirsts[k1]["sum"] += c;
    });

    var removed_count = 0

    // Filter unknowns and undefineds prototyping WIP
    if (filterUnknowns == true) {
        if (Object.keys(keyedFirsts).includes('undefined')) {
            removed_count += keyedFirsts["undefined"]["sum"]
            delete keyedFirsts["undefined"]
        }
    }

    if (filterUnknowns == true) {
        if (Object.keys(keyedFirsts).includes('unknown')) {
            removed_count += keyedFirsts["unknown"]["sum"]
            delete keyedFirsts["unknown"]
        }
    }

    if (filterOthers == true) {
        if (Object.keys(keyedFirsts).includes('other')) {
            removed_count += keyedFirsts["other"]["sum"]
            delete keyedFirsts["other"]
        }
    }

    // Create items array
    var sortedEntries = Object.keys(keyedFirsts).map(function(key) {
      return keyedFirsts[key];
    });

    // Sort the array based on the "sum" key in the second element
    sortedEntries = presorted ? sortedEntries : sortedEntries.sort((a, b) => a.sum < b.sum ? 1 : -1)

    var dist = [];
    var other_count = 0
    var others = {
        "other": {sum: 0, label: "other", items: {}}
    }
    Object.keys(keyedSeconds).forEach(function (s) {
        // console.log(s)
        others["other"]["items"][s] = { id: s, count: 0, label: keyedSeconds[s] }
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
            for (const s of Object.keys(keyedSeconds)) {
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

    Object.keys(keyedSeconds).sort().forEach(function (s) {
        // console.log(s)
        var thisTrace = {type: "bar", name: keyedSeconds[s], key: s, x: [], y: [], hovertext: []};
        for (const seconds of dist) {
            // console.log(seconds)
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

    return ({tracesData, agg_l, presorted})
 
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

