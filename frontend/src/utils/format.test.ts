import { describe, expect, it } from 'vitest'
import { formatDateTime, initials, relativeTime } from './format'

describe('format utilities', () => {
  it('handles empty and invalid dates safely', () => {
    expect(formatDateTime()).toBe('—')
    expect(formatDateTime('not-a-date')).toBe('—')
  })

  it('creates stable avatar initials', () => {
    expect(initials(' devflow ')).toBe('DE')
    expect(initials('')).toBe('DF')
  })

  it('falls back safely for an invalid relative date', () => {
    expect(relativeTime('invalid')).toBe('—')
  })
})
