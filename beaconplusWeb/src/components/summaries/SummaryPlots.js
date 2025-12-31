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

    let {tracesData} = SummaryTraces({ agg, filterUnknowns, filterOthers, colNo });

    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    const outer_w = boundingRect.width

    return (
        <>
            {tracesData[0].x.length > 0 ? (
                <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
                   <>
                   {/*The following has to be defined - avoiding here the incomplete pie definitions */}
                   {tracesData[0].x.length <= 8 && tracesData.length < 2 && !agg["sorted"] ? (
                        <SimplePlotlyPie
                            tracesData={tracesData} outer_w={outer_w} title={agg["label"]}
                        />
                    ) : (
                        <StackedPlotlyBar
                            tracesData={tracesData} outer_w={outer_w} title={agg["label"]}
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

