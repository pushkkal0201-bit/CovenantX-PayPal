# Phase 4 — Judge-facing workflow and payment impact

The overview now presents a clickable journey through contract approval, evidence inspection, review, settlement approval and PayPal Sandbox settlement. Completion indicators derive from the selected milestone's stored state, so the walkthrough follows the actual record instead of a static animation.

A transaction impact panel displays the contract amount, total rule deductions and proposed PayPal amount. It also surfaces the number of clause findings and active holds, and links directly to settlement details. The panel explains the responsibility boundary: Gemini reviews evidence, approved contract rules calculate the amount, and the client authorizes the exact snapshot. It does not imply that Gemini independently chooses a payment amount.

The layout adapts to mobile widths and respects reduced-motion preferences through the existing app behavior. Verification: `npm run build` passed with Next.js production compilation and TypeScript checks.
