module.exports = {
  // eslint-disable-next-line no-unused-vars
  webpack(config, options) {
    config.module.rules.push({
      test: /\.ya?ml$/,
      use: "js-yaml-loader"
    })
    return config
  },
  trailingSlash: true,
  productionBrowserSourceMaps: true
}
