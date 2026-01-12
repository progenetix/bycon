
//----------------------------------------------------------------------------//

export default function SummaryTraces({ summary, filterUnknowns, colNo, includeOthers }) {
    // TODO: The handling of "other" is currently done downstream but it would be
    // simpler to have a rewrite of the 2D distributions after collating everything
    // above the cut-off - rewriting the first propertyValue to other...
    let presorted       = summary["sorted"] ? true : false
    let distribution    = summary["distribution"]
    let dimension       = summary["concepts"] ? summary["concepts"].length : 1

    // getting all keys and generating the sums for sorting
    // for 1..n dimensions but downstream only 1 or 2 are used so far
    let keyedProps      = []
    distribution.forEach(function (v) {
        const { conceptValues, count } = v;
        conceptValues.forEach(function (cv, index) {
            ! keyedProps[index] ? keyedProps[index] = {} : keyedProps
            let key = cv.id;
            let label = cv.label || key;
            if (! (key in keyedProps[index])) {
                keyedProps[index][key] = {id: key, label: label, sum: count};
            } else {
                keyedProps[index][key]["sum"] += count;
            }
        });
    });

    // sorting & limiting the first dimension based on the "sum" key
    let sortedFirsts = Object.keys(keyedProps[0]).map(function(key) {
      return keyedProps[0][key];
    });
    sortedFirsts = presorted ? sortedFirsts : sortedFirsts.sort((a, b) => a.sum < b.sum ? 1 : -1);

    // finding or creating the "other" category for the first dimension
    let other = sortedFirsts.find(obj => obj.id === 'other') ? sortedFirsts.find(obj => obj.id === 'other') : {id: "other", label: "other", sum: 0};
    if (! other["sum"]) {
        other["sum"] = 0;
    }

    // removal of the "other" category from the first dimension before processing
    sortedFirsts = sortedFirsts.filter(object => {
        return object.id !== "other";
    });

    // removal of the "unknown" and "undefined" categories from the first dimension
    let unfilteredNo = sortedFirsts.length;
    if (filterUnknowns == true) {
        sortedFirsts = sortedFirsts.filter(object => {
            return object.id !== "unknown";
        });
        sortedFirsts = sortedFirsts.filter(object => {
            return object.id !== "undefined";
        });
    }
    let filteredNo = unfilteredNo - sortedFirsts.length;
    console.log(`Filtered out ${filteredNo} 'unknown'/'undefined' from first dimension.`);

    if (sortedFirsts.length > colNo) {
        sortedFirsts = sortedFirsts.slice(0, colNo);
    }

    let sortedFirstIds = sortedFirsts.map(obj => obj.id);
    let limitedDistribution = [];
    let otherDistribution = [];
    distribution.forEach(function (v) {
        let cvs = v["conceptValues"];
        if (sortedFirstIds.includes(cvs[0]["id"])) {
            limitedDistribution.push(v);
        } else {
            otherDistribution.push(v);
            other["sum"] += v["count"];
        }
    });

    if (dimension == 1) {
        if (other["sum"] > 0 && includeOthers == true) {
            sortedFirsts.push(other);
            limitedDistribution.push({
                conceptValues: [
                    {id: "other", label: "other"}
                ],
                count: other["sum"]
            });
        }
        // Early return if only single dimension
        let {tracesData} = SingleTrace({sortedFirsts})
        return {tracesData};
    }

    // Now only if more than 1 dimension

    // sorting the second dimension
    let sortedSeconds = []
    let otherSeconds = {}

    if (dimension > 1) {
        sortedSeconds = Object.keys(keyedProps[1]).map(function(key) {
          return keyedProps[1][key];
        });
    }
    sortedSeconds = sortedSeconds.sort((a, b) => a.sum < b.sum ? 1 : -1);

    for (let s of sortedSeconds) {
        otherSeconds[s["id"]] = {id: s["id"], label: s["label"], count: 0};
    }
    otherSeconds["undefined"] = {id: "undefined", label: "undefined", count: 0};
    otherDistribution.forEach(function (v) {
        let cvs = v["conceptValues"];
        let secondId =  cvs[1] ? cvs[1]["id"] : "undefined";
        otherSeconds[ secondId ]["count"] += v["count"];
    });

    if (includeOthers == true) {
        sortedFirsts.push(other);
        // adding the "other" category for the second dimension if needed
        for (let s in otherSeconds) {
            if (otherSeconds[s]["count"] > 0) {
                limitedDistribution.push({
                    conceptValues: [
                        {id: "other", label: "other"},
                        {id: otherSeconds[s]["id"], label: otherSeconds[s]["label"]}
                    ],
                    count: otherSeconds[s]["count"]
                });
            }
        }
    }

    let {sankeyLabels, sankeyLinks} = SankeyLinks({sortedFirsts, sortedSeconds, limitedDistribution});
    let {tracesData} = MultiTraces({sortedFirsts, sortedSeconds, limitedDistribution});
    return {tracesData, sankeyLabels, sankeyLinks};

}

//----------------------------------------------------------------------------//

function SingleTrace({sortedFirsts}) {
    let tracesData = [{
        x: sortedFirsts.map(first => (first.id)),
        y: sortedFirsts.map(first => (first.sum)),
        hovertext: sortedFirsts.map(first => (`${first.label}: ${first.sum}`))
    }];
    return {tracesData};
}

//----------------------------------------------------------------------------//

function MultiTraces({sortedFirsts, sortedSeconds, limitedDistribution}) {
    const tracesData = sortedSeconds.map(second => {
      const trace = { name: second.label, x: [], y: [], hovertext: [] };
      sortedFirsts.forEach(first => {
        const count = CountMatches(limitedDistribution, first.id, second.id);
        trace.x.push(first.id);
        trace.y.push(count);
        trace.hovertext.push(`${first.label} & ${second.label}: ${count} of ${first.sum}`);
      });
      return trace;
    });
    return {tracesData};
}

//----------------------------------------------------------------------------//

function SankeyLinks({ sortedFirsts, sortedSeconds, limitedDistribution }) {
    // Create a map of node IDs to their indices
    const idToIndex = new Map();
    const uniqueNodes = new Set();
    
    // Collect nodes from both sortedFirsts and sortedSeconds
    const allNodes = [
        ...sortedFirsts.map(node => ({ id: node.id, label: node.label, sum: node.sum })),
        ...sortedSeconds.map(node => ({ id: node.id, label: node.label, sum: node.sum }))
    ];
    
    // Build the node map and collect unique nodes
    let index = 0;
    for (const node of allNodes) {
        if (!uniqueNodes.has(node.id)) {
            uniqueNodes.add(node.id);
            idToIndex.set(node.id, index++);
        }
    }
    
    // Build the node labels array
    const nodeLabels = Array.from(uniqueNodes).map(nodeId => {
        const node = allNodes.find(n => n.id === nodeId);
        return `${node.label}: ${node.label} (${node.sum})`;
    });
    
    // Build the links array
    const source = [];
    const target = [];
    const value = [];
    
    for (const entry of limitedDistribution) {
        const [firstNode, secondNode] = entry.conceptValues;
        const firstId = firstNode.id;
        const secondId = secondNode.id;
        
        // Check if both nodes exist in the map
        if (idToIndex.has(firstId) && idToIndex.has(secondId)) {
            const sourceIdx = idToIndex.get(firstId);
            const targetIdx = idToIndex.get(secondId);
            const count = entry.count;
            
            source.push(sourceIdx);
            target.push(targetIdx);
            value.push(count);
        }
    }
    
    return {
        sankeyLabels: nodeLabels,
        sankeyLinks: {
            source,
            target,
            value
        }
    };
}

//----------------------------------------------------------------------------//

function CountMatches(distribution, id1, id2) {
    let c = 0
    let matches = distribution.filter(function (v) {
        let cvs = v["conceptValues"];
        if (cvs.length == 2) {
            return (cvs[0]["id"] == id1 && cvs[1]["id"] == id2)
        } else {
            return []
        }
    });
    if (matches.length > 0) {
        c = matches[0]["count"]
    }
    return c;
}


