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
  return summaryResults.map((r) => (
    <>
    {console.log(r)}
    {console.log(r["concepts"].length)}
    {r["concepts"].length == 1 && (
     <AggregatedDiagnoses agg={r} />
    )
    }
    </>
  ))
}


function AggregatedDiagnoses({ agg }) {

    console.log(agg)

    // const agg = summaryResults.find(item => item.id === "histologicalDiagnoses");

    const dist_all = agg["distribution"].map(item => ({
      id: item.conceptValues[0].id,
      label: item.conceptValues[0].label + " (" + item.count +")",
      count: item.count
    })).sort((a, b) => a.count < b.count ? 1 : -1)

    const agg_l = agg["label"]

    var dist = []
    var other = {
        id: "other",
        label: "other...",
        count: 0
    }

    var i = 0
    dist_all.forEach(function (item) {
        i += 1
        if (i < 21) {
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

    const padd = boundingRect.width / c

    return (
        <>
        {dist && dist.length > 1 && (
        <div ref={containerRef} style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", width: "100%", marginBottom: "0px" }}>
            <VictoryChart
                domainPadding={{ x: padd }}
                height={250}
                width={boundingRect.width}
                theme={VictoryTheme.material}
                  padding={{
                    left: 50,
                    top: 30,
                    right: 10,
                    bottom: 120,
                  }}
              >
                <VictoryLabel         
                    text={agg_l}         
                    textAnchor="middle"
                    x={boundingRect.width * 0.5}        
                    y={25}
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
