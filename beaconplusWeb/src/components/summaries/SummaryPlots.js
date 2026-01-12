import React, { useState, useCallback } from "react";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })
import SummaryTraces from "./SummaryTraces";

//----------------------------------------------------------------------------//

const colNo = 20
const includeOthers = true
// const includeOthers = false
const dashboardPies = ["selectedPlatformTechnologies", "sampleCountries"]
const dashboardSankeys = ["selectedDiagnosesBySex"]
// let sankeyHeight = 400

//----------------------------------------------------------------------------//

export function SummaryPlots({ summaryResults, filterUnknowns }) {

    return (
        <>
        {summaryResults ? 
            summaryResults.map((r) => (
                <>
                {r["concepts"].length > 0 && (
                    <SummaryPlot
                        summary={r}
                        filterUnknowns={filterUnknowns}
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

function SummaryPlot({ summary, filterUnknowns }) {

    console.log("==>> Plot for", summary["label"]);
    let summaryId = summary["id"]

    let {tracesData, sankeyLabels, sankeyLinks} = SummaryTraces({ summary, filterUnknowns, colNo, includeOthers });

    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    const outer_w = boundingRect.width

    // console.log("tracesData for", summary["label"], ":", tracesData.length, concepts.length);

    if (tracesData.length == 0) {
        return <></>;
    }

    if (dashboardPies.includes(summaryId)) {
        console.log("Rendering SimplePlotlyPie for", summary["label"]);
        return (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
            <SimplePlotlyPie
                tracesData={tracesData} outer_w={outer_w} title={summary["label"]}
            />
        </div>
        );
    }

    if (dashboardSankeys.includes(summaryId)) {
        console.log("Rendering SankeyPlot for", summary["label"]);
        return (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
            <SankeyPlot
                sankeyLabels={sankeyLabels}
                sankeyLinks={sankeyLinks}
                outer_w={outer_w}
                title={summary["label"] + " - Sankey Diagram"}
            />
        </div>
        );
    }

    console.log("Rendering StackedPlotlyBar for", summary["label"]);
    return (
    <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
        <StackedPlotlyBar
            tracesData={tracesData} outer_w={outer_w} title={summary["label"]}
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
        trace.values = trace.y;
        trace.labels = trace.x;
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
                height: 400,
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
        // height: 400,
        title: {text: title}
    };

    return (
      <Plot
        data={sankeyData}
        layout={sankeyLayout}
      />
    );
}

