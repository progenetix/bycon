import { checkIntegerRange } from "../../hooks/api"

test("checkIntegerRange", () => {
  expect(checkIntegerRange("1")).toBeFalsy()
  expect(checkIntegerRange("1-2")).toBeFalsy()
  expect(checkIntegerRange("1,2")).toBeFalsy()

  // This is like 1
  expect(checkIntegerRange("1,")).toBeFalsy()

  expect(checkIntegerRange("a")).toBeTruthy()

  // min > max
  expect(checkIntegerRange("2-1")).toBeTruthy()
})
