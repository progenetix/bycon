
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
    let sortedFirsts    = Object.keys(keyedProps[0]).map(function(key) {
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
    if (filterUnknowns == true) {
        sortedFirsts = sortedFirsts.filter(object => {
            return object.id !== "unknown";
        });
        sortedFirsts = sortedFirsts.filter(object => {
            return object.id !== "undefined";
        });
    }

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
    let tracesData = [{x: [], y: [], hovertext: []}];
    for (const first of sortedFirsts) {
        console.log("...SingleTrace first:", first)
        tracesData[0].x.push(first["id"]);
        tracesData[0].y.push(first["sum"]);
        tracesData[0].hovertext.push(`${first["label"]}: ${first["sum"]}`);
    }
    return {tracesData};
}

//----------------------------------------------------------------------------//

function MultiTraces({sortedFirsts, sortedSeconds, limitedDistribution}) {
    let tracesData = []
    for (const second of sortedSeconds) {
        let id2 = second["id"]
        let lab2 = second["label"]
        let thisTrace = {name: lab2, x: [], y: [], hovertext: []}
        for (const first of sortedFirsts) {
            let id1 = first["id"]
            let c = CountMatches(limitedDistribution, id1, id2)
            let lab = `${first["label"]} & ${lab2}: ${c} of ${first["sum"]}`;
            thisTrace.x.push(id1);
            thisTrace.y.push(c);
            thisTrace.hovertext.push(lab);
        }
        tracesData.push(thisTrace);
    }
    return {tracesData};
 
}
//----------------------------------------------------------------------------//

function SankeyLinks({sortedFirsts, sortedSeconds, limitedDistribution}) {

    let sankeyKeys = []
    let sankeyLabels = []
    let sankeyLinks = {
        source: [],
        target: [],
        value:  []
    }

    for (const f of sortedFirsts.concat(sortedSeconds)) {
        if (!sankeyKeys.includes(f["id"])) {
            sankeyKeys.push(f["id"])
            sankeyLabels.push(`${f["label"]}: ${f["label"]} (${f["sum"]})`)
        }
    }

    for (const d in limitedDistribution) {
        let cvs = limitedDistribution[d]["conceptValues"];
        if (cvs.length == 2) {
            let id1 = cvs[0]["id"];
            let id2 = cvs[1]["id"];
            let targetIndex = sankeyKeys.indexOf(id2);
            let count = limitedDistribution[d]["count"];
            if (sankeyKeys.includes(id1)) {
                let sourceIndex = sankeyKeys.indexOf(id1);
                sankeyLinks["source"].push(sourceIndex);
                sankeyLinks["target"].push(targetIndex);
                sankeyLinks["value"].push(count);
            }
        }
    }
 
    return {sankeyLabels, sankeyLinks};
 
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


