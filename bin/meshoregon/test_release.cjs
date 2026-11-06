const { test } = require("node:test");
const assert = require("node:assert/strict");
const { selectRelease, resolve } = require("./release.cjs");
const release = (tag, date, extra = {}) => ({ tag_name: tag, published_at: date, draft: false, ...extra });
const releases = [
  release("v2.8.3.abcdef0", "2026-11-06T00:00:00Z", { draft: true }),
  release("v2.8.2.older", "2026-11-02T00:00:00Z", { prerelease: true }),
  release("v2.8.2.newer", "2026-11-04T00:00:00Z", { prerelease: true }),
  release("v2.7.26.stable", "2026-06-24T00:00:00Z"),
];
test("2.8.2 resolves the newest published patch tag, including alpha releases", () => {
  assert.equal(selectRelease(releases, "2.8.2").tag_name, "v2.8.2.newer");
  assert.equal(selectRelease(releases, "v2.8.2.older").tag_name, "v2.8.2.older");
  assert.throws(() => selectRelease(releases, "2.8.20"), /No published/);
});
test("automatic selection uses publication time and excludes drafts", () => {
  assert.equal(selectRelease([...releases].reverse()).tag_name, "v2.8.2.newer");
  assert.throws(() => selectRelease([release("v2.8.3.test", null)]), /No published/);
});
function fixture({ exists = false, draft = false, status = 404 } = {}) {
  const outputs = {};
  const github = {
    paginate: async () => releases,
    rest: {
      repos: { listReleases() {}, getBranch: async () => ({ data: { commit: { sha: "profile-sha-123456789" } } }), getReleaseByTag: async () => { if (!exists) throw { status }; return { data: { draft } }; } },
      git: { getRef: async () => ({ data: { object: { type: "tag", sha: "annotated" } } }), getTag: async () => ({ data: { object: { type: "commit", sha: "upstream-sha" } } }) },
    },
  };
  const summary = { addHeading() { return this; }, addRaw() { return this; }, async write() {} };
  return { github, context: { repo: { owner: "example", repo: "firmware" }, eventName: "schedule" }, core: { summary, setOutput: (key, value) => { outputs[key] = value; } }, outputs, version: "2.7.26" };
}
test("scheduler pins both commits and peels annotated release tags", async () => {
  const input = fixture(); await resolve(input);
  assert.equal(input.outputs.build, "true");
  assert.equal(input.outputs.upstream_tag, "v2.8.2.newer");
  assert.equal(input.outputs.commit, "upstream-sha");
  assert.equal(input.outputs.profile_commit, "profile-sha-123456789");
});
test("an existing successful release is skipped; API errors remain failures", async () => {
  const input = fixture({ exists: true }); await resolve(input); assert.equal(input.outputs.build, "false");
  await assert.rejects(resolve(fixture({ status: 403 })), (error) => error.status === 403);
});

test("an incomplete draft release is retried", async () => {
  const input = fixture({ exists: true, draft: true });
  await resolve(input);
  assert.equal(input.outputs.build, "true");
});

test("manual version selection stays on 2.8.2 when a newer release exists", () => {
  const withFuture = [...releases, release("v2.9.0.future", "2027-01-01T00:00:00Z")];
  assert.equal(selectRelease(withFuture, "2.8.2").tag_name, "v2.8.2.newer");
  assert.equal(selectRelease(withFuture).tag_name, "v2.9.0.future");
});
