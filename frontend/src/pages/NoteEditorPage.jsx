import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getNote, updateNote, deleteNote } from '../api/notes'
import { getCollaborators, addCollaborator, removeCollaborator } from '../api/collaborators'
import { getVersions, restoreVersion } from '../api/versions'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuth } from '../context/AuthContext'

function formatDate(iso) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const CURSOR_COLORS = [
  'bg-blue-500', 'bg-green-500', 'bg-purple-500',
  'bg-orange-500', 'bg-pink-500', 'bg-teal-500',
  'bg-red-500', 'bg-yellow-500',
]

function colorForUser(username) {
  let hash = 0
  for (const c of username) hash = (hash * 31 + c.charCodeAt(0)) % CURSOR_COLORS.length
  return CURSOR_COLORS[hash]
}

function getLineFromPos(text, pos) {
  return text.slice(0, pos).split('\n').length
}

export default function NoteEditorPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [note, setNote] = useState(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [collaborators, setCollaborators] = useState([])
  const [versions, setVersions] = useState([])
  const [onlineUsers, setOnlineUsers] = useState([])
  const [remoteCursors, setRemoteCursors] = useState({})
  const [panel, setPanel] = useState(null)
  const [saveStatus, setSaveStatus] = useState('saved')
  const [error, setError] = useState('')
  const [collabEmail, setCollabEmail] = useState('')
  const [collabError, setCollabError] = useState('')
  const [loading, setLoading] = useState(true)

  const debounceRef = useRef(null)
  const isMineEdit = useRef(false)

  const isOwner = note?.owner_id === user?.id

  useEffect(() => {
    Promise.all([getNote(id), getCollaborators(id), getVersions(id)])
      .then(([n, collabs, vers]) => {
        setNote(n)
        setTitle(n.title)
        setContent(n.content)
        setCollaborators(collabs)
        setVersions(vers)
      })
      .catch(() => setError('Note not found or access denied'))
      .finally(() => setLoading(false))
  }, [id])

  const handleWsMessage = useCallback(
    (msg) => {
      if (msg.type === 'update' && msg.user_id !== user?.id) {
        if (!isMineEdit.current) {
          setContent(msg.content)
          setSaveStatus('saved')
        }
        setRemoteCursors((prev) => ({
          ...prev,
          [msg.user_id]: {
            username: msg.username,
            cursor_position: msg.cursor_position ?? 0,
          },
        }))
      }

      if (msg.type === 'cursor' && msg.user_id !== user?.id) {
        setRemoteCursors((prev) => ({
          ...prev,
          [msg.user_id]: {
            username: msg.username,
            cursor_position: msg.cursor_position,
          },
        }))
      }

      if (msg.type === 'presence') {
        if (msg.status === 'joined') {
          setOnlineUsers((prev) =>
            prev.find((u) => u.user_id === msg.user_id)
              ? prev
              : [...prev, { user_id: msg.user_id, username: msg.username }]
          )
        } else {
          setOnlineUsers((prev) => prev.filter((u) => u.user_id !== msg.user_id))
          setRemoteCursors((prev) => {
            const next = { ...prev }
            delete next[msg.user_id]
            return next
          })
        }
      }
    },
    [user?.id]
  )

  const { sendEdit, sendCursor } = useWebSocket(id, handleWsMessage)

  function handleContentChange(e) {
    const val = e.target.value
    setContent(val)
    setSaveStatus('unsaved')
    isMineEdit.current = true

    sendCursor(e.target.selectionStart)

    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      sendEdit(val, e.target.selectionStart)
      isMineEdit.current = false
      setSaveStatus('saved')
    }, 800)
  }

  function handleCursorMove(e) {
    sendCursor(e.target.selectionStart)
  }

  async function handleTitleBlur() {
    if (!note || title === note.title) return
    try {
      const updated = await updateNote(id, { title })
      setNote(updated)
    } catch {
      setTitle(note.title)
    }
  }

  async function handleDelete() {
    if (!confirm('Delete this note permanently?')) return
    try {
      await deleteNote(id)
      navigate('/notes')
    } catch {
      setError('Failed to delete note')
    }
  }

  async function handleAddCollaborator(e) {
    e.preventDefault()
    setCollabError('')
    try {
      await addCollaborator(id, collabEmail)
      const updated = await getCollaborators(id)
      setCollaborators(updated)
      setCollabEmail('')
    } catch (err) {
      setCollabError(err.response?.data?.detail || 'Failed to add collaborator')
    }
  }

  async function handleRemoveCollaborator(userId) {
    try {
      await removeCollaborator(id, userId)
      setCollaborators((prev) => prev.filter((c) => c.user_id !== userId))
    } catch {
      setCollabError('Failed to remove collaborator')
    }
  }

  async function handleRestoreVersion(versionId) {
    if (!confirm('Restore this version? Current content will be replaced.')) return
    try {
      await restoreVersion(id, versionId)
      const [updated, updatedVersions] = await Promise.all([getNote(id), getVersions(id)])
      setContent(updated.content)
      setNote(updated)
      setVersions(updatedVersions)
      setPanel(null)
    } catch {
      setError('Failed to restore version')
    }
  }

  async function openVersions() {
    const vers = await getVersions(id).catch(() => [])
    setVersions(vers)
    setPanel('versions')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        Loading...
      </div>
    )
  }

  if (error && !note) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-gray-500">{error}</p>
        <button onClick={() => navigate('/notes')} className="text-blue-600 text-sm hover:underline">
          Back to notes
        </button>
      </div>
    )
  }

  const cursors = Object.entries(remoteCursors)

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <header className="border-b border-gray-200 px-6 py-3 flex items-center gap-4">
        <button
          onClick={() => navigate('/notes')}
          className="text-gray-400 hover:text-gray-700 text-sm transition-colors"
        >
          Back
        </button>

        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleTitleBlur}
          className="flex-1 text-lg font-medium text-gray-900 focus:outline-none border-b border-transparent focus:border-gray-300 pb-0.5 transition-colors"
          placeholder="Untitled"
        />

        <div className="flex items-center gap-3 flex-shrink-0">
          <span
            className={`text-xs ${saveStatus === 'saved' ? 'text-gray-400' : 'text-amber-500'}`}
          >
            {saveStatus === 'saved' ? 'Saved' : 'Saving...'}
          </span>

          {onlineUsers.length > 0 && (
            <div className="flex -space-x-1">
              {onlineUsers.slice(0, 4).map((u) => (
                <div
                  key={u.user_id}
                  title={`${u.username} is online`}
                  className={`w-7 h-7 rounded-full ${colorForUser(u.username)} flex items-center justify-center text-white text-xs font-medium border-2 border-white`}
                >
                  {u.username[0].toUpperCase()}
                </div>
              ))}
              {onlineUsers.length > 4 && (
                <div className="w-7 h-7 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 text-xs border-2 border-white">
                  +{onlineUsers.length - 4}
                </div>
              )}
            </div>
          )}

          <button
            onClick={() => setPanel(panel === 'collaborators' ? null : 'collaborators')}
            className={`text-sm px-3 py-1.5 rounded-lg transition-colors ${
              panel === 'collaborators' ? 'bg-blue-50 text-blue-600' : 'text-gray-500 hover:bg-gray-100'
            }`}
          >
            People
          </button>

          <button
            onClick={panel === 'versions' ? () => setPanel(null) : openVersions}
            className={`text-sm px-3 py-1.5 rounded-lg transition-colors ${
              panel === 'versions' ? 'bg-blue-50 text-blue-600' : 'text-gray-500 hover:bg-gray-100'
            }`}
          >
            History
          </button>

          {isOwner && (
            <button
              onClick={handleDelete}
              className="text-sm px-3 py-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            >
              Delete
            </button>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 flex flex-col p-8 overflow-auto">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
              {error}
            </div>
          )}

          {cursors.length > 0 && (
            <div className="flex gap-2 mb-3 flex-wrap max-w-3xl mx-auto w-full">
              {cursors.map(([userId, cursor]) => (
                <span
                  key={userId}
                  className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full text-white ${colorForUser(cursor.username)}`}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-white opacity-80" />
                  {cursor.username}
                  {cursor.cursor_position != null && (
                    <span className="opacity-75">
                      · line {getLineFromPos(content, cursor.cursor_position)}
                    </span>
                  )}
                </span>
              ))}
            </div>
          )}

          <textarea
            value={content}
            onChange={handleContentChange}
            onKeyUp={handleCursorMove}
            onClick={handleCursorMove}
            placeholder="Start writing..."
            className="flex-1 w-full max-w-3xl mx-auto resize-none focus:outline-none text-gray-800 text-base leading-relaxed min-h-[70vh]"
          />
        </main>

        {panel === 'collaborators' && (
          <aside className="w-72 border-l border-gray-200 flex flex-col overflow-auto">
            <div className="px-5 py-4 border-b border-gray-100">
              <h3 className="font-medium text-gray-900 text-sm">Collaborators</h3>
            </div>

            {isOwner && (
              <form
                onSubmit={handleAddCollaborator}
                className="px-5 py-4 border-b border-gray-100 space-y-2"
              >
                <input
                  type="email"
                  value={collabEmail}
                  onChange={(e) => setCollabEmail(e.target.value)}
                  placeholder="Email address"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {collabError && <p className="text-xs text-red-500">{collabError}</p>}
                <button
                  type="submit"
                  className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  Add
                </button>
              </form>
            )}

            <div className="flex-1 px-5 py-4 space-y-3">
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-full ${colorForUser(note.owner_username || 'owner')} flex items-center justify-center text-white text-xs font-medium`}
                >
                  {(note.owner_username || 'O')[0].toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {note.owner_username || 'Owner'}
                  </p>
                  <p className="text-xs text-gray-400">Owner</p>
                </div>
              </div>

              {collaborators.map((c) => (
                <div key={c.user_id} className="flex items-center gap-3 group">
                  <div
                    className={`w-8 h-8 rounded-full ${colorForUser(c.username)} flex items-center justify-center text-white text-xs font-medium`}
                  >
                    {c.username[0].toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{c.username}</p>
                    <p className="text-xs text-gray-400 truncate">{c.email}</p>
                  </div>
                  {isOwner && (
                    <button
                      onClick={() => handleRemoveCollaborator(c.user_id)}
                      className="text-gray-300 hover:text-red-500 text-xs opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}

              {collaborators.length === 0 && (
                <p className="text-xs text-gray-400">No collaborators yet</p>
              )}
            </div>
          </aside>
        )}

        {panel === 'versions' && (
          <aside className="w-72 border-l border-gray-200 flex flex-col overflow-auto">
            <div className="px-5 py-4 border-b border-gray-100">
              <h3 className="font-medium text-gray-900 text-sm">Version History</h3>
            </div>
            <div className="flex-1 px-5 py-4 space-y-3">
              {versions.map((v, i) => (
                <div key={v.id} className="border border-gray-200 rounded-lg p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">{formatDate(v.created_at)}</span>
                    {i === 0 ? (
                      <span className="text-xs text-green-600 font-medium">Current</span>
                    ) : (
                      <button
                        onClick={() => handleRestoreVersion(v.id)}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Restore
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-gray-400">by {v.editor_username}</p>
                  <p className="text-xs text-gray-600 line-clamp-2">{v.content || 'Empty'}</p>
                </div>
              ))}
              {versions.length === 0 && (
                <p className="text-xs text-gray-400">No versions yet</p>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}
