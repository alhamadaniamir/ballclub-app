import { z } from 'zod'

const digitCount = (value) => value.replace(/\D/g, '').length

export const nameSchema = z
  .string()
  .trim()
  .min(2, 'Name must be 2-100 characters.')
  .max(100, 'Name must be 2-100 characters.')

export const optionalNameSchema = z.union([z.literal(''), nameSchema])

export const phoneSchema = z
  .string()
  .trim()
  .refine((value) => digitCount(value) >= 10 && digitCount(value) <= 15, 'Phone must be 10-15 digits.')

export const optionalPhoneSchema = z.union([z.literal(''), phoneSchema])

export const usernameSchema = z
  .string()
  .trim()
  .min(3, 'Username must be at least 3 characters.')
  .max(30, 'Username must be 30 characters or fewer.')
  .regex(/^[a-zA-Z0-9._-]+$/, 'Username can only use letters, numbers, dots, underscores, or hyphens.')
export const passwordSchema = z.string().min(8, 'Password must be at least 8 characters.')

export const fullNameSchema = z.object({
  firstName: nameSchema,
  middleName: optionalNameSchema,
  lastName: nameSchema,
})

export const memberSchema = fullNameSchema.extend({ phone: optionalPhoneSchema })
export const walkinSchema = fullNameSchema.extend({ phone: optionalPhoneSchema })
export const joinSchema = fullNameSchema.extend({ phone: phoneSchema })
export const ownerSchema = z.object({ username: usernameSchema, password: passwordSchema })
export const changePasswordSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required.'),
  newPassword: passwordSchema,
})

export const profileSchema = z.object({
  username: usernameSchema,
  firstName: optionalNameSchema,
  lastName: optionalNameSchema,
})

export const feeSchema = z.coerce.number({ message: 'Fee must be a number.' }).min(0, 'Fee must be 0 or more.')

export const sessionMetaSchema = z.object({
  title: z.string().trim().max(100, 'Title must be 100 characters or fewer.'),
  notes: z.string().trim().max(500, 'Notes must be 500 characters or fewer.'),
  location: z.string().trim().max(200, 'Location must be 200 characters or fewer.'),
  capacity: z.union([
    z.literal(''),
    z.coerce.number().int('Capacity must be a whole number.').min(1, 'Capacity must be at least 1.'),
  ]),
})

export function firstIssueMessage(result) {
  return result.success ? null : result.error.issues[0].message
}
