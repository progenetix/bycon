import { SITE_DEFAULTS } from "../../hooks/api"
import { Layout } from "../../site-specific/Layout"
import React, { useState } from "react"
import { useDropzone } from "react-dropzone"
import { uploadFile } from "../../hooks/api"
import Panel from "../../components/Panel"

export default function FileLoaderPage() {
  return (
    <Layout
      title="User File Upload"
      headline="Upload Files for CNV Visualization"
    >
      <Panel heading="CNV Data Plotting" className="content">
        <p>
          Here we provide users an option to visualize their own CNV data, using
          the standard Progenetix plotting options for histograms and samples.
          This functionality is currently limited to single segmens files
          without the group labeling options. However, we provide the plotting
          libraries as a Perl package through our{" "}
          <a
            href="https://github.com/progenetix/PGX"
            target="_blank"
            rel="noreferrer"
          >
            Github
          </a>{" "}
          repository. <b>NEW in 2023</b>: We transition to new plotting
          methods, provided through the `bycon` package and with demonstration
          applications in{" "}
          <a
            href="https://github.com/progenetix/byconaut"
            target="_blank"
            rel="noreferrer"
          >
            <i>byconaut</i>
          </a>.
        </p>
      </Panel>

      <div className="mb-5">
        <DataVisualizationUpload />
      </div>

      <Panel heading="Segment File format" className="content">
        <p>
          <b>NEW 2021</b>: We now recommend the use of our <code>.pgxseg</code>{" "}
          file format for th eupload of CNV segments files. As an extension of
          the standard tab-delimited segment file format below, the{" "}
          <code>.pgxseg</code> file format allows the addition of e.g. group
          label information. The file format is described on our{" "}
          <a
            href="https://docs.progenetix.org/services/#data-file-formats-pgxseg-segments-pgxfreq-cnv-frequencies"
            target="_blank"
            rel="noreferrer"
          >
            documentation site
          </a>
          {""}, including link to an example file.
        </p>
        <p>
          Otherwise, data has to be submitted as tab-delimited <code>.tsv</code>{" "}
          segment files. An example file is being provided{" "}
          <a
            href="/examples/multi-sample-segments-unfiltered.tsv"
            target="_blank"
            rel="noreferrer"
          >
            here
          </a>
          .
        </p>
        <p>
          While the header values are not being interpreted (i.e. it doesn not
          matter if the column is labeled <code>referenceName</code> or{" "}
          <code>chro</code>), the column order has to be respected:
        </p>
        <ol>
          <li>
            <code>biosample_id</code>
            <ul>
              <li>please use only word characters, underscores, dashes</li>
              <li>
                the <code>sample</code> value is used for splitting multi-sample
                files into their individual profiles
              </li>
            </ul>
          </li>
          <li>
            <code>reference_name</code>
            <ul>
              <li>the reference chromosome</li>
              <li>1-22, X, Y (23 =&gt; X; 24 =&gt; Y)</li>
            </ul>
          </li>
          <li>
            <code>start</code>
            <ul>
              <li>base positions according to the used reference genome</li>
            </ul>
          </li>
          <li>
            <code>end</code>
            <ul>
              <li>as above</li>
            </ul>
          </li>
          <li>
            <code>value</code>
            <ul>
              <li>the value of the segment</li>
              <li>should be 0-centered log2</li>
              <li>
                segments not passing the calling thresholds (fallback{" "}
                <code>0.15</code>, <code>-0.15</code>) are being filtered out
              </li>
              <li>
                one can use dummy values (e.g. <code>1</code> for gains,{" "}
                <code>-1</code> for losses)
              </li>
            </ul>
          </li>
          <li>
            <code>variant_type</code> (optional)
            <ul>
              <li>the called type of the segment</li>
              <li>
                one of <code>EFO:0030067</code> (CN gain) or <code>EFO:0030067</code> (deletion)
              </li>
              <li>
                this will override a status derived from thresholding the value
                in <code>mean</code>
              </li>
            </ul>
          </li>
        </ol>
      </Panel>
    </Layout>
  )
}

function DataVisualizationUpload() {
  const [result, setResult] = useState(null)
  return (
    <div>
      {result ? (
        <Results results={result} onCancelClicked={() => setResult(null)} />
      ) : (
        <Dropzone setResult={setResult} />
      )}
    </div>
  )
}

function Dropzone({ setResult }) {
  const { getRootProps, getInputProps } = useDropzone({
    accept: [".tsv", ".tab", ".pgxseg"],
    onDrop: async (acceptedFiles) => {
      const data = new FormData()
      data.append("upload_file", acceptedFiles[0], acceptedFiles[0].name)
      // data.append("plotType", "histoplot")
      const result = await uploadFile(data)
      setResult(result)
    }
  })

  return (
    <>
      <div className="content">
        <div {...getRootProps({ className: "dropzone" })}>
          <input {...getInputProps()} />
          <p>Drag and drop some files here, or click to select files.</p>
        </div>
      </div>
    </>
  )
}

function Results({ results, onCancelClicked }) {
  const fileId = results.fileId
  // const visualizationLink = getVisualizationLink("", "", fileId, "", "")
  const histoPlotLink = `${SITE_DEFAULTS.API_PATH}services/sampleplots/?datasetIds=upload&fileId=${fileId}`
  const samplesPlotLink = `${SITE_DEFAULTS.API_PATH}services/sampleplots/?datasetIds=upload&plotType=samplesplot&fileId=${fileId}`

  console.log("histoPlotLink...", histoPlotLink)

  return (
    <>
      <div className="message is-success animate__fadeIn animate__animated animate__faster">
        <div className="message-body content">
          <p>The file has been successfully uploaded!</p>
          <p>
{/*            <Link href={visualizationLink}>
              <a className="button is-link">Visualization form</a>
            </Link>
*/}           
            <a
              href={histoPlotLink}
              className="button is-link"
              style={{width : '200px'}}
              rel="noreferrer"
              target="_blank">
                CNV Histogram
            </a>
          </p>
          <p>
            <a
              href={samplesPlotLink}
              className="button is-link" 
              style={{width: '200px'}}
              rel="noreferrer"
              target="_blank">
                Samples Plot
            </a>
          </p>
          or{" "}
          <button onClick={onCancelClicked} className="button-link button-text">
            upload an other file instead.
          </button>
        </div>
      </div>
    </>
  )
}
