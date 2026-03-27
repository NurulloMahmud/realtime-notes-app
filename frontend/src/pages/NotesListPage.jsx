import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getNotes, createNote, deleteNote } from '../api/notes'
import { useAuth } from '../context/AuthContext'

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function NotesListPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [notes, setNotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showNewForm, setShowNewForm] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    getNotes()
      .then(setNotes)
      .catch(() => setError('Failed to load notes'))
      .finally(() => setLoading(false))
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    if (!newTitle.trim()) return
    setCreating(true)
    try {
      const note = await createNote(newTitle.trim())
      navigate(`/notes/${note.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create note')
      setCreating(false)
    }
  }

  async function handleDelete(e, noteId) {
    e.stopPropagation()
    if (!confirm('Delete this note?')) return
    try {
      await deleteNote(noteId)
      setNotes((prev) => prev.filter((n) => n.id !== noteId))
    } catch {
      setError('Failed to delete note')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Collab Notes</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">{user?.username}</span>
          <button
            onClick={logout}
            className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-medium text-gray-900">My Notes</h2>
          <button
            onClick={() => setShowNewForm(true)}
            className="bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            New note
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
            {error}
          </div>
        )}

        {showNewForm && (
          <form
            onSubmit={handleCreate}
            className="bg-white border border-gray-200 rounded-xl p-4 mb-4 flex gap-3"
          >
            <input
              autoFocus
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Note title..."
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={creating}
              className="bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
            <button
              type="button"
              onClick={() => { setShowNewForm(false); setNewTitle('') }}
              className="text-gray-500 text-sm px-3 py-2 rounded-lg hover:bg-gray-100"
            >
              Cancel
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-center py-16 text-gray-400">Loading...</div>
        ) : notes.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-gray-400 mb-4">No notes yet</p>
            <button
              onClick={() => setShowNewForm(true)}
              className="text-blue-600 text-sm hover:underline"
            >
              Create your first note
            </button>
          </div>
        ) : (
          <div className="grid gap-3">
            {notes.map((note) => (
              <div
                key={note.id}
                onClick={() => navigate(`/notes/${note.id}`)}
                className="bg-white border border-gray-200 rounded-xl p-5 cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">{note.title}</h3>
                    <p className="text-sm text-gray-400 mt-1 truncate">
                      {note.content || 'No content'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 ml-4 flex-shrink-0">
                    <span className="text-xs text-gray-400">{formatDate(note.updated_at)}</span>
                    {note.owner_id === user?.id && (
                      <button
                        onClick={(e) => handleDelete(e, note.id)}
                        className="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all text-sm"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
