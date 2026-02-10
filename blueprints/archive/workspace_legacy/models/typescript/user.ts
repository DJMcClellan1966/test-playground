// User - A user in the system

export interface User {
  id: string;
  email: string;
  name: string;
}
export function validateUser(obj: User): string[] {
  const errors: string[] = [];
  return errors;
}