# libssh2 patches

`Vendor/libssh2` is the official upstream submodule; its gitlink pins the commit.
Numbered unified diffs are the only maintained native changes. CI applies them
to an ignored `.build/patched-native` export and publishes an XCFramework.
Never commit the exported or patched source tree.

- `0001-external-publickey-signatures.patch` preserves the complete SSH signature
  API from the former fork's commit `be1ed3f087b35db3248c7bb2e9d496ab72ecb94f`.
  It includes the C regression test and its build registration. Fork-only CI
  branch changes are intentionally excluded.

`Script/apply-patches.sh <source_dir>` applies `.patch` files in filename order,
skips patches whose full reverse diff validates, and fails on conflicts or
unsupported file types. Markdown files are ignored. It never uses a fuzzy or
three-way fallback. Add or edit a patch, run the native regressions, and publish through CI.
When upgrading upstream, resolve any conflict explicitly and keep the regression
tests. Remove a patch once the pinned upstream implements the same behavior.

The external callback's allocator ownership and nonblocking `EAGAIN` contract
remain documented in `include/libssh2.h`. Its tests cover complete signature
encoding, asynchronous retries without signing twice, invalid output, and the
legacy API's signature wrapping.
