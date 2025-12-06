import { useState } from 'react'
import {
  useDepartments,
  useCreateDepartment,
  useUpdateDepartment,
  useDeleteDepartment
} from '../hooks/useDepartments'
import { useTranslation } from 'react-i18next'
import { Building, Plus, Edit, Trash2, X, Loader2, Save, CheckCircle2 } from 'lucide-react'

export default function DepartmentManager() {
  const { t } = useTranslation()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingDept, setEditingDept] = useState<any>(null)
  const [formData, setFormData] = useState({ name: '', description: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const { data: departments = [], isLoading: loading } = useDepartments()
  const createMutation = useCreateDepartment()
  const updateMutation = useUpdateDepartment()
  const deleteMutation = useDeleteDepartment()

  const handleCreate = async () => {
    setError('')
    try {
      await createMutation.mutateAsync(formData)
      setSuccess(t('departments.addDepartment'))
      setShowCreateModal(false)
      setFormData({ name: '', description: '' })
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    }
  }

  const handleUpdate = async () => {
    setError('')
    try {
      await updateMutation.mutateAsync({ departmentId: editingDept.id, data: formData })
      setSuccess(t('common.success'))
      setEditingDept(null)
      setFormData({ name: '', description: '' })
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(t('departments.delete') + '?')) return

    setError('')
    try {
      await deleteMutation.mutateAsync(id)
      setSuccess(t('common.success'))
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    }
  }

  const startEdit = (dept: any) => {
    setEditingDept(dept)
    setFormData({ name: dept.name, description: dept.description || '' })
    setError('')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">{t('departments.title')}</h2>
        <button
          onClick={() => {
            setShowCreateModal(true)
            setFormData({ name: '', description: '' })
            setError('')
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t('departments.addDepartment')}
        </button>
      </div>

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          {success}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      {departments.length === 0 ? (
        <div className="text-center py-12">
          <Building className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">{t('departments.noDepartments')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map((dept) => (
            <div key={dept.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{dept.name}</h3>
                {dept.description && <p className="text-sm text-gray-600">{dept.description}</p>}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => startEdit(dept)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm font-medium"
                >
                  <Edit className="w-4 h-4" />
                  {t('departments.edit')}
                </button>
                <button
                  onClick={() => handleDelete(dept.id)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm font-medium"
                >
                  <Trash2 className="w-4 h-4" />
                  {t('departments.delete')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {(showCreateModal || editingDept) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => {
          setShowCreateModal(false)
          setEditingDept(null)
          setFormData({ name: '', description: '' })
          setError('')
        }}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingDept ? t('departments.edit') : t('departments.addDepartment')}
              </h3>
              <button onClick={() => {
                setShowCreateModal(false)
                setEditingDept(null)
                setFormData({ name: '', description: '' })
                setError('')
              }} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('departments.name')} *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder={t('departments.name')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('departments.description')}
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder={t('departments.description')}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setEditingDept(null)
                  setFormData({ name: '', description: '' })
                  setError('')
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={editingDept ? handleUpdate : handleCreate}
                disabled={!formData.name || createMutation.isPending || updateMutation.isPending}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {createMutation.isPending || updateMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {createMutation.isPending || updateMutation.isPending
                  ? t('common.loading')
                  : editingDept ? t('common.save') : t('common.create')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
