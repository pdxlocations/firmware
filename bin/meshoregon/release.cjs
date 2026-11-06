const UPSTREAM = { owner: "meshtastic", repo: "firmware" };

function selectRelease(releases, requested = "") {
  const version = requested.trim().replace(/^v/, "");
  const published = releases.filter((release) => !release.draft && release.published_at && /^v?\d+\.\d+\.\d+(?:[.-]|$)/.test(release.tag_name));
  published.sort((a, b) => Date.parse(b.published_at) - Date.parse(a.published_at));
  const match = published.find((release) => {
    const tag = release.tag_name.replace(/^v/, "");
    return !version || tag === version || tag.startsWith(version + ".") || tag.startsWith(version + "-");
  });
  if (!match) throw new Error(`No published Meshtastic release matches ${requested || "latest"}`);
  return match;
}

async function resolve({ github, context, core, version }) {
  const releases = await github.paginate(github.rest.repos.listReleases, { ...UPSTREAM, per_page: 100 });
  const release = selectRelease(releases, context.eventName === "schedule" ? "" : version);
  const profile = await github.rest.repos.getBranch({ ...context.repo, branch: "MeshOregon" });
  const profileCommit = profile.data.commit.sha;
  const reference = await github.rest.git.getRef({ ...UPSTREAM, ref: `tags/${release.tag_name}` });
  let object = reference.data.object;
  for (let depth = 0; object.type === "tag" && depth < 8; depth++) {
    object = (await github.rest.git.getTag({ ...UPSTREAM, tag_sha: object.sha })).data.object;
  }
  if (object.type !== "commit") throw new Error("Upstream release tag does not resolve to a commit");
  const tag = `meshoregon-${release.tag_name}-${profileCommit.slice(0, 12)}`;
  let exists = false;
  try {
    const existing = await github.rest.repos.getReleaseByTag({ ...context.repo, tag });
    exists = !existing.data.draft;
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  core.setOutput("build", String(!exists));
  core.setOutput("commit", object.sha);
  core.setOutput("profile_commit", profileCommit);
  core.setOutput("upstream_tag", release.tag_name);
  core.setOutput("upstream_release_id", String(release.id));
  core.setOutput("release_tag", tag);
  await core.summary.addHeading("MeshOregon firmware").addRaw(
    `Upstream: ${release.tag_name} (${object.sha})\n\nMeshOregon profile: ${profileCommit}\n\n${exists ? "Already published; skipping." : "Building all hardware targets."}`
  ).write();
}

module.exports = { resolve, selectRelease };
