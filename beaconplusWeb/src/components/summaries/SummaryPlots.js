import React, { useState, useCallback } from "react";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })
import SummaryTraces from "./SummaryTraces";

//----------------------------------------------------------------------------//

const colNo = 20
const includeOthers = true
// const includeOthers = false
const dashboardPies = ["selectedPlatformTechnologies", "sampleCountries"]
const dashboardSankeys = ["selectedHistologicalDiagnoses::sampleSex"]

//----------------------------------------------------------------------------//

export function SummaryPlots({ resultsAggregation, filterUnknowns }) {

    return (
        <>
        {resultsAggregation ? 
            resultsAggregation.map((r) => (
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

    let {summaryId, summaryLabel, tracesData, sankeyLabels, sankeyLinks} = SummaryTraces({ summary, filterUnknowns, colNo, includeOthers });

    console.log("==>> Plot for", summaryId, summaryLabel, tracesData);

    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    const outer_w = boundingRect.width

    if (!summaryId) {
        console.log("undefined summaryId")
        return <></>;
    }

    if (!tracesData) {
        console.log("undefined tracesData")
        return <></>;
    }
    if (tracesData.length == 0) {
        return <></>;
    }

    if (dashboardPies.includes(summaryId)) {
        console.log("Rendering SimplePlotlyPie for", summaryLabel);
        return (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
            <SimplePlotlyPie
                tracesData={tracesData} outer_w={outer_w} title={summaryLabel}
            />
        </div>
        );
    }

    if (dashboardSankeys.includes(summaryId)) {
        console.log("Rendering SankeyPlot for", summaryLabel);
        return (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
            <SankeyPlot
                sankeyLabels={sankeyLabels}
                sankeyLinks={sankeyLinks}
                outer_w={outer_w}
                title={summaryLabel + " - Sankey Diagram"}
            />
        </div>
        );
    }

    console.log("Rendering StackedPlotlyBar for", summaryLabel);
    return (
    <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
        <StackedPlotlyBar
            tracesData={tracesData} outer_w={outer_w} title={summaryLabel}
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

