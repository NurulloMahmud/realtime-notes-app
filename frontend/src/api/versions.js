import client from './client'

export async function getVersions(noteId) {
  const { data } = await client.get(`/notes/${noteId}/versions`)
  return data
}

export async function restoreVersion(noteId, versionId) {
  const { data } = await client.post(`/notes/${noteId}/versions/${versionId}/restore`)
  return data
}
