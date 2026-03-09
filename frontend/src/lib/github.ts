export interface GistResult {
  gistUrl: string;
  previewUrl: string;
}

export async function postGist(
  token: string,
  description: string,
  files: Record<string, string>, // filename → content
  previewFilename: string,       // which file to open in htmlpreview
): Promise<GistResult> {
  const res = await fetch("https://api.github.com/gists", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Accept: "application/vnd.github+json",
    },
    body: JSON.stringify({
      description,
      public: false,
      files: Object.fromEntries(Object.entries(files).map(([k, v]) => [k, { content: v }])),
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { message?: string }).message ?? `GitHub API error ${res.status}`);
  }

  const data = (await res.json()) as {
    html_url: string;
    id: string;
    owner: { login: string };
  };

  const rawUrl = `https://gist.githubusercontent.com/${data.owner.login}/${data.id}/raw/${previewFilename}`;

  return {
    gistUrl: data.html_url,
    previewUrl: `https://htmlpreview.github.io/?${rawUrl}`,
  };
}
