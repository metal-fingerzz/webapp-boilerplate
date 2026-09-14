import { transformSync } from "@babel/core";
import { expect, it } from "vitest";

// This file mirrors no source module, where docs/testing.md §2 asks the test
// tree to follow the sources. The exception is deliberate: what is guarded here
// is the toolchain, not a module, and it stays confined to this file.
//
// babel-plugin-react-compiler asserts the @babel/core major when it loads
// ("Requires Babel ^7.0.0-0"). Under a major it does not support it either
// throws, or — depending on how the pipeline loads it — stops compiling without
// a word. Nothing else would catch that second case: the package declares
// neither peerDependencies nor engines, and the rest of this suite exercises
// rendering, never memoisation. A component that is no longer compiled still
// renders; it just stops being memoised.
//
// The check is therefore behavioural rather than a comparison of declared
// versions, which would only be a proxy for the assertion above: it runs the
// compiler and looks for what compiled output carries. Upstream bug:
// react/react#36868.

const COMPONENT = `
export function Counter({ items }) {
  const total = items.reduce((sum, item) => sum + item, 0);
  return <div>{total}</div>;
}
`;

const REFUSAL =
  "The React Compiler no longer compiles through the installed @babel/core. " +
  "If a @babel/core upgrade is being proposed, this is the reason not to merge it.";

it("compiles a component through the installed @babel/core", () => {
  let compiled;

  try {
    compiled = transformSync(COMPONENT, {
      filename: "Counter.jsx",
      plugins: [["babel-plugin-react-compiler", {}]],
      parserOpts: { plugins: ["jsx"] },
      configFile: false,
      babelrc: false,
    });
  } catch (error) {
    throw new Error(REFUSAL, { cause: error });
  }

  // Compiled components read their memoisation cache from this entry point;
  // left uncompiled, the output is the source unchanged.
  expect(compiled?.code, REFUSAL).toContain("react/compiler-runtime");
});
