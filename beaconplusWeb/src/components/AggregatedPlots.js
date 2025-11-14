import React, { useState, useCallback } from "react";
import {
    VictoryChart,
    VictoryLabel,
    VictoryAxis,
    VictoryBar,
    VictoryTheme,
    VictoryTooltip,
    // VictoryZoomContainer
} from 'victory';

export function AggregatedPlots({ summaryResults }) {
    return (
        <>
        {summaryResults ? (
            summaryResults.map((r) => (
                <>
                {r["concepts"].length == 1 && (
                    <AggregatedPlot agg={r} />
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



function AggregatedPlot({ agg }) {

    var dist_all = agg["distribution"].map(item => ({
      id: item.conceptValues[0].id,
      label: `${item.conceptValues[0].label} (${item.conceptValues[0].id}, ${item.count})`,
      count: item.count
    }))

    const agg_l = agg["label"]

    dist_all = agg["sorted"] ? dist_all : dist_all.sort((a, b) => a.count < b.count ? 1 : -1)

    var dist = []
    var other = {
        id: "other",
        label: "other...",
        count: 0
    }

    var col_no = 25
    var i = 0
    dist_all.forEach(function (item) {
        i += 1
        if (i < col_no) {
            dist.push(item)
        } else {
            other["count"] += item["count"]
        }
    });

    if (other["count"] > 0) {
        other["label"] += " (" + other.count +")"
        dist.push(other)
    }

    const [boundingRect, setBoundingRect] = useState({ width: 0, height: 0 });
    const containerRef = useCallback((node) => {
        if (node !== null) { setBoundingRect(node.getBoundingClientRect()); }
    }, []);

    var c = dist.length
    if (c < 1) {
        c = 0
    }

    const padd_l = 70
    const padd_r = 30
    const padd_t = 30
    const padd_b = 120

    const plot_h = 250

    var outer_w = boundingRect.width

    const padd = outer_w / c

    return (
        <>
        {dist && dist.length > 1 && (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
            <VictoryChart
                domainPadding={{ x: padd }}
                height={plot_h}
                width={outer_w}
                theme={VictoryTheme.material}
                padding={{left: padd_l, top: padd_t, right: padd_r, bottom: padd_b}}
              >
                <VictoryLabel         
                    text={agg_l}         
                    textAnchor="middle"
                    x={outer_w * 0.5}        
                    y={padd_t - 15}
                />
                <VictoryBar
                    data={dist}
                    x="id"         
                    y="count"
                    theme={VictoryTheme.clean}
                    labelComponent={<VictoryTooltip />}
                    labels={({ label }) => label}
                    style={{
                      data: {
                        fill: "#c43a31",
                        fillOpacity: 0.4,
                        stroke: "#c43a31",
                        strokeWidth: 2,
                      },
                      labels: {
                        fontSize: 12,
                        fill: "#c43a31",
                      },
                    }}
                />
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
        </div>

        )}
        </>
    );
}

                // containerComponent={
                //     <VictoryZoomContainer
                //       zoomDimension="x"
                //       zoomDomain={{ x: [0, 15] }}
                //       minimumZoom={{ x: 1 }}
                //     />
                //   }
