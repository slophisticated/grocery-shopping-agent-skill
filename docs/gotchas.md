# Gotchas

## Retailer catalog fields cannot grant substitution permission

Issue: a cheaper catalog match may be incomplete or replace a locked product.

Verified fix: the fictional retailer adapter keeps caller-owned requirements
separate from catalog evidence. Its integration tests confirm that the sample
evaluator rejects missing items, undersized packages, forbidden substitutions,
and substitutes that fail protected attributes; expired or ineligible coupons
are excluded from the normalized price.

## Historical artifacts can disagree

Issue: multiple shopping artifacts may contain different item counts, totals, or update times.

Verified fix: designate one canonical state file, treat other artifacts as historical evidence, and compare timestamps before applying changes.

## A low item price can produce a worse basket

Issue: delivery fees, service fees, minimum-order charges, and incomplete coverage can erase item-level savings.

Verified fix: compare normalized unit cost and the complete delivered basket, then show any split order separately.

## Checkout claims are not public evidence

Issue: exact eligibility, account-only coupons, taxes, tips, and member pricing may not be visible without authentication.

Verified fix: keep those fields unknown or estimated until verified and never present them as confirmed public facts.

## Package changes can hide a bad substitution

Issue: a cheaper-looking replacement may use a smaller package or cover fewer days.

Verified fix: normalize units and state the package and horizon differences in every substitution proposal.

## The bundled skill checker may lack its YAML dependency

Issue: the local `quick_validate.py` entrypoint could not start because PyYAML was not installed in its Python environment, and the installed Ruby YAML version did not expose `safe_load_file` for the first fallback attempt.

Verified fix: the repository's dependency-free validator passed, the YAML frontmatter and `agents/openai.yaml` were parsed with `safe_load` over explicit file contents, and no scaffold placeholders remained.

## Packaging checks depend on the current directory

Issue: one final metadata command was launched from the `outputs` directory while still prefixing repository paths with `outputs/`, so the files were not found.

Verified fix: rerun the checks with repository paths relative to the actual current directory, then rebuild and test the archive.

## GitHub publishing may require approved network access

Issue: the first GitHub identity check produced no output inside the restricted network environment.

Verified fix: rerun the narrow GitHub command with approved network access, verify the active account, create the repository as private, push `main`, and read back the private visibility setting.

## Inspect ZIP archives one at a time

Issue: `zipinfo` treats a second archive argument as a filename pattern inside the first archive rather than as another archive to inspect.

Verified fix: inspect each archive in a separate command and confirm that neither contains `.git` metadata.

## A technical README can hide the fun part

Issue: the original README led with the repository tree before showing the address-aware delivery comparison, deal search, and smart substitution experience.

Verified fix: lead with user outcomes and visual examples, move implementation details lower, and keep every capability claim tied to the actual approval and privacy boundaries.

## Keep multi-file patches scoped to the correct file

Issue: the first combined redesign patch targeted a gotcha-log sentence inside the workflow reference, so patch verification rejected the entire change before editing any file.

Verified fix: split the work into file-specific hunks, apply the workflow and gotcha changes to their correct paths, and verify the resulting diff before testing.

## Preview SVG artwork through a rendered copy

Issue: the local image viewer does not open SVG files directly, so it could not provide the required visual inspection of the README hero artwork.

Verified fix: validate the source SVG as XML, render a temporary PNG with ImageMagick, visually inspect the PNG, and keep the resolution-independent SVG as the only repository asset.

## Use the supported Ruby YAML interface

Issue: the installed Ruby YAML library does not expose `safe_load_file`, so the first final metadata check failed before parsing the agent manifest.

Verified fix: read the file explicitly and pass its contents to `YAML.safe_load`; the manifest then parsed successfully with aliases disabled.

## Use the supported repository view output

Issue: `gh-axi repo view` does not support the GitHub CLI `--json` flag, so the first remote visibility check was rejected.

Verified fix: inspect the command help, run the supported repository view command without that flag, and confirm that the repository reports `visibility: private` and `branch: main`.

## README heroes and social cards use different aspect ratios

Issue: the wide 1200 by 360 README hero crops poorly when reused directly as GitHub's approximately 2:1 social preview.

Verified fix: render a separate 1280 by 640 PNG from a converter-stable SVG copy, replace unsupported gradients with matching solid palette colors, preserve the full hero inside a matching background, and visually verify the result before upload.

## Fall back cleanly when the GitHub wrapper cache is unavailable

Issue: `npx -y gh-axi` could not start because the local npm cache contained root-owned temporary files.

Verified fix: use the already authenticated `gh` CLI for the same narrowly scoped GitHub operations, and verify each remote result through GitHub's API.

## Verify current action versions with network access

Issue: the first action-version lookup could not reach GitHub from the restricted environment.

Verified fix: grant network access for the GitHub task, query the official action repositories, and pin the workflow to the current `actions/checkout@v7` and `actions/setup-python@v7` major versions.

## Use explicit percentage coordinates for social-card gradients

Issue: ImageMagick interpreted unitless SVG gradient endpoints differently and rendered the first social-preview background nearly black.

Verified fix: replace conversion-sensitive gradient fills with calibrated solid brand colors, render the PNG again, and visually inspect the final 1280 by 640 asset.

## Preserve concurrent public-presentation improvements

Issue: the remote repository gained a presentation commit while the local CI and social-preview commit was being prepared, so the first push was correctly rejected and the rebase found overlapping social assets.

Verified fix: fetch and inspect the remote commit, retain its README copy and cross-repository links, keep the newer 1280 by 640 social card, combine both gotcha records, rerun validation, and only then push the integrated history.

## Use fields supported by the installed release client

Issue: the installed GitHub CLI does not expose an `isLatest` field through `gh release view --json`, so the first release-verification query was rejected.

Verified fix: query the supported tag, draft, prerelease, immutability, publication-time, target, and URL fields, then confirm that `v0.1.0` is a published non-draft release.

## Keep the patch terminator outside added file content

Issue: the first combined community-file patch accidentally prefixed the patch terminator as added content, so `apply_patch` rejected the patch before changing any file.

Verified fix: correct the final patch marker, reapply the complete patch, and verify that all community files were created in their intended paths.

## Read GIF loop metadata from verbose identification output

Issue: ImageMagick warned that the compact `%[iterations]` property was unknown while checking the generated demo GIF.

Verified fix: inspect the GIF with `identify -verbose`, confirm all three frame delays, and verify that every frame reports `Iterations: 0` for continuous looping.
