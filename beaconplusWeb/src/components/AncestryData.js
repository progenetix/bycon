import React, { useState, useCallback } from "react"
import {VictoryPie, VictoryLegend } from "victory";

export function AncestryData({ individual }) {
    const processedData = individual?.genomeAncestry
        ?.sort((a, b) => a.label.localeCompare(b.label)) // Sort alphabetically
        ?.filter((datum) => parseFloat(datum.percentage) > 0); // Filter out data points with percentage of 0
    const legendData = processedData.map((datum) => ({ name: `${datum.label} ${datum.percentage}%` }))
    const colorScale = ['#E0BBE4', '#957DAD', '#D291BC', '#FEC8D8', '#FFDFD3', '#FEE1E8', '#D3C2CE']
    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    return (
        <>
            {processedData && processedData.length > 0 && (
                <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
                    <VictoryPie
                        data={processedData}
                        x="label"
                        y={(datum) => parseFloat(datum.percentage)}
                        radius={boundingRect.height * 0.35}
                        colorScale={colorScale}
                        height={boundingRect.height * 0.9}
                        width={boundingRect.width * 0.45}
                        style={{ labels: { display: "none" } }}
                    />
                    <VictoryLegend
                        data={legendData}
                        style={{ labels: { fontSize: 12} }}
                        colorScale={colorScale}
                        height={boundingRect.height * 0.9}
                        width={boundingRect.width * 0.45}
                    />
                </div>
            )}
        </>
    );
}