import client from './client'

export async function getCollaborators(noteId) {
  const { data } = await client.get(`/notes/${noteId}/collaborators`)
  return data
}

export async function addCollaborator(noteId, email) {
  const { data } = await client.post(`/notes/${noteId}/collaborators`, { email })
  return data
}

export async function removeCollaborator(noteId, userId) {
  await client.delete(`/notes/${noteId}/collaborators/${userId}`)
}
