module.exports = {
  collectCoverageFrom: ["**/*.{js,jsx}", "!**/node_modules/**"],
  testPathIgnorePatterns: ["/node_modules/", "/.next/", ".yaml"],
  transform: {
    "^.+\\.(js|jsx)$": "<rootDir>/node_modules/babel-jest"
  },
  transformIgnorePatterns: ["/node_modules/"]
}
