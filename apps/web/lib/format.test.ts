import { describe, expect, it } from "vitest";

import { formatBudget, formatPoints, freshnessTone, riskLabel } from "./format";

describe("format helpers", () => {
  it("formats strategy metrics consistently", () => {
    expect(formatPoints(42)).toBe("42.0 pts");
    expect(formatBudget(1.25)).toBe("1.3M");
    expect(riskLabel(0.2)).toBe("Low");
    expect(riskLabel(0.4)).toBe("Medium");
    expect(riskLabel(0.8)).toBe("High");
    expect(freshnessTone("ok")).toBe("good");
    expect(freshnessTone("degraded")).toBe("warn");
  });
});
