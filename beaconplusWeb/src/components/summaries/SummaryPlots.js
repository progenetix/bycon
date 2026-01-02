import React, { useState, useCallback } from "react";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })
import SummaryTraces from "./SummaryTraces";

//----------------------------------------------------------------------------//

var colNo = 15

//----------------------------------------------------------------------------//

export function SummaryPlots({ summaryResults, filterUnknowns }) {

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

    let concepts        = agg["concepts"]
    console.log(Object.keys(agg));

    let dims = 1
    if (concepts && concepts.length > 0) {
        dims = concepts.length
    }

    let {tracesData, sankeyLabels, sankeyLinks} = SummaryTraces({ agg, filterUnknowns, filterOthers, colNo });

    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    const outer_w = boundingRect.width

    // console.log("tracesData for", agg["label"], ":", tracesData.length, concepts.length);

    if (tracesData.length == 0) {
        return <></>;
    }

    if (tracesData[0].x.length <= 8 && dims < 2 && !agg["sorted"]) {
        console.log("Rendering SimplePlotlyPie for", agg["label"]);
        return (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
            <SimplePlotlyPie
                tracesData={tracesData} outer_w={outer_w} title={agg["label"]}
            />
        </div>
        );
    }

    if (tracesData[0].x.length <= 8 && dims == 2 && sankeyLabels && sankeyLabels.length > 0) {
        console.log("Rendering SankeyPlot for", agg["label"]);
        return (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
            <SankeyPlot
                sankeyLabels={sankeyLabels}
                sankeyLinks={sankeyLinks}
                outer_w={outer_w}
                title={agg["label"] + " - Sankey Diagram"}
            />
        </div>
        );
    }

    console.log("Rendering StackedPlotlyBar for", agg["label"]);
    return (
    <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
        <StackedPlotlyBar
            tracesData={tracesData} outer_w={outer_w} title={agg["label"]}
        />
     </div>
    );

}

//----------------------------------------------------------------------------//
//----------------------------------------------------------------------------//
//----------------------------------------------------------------------------//

function SimplePlotlyPie({ tracesData, outer_w, title}) { //, title
    for (let trace of tracesData) {
        trace.type = 'pie';
        trace.hole = 0.4;
        trace.values = trace["y"];
        trace.labels = trace["x"];
        trace.hoverinfo = "text";
    }
    return (
      <Plot
        data={tracesData}
        layout={ {width: outer_w, height: 400, title: {text: title}} }
      />
    );
}

//----------------------------------------------------------------------------//

function StackedPlotlyBar({ tracesData, outer_w, title}) { //, title
    for (let trace of tracesData) {
        trace.type = 'bar';
        trace.hoverinfo = "text";
    }
    return (
      <Plot
        data={tracesData}
        layout={
            {
                barmode: 'stack',
                width: outer_w,
                height: 240,
                title: {text: title}
            }
        }
      />
    );
}

//----------------------------------------------------------------------------//

function SankeyPlot({ sankeyLabels, sankeyLinks, outer_w, title}) { //, title

    let sankeyData = {
        type: "sankey",
        orientation: "h",
        node: {
            pad: 15,
            thickness: 30,
            label: sankeyLabels,
        },
        link: sankeyLinks
    };

    sankeyData = [sankeyData];

    let sankeyLayout = {
        width: outer_w,
        height: 400,
        title: {text: title}
    };

    console.log("SankeyPlot sankeyData:", sankeyData[0]);
    console.log("SankeyPlot sankeyLayout:", sankeyLayout);

    return (
      <Plot
        data={sankeyData}
        layout={sankeyLayout}
      />
    );
}

