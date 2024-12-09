// Small "functional" tree utilities. See tests for understanding
export function hasChildren(node) {
  return (
    !!node &&
    typeof node === "object" &&
    typeof node.children !== "undefined" &&
    node.children.length > 0
  )
}

export function getNode(node, path) {
  const id = path.slice(-1)[0]
  const parentPath = path.slice(0, -1)
  if (parentPath.length > 0) {
    const parentNode = getNode(node, parentPath)
    if (hasChildren(parentNode)) {
      return parentNode.children.find((c) => c.id === id)
    } else return null
  } else {
    if (node.id === id) return node
    return null
  }
}

// Note: mutate the node
export function getOrMakeChild(parent, id, makeUid = (id) => id) {
  if (!hasChildren(parent)) {
    parent.children = []
  }
  // ignore duplicates
  if (!parent.children.find((c) => c.id === id)) {
    parent.children.push({
      id,
      uid: makeUid(id),
      path: [...(parent.path ?? parent.id), id]
    })
  }
  const [child] = parent.children.slice(-1)
  return child
}

// Note: mutate the node
export function getOrMakeNode(baseNode, path, makeUid = (id) => id) {
  const [id] = path.slice(-1)
  const parentPath = path.slice(0, -1)
  let parentNode = getNode(baseNode, parentPath)
  if (!parentNode) {
    parentNode = getOrMakeNode(baseNode, parentPath, makeUid)
  }
  return getOrMakeChild(parentNode, id, makeUid)
}

export function filterNode(node, match) {
  const isCurrentMatched = match(node)
  const filteredChildren =
    node.children?.map((c) => filterNode(c, match)).filter((c) => !!c) || []

  if (isCurrentMatched || filteredChildren.length > 0) {
    return { ...node, children: filteredChildren }
  } else return null
}
