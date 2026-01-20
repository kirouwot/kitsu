/**
 * API Contract Validation Guards
 * 
 * This module provides fail-fast contract validation for API responses.
 * All guards:
 * - Throw Error on contract violation
 * - Are synchronous and deterministic
 * - Have no side effects
 * - Do NOT use optional chaining
 * - Do NOT provide fallback values
 */

/**
 * Asserts that value is an object (not null, not array)
 * @throws Error if value is not an object
 */
export function assertObject(value: unknown, name: string): asserts value is Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error(`Contract violation: ${name} must be an object, got ${typeof value}`);
  }
}

/**
 * Asserts that value is a string
 * @throws Error if value is not a string
 */
export function assertString(value: unknown, field: string): asserts value is string {
  if (typeof value !== 'string') {
    throw new Error(`Contract violation: ${field} must be string, got ${typeof value}`);
  }
}

/**
 * Asserts that value is a number
 * @throws Error if value is not a number
 */
export function assertNumber(value: unknown, field: string): asserts value is number {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    throw new Error(`Contract violation: ${field} must be number, got ${typeof value}`);
  }
}

/**
 * Asserts that value is an array
 * @throws Error if value is not an array
 */
export function assertArray(value: unknown, field: string): asserts value is unknown[] {
  if (!Array.isArray(value)) {
    throw new Error(`Contract violation: ${field} must be array, got ${typeof value}`);
  }
}

/**
 * Validates optional fields - returns true if value is present and valid
 * @param value - The value to validate
 * @param validator - Function that validates the value if present
 * @returns true if value is present and valid, false if null/undefined
 * @throws Error if value is present but invalid
 */
export function assertOptional<T>(
  value: unknown,
  validator: (value: unknown) => asserts value is T
): value is T {
  if (value === null || value === undefined) {
    return false;
  }
  validator(value);
  return true;
}

/**
 * Asserts API success response envelope
 * Validates that data is an object and not null/undefined
 * @throws Error if response is not a valid success envelope
 */
export function assertApiSuccessResponse(data: unknown): asserts data is Record<string, unknown> {
  if (data === null || data === undefined) {
    throw new Error('Contract violation: API response data must not be null or undefined');
  }
  assertObject(data, 'API response data');
}

/**
 * Asserts API array response
 * Validates that data is an array and not null/undefined
 * @throws Error if response is not a valid array
 */
export function assertArrayResponse(data: unknown): asserts data is unknown[] {
  if (data === null || data === undefined) {
    throw new Error('Contract violation: API array response must not be null or undefined');
  }
  assertArray(data, 'API array response');
}
