export function pluralizeWord(word, count) {
  if (count != 1) {
    word = word + "s"
  }
  return word
}

export function subsetCountLabel(subset) {
  if (!('count' in subset)) {
    return ""
  }
  const cnvCountLabel = subset.cnvAnalyses ? `, ${subset.cnvAnalyses} ${pluralizeWord("CNV profile", subset.cnvAnalyses)}` : ""
  return `(${subset.count} ${pluralizeWord("sample", subset.count)}${cnvCountLabel})`
}
