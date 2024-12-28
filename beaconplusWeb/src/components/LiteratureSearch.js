import React, { useState } from "react"
import {
    useServiceItemDelivery,
    useLiteratureSearchResults,
    useLiteratureCellLineMatches
} from "../hooks/api"
import cn from "classnames"
import { Loader } from "./Loader"
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
const service = "collations"

export function LiteratureSearch({ id, datasetIds, plotGeneSymbols, setGeneSymbols, plotCytoregionLabels, setCytoregionSymbols})
{
    console.log(setGeneSymbols, setCytoregionSymbols)

    const { data, error, isLoading } = useServiceItemDelivery(
        id,
        service,
        datasetIds
    )
    return (
        <Loader isLoading={isLoading} hasError={error} background>
            {data && (
                <LiteratureSearchResultsTabbed label={data.response.results[0].label} plotGeneSymbols={plotGeneSymbols} setGeneSymbols={setGeneSymbols} plotCytoregionLabels={plotCytoregionLabels} setCytoregionSymbols={setCytoregionSymbols}/>
            )}
        </Loader>
    );
}

function LiteratureSearchResultsTabbed({label, plotGeneSymbols, setGeneSymbols, plotCytoregionLabels, setCytoregionSymbols}) {

    const {data,error,isLoading} = useLiteratureCellLineMatches(label);
    const TABS = {
        genes: { id: "genes", label: "Gene Matches", info: "Genes that have been matched in publications related to the cell line. The connection between gene and cell line may be indirect (e.g. as part of a process affected in the CL) or circumstantial (e.g. involving another CL or sample discussed in the context)."},
        cytobands: { id: "cytobands", label: "Cytoband Matches", info: "Genomic regions by cytoband annotation (8q24, 17p ...) named in a CL context"},
        variants: { id: "variants", label: "Variants", info: "Genomic variation types or processes mentioned in the context of the CL, in the corresponding publication (not necessarily applying to the CL itself)"}
    }
    // process: "Disease Annotations",
    // TABS.process,

    const tabNames = [TABS.genes.label, TABS.cytobands.label, TABS.variants.label]
    const [selectedTab, setSelectedTab] = useState(tabNames[0])

    return (
        <Loader isLoading={isLoading} hasError={error} background>
            {data && Object.keys(data).length > 0 ?
                <div className="box">
                    {tabNames?.length > 0 ?
                        <div className="tabs is-boxed">
                            <ul>
                                {tabNames.map((tabName, i) => (
                                    <li
                                        className={cn({
                                            "is-active": selectedTab === tabName
                                        })}
                                        key={i}
                                        onClick={() => setSelectedTab(tabName)}
                                    >
                                        <a>{tabName}</a>
                                    </li>
                                ))}
                            </ul> 
                        </div>
                        : null}
                    {data?.Gene?.length > 0 && selectedTab === TABS.genes.label &&
                        <GeneComponent cellline={label} genes={data.Gene.sort()} plotGeneSymbols={plotGeneSymbols} setGeneSymbols={setGeneSymbols}/>
                    }
                    {data?.Band?.length > 0 && selectedTab === TABS.cytobands.label &&
                        <CytobandComponent cellline={label} cytobands={data.Band.sort()} plotCytoregionLabels={plotCytoregionLabels} setCytoregionSymbols={setCytoregionSymbols}/>
                    }
                    {data?.Variant?.length > 0 && selectedTab === TABS.variants.label &&
                        <ResultComponent cellline={label} entities={data.Variant} />
                    }
                </div> : "Nothing to see here..."
            }
        </Loader>
    )
}

/*==============================================================================
================================================================================
==============================================================================*/

function GeneComponent({cellline, genes, plotGeneSymbols, setGeneSymbols})
{
 console.log(plotGeneSymbols)
    return (
        <section className="content">
            <table>
                {plotGeneSymbols.length >= 1 ? <tr><td colSpan="9" align="center"><Button contained color="secondary" onClick={() => window.location.reload(true)}>Clear Annotations</Button></td></tr> : ""}
                {genes.map((gene,i)=>(<GeneResultSet key={`${i}`} gene={gene} cellline={cellline} plotGeneSymbols={plotGeneSymbols} setGeneSymbols={setGeneSymbols}/>))}
            </table>
        </section>
    );
}

function CytobandComponent({cellline, cytobands, plotCytoregionLabels, setCytoregionSymbols})
{
  return (
    <section className="content">
      <table>
        {plotCytoregionLabels.length >= 1 ? <tr><td colSpan="9" align="center"><Button contained color="secondary" onClick={() => window.location.reload(true)}>Clear Annotations</Button></td></tr> : ""}
        {cytobands.map((cytoband,i)=>(<CytobandResultSet key={`${i}`} cytoband={cytoband} cellline={cellline} plotCytoregionLabels={plotCytoregionLabels} setCytoregionSymbols={setCytoregionSymbols}/>))}
      </table>
    </section>
  );
}

function ResultComponent({cellline, entities})
{
    return (
        <section className="content">
            <table>
                {entities.map((ent,i)=>(<ResultSet key={`${i}`} entity={ent} cellline={cellline} />))}
            </table>
        </section>
    );
}

/*============================== gene labeling ===============================*/

function addGeneLabel(gene, plotGeneSymbols, setGeneSymbols, setLabelButton) {
    var l = plotGeneSymbols;
    setLabelButton(true)
    if (l === "") {
        l += gene;
    } else {
        l += "," + gene;
    }
    window.scrollTo(0, 0);
    setGeneSymbols(l);
}

/*============================ cytoband labeling =============================*/

function addCytobandLabel(cytoband, plotCytoregionLabels, setCytoregionSymbols, setCytobandLabelButton) {
    var c = plotCytoregionLabels;
    setCytobandLabelButton(true)
    if (c === "") {
        c += cytoband;
    } else {
        c += "," + cytoband;
    }
    window.scrollTo(0, 0);
    setCytoregionSymbols(c);
}

function GeneResultSet({cellline, gene, plotGeneSymbols, setGeneSymbols})
{
    const {data, error, isLoading} = useLiteratureSearchResults([cellline],[gene]);
    const [expand, setExpand] = useState(false);
    const [labelButton, setLabelButton] = useState(false);

    //console.log('data:', data)
    return (
        <Loader isLoading={isLoading} hasError={error} background>
            {data && data.pairs.length > 0 ? <tr><td>
                {labelButton && plotGeneSymbols.length > 1 ? <Button disabled variant="contained">{gene}</Button> :
                    <Tooltip title={`add gene ${gene} to the plot!`}>
                        <Button onClick={()=>addGeneLabel(gene, plotGeneSymbols, setGeneSymbols, setLabelButton)}>{gene}</Button>
                    </Tooltip>}
            </td>
                {expand ?
                    <td>{data.pairs.map((pair,i)=>(<ResultRow key={`${i}`} pair={pair}/>))}</td>
                    :
                    <td><ResultRow key={0} pair={data.pairs[0]} expand={expand} setExpand={setExpand}/></td>
                }

                {data.pairs.length < 2 ?
                    <td>&nbsp;</td>
                    :
                    <td>
                        <Button color="secondary" onClick={() => {setExpand(!expand)}}>{expand ? <b>Close</b> : <b>More Abstracts</b>}</Button>
                    </td>
                }
            </tr> : ""}
        </Loader>
    )
}

function CytobandResultSet({cellline, cytoband, plotCytoregionLabels, setCytoregionSymbols})
{
    const {data, error, isLoading} = useLiteratureSearchResults([cellline],[cytoband]);
    const [expand, setExpand] = useState(false);
    const [cytobandLabelButton, setCytobandLabelButton] = useState(false);

    console.log(cytoband)
    return (
        <Loader isLoading={isLoading} hasError={error} background>
            {data && data.pairs.length > 0 ? <tr><td>
                {cytobandLabelButton && plotCytoregionLabels?.length > 1 ? <Button disabled variant="contained">{cytoband}</Button> :
                    <Tooltip title={`add cytoband ${cytoband} to the plot!`}>
                        <Button onClick={()=>addCytobandLabel(cytoband, plotCytoregionLabels, setCytoregionSymbols, setCytobandLabelButton)}>{cytoband}</Button>
                    </Tooltip>}
            </td>
                {expand ?
                    <td>{data.pairs.map((pair,i)=>(<ResultRow key={`${i}`} pair={pair}/>))}</td>
                    :
                    <td><ResultRow key={0} pair={data.pairs[0]} expand={expand} setExpand={setExpand}/></td>
                }

                {data.pairs.length < 2 ?
                    <td>&nbsp;</td>
                    :
                    <td>
                        <Button color="secondary" onClick={() => {setExpand(!expand)}}>{expand ? <b>Close</b> : <b>Expand</b>}</Button>
                    </td>
                }
            </tr> : ""}
        </Loader>
    )
}

function ResultSet({cellline,entity})
{
    const {data,error,isLoading} = useLiteratureSearchResults([cellline],[entity]);
    return (
        <Loader isLoading={isLoading} hasError={error} background>
            {data && data.pairs.length > 0 ? <tr><td>
                <b>{entity}</b>
            </td><td>{data.pairs.map((pair,i)=>(<ResultRow key={`${i}`} pair={pair} />))}</td></tr> : ""}
        </Loader>
    )
}

// function GeneResultRow({pair})
// {
//     const [showAbstract, setShowAbstract] = useState(false);
//     return (
//         <tr>
//             <table>
//                 <tr>
//                     <td style={{border: '0px'}}>
//                         <div dangerouslySetInnerHTML={{ __html:pair.text}}/>
//                     </td>
//                     <td colSpan="3"  style={{border: '0px'}}>
//                         <a target="_blank" rel="noreferrer" href={"https://pubmed.ncbi.nlm.nih.gov/"+pair.pmid}>{pair.title} ({pair.pmid})</a>
//                     </td>
//                     <td style={{border: '0px'}}><Button onClick={() => {setShowAbstract(!showAbstract)}}>{!showAbstract ? <p>Abstract</p> : <p>Close Abstract</p>}</Button></td>
//                 </tr>
//                 {showAbstract ?
//                     <tr>
//                         <td colSpan="9" dangerouslySetInnerHTML={{ __html:pair.abstract}} style={{border: '0px'}}></td>
//                     </tr>
//                     : ""}
//             </table>
//         </tr>
//     );
// }

// TODO: Standard react memo(?) component for table
function ResultRow({pair})
{
    const [showAbstract, setShowAbstract] = useState(false);
    return (
        <tr>
            <table>
                <tr>
                    <td style={{border: '0px'}}>
                        <div dangerouslySetInnerHTML={{ __html:pair.text}}/>
                    </td>
                    <td style={{border: '0px'}}>
                        <a target="_blank" rel="noreferrer" href={"https://pubmed.ncbi.nlm.nih.gov/"+pair.pmid}>{pair.title}</a>
                    </td>
                    <td style={{border: '0px'}}><Button onClick={() => {setShowAbstract(!showAbstract)}}>{!showAbstract ? <p>Abstract</p> : <p>Close Abstract</p>}</Button></td>
                </tr>
                {showAbstract ?
                    <tr>
                        <td colSpan="9" dangerouslySetInnerHTML={{ __html:pair.abstract}} style={{border: '0px'}}></td>
                    </tr>
                    : ""}
            </table>
        </tr>
    );
}

