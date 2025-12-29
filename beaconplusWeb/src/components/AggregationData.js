
//----------------------------------------------------------------------------//

export default function MakeTraces({ agg, filterUnknowns, filterOthers, colNo }) {

    let presorted = agg["sorted"] ? true : false
    let distribution = agg["distribution"]
    let keyedProps = []

    // getting all keys and generating the sums for sorting
    // for 1..n dimensions but downstream only 1 or 2 are used so far
    distribution.forEach(function (v) {
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

    // sorting & limiting the first dimension based on the "sum" key
    let sortedFirsts = Object.keys(keyedProps[0]).map(function(key) {
      return keyedProps[0][key];
    });
    sortedFirsts = presorted ? sortedFirsts : sortedFirsts.sort((a, b) => a.sum < b.sum ? 1 : -1);

    // finding or creating the "other" category for the first dimension
    let other = sortedFirsts.find(obj => obj.id === 'other') ? sortedFirsts.find(obj => obj.id === 'other') : {id: "other", label: "other", sum: 0};
    let otherIds = []

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

    // filtering based on the column number with other matches counted with the "other" category
    let filteredFirsts = []
    let i = 0
    for (const first of sortedFirsts) {
        i += 1
        if (i <= colNo) {
            filteredFirsts.push(first)
        } else {
            other["sum"] += first["sum"]
            otherIds.push(first["id"])
        }
    }

    // Early return if only single dimension
    if (keyedProps.length == 1) {
        return SingleTrace({filteredFirsts, other, filterOthers});
    }

    // sorting the second dimension
    let sortedSeconds = Object.keys(keyedProps[1]).map(function(key) {
      return keyedProps[1][key];
    });
    sortedSeconds = sortedSeconds.sort((a, b) => a.sum < b.sum ? 1 : -1);

    return MultiTraces({filteredFirsts, other, otherIds, filterOthers, sortedSeconds, distribution});

}

//----------------------------------------------------------------------------//

function MultiTraces({filteredFirsts, other, otherIds, filterOthers, sortedSeconds, distribution}) {

    let tracesData = []
    
    for (const second of sortedSeconds) {
        let id2 = second["id"]
        let lab2 = second["label"]
        let thisTrace = {name: lab2, x: [], y: [], hovertext: []}
        for (const first of filteredFirsts) {
            let id1 = first["id"]
            let lab1 = first["label"]
            let c = CountMatches(distribution, id1, id2)
            thisTrace.x.push(id1);
            thisTrace.y.push(c);
            let lab = `${lab1} & ${lab2}: ${c}`;
            lab += ` of ${first["sum"]}`;
            thisTrace.hovertext.push(lab);
        }
        // adding the "other" category if needed as last entry per trace
        if (filterOthers == false) {
            let c = 0
            for (const oid of otherIds) {
                c += CountMatches(distribution, oid, id2)
            }
            if (c > 0) {
                thisTrace.x.push("other");
                thisTrace.y.push(c);
                let lab = `other & ${lab2}: ${c}`;
                lab += ` of ${other["sum"]}`;
                thisTrace.hovertext.push(lab);
            }
        }
        tracesData.push(thisTrace);
    }

    return ({tracesData})
 
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
    return c
}

//----------------------------------------------------------------------------//

function SingleTrace({filteredFirsts, other, filterOthers}) {
    if (other["sum"] > 0 && filterOthers == false) {
        filteredFirsts.push(other)
    }
    let xs = [];
    let ys = [];
    let hos = [];
    for (const first of filteredFirsts) {
        xs.push(first["id"]);
        ys.push(first["sum"]);
        hos.push(`${first["label"]}: ${first["sum"]}`);
    }
    const tracesData = [{x: xs, y: ys, hovertext: hos}];
    return ({tracesData})
}

