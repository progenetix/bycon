import {
  NoResultsHelp,
  urlRetrieveIds
} from "../hooks/api"
import { SubsetLoader } from "../components/SubsetLoader"
import { Layout } from "../site-specific/Layout"
import { withUrlQuery } from "../hooks/url-query"

const SubsetDetailsPage = withUrlQuery(({ urlQuery }) => {
  const { id, datasetIds, hasAllParams } = urlRetrieveIds(urlQuery)
  return (
    <Layout title="Subset Details">
      {!hasAllParams ? (
        NoResultsHelp("subset details")
      ) : (
        <SubsetLoader id={id} datasetIds={datasetIds} />
      )}
    </Layout>
  )
})

export default SubsetDetailsPage

