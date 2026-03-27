import client from './client'

export async function getNotes() {
  const { data } = await client.get('/notes')
  return data
}

export async function getNote(id) {
  const { data } = await client.get(`/notes/${id}`)
  return data
}

export async function createNote(title, content = '') {
  const { data } = await client.post('/notes', { title, content })
  return data
}

export async function updateNote(id, patch) {
  const { data } = await client.patch(`/notes/${id}`, patch)
  return data
}

export async function deleteNote(id) {
  await client.delete(`/notes/${id}`)
}
