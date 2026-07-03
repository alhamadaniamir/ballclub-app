<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhUserCircle, PhLockKey, PhPencilSimple, PhSignOut, PhSparkle } from '@phosphor-icons/vue'
import { getMe, changePassword, updateProfile } from '@/lib/api'
import { changePasswordSchema, profileSchema, firstIssueMessage } from '@/lib/validation'
import { useAuth } from '@/composables/useAuth'
import { useConfirm } from '@/composables/useConfirm'
import ErrorMessage from '@/components/ui/ErrorMessage.vue'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const router = useRouter()
const auth = useAuth()
const { confirm } = useConfirm()

async function handleLogout() {
  const ok = await confirm({
    title: 'Log out?',
    message: 'You will need to sign in again to access the dashboard.',
    confirmText: 'Log out',
    danger: true,
  })
  if (!ok) return
  auth.logout()
  router.push({ name: 'login' })
}

const me = ref(null)
const loading = ref(true)

const isEditing = ref(false)
const editUsername = ref('')
const editFirstName = ref('')
const editLastName = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const error = ref('')
const success = ref('')
const saving = ref(false)

function syncEditFields() {
  editUsername.value = me.value.username
  editFirstName.value = me.value.first_name
  editLastName.value = me.value.last_name
  currentPassword.value = ''
  newPassword.value = ''
}

async function load() {
  loading.value = true
  try {
    me.value = await getMe()
    syncEditFields()
  } finally {
    loading.value = false
  }
}

function startEditing() {
  error.value = ''
  success.value = ''
  isEditing.value = true
}

function cancelEditing() {
  syncEditFields()
  error.value = ''
  isEditing.value = false
}

function generateUsername() {
  const first = editFirstName.value.trim().split(/\s+/)[0] || ''
  const last = editLastName.value.trim().replace(/\s+/g, '')
  const base = `${first}${last}`.toLowerCase().replace(/[^a-z0-9]/g, '')
  if (base.length < 3) {
    error.value = 'Add a first and last name first to generate a username.'
    return
  }
  error.value = ''
  editUsername.value = base
}

async function handleSave() {
  error.value = ''
  success.value = ''

  const profileResult = profileSchema.safeParse({
    username: editUsername.value,
    firstName: editFirstName.value,
    lastName: editLastName.value,
  })
  if (!profileResult.success) {
    error.value = firstIssueMessage(profileResult)
    return
  }

  const wantsPasswordChange = currentPassword.value || newPassword.value
  let passwordResult = null
  if (wantsPasswordChange) {
    passwordResult = changePasswordSchema.safeParse({
      currentPassword: currentPassword.value,
      newPassword: newPassword.value,
    })
    if (!passwordResult.success) {
      error.value = firstIssueMessage(passwordResult)
      return
    }
  }

  saving.value = true
  try {
    me.value = await updateProfile(profileResult.data.username, profileResult.data.firstName, profileResult.data.lastName)
    if (passwordResult) {
      await changePassword(passwordResult.data.currentPassword, passwordResult.data.newPassword)
    }
    syncEditFields()
    isEditing.value = false
    success.value = wantsPasswordChange ? 'Profile and password updated.' : 'Profile updated.'
  } catch (err) {
    error.value = err.message || 'Failed to save changes'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="mb-2 text-[11px] tracking-wide text-muted-foreground">MY PROFILE</div>

    <Card v-if="loading" size="sm" class="w-full">
      <CardContent>
        <div class="flex flex-col gap-2">
          <Skeleton class="h-11 w-full" />
          <Skeleton class="h-11 w-full" />
          <Skeleton class="h-11 w-full" />
        </div>
      </CardContent>
    </Card>

    <Card v-else size="sm" class="w-full shadow-sm shadow-black/10">
      <CardHeader>
        <CardTitle class="flex items-center gap-2 text-[11px] tracking-wide text-muted-foreground">
          <PhUserCircle :size="16" />
          ACCOUNT INFO
        </CardTitle>
        <CardAction v-if="!isEditing">
          <Button variant="outline" size="sm" @click="startEditing">
            <PhPencilSimple :size="13" weight="bold" />
            Edit
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent>
        <form class="flex flex-col gap-2" @submit.prevent="handleSave">
          <Label for="profile-username" class="sr-only">Username</Label>
          <div class="relative">
            <Input
              id="profile-username"
              v-model="editUsername"
              type="text"
              name="username"
              autocomplete="username"
              placeholder="Username"
              :disabled="!isEditing"
              :class="isEditing ? 'pr-28' : ''"
            />
            <button
              v-if="isEditing"
              type="button"
              class="absolute right-1.5 top-1/2 flex -translate-y-1/2 items-center gap-1 rounded-md bg-secondary px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground"
              title="Generate a username from your first and last name"
              @click="generateUsername"
            >
              <PhSparkle :size="12" weight="bold" />
              Generate
            </button>
          </div>
          <Label for="profile-first-name" class="sr-only">First Name</Label>
          <Input
            id="profile-first-name"
            v-model="editFirstName"
            type="text"
            name="firstName"
            autocomplete="given-name"
            placeholder="First Name"
            :disabled="!isEditing"
          />
          <Label for="profile-last-name" class="sr-only">Last Name</Label>
          <Input
            id="profile-last-name"
            v-model="editLastName"
            type="text"
            name="lastName"
            autocomplete="family-name"
            placeholder="Last Name"
            :disabled="!isEditing"
          />

          <div class="mb-1 mt-3 flex items-center gap-2 text-[11px] tracking-wide text-muted-foreground">
            <PhLockKey :size="14" />
            {{ isEditing ? 'PASSWORD (LEAVE BLANK TO KEEP CURRENT)' : 'PASSWORD' }}
          </div>
          <Label for="profile-current-password" class="sr-only">Current password</Label>
          <Input
            id="profile-current-password"
            :model-value="isEditing ? currentPassword : '••••••••'"
            type="password"
            name="current-password"
            autocomplete="current-password"
            placeholder="Current password"
            :disabled="!isEditing"
            @update:model-value="currentPassword = $event"
          />
          <Label for="profile-new-password" class="sr-only">New password</Label>
          <Input
            id="profile-new-password"
            :model-value="isEditing ? newPassword : '••••••••'"
            type="password"
            name="new-password"
            autocomplete="new-password"
            placeholder="New password"
            :disabled="!isEditing"
            @update:model-value="newPassword = $event"
          />

          <ErrorMessage :message="error" />

          <div v-if="isEditing" class="mt-1 flex gap-2">
            <Button type="button" variant="outline" class="flex-1" @click="cancelEditing">
              Cancel
            </Button>
            <Button type="submit" class="flex-1" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </Button>
          </div>
          <div v-if="success && !isEditing" class="text-center text-sm text-brand-paid">{{ success }}</div>
        </form>
      </CardContent>
    </Card>

    <Button
      v-if="!loading"
      variant="outline"
      class="mt-4 w-full gap-2 text-destructive hover:text-destructive md:hidden"
      @click="handleLogout"
    >
      <PhSignOut :size="16" weight="bold" />
      Log out
    </Button>
  </div>
</template>
