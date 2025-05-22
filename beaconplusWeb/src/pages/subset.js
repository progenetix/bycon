import {
  NoResultsHelp,
  urlRetrieveIds
} from "../hooks/api"
import { SubsetLoader } from "../components/SubsetLoader"
import { Layout } from "../site-specific/Layout"
import { withUrlQuery } from "../hooks/url-query"

const SubsetDetailsPage = withUrlQuery(({ urlQuery }) => {
  var { id, datasetIds } = urlRetrieveIds(urlQuery)
  return (
    <Layout title="Subset Details">
      {id && datasetIds ? (
        <SubsetLoader id={id} datasetIds={datasetIds} />
      ) : (
        NoResultsHelp("subset details")
      )}
    </Layout>
  )
})

export default SubsetDetailsPage

